"""Estáticos com a versão no caminho: hash do conteúdo, rota e cache."""
from static_assets import static_url, static_version


def _write(root, relative, content):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# ── Versão ───────────────────────────────────────────────
def test_versao_muda_quando_o_conteudo_muda_mesmo_com_o_mesmo_tamanho(tmp_path):
    _write(tmp_path, "css/app.css", "a { color: #111111 }")
    before = static_version(tmp_path)
    _write(tmp_path, "css/app.css", "a { color: #222222 }")
    assert static_version(tmp_path) != before


def test_versao_ignora_uploads(tmp_path):
    _write(tmp_path, "js/app.js", "console.log(1)")
    before = static_version(tmp_path)
    _write(tmp_path, "uploads/condo-a/foto.jpg", "jpeg")
    assert static_version(tmp_path) == before


def test_static_url_usa_a_versao_atual():
    assert static_url("css/styles.css") == f"/static/v/{static_version()}/css/styles.css"


# ── Rota /static/v/<versão>/ ─────────────────────────────
IMMUTABLE = "public, max-age=31536000, s-maxage=31536000, immutable"


def test_asset_com_a_versao_atual_fica_em_cache_por_um_ano(client):
    res = client.get(static_url("js/app.js"))
    assert res.status_code == 200
    assert res.headers["cache-control"] == IMMUTABLE
    assert res.headers["content-type"].startswith("text/javascript")


def test_import_relativo_de_modulo_resolve_dentro_da_versao(client):
    # app.js faz `import ... from "./core.js"`: o navegador pede o irmão no mesmo caminho
    res = client.get(static_url("admin/core.js"))
    assert res.status_code == 200
    assert res.headers["cache-control"] == IMMUTABLE


def test_asset_com_versao_velha_e_servido_sem_cache(client):
    res = client.get("/static/v/000000000000/js/app.js")
    assert res.status_code == 200
    assert res.headers["cache-control"] == "no-cache"


def test_304_mantem_o_cache_de_um_ano(client):
    etag = client.get(static_url("css/styles.css")).headers["etag"]
    res = client.get(static_url("css/styles.css"), headers={"If-None-Match": etag})
    assert res.status_code == 304
    assert res.headers["cache-control"] == IMMUTABLE


def test_asset_inexistente_da_404_sem_cache_de_um_ano(client):
    res = client.get(static_url("js/nao-existe.js"))
    assert res.status_code == 404
    assert "immutable" not in res.headers.get("cache-control", "")


def test_static_sem_versao_continua_servindo_o_placeholder(client):
    assert client.get("/static/assets/placeholder-sale.svg").status_code == 200


# ── Páginas ──────────────────────────────────────────────
def test_portal_referencia_css_e_js_versionados(client):
    page = client.get("/").text
    assert f'href="{static_url("css/styles.css")}"' in page
    assert f'src="{static_url("js/app.js")}"' in page


def test_admin_referencia_css_e_modulo_versionados(client):
    page = client.get("/admin").text
    assert f'href="{static_url("css/styles.css")}"' in page
    assert f'href="{static_url("admin/admin.css")}"' in page
    assert f'src="{static_url("admin/app.js")}"' in page
