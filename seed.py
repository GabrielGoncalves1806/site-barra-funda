"""Popula um banco novo com um condomínio de demonstração, pra dev local.

Rode antes `alembic upgrade head`. Cria o condomínio "demo", acessível em
localhost e 127.0.0.1, e pede a senha do admin no terminal. Todo o conteúdo é
fictício.
"""

import json

from sqlmodel import Session, select

import condo_config
import manage
from database import engine
from models import Condominium, Notice, Sale, Area, FAQ

DEMO_HOSTS = ["localhost", "127.0.0.1"]
PLACEHOLDER = "/static/assets/placeholder-sale.svg"

DEMO_CONFIG = {
    "identity": {"name": "Residencial Exemplo"},
    "address": {"text": "Rua de Exemplo, 123 — Centro, São Paulo/SP"},
    "hero": {
        "title": "Bem-vindo ao Residencial Exemplo",
        "subtitle": "Avisos, regras, documentos, contatos e informações das áreas comuns em um só lugar.",
    },
    "contacts": [
        {"label": "Portaria 24h", "phone": "(11) 90000-0001", "whatsapp": True},
        {"label": "Zeladoria", "phone": "(11) 3000-0002"},
        {"label": "Administração", "phone": "(11) 90000-0003", "whatsapp": True, "email": "adm@exemplo.com"},
    ],
    "nearby": [
        {"name": "Hospital Municipal de Exemplo", "tag": "Público • 24h", "details": "Av. Exemplo, 500 — (11) 3000-0100"},
    ],
    "documents": [
        {"icon": "📘", "title": "Regulamento Interno", "url": "https://exemplo.com/regulamento.pdf"},
    ],
    "onboarding": [
        {
            "icon": "📱", "title": "Cadastro no app do condomínio",
            "items": ["Baixe o app indicado pela administração.", "Cadastre sua unidade e aguarde a aprovação."],
            "links": [{"icon": "🌐", "label": "Acessar site", "url": "https://exemplo.com"}],
        },
        {"icon": "🔑", "title": "Retirada de tags e chaves", "items": ["Procure a administração com um documento com foto."]},
        {"icon": "📋", "title": "Conheça as regras", "items": ["Leia o regulamento interno na aba Documentos."]},
    ],
    "areas": {"intro": "Conheça os espaços de lazer do condomínio. Reservas pela administração."},
}


def seed():
    with Session(engine) as session:
        if session.exec(select(Condominium)).first():
            print("Banco já possui condomínios. Seed ignorado.")
            return

        condominium = manage.create_condominium(session, "demo", "Residencial Exemplo", manage.ask_password())
        for host in DEMO_HOSTS:
            manage.add_domain(session, condominium.slug, host)
        condominium.config = {name: condo_config.validate_section(name, value) for name, value in DEMO_CONFIG.items()}

        notices = [
            Notice(title="Bem-vindo ao portal", text="Aqui você encontra os avisos oficiais do condomínio.",
                   level="normal", author="Administração", date="Janeiro"),
            Notice(title="Horário de silêncio", text="Seg-Sex: 22h às 07h | Fins de semana: 22h às 08h.",
                   level="alerta", author="Síndico", date="Janeiro"),
        ]
        sales = [
            Sale(title="Bolo caseiro", description="Bolos sob encomenda.", price="R$ 40,00", image=PLACEHOLDER,
                 seller="Maria - Apto 101", whatsapp="5511999999999"),
        ]
        areas = [
            Area(title="Academia", slug="academia", icon="🏋️", tag="Uso livre", image=PLACEHOLDER,
                 description="Equipamentos de musculação e cardio.",
                 rules=json.dumps(["Horário: 06h às 23h.", "Use toalha."]),
                 highlights=json.dumps(["Aberta todos os dias"]), meta=json.dumps(["Capacidade: 8 pessoas"]),
                 display_order=1),
            Area(title="Salão de Festas", slug="salao", icon="🎉", tag="Reserva", image=PLACEHOLDER,
                 description="Espaço para eventos dos moradores.",
                 rules=json.dumps(["Reserva com 48h de antecedência."]),
                 highlights=json.dumps(["Cozinha de apoio"]), meta=json.dumps(["Capacidade: 40 pessoas"]),
                 display_order=2),
        ]
        faqs = [
            FAQ(question="Posso ter animais de estimação?", answer="Sim, seguindo as regras do regulamento.",
                icon="🐾", display_order=1),
            FAQ(question="Como reservo o salão de festas?", answer="Pela administração, com 48h de antecedência.",
                icon="🎉", display_order=2),
        ]

        items = notices + sales + areas + faqs
        for item in items:
            item.condominium_id = condominium.id
        session.add_all(items)
        session.add(condominium)
        session.commit()
        print(f"Seed concluído: {len(notices)} avisos, {len(sales)} vendas, {len(areas)} áreas e {len(faqs)} FAQs inseridos.")


if __name__ == "__main__":
    seed()
