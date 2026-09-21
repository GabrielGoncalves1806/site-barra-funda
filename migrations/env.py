"""Ambiente do Alembic.

A URL do banco vem do DATABASE_URL (mesma do app). Quem chama o Alembic por
código (os testes) pode sobrescrever com a opção `sqlalchemy.url`.
"""
from alembic import context
from sqlalchemy import create_engine
from sqlmodel import SQLModel

import models  # noqa: F401 (registra as tabelas no metadata)
from database import engine as app_engine

config = context.config
target_metadata = SQLModel.metadata


def run_migrations_online() -> None:
    url = config.get_main_option("sqlalchemy.url")
    connectable = create_engine(url) if url else app_engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite não faz ALTER de constraint; o modo batch recria a tabela.
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise SystemExit("Modo offline não é suportado; rode com um banco acessível.")

run_migrations_online()
