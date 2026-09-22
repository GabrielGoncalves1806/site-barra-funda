// Recursos com CRUD próprio na API (avisos, vendas, áreas, FAQs). Um componente
// só monta o formulário e a lista de qualquer um deles a partir da definição.
import { api, attempt, h } from "./core.js";
import { createForm } from "./fields.js";

const LEVELS = [
  { value: "normal", label: "Info (normal)" },
  { value: "alerta", label: "Atenção (alerta)" },
  { value: "alto", label: "Prioridade (alto)" },
];
const LEVEL_LABELS = Object.fromEntries(LEVELS.map(level => [level.value, level.label]));
const SALE_PLACEHOLDER = "/static/assets/placeholder-sale.svg";

function slugify(text) {
  return text.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
    .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 80);
}

export const RESOURCES = {
  notices: {
    endpoint: "/api/notices",
    newTitle: "Novo aviso",
    listTitle: "Avisos publicados",
    editingTitle: "Editando aviso",
    addedMessage: "Aviso publicado.",
    emptyText: "Nenhum aviso publicado.",
    fields: [
      { name: "title", label: "Título", required: true, placeholder: "Ex.: Manutenção do elevador" },
      { name: "text", label: "Mensagem", type: "textarea", required: true, placeholder: "Descreva o aviso..." },
      { name: "level", label: "Nível", type: "select", options: LEVELS, half: true },
      { name: "author", label: "Autor", default: "Síndico", half: true },
    ],
    beforeSave: values => ({ ...values, date: new Date().toLocaleDateString("pt-BR", { month: "long", year: "numeric" }) }),
    itemTitle: notice => notice.title,
    itemMeta: notice => `${LEVEL_LABELS[notice.level] || notice.level} • ${notice.author} • ${notice.date}`,
  },

  sales: {
    endpoint: "/api/sales",
    newTitle: "Novo anúncio",
    listTitle: "Anúncios",
    editingTitle: "Editando anúncio",
    addedMessage: "Anúncio publicado.",
    emptyText: "Nenhum anúncio ainda.",
    fields: [
      { name: "title", label: "Produto ou serviço", required: true, placeholder: "Ex.: Bolo de pote" },
      { name: "description", label: "Descrição", type: "textarea", required: true },
      { name: "price", label: "Preço", required: true, half: true, placeholder: "Ex.: R$ 15,00" },
      { name: "whatsapp", label: "WhatsApp", required: true, half: true, placeholder: "5511999999999",
        help: "Com DDI e DDD, só números." },
      { name: "seller", label: "Vendedor", required: true, placeholder: "Ex.: Maria - Bloco A, Apto 102" },
      { name: "image", label: "Foto", type: "image", default: SALE_PLACEHOLDER },
    ],
    itemTitle: sale => `${sale.title} — ${sale.price}`,
    itemMeta: sale => `${sale.seller} • ${sale.active ? "✅ Aparecendo no portal" : "⏸️ Pausado"}`,
    itemImage: sale => sale.image,
    actions: [{
      icon: sale => (sale.active ? "⏸️" : "▶️"),
      title: sale => (sale.active ? "Pausar anúncio" : "Voltar a mostrar"),
      run: sale => api("PATCH", `/api/sales/${sale.id}/toggle`),
      success: "Status atualizado.",
    }],
  },

  areas: {
    endpoint: "/api/areas",
    newTitle: "Nova área",
    listTitle: "Áreas cadastradas",
    editingTitle: "Editando área",
    addedMessage: "Área adicionada.",
    emptyText: "Nenhuma área cadastrada.",
    fields: [
      { name: "title", label: "Nome", required: true, half: true, placeholder: "Ex.: Academia" },
      { name: "icon", label: "Ícone", type: "emoji", default: "🏢", half: true, help: "Aparece na grade da página inicial." },
      { name: "tag", label: "Etiqueta", half: true, placeholder: "Ex.: Uso livre 24h" },
      { name: "display_order", label: "Ordem", type: "number", half: true, help: "Menor aparece primeiro." },
      { name: "image", label: "Foto", type: "image" },
      { name: "description", label: "Descrição", type: "textarea" },
      { name: "rules", label: "Regras", type: "lines", json: true, help: "Uma por linha. Aparecem no card da área." },
      { name: "highlights", label: "Destaques", type: "lines", json: true, help: "Uma por linha. Aparecem ao abrir a área." },
      { name: "meta", label: "Informações extras", type: "lines", json: true, rows: 3,
        help: "Uma por linha (ex.: Capacidade: 30 pessoas). Links começando com https:// ficam clicáveis." },
    ],
    // O slug identifica a área (busca, âncoras); nasce do nome e não muda ao editar.
    beforeSave: (values, editing) => ({ ...values, slug: editing?.slug || slugify(values.title) || "area" }),
    itemTitle: area => `${area.icon} ${area.title}`,
    itemMeta: area => `${area.tag || "Sem etiqueta"} • ordem ${area.display_order}`,
    itemImage: area => area.image,
  },

  faqs: {
    endpoint: "/api/faqs",
    newTitle: "Nova pergunta",
    listTitle: "Perguntas frequentes",
    editingTitle: "Editando pergunta",
    addedMessage: "Pergunta adicionada.",
    emptyText: "Nenhuma pergunta cadastrada.",
    fields: [
      { name: "question", label: "Pergunta", required: true, placeholder: "Ex.: Até que horas posso fazer barulho?" },
      { name: "answer", label: "Resposta", type: "textarea", required: true },
      { name: "icon", label: "Ícone", type: "emoji", default: "❓", half: true },
      { name: "display_order", label: "Ordem", type: "number", half: true, help: "Menor aparece primeiro." },
    ],
    itemTitle: faq => `${faq.icon} ${faq.question}`,
    itemMeta: faq => `ordem ${faq.display_order}`,
  },
};

export function mountResource(container, def) {
  let items = [];
  let editing = null;

  const form = createForm(def.fields);
  const formTitle = h("h3", {}, def.newTitle);
  const submit = h("button", { type: "submit", class: "btn-admin btn-admin--primary" }, "Adicionar");
  const cancel = h("button", { type: "button", class: "btn-admin btn-admin--ghost", hidden: true }, "Cancelar edição");
  const formEl = h("form", { class: "admin-card" }, formTitle, form.el, h("div", { class: "btn-row" }, submit, cancel));
  const list = h("div", { class: "item-list" });
  container.append(formEl, h("div", { class: "admin-card" }, h("h3", {}, def.listTitle), list));

  async function load() {
    const data = await attempt(() => api("GET", def.endpoint));
    if (data) {
      items = data;
      render();
    }
  }

  function render() {
    if (!items.length) {
      list.replaceChildren(h("p", { class: "muted" }, def.emptyText));
      return;
    }
    list.replaceChildren(...items.map(item => h("div", { class: "item-row" },
      def.itemImage?.(item) ? h("img", { class: "item-row__thumb", src: def.itemImage(item), alt: "" }) : null,
      h("div", { class: "item-row__info" },
        h("div", { class: "item-row__title" }, def.itemTitle(item)),
        h("div", { class: "item-row__meta" }, def.itemMeta(item))),
      h("div", { class: "item-row__actions" },
        (def.actions || []).map(action => h("button", {
          type: "button", class: "btn-icon", title: action.title(item), onclick: () => runAction(action, item),
        }, action.icon(item))),
        h("button", { type: "button", class: "btn-icon", title: "Editar", onclick: () => startEditing(item) }, "✏️"),
        h("button", { type: "button", class: "btn-icon btn-icon--danger", title: "Excluir", onclick: () => remove(item) }, "🗑️")),
    )));
  }

  function startEditing(item) {
    editing = item;
    form.set(item);
    formTitle.textContent = def.editingTitle;
    submit.textContent = "Salvar alterações";
    cancel.hidden = false;
    formEl.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function stopEditing() {
    editing = null;
    form.set({});
    formTitle.textContent = def.newTitle;
    submit.textContent = "Adicionar";
    cancel.hidden = true;
  }

  async function save(event) {
    event.preventDefault();
    if (!formEl.reportValidity()) return;
    const values = def.beforeSave ? def.beforeSave(form.get(), editing) : form.get();
    const saved = await attempt(
      () => (editing ? api("PUT", `${def.endpoint}/${editing.id}`, values) : api("POST", def.endpoint, values)),
      editing ? "Alterações salvas." : def.addedMessage,
    );
    if (saved) {
      stopEditing();
      await load();
    }
  }

  async function remove(item) {
    if (!confirm(`Excluir "${def.itemTitle(item)}"?`)) return;
    const ok = await attempt(() => api("DELETE", `${def.endpoint}/${item.id}`), "Excluído.");
    if (ok) {
      if (editing?.id === item.id) stopEditing();
      await load();
    }
  }

  async function runAction(action, item) {
    const ok = await attempt(() => action.run(item), action.success);
    if (ok) await load();
  }

  formEl.addEventListener("submit", save);
  cancel.addEventListener("click", stopEditing);
  load();
}
