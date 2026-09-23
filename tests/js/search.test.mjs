// Pontuação da busca do portal. Roda com: node --test tests/js
import assert from "node:assert/strict";
import { test } from "node:test";

import { normalize, rank } from "../../static/js/search.js";

const item = (title, text = "", type = "FAQ") => ({ title, text, type });

const ITEMS = [
  item("Churrasqueira", "Capacidade 15 pessoas", "Área"),
  item("E a churrasqueira?", "Reserva com 48h e taxa de 5% do salário mínimo."),
  item("Um corretor pode mostrar meu apartamento? Tem horário?", "De segunda a sexta das 9h às 17h."),
  item("A academia funciona 24 horas? Posso levar visita ou personal?", "Funciona todos os dias, 24 horas."),
  item("Como funciona o Espaço Pet?", "O horário é das 8h às 22h."),
  item("Salão de Festas", "Área comum para eventos", "Área"),
  item("Zeladoria", "(11) 3333-4444", "Contato"),
];

test("normalize tira acento e caixa", () => {
  assert.equal(normalize("Salão de Festas"), "salao de festas");
});

test("acha pelo título mesmo sem acento", () => {
  const [first] = rank("salao", ITEMS);
  assert.equal(first.title, "Salão de Festas");
});

test("quem casa com todas as palavras vem primeiro", () => {
  const titles = rank("churrasqueira taxa", ITEMS).map(x => x.title);
  assert.equal(titles[0], "E a churrasqueira?");
});

test("sem item que case com tudo, mostra o parcial mais relevante", () => {
  // "horário da academia": nenhuma FAQ tem as duas palavras ("24 horas", não "horário").
  // "academia" é palavra rara e tem que ganhar de "horário", que aparece em vários itens.
  const titles = rank("horario da academia", ITEMS).map(x => x.title);
  assert.match(titles[0], /academia/);
  assert.ok(titles.indexOf("Um corretor pode mostrar meu apartamento? Tem horário?") > 0);
});

test("com três palavras, ignora quem casa só uma", () => {
  // salao + festas casam; "E a churrasqueira?" casa só "taxa" e fica de fora
  assert.deepEqual(rank("taxa do salao de festas", ITEMS).map(x => x.title), ["Salão de Festas"]);
});

test("título vence corpo", () => {
  const titles = rank("churrasqueira", ITEMS).map(x => x.title);
  assert.deepEqual(titles.slice(0, 2), ["Churrasqueira", "E a churrasqueira?"]);
});

test("começo da palavra vence o meio", () => {
  const items = [item("Playground", "", "Área"), item("Como funciona o Espaço Pet?", "cães e gatos no playground")];
  assert.equal(rank("play", items)[0].title, "Playground");
});

test("acha no corpo quando o título não tem a palavra", () => {
  assert.equal(rank("3333", ITEMS)[0].title, "Zeladoria");
});

test("ignora palavras curtas e de ligação", () => {
  assert.equal(rank("o que e a churrasqueira", ITEMS)[0].title, "Churrasqueira");
});

test("busca vazia ou só com stopwords não retorna nada", () => {
  assert.deepEqual(rank("   ", ITEMS), []);
  assert.deepEqual(rank("de", ITEMS), []);
});

test("limita a quantidade de resultados", () => {
  const many = Array.from({ length: 20 }, (_, i) => item(`Aviso ${i}`, "manutenção do elevador"));
  assert.equal(rank("aviso", many).length, 8);
  assert.equal(rank("aviso", many, { limit: 3 }).length, 3);
});

test("sinônimo genérico acha o conteúdo do condomínio", () => {
  const items = [
    item("PS Municipal Barra Funda", "Pronto socorro 24h", "Perto daqui"),
    item("Como funciona o Espaço Pet?", "Área para cães e gatos", "FAQ"),
  ];
  assert.equal(rank("hospital", items)[0].title, "PS Municipal Barra Funda");
  assert.match(rank("cachorro", items)[0].title, /Pet/);
});

test("havendo item que casa com tudo, o parcial some da lista", () => {
  const titles = rank("churrasqueira taxa", ITEMS).map(x => x.title);
  assert.deepEqual(titles, ["E a churrasqueira?"]);
});
