"""Troca de senha pelo próprio admin do condomínio."""
from tests.conftest import TEST_PASSWORD


def _change(client, current, new):
    return client.post("/api/password", json={"current_password": current, "new_password": new})


def test_trocar_senha_exige_login(client):
    assert _change(client, TEST_PASSWORD, "senha-nova-123").status_code == 401


def test_senha_atual_errada_e_recusada(auth_client):
    assert _change(auth_client, "errada", "senha-nova-123").status_code == 400


def test_senha_nova_curta_e_recusada(auth_client):
    assert _change(auth_client, TEST_PASSWORD, "curta").status_code == 422


def test_trocar_senha_vale_no_proximo_login(auth_client):
    assert _change(auth_client, TEST_PASSWORD, "senha-nova-123").status_code == 200
    auth_client.cookies.clear()
    assert auth_client.post("/api/auth", json={"password": TEST_PASSWORD}).status_code == 401
    assert auth_client.post("/api/auth", json={"password": "senha-nova-123"}).status_code == 200


def test_trocar_senha_nao_mexe_em_outro_condominio(auth_client, client_b):
    from tests.conftest import OTHER_PASSWORD
    _change(auth_client, TEST_PASSWORD, "senha-nova-123")
    assert client_b.post("/api/auth", json={"password": OTHER_PASSWORD}).status_code == 200
