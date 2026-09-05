const noticeEl = document.getElementById("notice");
const btnEl = document.getElementById("analyze-btn");
const clearBtnEl = document.getElementById("clear-btn");
const resultEl = document.getElementById("result");
const loadingEl = document.getElementById("loading");
const emptyEl = document.getElementById("empty");
const pickerEl = document.getElementById("sample-picker");

let samplesCache = [];

function esc(s) {
  const div = document.createElement("div");
  div.textContent = s ?? "";
  return div.innerHTML;
}

async function loadSamples() {
  const res = await fetch("/api/samples");
  samplesCache = await res.json();
  samplesCache.forEach((s, i) => {
    const opt = document.createElement("option");
    opt.value = i;
    opt.textContent = s.title;
    pickerEl.appendChild(opt);
  });
  pickerEl.addEventListener("change", () => {
    if (pickerEl.value === "") return;
    noticeEl.value = samplesCache[pickerEl.value].text;
    noticeEl.focus();
  });
}

function fmtDate(iso) {
  return iso ? iso : "-";
}

function urgencyTier(score) {
  if (score >= 100) return "critical";
  if (score >= 60) return "high";
  if (score >= 30) return "medium";
  return "low";
}

const OPTION_ICON = {
  expedite: "⚡",
  part_ship: "◨",
  reallocate: "⇄",
  notify_customer: "✉",
};

function renderOption(o, isRecommended) {
  const div = document.createElement("div");
  div.className = "option" + (isRecommended ? " recommended" : "");
  const icon = OPTION_ICON[o.kind] || "•";
  div.innerHTML = `
    <div class="option-head">
      <span class="option-icon">${icon}</span>
      <strong>${esc(o.kind.replace("_", " "))}</strong>
      ${isRecommended ? '<span class="badge-recommended">Recommended</span>' : ""}
    </div>
    <div class="option-desc">${esc(o.description)}</div>
    <div class="option-tradeoff">Trade-off: ${esc(o.trade_off)}</div>
  `;
  return div;
}

function renderOrder(o) {
  const div = document.createElement("div");
  const tier = urgencyTier(o.urgency_score);
  div.className = "order-card urgency-" + tier;
  const slip = o.slip_days === null ? "unquantified" : `${o.slip_days}d slip`;
  div.innerHTML = `
    <div class="order-head">
      <span class="order-id">${esc(o.order_id)}</span>
      <span class="tier tier-${esc(o.tier)}">${esc(o.tier)}</span>
      <span class="urgency-pill urgency-pill-${tier}">${esc(tier)} &middot; ${esc(String(o.urgency_score))}</span>
    </div>
    <div class="order-meta">${esc(o.customer)} &middot; ${esc(String(o.quantity))}&times; ${esc(o.product)} &middot; due ${esc(fmtDate(o.requested_delivery_date))} &middot; ${esc(slip)}</div>
    <div class="order-trace">source: ${esc(o.source_ids.join(", "))}</div>
  `;
  const optsWrap = document.createElement("div");
  optsWrap.className = "options";
  o.options.forEach((opt, i) => optsWrap.appendChild(renderOption(opt, i === o.recommended_index)));
  div.appendChild(optsWrap);
  return div;
}

function renderSummary(data) {
  const bar = document.createElement("div");
  bar.className = "summary-bar";
  const count = data.affected_orders.length;
  const slips = data.affected_orders.map(o => o.slip_days).filter(s => s !== null);
  const slipRange = slips.length ? `${Math.min(...slips)}-${Math.max(...slips)}d` : "unquantified";
  const top = data.affected_orders[0];
  bar.innerHTML = `
    <div class="stat"><span class="stat-value">${count}</span><span class="stat-label">orders affected</span></div>
    <div class="stat"><span class="stat-value">${esc(slipRange)}</span><span class="stat-label">slip range</span></div>
    <div class="stat"><span class="stat-value">${top ? esc(top.order_id) : "-"}</span><span class="stat-label">most urgent</span></div>
    <div class="stat"><span class="stat-value">${data.unresolved_mentions.length}</span><span class="stat-label">unresolved mentions</span></div>
  `;
  return bar;
}

async function analyze() {
  const notice = noticeEl.value.trim();
  if (!notice) return;

  btnEl.disabled = true;
  emptyEl.hidden = true;
  resultEl.hidden = true;
  loadingEl.hidden = false;

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notice }),
    });
    const data = await res.json();
    if (!res.ok) {
      resultEl.innerHTML = `<div class="error">${esc(data.error || "Request failed.")}</div>`;
      resultEl.hidden = false;
      return;
    }
    render(data);
  } catch (e) {
    resultEl.innerHTML = `<div class="error">Something went wrong: ${esc(String(e))}</div>`;
    resultEl.hidden = false;
  } finally {
    btnEl.disabled = false;
    loadingEl.hidden = true;
  }
}

function render(data) {
  resultEl.innerHTML = "";
  resultEl.hidden = false;

  const narrative = document.createElement("div");
  narrative.className = "narrative " + (data.no_impact ? "no-impact" : "impact");
  narrative.innerHTML = `<strong>${data.no_impact ? "NO IMPACT" : "IMPACT ASSESSMENT"}</strong><p>${esc(data.narrative)}</p>`;
  resultEl.appendChild(narrative);

  if (!data.no_impact && data.affected_orders.length) {
    resultEl.appendChild(renderSummary(data));
  }

  if (data.resolved_entities.length || data.unresolved_mentions.length) {
    const trace = document.createElement("div");
    trace.className = "trace-panel";
    const resolvedHtml = data.resolved_entities
      .map(r => `<li>"${esc(r.mention)}" &rarr; ${esc(r.entity_key ?? "no confident match")} (${esc(r.method)}, score ${esc(String(r.score))})</li>`)
      .join("");
    trace.innerHTML = `<details><summary>Entity resolution (${data.resolved_entities.length})</summary><ul>${resolvedHtml}</ul></details>`;
    resultEl.appendChild(trace);
  }

  if (!data.no_impact) {
    const list = document.createElement("div");
    list.className = "order-list";
    data.affected_orders.forEach(o => list.appendChild(renderOrder(o)));
    resultEl.appendChild(list);
  }

  resultEl.scrollIntoView({ behavior: "smooth", block: "start" });
}

function clearAll() {
  noticeEl.value = "";
  pickerEl.value = "";
  resultEl.hidden = true;
  resultEl.innerHTML = "";
  loadingEl.hidden = true;
  emptyEl.hidden = false;
  noticeEl.focus();
}

btnEl.addEventListener("click", analyze);
clearBtnEl.addEventListener("click", clearAll);
noticeEl.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") analyze();
});
loadSamples();
