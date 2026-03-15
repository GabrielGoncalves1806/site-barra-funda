"""Popula o banco com dados iniciais (avisos e vendas de exemplo)."""

from database import create_db_and_tables, engine
from models import Notice, Sale
from sqlmodel import Session, select


def seed():
    create_db_and_tables()

    with Session(engine) as session:
        if session.exec(select(Notice)).first():
            print("Banco já possui dados. Seed ignorado.")
            return

        notices = [
            Notice(
                title="Cadastre-se no Portal Winker",
                text="Todos os moradores devem se cadastrar no app Winker para acesso ao condomínio, reservas de áreas comuns e comunicados oficiais.",
                level="alto",
                author="Administração",
                date="Janeiro de 2026",
            ),
            Notice(
                title="Horário de silêncio",
                text="Seg-Sex: 22h às 07h | Sáb, Dom e Feriados: 22h às 08h. Respeite seus vizinhos e evite ruídos excessivos.",
                level="alerta",
                author="Síndico",
                date="Janeiro de 2026",
            ),
            Notice(
                title="Lavanderia Laundry Express",
                text="Use o app Laundry Express para reservar máquinas. Retire suas roupas imediatamente após o ciclo para não atrasar outros moradores.",
                level="normal",
                author="Administração",
                date="Janeiro de 2026",
            ),
        ]

        sales = [
            Sale(
                title="Bolo de Pote - Brigadeiro",
                description="Delicioso bolo de pote caseiro sabor brigadeiro. Feito com ingredientes de qualidade!",
                price="R$ 12,00",
                image="/static/assets/placeholder-sale.jpg",
                seller="Maria - Bloco A, Apto 102",
                whatsapp="5511999999999",
                active=True,
            ),
            Sale(
                title="Salgados para Festa",
                description="Cento de salgados variados: coxinha, bolinha de queijo e risole. Encomende com antecedência!",
                price="R$ 45,00 (cento)",
                image="/static/assets/placeholder-sale.jpg",
                seller="João - Bloco B, Apto 305",
                whatsapp="5511988888888",
                active=True,
            ),
            Sale(
                title="Marmitas Fitness",
                description="Marmitas saudáveis com proteína, carboidrato e salada. Ideal para quem treina!",
                price="R$ 18,00",
                image="/static/assets/placeholder-sale.jpg",
                seller="Ana - Bloco C, Apto 201",
                whatsapp="5511977777777",
                active=True,
            ),
        ]

        session.add_all(notices + sales)
        session.commit()
        print(f"Seed concluído: {len(notices)} avisos e {len(sales)} vendas inseridos.")


if __name__ == "__main__":
    seed()
