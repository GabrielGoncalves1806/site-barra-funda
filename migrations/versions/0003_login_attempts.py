"""login attempts: tentativas de login pro limite por IP

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-21 21:37:13.098770

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # noqa: F401 (tipos como AutoString aparecem nas migrações)


# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('loginattempt',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ip', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('loginattempt', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_loginattempt_created_at'), ['created_at'], unique=False)



def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('loginattempt', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_loginattempt_created_at'))

    op.drop_table('loginattempt')
