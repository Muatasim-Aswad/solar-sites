import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("email", sa.Text(collation="NOCASE"), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.CheckConstraint("length(trim(email)) > 0"),
        sa.CheckConstraint("length(password_hash) > 0"),
        sqlite_strict=True,
    )
    op.create_table(
        "sessions",
        sa.Column("session_token_hash", sa.LargeBinary(), primary_key=True),
        sa.Column(
            "user_id", sa.Text(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("csrf_token", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=False),
        sa.CheckConstraint("length(session_token_hash) = 32"),
        sa.CheckConstraint("length(csrf_token) > 0"),
        sa.CheckConstraint("expires_at > created_at"),
        sqlite_strict=True,
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"])
    op.create_table(
        "sites",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "user_id", sa.Text(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("client_name", sa.Text(), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("latitude", sa.REAL(), nullable=False),
        sa.Column("longitude", sa.REAL(), nullable=False),
        sa.Column("roof_area_m2", sa.REAL()),
        sa.Column("peak_kwp", sa.REAL(), nullable=False),
        sa.CheckConstraint("length(trim(client_name)) BETWEEN 1 AND 200"),
        sa.CheckConstraint("length(trim(address)) BETWEEN 1 AND 500"),
        sa.CheckConstraint("latitude BETWEEN -90 AND 90"),
        sa.CheckConstraint("longitude BETWEEN -180 AND 180"),
        sa.CheckConstraint("roof_area_m2 IS NULL OR roof_area_m2 > 0 AND roof_area_m2 <= 1000000"),
        sa.CheckConstraint("peak_kwp > 0 AND peak_kwp <= 100000"),
        sqlite_strict=True,
    )
    op.create_index("ix_sites_user_id", "sites", ["user_id"])


def downgrade() -> None:
    op.drop_table("sites")
    op.drop_table("sessions")
    op.drop_table("users")
