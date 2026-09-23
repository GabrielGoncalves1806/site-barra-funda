# Busca do portal com sugestões — Desenho

**Data:** 2026-09-22
**Status:** aprovado, implementado

## Problema

A busca da home era "estou com sorte": pulava direto pra um único alvo e, quando
não achava, abria um `alert()`. Pior, ela só enxergava FAQs e títulos de áreas —
o resto dependia de uma lista de palavras-chave fixa no JS (`hospital`, `aviso`,
`venda`...), escrita pro Barra Funda. `mercadinho`, `zeladoria` e `reconhecimento
facial` não achavam nada, embora estivessem na página.

Com as 70 FAQs geradas a partir dos documentos do condomínio, a pontuação antiga
(contar palavras, desempatar pela ordem da lista) passou a errar: "horário da
academia" caía na FAQ do corretor, que também tem "horário".

## Decisão

Sugestões enquanto digita, alimentadas por um índice montado **a partir do DOM**.

- Todo elemento com `data-search-title` entra no índice; `data-search` vira a
  etiqueta do resultado ("FAQ", "Área", "Documento", "Contato", "Perto daqui",
  "Novo morador", "Aviso", "Venda"). O texto do elemento é o corpo da busca.
- Quem é renderizado pelo Jinja ganha a marca no template; quem é renderizado
  pelo JS (FAQs, áreas, avisos, vendas) ganha na função de render, que chama
  `refreshIndex()` no fim.
- Assim o que é pesquisável é exatamente o que está na página, e condomínio novo
  ganha busca do conteúdo dele sem configurar nada.

Descartado: indexar as APIs e o config em vez do DOM. Cobre o mesmo, mas exige
manter em dia o mapa de "qual campo da API mora em qual lugar da página".

## Pontuação (`rank`, em `static/js/search.js`)

1. A busca é normalizada (sem acento, minúscula) e quebrada em palavras de 3+
   letras, fora uma lista curta de palavras de ligação.
2. Cada palavra pontua no item: título começando com ela (10) > título contendo
   (6) > corpo começando (3) > corpo contendo (2).
3. A pontuação é multiplicada pelo peso da palavra, que é maior quanto mais rara
   ela for no índice. É o que faz "academia" ganhar de "horário".
4. **Se algum item casa com todas as palavras, só esses aparecem.** Senão, vale
   o parcial, exigindo pelo menos metade das palavras.
5. No máximo 8 resultados.

Sinônimos genéricos (`hospital` → saúde/pronto socorro, `cachorro` → pet,
`wifi` → internet...) são expandidos na busca. São poucos e servem pra qualquer
condomínio; o resto do vocabulário vem do conteúdo.

## Interação

- 120 ms de debounce, mínimo de 2 caracteres.
- ↑↓ navegam, Enter abre o selecionado (ou o primeiro), Esc e clique fora fecham.
- A ação depende do tipo: **FAQ** abre o `<details>`, **Área** abre o modal (é lá
  que estão as regras), o resto rola até o item e destaca — como já era.
- Sem resultado: uma linha na própria lista com atalho pra aba Contatos. O
  `alert()` saiu.
- `role="combobox"` no campo e `role="listbox"/"option"` na lista, com
  `aria-expanded` e `aria-activedescendant`.

## Testes

- `rank` é função pura: `node --test tests/js/search.test.mjs` (sem dependência).
  Cobre acento, palavra rara, casamento total x parcial, título x corpo,
  sinônimo e limite.
- O pytest garante que os marcadores `data-search-title` saem no HTML das páginas
  e que a home traz a lista de sugestões.
- Índice, teclado e as três ações foram validados no Chrome.

## Fora do escopo

A aba FAQ com 70 itens continua uma lista longa. Agrupar por tema ou filtrar
dentro da aba é outro trabalho.
