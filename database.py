import os

from sqlalchemy import event
from sqlmodel import SQLModel, Session, create_engine

# Configurável via env pra produção apontar pra um path fora da árvore do
# git (deploy_vps.py faz isso) — um `git pull` nunca deve poder sobrescrever
# o banco. Default local continua o mesmo pra não quebrar dev/testes.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data.db")

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """WAL + busy_timeout: evita 'database is locked' com o admin editando
    enquanto páginas públicas leem ao mesmo tempo."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
