// Busca do portal: sugestões enquanto o morador digita.
//
// O índice sai do próprio DOM — todo elemento com `data-search-title` entra —,
// então cada condomínio ganha busca do conteúdo dele sem configurar nada.

const STOPWORDS = new Set(["que", "quero", "como", "para", "com", "uma", "uns", "dos", "das", "nos", "nas",
  "onde", "qual", "quais", "pode", "posso", "fazer", "tem", "sobre", "meu", "minha", "seu", "sua", "por", "mais"]);

export function normalize(text) {
  return String(text || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

function words(text) {
  return normalize(text).split(/[^a-z0-9]+/).filter(Boolean);
}

function queryTerms(query) {
  return words(query).filter(word => word.length >= 3 && !STOPWORDS.has(word));
}

// Só sinônimos que valem pra qualquer condomínio: o resto vem do conteúdo.
const SYNONYMS = {
  hospital: ["saude", "pronto", "socorro", "medico", "upa"],
  medico: ["saude", "pronto", "socorro", "hospital"],
  farmacia: ["remedio", "drogaria"],
  cachorro: ["pet", "animal", "cao"],
  cao: ["pet", "animal"],
  gato: ["pet", "animal"],
  wifi: ["internet", "wi-fi"],
  internet: ["wifi", "provedor"],
  barulho: ["silencio", "som", "ruido"],
  carro: ["garagem", "vaga", "estacionamento"],
  faxina: ["diarista", "empregada", "limpeza"],
  encomenda: ["entrega", "pacote", "delivery"],
};

function expand(term) {
  return [term, ...(SYNONYMS[term] || [])];
}

// Título vale mais que corpo, e começo de palavra vale mais que meio dela.
function scoreOne(term, titleWords, textWords) {
  if (titleWords.some(word => word.startsWith(term))) return 10;
  if (titleWords.some(word => word.includes(term))) return 6;
  if (textWords.some(word => word.startsWith(term))) return 3;
  if (textWords.some(word => word.includes(term))) return 2;
  return 0;
}

function termScore(term, titleWords, textWords) {
  return Math.max(...expand(term).map(word => scoreOne(word, titleWords, textWords)));
}

export function rank(query, items, { limit = 8 } = {}) {
  const terms = queryTerms(query);
  if (!terms.length) return [];

  const indexed = items.map(item => ({ item, titleWords: words(item.title), textWords: words(item.text) }));
  // Palavra rara pesa mais: em "horário da academia", "academia" tem que ganhar
  // de "horário", que aparece em meia dúzia de itens.
  const weight = new Map(terms.map(term => {
    const hits = indexed.filter(entry => termScore(term, entry.titleWords, entry.textWords)).length;
    return [term, Math.log(1 + items.length / (1 + hits))];
  }));

  // Ninguém casa com tudo? Mostra o parcial, mas exige metade das palavras
  // pra não encher a lista de item que só bateu numa palavra solta.
  const minTerms = Math.max(1, Math.ceil(terms.length / 2));

  const scored = [];
  for (const { item, titleWords, textWords } of indexed) {
    let matched = 0;
    let total = 0;
    for (const term of terms) {
      const score = termScore(term, titleWords, textWords);
      if (!score) continue;
      matched += 1;
      total += score * weight.get(term);
    }
    if (matched >= minTerms) scored.push({ item, matched, total });
  }
  // Se alguém casa com a busca inteira, o parcial só atrapalha.
  const complete = scored.filter(entry => entry.matched === terms.length);
  const finalists = complete.length ? complete : scored;

  return finalists
    .sort((a, b) => b.matched - a.matched || b.total - a.total)
    .slice(0, limit)
    .map(entry => entry.item);
}


// ── Índice: tudo que tem data-search-title na página ─────
let index = null;

export function buildIndex(root = document) {
  return [...root.querySelectorAll("[data-search-title]")].map(el => ({
    title: el.getAttribute("data-search-title"),
    type: el.getAttribute("data-search") || "",
    text: el.textContent.replace(/\s+/g, " ").trim(),
    tab: el.closest(".tab-content")?.id.replace(/^tab-/, "") || "",
    el,
  }));
}

/** Chamado quando a página ganha conteúdo novo (FAQs, áreas, avisos, vendas). */
export function refreshIndex() {
  index = null;
}

// ── Sugestões enquanto digita ────────────────────────────
const DEBOUNCE_MS = 120;
const MIN_CHARS = 2;

export function initSearch({ form, input, results, showTab, openArea }) {
  if (!form || !input || !results) return;

  let matches = [];
  let active = -1;
  let timer = null;

  function close() {
    results.hidden = true;
    results.innerHTML = "";
    matches = [];
    active = -1;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  }

  function highlight(next) {
    const options = [...results.querySelectorAll(".search-result")];
    options.forEach(option => option.classList.remove("is-active"));
    if (next < 0 || next >= options.length) {
      active = -1;
      input.removeAttribute("aria-activedescendant");
      return;
    }
    active = next;
    options[active].classList.add("is-active");
    options[active].scrollIntoView({ block: "nearest" });
    input.setAttribute("aria-activedescendant", options[active].id);
  }

  function select(item) {
    close();
    input.blur();
    if (item.tab) showTab(item.tab);
    // A aba precisa aparecer antes de rolar até o item.
    setTimeout(() => {
      const areaSlug = item.el.getAttribute("data-area-detail");
      if (areaSlug && openArea) {
        openArea(areaSlug);
        return;
      }
      if (item.el.tagName === "DETAILS") item.el.open = true;
      item.el.classList.add("search-hit");
      item.el.scrollIntoView({ behavior: "smooth", block: "center" });
      setTimeout(() => item.el.classList.remove("search-hit"), 1800);
    }, 150);
  }

  function renderEmpty(query) {
    const empty = document.createElement("p");
    empty.className = "search-results__empty";
    empty.textContent = `Não achei nada com “${query}”. Tente outra palavra ou `;
    const link = document.createElement("button");
    link.type = "button";
    link.className = "search-results__link";
    link.textContent = "fale com a administração";
    link.addEventListener("click", () => {
      close();
      showTab("contatos");
    });
    empty.appendChild(link);
    results.appendChild(empty);
  }

  function search(query) {
    if (query.trim().length < MIN_CHARS) return close();

    if (!index) index = buildIndex();
    matches = rank(query, index);
    results.innerHTML = "";

    if (!matches.length) {
      renderEmpty(query.trim());
    } else {
      matches.forEach((item, i) => {
        const option = document.createElement("button");
        option.type = "button";
        option.className = "search-result";
        option.id = `search-result-${i}`;
        option.setAttribute("role", "option");
        option.innerHTML = `<span class="search-result__type"></span><span class="search-result__title"></span>`;
        option.querySelector(".search-result__type").textContent = item.type;
        option.querySelector(".search-result__title").textContent = item.title;
        option.addEventListener("mousedown", (e) => e.preventDefault());  // não tira o foco antes do clique
        option.addEventListener("click", () => select(item));
        results.appendChild(option);
      });
    }

    results.hidden = false;
    input.setAttribute("aria-expanded", "true");
    highlight(-1);
  }

  input.addEventListener("input", () => {
    clearTimeout(timer);
    const query = input.value;
    timer = setTimeout(() => search(query), DEBOUNCE_MS);
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Escape") return close();
    if (!matches.length) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      highlight(active + 1 >= matches.length ? 0 : active + 1);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      highlight(active - 1 < 0 ? matches.length - 1 : active - 1);
    } else if (e.key === "Enter") {
      e.preventDefault();
      select(matches[active >= 0 ? active : 0]);
    }
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    if (matches.length) select(matches[active >= 0 ? active : 0]);
    else search(input.value);
  });

  input.addEventListener("focus", () => search(input.value));
  document.addEventListener("click", (e) => {
    if (!form.contains(e.target)) close();
  });
}
