"""Testes de autenticação: login, logout, /api/me, rate limit."""
from tests.conftest import TEST_PASSWORD


def test_login_sucesso(client):
    res = client.post("/api/auth", json={"password": TEST_PASSWORD})
    assert res.status_code == 200
    assert res.json() == {"ok": True}
    assert "admin_session" in res.cookies


def test_login_falha_senha_errada(client):
    res = client.post("/api/auth", json={"password": "errada"})
    assert res.status_code == 401


def test_login_falha_payload_invalido(client):
    res = client.post("/api/auth", json={"password": 123})
    assert res.status_code == 401


def test_me_sem_cookie_401(client):
    res = client.get("/api/me")
    assert res.status_code == 401


def test_me_com_cookie_ok(auth_client):
    res = auth_client.get("/api/me")
    assert res.status_code == 200
    assert res.json() == {"subject": "admin"}


def test_logout_limpa_cookie(auth_client):
    res = auth_client.post("/api/logout")
    assert res.status_code == 200
    # Após logout, /api/me deve voltar a 401
    res = auth_client.get("/api/me", cookies={})
    # TestClient mantém cookies por padrão; força sem
    auth_client.cookies.clear()
    res = auth_client.get("/api/me")
    assert res.status_code == 401


def test_rate_limit_login(client):
    # 5 tentativas permitidas, 6ª bloqueia
    for _ in range(5):
        res = client.post("/api/auth", json={"password": "errada"})
        assert res.status_code == 401
    res = client.post("/api/auth", json={"password": "errada"})
    assert res.status_code == 429
