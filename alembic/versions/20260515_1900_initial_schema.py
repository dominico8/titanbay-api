"""initial schema

Revision ID: a63e92036391
Revises:
Create Date: 2026-05-15 19:00:38.591622+00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = 'a63e92036391'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    fund_status = postgresql.ENUM(
        'Fundraising', 'Investing', 'Closed',
        name='fund_status',
    )
    fund_status.create(op.get_bind(), checkfirst=True)

    investor_type = postgresql.ENUM(
        'Individual', 'Institution', 'Family Office',
        name='investor_type',
    )
    investor_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'funds',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
        ),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('vintage_year', sa.Integer(), nullable=False),
        sa.Column('target_size_usd', sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column(
            'status',
            postgresql.ENUM(
                'Fundraising', 'Investing', 'Closed',
                name='fund_status',
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            'created_at',
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.CheckConstraint('target_size_usd > 0', name='ck_funds_target_size_usd_positive'),
        sa.CheckConstraint(
            'vintage_year BETWEEN 1900 AND 2100',
            name='ck_funds_vintage_year_range',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'investors',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
        ),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column(
            'investor_type',
            postgresql.ENUM(
                'Individual', 'Institution', 'Family Office',
                name='investor_type',
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column(
            'created_at',
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_table(
        'investments',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
        ),
        sa.Column('investor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fund_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount_usd', sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column('investment_date', sa.Date(), nullable=False),
        sa.Column(
            'created_at',
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.CheckConstraint('amount_usd > 0', name='ck_investments_amount_usd_positive'),
        sa.ForeignKeyConstraint(['fund_id'], ['funds.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['investor_id'], ['investors.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_investments_fund_id', 'investments', ['fund_id'], unique=False)
    op.create_index('ix_investments_investor_id', 'investments', ['investor_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_investments_investor_id', table_name='investments')
    op.drop_index('ix_investments_fund_id', table_name='investments')
    op.drop_table('investments')
    op.drop_table('investors')
    op.drop_table('funds')

    op.execute('DROP TYPE IF EXISTS investor_type')
    op.execute('DROP TYPE IF EXISTS fund_status')
