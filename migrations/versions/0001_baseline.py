"""baseline: as 4 tabelas como existiam antes do Alembic

Revision ID: 0001
Revises: 
Create Date: 2026-09-21 20:37:28.003761

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # noqa: F401 (tipos como AutoString aparecem nas migrações)


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Bancos criados antes do Alembic (pelo antigo create_all no startup) já
    # têm essas tabelas: aí a baseline só é marcada como aplicada.
    if sa.inspect(op.get_bind()).has_table("notice"):
        return

    op.create_table('area',
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(length=150), nullable=False),
    sa.Column('slug', sqlmodel.sql.sqltypes.AutoString(length=80), nullable=False),
    sa.Column('tag', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=2000), nullable=False),
    sa.Column('image', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
    sa.Column('highlights', sqlmodel.sql.sqltypes.AutoString(length=3000), nullable=False),
    sa.Column('meta', sqlmodel.sql.sqltypes.AutoString(length=2000), nullable=False),
    sa.Column('rules', sqlmodel.sql.sqltypes.AutoString(length=5000), nullable=False),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('faq',
    sa.Column('question', sqlmodel.sql.sqltypes.AutoString(length=300), nullable=False),
    sa.Column('answer', sqlmodel.sql.sqltypes.AutoString(length=3000), nullable=False),
    sa.Column('icon', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
    sa.Column('anchor_id', sqlmodel.sql.sqltypes.AutoString(length=80), nullable=False),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('notice',
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
    sa.Column('text', sqlmodel.sql.sqltypes.AutoString(length=5000), nullable=False),
    sa.Column('level', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
    sa.Column('author', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('date', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sale',
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(length=150), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=2000), nullable=False),
    sa.Column('price', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('image', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
    sa.Column('seller', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('whatsapp', sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('sale')
    op.drop_table('notice')
    op.drop_table('faq')
    op.drop_table('area')
