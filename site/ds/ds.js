/* Data Science Project: kartu studi kasus dibaca dari data.json (dibangun oleh DS-BUILD/build.py). */
(() => {
"use strict";
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const md = (s) => esc(s).replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>");
let DATA = [], flt = "all", last = null;

const FILTERS = { all: "Semua", lomba: "Lomba", kuliah: "Kuliah", Python: "Python", R: "R" };
const match = (p) => flt === "all" || p.repo === flt || p.lang === flt;

function stats() {
  const lomba = DATA.filter((p) => p.repo === "lomba").length, kuliah = DATA.length - lomba;
  const r = DATA.filter((p) => p.lang === "R").length;
  $("stats").innerHTML = [[lomba, "lomba"], [kuliah, "proyek kuliah"], [DATA.length - r, "Python"], [r, "R"]]
    .map(([n, l]) => `<div class="stat"><b>${n}</b><span>${l}</span></div>`).join("");
}
function filters() {
  $("filters").innerHTML = Object.entries(FILTERS).map(([k, l]) => `<button data-f="${k}" class="${k === flt ? "on" : ""}">${l}</button>`).join("");
}
function grid() {
  $("grid").innerHTML = DATA.filter(match).map((p) => `<button class="card" data-id="${esc(p.id)}" aria-label="${esc(p.title)}">
    <div class="meta"><span class="pill ${p.repo}">${p.repo === "lomba" ? "Lomba" : "Kuliah"}</span><span class="pill ${p.lang === "R" ? "r" : "py"}">${esc(p.lang)}</span><span>${esc(p.period)}</span></div>
    <h2>${esc(p.title)}</h2><div class="sub">${esc(p.subtitle)}</div>
    <div class="tags">${p.tags.slice(0, 4).map((t) => `<i>${esc(t)}</i>`).join("")}</div>
    <div class="hero">${esc(p.metrics[0][0])}: <b>${esc(p.metrics[0][1])}</b></div></button>`).join("") || '<p class="foot">Tidak ada studi kasus.</p>';
}
function rank(p) {
  const e = (p.peringkat && p.peringkat.entries) || [];
  if (!e.length) return "";
  const rows = e.map((x) => {
    if (x.pos && x.total) {
      const top = Math.max(1, Math.round((x.pos / x.total) * 1000) / 10);
      return `<div class="row"><div class="big">${esc(x.pos)}<span> / ${esc(x.total)}</span></div>
        <div class="lbl"><b>${esc(x.label)}</b>peringkat ${esc(x.pos)} dari ${esc(x.total)} peserta (teratas ${top}%)<div class="bar"><i style="width:${Math.max(4, 100 - top)}%"></i></div></div></div>`;
    }
    return `<div class="row"><div class="big">— <span>/ —</span></div><div class="lbl"><b>${esc(x.label)}</b><span class="tbd">Peringkat dan jumlah peserta akan ditambahkan setelah pengumuman.</span></div></div>`;
  }).join("");
  return `<section class="rank"><h3>Peringkat</h3>${rows}</section>`;
}
function open(id, push) {
  const p = DATA.find((x) => x.id === id); if (!p) return;
  last = document.activeElement;
  const files = p.files.length
    ? `<ul class="files">${p.files.map((f) => `<li><a href="${esc(f.url)}" target="_blank" rel="noopener">${esc(f.name)} ↗</a>${f.note ? ` <small>— ${esc(f.note)}</small>` : ""}</li>`).join("")}</ul>`
    : (p.kode === "menyusul" ? "<p>Kode belum dipublikasikan (lihat catatan).</p>" : "");
  const link = p.link ? `<p><a href="${esc(p.link.url)}" target="_blank" rel="noopener" style="color:var(--acc2)">${esc(p.link.label)} ↗</a></p>` : "";
  $("case").innerHTML = `
    <p class="eyebrow">${p.repo === "lomba" ? "Studi kasus · Lomba" : "Studi kasus · Kuliah"}</p>
    <h1 id="sTitle">${esc(p.title)}</h1><div class="sub">${esc(p.subtitle)}</div>
    <div class="meta">${esc(p.period)} · ${esc(p.lang)}</div>
    <div class="tags">${p.tags.map((t) => `<i>${esc(t)}</i>`).join("")}</div>
    <div class="mrow">${p.metrics.map((m) => `<div class="m"><small>${esc(m[0])}</small><b>${esc(m[1])}</b></div>`).join("")}</div>
    <h3>Masalah</h3><p>${md(p.masalah)}</p>
    <h3>Data</h3><p>${md(p.data)}</p>
    <h3>Pendekatan</h3><ol>${p.pendekatan.map((x) => `<li>${md(x)}</li>`).join("")}</ol>
    <h3>Temuan</h3><ul>${p.temuan.map((x) => `<li>${md(x)}</li>`).join("")}</ul>
    ${p.catatan ? `<div class="note">${md(p.catatan)}</div>` : ""}
    <h3>Berkas</h3>${files}${link}
    <p><a href="${esc(p.url)}" target="_blank" rel="noopener" style="color:var(--acc2)">Lihat folder di GitHub ↗</a></p>
    ${p.repo === "lomba" ? rank(p) : ""}`;
  const b = $("sBadge");
  b.textContent = p.status === "berjalan" ? "Lomba berjalan" : p.kode === "menyusul" ? "Kode menyusul" : "";
  b.className = "badge" + (p.status === "berjalan" ? " live" : ""); b.hidden = !b.textContent;
  $("sheet").hidden = false; $("sheet").scrollTop = 0; document.body.classList.add("lock");
  if (push) history.pushState({ id }, "", "#" + id);
  $("sBack").focus();
}
function closeSheet(pop) {
  if ($("sheet").hidden) return;
  $("sheet").hidden = true; document.body.classList.remove("lock");
  if (!pop && location.hash) history.pushState(null, "", location.pathname + location.search);
  last && last.focus && last.focus();
}
document.addEventListener("click", (e) => {
  const f = e.target.closest("#filters button"); if (f) { flt = f.dataset.f; filters(); grid(); return; }
  const c = e.target.closest(".card"); if (c) open(c.dataset.id, true);
});
$("sBack").onclick = () => closeSheet(false);
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeSheet(false); });
window.addEventListener("popstate", () => { const id = location.hash.slice(1); id ? open(id, false) : closeSheet(true); });

fetch("data.json").then((r) => r.json()).then((d) => {
  DATA = d; stats(); filters(); grid();
  if (location.hash.length > 1) open(location.hash.slice(1), false);
}).catch((e) => { $("grid").innerHTML = `<p class="foot">Gagal memuat data: ${esc(e.message)}</p>`; });
})();
