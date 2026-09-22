// Utilidades compartilhadas do admin: montar DOM, falar com a API, toast e upload.

// Cria um elemento. Filhos em texto viram textNode (nunca HTML), então dado do
// usuário não vira código na tela.
export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") el.className = value;
    else if (key === "value") el.value = value;
    else if (key === "checked") el.checked = Boolean(value);
    else if (key.startsWith("on")) el.addEventListener(key.slice(2), value);
    else el.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    el.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return el;
}

// ── API ──────────────────────────────────────────────────
export class ApiError extends Error {}

let onUnauthorized = () => {};
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

function errorMessage(data, status) {
  const detail = data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) {
    const first = detail[0];
    const field = (first.loc || []).filter(part => part !== "body").join(" › ");
    const message = String(first.msg || "").replace(/^Value error, /, "");
    return field ? `${field}: ${message}` : message;
  }
  if (status === 413) return "Arquivo grande demais.";
  return "Não foi possível salvar. Tente de novo.";
}

export async function api(method, url, body) {
  const options = { method, headers: {} };
  if (body instanceof FormData) {
    options.body = body;
  } else if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const res = await fetch(url, options);
  if (res.status === 401 && url !== "/api/auth") {
    onUnauthorized();
    throw new ApiError("Sessão expirada. Faça login novamente.");
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(errorMessage(data, res.status));
  return data;
}

// ── Toast ────────────────────────────────────────────────
let toastTimer = null;
export function toast(message, type = "success") {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.classList.toggle("toast--error", type === "error");
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), type === "error" ? 5000 : 3000);
}

// Roda uma ação mostrando o erro num toast em vez de estourar no console.
export async function attempt(action, successMessage) {
  try {
    const result = await action();
    if (successMessage) toast(successMessage);
    return result;
  } catch (err) {
    toast(err instanceof ApiError ? err.message : "Algo deu errado. Tente de novo.", "error");
    if (!(err instanceof ApiError)) console.error(err);
    return undefined;
  }
}

// ── Upload ───────────────────────────────────────────────
const MAX_UPLOAD_BYTES = 4 * 1024 * 1024; // a Vercel recusa corpo acima de 4,5 MB
const MAX_IMAGE_SIDE = 1600;

// Foto de celular tem 3-5 MB: reduz no navegador antes de subir. GIF fica como
// está (perderia a animação).
async function resizeImage(file) {
  if (!file.type.startsWith("image/") || file.type === "image/gif") return file;
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, MAX_IMAGE_SIDE / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#fff"; // PNG transparente viraria fundo preto no JPEG
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg", 0.85));
  return new File([blob], file.name.replace(/\.[^.]+$/, "") + ".jpg", { type: "image/jpeg" });
}

export async function uploadFile(file) {
  const prepared = await resizeImage(file);
  if (prepared.size > MAX_UPLOAD_BYTES) {
    throw new ApiError(file.type === "application/pdf"
      ? "PDF maior que 4 MB: suba no Google Drive e cole o link aqui."
      : "Arquivo maior que 4 MB.");
  }
  const form = new FormData();
  form.append("file", prepared);
  const { url } = await api("POST", "/api/upload", form);
  return url;
}
