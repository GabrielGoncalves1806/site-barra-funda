// Campos de formulário a partir de uma definição. Cada campo devolve
// { el, get(), set(valor) }; createForm junta vários num objeto.
//
// Definição: { name, label, type, required, placeholder, help, half, default,
//   options (select), json (lines guardadas como texto JSON),
//   fields / itemLabel / titleFrom / emptyText (repeat) }
import { attempt, h, toast, uploadFile } from "./core.js";

function notifyChange(el) {
  el.dispatchEvent(new Event("input", { bubbles: true }));
}

function inputField(def, type) {
  const el = h("input", {
    type, placeholder: def.placeholder, required: def.required, autocomplete: def.autocomplete,
    maxlength: def.maxlength, class: def.type === "emoji" ? "input--emoji" : null,
  });
  return {
    el,
    get() {
      if (type === "number") return parseInt(el.value, 10) || 0;
      return type === "password" ? el.value : el.value.trim(); // senha não se mexe
    },
    set: value => { el.value = value ?? ""; },
  };
}

function textareaField(def) {
  const el = h("textarea", { placeholder: def.placeholder, required: def.required, rows: def.rows || 4 });
  return { el, get: () => el.value.trim(), set: value => { el.value = value ?? ""; } };
}

function selectField(def) {
  const el = h("select", {}, def.options.map(opt => h("option", { value: opt.value }, opt.label)));
  // Valor vazio (formulário zerado) cai na primeira opção, senão o select fica em branco.
  return { el, get: () => el.value, set: value => { el.value = value || def.options[0].value; } };
}

function toggleField() {
  const el = h("input", { type: "checkbox" });
  return { el, get: () => el.checked, set: value => { el.checked = Boolean(value); } };
}

// Uma linha por item. Algumas colunas antigas guardam a lista como texto JSON.
function linesField(def) {
  const el = h("textarea", { placeholder: def.placeholder, rows: def.rows || 4 });
  return {
    el,
    get() {
      const lines = el.value.split("\n").map(line => line.trim()).filter(Boolean);
      return def.json ? JSON.stringify(lines) : lines;
    },
    set(value) {
      let lines = value;
      if (typeof value === "string") {
        try { lines = JSON.parse(value); } catch { lines = []; }
      }
      el.value = Array.isArray(lines) ? lines.join("\n") : "";
    },
  };
}

function imageField(def) {
  let value = "";
  const preview = h("img", { class: "image-field__preview", alt: "" });
  const status = h("small", { class: "help" });
  const file = h("input", { type: "file", accept: "image/*", hidden: true });
  const pick = h("button", { type: "button", class: "btn-admin btn-admin--ghost", onclick: () => file.click() }, "Enviar foto");
  const remove = h("button", { type: "button", class: "btn-admin btn-admin--ghost" }, "Remover");
  const el = h("div", { class: "image-field" }, preview, h("div", { class: "image-field__actions" }, pick, remove, file), status);

  function set(url) {
    value = url || "";
    preview.src = value;
    preview.hidden = !value;
    remove.hidden = !value || value === def.default;
  }

  file.addEventListener("change", async () => {
    const chosen = file.files[0];
    file.value = "";
    if (!chosen) return;
    status.textContent = "Enviando...";
    const url = await attempt(() => uploadFile(chosen));
    status.textContent = url ? "Foto enviada. Lembre de salvar." : "";
    if (url) {
      set(url);
      notifyChange(el);
    }
  });
  remove.addEventListener("click", () => {
    set(def.default || "");
    notifyChange(el);
  });

  set(def.default || "");
  return { el, get: () => value, set };
}

// Link de documento: cola uma URL (Drive, site) ou sobe um PDF de até 4 MB.
function documentField(def) {
  const input = h("input", { type: "text", required: def.required, placeholder: def.placeholder || "https://... ou envie um PDF" });
  const file = h("input", { type: "file", accept: "application/pdf", hidden: true });
  const pick = h("button", { type: "button", class: "btn-admin btn-admin--ghost", onclick: () => file.click() }, "Enviar PDF");
  file.addEventListener("change", async () => {
    const chosen = file.files[0];
    file.value = "";
    if (!chosen) return;
    const url = await attempt(() => uploadFile(chosen));
    if (url) {
      input.value = url;
      notifyChange(input);
      toast("PDF enviado. Lembre de salvar.");
    }
  });
  return {
    el: h("div", { class: "document-field" }, input, pick, file),
    get: () => input.value.trim(),
    set: value => { input.value = value ?? ""; },
  };
}

// Lista de itens com os mesmos campos: adicionar, remover e reordenar.
// Setas em vez de arrastar, porque arrastar no celular é sofrimento.
function repeatField(def) {
  const items = [];
  const list = h("div", { class: "repeat__list" });
  const empty = h("p", { class: "muted" }, def.emptyText || "Nenhum item ainda.");
  const add = h("button", { type: "button", class: "btn-admin btn-admin--ghost repeat__add" }, `+ Adicionar ${def.itemLabel}`);
  const el = h("div", { class: "repeat" }, empty, list, add);

  function refresh() {
    items.forEach((item, index) => {
      const title = def.titleFrom ? item.form.get()[def.titleFrom] : "";
      item.title.textContent = title ? `${index + 1}. ${title}` : `${def.itemLabel} ${index + 1}`;
      item.up.disabled = index === 0;
      item.down.disabled = index === items.length - 1;
    });
    empty.hidden = items.length > 0;
  }

  function addItem(values) {
    const item = { form: createForm(def.fields) };
    item.form.set(values);
    item.title = h("strong", { class: "repeat__title" });
    item.up = h("button", { type: "button", class: "btn-icon", title: "Subir", onclick: () => move(item, -1) }, "↑");
    item.down = h("button", { type: "button", class: "btn-icon", title: "Descer", onclick: () => move(item, 1) }, "↓");
    const remove = h("button", { type: "button", class: "btn-icon btn-icon--danger", title: "Remover", onclick: () => removeItem(item) }, "✕");
    item.card = h("div", { class: "repeat__item" },
      h("div", { class: "repeat__head" }, item.title, h("div", { class: "repeat__actions" }, item.up, item.down, remove)),
      item.form.el);
    item.form.el.addEventListener("input", refresh);
    items.push(item);
    list.append(item.card);
    refresh();
    return item;
  }

  function move(item, delta) {
    const from = items.indexOf(item);
    const to = from + delta;
    if (to < 0 || to >= items.length) return;
    items.splice(from, 1);
    items.splice(to, 0, item);
    items.forEach(it => list.append(it.card));
    refresh();
    notifyChange(el);
  }

  function removeItem(item) {
    items.splice(items.indexOf(item), 1);
    item.card.remove();
    refresh();
    notifyChange(el);
  }

  add.addEventListener("click", () => {
    const item = addItem({});
    item.card.querySelector("input, textarea")?.focus();
  });

  return {
    el,
    get: () => items.map(item => item.form.get()),
    set(values) {
      items.splice(0).forEach(item => item.card.remove());
      (values || []).forEach(value => addItem(value));
      refresh();
    },
  };
}

function createField(def) {
  switch (def.type) {
    case "textarea": return textareaField(def);
    case "select": return selectField(def);
    case "toggle": return toggleField(def);
    case "lines": return linesField(def);
    case "image": return imageField(def);
    case "document": return documentField(def);
    case "repeat": return repeatField(def);
    case "number": return inputField(def, "number");
    case "password": return inputField(def, "password");
    case "color": return inputField(def, "color");
    case "emoji": return inputField({ ...def, maxlength: 10 }, "text");
    default: return inputField(def, "text");
  }
}

function emptyValue(def) {
  if (def.type === "repeat") return [];
  if (def.type === "toggle") return false;
  if (def.type === "number") return 0;
  if (def.type === "lines") return def.json ? "[]" : [];
  return "";
}

function wrap(def, field) {
  const classes = "form-group" + (def.half ? "" : " form-group--full");
  const help = def.help ? h("small", { class: "help" }, def.help) : null;
  if (def.type === "toggle") {
    return h("div", { class: classes }, h("label", { class: "toggle" }, field.el, def.label), help);
  }
  return h("div", { class: classes }, h("label", {}, def.label, def.required ? " *" : ""), field.el, help);
}

export function createForm(defs) {
  const fields = defs.map(def => ({ def, field: createField(def) }));
  const el = h("div", { class: "form-grid" }, fields.map(({ def, field }) => wrap(def, field)));
  const form = {
    el,
    get: () => Object.fromEntries(fields.map(({ def, field }) => [def.name, field.get()])),
    set(values = {}) {
      fields.forEach(({ def, field }) => field.set(values[def.name] ?? def.default ?? emptyValue(def)));
    },
  };
  form.set({});
  return form;
}

export { repeatField };
