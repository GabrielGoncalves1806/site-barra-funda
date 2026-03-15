"""Popula o banco com dados iniciais (avisos e vendas de exemplo)."""

from database import create_db_and_tables, engine
import json
from models import Notice, Sale, Area, FAQ
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

        areas = [
            Area(
                title="Academia", slug="academia", tag="Uso livre 24h",
                description="Espaço equipado com esteiras, bicicletas, pesos livres e máquinas multiestação.",
                image="/static/assets/area-academia.jpg",
                highlights=json.dumps(["Acesso por reconhecimento facial", "Use toalha e limpe os aparelhos", "Proibido treinar descalço", "Capacidade sugerida: 8 pessoas"]),
                meta=json.dumps(["Reservas: dispensa", "Contato: Administração"]),
                rules=json.dumps(["Acesso 24h via reconhecimento facial.", "Exclusivo para moradores cadastrados.", "Uso obrigatório de toalha e tênis.", "Limpe e organize os equipamentos."]),
                display_order=1,
            ),
            Area(
                title="Salão de Festas", slug="salao", tag="Reserva via Winker",
                description="Ambiente climatizado com copa, mesas e cadeiras para eventos sociais.",
                image="/static/assets/area-salao.jpg",
                highlights=json.dumps(["Capacidade 30 pessoas", "Dom-qui 10h-22h | Sex-sáb 10h-23h", "Taxa: 6% de 1 salário mínimo", "Entrega de chave na portaria"]),
                meta=json.dumps(["Reserva: 48h antecipada", "Limpeza obrigatória"]),
                rules=json.dumps(["Capacidade para 30 pessoas.", "Dom-qui 10h-22h | Sex/sáb 10h-23h.", "Reserva no app Winker (48h).", "Taxa: 6% do salário mínimo."]),
                display_order=2,
            ),
            Area(
                title="Lavanderia Laundry Express", slug="lavanderia", tag="Funcionamento 24h",
                description="Máquinas inteligentes de lavar e secar roupa com pagamento por uso.",
                image="/static/assets/area-lavanderia.jpg",
                highlights=json.dumps(["Reserve e pague no app", "Retire as roupas ao término", "Dispõe de vending machine de sabão", "Relate problemas no app"]),
                meta=json.dumps(["Suporte: Laundry Express", "Acesso com QR Code"]),
                rules=json.dumps(["Operação 24h com o app Laundry Express.", "Reserve máquinas e pague por uso.", "Retire as peças ao fim do ciclo.", "Informe falhas pelo aplicativo."]),
                display_order=3,
            ),
            Area(
                title="Playground", slug="playground", tag="Uso orientado",
                description="Área arborizada com brinquedos para crianças até 10 anos.",
                image="/static/assets/area-playground.jpg",
                highlights=json.dumps(["Horário 8h às 22h", "Adulto responsável obrigatório", "Entrada de pets proibida", "Traga garrafa de água"]),
                meta=json.dumps(["Capacidade sugerida: 8 crianças", "Manutenção mensal"]),
                rules=json.dumps(["Para crianças até 10 anos.", "Horário diário: 8h às 22h.", "Sob supervisão de um responsável.", "Organize e guarde os brinquedos."]),
                display_order=4,
            ),
            Area(
                title="Churrasqueira", slug="churrasqueira", tag="Reserva via Winker",
                description="Deck externo com grelha, bancada, pia e freezer compartilhado.",
                image="/static/assets/area-churrasqueira.jpg",
                highlights=json.dumps(["Capacidade 15 pessoas", "Horário 10h às 22h", "Taxa 5% de 1 salário mínimo", "Não combinar com salão"]),
                meta=json.dumps(["Reserva 48h antes", "Levar carvão/utensílios"]),
                rules=json.dumps(["Capacidade máxima: 15 pessoas.", "Funcionamento diário 10h-22h.", "Reserva pelo app Winker (48h).", "Taxa: 5% do salário mínimo."]),
                display_order=5,
            ),
            Area(
                title="Coworking", slug="coworking", tag="Uso compartilhado",
                description="Sala com mesas colaborativas, cabines para videochamadas e internet de alta velocidade.",
                image="/static/assets/area-coworking.jpg",
                highlights=json.dumps(["Horário 7h às 22h", "Até 3 convidados por unidade", "Obrigatório uso de fones", "Disponível café e água"]),
                meta=json.dumps(["Reservas: dispensadas", "Manter silêncio"]),
                rules=json.dumps(["Ambiente climatizado e Wi-Fi.", "Horário: 7h às 22h.", "Máx. 3 convidados por unidade.", "Use fones e mantenha silêncio."]),
                display_order=6,
            ),
            Area(
                title="Espaço Pet", slug="espaco-pet", tag="Aberto 24h",
                description="Pet place com gramado sintético, bebedouro e dispenser de sacos para recolhimento.",
                image="/static/assets/area-pet.jpg",
                highlights=json.dumps(["Pets sempre em coleira", "Permitido somente animais vacinados", "Limpe após o uso", "Evite horários de pico se o pet for reativo"]),
                meta=json.dumps(["Acesso livre", "Contato: Síndico"]),
                rules=json.dumps(["Funcionamento 24h.", "Use para necessidades dos pets.", "Somente animais vacinados e em coleira.", "Recolha os resíduos imediatamente."]),
                display_order=7,
            ),
            Area(
                title="Bicicletário", slug="bicicletario", tag="Uso com cadastro",
                description="Estacionamento coberto com suportes verticais e monitoramento por câmeras.",
                image="/static/assets/area-bicicletario.jpg",
                highlights=json.dumps(["1 bicicleta por unidade", "Obrigatório cadeado", "Identifique com bloco/apto", "Não deixe acessórios soltos"]),
                meta=json.dumps(["Cadastro com zeladoria", "Proibido motos"]),
                rules=json.dumps(["1 bicicleta por unidade cadastrada.", "Cadeado obrigatório.", "Identifique com bloco e apartamento.", "Não deixe acessórios ou caixas soltas."]),
                display_order=8,
            ),
        ]

        faqs = [
            FAQ(question="Quem precisa seguir o regulamento interno?", answer="Todos os ocupantes do condomínio: proprietários, inquilinos, comodatários, visitantes e prestadores de serviço. A convivência é coletiva e o regulamento se aplica igualmente a todos.", icon="📋", anchor_id="faq-regulamento", display_order=1),
            FAQ(question="Até que horas posso fazer barulho?", answer="Horário de silêncio: segunda a sexta das 22h às 7h, fins de semana e feriados das 22h às 8h. Mesmo fora desses horários, use o bom senso para não incomodar vizinhos.", icon="🔇", anchor_id="faq-silencio", display_order=2),
            FAQ(question="Portaria recebe qualquer tipo de entrega?", answer="Somente volumes pequenos (até 40x40 cm). A portaria não recebe móveis, compras grandes ou alimentos. Combine entregas volumosas para recebimento direto pelo morador.", icon="📦", anchor_id="faq-portaria", display_order=3),
            FAQ(question="Quero fazer reforma: como proceder?", answer="Envie projeto com ART/RRT assinada, aguarde aprovação do síndico e respeite os horários permitidos (seg-sex 8h às 17h, sáb 9h às 12h). Domingos e feriados são proibidos.", icon="🏗️", anchor_id="faq-reforma", display_order=4),
            FAQ(question="Posso alugar meu apartamento por temporada?", answer="Sim, mas o proprietário segue responsável pelos hóspedes. Cadastre-os, entregue o regulamento e limite o uso às áreas liberadas (academia, coworking, playground e lavanderia).", icon="🏡", anchor_id="faq-aluguel", display_order=5),
            FAQ(question="Animais de estimação são permitidos?", answer="São, desde que em coleira (e focinheira para raças grandes), circulando apenas até o Espaço Pet. Tutores devem recolher resíduos, controlar ruídos e manter vacinas em dia.", icon="🐾", anchor_id="faq-animais", display_order=6),
            FAQ(question="Como funciona o salão de festas?", answer="Uso exclusivo de moradores, com reserva via portal com 48h de antecedência. Horário: 10h-22h (dom-qui) e até 23h (sex/sáb). Capacidade 30 pessoas e taxa de 6% do salário mínimo.", icon="🎉", anchor_id="faq-salao", display_order=7),
            FAQ(question="E a churrasqueira?", answer="Capacidade 15 pessoas, horário diário das 10h às 22h, reserva com 48h e taxa de 5% do salário mínimo. Não pode ser usada junto com o salão pela mesma unidade.", icon="🍖", anchor_id="faq-churrasqueira", display_order=8),
            FAQ(question="Posso alterar fachada, instalar varal ou antena?", answer="Não. A fachada é padrão coletivo. É proibido pintar, furar, instalar toldos, vasos, películas, antenas ou varais visíveis.", icon="🏗️", anchor_id="faq-fachada", display_order=9),
            FAQ(question="É permitido fumar nas áreas comuns?", answer="Não. A legislação federal proíbe fumar em qualquer dependência coletiva do condomínio.", icon="🚭", anchor_id="faq-fumar", display_order=10),
            FAQ(question="Como registrar reclamação ou sugestão?", answer="Use os canais oficiais: portal da administradora, e-mail ou contato direto com síndico/administrador. Evite recados informais para porteiros.", icon="📝", anchor_id="faq-reclamacao", display_order=11),
            FAQ(question="Visitantes podem usar áreas comuns?", answer="As áreas de lazer são exclusivas dos moradores. Visitantes só podem acessar espaços reservados que estejam vinculados a uma unidade e identificados na lista de convidados.", icon="👥", anchor_id="faq-visitantes", display_order=12),
        ]

        session.add_all(notices + sales + areas + faqs)
        session.commit()
        print(f"Seed concluído: {len(notices)} avisos, {len(sales)} vendas, {len(areas)} áreas e {len(faqs)} FAQs inseridos.")


if __name__ == "__main__":
    seed()
