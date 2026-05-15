# Plano de Melhorias — Site Plano&Estação Barra Funda

> **Estratégia:** entregas pequenas e testáveis, cada milestone gera 1 PR/commit independente. Estimativas em horas de trabalho focado.

---

## ✅ M1 — Mobile: Fix Crítico do Hero & Busca (CONCLUÍDO)

**Objetivo:** parar de quebrar nas telas que apareceram no print (iPhone 375-414px).

**Escopo:**
- Adicionar breakpoint `@media (max-width: 480px)` em `styles.css`.
- `.hero-search__field`: trocar grid por `flex-wrap: wrap`; botão "Buscar" vira `width: 100%` abaixo de 480px.
- H1/H2 do hero usando `clamp()` (ex.: `font-size: clamp(2rem, 8vw, 3.5rem)`).
- Reduzir padding lateral da `.hero` em mobile.
- Adicionar `overflow-x: hidden` no `body` como safety net.

**Aceite:** abrir Chrome DevTools em 320/375/390/414px — nenhum scroll horizontal, botão "Buscar" visível inteiro, título sem cortar.

---

## ✅ M2 — Mobile: Navegação & Menu (CONCLUÍDO)

**Objetivo:** menu lateral/topo funcional em mobile.

**Escopo:**
- Remover `min-width: 220px` da `.nav` em telas < 640px.
- Revisar comportamento do botão "Menu" (existe drawer? testar abrir/fechar em mobile).
- Garantir que o logo + título "Plano&Estação Barra Funda" não estoure o header.
- Touch targets mínimos de 44×44px (Apple HIG).

**Aceite:** menu abre/fecha em iPhone, header não quebra em 2 linhas estranhas.

---

## ✅ M3 — Mobile: Grids & Cards (CONCLUÍDO)

**Objetivo:** áreas comuns, FAQs, avisos legíveis em mobile.

**Escopo:**
- `.areas-grid`: ajustar `minmax()` para `minmax(140px, 1fr)` ou virar 2 colunas em <480px.
- `.grid-2` (Novo Morador): garantir 1 coluna fluida em <640px com padding reduzido nos `.panel`.
- Revisar tabelas/listas longas — usar scroll horizontal isolado se necessário.
- Imagens: `max-width: 100%; height: auto;`.

**Aceite:** percorrer index e novo_morador inteiros no iPhone sem nada cortado.

---

## ✅ M4 — Mobile: Páginas Internas & Polimento (CONCLUÍDO)

**Escopo:**
- Auditar `templates/` (admin, documentos, etc.) em mobile.
- Form inputs com `font-size: 16px` mínimo (evita zoom automático do iOS).
- Botões de ação espaçados (evitar "fat finger").
- Testar em landscape também.

**Aceite:** todas as páginas navegáveis em mobile sem quebra visível.

---

## ✅ M5 — Segurança: Secrets & Senha Hasheada (CONCLUÍDO)

**Objetivo:** tirar credenciais do Git.

**Escopo:**
- Adicionar `python-dotenv` ou `pydantic-settings`.
- Criar `.env` (gitignored) + `.env.example` (commitado).
- Hashear senha admin com `passlib[bcrypt]`.
- Tirar `data.db` do Git (`git rm --cached data.db` + `.gitignore`).
- **Trocar a senha atual** (já vazou no histórico).

**Aceite:** `grep -r "sindico2026" .` não retorna nada; login funciona com senha nova.

---

## ✅ M6 — Segurança: JWT + Proteção de Rotas (CONCLUÍDO)

**Objetivo:** backend de verdade autenticando.

**Escopo:**
- Instalar `python-jose[cryptography]`.
- Endpoint `/api/auth` retorna JWT (expira em 8h, por ex.).
- Dependency `get_current_admin` aplicada em **todas** rotas de escrita (`POST/PUT/DELETE` em notices, sales, areas, faqs, upload).
- Frontend guarda JWT em **cookie httpOnly + secure + sameSite=strict** (não localStorage).
- Logout limpa o cookie.

**Aceite:** `curl -X POST /api/notices` sem token retorna 401; com token válido funciona.

---

## ✅ M7 — Segurança: Hardening (CONCLUÍDO)

**Escopo:**
- Rate limit em `/api/auth` com `slowapi` (5 tentativas/min por IP).
- CORS restrito ao domínio do Render + localhost.
- Validação de upload: MIME type allowlist, tamanho máx (ex.: 5MB), extensão.
- Validators no Pydantic (`max_length`, regex em campos chave).
- Headers de segurança (`X-Content-Type-Options`, `X-Frame-Options`, CSP básico).

**Aceite:** brute force no login é bloqueado; upload de `.exe` rejeitado.

---

## ✅ M8 — Observabilidade & Qualidade (CONCLUÍDO)

**Escopo:**
- Logging estruturado (`logging` ou `loguru`) — audit log de operações admin (quem, quando, o quê).
- `pytest` + `httpx` com testes de smoke: auth (sucesso/falha), CRUD de notices (com/sem token).
- Atualizar dependências (`pip list --outdated`).
- README com instruções de setup (.env, seed, run).

**Aceite:** `pytest` passa; logs mostram tentativas de login.

---

## Resumo de Prioridade

| Milestone | Esforço | Bloqueador? |
|-----------|---------|-------------|
| M1 — Hero/Busca mobile | 2h | Sim (UX visível) |
| M2 — Nav mobile | 1.5h | Sim |
| M3 — Grids mobile | 2h | Sim |
| M4 — Polimento mobile | 1.5h | Não |
| M5 — Secrets + bcrypt | 2h | **Sim, antes de prod** |
| M6 — JWT + rotas | 3h | **Sim, antes de prod** |
| M7 — Hardening | 2h | Recomendado |
| M8 — Logs + testes | 3h | Recomendado |

**Total:** ~17h. Bloco mobile (M1-M4) = ~7h; bloco segurança (M5-M7) = ~7h.
