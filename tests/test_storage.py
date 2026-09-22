"""Testes do storage de uploads: disco local e Vercel Blob."""
import pytest

import storage
from storage import BlobStorage, LocalStorage

JPEG = b"\xff\xd8\xff\xe0fake-jpeg"
BLOB_HOST = "https://abc123.public.blob.vercel-storage.com"


# ── Disco local ──────────────────────────────────────────
def test_local_save_guarda_na_pasta_do_condominio(tmp_path):
    local = LocalStorage(tmp_path)
    url = local.save(JPEG, ".jpg", "image/jpeg", "condo-a")
    assert url.startswith("/static/uploads/condo-a/") and url.endswith(".jpg")
    assert (tmp_path / url.removeprefix("/static/uploads/")).read_bytes() == JPEG


def test_local_delete_apaga_arquivo_do_proprio_condominio(tmp_path):
    local = LocalStorage(tmp_path)
    url = local.save(JPEG, ".jpg", "image/jpeg", "condo-a")
    local.delete(url, "condo-a")
    assert not (tmp_path / url.removeprefix("/static/uploads/")).exists()


def test_local_delete_ignora_arquivo_de_outro_condominio(tmp_path):
    local = LocalStorage(tmp_path)
    url = local.save(JPEG, ".jpg", "image/jpeg", "condo-a")
    local.delete(url, "condo-b")
    assert (tmp_path / url.removeprefix("/static/uploads/")).exists()


def test_local_delete_bloqueia_path_traversal(tmp_path):
    local = LocalStorage(tmp_path / "uploads")
    outside = tmp_path / "escaped.txt"
    outside.write_text("não pode apagar")
    local.delete("/static/uploads/condo-a/../../escaped.txt", "condo-a")
    assert outside.exists()


@pytest.mark.parametrize("url", [None, "", "/static/assets/area-salao.jpg", "https://exemplo.com/x.jpg"])
def test_local_delete_ignora_url_que_nao_e_upload(tmp_path, url):
    LocalStorage(tmp_path).delete(url, "condo-a")  # não levanta erro


# ── Vercel Blob ──────────────────────────────────────────
@pytest.mark.parametrize("url,owned", [
    (f"{BLOB_HOST}/condo-a/uploads/x.jpg", True),
    (f"{BLOB_HOST}/condo-b/uploads/x.jpg", False),
    (f"{BLOB_HOST}/condo-a/../condo-b/uploads/x.jpg", False),
    ("https://evil.com/condo-a/uploads/x.jpg", False),
    ("http://abc123.public.blob.vercel-storage.com/condo-a/uploads/x.jpg", False),
    ("/static/uploads/condo-a/x.jpg", False),
    ("", False),
    (None, False),
])
def test_blob_so_reconhece_urls_do_proprio_condominio(url, owned):
    assert BlobStorage("token").owns(url, "condo-a") is owned


def test_blob_delete_nao_chama_api_para_url_alheia(monkeypatch):
    calls = []
    monkeypatch.setattr(storage.blob, "delete", lambda *a, **kw: calls.append(a))
    BlobStorage("token").delete(f"{BLOB_HOST}/condo-b/uploads/x.jpg", "condo-a")
    assert calls == []


# ── Escolha da implementação ─────────────────────────────
def test_get_storage_usa_disco_sem_token(monkeypatch):
    monkeypatch.setenv("BLOB_READ_WRITE_TOKEN", "")
    assert isinstance(storage.get_storage(), LocalStorage)


def test_get_storage_usa_blob_com_token(monkeypatch):
    monkeypatch.setenv("BLOB_READ_WRITE_TOKEN", "vercel_blob_rw_x_y")
    assert isinstance(storage.get_storage(), BlobStorage)
