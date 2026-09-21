# Portal multi-condomínio e configurável — Desenho

**Data:** 2026-09-21
**Status:** aprovado, implementação em fases (F1 → F5)

## Objetivo

1. Tudo que hoje está cravado no HTML (nome, contatos, documentos, guia de novo
   morador, fotos...) passa a ser editável pelo admin do condomínio.
2. O mesmo deploy serve vários condomínios. Ainda não é produto, mas o síndico
   do Barra Funda vai indicar outros síndicos — a base precisa estar pronta.

## Decisões

| Tema | Decisão |
|---|---|
| Liberdade do admin | Estrutura fixa (mesmas abas), conteúdo editável, abas liga/desliga. Sem montador de páginas. |
| Onde mora a config | Híbrido: conteúdo que cresce em tabelas (avisos, vendas, áreas, FAQs); configuração num JSON por condomínio validado por Pydantic. |
| Isolamento | Um banco, coluna `condominium_id` em tudo. |
| Login | Uma senha por condomínio (hash no banco). Super-admin é um CLI (`manage.py`). |
| Como o morador chega | Pelo domínio: tabela `domain` (host → condomínio). Barra Funda usa o domínio do síndico; os próximos usam subdomínio de um domínio do produto (a registrar). |
| Nomes no código | Inglês, seguindo o projeto: `Condominium`, `condominium_id`, `Domain`. |

## Modelo de dados

```
condominium: id, slug (único), name, password_hash, active, config (JSON/JSONB), created_at
domain:      host (PK), condominium_id → condominium.id
notice, sale, area, faq: + condominium_id (NOT NULL, FK, índice)
```

Blocos do `config` (F3): `identity` (nome de exibição, subtítulo, logo, cores),
`address` (texto, link do mapa), `hero` (título, subtítulo, fotos), `contacts`,
`nearby`, `documents`, `onboarding` (passos), `areas` (intro, callout opcional),
`tabs` (liga/desliga; Início sempre ligada). Todo campo novo tem default, então
configs antigos continuam válidos quando o schema cresce. Telefones de
emergência (190/192/193) seguem fixos no template.

## Resolução do condomínio

- Dependency `get_current_condominium`: lê o `Host`, tira a porta, minúsculas,
  procura em `domain`. Não achou ou inativo → 404 (HTML nas páginas, JSON na API).
- Dev: o banco local registra `localhost` e `127.0.0.1` como domínios. Nenhum
  "fallback pra localhost" no código.
- Leituras filtram por condomínio; escritas pegam o `condominium_id` do domínio,
  nunca do corpo da requisição.
- Editar/apagar usa `get_owned(...)`: registro de outro condomínio → 404 (não 403,
  pra não confirmar que existe).
- O JWT carrega `cid`; `require_admin` exige `cid` igual ao condomínio do Host.
- CORS sai (site e API sempre no mesmo domínio) — some a env `ALLOWED_ORIGINS`.

## Admin (F4)

- Sidebar em grupos (Dia a dia / Conteúdo / Aparência / Configurações), vira menu
  no celular. Link "Ver portal".
- Dois componentes genéricos: **recurso** (form + lista, CRUD existente, dirigido
  por definição de campos) e **seção de config** (salva só a própria seção via
  `PUT /api/config/{seção}`).
- Campos: texto, texto longo, número, liga/desliga, cor, select, imagem, PDF,
  lista de linhas, lista repetível (adicionar/remover/↑↓).
- "Trocar senha" pro próprio síndico.
- JS puro em módulos nativos, sem build: `static/admin/{admin.css,app.js,fields.js,resources.js,sections.js}`.

## Portal do morador (F3)

- A rota da página resolve o condomínio e passa `condominium` e `config` pro
  Jinja; o menu mostra só abas ligadas.
- Resumo do novo morador na Início é gerado dos 4 primeiros passos do `onboarding`.
- Busca: palavras-chave genéricas por aba ficam no JS; FAQs e áreas são buscadas
  pelo texto real vindo da API; abas desligadas ficam fora. O campo "Âncora" some
  (âncora vira `faq-{id}`).
- Segurança: cores validadas `#rrggbb`; URLs só `https://`, `http://` ou `/...`;
  link de WhatsApp montado só com dígitos.
- Condomínio novo nasce com config padrão e estados vazios amigáveis.

## Infra

- **Storage** (`storage.py`): disco local em dev/testes, Vercel Blob em produção
  (escolhido pela presença de `BLOB_READ_WRITE_TOKEN`). Chaves prefixadas pelo
  slug; delete recusa URL fora do prefixo do condomínio. Fotos reduzidas no
  navegador (≤1600 px, JPEG) antes do upload. PDF pelo admin até 4 MB (limite de
  4,5 MB da Vercel); maior que isso entra como link.
- **Alembic** gerencia o schema. O app não roda mais `create_all` no startup.
  Baseline idempotente (bancos existentes não precisam de `stamp`).
- **Barra Funda**: a migração adota os dados existentes num condomínio
  `barra-funda`; a senha nova é definida via `manage.py set-password`. Conteúdo
  e arquivos saem do repo (F3); `seed.py` vira um condomínio de demonstração.
- **Serverless** (F2): rate limit global do slowapi sai (firewall da Vercel);
  limite de login contado no banco; audit log numa tabela.

## Fases

| Fase | Entrega | Morador vê |
|---|---|---|
| F1 | Alembic, `Condominium`/`Domain`, resolução por Host, escopo em todas as rotas, senha por condomínio, `manage.py` | nada muda |
| F2 | Storage no Blob, rate limit de login no banco, audit em tabela, deploy na Vercel | fim do cold start |
| F3 | Config + templates lendo dele, busca dinâmica, repo sem dados do Barra Funda | nada muda |
| F4 | Admin novo | síndico ganha painel novo |
| F5 | Domínio do síndico (CNAME; MX/SPF intocados; não trocar nameservers) | endereço próprio |

## Testes

- Fixtures com dois condomínios (A e B); o `TestClient` troca o Host.
- Isolamento: B não lê/edita/apaga nada de A (404); token de A rejeitado no Host de B.
- Config: rejeita cor inválida e URL `javascript:`; salvar uma seção não mexe nas outras.
- Storage: delete fora do prefixo é recusado.
- `alembic check` garante que models e migrações não divergem.
- JS do admin: validação manual no navegador a cada fase (sem teste automatizado).
