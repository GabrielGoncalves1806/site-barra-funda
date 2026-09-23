import { initSearch, refreshIndex } from "./search.js";

// ===== SISTEMA DE ABAS =====
function showTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(btn => btn.classList.remove('active'));

  const targetTab = document.getElementById(`tab-${tabId}`);
  if (targetTab) targetTab.classList.add('active');

  const targetBtn = document.querySelector(`[data-tab="${tabId}"]`);
  if (targetBtn && targetBtn.classList.contains('nav-tab')) targetBtn.classList.add('active');
}

document.querySelectorAll('[data-tab]').forEach(btn => {
  btn.addEventListener('click', (e) => {
    e.preventDefault();
    const tabId = btn.getAttribute('data-tab');
    showTab(tabId);

    const nav = document.querySelector("#nav");
    const toggle = document.querySelector(".nav__toggle");
    if (nav && toggle) {
      nav.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    }
  });
});

// ===== BUSCA GLOBAL =====
// A lista de sugestões e a pontuação ficam em search.js; aqui só ligamos o
// módulo à página (trocar de aba e abrir o modal de área são coisas daqui).
initSearch({
  form: document.querySelector("#siteSearchForm"),
  input: document.querySelector("#siteSearchInput"),
  results: document.querySelector("#searchResults"),
  showTab,
  openArea: (slug) => openModal(AREA_DETAILS[slug]),
});

// ===== SANITIZAÇÃO =====
// Todo conteúdo vindo da API (avisos, vendas, áreas, FAQs) é texto livre
// cadastrado via painel admin — precisa ser escapado antes de virar HTML,
// senão um campo com "<script>" executa pra todo mundo que visita o site.
function escapeHTML(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// ===== ÁREAS COMUNS (carregadas da API) =====
let AREA_DETAILS = {};

const modal = document.querySelector("#areaModal");
const modalImage = document.querySelector("#areaModalImage");
const modalTag = document.querySelector("#areaModalTag");
const modalTitle = document.querySelector("#areaModalTitle");
const modalDescription = document.querySelector("#areaModalDescription");
const modalHighlights = document.querySelector("#areaModalHighlights");
const modalMeta = document.querySelector("#areaModalMeta");

function parseJSON(str) {
  try { return JSON.parse(str); } catch { return []; }
}

function populateModal(data) {
  if (!data) return;
  const highlights = Array.isArray(data.highlights) ? data.highlights : parseJSON(data.highlights);
  const meta = Array.isArray(data.meta) ? data.meta : parseJSON(data.meta);
  modalImage.src = data.image;
  modalImage.alt = data.title;
  modalTag.textContent = data.tag;
  modalTitle.textContent = data.title;
  modalDescription.textContent = data.description;
  modalHighlights.innerHTML = highlights.map(item => `<li>${escapeHTML(item)}</li>`).join("");
  modalMeta.innerHTML = meta.map(item => {
    if (/^https?:\/\//.test(item)) {
      const display = item.replace(/^https?:\/\//, '');
      return `<span><a href="${escapeHTML(item)}" target="_blank" rel="noopener noreferrer" style="pointer-events:auto">${escapeHTML(display)}</a></span>`;
    }
    return `<span>${escapeHTML(item)}</span>`;
  }).join("");
}

function openModal(data) {
  populateModal(data);
  modal?.classList.add("is-open");
  document.body.classList.add("modal-open");
}

function closeModal() {
  modal?.classList.remove("is-open");
  document.body.classList.remove("modal-open");
}

function bindAreaCard(card) {
  card.addEventListener('click', () => {
    const key = card.getAttribute('data-area-detail');
    openModal(AREA_DETAILS[key]);
  });
  card.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      const key = card.getAttribute('data-area-detail');
      openModal(AREA_DETAILS[key]);
    }
  });
}

function renderHomeAreas(areas) {
  const root = document.querySelector('[data-home-areas-root]');
  if (!root) return;
  root.innerHTML = "";

  areas.forEach(area => {
    const button = document.createElement("button");
    button.className = "area-card";
    button.type = "button";
    button.innerHTML = `
      <span class="area-icon">${escapeHTML(area.icon)}</span>
      <span class="area-name">${escapeHTML(area.title)}</span>
    `;
    button.addEventListener("click", () => {
      showTab("areas");
      openModal(area);
    });
    root.appendChild(button);
  });
}

function renderAreaCards(areas) {
  const root = document.querySelector('[data-areas-root]');
  if (!root) return;
  root.innerHTML = "";
  AREA_DETAILS = {};

  areas.forEach(area => {
    const rules = Array.isArray(area.rules) ? area.rules : parseJSON(area.rules);
    AREA_DETAILS[area.slug] = area;

    const card = document.createElement("article");
    card.className = "card";
    card.setAttribute("data-area-detail", area.slug);
    card.setAttribute("data-search", "Área");
    card.setAttribute("data-search-title", area.title);
    card.setAttribute("role", "button");
    card.setAttribute("tabindex", "0");
    card.setAttribute("aria-label", `Ver detalhes de ${area.title}`);
    card.innerHTML = `
      <img src="${escapeHTML(area.image)}" alt="${escapeHTML(area.title)}" loading="lazy" />
      <div class="card__body">
        <h3>${escapeHTML(area.title)}</h3>
        <ul>${rules.map(r => `<li>${escapeHTML(r)}</li>`).join("")}</ul>
      </div>
    `;
    bindAreaCard(card);
    root.appendChild(card);
  });
}

async function loadAreas() {
  try {
    const res = await fetch('/api/areas');
    const areas = await res.json();
    renderAreaCards(areas);
    renderHomeAreas(areas);
    refreshIndex();
  } catch (err) {
    console.warn('Não foi possível carregar áreas:', err);
  }
}
loadAreas();

document.querySelectorAll('[data-modal-close]').forEach(btn => btn.addEventListener('click', closeModal));
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && modal?.classList.contains('is-open')) closeModal();
});

// ===== FAQs (carregadas da API) =====
function renderFAQs(faqs) {
  const root = document.querySelector('[data-faqs-root]');
  if (!root) return;
  root.innerHTML = "";

  faqs.forEach(faq => {
    const details = document.createElement("details");
    details.id = `faq-${faq.id}`;
    details.setAttribute("data-search", "FAQ");
    details.setAttribute("data-search-title", faq.question);
    details.innerHTML = `
      <summary>${escapeHTML(faq.icon)} ${escapeHTML(faq.question)}</summary>
      <p>${escapeHTML(faq.answer)}</p>
    `;
    root.appendChild(details);
  });
}

async function loadFAQs() {
  try {
    const res = await fetch('/api/faqs');
    const faqs = await res.json();
    renderFAQs(faqs);
    refreshIndex();
  } catch (err) {
    console.warn('Não foi possível carregar FAQs:', err);
  }
}
loadFAQs();

// ===== NAV MOBILE =====
const toggle = document.querySelector(".nav__toggle");
const nav = document.querySelector("#nav");

if (toggle && nav) {
  toggle.addEventListener("click", () => {
    const isOpen = nav.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
}

// ===== FOOTER YEAR =====
document.querySelector("#year")?.textContent && (document.querySelector("#year").textContent = new Date().getFullYear());
document.querySelectorAll(".year").forEach(el => {
  el.textContent = new Date().getFullYear();
});

// ===== HERO SLIDER =====
const slides = Array.from(document.querySelectorAll(".slider__img"));
const dotsWrap = document.querySelector(".slider__dots");
let current = 0;
let timer = null;

function renderDots() {
  if (!dotsWrap) return;
  dotsWrap.innerHTML = "";
  slides.forEach((_, idx) => {
    const b = document.createElement("button");
    b.className = "dot" + (idx === current ? " is-active" : "");
    b.type = "button";
    b.setAttribute("aria-label", `Ir para imagem ${idx + 1}`);
    b.addEventListener("click", () => goTo(idx));
    dotsWrap.appendChild(b);
  });
}

function goTo(idx) {
  if (!slides.length) return;
  slides[current]?.classList.remove("is-active");
  current = (idx + slides.length) % slides.length;
  slides[current]?.classList.add("is-active");
  renderDots();
}

function next() { goTo(current + 1); }
function prev() { goTo(current - 1); }

document.querySelectorAll("[data-slider='next']").forEach(btn => btn.addEventListener("click", next));
document.querySelectorAll("[data-slider='prev']").forEach(btn => btn.addEventListener("click", prev));

function startAuto() {
  if (!slides.length) return;
  stopAuto();
  timer = setInterval(next, 5500);
}
function stopAuto() {
  if (timer) clearInterval(timer);
  timer = null;
}

renderDots();
startAuto();

const slider = document.querySelector(".slider");
if (slider) {
  slider.addEventListener("mouseenter", stopAuto);
  slider.addEventListener("mouseleave", startAuto);
}

// ===== AVISOS (carregados da API) =====
function badgeFor(level) {
  if (level === "alto") return { cls: "badge badge--high", label: "Prioridade" };
  if (level === "alerta") return { cls: "badge badge--alert", label: "Atenção" };
  return { cls: "badge", label: "Info" };
}

function renderNotices(notices) {
  const roots = document.querySelectorAll('[data-notices-root]');
  if (!roots.length) return;

  roots.forEach(root => {
    root.innerHTML = "";
    notices.forEach(n => {
      const b = badgeFor(n.level);
      const el = document.createElement("article");
      el.className = "notice";
      el.setAttribute("data-search", "Aviso");
      el.setAttribute("data-search-title", n.title);
      el.innerHTML = `
        <div class="notice__top">
          <span class="${b.cls}">${b.label}</span>
          <span class="badge">${escapeHTML(n.author)}</span>
        </div>
        <h3>${escapeHTML(n.title)}</h3>
        <p>${escapeHTML(n.text)}</p>
        <div class="notice__meta">${escapeHTML(n.date)}</div>
      `;
      root.appendChild(el);
    });
  });
}

async function loadNotices() {
  try {
    const res = await fetch('/api/notices');
    const notices = await res.json();
    renderNotices(notices);
    refreshIndex();
  } catch (err) {
    console.warn('Não foi possível carregar avisos:', err);
  }
}
loadNotices();

// ===== VENDAS (carregadas da API) =====
function renderSales(sales) {
  const root = document.querySelector('[data-sales-root]');
  const emptyState = document.querySelector('#salesEmpty');
  if (!root) return;

  const activeSales = sales.filter(s => s.active);

  if (!activeSales.length) {
    root.style.display = 'none';
    if (emptyState) emptyState.style.display = 'block';
    return;
  }

  root.style.display = 'grid';
  if (emptyState) emptyState.style.display = 'none';
  root.innerHTML = "";

  activeSales.forEach(item => {
    const card = document.createElement("article");
    card.className = "sale-card";
    card.setAttribute("data-search", "Venda");
    card.setAttribute("data-search-title", item.title);
    card.innerHTML = `
      <img class="sale-card__image" src="${escapeHTML(item.image)}" alt="${escapeHTML(item.title)}" onerror="this.src='/static/assets/placeholder-sale.svg'" />
      <div class="sale-card__body">
        <h3 class="sale-card__title">${escapeHTML(item.title)}</h3>
        <p class="sale-card__description">${escapeHTML(item.description)}</p>
        <span class="sale-card__price">${escapeHTML(item.price)}</span>
        <p class="sale-card__seller">📍 ${escapeHTML(item.seller)}</p>
        <a class="sale-card__whatsapp" href="https://wa.me/${encodeURIComponent(item.whatsapp)}?text=Olá! Vi seu anúncio de ${encodeURIComponent(item.title)} no portal do condomínio." target="_blank" rel="noreferrer">
          📱 Chamar no WhatsApp
        </a>
      </div>
    `;
    root.appendChild(card);
  });
}

async function loadSales() {
  try {
    const res = await fetch('/api/sales');
    const sales = await res.json();
    renderSales(sales);
    refreshIndex();
  } catch (err) {
    console.warn('Não foi possível carregar vendas:', err);
    const emptyState = document.querySelector('#salesEmpty');
    if (emptyState) emptyState.style.display = 'block';
  }
}
loadSales();

// ===== GERAR MENSAGEM (FORM) =====
const form = document.querySelector("#requestForm");
if (form) {
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const subject = String(fd.get("subject") || "").trim();
    const message = String(fd.get("message") || "").trim();

    const text =
      `SOLICITAÇÃO — ${subject}

Olá! Segue solicitação:

${message}

Obrigado(a).`;

    navigator.clipboard?.writeText(text).catch(() => { });
    alert("Mensagem gerada e copiada (se o navegador permitir). Você também pode copiar manualmente:\n\n" + text);
    form.reset();
  });
}
