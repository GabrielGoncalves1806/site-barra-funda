"""Testes do CLI de super-admin (manage.py)."""
import bcrypt
import pytest

import manage
from tests.conftest import HOST_A, TEST_PASSWORD


def test_create_condominium_guarda_hash_da_senha(session):
    condo = manage.create_condominium(session, "novo-condo", "Novo Condomínio", "senha-forte-123")
    assert condo.id is not None
    assert bcrypt.checkpw(b"senha-forte-123", condo.password_hash.encode())


@pytest.mark.parametrize("slug", ["Barra Funda", "barra_funda", "-barra", "barra-", ""])
def test_create_condominium_rejeita_slug_invalido(session, slug):
    with pytest.raises(ValueError):
        manage.create_condominium(session, slug, "X", "senha-forte-123")


def test_create_condominium_rejeita_slug_repetido(session):
    with pytest.raises(ValueError):
        manage.create_condominium(session, "condo-a", "X", "senha-forte-123")


def test_create_condominium_rejeita_senha_curta(session):
    with pytest.raises(ValueError):
        manage.create_condominium(session, "novo-condo", "X", "curta")


def test_add_domain_normaliza_host(session):
    domain = manage.add_domain(session, "condo-a", "Portal.Exemplo.com.br:443")
    assert domain.host == "portal.exemplo.com.br"


@pytest.mark.parametrize("host", ["https://portal.exemplo.com.br", "portal.exemplo.com.br/admin", ""])
def test_add_domain_rejeita_url_no_lugar_do_host(session, host):
    with pytest.raises(ValueError):
        manage.add_domain(session, "condo-a", host)


def test_add_domain_rejeita_host_ja_usado(session):
    with pytest.raises(ValueError):
        manage.add_domain(session, "condo-b", HOST_A)


def test_add_domain_rejeita_condominio_inexistente(session):
    with pytest.raises(ValueError):
        manage.add_domain(session, "nao-existe", "portal.exemplo.com.br")


def test_remove_domain_tira_o_portal_do_ar(session, client):
    manage.remove_domain(session, HOST_A)
    assert client.get("/api/notices").status_code == 404


def test_set_password_troca_a_senha_do_login(session, client):
    manage.set_password(session, "condo-a", "senha-nova-789")
    assert client.post("/api/auth", json={"password": TEST_PASSWORD}).status_code == 401
    assert client.post("/api/auth", json={"password": "senha-nova-789"}).status_code == 200
