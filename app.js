const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
let cat = "all", dev = "desktop", current = null, lastFocus = null;

// ---------- panel ----------
$("filters").innerHTML = Object.entries(CATS).map(([k, l]) =>
  `<button data-c="${k}" class="${k === "all" ? "on" : ""}">${l}</button>`).join("");
$("filters").onclick = e => {
  const b = e.target.closest("button"); if (!b) return;
  cat = b.dataset.c;
  [...$("filters").children].forEach(x => x.classList.toggle("on", x === b));
  drawGrid();
};

function thumb(p) {
  return p.img
    ? `<img src="${esc(p.img)}" alt="" loading="lazy">`
    : `<div class="ph ph-${esc(p.cat)}"><span>${{ data: "📈", game: "🀄", web: "🌐", app: "🧩" }[p.cat] || "📁"}</span></div>`;
}
function drawGrid() {
  $("grid").innerHTML = PROJECTS.filter(p => cat === "all" || p.cat === cat).map(p => {
    const live = !!p.url;
    const badge = !live ? `<span class="badge soon">Demo segera</span>`
      : p.type === "redirect" ? `<span class="badge go">Buka situs ↗</span>` : `<span class="badge live">● Demo hidup</span>`;
    return `<button class="card" data-id="${esc(p.id)}" aria-label="Buka ${esc(p.title)}">
      <div class="thumb">${thumb(p)}${badge}</div>
      <div class="body"><h2>${esc(p.title)}</h2><p class="sub">${esc(p.sub)}</p><p>${esc(p.desc)}</p>
      <div class="tags">${p.tags.map(t => `<i>${esc(t)}</i>`).join("")}</div></div></button>`;
  }).join("") || `<p class="muted">Tidak ada proyek.</p>`;
}
$("grid").onclick = e => { const c = e.target.closest(".card"); if (c) openProject(c.dataset.id, true); };

// ---------- penampil ----------
function openProject(id, push) {
  const p = PROJECTS.find(x => x.id === id); if (!p) return;
  if (p.type === "redirect" && p.url) { location.href = p.url; return; }   // game: pindah halaman
  current = p; lastFocus = document.activeElement;
  $("vTitle").textContent = p.title;
  const hint = $("vHint"); hint.hidden = !p.hint; hint.textContent = p.hint || "";
  const open = $("vOpen");
  if (p.url) { open.href = p.url; open.hidden = false; } else { open.removeAttribute("href"); open.hidden = true; }
  $("vReload").hidden = !p.url;
  $("viewer").hidden = false; document.body.classList.add("lock");
  if (push) history.pushState({ id }, "", "#" + id);
  setDevice(dev); loadStage(); $("vClose").focus();
}
function loadStage() {
  const p = current, st = $("vStage");
  if (!p.url) {
    st.innerHTML = `<div class="soon-box">${p.img ? `<img src="${esc(p.img)}" alt="Cuplikan ${esc(p.title)}">` : ""}
      <h3>${p.type === "redirect" ? "Situs game belum tersedia" : "Demo online belum tersedia"}</h3>
      <p>${esc(p.desc)}</p>${p.repo ? `<a class="vbtn" href="${esc(p.repo)}" target="_blank" rel="noopener">Lihat kode di GitHub ↗</a>` : ""}</div>`;
    return;
  }
  st.innerHTML = `<div class="loading">Memuat…</div><iframe title="${esc(p.title)}" src="${esc(p.url)}" loading="eager"
    allow="clipboard-write; fullscreen" referrerpolicy="no-referrer-when-downgrade"></iframe>`;
  st.querySelector("iframe").onload = () => st.querySelector(".loading")?.remove();
}
function setDevice(d) {
  dev = d; $("vStage").dataset.dev = d;
  [...$("vDev").children].forEach(b => b.classList.toggle("on", b.dataset.d === d));
}
function closeViewer(fromPop) {
  if (!current) return;
  $("viewer").hidden = true; $("vStage").innerHTML = ""; document.body.classList.remove("lock"); current = null;
  if (!fromPop && location.hash) history.pushState(null, "", location.pathname + location.search);
  lastFocus && lastFocus.focus && lastFocus.focus();
}
$("vClose").onclick = () => closeViewer(false);
$("vDev").onclick = e => { const b = e.target.closest("button"); if (b) setDevice(b.dataset.d); };
$("vReload").onclick = () => current && loadStage();
document.addEventListener("keydown", e => { if (e.key === "Escape" && current) closeViewer(false); });
window.addEventListener("popstate", () => {
  const id = location.hash.slice(1);
  if (id) openProject(id, false); else closeViewer(true);
});

drawGrid();
if (location.hash.length > 1) openProject(location.hash.slice(1), false);   // tautan langsung ke satu proyek
