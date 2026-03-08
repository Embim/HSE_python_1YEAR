"""Initial schema with timezone-aware timestamps.

Works for both:
  - fresh deployments (creates tables)
  - existing deployments with TIMESTAMP columns (alters to TIMESTAMPTZ)

Revision ID: 001
Revises:
Create Date: 2026-03-08
"""
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CREATE TABLE IF NOT EXISTS — safe for both fresh and existing deployments
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          SERIAL      NOT NULL PRIMARY KEY,
            username    VARCHAR(50) NOT NULL UNIQUE,
            email       VARCHAR(100) NOT NULL UNIQUE,
            hashed_password VARCHAR NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id           SERIAL      NOT NULL PRIMARY KEY,
            original_url VARCHAR     NOT NULL,
            short_code   VARCHAR(20) NOT NULL UNIQUE,
            user_id      INTEGER     REFERENCES users(id),
            created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_at   TIMESTAMPTZ,
            last_used_at TIMESTAMPTZ,
            click_count  INTEGER     NOT NULL DEFAULT 0,
            is_deleted   BOOLEAN     NOT NULL DEFAULT false
        )
    """)

    # Ensure all timestamp columns are TIMESTAMPTZ.
    # If the column is already TIMESTAMPTZ this is a no-op.
    # If it was TIMESTAMP (naive), existing values are reinterpreted as UTC.
    op.execute("""
        ALTER TABLE users
            ALTER COLUMN created_at TYPE TIMESTAMPTZ
                USING created_at AT TIME ZONE 'UTC'
    """)
    op.execute("""
        ALTER TABLE links
            ALTER COLUMN created_at  TYPE TIMESTAMPTZ
                USING created_at  AT TIME ZONE 'UTC',
            ALTER COLUMN expires_at  TYPE TIMESTAMPTZ
                USING expires_at  AT TIME ZONE 'UTC',
            ALTER COLUMN last_used_at TYPE TIMESTAMPTZ
                USING last_used_at AT TIME ZONE 'UTC'
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS links")
    op.execute("DROP TABLE IF EXISTS users")
