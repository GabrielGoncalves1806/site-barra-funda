"""Estáticos com a versão no caminho, pra CDN e navegador guardarem sem medo.

`/static/v/<versão>/...` serve os mesmos arquivos de `/static/...`, mas a
versão é um hash do conteúdo de static/: quando qualquer arquivo muda, a URL
muda, então dá pra cachear por um ano. Os imports relativos dos módulos ES
(`./core.js`) herdam a versão sozinhos.

O ETag padrão do Starlette não serve pra isso: ele usa mtime + tamanho, e na
Vercel o mtime de todo arquivo é fixo — uma edição que mantém o tamanho não
mudaria o ETag.
"""
import hashlib
from pathlib import Path

from starlette.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).resolve().parent / "static"
VERSIONED_PREFIX = "/static/v"
# s-maxage é o que faz a CDN da Vercel guardar (ela tira antes de mandar pro navegador)
CACHE_FOREVER = "public, max-age=31536000, s-maxage=31536000, immutable"


def static_version(root: Path = STATIC_DIR) -> str:
    """Hash do conteúdo de static/, sem uploads/ (uploads do dev mudam em runtime).

    Recalculado a cada chamada (~0,5 ms): no dev, editar um arquivo já muda a URL.
    """
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or relative.parts[0] == "uploads":
            continue
        digest.update(relative.as_posix().encode() + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def static_url(path: str) -> str:
    return f"{VERSIONED_PREFIX}/{static_version()}/{path}"


class VersionedStaticFiles(StaticFiles):
    """Serve `/static/v/{version}/...`. Montar ANTES do `/static`, senão ele captura o caminho.

    Versão atual → cache de um ano. Versão diferente (aba aberta antes do deploy,
    URL inventada) → serve o arquivo atual sem cache, pra CDN não gravar conteúdo
    novo numa URL velha.
    """

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        current = scope["path_params"]["version"] == static_version(Path(self.directory))
        response.headers["Cache-Control"] = CACHE_FOREVER if current else "no-cache"
        return response
