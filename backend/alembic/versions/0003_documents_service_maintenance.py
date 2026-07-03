"""documents, service_records, maintenance_rules

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-03

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    document_type = sa.Enum("RCA", "CASCO", "ITP", "Rovinieta", name="document_type")
    document_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "vehicle_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "RCA", "CASCO", "ITP", "Rovinieta",
                name="document_type", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("series_number", sa.String(length=50), nullable=False),
        sa.Column("issuer", sa.String(length=120), nullable=True),
        sa.Column("cost", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("cost >= 0", name="ck_document_cost_nonneg"),
        sa.CheckConstraint("expiry_date > issue_date", name="ck_document_dates"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
    )
    op.create_index(
        "ix_vehicle_documents_vehicle_id", "vehicle_documents", ["vehicle_id"]
    )

    op.create_table(
        "service_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("km_at_service", sa.Integer(), nullable=False),
        sa.Column("work_description", sa.Text(), nullable=False),
        sa.Column("parts_replaced", sa.Text(), nullable=True),
        sa.Column("cost", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("cost >= 0", name="ck_service_cost_nonneg"),
        sa.CheckConstraint("km_at_service >= 0", name="ck_service_km_nonneg"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
    )
    op.create_index(
        "ix_service_records_vehicle_id", "service_records", ["vehicle_id"]
    )

    op.create_table(
        "maintenance_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False, server_default="Service"),
        sa.Column("interval_km", sa.Integer(), nullable=False),
        sa.Column("interval_months", sa.Integer(), nullable=False),
        sa.Column("last_service_km", sa.Integer(), nullable=False),
        sa.Column("last_service_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("interval_km > 0", name="ck_rule_interval_km_positive"),
        sa.CheckConstraint("interval_months > 0", name="ck_rule_interval_months_positive"),
        sa.CheckConstraint("last_service_km >= 0", name="ck_rule_last_km_nonneg"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
    )
    op.create_index(
        "ix_maintenance_rules_vehicle_id", "maintenance_rules", ["vehicle_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_maintenance_rules_vehicle_id", table_name="maintenance_rules")
    op.drop_table("maintenance_rules")
    op.drop_index("ix_service_records_vehicle_id", table_name="service_records")
    op.drop_table("service_records")
    op.drop_index("ix_vehicle_documents_vehicle_id", table_name="vehicle_documents")
    op.drop_table("vehicle_documents")
    sa.Enum(name="document_type").drop(op.get_bind(), checkfirst=True)
