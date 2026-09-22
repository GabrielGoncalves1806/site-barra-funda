"""Páginas renderizadas a partir do config do condomínio."""
from sqlmodel import select

from models import Condominium

CONFIG = {
    "identity": {"name": "Residencial Aurora", "subtitle": "Portal da Aurora", "logo": "🌅", "accent": "#123456"},
    "address": {"text": "Rua das Flores, 100 — Centro"},
    "hero": {"title": "Bem-vindo à Aurora", "subtitle": "Tudo sobre o prédio.",
             "images": [{"url": "https://exemplo.com/foto.jpg", "alt": "Fachada"}]},
    "contacts": [{"label": "Portaria", "phone": "(11) 91234-5678", "whatsapp": True},
                 {"label": "Zeladoria", "phone": "(11) 3333-4444", "whatsapp": False}],
    "nearby": [{"name": "Hospital Central", "tag": "24h", "details": "Rua X, 1"}],
    "documents": [{"icon": "📘", "title": "Regulamento", "url": "https://exemplo.com/regulamento.pdf"}],
    "onboarding": [{"icon": "📱", "title": "Baixe o app", "items": ["Instale o app"],
                    "links": [{"icon": "🤖", "label": "Android", "url": "https://play.google.com/x"}]}],
    "areas": {"intro": "Nossos espaços.", "callout": {"title": "Mercadinho", "text": "Aberto 24h."}},
}


def _set_config(session, slug, config):
    condo = session.exec(select(Condominium).where(Condominium.slug == slug)).one()
    condo.config = config
    session.add(condo)
    session.commit()


def test_pagina_mostra_o_conteudo_do_config(client, session):
    _set_config(session, "condo-a", CONFIG)
    page = client.get("/").text
    for expected in ["Residencial Aurora", "Portal da Aurora", "🌅", "Bem-vindo à Aurora",
                     "Rua das Flores, 100 — Centro", "https://exemplo.com/foto.jpg", "Hospital Central",
                     "https://exemplo.com/regulamento.pdf", "Baixe o app", "https://play.google.com/x",
                     "Nossos espaços.", "Aberto 24h.", "--accent: #123456"]:
        assert expected in page, expected


def test_contato_whatsapp_vira_link_do_whatsapp_e_fixo_vira_telefone(client, session):
    _set_config(session, "condo-a", CONFIG)
    page = client.get("/").text
    assert 'href="https://wa.me/5511912345678"' in page
    assert 'href="tel:+551133334444"' in page


def test_emergencias_continuam_fixas(client):
    page = client.get("/").text
    assert 'href="tel:190"' in page and 'href="tel:192"' in page and 'href="tel:193"' in page


def test_aba_desligada_some_do_menu_e_da_pagina(client, session):
    _set_config(session, "condo-a", {**CONFIG, "tabs": {"vendas": False}})
    page = client.get("/").text
    assert 'data-tab="vendas"' not in page
    assert 'id="tab-vendas"' not in page
    assert 'id="tab-faq"' in page


def test_condominio_sem_config_renderiza_com_defaults(client_b):
    res = client_b.get("/")
    assert res.status_code == 200
    assert "Condomínio B" in res.text  # nome do cadastro quando o config não tem nome


def test_texto_do_config_e_escapado(client, session):
    evil = {**CONFIG, "contacts": [{"label": "<script>alert(1)</script>", "phone": "1"}]}
    _set_config(session, "condo-a", evil)
    page = client.get("/").text
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page


def test_area_tem_icone_com_default(auth_client):
    area = auth_client.post("/api/areas", json={"title": "Salão", "slug": "salao"}).json()
    assert area["icon"] == "🏢"
    area = auth_client.post("/api/areas", json={"title": "Pet", "slug": "pet", "icon": "🐾"}).json()
    assert area["icon"] == "🐾"
