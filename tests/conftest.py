"""Fixtures compartilhadas: app com banco em memória + helpers de auth."""
import os

import bcrypt

# Configurar env ANTES de importar main (que valida na carga)
TEST_PASSWORD = "test-password-123"
os.environ["ADMIN_PASSWORD_HASH"] = bcrypt.hashpw(
    TEST_PASSWORD.encode(), bcrypt.gensalt(rounds=4)
).decode()
os.environ["SECRET_KEY"] = "test-secret-key-only-for-tests-not-secure"
os.environ["ALLOWED_ORIGINS"] = "http://testserver"

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

import main
from database import get_session


@pytest.fixture
def client():
    """TestClient com banco SQLite em memória e isolado por teste."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)

    def override_get_session():
        with Session(test_engine) as session:
            yield session

    main.app.dependency_overrides[get_session] = override_get_session

    # Reset rate limiter entre testes
    if hasattr(main.app.state, "limiter"):
        main.app.state.limiter.reset()

    with TestClient(main.app) as c:
        yield c

    main.app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    """TestClient já autenticado."""
    res = client.post("/api/auth", json={"password": TEST_PASSWORD})
    assert res.status_code == 200, f"Login na fixture falhou: {res.text}"
    return client
