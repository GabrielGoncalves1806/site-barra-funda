# Portal do Morador — Condomínio Plano&Estação Barra Funda

Portal web para moradores do condomínio com painel administrativo para o síndico gerenciar avisos, vendas, áreas comuns e FAQs.

## Tecnologias

- **Backend:** FastAPI + Uvicorn
- **Banco:** SQLite (via SQLModel)
- **Templates:** Jinja2
- **Frontend:** HTML/CSS/JS (vanilla)
- **Auth:** JWT em cookie httpOnly, senha hasheada com bcrypt
- **Testes:** pytest + httpx
- **Deploy:** Docker (Render)

## Setup local

### 1. Ambiente virtual + dependências

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # inclui pytest/httpx; em prod use requirements.txt
```

### 2. Configurar variáveis de ambiente

Copie o template:
```bash
cp .env.example .env
```

Gere um hash bcrypt para a senha do admin:
```bash
python scripts/generate_password_hash.py "suaSenhaForte"
```

Cole o hash retornado em `.env` na variável `ADMIN_PASSWORD_HASH`. Gere também uma `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Exemplo de `.env` válido:
```
ADMIN_PASSWORD_HASH=$2b$12$...
SECRET_KEY=...
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

### 3. Popular banco com dados iniciais (opcional)

```bash
python seed.py
```

### 4. Rodar

```bash
uvicorn main:app --reload --port 8000
```

- Portal: <http://localhost:8000>
- Admin: <http://localhost:8000/admin>
- Docs API: <http://localhost:8000/docs>

## Rodar testes

```bash
pytest -v
```

## Estrutura

```
site-barra-funda/
├── main.py                 # App FastAPI + rotas
├── auth.py                 # JWT, cookies, dependency require_admin
├── database.py             # SQLite + sessão
├── models.py               # SQLModel models (Notice, Sale, Area, FAQ)
├── logging_config.py       # Setup de logging + audit log
├── seed.py                 # Popula banco com dados iniciais
├── scripts/
│   └── generate_password_hash.py   # Helper bcrypt
├── tests/                  # pytest
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── admin.html
│   └── tabs/...
└── static/
    ├── css/styles.css
    ├── js/app.js
    └── assets/
```

## Endpoints da API

### Públicos (GET)
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/notices` | Lista avisos |
| GET | `/api/sales` | Lista vendas |
| GET | `/api/areas` | Lista áreas |
| GET | `/api/faqs` | Lista FAQs |

### Auth
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/auth` | Login (5/min por IP). Seta cookie `admin_session` |
| POST | `/api/logout` | Limpa cookie |
| GET | `/api/me` | Retorna o subject se o cookie é válido |

### Protegidas (requerem cookie `admin_session`)
| Método | Rota | Descrição |
|--------|------|-----------|
| POST/PUT/DELETE | `/api/notices[/{id}]` | CRUD avisos |
| POST/PUT/PATCH/DELETE | `/api/sales[/{id}]` | CRUD vendas |
| POST/PUT/DELETE | `/api/areas[/{id}]` | CRUD áreas |
| POST/PUT/DELETE | `/api/faqs[/{id}]` | CRUD FAQs |
| POST | `/api/upload` | Upload de imagem (5MB máx, jpg/png/webp/gif) |

## Deploy no Render

O deploy usa o `Dockerfile`. Configure as env vars no painel **Settings → Environment**:

```
ADMIN_PASSWORD_HASH=<hash gerado pelo script>
SECRET_KEY=<token aleatório>
ALLOWED_ORIGINS=https://seu-app.onrender.com
COOKIE_SECURE=true
```

> `COOKIE_SECURE=true` é **obrigatório em produção** (cookie só transita via HTTPS).
> Sem `ADMIN_PASSWORD_HASH` ou `SECRET_KEY`, a aplicação não sobe.

### Banco persistente

Atualmente o `data.db` é embarcado na imagem Docker — qualquer alteração feita pelo admin via deploy é **perdida** quando o container reinicia. Para persistência real, mover para um Render Disk ou Postgres.

## Segurança

- ✅ Senha admin hasheada com bcrypt (cost 12)
- ✅ JWT em cookie httpOnly + SameSite=Strict
- ✅ Rate limit no login (5/min/IP)
- ✅ CORS restrito por env var
- ✅ Headers: X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- ✅ Upload validado (MIME + extensão + tamanho)
- ✅ Validação de tamanho de inputs (Pydantic max_length)
- ✅ Audit log de login/logout
