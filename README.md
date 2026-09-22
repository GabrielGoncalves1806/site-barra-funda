# Portal do Morador

Portal web para moradores de condomínio, com painel administrativo para o síndico gerenciar avisos, vendas, áreas comuns e FAQs. Um mesmo deploy atende vários condomínios: cada um é identificado pelo domínio de acesso.

## Tecnologias

- **Backend:** FastAPI + Uvicorn
- **Banco:** Postgres no Neon em produção, SQLite em dev/testes (via SQLModel)
- **Migrações:** Alembic
- **Templates:** Jinja2
- **Frontend:** HTML/CSS/JS (vanilla)
- **Auth:** JWT em cookie httpOnly, uma senha (bcrypt) por condomínio
- **Testes:** pytest + httpx
- **Arquivos enviados:** Vercel Blob em produção, disco local em dev
- **Deploy:** Vercel (região `cle1`, junto do Neon em Ohio)

## Como funciona o multi-condomínio

- Cada condomínio tem um `slug`, uma senha de admin e um ou mais **domínios**.
- O backend descobre o condomínio pelo `Host` da requisição (tabela `domain`). Host desconhecido → 404.
- Todos os dados (avisos, vendas, áreas, FAQs) têm `condominium_id`; leituras e escritas são sempre filtradas pelo condomínio do domínio.
- A sessão do admin (JWT) vale só para o condomínio em que o login foi feito.
- Condomínios, domínios e senhas são gerenciados pelo `manage.py` (super-admin, linha de comando).
- O conteúdo de cada portal (nome, contatos, documentos, guia do novo morador, fotos, abas visíveis) fica no **config** do condomínio, no banco — nada de dado de condomínio no HTML nem no repo.

## Config do condomínio

Guardado em `condominium.config` (JSONB) e validado por `condo_config.py`. Seções:

| Seção | Conteúdo |
|---|---|
| `identity` | nome exibido, subtítulo, logo (emoji), cores `accent`/`accent2` (`#rrggbb`) |
| `address` | endereço e link do mapa (vazio = busca do endereço no Google Maps) |
| `hero` | título, subtítulo e fotos do slider da Início |
| `contacts` | rótulo, telefone, se é WhatsApp, e-mail |
| `nearby` | serviços próximos (hospitais etc.) |
| `documents` | ícone, título e URL (PDF no Blob ou link externo) |
| `onboarding` | passos do novo morador: ícone, título, itens e botões com link (os 4 primeiros viram o resumo da Início) |
| `areas` | texto de introdução e um aviso opcional (`callout`) |
| `tabs` | liga/desliga de cada aba (a Início é sempre visível) |

Todo campo tem valor padrão: condomínio novo já abre com estados vazios, e uma seção inválida no banco cai no padrão em vez de derrubar a página. URLs só aceitam `https://`, `http://` ou `/...` (bloqueia `javascript:`). Os telefones de emergência (190/192/193) são fixos no template.

As áreas comuns continuam em tabela (`/api/areas`), com um `icon` que aparece na grade da Início.

## Setup local

### 1. Ambiente virtual + dependências

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # inclui pytest/httpx; em prod use requirements.txt
```

### 2. Variáveis de ambiente

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"   # cole em SECRET_KEY
```

Sem `DATABASE_URL`, o app usa o SQLite em `./data.db`.

### 3. Banco

```bash
alembic upgrade head   # cria/atualiza as tabelas
python seed.py         # opcional: condomínio "demo" em localhost, com dados de exemplo (pede a senha)
```

Sem o seed, cadastre um condomínio na mão:

```bash
python manage.py create-condominium meu-condo "Meu Condomínio"   # pede a senha do admin
python manage.py add-domain meu-condo localhost
```

### 4. Rodar

```bash
uvicorn main:app --reload --port 8000
```

- Portal: <http://localhost:8000>
- Admin: <http://localhost:8000/admin>
- Docs API: <http://localhost:8000/docs>

No VS Code, o F5 tem duas configs: **SQLite local** (padrão) e **Neon - PRODUÇÃO** (usa o `DATABASE_URL` do `.env`; cuidado, edita os dados reais).

## Super-admin (`manage.py`)

Usa o banco do `DATABASE_URL`. Senhas são pedidas no terminal, sem eco e sem ir pro histórico do shell.

```bash
python manage.py list                                   # condomínios e domínios
python manage.py create-condominium <slug> "<nome>"
python manage.py add-domain <slug> <host>               # ex.: portal.exemplo.com.br
python manage.py remove-domain <host>
python manage.py set-password <slug>
```

## Migrações

O schema é do Alembic; o app **não** cria tabelas no startup.

```bash
alembic upgrade head                                   # aplica no banco do DATABASE_URL
alembic revision --autogenerate -m "descrição"         # depois de mudar models.py
```

Em produção, rode `alembic upgrade head` apontando pro Neon **antes** de subir o código que depende da migração.

Bancos criados antes do Alembic (pelo antigo `create_all`) não precisam de passo extra: a baseline detecta as tabelas existentes, e a migração `0002` adota os dados antigos num condomínio `barra-funda`. Depois disso, defina a senha com `manage.py set-password barra-funda` e cadastre os domínios.

## Rodar testes

```bash
pytest -v
```

## Estrutura

```
site-barra-funda/
├── main.py                 # App FastAPI + rotas
├── tenancy.py              # Resolução do condomínio pelo Host + get_owned
├── auth.py                 # JWT (preso ao condomínio), cookies, require_admin
├── database.py             # Engine (SQLite ou Postgres) + sessão
├── models.py               # Condominium, Domain, Notice, Sale, Area, FAQ
├── manage.py               # CLI de super-admin
├── storage.py              # Uploads: disco local ou Vercel Blob, separados por condomínio
├── condo_config.py         # Schema e validação do config de cada condomínio
├── logging_config.py       # Setup de logging + audit log
├── seed.py                 # Condomínio de demonstração pra dev
├── alembic.ini
├── vercel.json             # Região da function (cle1, junto do Neon)
├── migrations/             # Alembic (env.py + versions/)
├── tests/                  # pytest
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── admin.html
│   ├── not_found.html      # host sem condomínio
│   └── tabs/...
└── static/
    ├── css/styles.css
    ├── js/app.js
    └── assets/
```

## Endpoints da API

Todas as rotas respondem no contexto do condomínio do domínio acessado.

### Públicos (GET)
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/notices` | Lista avisos |
| GET | `/api/sales` | Lista vendas |
| GET | `/api/areas` | Lista áreas |
| GET | `/api/faqs` | Lista FAQs |
| GET | `/api/config` | Config do condomínio (com os padrões preenchidos) |

### Auth
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/auth` | Login com a senha do condomínio (5 tentativas/min por IP). Seta cookie `admin_session` |
| POST | `/api/logout` | Limpa cookie |
| GET | `/api/me` | Retorna o subject se o cookie é válido para este condomínio |

### Protegidas (requerem cookie `admin_session`)
| Método | Rota | Descrição |
|--------|------|-----------|
| POST/PUT/DELETE | `/api/notices[/{id}]` | CRUD avisos |
| POST/PUT/PATCH/DELETE | `/api/sales[/{id}]` | CRUD vendas |
| POST/PUT/DELETE | `/api/areas[/{id}]` | CRUD áreas |
| POST/PUT/DELETE | `/api/faqs[/{id}]` | CRUD FAQs |
| POST | `/api/upload` | Upload de imagem (4MB máx, jpg/png/webp/gif) |
| PUT | `/api/config/{seção}` | Salva uma seção do config (as outras não mudam) |

Registro de outro condomínio responde 404, igual a inexistente.

## Deploy na Vercel

A Vercel detecta o FastAPI pelo `main.py` e instala as dependências do `requirements.txt`.

> ⚠️ Não crie um `pyproject.toml`: se ele existir, a Vercel instala as dependências por ele e ignora o `requirements.txt`.

Env vars no projeto (**Settings → Environment Variables**):

```
SECRET_KEY=<token aleatório>
COOKIE_SECURE=true
DATABASE_URL=<connection string pooled do Neon>
BLOB_READ_WRITE_TOKEN=<criado ao conectar o Blob store ao projeto>
```

> `COOKIE_SECURE=true` é **obrigatório em produção** (cookie só transita via HTTPS).
> Sem `SECRET_KEY` ou `COOKIE_SECURE` o login falha. Sem `BLOB_READ_WRITE_TOKEN`
> os uploads iriam pro disco da function, que não persiste.

- **Preview ≠ produção:** deploys de branch (Preview) devem usar um `DATABASE_URL` de uma
  branch do Neon, nunca o banco de produção.
- **Blob store público:** fotos e PDFs são abertos direto pelo navegador.
- **Uploads passam pela function**, então valem os 4,5 MB de corpo de request da Vercel
  (o app aceita até 4 MB).
- Cada host de acesso (`*.vercel.app`, domínio próprio) precisa estar cadastrado:
  `manage.py add-domain <slug> <host>`.

Ordem pra subir uma versão com migração: `alembic upgrade head` apontando pro Neon de
produção, **depois** o deploy.

## Segurança

- ✅ Senha de admin por condomínio, hasheada com bcrypt (cost 12)
- ✅ JWT em cookie httpOnly + SameSite=Strict, preso ao condomínio do login
- ✅ Isolamento entre condomínios: leituras filtradas, escritas com o condomínio do domínio, 404 para registro alheio
- ✅ Rate limit no login (5 tentativas/min/IP), contado no banco pra valer entre instâncias serverless; abuso nas rotas públicas fica com o firewall da Vercel
- ✅ Sem CORS: site e API sempre no mesmo domínio
- ✅ Headers: X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- ✅ Upload validado (MIME + extensão + tamanho); arquivos separados por condomínio e remoção só dentro do prefixo do próprio condomínio
- ✅ Validação de tamanho de inputs (Pydantic max_length)
- ✅ Conteúdo de avisos/vendas/áreas/FAQs escapado antes de ir pro DOM (evita XSS armazenado)
- ✅ Audit log de login/logout (com o condomínio)
