"""multi condominium: tabelas condominium/domain e condominium_id em tudo

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-21 20:40:58.331372

"""
import os
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # noqa: F401 (tipos como AutoString aparecem nas migrações)
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONTENT_TABLES = ("notice", "sale", "area", "faq")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('condominium',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sqlmodel.sql.sqltypes.AutoString(length=60), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
    sa.Column('password_hash', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('config', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug')
    )
    op.create_table('domain',
    sa.Column('host', sqlmodel.sql.sqltypes.AutoString(length=253), nullable=False),
    sa.Column('condominium_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['condominium_id'], ['condominium.id'], ),
    sa.PrimaryKeyConstraint('host')
    )
    with op.batch_alter_table('domain', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_domain_condominium_id'), ['condominium_id'], unique=False)

    # A coluna nasce aceitando nulo, é preenchida e só então vira NOT NULL —
    # direto como NOT NULL quebraria em tabela que já tem linhas.
    for table in CONTENT_TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(sa.Column('condominium_id', sa.Integer(), nullable=True))

    _adopt_existing_rows()

    for table in CONTENT_TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column('condominium_id', existing_type=sa.Integer(), nullable=False)
            batch_op.create_index(batch_op.f(f'ix_{table}_condominium_id'), ['condominium_id'], unique=False)
            batch_op.create_foreign_key(f'fk_{table}_condominium_id', 'condominium', ['condominium_id'], ['id'])


def _adopt_existing_rows() -> None:
    """Linhas de antes do multi-condomínio são do Barra Funda, o único que existia.

    Banco novo (sem linhas) não ganha condomínio nenhum. O hash de senha da env
    antiga mantém o login funcionando até alguém rodar `manage.py set-password`;
    sem ele, "!" não bate com senha nenhuma.
    """
    bind = op.get_bind()
    if not any(bind.execute(sa.text(f"SELECT 1 FROM {t} LIMIT 1")).first() for t in CONTENT_TABLES):
        return

    bind.execute(
        sa.text(
            "INSERT INTO condominium (slug, name, password_hash, active, config, created_at) "
            "VALUES (:slug, :name, :password_hash, :active, '{}', :created_at)"
        ).bindparams(sa.bindparam("created_at", type_=sa.DateTime())),
        {
            "slug": "barra-funda",
            "name": "Plano&Estação Barra Funda",
            "password_hash": os.environ.get("ADMIN_PASSWORD_HASH") or "!",
            "active": True,
            "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
        },
    )
    condominium_id = bind.execute(
        sa.text("SELECT id FROM condominium WHERE slug = 'barra-funda'")
    ).scalar_one()
    for table in CONTENT_TABLES:
        bind.execute(sa.text(f"UPDATE {table} SET condominium_id = :id"), {"id": condominium_id})


def downgrade() -> None:
    """Downgrade schema."""
    for table in CONTENT_TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_constraint(f'fk_{table}_condominium_id', type_='foreignkey')
            batch_op.drop_index(batch_op.f(f'ix_{table}_condominium_id'))
            batch_op.drop_column('condominium_id')

    with op.batch_alter_table('domain', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_domain_condominium_id'))

    op.drop_table('domain')
    op.drop_table('condominium')
