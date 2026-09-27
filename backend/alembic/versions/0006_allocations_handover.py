"""allocations (no-overlap EXCLUDE constraints) + handover_reports + trigger

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-05

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Rule 2.1: overlapping allocations for the same vehicle or driver are
# impossible at the DB level, even under concurrent requests. NULL end_at is
# treated as an open-ended (infinite) period. btree_gist allows the integer
# equality inside a gist exclusion constraint.
_EXCLUDE_SQL = [
    "CREATE EXTENSION IF NOT EXISTS btree_gist",
    """
    ALTER TABLE allocations ADD CONSTRAINT ex_allocations_vehicle_period
    EXCLUDE USING gist (
        vehicle_id WITH =,
        tstzrange(start_at, COALESCE(end_at, 'infinity'::timestamptz)) WITH &&
    ) WHERE (deleted_at IS NULL)
    """,
    """
    ALTER TABLE allocations ADD CONSTRAINT ex_allocations_driver_period
    EXCLUDE USING gist (
        driver_id WITH =,
        tstzrange(start_at, COALESCE(end_at, 'infinity'::timestamptz)) WITH &&
    ) WHERE (deleted_at IS NULL)
    """,
]

# Rule 2.3: closed handover reports are read-only, enforced at the DB level
# (same pattern as the trip-sheet trigger in migration 0004).
_TRIGGER_FN = """
CREATE OR REPLACE FUNCTION reject_closed_handover_change()
RETURNS trigger AS $$
BEGIN
    IF OLD.status = 'closed' THEN
        RAISE EXCEPTION 'Closed handover reports are immutable (rule 2.3)';
    END IF;
    IF (TG_OP = 'DELETE') THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

_TRIGGER = """
CREATE TRIGGER trg_handover_immutable
BEFORE UPDATE OR DELETE ON handover_reports
FOR EACH ROW EXECUTE FUNCTION reject_closed_handover_change();
"""


def upgrade() -> None:
    allocation_type = sa.Enum("permanent", "trip", name="allocation_type")
    allocation_status = sa.Enum("active", "ended", name="allocation_status")
    handover_direction = sa.Enum("handover", "return", name="handover_direction")
    handover_status = sa.Enum("draft", "closed", name="handover_status")
    for enum in (allocation_type, allocation_status, handover_direction, handover_status):
        enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("driver_id", sa.Integer(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "type",
            postgresql.ENUM("permanent", "trip", name="allocation_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM("active", "ended", name="allocation_status", create_type=False),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("end_at IS NULL OR end_at > start_at", name="ck_allocation_period"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"]),
    )
    op.create_index("ix_allocations_vehicle_id", "allocations", ["vehicle_id"])
    op.create_index("ix_allocations_driver_id", "allocations", ["driver_id"])

    op.create_table(
        "handover_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("allocation_id", sa.Integer(), nullable=False),
        sa.Column(
            "direction",
            postgresql.ENUM("handover", "return", name="handover_direction", create_type=False),
            nullable=False,
        ),
        sa.Column("km", sa.Integer(), nullable=False),
        sa.Column("fuel_level_pct", sa.Integer(), nullable=False),
        sa.Column("visual_observations", sa.Text(), nullable=True),
        sa.Column("cleanliness", sa.String(length=50), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("draft", "closed", name="handover_status", create_type=False),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("km >= 0", name="ck_handover_km_nonneg"),
        sa.CheckConstraint(
            "fuel_level_pct >= 0 AND fuel_level_pct <= 100", name="ck_handover_fuel_pct"
        ),
        sa.ForeignKeyConstraint(["allocation_id"], ["allocations.id"]),
    )
    op.create_index("ix_handover_reports_allocation_id", "handover_reports", ["allocation_id"])

    for stmt in _EXCLUDE_SQL:
        op.execute(stmt)
    op.execute(_TRIGGER_FN)
    op.execute(_TRIGGER)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_handover_immutable ON handover_reports")
    op.execute("DROP FUNCTION IF EXISTS reject_closed_handover_change")
    op.drop_index("ix_handover_reports_allocation_id", table_name="handover_reports")
    op.drop_table("handover_reports")
    op.drop_index("ix_allocations_driver_id", table_name="allocations")
    op.drop_index("ix_allocations_vehicle_id", table_name="allocations")
    op.drop_table("allocations")
    for name in ("handover_status", "handover_direction", "allocation_status", "allocation_type"):
        sa.Enum(name=name).drop(op.get_bind(), checkfirst=True)
