// Blocos que editam o config do condomínio. Cada bloco salva só a própria
// seção (PUT /api/config/{seção}), então salvar contatos nunca apaga a identidade.
import { api, attempt, h, toast } from "./core.js";
import { createForm, repeatField } from "./fields.js";

const EMOJI_HELP = "Um emoji. No celular, use o teclado de emojis.";

export const CONFIG_BLOCKS = {
  identity: {
    section: "identity",
    title: "Identidade",
    description: "Como o condomínio aparece no topo, no rodapé e na aba do navegador.",
    fields: [
      { name: "name", label: "Nome do condomínio", placeholder: "Ex.: Residencial Aurora",
        help: "Se ficar vazio, usa o nome do cadastro." },
      { name: "subtitle", label: "Subtítulo", default: "Portal do Morador", half: true },
      { name: "logo", label: "Logo", type: "emoji", default: "🏢", half: true, help: EMOJI_HELP },
      { name: "accent", label: "Cor principal", type: "color", default: "#667eea", half: true },
      { name: "accent2", label: "Cor secundária", type: "color", default: "#764ba2", half: true },
    ],
  },

  address: {
    section: "address",
    title: "Endereço",
    fields: [
      { name: "text", label: "Endereço", placeholder: "Ex.: Rua das Flores, 100 — Centro, São Paulo/SP" },
      { name: "map_url", label: "Link do mapa (opcional)", placeholder: "https://maps.app.goo.gl/...",
        help: "Se ficar vazio, o botão do mapa busca o endereço no Google Maps." },
    ],
  },

  hero: {
    section: "hero",
    title: "Topo da página inicial",
    fields: [
      { name: "title", label: "Título", required: true },
      { name: "subtitle", label: "Texto de apresentação", type: "textarea", rows: 3 },
      { name: "images", label: "Fotos do carrossel", type: "repeat", itemLabel: "foto", titleFrom: "alt",
        emptyText: "Sem fotos: o topo aparece só com o texto.",
        fields: [
          { name: "url", label: "Foto", type: "image" },
          { name: "alt", label: "Descrição da foto", placeholder: "Ex.: Academia equipada",
            help: "Lida por leitores de tela e mostrada se a foto não carregar." },
        ] },
    ],
  },

  contacts: {
    section: "contacts",
    title: "Contatos",
    description: "Os telefones de emergência (190, 192, 193) aparecem sempre, não precisa cadastrar.",
    list: {
      itemLabel: "contato", titleFrom: "label", emptyText: "Nenhum contato cadastrado.",
      fields: [
        { name: "label", label: "Nome", required: true, placeholder: "Ex.: Portaria 24h" },
        { name: "phone", label: "Telefone", half: true, placeholder: "(11) 91234-5678" },
        { name: "email", label: "E-mail", half: true, placeholder: "portaria@exemplo.com" },
        { name: "whatsapp", label: "Esse telefone é WhatsApp", type: "toggle" },
      ],
    },
  },

  nearby: {
    section: "nearby",
    title: "Serviços próximos",
    description: "Hospitais, farmácias e outros lugares úteis perto do condomínio.",
    list: {
      itemLabel: "local", titleFrom: "name", emptyText: "Nenhum local cadastrado.",
      fields: [
        { name: "name", label: "Nome", required: true, half: true, placeholder: "Ex.: Hospital Municipal" },
        { name: "icon", label: "Ícone", type: "emoji", default: "🏥", half: true },
        { name: "tag", label: "Etiqueta", placeholder: "Ex.: Público • 24h" },
        { name: "details", label: "Endereço e telefone", placeholder: "Ex.: Rua X, 100 — (11) 3000-0000" },
        { name: "url", label: "Link (opcional)", placeholder: "https://maps.google.com/..." },
      ],
    },
  },

  documents: {
    section: "documents",
    title: "Documentos",
    description: "PDF de até 4 MB dá pra enviar direto. Arquivo maior: suba no Google Drive e cole o link.",
    list: {
      itemLabel: "documento", titleFrom: "title", emptyText: "Nenhum documento publicado.",
      fields: [
        { name: "title", label: "Título", required: true, half: true, placeholder: "Ex.: Regulamento Interno" },
        { name: "icon", label: "Ícone", type: "emoji", default: "📄", half: true },
        { name: "url", label: "Arquivo ou link", type: "document", required: true },
      ],
    },
  },

  onboarding: {
    section: "onboarding",
    title: "Guia do novo morador",
    description: "Os 4 primeiros passos também aparecem resumidos na página inicial.",
    list: {
      itemLabel: "passo", titleFrom: "title", emptyText: "Nenhum passo cadastrado.",
      fields: [
        { name: "title", label: "Título do passo", required: true, half: true, placeholder: "Ex.: Cadastro no app" },
        { name: "icon", label: "Ícone", type: "emoji", default: "✅", half: true },
        { name: "items", label: "Instruções", type: "lines", help: "Uma por linha." },
        { name: "links", label: "Botões", type: "repeat", itemLabel: "botão", titleFrom: "label",
          emptyText: "Sem botões.",
          fields: [
            { name: "label", label: "Texto do botão", required: true, half: true, placeholder: "Ex.: Android" },
            { name: "icon", label: "Ícone", type: "emoji", default: "🔗", half: true },
            { name: "url", label: "Link", required: true, placeholder: "https://..." },
          ] },
      ],
    },
  },

  areasInfo: {
    section: "areas",
    title: "Texto da aba Áreas",
    fields: [
      { name: "intro", label: "Introdução", type: "textarea", rows: 2 },
      { name: "callout_title", label: "Aviso em destaque: título (opcional)", placeholder: "Ex.: Mercadinho" },
      { name: "callout_text", label: "Aviso em destaque: texto", type: "textarea", rows: 2 },
    ],
    // Na API o aviso é um objeto opcional; no formulário, dois campos soltos.
    fromApi: value => ({
      intro: value?.intro,
      callout_title: value?.callout?.title || "",
      callout_text: value?.callout?.text || "",
    }),
    toApi: form => ({
      intro: form.intro,
      callout: form.callout_title || form.callout_text ? { title: form.callout_title, text: form.callout_text } : null,
    }),
  },

  tabs: {
    section: "tabs",
    title: "Abas visíveis",
    description: "Desligue as abas que não fazem sentido pro seu condomínio. A Início aparece sempre.",
    fields: [
      { name: "areas", label: "Áreas Comuns", type: "toggle" },
      { name: "documentos", label: "Documentos/Avisos", type: "toggle" },
      { name: "faq", label: "FAQ", type: "toggle" },
      { name: "novo_morador", label: "Novo Morador", type: "toggle" },
      { name: "vendas", label: "Vendas", type: "toggle" },
      { name: "contatos", label: "Contatos", type: "toggle" },
    ],
  },
};

export function mountConfigBlock(container, block, config, onSaved) {
  const editor = block.list ? repeatField({ type: "repeat", ...block.list }) : createForm(block.fields);
  const load = value => editor.set(block.fromApi ? block.fromApi(value) : value);
  load(config[block.section]);

  const submit = h("button", { type: "submit", class: "btn-admin btn-admin--primary" }, "Salvar");
  const formEl = h("form", { class: "admin-card" },
    h("h3", {}, block.title),
    block.description ? h("p", { class: "muted card-description" }, block.description) : null,
    editor.el,
    h("div", { class: "btn-row" }, submit));

  formEl.addEventListener("submit", async event => {
    event.preventDefault();
    if (!formEl.reportValidity()) return;
    const value = block.toApi ? block.toApi(editor.get()) : editor.get();
    const saved = await attempt(() => api("PUT", `/api/config/${block.section}`, value), "Salvo! Já está no portal.");
    if (saved !== undefined) {
      config[block.section] = saved;
      load(saved);
      onSaved?.(saved);
    }
  });
  container.append(formEl);
}

export function mountPasswordBlock(container) {
  const form = createForm([
    { name: "current_password", label: "Senha atual", type: "password", required: true, autocomplete: "current-password" },
    { name: "new_password", label: "Senha nova", type: "password", required: true, autocomplete: "new-password",
      help: "Pelo menos 8 caracteres." },
    { name: "confirm", label: "Repita a senha nova", type: "password", required: true, autocomplete: "new-password" },
  ]);
  const submit = h("button", { type: "submit", class: "btn-admin btn-admin--primary" }, "Trocar senha");
  const formEl = h("form", { class: "admin-card" },
    h("h3", {}, "Trocar senha"),
    h("p", { class: "muted card-description" }, "Quem já estiver logado continua logado até a sessão expirar (8 horas)."),
    form.el,
    h("div", { class: "btn-row" }, submit));

  formEl.addEventListener("submit", async event => {
    event.preventDefault();
    if (!formEl.reportValidity()) return;
    const { current_password, new_password, confirm } = form.get();
    if (new_password.length < 8) return toast("A senha nova precisa ter pelo menos 8 caracteres.", "error");
    if (new_password !== confirm) return toast("As senhas novas não conferem.", "error");
    const ok = await attempt(() => api("POST", "/api/password", { current_password, new_password }), "Senha trocada!");
    if (ok) form.set({});
  });
  container.append(formEl);
}
