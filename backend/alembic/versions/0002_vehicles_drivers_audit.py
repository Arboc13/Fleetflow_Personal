"""vehicles, drivers, audit_log

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-03

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    fuel_type = sa.Enum(
        "petrol", "diesel", "electric", "hybrid", "lpg", name="fuel_type"
    )
    vehicle_status = sa.Enum(
        "active", "in_service", "unavailable", name="vehicle_status"
    )
    fuel_type.create(op.get_bind(), checkfirst=True)
    vehicle_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plate", sa.String(length=20), nullable=False),
        sa.Column("vin", sa.String(length=17), nullable=False),
        sa.Column("make", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column(
            "fuel_type",
            sa.Enum(
                "petrol", "diesel", "electric", "hybrid", "lpg",
                name="fuel_type", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("current_km", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.Enum(
                "active", "in_service", "unavailable",
                name="vehicle_status", create_type=False,
            ),
            nullable=False,
            server_default="active",
        ),
        sa.Column("tank_capacity_l", sa.Float(), nullable=False),
        sa.Column("fuel_card_number", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("current_km >= 0", name="ck_vehicle_km_nonneg"),
        sa.CheckConstraint("tank_capacity_l > 0", name="ck_vehicle_tank_positive"),
    )
    op.create_index("ix_vehicles_plate", "vehicles", ["plate"], unique=True)
    op.create_index("ix_vehicles_vin", "vehicles", ["vin"], unique=True)

    op.create_table(
        "drivers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("cnp_encrypted", sa.String(length=255), nullable=False),
        sa.Column("license_number", sa.String(length=30), nullable=False),
        sa.Column("license_series", sa.String(length=10), nullable=True),
        sa.Column("license_category", sa.String(length=20), nullable=False),
        sa.Column("license_expiry", sa.Date(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id", name="uq_drivers_user_id"),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("field", sa.String(length=50), nullable=False),
        sa.Column("old_value", sa.String(length=255), nullable=True),
        sa.Column("new_value", sa.String(length=255), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("drivers")
    op.drop_index("ix_vehicles_vin", table_name="vehicles")
    op.drop_index("ix_vehicles_plate", table_name="vehicles")
    op.drop_table("vehicles")
    sa.Enum(name="vehicle_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="fuel_type").drop(op.get_bind(), checkfirst=True)
