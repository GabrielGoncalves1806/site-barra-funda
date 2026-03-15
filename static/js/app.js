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
const SEARCH_MAP = [
  { keywords: ["hospital", "hospitais", "emergencia"], tab: "contatos", target: "#contatos" },
  { keywords: ["contato", "telefone", "ramal", "portaria"], tab: "contatos", target: "#contatos" },
  { keywords: ["aviso", "documento", "regulamento", "atas"], tab: "documentos", target: "#documentos" },
  { keywords: ["venda", "produto", "anuncio"], tab: "vendas", target: "[data-sales-root]" },
  { keywords: ["novo", "cadastro", "morador"], tab: "novo-morador", target: "#novo-morador" },
  { keywords: ["faq", "duvida", "pergunta", "regras"], tab: "faq", target: "#tab-faq .faq" },
  { keywords: ["portaria", "entrega"], tab: "faq", target: "#faq-portaria" },
  { keywords: ["aluguel", "temporada"], tab: "faq", target: "#faq-aluguel" },
  { keywords: ["animal", "pet"], tab: "faq", target: "#faq-animais" },
  { keywords: ["churrasqueira"], tab: "faq", target: "#faq-churrasqueira" },
  { keywords: ["fumar", "cigarro"], tab: "faq", target: "#faq-fumar" },
  { keywords: ["reclamacao", "sugestao"], tab: "faq", target: "#faq-reclamacao" },
  { keywords: ["visitante", "visita"], tab: "faq", target: "#faq-visitantes" },
  { keywords: ["area", "churrasqueira", "academia", "coworking", "espaco"], tab: "areas", target: "#tab-areas" }
];

function highlightAndScroll(selector) {
  if (!selector) return;
  const el = document.querySelector(selector);
  if (!el) return;
  el.classList.add("search-hit");
  el.scrollIntoView({ behavior: "smooth", block: "center" });
  setTimeout(() => el.classList.remove("search-hit"), 1800);
}

const searchForm = document.querySelector("#siteSearchForm");
const searchInput = document.querySelector("#siteSearchInput");

if (searchForm && searchInput) {
  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const term = searchInput.value.trim().toLowerCase();
    if (!term) return;

    const match = SEARCH_MAP.find(entry =>
      entry.keywords.some(keyword => term.includes(keyword))
    );

    if (match) {
      showTab(match.tab);
      setTimeout(() => highlightAndScroll(match.target), 150);
    } else {
      alert("Não encontrei resultados para sua busca. Tente palavras como 'hospital', 'avisos' ou 'vendas'.");
    }

    searchInput.blur();
  });
}

// ===== MODAL ÁREAS COMUNS =====
const AREA_DETAILS = {
  academia: {
    title: "Academia",
    tag: "Uso livre 24h",
    description: "Espaço equipado com esteiras, bicicletas, pesos livres e máquinas multiestação. Priorize o uso responsável e dê espaço a outros moradores.",
    image: "/static/assets/area-academia.jpg",
    highlights: [
      "Acesso por reconhecimento facial",
      "Use toalha e limpe os aparelhos",
      "Proibido treinar descalço",
      "Capacidade sugerida: 8 pessoas"
    ],
    meta: ["Reservas: dispensa", "Contato: Administração"],
  },
  salao: {
    title: "Salão de Festas",
    tag: "Reserva via Winker",
    description: "Ambiente climatizado com copa, mesas e cadeiras para eventos sociais. Ideal para aniversários, confraternizações e reuniões.",
    image: "/static/assets/area-salao.jpg",
    highlights: [
      "Capacidade 30 pessoas",
      "Dom-qui 10h-22h | Sex-sáb 10h-23h",
      "Taxa: 6% de 1 salário mínimo",
      "Entrega de chave na portaria"
    ],
    meta: ["Reserva: 48h antecipada", "Limpeza obrigatória"],
  },
  lavanderia: {
    title: "Lavanderia Laundry Express",
    tag: "Funcionamento 24h",
    description: "Máquinas inteligentes de lavar e secar roupa com pagamento por uso. Acompanhe ciclos pelo app.",
    image: "/static/assets/area-lavanderia.jpg",
    highlights: [
      "Reserve e pague no app",
      "Retire as roupas ao término",
      "Dispõe de vending machine de sabão",
      "Relate problemas no app"
    ],
    meta: ["Suporte: Laundry Express", "Acesso com QR Code"],
  },
  playground: {
    title: "Playground",
    tag: "Uso orientado",
    description: "Área arborizada com brinquedos para crianças até 10 anos. Todos os brinquedos passam por inspeções periódicas.",
    image: "/static/assets/area-playground.jpg",
    highlights: [
      "Horário 8h às 22h",
      "Adulto responsável obrigatório",
      "Entrada de pets proibida",
      "Traga garrafa de água"
    ],
    meta: ["Capacidade sugerida: 8 crianças", "Manutenção mensal"],
  },
  churrasqueira: {
    title: "Churrasqueira",
    tag: "Reserva via Winker",
    description: "Deck externo com grelha, bancada, pia e freezer compartilhado. Perfeito para confraternizações intimistas.",
    image: "/static/assets/area-churrasqueira.jpg",
    highlights: [
      "Capacidade 15 pessoas",
      "Horário 10h às 22h",
      "Taxa 5% de 1 salário mínimo",
      "Não combinar com salão"
    ],
    meta: ["Reserva 48h antes", "Levar carvão/utensílios"],
  },
  coworking: {
    title: "Coworking",
    tag: "Uso compartilhado",
    description: "Sala com mesas colaborativas, cabines para videochamadas e internet de alta velocidade.",
    image: "/static/assets/area-coworking.jpg",
    highlights: [
      "Horário 7h às 22h",
      "Até 3 convidados por unidade",
      "Obrigatório uso de fones",
      "Disponível café e água"
    ],
    meta: ["Reservas: dispensadas", "Manter silêncio"],
  },
  "espaco-pet": {
    title: "Espaço Pet",
    tag: "Aberto 24h",
    description: "Pet place com gramado sintético, bebedouro e dispenser de sacos para recolhimento.",
    image: "/static/assets/area-pet.jpg",
    highlights: [
      "Pets sempre em coleira",
      "Permitido somente animais vacinados",
      "Limpe após o uso",
      "Evite horários de pico se o pet for reativo"
    ],
    meta: ["Acesso livre", "Contato: Síndico"],
  },
  bicicletario: {
    title: "Bicicletário",
    tag: "Uso com cadastro",
    description: "Estacionamento coberto com suportes verticais e monitoramento por câmeras.",
    image: "/static/assets/area-bicicletario.jpg",
    highlights: [
      "1 bicicleta por unidade",
      "Obrigatório cadeado",
      "Identifique com bloco/apto",
      "Não deixe acessórios soltos"
    ],
    meta: ["Cadastro com zeladoria", "Proibido motos"],
  }
};

const modal = document.querySelector("#areaModal");
const modalImage = document.querySelector("#areaModalImage");
const modalTag = document.querySelector("#areaModalTag");
const modalTitle = document.querySelector("#areaModalTitle");
const modalDescription = document.querySelector("#areaModalDescription");
const modalHighlights = document.querySelector("#areaModalHighlights");
const modalMeta = document.querySelector("#areaModalMeta");

function populateModal(data) {
  if (!data) return;
  modalImage.src = data.image;
  modalImage.alt = data.title;
  modalTag.textContent = data.tag;
  modalTitle.textContent = data.title;
  modalDescription.textContent = data.description;
  modalHighlights.innerHTML = data.highlights.map(item => `<li>${item}</li>`).join("");
  modalMeta.innerHTML = data.meta.map(item => `<span>${item}</span>`).join("");
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

document.querySelectorAll('[data-area-detail]').forEach(card => {
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
});

document.querySelectorAll('[data-modal-close]').forEach(btn => btn.addEventListener('click', closeModal));
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && modal?.classList.contains('is-open')) closeModal();
});

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
      el.innerHTML = `
        <div class="notice__top">
          <span class="${b.cls}">${b.label}</span>
          <span class="badge">${n.author}</span>
        </div>
        <h3>${n.title}</h3>
        <p>${n.text}</p>
        <div class="notice__meta">${n.date}</div>
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
    card.innerHTML = `
      <img class="sale-card__image" src="${item.image}" alt="${item.title}" onerror="this.src='/static/assets/placeholder-sale.svg'" />
      <div class="sale-card__body">
        <h3 class="sale-card__title">${item.title}</h3>
        <p class="sale-card__description">${item.description}</p>
        <span class="sale-card__price">${item.price}</span>
        <p class="sale-card__seller">📍 ${item.seller}</p>
        <a class="sale-card__whatsapp" href="https://wa.me/${item.whatsapp}?text=Olá! Vi seu anúncio de ${encodeURIComponent(item.title)} no portal do condomínio." target="_blank" rel="noreferrer">
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
