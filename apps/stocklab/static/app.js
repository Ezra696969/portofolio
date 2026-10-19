/* StockLab — antarmuka Flask/JS.
   Susunan panel, kontrol, nilai awal, dan teks mengikuti stocklab/ui/app.py dan panels.py.
   Perhitungan tidak dilakukan di sini; semua dari server (paket stocklab). */
(() => {
"use strict";

// ---------------------------------------------------------------- util
const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
function el(tag, attrs, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "class") n.className = v;
    else if (k === "html") n.innerHTML = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) if (kid !== null && kid !== undefined && kid !== false) n.append(kid.nodeType ? kid : document.createTextNode(kid));
  return n;
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const decimals = (step) => { const s = String(step); return s.includes(".") ? s.split(".")[1].length : 0; };

/** Markdown secukupnya (tebal, kode, daftar, paragraf) untuk teks chat dan penjelasan panel. */
function md(text) {
  const inline = (s) => esc(s).replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
  const out = []; let list = null, para = [];
  const flushPara = () => { if (para.length) { out.push("<p>" + para.map(inline).join("<br>") + "</p>"); para = []; } };
  const flushList = () => { if (list) { out.push(`<${list.t}>` + list.items.map((i) => `<li>${inline(i)}</li>`).join("") + `</${list.t}>`); list = null; } };
  for (const line of String(text ?? "").split("\n")) {
    const ul = /^\s*[-*]\s+(.*)$/.exec(line), ol = /^\s*\d+[.)]\s+(.*)$/.exec(line);
    if (ul || ol) { flushPara(); const t = ul ? "ul" : "ol"; if (!list || list.t !== t) { flushList(); list = { t, items: [] }; } list.items.push((ul || ol)[1]); }
    else if (!line.trim()) { flushPara(); flushList(); }
    else { flushList(); para.push(line); }
  }
  flushPara(); flushList();
  return `<div class="md">${out.join("")}</div>`;
}

// ---------------------------------------------------------------- widget
const helpIcon = (tip) => (tip ? el("span", { class: "help", "data-tip": tip, tabindex: "0" }, "?") : null);
const caption = (text) => el("div", { class: "caption", html: esc(text) });
const alertBox = (kind, html) => el("div", { class: "alert " + kind, html });

function field(label, control, tip) {
  return el("div", { class: "field" }, label ? el("div", { class: "lbl" }, label, helpIcon(tip)) : null, control);
}

function slider({ label, min, max, step, value, tip, onChange, fmt }) {
  const dec = Math.max(0, decimals(step));
  const show = fmt || ((v) => (Number.isInteger(step) ? String(Math.round(v)) : Number(v).toFixed(Math.max(2, dec))));
  const val = el("span", { class: "val" }, show(value));
  const input = el("input", { type: "range", min, max, step, value });
  const fill = () => input.style.setProperty("--pct", ((input.value - min) / (max - min)) * 100 + "%");
  fill();
  input.addEventListener("input", () => { const v = Number(input.value); val.textContent = show(v); fill(); onChange(v); });
  return el("div", { class: "field slider" },
    el("div", { class: "top" }, el("div", { class: "lbl", style: "margin:0" }, label, helpIcon(tip)), val),
    input,
    el("div", { class: "ends" }, el("span", {}, show(min)), el("span", {}, show(max))));
}

function select({ label, options, value, tip, onChange }) {
  const sel = el("select", {}, options.map((o, i) => el("option", { value: i, selected: JSON.stringify(o.value) === JSON.stringify(value) }, o.label)));
  sel.addEventListener("change", () => onChange(options[Number(sel.value)].value));
  return field(label, sel, tip);
}

function radio({ label, options, value, tip, onChange }) {
  const name = "r" + Math.random().toString(36).slice(2);
  const box = el("div", { class: "radios" }, options.map((o) => {
    const inp = el("input", { type: "radio", name, checked: o.value === value });
    inp.addEventListener("change", () => onChange(o.value));
    return el("label", {}, inp, o.label);
  }));
  return field(label, box, tip);
}

function checkbox({ label, value, tip, onChange }) {
  const inp = el("input", { type: "checkbox", checked: !!value });
  inp.addEventListener("change", () => onChange(inp.checked));
  return el("div", { class: "field" }, el("label", { class: "check" }, inp, label, helpIcon(tip)));
}

function toggle({ label, value, onChange }) {
  const inp = el("input", { type: "checkbox", checked: !!value });
  inp.addEventListener("change", () => onChange(inp.checked));
  return el("div", { class: "field" }, el("label", { class: "toggle" }, inp, el("span", { class: "sw" }), label));
}

function numberInput({ label, value, min, max, step, tip, onChange }) {
  const inp = el("input", { type: "number", value, min, max, step });
  const commit = () => { let v = Number(inp.value); if (Number.isNaN(v)) return; if (min !== undefined) v = Math.max(min, v); if (max !== undefined) v = Math.min(max, v); onChange(v); };
  inp.addEventListener("change", () => { commit(); });
  const bump = (d) => { let v = (Number(inp.value) || 0) + d * step; if (min !== undefined) v = Math.max(min, v); if (max !== undefined) v = Math.min(max, v); inp.value = Number(v.toFixed(8)); onChange(Number(inp.value)); };
  return field(label, el("div", { class: "numwrap" }, inp, el("button", { type: "button", onclick: () => bump(-1) }, "−"), el("button", { type: "button", onclick: () => bump(1) }, "+")), tip);
}

function dateInput({ label, value, tip, onChange }) {
  const inp = el("input", { type: "date", value: value || "" });
  inp.addEventListener("change", () => onChange(inp.value));
  return field(label, inp, tip);
}

function multiselect({ label, options, value, tip, onChange }) {
  let current = [...value];
  const root = el("div", { class: "ms" });
  const box = el("div", { class: "box", tabindex: "0" });
  const menu = el("div", { class: "menu" });
  const label_of = (v) => (options.find((o) => o.value === v) || { label: v }).label;
  const draw = () => {
    box.replaceChildren(...current.map((v) => el("span", { class: "tag" }, label_of(v), el("button", { type: "button", "aria-label": "Hapus", onclick: (e) => { e.stopPropagation(); current = current.filter((x) => x !== v); draw(); onChange(current); } }, "×"))));
    const rest = options.filter((o) => !current.includes(o.value));
    menu.replaceChildren(...(rest.length ? rest.map((o) => el("div", { onclick: () => { current = [...current, o.value]; root.classList.remove("open"); draw(); onChange(current); } }, o.label)) : [el("div", { class: "none" }, "Tidak ada pilihan lain")]));
  };
  box.addEventListener("click", () => root.classList.toggle("open"));
  document.addEventListener("click", (e) => { if (!root.contains(e.target)) root.classList.remove("open"); });
  draw();
  root.append(box, menu);
  return field(label, root, tip);
}

function uploader({ label, accept, hint, onChange }) {
  const input = el("input", { type: "file", accept, class: "hidden" });
  const info = el("span", {}, hint);
  const drop = el("div", { class: "drop" }, info, el("button", { type: "button", class: "btn", style: "width:auto;padding:.3rem .8rem", onclick: () => input.click() }, "Browse files"));
  const show = (f) => {
    if (!f) { info.textContent = hint; return; }
    info.replaceChildren(el("span", { class: "file" }, `${f.name} (${(f.size / 1024).toFixed(1)}KB)`, el("button", { type: "button", "aria-label": "Hapus berkas", onclick: () => { input.value = ""; show(null); onChange(null); } }, "×")));
  };
  input.addEventListener("change", () => { const f = input.files[0] || null; show(f); onChange(f); });
  drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
  drop.addEventListener("dragleave", () => drop.classList.remove("over"));
  drop.addEventListener("drop", (e) => { e.preventDefault(); drop.classList.remove("over"); const f = e.dataTransfer.files[0]; if (f) { show(f); onChange(f); } });
  return field(label, el("div", {}, input, drop));
}

function expander(title, content, open) {
  return el("details", { class: "exp", open: !!open }, el("summary", {}, title), el("div", { class: "inner" }, content));
}

// ---------------------------------------------------------------- tabel & blok
function fmtCell(v) {
  if (v === null || v === undefined) return "None";
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toLocaleString("en-US", { maximumFractionDigits: 4, useGrouping: false });
  return String(v);
}
function table(block) {
  const cols = [block.index_name || "", ...block.columns];
  let rows = block.rows.map((r) => r.slice());
  let sortCol = -1, asc = true;
  const wrap = el("div", { class: "tablewrap" });
  if (block.height) wrap.style.maxHeight = block.height + "px";
  const draw = () => {
    const ths = cols.map((c, i) => el("th", { class: i > 0 ? "num" : "", onclick: () => { if (sortCol === i) asc = !asc; else { sortCol = i; asc = true; } rows.sort((a, b) => { const x = a[i], y = b[i]; if (x === y) return 0; if (x === null) return 1; if (y === null) return -1; return (x > y ? 1 : -1) * (asc ? 1 : -1); }); draw(); } }, c + (sortCol === i ? (asc ? " ▲" : " ▼") : "")));
    const body = rows.map((r) => el("tr", {}, r.map((v, i) => el("td", { class: typeof v === "number" ? "num" : "" }, fmtCell(v)))));
    wrap.replaceChildren(el("table", { class: "df" }, el("thead", {}, el("tr", {}, ths)), el("tbody", {}, body)));
  };
  draw();
  return wrap;
}
function metricRow(block) {
  return el("div", { class: "metric-row" }, block.items.map((m) => el("div", { class: "metric" + (m.label === block.accent ? " is-accent" : "") },
    el("div", { class: "label" }, m.label), el("div", { class: "value" }, m.value), m.sub ? el("div", { class: "sub" }, m.sub) : null)));
}
function concerns(block) {
  if (!block.items.length) return block.empty ? el("div", { class: "clear" }, block.empty) : null;
  return el("div", {}, block.items.map((c) => el("div", { class: "concern" }, el("span", { class: "mark" }, "!"), el("span", {}, c))));
}
function renderBlock(b) {
  switch (b.type) {
    case "md": return el("div", { html: md(b.text) });
    case "caption": return caption(b.text);
    case "metrics": return metricRow(b);
    case "table": return table(b);
    case "concerns": return concerns(b);
    default: return null;
  }
}
function title(text, note) { return [el("p", { class: "panel-title" }, text), note ? el("p", { class: "panel-note" }, note) : null].filter(Boolean); }

function plot(container, fig, height) {
  const div = el("div", { style: height ? `height:${height}px` : "" });
  container.append(div);
  if (window.Plotly) {
    Plotly.newPlot(div, fig.data, fig.layout, { displayModeBar: false, responsive: true });
  } else {
    div.append(caption("Grafik membutuhkan plotly.js (gagal dimuat dari CDN)."));
  }
  return div;
}

// ---------------------------------------------------------------- keadaan
let META = null, SNAP = null, busy = false;
const F = { source: "Ticker", ticker: null, start: null, end: null, capital: 100000, cost: 10, slippage: 5, train: 252, test: 21, expanding: true, horizon: 1,
  universe: [], model: null, sizing: "binary", threshold: 0.5, allowPickle: false, trainEnd: "", features: [] };
const V = {};            // nilai kontrol parameter, kunci seperti di versi Streamlit: feat_<n>_<p> / param_<model>_<p>
const FILES = { csv: null, model: null };
let tabIndex = 0;

async function api(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) { let m = r.statusText; try { m = (await r.json()).error || m; } catch (e) { /* abaikan */ } throw new Error(m); }
  return r.json();
}

// ---------------------------------------------------------------- kontrol parameter
function renderParams(specs, prefix) {
  const nodes = [];
  for (const spec of specs) {
    if (!spec.editable) continue;                 // kind "opaque" sengaja dilewati
    const key = `${prefix}_${spec.name}`;
    if (!(key in V)) V[key] = spec.default;
    const on = (v) => { V[key] = v; };
    if (spec.kind === "bool") nodes.push(checkbox({ label: spec.label, value: V[key], tip: spec.help, onChange: on }));
    else if (spec.kind === "choice" && spec.choices) nodes.push(select({ label: spec.label, options: spec.choices.map((c) => ({ value: c, label: c === null ? "otomatis" : String(c) })), value: V[key], tip: spec.help, onChange: on }));
    else if (spec.kind === "int" && spec.bounded) nodes.push(slider({ label: spec.label, min: spec.low, max: spec.high, step: spec.step || 1, value: V[key], tip: spec.help, onChange: on }));
    else if (spec.kind === "float" && spec.bounded) nodes.push(slider({ label: spec.label, min: spec.low, max: spec.high, step: spec.step || 0.01, value: V[key], tip: spec.help, onChange: on }));
    else if (spec.kind === "int" || spec.kind === "float") nodes.push(numberInput({ label: spec.label, value: V[key], step: spec.kind === "int" ? 1 : 0.01, tip: spec.help, onChange: on }));
  }
  return nodes;
}
const modelEntry = () => META.models.find((m) => m.name === F.model);

// ---------------------------------------------------------------- sidebar
function renderSidebar() {
  const sb = $("#sidebar");
  const horizonCaption = el("div", { class: "caption" });
  const setHorizon = () => { horizonCaption.textContent = `Embargo mengikuti horizon (${F.horizon} bar) supaya label tidak membocorkan periode uji ke data latih.`; };
  setHorizon();
  const tickerField = select({ label: "Simbol", options: META.presets.map((t) => ({ value: t, label: t })), value: F.ticker, onChange: (v) => { F.ticker = v; } });
  const csvField = uploader({ label: "CSV harga", accept: ".csv", hint: "Drag and drop file here · Limit 200MB per file · CSV", onChange: (f) => { FILES.csv = f; } });
  csvField.classList.add("hidden");
  const trialBox = el("div", { id: "trialbox" });

  sb.replaceChildren(
    el("h3", {}, "Data"),
    radio({ label: "Sumber", options: [{ value: "Ticker", label: "Ticker" }, { value: "Berkas CSV", label: "Berkas CSV" }], value: F.source, onChange: (v) => { F.source = v; tickerField.classList.toggle("hidden", v !== "Ticker"); csvField.classList.toggle("hidden", v === "Ticker"); } }),
    tickerField, csvField,
    el("div", { class: "two" },
      dateInput({ label: "Mulai", value: F.start, onChange: (v) => { F.start = v; } }),
      dateInput({ label: "Sampai", value: F.end, onChange: (v) => { F.end = v; } })),
    el("h3", {}, "Backtest"),
    numberInput({ label: "Modal awal", value: F.capital, min: 1000, max: 10000000000, step: 10000, onChange: (v) => { F.capital = v; } }),
    slider({ label: "Biaya transaksi (bps)", min: 0, max: 60, step: 0.5, value: F.cost, onChange: (v) => { F.cost = v; } }),
    slider({ label: "Slippage (bps)", min: 0, max: 30, step: 0.5, value: F.slippage, onChange: (v) => { F.slippage = v; } }),
    caption("Keduanya per satu sisi transaksi. Strategi ber-turnover tinggi sangat sensitif terhadap angka ini — jalankan Validasi untuk melihat titik impasnya."),
    el("h3", {}, "Walk-forward"),
    slider({ label: "Jendela latih (bar)", min: 60, max: 756, step: 21, value: F.train, onChange: (v) => { F.train = v; } }),
    slider({ label: "Latih ulang tiap (bar)", min: 5, max: 126, step: 1, value: F.test, onChange: (v) => { F.test = v; } }),
    toggle({ label: "Jendela membesar", value: F.expanding, onChange: (v) => { F.expanding = v; } }),
    slider({ label: "Horizon prediksi (bar)", min: 1, max: 10, step: 1, value: F.horizon, onChange: (v) => { F.horizon = v; setHorizon(); } }),
    horizonCaption,
    el("h3", {}, "Lintas saham"),
    multiselect({ label: "Aset pembanding", options: META.presets.map((t) => ({ value: t, label: t })), value: F.universe, tip: "Alur yang sama dijalankan pada tiap aset. Ini pemeriksaan paling lama, dan yang paling sering membantah hasil yang lolos pemeriksaan lain.", onChange: (v) => { F.universe = v; updateButtons(); } }),
    trialBox);
}

function renderTrials() {
  const box = $("#trialbox"); if (!box) return;
  const t = SNAP.trials;
  if (!t.n_runs) { box.replaceChildren(); return; }
  box.replaceChildren(el("hr"), caption(`${t.n_runs} run, ${t.n_distinct} konfigurasi berbeda. Jumlah ini masuk ke koreksi deflated Sharpe.`),
    el("button", { class: "btn", style: "width:auto", onclick: async () => { await api("api/reset_trials", { method: "POST" }); await refresh(); } }, "Reset hitungan"));
}

// ---------------------------------------------------------------- panel bawah
function renderModelPanel() {
  const p = $("#p-model"); const entry = modelEntry();
  const names = META.models;
  const modelBox = [];
  modelBox.push(...title("Model"));
  modelBox.push(select({ label: "Algoritma", options: names.map((m) => ({ value: m.name, label: m.label })), value: F.model, onChange: (v) => { F.model = v; renderModelPanel(); renderParamPanel(); } }));
  modelBox.push(caption(entry.description));
  if (entry.kind === "forecast") modelBox.push(alertBox("info", "Peramal deret waktu membaca riwayat harga, bukan indikator. Pilih <b>Harga</b> di panel Indikator; indikator lain diabaikan."));
  modelBox.push(radio({ label: "Ukuran posisi", options: [{ value: "binary", label: "Penuh / kas" }, { value: "scaled", label: "Ikut keyakinan" }], value: F.sizing, tip: "Penuh/kas: masuk sepenuhnya atau tidak sama sekali. Ikut keyakinan: prediksi yang ragu mendapat modal lebih kecil.", onChange: (v) => { F.sizing = v; } }));
  modelBox.push(slider({ label: "Ambang keyakinan", min: 0.5, max: 0.8, step: 0.01, value: F.threshold, tip: "Menaikkannya membuat model lebih pemilih dan menurunkan turnover.", onChange: (v) => { F.threshold = v; } }));

  // Model sendiri (upload artifact)
  const risk = el("div");
  const drawRisk = () => {
    risk.replaceChildren(F.allowPickle ? alertBox("warning", esc(META.pickle_risk_on)) : caption(META.pickle_risk_off));
    if (F.allowPickle && !META.pickle_allowed) risk.append(alertBox("info", "Di server publik ini format pickle/joblib dinonaktifkan karena menjalankan kode dari berkas yang diunggah. ONNX tetap bisa dipakai."));
  };
  drawRisk();
  const inner = el("div", {},
    checkbox({ label: "Izinkan format pickle (.joblib / .pkl)", value: F.allowPickle, onChange: (v) => { F.allowPickle = v; drawRisk(); } }),
    risk,
    uploader({ label: "Artifact model", accept: ".onnx,.joblib,.pkl", hint: "Drag and drop file here · Limit 200MB per file · ONNX, JOBLIB, PKL", onChange: (f) => { FILES.model = f; } }),
    dateInput({ label: "Data latih berakhir (opsional)", value: F.trainEnd, tip: "Kalau diisi, backtest dimulai setelah tanggal ini. Aplikasi tidak punya cara memeriksa apakah model sudah pernah melihat periode yang diuji; kalau dikosongkan, hasilnya jadi tanggung jawabmu.", onChange: (v) => { F.trainEnd = v; } }));
  modelBox.push(expander("Model sendiri", inner, false));
  p.replaceChildren(...modelBox.filter(Boolean));
}

function renderIndicatorPanel() {
  const p = $("#p-indicators");
  const nodes = [...title("Indikator")];
  nodes.push(multiselect({ label: "Dipakai sebagai fitur", options: META.features.map((f) => ({ value: f.name, label: f.label })), value: F.features, onChange: (v) => { F.features = v; renderIndicatorPanel(); } }));
  for (const name of F.features) {
    const spec = META.features.find((f) => f.name === name);
    nodes.push(expander(spec.label, [caption(spec.description), ...renderParams(spec.params, `feat_${name}`)], F.features.length <= 2));
  }
  if (!F.features.length) nodes.push(caption("Pilih minimal satu indikator."));
  p.replaceChildren(...nodes);
}

function renderParamPanel() {
  const p = $("#p-params"); const entry = modelEntry();
  const nodes = [...title("Parameter Model", entry.label), ...renderParams(entry.params, `param_${entry.name}`)];
  const hidden = entry.params.filter((s) => !s.editable).map((s) => s.name);
  if (hidden.length) nodes.push(caption(`${hidden.length} parameter tidak ditampilkan karena tipenya tidak bisa diwakili satu kontrol: ${hidden.join(", ")}.`));
  p.replaceChildren(...nodes);
}

// ---------------------------------------------------------------- panel hasil
function renderChart() {
  const p = $("#p-chart"); const c = SNAP.chart;
  if (!c) { p.replaceChildren(...title("Kurva Ekuitas"), el("div", { class: "placeholder", html: "Pilih model dan indikator di panel bawah,<br>lalu tekan Jalankan." })); return; }
  p.replaceChildren(...title("Kurva Ekuitas", c.note));
  plot(p, c.figure, c.figure.layout.height || 372);
  p.append(el("div", { style: "height:14px" }), metricRow(c.metrics));
}

function renderChat() {
  const p = $("#p-chat"); const chat = SNAP.chat;
  const hist = el("div", { class: "history" });
  const bubble = (role, text) => el("div", { class: "msg " + role }, el("div", { class: "av" }, role === "user" ? "🙂" : "🤖"), el("div", { class: "body", html: md(text) }));
  if (!chat.messages.length) hist.append(bubble("assistant", chat.greeting));
  chat.messages.forEach((m) => hist.append(bubble(m.role, m.content)));
  const input = el("textarea", { placeholder: "Tanya tentang hasil backtest...", rows: "1", maxlength: "2000" });
  const send = el("button", { type: "button", "aria-label": "Kirim" }, "➤");
  input.disabled = send.disabled = busy;
  const submit = () => { const q = input.value.trim(); if (!q || busy) return; runJob("api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: q }) }); };
  send.addEventListener("click", submit);
  input.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); } });
  p.replaceChildren(...title("Asisten", chat.note), hist, el("div", { class: "chatin" }, input, send));
  hist.scrollTop = hist.scrollHeight;
}

function renderValidation() {
  const p = $("#p-validation"); const v = SNAP.validation;
  p.replaceChildren(...title("Validasi", v.note));
  if (!v.report) { p.append(caption(v.empty)); return; }
  const r = v.report;
  p.append(concerns(r.concerns) || "");
  const body = el("div");
  const tabs = el("div", { class: "tabs" }, r.tabs.map((t, i) => el("button", { type: "button", class: i === tabIndex ? "on" : "", onclick: () => { tabIndex = i; renderValidation(); } }, t.label)));
  r.tabs[tabIndex].blocks.forEach((b) => body.append(renderBlock(b) || ""));
  p.append(tabs, body);
  if (r.deflated) p.append(el("div", { class: "deflated", html: `Deflated Sharpe <b>${r.deflated.value.toFixed(3)}</b> — peluang Sharpe ini benar-benar positif setelah memperhitungkan ${r.deflated.n} konfigurasi yang dicoba.` }));
}

function renderCross() {
  const p = $("#p-cross"); const c = SNAP.cross;
  p.replaceChildren(...title("Lintas Saham"));
  if (!c.report) { p.append(caption(c.empty)); return; }
  const r = c.report;
  p.append(concerns(r.concerns) || "", metricRow(r.metrics));
  plot(p, r.figure, r.figure.layout.height);
  p.append(expander("Angka per aset", table(r.table), false));
}

// ---------------------------------------------------------------- tombol, status, pekerjaan
function updateButtons() {
  const has = SNAP && SNAP.has_result;
  $("#b-run").disabled = busy;
  $("#b-validate").disabled = busy || !has;
  $("#b-cross").disabled = busy || !has || F.universe.length < 2;
}
function setStatus(job, error) {
  const s = $("#status"); s.replaceChildren();
  if (error) { s.append(alertBox("error", esc(error))); return; }
  if (!job || !(job.status === "queued" || job.status === "running")) return;
  if (job.progress !== null && job.progress !== undefined) s.append(el("div", { style: "width:100%" }, el("div", { class: "progress" }, el("i", { style: `width:${Math.round(job.progress * 100)}%` })), el("div", { class: "caption" }, job.message)));
  else s.append(el("div", { class: "status" }, el("div", { class: "spin" }), job.message));
}

function collectSettings() {
  const chosen = F.features.map((name) => {
    const spec = META.features.find((f) => f.name === name); const params = {};
    for (const s of spec.params) if (s.editable) params[s.name] = V[`feat_${name}_${s.name}`] ?? s.default;
    return { name, params };
  });
  const entry = modelEntry(); const mparams = {};
  for (const s of entry.params) if (s.editable) mparams[s.name] = V[`param_${entry.name}_${s.name}`] ?? s.default;
  return {
    source: F.source, ticker: F.ticker, start: F.start, end: F.end, universe: F.universe,
    run: { initial_capital: F.capital, cost_bps: F.cost, slippage_bps: F.slippage, train_size: F.train, test_size: F.test, expanding: F.expanding, horizon: F.horizon },
    features: chosen, model: { name: F.model, params: mparams, sizing: F.sizing, threshold: F.threshold },
    upload: { allow_pickle: F.allowPickle, train_end: F.trainEnd || null },
  };
}
function formBody(withModel) {
  const fd = new FormData();
  fd.append("settings", JSON.stringify(collectSettings()));
  if (F.source === "Berkas CSV" && FILES.csv) fd.append("csv", FILES.csv);
  if (withModel && FILES.model) fd.append("model_file", FILES.model);
  return { method: "POST", body: fd };
}

async function runJob(path, opts) {
  if (busy) return;
  busy = true; setStatus(null, null); updateButtons();
  try { await api(path, opts); }
  catch (e) { busy = false; setStatus(null, e.message); updateButtons(); return; }
  await poll();
}
async function poll() {
  busy = true; updateButtons();
  let job = null;
  for (;;) {
    try { job = await api("api/job"); } catch (e) { setStatus(null, e.message); break; }
    if (!job) break;
    setStatus(job, null);
    if (job.status === "done" || job.status === "error") break;
    if (job.kind === "chat" && !SNAP.chat.messages.some((m) => m.pending)) { /* pesan pengguna segera tampil setelah refresh berikut */ }
    await sleep(job.kind === "cross" ? 500 : 800);
  }
  busy = false;
  await refresh();
  if (job && job.status === "error") setStatus(null, job.error);
}

async function refresh() {
  SNAP = await api("api/state");
  renderChart(); renderChat(); renderValidation(); renderCross(); renderTrials(); updateButtons();
  const j = SNAP.job; if (j && (j.status === "queued" || j.status === "running") && !busy) poll();
}

// ---------------------------------------------------------------- mulai
async function init() {
  META = await api("api/meta");
  F.ticker = META.presets[0]; F.start = META.default_start; F.end = META.default_end;
  F.universe = [...META.default_universe]; F.model = META.default_model; F.features = [...META.default_features];
  renderSidebar(); renderModelPanel(); renderIndicatorPanel(); renderParamPanel();
  $("#b-run").addEventListener("click", () => runJob("api/run", formBody(true)));
  $("#b-validate").addEventListener("click", () => runJob("api/validate", formBody(false)));
  $("#b-cross").addEventListener("click", () => runJob("api/cross", formBody(false)));
  $("#toggle").addEventListener("click", () => document.body.classList.toggle(window.matchMedia("(max-width: 820px)").matches ? "side-open" : "side-closed"));
  await refresh();
}
init().catch((e) => { document.body.prepend(el("div", { class: "alert error", style: "margin:1rem" }, "Gagal memuat aplikasi: " + e.message)); });
})();
