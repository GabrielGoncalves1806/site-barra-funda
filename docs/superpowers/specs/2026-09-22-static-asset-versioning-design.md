# Versionamento dos estáticos e cache na CDN — Desenho

**Data:** 2026-09-22
**Status:** aprovado

## Problema

1. **JS/CSS velho depois de deploy.** A Vercel responde `/static` com
   `Cache-Control: public, max-age=0, must-revalidate`, então o navegador sempre
   revalida pelo `ETag`. O Starlette calcula o ETag como `md5(mtime-tamanho)`, e
   na Vercel o mtime de todo arquivo é fixo (`Last-Modified: 20 Oct 2018`). O
   ETag só muda quando muda o tamanho: uma edição que mantém o número de bytes
   (cor hex, número, typo) volta 304 e o navegador fica com o arquivo antigo.
2. **Todo estático passa pela function em `cle1`, sem cache** (`x-vercel-cache:
   MISS` sempre). O admin abre 2 CSS + 5 módulos JS, e cada um é uma ida até
   Cleveland.

## Decisão

Versão global no caminho: `/static/v/<versão>/css/styles.css`.

- **Versão** = os 12 primeiros hex do SHA-256 do conteúdo de `static/` (caminho
  relativo + bytes de cada arquivo, em ordem), **sem `static/uploads/`** — lá
  ficam os uploads do dev, que mudam em runtime.
- É recalculada a cada chamada (~0,5 ms medido). Sem cache de processo nem flag
  de ambiente: no dev, editar um JS e dar F5 já pega a versão nova. Se `static/`
  crescer muito, aí vale memoizar.
- A versão é uma só pra tudo: qualquer mudança invalida todos os arquivos.
  Com ~93 KB de estáticos, granularidade por arquivo não compensa.

Descartadas:
- **Query por arquivo (`app.js?v=…`)**: o `?v=` não passa pros imports
  relativos dos módulos do admin (`./core.js`); exigiria import map.
- **Mover pra `public/` e servir pelo estático nativo da Vercel**: sem garantia
  de funcionar sem `pyproject.toml` (que já quebrou um deploy) e muda o dev local.

## Como funciona

- **`static_url(path)`**, global do Jinja → `/static/v/<versão>/<path>`.
  `base.html` e `admin.html` passam a usar pro CSS e JS.
- **Imports relativos** (`import … from "./core.js"`) resolvem dentro do caminho
  versionado sozinhos; nenhuma mudança nos módulos.
- **Rota `/static/v/{version}/…`**: subclasse de `StaticFiles` montada **antes**
  do `/static` (senão o mount antigo captura o caminho e dá 404).
  - Versão igual à atual → `Cache-Control: public, max-age=31536000,
    s-maxage=31536000, immutable`. O `s-maxage` faz a CDN da Vercel guardar
    (ela tira o `s-maxage` antes de mandar pro navegador); o resto vale pro
    navegador.
  - Versão diferente (aba aberta antes do deploy, URL inventada) → serve o
    arquivo atual com `Cache-Control: no-cache`, pra CDN não gravar conteúdo
    novo numa URL velha.
  - O 304 herda os mesmos headers; arquivo inexistente continua 404 sem header
    de cache.
- **`/static/…` sem versão continua** do jeito que está: o placeholder de venda
  (`/static/assets/placeholder-sale.*`, gravado no banco e no JS) e os uploads
  locais do dev usam ele.

## Fora do escopo

- Cache do HTML das páginas (é dinâmico por host e muda quando o admin salva).
- Versionar `/static/assets/` e `/static/uploads/`.
- Build step, bundler ou `pyproject.toml`.

## Testes

- A versão muda quando o conteúdo de um arquivo muda e ignora `uploads/`.
- `static_url` monta o caminho com a versão atual.
- `/` e `/admin` referenciam CSS/JS pelo caminho versionado.
- Versão certa → 200 com o header `immutable` + `s-maxage`; versão errada → 200
  com `no-cache`; arquivo inexistente → 404.
- `/static/assets/placeholder-sale.svg` sem versão continua 200.

## Verificação em produção

Depois do deploy: `curl -I` num asset versionado duas vezes e ver
`x-vercel-cache` ir de `MISS` pra `HIT`; conferir que o navegador recebe o
`Cache-Control` sem `s-maxage`; abrir o portal e o admin no Chrome e ver que
tudo carrega (console sem erro de módulo).
