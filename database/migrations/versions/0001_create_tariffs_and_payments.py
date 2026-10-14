"""Создаёт таблицы tariffs и payments.

Revision ID: 0001
Revises:
Create Date: 2026-10-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Создаёт таблицы tariffs и payments с ограничениями и индексами."""
    op.create_table(
        "tariffs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=64), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_tariffs"),
        sa.UniqueConstraint("code", name="uq_tariffs_code"),
        sa.CheckConstraint("price > 0", name="price_positive"),
    )
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("tariff_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("discount", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(length=16), nullable=False),
        sa.Column("installment_months", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tariff_id"],
            ["tariffs.id"],
            name="fk_payments_tariff_id_tariffs",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_payments"),
        sa.UniqueConstraint("idempotency_key", name="uq_payments_idempotency_key"),
        sa.CheckConstraint("amount >= 0", name="amount_non_negative"),
        sa.CheckConstraint("discount >= 0", name="discount_non_negative"),
        sa.CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed', 'refunded')",
            name="status_values",
        ),
        sa.CheckConstraint("method IN ('card', 'sbp', 'installment')", name="method_values"),
        sa.CheckConstraint(
            "(method = 'installment' AND installment_months IN (3, 6, 12))"
            " OR (method <> 'installment' AND installment_months IS NULL)",
            name="installment_months_consistency",
        ),
    )
    op.create_index("ix_payments_email", "payments", ["email"])
    op.create_index("ix_payments_status", "payments", ["status"])
    op.create_index("ix_payments_tariff_id", "payments", ["tariff_id"])


def downgrade() -> None:
    """Удаляет таблицы payments и tariffs вместе с индексами."""
    op.drop_table("payments")
    op.drop_table("tariffs")
