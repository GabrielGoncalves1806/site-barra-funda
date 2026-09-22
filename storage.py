"""Onde ficam os arquivos enviados pelo admin.

Disco local em dev/testes; Vercel Blob em produção (basta existir o
BLOB_READ_WRITE_TOKEN). Os arquivos ficam separados por condomínio, com o slug
como prefixo, e o delete recusa qualquer URL fora do prefixo do condomínio —
senão o admin de um condomínio apagaria a foto de outro só colando a URL dela
numa venda e apagando a venda.
"""
import os
import posixpath
import uuid
from pathlib import Path
from urllib.parse import urlparse

from vercel import blob

LOCAL_UPLOAD_DIR = Path(__file__).resolve().parent / "static" / "uploads"
LOCAL_URL_PREFIX = "/static/uploads/"
BLOB_PUBLIC_HOST_SUFFIX = ".public.blob.vercel-storage.com"


class LocalStorage:
    def __init__(self, root: Path = LOCAL_UPLOAD_DIR):
        self.root = root

    def save(self, data: bytes, extension: str, content_type: str, condominium_slug: str) -> str:
        folder = self.root / condominium_slug
        folder.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}{extension}"
        (folder / filename).write_bytes(data)
        return f"{LOCAL_URL_PREFIX}{condominium_slug}/{filename}"

    def delete(self, url: str | None, condominium_slug: str) -> None:
        if not url or not url.startswith(f"{LOCAL_URL_PREFIX}{condominium_slug}/"):
            return
        path = (self.root / url.removeprefix(LOCAL_URL_PREFIX)).resolve()
        try:
            path.relative_to((self.root / condominium_slug).resolve())
        except ValueError:
            return
        path.unlink(missing_ok=True)


class BlobStorage:
    def __init__(self, token: str):
        self.token = token

    def save(self, data: bytes, extension: str, content_type: str, condominium_slug: str) -> str:
        pathname = f"{condominium_slug}/uploads/{uuid.uuid4().hex}{extension}"
        result = blob.put(pathname, data, access="public", content_type=content_type, token=self.token)
        return result.url

    def owns(self, url: str | None, condominium_slug: str) -> bool:
        parsed = urlparse(url or "")
        path = posixpath.normpath(parsed.path)
        return (
            parsed.scheme == "https"
            and (parsed.hostname or "").endswith(BLOB_PUBLIC_HOST_SUFFIX)
            and path == parsed.path
            and path.startswith(f"/{condominium_slug}/")
        )

    def delete(self, url: str | None, condominium_slug: str) -> None:
        if self.owns(url, condominium_slug):
            blob.delete(url, token=self.token)


def get_storage() -> LocalStorage | BlobStorage:
    token = os.getenv("BLOB_READ_WRITE_TOKEN")
    return BlobStorage(token) if token else LocalStorage()
