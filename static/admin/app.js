// Painel do síndico: login, sidebar e troca de telas. Cada tela é montada na
// primeira visita e reaproveitada depois.
import { api, ApiError, attempt, h, setUnauthorizedHandler } from "./core.js";
import { RESOURCES, mountResource } from "./resources.js";
import { CONFIG_BLOCKS, mountConfigBlock, mountPasswordBlock } from "./sections.js";

const SCREENS = [
  { group: "Dia a dia", id: "avisos", icon: "📢", label: "Avisos", blocks: [{ resource: "notices" }] },
  { group: "Dia a dia", id: "vendas", icon: "🛒", label: "Vendas", blocks: [{ resource: "sales" }] },
  { group: "Conteúdo", id: "areas", icon: "🏋️", label: "Áreas", blocks: [{ config: "areasInfo" }, { resource: "areas" }] },
  { group: "Conteúdo", id: "faqs", icon: "❓", label: "FAQs", blocks: [{ resource: "faqs" }] },
  { group: "Conteúdo", id: "documentos", icon: "📄", label: "Documentos", blocks: [{ config: "documents" }] },
  { group: "Conteúdo", id: "contatos", icon: "📞", label: "Contatos", blocks: [{ config: "contacts" }] },
  { group: "Conteúdo", id: "proximos", icon: "🏥", label: "Serviços próximos", blocks: [{ config: "nearby" }] },
  { group: "Conteúdo", id: "novo-morador", icon: "🏠", label: "Novo morador", blocks: [{ config: "onboarding" }] },
  { group: "Aparência", id: "identidade", icon: "🎨", label: "Identidade", blocks: [{ config: "identity" }, { config: "address" }] },
  { group: "Aparência", id: "inicio", icon: "🖼️", label: "Página inicial", blocks: [{ config: "hero" }] },
  { group: "Configurações", id: "abas", icon: "👁️", label: "Abas visíveis", blocks: [{ config: "tabs" }] },
  { group: "Configurações", id: "senha", icon: "🔑", label: "Trocar senha", blocks: [{ password: true }] },
];

const $ = id => document.getElementById(id);
const mounted = new Map();
let config = null;

// ── Login ────────────────────────────────────────────────
function showLogin(message = "") {
  $("adminPanel").classList.add("hidden");
  $("loginOverlay").classList.remove("hidden");
  const error = $("loginError");
  error.textContent = message;
  error.hidden = !message;
  $("adminPassword").focus();
}

async function enterPanel() {
  config = await attempt(() => api("GET", "/api/config"));
  if (!config) return;
  $("loginOverlay").classList.add("hidden");
  $("adminPanel").classList.remove("hidden");
  buildNav();
  openScreen(location.hash.slice(1));
}

$("loginForm").addEventListener("submit", async event => {
  event.preventDefault();
  const password = $("adminPassword").value;
  try {
    await api("POST", "/api/auth", { password });
    $("adminPassword").value = "";
    await enterPanel();
  } catch (err) {
    showLogin(err instanceof ApiError ? err.message : "Não foi possível entrar. Tente de novo.");
  }
});

$("logoutBtn").addEventListener("click", async () => {
  await api("POST", "/api/logout").catch(() => {});
  location.hash = "";
  location.reload();
});

setUnauthorizedHandler(() => showLogin("Sessão expirada. Faça login novamente."));

// ── Navegação ────────────────────────────────────────────
function buildNav() {
  const nav = $("sidebarNav");
  nav.replaceChildren();
  let group = null;
  for (const screen of SCREENS) {
    if (screen.group !== group) {
      group = screen.group;
      nav.append(h("p", { class: "sidebar__group" }, group));
    }
    nav.append(h("a", { class: "sidebar__link", href: `#${screen.id}`, "data-screen": screen.id },
      h("span", { class: "sidebar__icon", "aria-hidden": "true" }, screen.icon), screen.label));
  }
}

function mountBlock(container, block) {
  if (block.resource) return mountResource(container, RESOURCES[block.resource]);
  if (block.password) return mountPasswordBlock(container);
  const def = CONFIG_BLOCKS[block.config];
  // O nome na sidebar acompanha o que foi salvo na identidade.
  const onSaved = block.config === "identity"
    ? saved => { $("brandName").textContent = saved.name || $("brandName").dataset.fallback; }
    : null;
  return mountConfigBlock(container, def, config, onSaved);
}

function openScreen(id) {
  const screen = SCREENS.find(s => s.id === id) || SCREENS[0];
  if (!mounted.has(screen.id)) {
    const el = h("section", { class: "screen" });
    screen.blocks.forEach(block => mountBlock(el, block));
    mounted.set(screen.id, el);
    $("screen").append(el);
  }
  mounted.forEach((el, key) => { el.hidden = key !== screen.id; });
  document.querySelectorAll(".sidebar__link").forEach(link => {
    link.classList.toggle("active", link.dataset.screen === screen.id);
  });
  $("screenTitle").textContent = `${screen.icon} ${screen.label}`;
  closeSidebar();
  window.scrollTo(0, 0);
}

window.addEventListener("hashchange", () => {
  if (config) openScreen(location.hash.slice(1));
});

// ── Menu no celular ──────────────────────────────────────
function closeSidebar() {
  $("sidebar").classList.remove("is-open");
  $("sidebarBackdrop").classList.remove("is-open");
  $("menuToggle").setAttribute("aria-expanded", "false");
}

$("menuToggle").addEventListener("click", () => {
  const open = $("sidebar").classList.toggle("is-open");
  $("sidebarBackdrop").classList.toggle("is-open", open);
  $("menuToggle").setAttribute("aria-expanded", String(open));
});
$("sidebarBackdrop").addEventListener("click", closeSidebar);

// ── Início ───────────────────────────────────────────────
// Fetch cru (sem o aviso de "sessão expirada"): na primeira visita é normal
// não ter sessão.
fetch("/api/me").then(res => (res.ok ? enterPanel() : showLogin())).catch(() => showLogin());
