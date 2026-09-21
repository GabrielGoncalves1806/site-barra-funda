import os

from dotenv import load_dotenv
from sqlalchemy import event
from sqlmodel import Session, create_engine

# A URL é lida na importação, então o .env precisa estar carregado aqui —
# senão scripts como seed.py caem no SQLite local sem avisar.
load_dotenv()


def _normalize_url(url: str) -> str:
    """Neon/Vercel entregam a URL como postgresql:// (ou postgres://), que o
    SQLAlchemy associa ao psycopg2. A gente usa o psycopg 3."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


# Em produção aponta pro Postgres (Neon). Sem a env, cai no SQLite local
# pra não quebrar dev/testes.
DATABASE_URL = _normalize_url(os.getenv("DATABASE_URL", "sqlite:///data.db"))

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        """WAL + busy_timeout: evita 'database is locked' com o admin editando
        enquanto páginas públicas leem ao mesmo tempo."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()
else:
    # O Neon desliga o compute depois de 5 min parado e derruba as conexões
    # abertas; pool_pre_ping testa a conexão antes de usar e reconecta.
    engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)


def get_session():
    with Session(engine) as session:
        yield session
