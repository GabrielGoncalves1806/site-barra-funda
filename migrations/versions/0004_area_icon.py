"""area icon: emoji de cada área (usado na grade da Início)

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-21 23:28:14.045757

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # noqa: F401 (tipos como AutoString aparecem nas migrações)


# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default preenche as áreas que já existem (NOT NULL sem default
    # quebraria numa tabela com linhas).
    with op.batch_alter_table('area', schema=None) as batch_op:
        batch_op.add_column(sa.Column('icon', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False, server_default='🏢'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('area', schema=None) as batch_op:
        batch_op.drop_column('icon')
