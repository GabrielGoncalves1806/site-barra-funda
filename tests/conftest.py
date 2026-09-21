"""Fixtures compartilhadas: app com banco em memória, dois condomínios e helpers de auth.

O condomínio A responde no host padrão do TestClient ("testserver"), então os
testes que não ligam pra multi-condomínio continuam simples. O B responde em
"b.test".
"""
import os

import bcrypt

# Configurar env ANTES de importar main
os.environ["SECRET_KEY"] = "test-secret-key-only-for-tests-not-secure"
os.environ["COOKIE_SECURE"] = "false"
# Sem isso, o DATABASE_URL do .env (Neon) seria usado no startup do app
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

import main
from database import get_session
from models import Condominium, Domain

TEST_PASSWORD = "test-password-123"
OTHER_PASSWORD = "other-password-456"
HOST_A = "testserver"
HOST_B = "b.test"


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=4)).decode()


@pytest.fixture
def engine():
    """SQLite em memória, isolado por teste, com os condomínios A e B."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        a = Condominium(slug="condo-a", name="Condomínio A", password_hash=_hash(TEST_PASSWORD))
        b = Condominium(slug="condo-b", name="Condomínio B", password_hash=_hash(OTHER_PASSWORD))
        session.add_all([a, b])
        session.commit()
        session.add_all([
            Domain(host=HOST_A, condominium_id=a.id),
            Domain(host=HOST_B, condominium_id=b.id),
        ])
        session.commit()
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def app(engine):
    def override_get_session():
        with Session(engine) as session:
            yield session

    main.app.dependency_overrides[get_session] = override_get_session

    # Reset rate limiter entre testes
    if hasattr(main.app.state, "limiter"):
        main.app.state.limiter.reset()

    yield main.app
    main.app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    """TestClient do condomínio A."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_b(app):
    """TestClient do condomínio B."""
    with TestClient(app, base_url=f"http://{HOST_B}") as c:
        yield c


@pytest.fixture
def auth_client(client):
    """TestClient do condomínio A, já autenticado."""
    res = client.post("/api/auth", json={"password": TEST_PASSWORD})
    assert res.status_code == 200, f"Login na fixture falhou: {res.text}"
    return client


@pytest.fixture
def auth_client_b(client_b):
    """TestClient do condomínio B, já autenticado."""
    res = client_b.post("/api/auth", json={"password": OTHER_PASSWORD})
    assert res.status_code == 200, f"Login na fixture falhou: {res.text}"
    return client_b
