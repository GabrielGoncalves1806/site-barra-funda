"""Config editável por condomínio: validação, defaults e API por seção."""
import pytest

from condo_config import CondominiumConfig, load_config, maps_url, tel_url, whatsapp_url

CONTACTS = [{"label": "Portaria 24h", "phone": "(11) 96335-0837", "whatsapp": True}]


# ── Defaults e tolerância ────────────────────────────────
def test_config_vazio_vira_defaults():
    config = load_config({})
    assert config.contacts == []
    assert config.tabs.vendas is True
    assert config.identity.accent == "#667eea"


def test_secao_invalida_no_banco_cai_no_default_sem_derrubar_as_outras():
    config = load_config({"identity": {"accent": "vermelho"}, "contacts": CONTACTS})
    assert config.identity.accent == "#667eea"
    assert config.contacts[0].label == "Portaria 24h"


def test_chave_desconhecida_no_banco_e_ignorada():
    assert load_config({"secao_que_nao_existe": 1}) == CondominiumConfig()


# ── Helpers de link ──────────────────────────────────────
@pytest.mark.parametrize("phone,url", [
    ("(11) 96335-0837", "https://wa.me/5511963350837"),
    ("11 3826-5666", "https://wa.me/551138265666"),
    ("+55 13 98150-0179", "https://wa.me/5513981500179"),
])
def test_whatsapp_url_usa_so_digitos_com_ddi(phone, url):
    assert whatsapp_url(phone) == url


def test_tel_url():
    assert tel_url("(11) 96335-0837") == "tel:+5511963350837"


def test_maps_url_sem_link_proprio_busca_o_endereco():
    assert maps_url("", "Av. Thomas Edison, 944") == (
        "https://www.google.com/maps/search/?api=1&query=Av.%20Thomas%20Edison%2C%20944"
    )
    assert maps_url("https://maps.app.goo.gl/x", "qualquer") == "https://maps.app.goo.gl/x"


# ── API ──────────────────────────────────────────────────
def test_get_config_e_publico(client):
    res = client.get("/api/config")
    assert res.status_code == 200
    assert res.json()["tabs"]["faq"] is True


def test_put_config_exige_login(client):
    assert client.put("/api/config/contacts", json=CONTACTS).status_code == 401


def test_put_salva_so_a_propria_secao(auth_client):
    auth_client.put("/api/config/identity", json={"name": "Residencial Teste", "accent": "#112233"})
    assert auth_client.put("/api/config/contacts", json=CONTACTS).status_code == 200
    config = auth_client.get("/api/config").json()
    assert config["contacts"][0]["phone"] == "(11) 96335-0837"
    assert config["identity"]["name"] == "Residencial Teste"
    assert config["identity"]["accent"] == "#112233"


def test_put_secao_inexistente_404(auth_client):
    assert auth_client.put("/api/config/nao-existe", json={}).status_code == 404


def test_put_rejeita_cor_invalida(auth_client):
    res = auth_client.put("/api/config/identity", json={"accent": "red; background: url(x)"})
    assert res.status_code == 422


@pytest.mark.parametrize("url", ["javascript:alert(1)", "//evil.com/x.pdf", "data:text/html,oi", "  JavaScript:alert(1)"])
def test_put_rejeita_url_perigosa(auth_client, url):
    res = auth_client.put("/api/config/documents", json=[{"title": "Regulamento", "url": url}])
    assert res.status_code == 422


@pytest.mark.parametrize("url", ["https://exemplo.com/regulamento.pdf", "/static/assets/x.pdf"])
def test_put_aceita_url_segura(auth_client, url):
    res = auth_client.put("/api/config/documents", json=[{"title": "Regulamento", "url": url}])
    assert res.status_code == 200


def test_config_de_um_condominio_nao_vaza_pro_outro(auth_client, client_b):
    auth_client.put("/api/config/contacts", json=CONTACTS)
    assert client_b.get("/api/config").json()["contacts"] == []
