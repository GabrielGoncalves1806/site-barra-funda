# Portal do Morador — Condomínio Plano&Estação Barra Funda

Portal web para moradores do condomínio com painel administrativo para o síndico gerenciar avisos e vendas.

## Tecnologias

- **Backend:** FastAPI + Uvicorn
- **Banco de dados:** SQLite (via SQLModel)
- **Templates:** Jinja2
- **Frontend:** HTML/CSS/JS (vanilla)

## Estrutura do Projeto

```
site-barra-funda/
├── main.py              # App FastAPI (rotas de páginas e API)
├── database.py          # Conexão com SQLite
├── models.py            # Modelos (Notice, Sale)
├── seed.py              # Populador de dados iniciais
├── requirements.txt     # Dependências Python
├── data.db              # Banco SQLite (criado automaticamente)
├── templates/
│   ├── base.html        # Layout base (header, nav, scripts)
│   ├── index.html       # Página principal (monta todas as abas)
│   ├── admin.html       # Painel de administração
│   ├── partials/
│   │   └── _footer.html # Footer reutilizável
│   └── tabs/
│       ├── inicio.html
│       ├── areas.html
│       ├── documentos.html
│       ├── novo_morador.html
│       ├── contatos.html
│       ├── vendas.html
│       └── faq.html
└── static/
    ├── css/
    │   └── styles.css
    ├── js/
    │   └── app.js
    └── assets/          # Imagens, PDFs, ícones
```

## Como rodar

### 1. Criar ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Popular o banco com dados iniciais (opcional)

```bash
python seed.py
```

Isso cria o arquivo `data.db` com avisos e vendas de exemplo. Se o banco já tiver dados, o seed é ignorado.

### 4. Iniciar o servidor

```bash
uvicorn main:app --reload --port 8000
```

### 5. Acessar

- **Portal do Morador:** [http://localhost:8000](http://localhost:8000)
- **Painel Admin:** [http://localhost:8000/admin](http://localhost:8000/admin)
- **Documentação API:** [http://localhost:8000/docs](http://localhost:8000/docs)

## Painel de Administração

Acesse `/admin` e use a senha `sindico2026` para entrar. No painel é possível:

- **Avisos:** Criar e excluir comunicados (exibidos na aba Documentos/Avisos)
- **Vendas:** Criar, ativar/desativar e excluir produtos de moradores (exibidos na aba Vendas)

As alterações são salvas no banco de dados e refletidas imediatamente no portal.

## Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/notices` | Lista todos os avisos |
| `POST` | `/api/notices` | Cria um aviso |
| `PUT` | `/api/notices/{id}` | Atualiza um aviso |
| `DELETE` | `/api/notices/{id}` | Exclui um aviso |
| `GET` | `/api/sales` | Lista todas as vendas |
| `POST` | `/api/sales` | Cria uma venda |
| `PUT` | `/api/sales/{id}` | Atualiza uma venda |
| `PATCH` | `/api/sales/{id}/toggle` | Ativa/desativa uma venda |
| `DELETE` | `/api/sales/{id}` | Exclui uma venda |
| `POST` | `/api/auth` | Verifica senha do admin |

## Hospedagem

O projeto pode ser hospedado gratuitamente em:

- **[Render](https://render.com)** — Deploy direto do GitHub, suporte a Python
- **[Railway](https://railway.app)** — Deploy com SQLite persistente
- **[Fly.io](https://fly.io)** — Free tier com volumes para o banco
