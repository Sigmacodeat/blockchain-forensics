"""partner_affiliate

Revision ID: 20251020_partner_affiliate
Revises: 20251019_link_tracking
Create Date: 2025-10-23 20:15:00.000000

Partner-/Affiliate-System: Accounts, Referrals, Kommissionen, Auszahlungen
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251020_partner_affiliate"
down_revision = "20251019_link_tracking"
branch_labels = None
depends_on = None


def upgrade():
    # partner_accounts
    op.create_table(
        "partner_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("referral_code", sa.Text(), nullable=False),
        sa.Column("commission_rate", sa.Numeric(5, 2), nullable=False, server_default="20.0"),
        sa.Column("recurring_rate", sa.Numeric(5, 2), nullable=False, server_default="20.0"),
        sa.Column("cookie_duration_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("min_payout_usd", sa.Numeric(12, 2), nullable=False, server_default="50.0"),
        sa.Column("payout_method", sa.Text(), nullable=True),
        sa.Column("payout_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("referral_code")
    )
    op.create_foreign_key(
        "partner_accounts_user_id_fkey",
        "partner_accounts",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_partner_accounts_is_active", "partner_accounts", ["is_active"])
    op.create_index("ix_partner_accounts_created_at", "partner_accounts", ["created_at"])

    # partner_referrals
    op.create_table(
        "partner_referrals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("referred_user_id", sa.String(length=255), nullable=False),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("tracking_id", sa.Text(), nullable=True),
        sa.Column("first_touch_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_touch_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("attributions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_foreign_key(
        "partner_referrals_partner_id_fkey",
        "partner_referrals",
        "partner_accounts",
        ["partner_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "partner_referrals_referred_user_id_fkey",
        "partner_referrals",
        "users",
        ["referred_user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_partner_referrals_partner_id", "partner_referrals", ["partner_id"])
    op.create_index("ix_partner_referrals_referred_user_id", "partner_referrals", ["referred_user_id"])
    op.create_index("ix_partner_referrals_created_at", "partner_referrals", ["created_at"])

    # partner_commissions
    op.create_table(
        "partner_commissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("referred_user_id", sa.String(length=255), nullable=True),
        sa.Column("payment_id", sa.Integer(), nullable=True),
        sa.Column("order_id", sa.Text(), nullable=True),
        sa.Column("plan_name", sa.Text(), nullable=True),
        sa.Column("amount_usd", sa.Numeric(12, 2), nullable=False),
        sa.Column("commission_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("commission_usd", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_foreign_key(
        "partner_commissions_partner_id_fkey",
        "partner_commissions",
        "partner_accounts",
        ["partner_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "partner_commissions_referred_user_id_fkey",
        "partner_commissions",
        "users",
        ["referred_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_partner_commissions_partner_id", "partner_commissions", ["partner_id"])
    op.create_index("ix_partner_commissions_referred_user_id", "partner_commissions", ["referred_user_id"])
    op.create_index("ix_partner_commissions_status", "partner_commissions", ["status"])
    op.create_index("ix_partner_commissions_event_time", "partner_commissions", ["event_time"])

    # partner_payouts
    op.create_table(
        "partner_payouts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount_usd", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="requested"),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tx_ref", sa.Text(), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_foreign_key(
        "partner_payouts_partner_id_fkey",
        "partner_payouts",
        "partner_accounts",
        ["partner_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_partner_payouts_partner_id", "partner_payouts", ["partner_id"])
    op.create_index("ix_partner_payouts_status", "partner_payouts", ["status"])
    op.create_index("ix_partner_payouts_requested_at", "partner_payouts", ["requested_at"])

    # users: referral columns
    op.add_column(
        "users",
        sa.Column("referred_by_partner_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("referred_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "users_referred_by_partner_id_fkey",
        "users",
        "partner_accounts",
        ["referred_by_partner_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_users_referred_by_partner_id", "users", ["referred_by_partner_id"])


def downgrade():
    # users referral columns + fkey
    op.drop_index("ix_users_referred_by_partner_id", table_name="users")
    op.drop_constraint("users_referred_by_partner_id_fkey", "users", type_="foreignkey")
    op.drop_column("users", "referred_at")
    op.drop_column("users", "referred_by_partner_id")

    # partner_payouts
    op.drop_index("ix_partner_payouts_requested_at", table_name="partner_payouts")
    op.drop_index("ix_partner_payouts_status", table_name="partner_payouts")
    op.drop_index("ix_partner_payouts_partner_id", table_name="partner_payouts")
    op.drop_constraint("partner_payouts_partner_id_fkey", "partner_payouts", type_="foreignkey")
    op.drop_table("partner_payouts")

    # partner_commissions
    op.drop_index("ix_partner_commissions_event_time", table_name="partner_commissions")
    op.drop_index("ix_partner_commissions_status", table_name="partner_commissions")
    op.drop_index("ix_partner_commissions_referred_user_id", table_name="partner_commissions")
    op.drop_index("ix_partner_commissions_partner_id", table_name="partner_commissions")
    op.drop_constraint("partner_commissions_referred_user_id_fkey", "partner_commissions", type_="foreignkey")
    op.drop_constraint("partner_commissions_partner_id_fkey", "partner_commissions", type_="foreignkey")
    op.drop_table("partner_commissions")

    # partner_referrals
    op.drop_index("ix_partner_referrals_created_at", table_name="partner_referrals")
    op.drop_index("ix_partner_referrals_referred_user_id", table_name="partner_referrals")
    op.drop_index("ix_partner_referrals_partner_id", table_name="partner_referrals")
    op.drop_constraint("partner_referrals_referred_user_id_fkey", "partner_referrals", type_="foreignkey")
    op.drop_constraint("partner_referrals_partner_id_fkey", "partner_referrals", type_="foreignkey")
    op.drop_table("partner_referrals")

    # partner_accounts
    op.drop_index("ix_partner_accounts_created_at", table_name="partner_accounts")
    op.drop_index("ix_partner_accounts_is_active", table_name="partner_accounts")
    op.drop_constraint("partner_accounts_user_id_fkey", "partner_accounts", type_="foreignkey")
    op.drop_table("partner_accounts")
