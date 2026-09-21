"""Copia os dados do SQLite local (data.db) pro Postgres do DATABASE_URL.

Uso (com o DATABASE_URL do Neon no .env):
    python scripts/migrate_sqlite_to_postgres.py [caminho/do/data.db]

Tudo roda numa transação só: se qualquer linha falhar, nada é gravado.
Recusa rodar se o destino já tiver dados, pra não duplicar nada.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from sqlmodel import Session, create_engine, select

from database import create_db_and_tables, engine as target_engine
from models import Area, FAQ, Notice, Sale

MODELS = [Notice, Sale, Area, FAQ]


def main() -> None:
    sqlite_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data.db"
    if not sqlite_path.exists():
        print(f"Arquivo não encontrado: {sqlite_path}")
        sys.exit(1)

    if target_engine.dialect.name != "postgresql":
        print("DATABASE_URL não aponta pra um Postgres. Confira o .env.")
        sys.exit(1)

    source_engine = create_engine(f"sqlite:///{sqlite_path}")
    create_db_and_tables()

    with Session(source_engine) as source, Session(target_engine) as target:
        for model in MODELS:
            if target.exec(select(model)).first():
                print(f"Tabela '{model.__tablename__}' já tem dados no destino. Abortando.")
                sys.exit(1)

        for model in MODELS:
            rows = source.exec(select(model)).all()
            for row in rows:
                target.add(model(**row.model_dump()))
            print(f"{model.__tablename__}: {len(rows)} linha(s)")

        # Os ids foram copiados na mão, então as sequences do Postgres ainda
        # estão em 1 — sem isso o próximo INSERT do admin bate em id duplicado.
        target.flush()
        for model in MODELS:
            table = model.__tablename__
            target.connection().execute(text(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                f"COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM {table}"
            ))

        target.commit()

    print("Migração concluída.")


if __name__ == "__main__":
    main()
