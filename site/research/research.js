(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  let DATA = [];
  let currentFilter = "all";

  const FILTERS = {
    all: "Semua Riset",
    fin: "Financial AI (IDX)",
    gov: "Public Sector (LKPP)",
    geo: "Geospatial & Climate (Sentinel-2)"
  };

  async function init() {
    try {
      const res = await fetch("research_data.json");
      DATA = await res.json();
      renderFilters();
      renderGrid();
      setupEvents();
      checkHash();
    } catch (err) {
      console.error("Gagal memuat research_data.json:", err);
      $("grid").innerHTML = `<p class="foot">Gagal memuat data riset.</p>`;
    }
  }

  function renderFilters() {
    $("filters").innerHTML = Object.entries(FILTERS)
      .map(([k, label]) => `<button data-f="${k}" class="${k === currentFilter ? "on" : ""}">${label}</button>`)
      .join("");

    $("filters").querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => {
        currentFilter = btn.dataset.f;
        renderFilters();
        renderGrid();
      });
    });
  }

  function renderGrid() {
    const filtered = currentFilter === "all" ? DATA : DATA.filter((d) => d.category === currentFilter);

    $("grid").innerHTML = filtered.map((item) => {
      const sourcesHtml = item.sources
        .map((s) => `<li>${esc(s)}</li>`)
        .join("");

      const metricsHtml = item.metrics
        .map(([lbl, val]) => `<div class="m-item"><small>${esc(lbl)}</small><b>${esc(val)}</b></div>`)
        .join("");

      return `
        <article class="card" data-id="${esc(item.id)}">
          <div class="c-meta">
            <span class="pill ${esc(item.category)}">${esc(item.category_label)}</span>
            <span style="font-size:12px; color:var(--mut); margin-left:auto;">${esc(item.period)}</span>
          </div>
          <h2>${esc(item.title)}</h2>
          <div class="c-sub">${esc(item.subtitle)}</div>
          <p class="c-lead">${esc(item.lead)}</p>
          
          <div class="m-grid">${metricsHtml}</div>
          
          <div class="sources-box">
            <div class="sources-title">Sumber Data Resmi</div>
            <ul>${sourcesHtml}</ul>
          </div>
          
          <button class="c-btn">Baca Technical Whitepaper →</button>
        </article>
      `;
    }).join("");

    $("grid").querySelectorAll(".card").forEach((card) => {
      card.addEventListener("click", () => {
        openPaper(card.dataset.id);
      });
    });
  }

  function parseMarkdown(md) {
    if (!md) return "";
    let html = esc(md);

    // Headings
    html = html.replace(/^### (.*$)/gim, "<h3>$1</h3>");
    html = html.replace(/^## (.*$)/gim, "<h2>$1</h2>");
    html = html.replace(/^# (.*$)/gim, "<h1>$1</h1>");

    // Bold & italic
    html = html.replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
    html = html.replace(/\*([^*]+)\*/g, "<i>$1</i>");

    // Code blocks
    html = html.replace(/```([\s\S]*?)```/gm, (m, code) => {
      return `<pre><code>${code.trim()}</code></pre>`;
    });
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

    // Horizontal rules
    html = html.replace(/^---$/gim, "<hr style='border:0;border-top:1px solid var(--line);margin:32px 0;'>");

    // Tables (simple markdown tables)
    html = html.replace(/\|(.+)\|/g, (match) => {
      return match;
    });

    const lines = html.split("\n");
    let inTable = false;
    let tableHtml = "";
    let processedLines = [];

    for (let line of lines) {
      line = line.trim();
      if (line.startsWith("|") && line.endsWith("|")) {
        if (line.includes("---")) {
          // Separator line
          continue;
        }
        if (!inTable) {
          inTable = true;
          tableHtml = "<table><tbody>";
        }
        const cells = line.slice(1, -1).split("|").map(c => `<td>${c.trim()}</td>`).join("");
        tableHtml += `<tr>${cells}</tr>`;
      } else {
        if (inTable) {
          tableHtml += "</tbody></table>";
          processedLines.push(tableHtml);
          inTable = false;
        }
        if (line) {
          if (!line.startsWith("<h") && !line.startsWith("<pre") && !line.startsWith("<hr")) {
            processedLines.push(`<p>${line}</p>`);
          } else {
            processedLines.push(line);
          }
        }
      }
    }
    if (inTable) {
      tableHtml += "</tbody></table>";
      processedLines.push(tableHtml);
    }

    return processedLines.join("\n");
  }

  function renderMathInElement(element) {
    if (window.katex) {
      // Inline math: $...$
      element.innerHTML = element.innerHTML.replace(/\$([^\$\n]+)\$/g, (match, expr) => {
        try {
          return window.katex.renderToString(expr.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">"), { displayMode: false });
        } catch (e) {
          return match;
        }
      });
      // Block math: $$...$$
      element.innerHTML = element.innerHTML.replace(/\$\$([^\$]+)\$\$/g, (match, expr) => {
        try {
          return window.katex.renderToString(expr.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">"), { displayMode: true });
        } catch (e) {
          return match;
        }
      });
    }
  }

  function openPaper(id) {
    const item = DATA.find((d) => d.id === id);
    if (!item) return;

    window.location.hash = id;
    document.body.classList.add("lock");
    $("sheet").hidden = false;

    $("sBadge").textContent = item.status_badge;

    const parsedHtml = parseMarkdown(item.paper_content);

    $("paperView").innerHTML = `
      <div class="paper-meta">
        <div><b>Penulis:</b> ${esc(item.author)} (${esc(item.affiliation)})</div>
        <div><b>Bidang:</b> ${esc(item.tags.join(" · "))}</div>
        <div><b>Kode & Modul:</b> <code>${esc(item.repo_folder)}</code></div>
      </div>
      <div class="paper-content" id="paperBody">${parsedHtml}</div>
    `;

    renderMathInElement($("paperBody"));
  }

  function closePaper() {
    $("sheet").hidden = true;
    document.body.classList.remove("lock");
    history.pushState("", document.title, window.location.pathname + window.location.search);
  }

  function setupEvents() {
    $("sBack").addEventListener("click", closePaper);
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !$("sheet").hidden) {
        closePaper();
      }
    });
  }

  function checkHash() {
    const hash = window.location.hash.replace("#", "");
    if (hash && DATA.some((d) => d.id === hash)) {
      openPaper(hash);
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();
