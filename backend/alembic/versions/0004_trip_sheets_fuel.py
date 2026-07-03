"""trip_sheets, import_batches, fuel_transactions + immutability trigger

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-03

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Rule 2.3: closed trip sheets are read-only, enforced at the DB level so even
# direct SQL / concurrent writes cannot mutate a legal record.
_TRIGGER_FN = """
CREATE OR REPLACE FUNCTION reject_closed_trip_sheet_change()
RETURNS trigger AS $$
BEGIN
    IF OLD.status = 'closed' THEN
        RAISE EXCEPTION 'Closed trip sheets are immutable (rule 2.3)';
    END IF;
    IF (TG_OP = 'DELETE') THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

_TRIGGER = """
CREATE TRIGGER trg_trip_sheet_immutable
BEFORE UPDATE OR DELETE ON trip_sheets
FOR EACH ROW EXECUTE FUNCTION reject_closed_trip_sheet_change();
"""


def upgrade() -> None:
    trip_status = sa.Enum("draft", "closed", name="trip_status")
    import_status = sa.Enum(
        "pending", "processing", "completed", "failed", name="import_status"
    )
    trip_status.create(op.get_bind(), checkfirst=True)
    import_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "trip_sheets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("driver_id", sa.Integer(), nullable=False),
        sa.Column("departure_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("arrival_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("start_km", sa.Integer(), nullable=False),
        sa.Column("end_km", sa.Integer(), nullable=True),
        sa.Column("purpose", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            sa.Enum("draft", "closed", name="trip_status", create_type=False),
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
        sa.CheckConstraint("end_km IS NULL OR end_km > start_km", name="ck_trip_km"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"]),
    )
    op.create_index("ix_trip_sheets_vehicle_id", "trip_sheets", ["vehicle_id"])
    op.create_index("ix_trip_sheets_driver_id", "trip_sheets", ["driver_id"])

    op.create_table(
        "import_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "processing", "completed", "failed",
                name="import_status", create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imported_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_report", sa.JSON(), nullable=True),
        sa.Column("uploaded_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
    )

    op.create_table(
        "fuel_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("liters", sa.Numeric(8, 2), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        sa.Column("odometer_reported", sa.Integer(), nullable=True),
        sa.Column("station", sa.String(length=120), nullable=True),
        sa.Column("import_batch_id", sa.Integer(), nullable=True),
        sa.Column("is_suspect", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("suspect_reason", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.ForeignKeyConstraint(["import_batch_id"], ["import_batches.id"]),
    )
    op.create_index(
        "ix_fuel_transactions_vehicle_id", "fuel_transactions", ["vehicle_id"]
    )
    op.create_index(
        "ix_fuel_transactions_import_batch_id", "fuel_transactions", ["import_batch_id"]
    )

    op.execute(_TRIGGER_FN)
    op.execute(_TRIGGER)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_trip_sheet_immutable ON trip_sheets")
    op.execute("DROP FUNCTION IF EXISTS reject_closed_trip_sheet_change")
    op.drop_index("ix_fuel_transactions_import_batch_id", table_name="fuel_transactions")
    op.drop_index("ix_fuel_transactions_vehicle_id", table_name="fuel_transactions")
    op.drop_table("fuel_transactions")
    op.drop_table("import_batches")
    op.drop_index("ix_trip_sheets_driver_id", table_name="trip_sheets")
    op.drop_index("ix_trip_sheets_vehicle_id", table_name="trip_sheets")
    op.drop_table("trip_sheets")
    sa.Enum(name="import_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="trip_status").drop(op.get_bind(), checkfirst=True)
