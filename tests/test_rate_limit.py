"""Limite de tentativas de login, contado no banco (funciona entre instâncias serverless)."""
from datetime import datetime, timedelta, timezone

from models import LoginAttempt


def _login(client, ip: str):
    return client.post("/api/auth", json={"password": "errada"}, headers={"x-forwarded-for": ip})


def test_sexta_tentativa_no_mesmo_minuto_e_bloqueada(client):
    for _ in range(5):
        assert _login(client, "1.1.1.1").status_code == 401
    assert _login(client, "1.1.1.1").status_code == 429


def test_limite_e_por_ip(client):
    for _ in range(5):
        _login(client, "1.1.1.1")
    assert _login(client, "2.2.2.2").status_code == 401


def test_usa_o_primeiro_ip_do_x_forwarded_for(client):
    for _ in range(5):
        _login(client, "1.1.1.1, 10.0.0.1")
    assert _login(client, "1.1.1.1, 10.0.0.2").status_code == 429


def test_tentativas_de_mais_de_um_minuto_atras_nao_contam(client, session):
    old = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=2)
    session.add_all([LoginAttempt(ip="1.1.1.1", created_at=old) for _ in range(5)])
    session.commit()
    assert _login(client, "1.1.1.1").status_code == 401


def test_rotas_publicas_nao_tem_limite_na_aplicacao(client):
    # O limite global saiu da aplicação (em serverless cada instância contaria
    # sozinha); proteção contra abuso fica com o firewall da Vercel.
    for _ in range(130):
        assert client.get("/api/notices").status_code == 200
