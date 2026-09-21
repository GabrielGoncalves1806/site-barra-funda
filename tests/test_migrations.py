"""Testes das migrações do Alembic."""
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parent.parent


def _config(db_path: Path) -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def _legacy_db(tmp_path: Path) -> tuple[Config, sa.Engine]:
    """Banco como o antigo create_all deixava: tabelas com dados, sem alembic_version."""
    db = tmp_path / "legado.db"
    cfg = _config(db)
    command.upgrade(cfg, "0001")
    engine = sa.create_engine(f"sqlite:///{db}")
    with engine.begin() as conn:
        conn.execute(sa.text("DROP TABLE alembic_version"))
        conn.execute(sa.text(
            "INSERT INTO notice (title, text, level, author, date, created_at) "
            "VALUES ('Aviso antigo', 't', 'normal', 'Síndico', '', '2026-01-01 00:00:00')"
        ))
    return cfg, engine


def test_migracoes_batem_com_os_models(tmp_path):
    cfg = _config(tmp_path / "novo.db")
    command.upgrade(cfg, "head")
    command.check(cfg)  # falha se algum model tiver algo que as migrações não criam


def test_banco_novo_nao_ganha_condominio(tmp_path):
    db = tmp_path / "novo.db"
    command.upgrade(_config(db), "head")
    with sa.create_engine(f"sqlite:///{db}").connect() as conn:
        assert conn.execute(sa.text("SELECT COUNT(*) FROM condominium")).scalar_one() == 0


def test_banco_antigo_tem_dados_adotados_pelo_barra_funda(tmp_path):
    cfg, engine = _legacy_db(tmp_path)
    command.upgrade(cfg, "head")
    with engine.connect() as conn:
        condo_id = conn.execute(
            sa.text("SELECT id FROM condominium WHERE slug = 'barra-funda'")
        ).scalar_one()
        assert conn.execute(sa.text("SELECT condominium_id FROM notice")).scalar_one() == condo_id


def test_adocao_aproveita_o_hash_de_senha_antigo(tmp_path, monkeypatch):
    old_hash = "$2b$12$abcdefghijklmnopqrstuuMQx1Yk6r0DdOqBpo5fLkM6VxJm4yK3W"
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", old_hash)
    cfg, engine = _legacy_db(tmp_path)
    command.upgrade(cfg, "head")
    with engine.connect() as conn:
        assert conn.execute(sa.text("SELECT password_hash FROM condominium")).scalar_one() == old_hash
