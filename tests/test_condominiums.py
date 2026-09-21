"""Testes multi-condomínio: resolução pelo Host e isolamento entre condomínios."""
import pytest
from sqlmodel import select

from models import Condominium
from tests.conftest import OTHER_PASSWORD, TEST_PASSWORD

RESOURCES = [
    ("notices", {"title": "Aviso", "text": "Texto do aviso"}),
    ("sales", {"title": "Bike", "description": "Aro 29", "price": "R$ 500",
               "seller": "Ana 12A", "whatsapp": "11999999999"}),
    ("areas", {"title": "Salão de festas", "slug": "salao"}),
    ("faqs", {"question": "Pode ter pet?", "answer": "Pode."}),
]


def _condo(session, slug):
    return session.exec(select(Condominium).where(Condominium.slug == slug)).one()


# ── Resolução pelo Host ──────────────────────────────────
def test_host_desconhecido_na_api_retorna_404(client):
    res = client.get("http://desconhecido.test/api/notices")
    assert res.status_code == 404
    assert res.json()["detail"] == "Portal não encontrado"


def test_host_desconhecido_na_pagina_retorna_404_em_html(client):
    res = client.get("http://desconhecido.test/")
    assert res.status_code == 404
    assert res.headers["content-type"].startswith("text/html")


def test_host_ignora_porta_e_maiusculas(client):
    res = client.get("/api/notices", headers={"host": "TestServer:8000"})
    assert res.status_code == 200


def test_condominio_inativo_retorna_404(client, session):
    condo = _condo(session, "condo-a")
    condo.active = False
    session.add(condo)
    session.commit()
    assert client.get("/api/notices").status_code == 404


# ── Isolamento dos dados ─────────────────────────────────
@pytest.mark.parametrize("resource,payload", RESOURCES)
def test_listagem_mostra_so_dados_do_proprio_condominio(auth_client, client_b, resource, payload):
    assert auth_client.post(f"/api/{resource}", json=payload).status_code == 201
    assert len(auth_client.get(f"/api/{resource}").json()) == 1
    assert client_b.get(f"/api/{resource}").json() == []


def test_criacao_ignora_condominium_id_vindo_no_corpo(auth_client, client_b, session):
    other_id = _condo(session, "condo-b").id
    res = auth_client.post("/api/notices", json={"title": "x", "text": "y", "condominium_id": other_id})
    assert res.status_code == 201
    assert client_b.get("/api/notices").json() == []


@pytest.mark.parametrize("resource,payload", RESOURCES)
def test_nao_edita_registro_de_outro_condominio(auth_client, auth_client_b, resource, payload):
    item_id = auth_client.post(f"/api/{resource}", json=payload).json()["id"]
    res = auth_client_b.put(f"/api/{resource}/{item_id}", json=payload)
    assert res.status_code == 404


@pytest.mark.parametrize("resource,payload", RESOURCES)
def test_nao_apaga_registro_de_outro_condominio(auth_client, auth_client_b, resource, payload):
    item_id = auth_client.post(f"/api/{resource}", json=payload).json()["id"]
    assert auth_client_b.delete(f"/api/{resource}/{item_id}").status_code == 404
    assert len(auth_client.get(f"/api/{resource}").json()) == 1


def test_nao_alterna_venda_de_outro_condominio(auth_client, auth_client_b):
    sale_id = auth_client.post("/api/sales", json=RESOURCES[1][1]).json()["id"]
    assert auth_client_b.patch(f"/api/sales/{sale_id}/toggle").status_code == 404
    assert auth_client.get("/api/sales").json()[0]["active"] is True


# ── Autenticação por condomínio ──────────────────────────
def test_login_usa_a_senha_do_condominio_do_host(client_b):
    assert client_b.post("/api/auth", json={"password": TEST_PASSWORD}).status_code == 401
    assert client_b.post("/api/auth", json={"password": OTHER_PASSWORD}).status_code == 200


def test_token_de_um_condominio_e_rejeitado_em_outro(auth_client, client_b):
    token = auth_client.cookies.get("admin_session")
    res = client_b.get("/api/me", headers={"cookie": f"admin_session={token}"})
    assert res.status_code == 401
