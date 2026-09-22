"""Testes das rotas: GETs públicos, escritas protegidas, validação."""


def test_list_notices_sem_auth_ok(client):
    res = client.get("/api/notices")
    assert res.status_code == 200
    assert res.json() == []


def test_list_sales_sem_auth_ok(client):
    res = client.get("/api/sales")
    assert res.status_code == 200


def test_criar_notice_sem_auth_401(client):
    res = client.post("/api/notices", json={"title": "x", "text": "y"})
    assert res.status_code == 401


def test_deletar_notice_sem_auth_401(client):
    res = client.delete("/api/notices/1")
    assert res.status_code == 401


def test_upload_sem_auth_401(client):
    res = client.post("/api/upload", files={"file": ("x.jpg", b"x", "image/jpeg")})
    assert res.status_code == 401


def test_criar_e_deletar_notice_com_auth(auth_client):
    res = auth_client.post(
        "/api/notices",
        json={"title": "Teste", "text": "Conteúdo de teste"},
    )
    assert res.status_code == 201
    notice_id = res.json()["id"]

    res = auth_client.delete(f"/api/notices/{notice_id}")
    assert res.status_code == 200


def test_validacao_title_muito_longo(auth_client):
    res = auth_client.post(
        "/api/notices",
        json={"title": "x" * 201, "text": "ok"},
    )
    assert res.status_code == 422  # Pydantic validation error


def test_upload_rejeita_extensao_invalida(auth_client):
    res = auth_client.post(
        "/api/upload",
        files={"file": ("evil.exe", b"MZ\x00", "application/octet-stream")},
    )
    assert res.status_code == 400


def test_security_headers_presentes(client):
    res = client.get("/")
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"
    assert "referrer-policy" in res.headers
