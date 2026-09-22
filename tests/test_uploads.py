"""Upload pelo admin: pasta do condomínio, limite de tamanho e remoção segura."""
import pytest

from storage import LocalStorage, get_storage

JPEG = b"\xff\xd8\xff\xe0fake-jpeg"
SALE = {"title": "Bike", "description": "Aro 29", "price": "R$ 500", "seller": "Ana 12A", "whatsapp": "11999999999"}
AREA = {"title": "Salão de festas", "slug": "salao"}


@pytest.fixture
def uploads(app, tmp_path):
    """Troca o storage do app por um disco local numa pasta temporária."""
    local = LocalStorage(tmp_path)
    app.dependency_overrides[get_storage] = lambda: local
    return tmp_path


def _upload(client) -> str:
    res = client.post("/api/upload", files={"file": ("foto.jpg", JPEG, "image/jpeg")})
    assert res.status_code == 200, res.text
    return res.json()["url"]


def _file(uploads, url):
    return uploads / url.removeprefix("/static/uploads/")


def test_upload_vai_para_a_pasta_do_condominio(auth_client, uploads):
    url = _upload(auth_client)
    assert url.startswith("/static/uploads/condo-a/")
    assert _file(uploads, url).read_bytes() == JPEG


def test_upload_acima_de_4mb_e_recusado(auth_client, uploads):
    big = b"\xff" * (4 * 1024 * 1024 + 1)
    res = auth_client.post("/api/upload", files={"file": ("grande.jpg", big, "image/jpeg")})
    assert res.status_code == 413
    assert list(uploads.rglob("*.jpg")) == []


@pytest.mark.parametrize("resource,payload", [("sales", SALE), ("areas", AREA)])
def test_apagar_registro_apaga_a_propria_imagem(auth_client, uploads, resource, payload):
    url = _upload(auth_client)
    item_id = auth_client.post(f"/api/{resource}", json={**payload, "image": url}).json()["id"]
    assert auth_client.delete(f"/api/{resource}/{item_id}").status_code == 200
    assert not _file(uploads, url).exists()


@pytest.mark.parametrize("resource,payload", [("sales", SALE), ("areas", AREA)])
def test_apagar_registro_nao_apaga_imagem_de_outro_condominio(auth_client, auth_client_b, uploads, resource, payload):
    url = _upload(auth_client)
    item_id = auth_client_b.post(f"/api/{resource}", json={**payload, "image": url}).json()["id"]
    assert auth_client_b.delete(f"/api/{resource}/{item_id}").status_code == 200
    assert _file(uploads, url).exists()
