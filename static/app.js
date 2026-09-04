const noticeEl = document.getElementById("notice");
const btnEl = document.getElementById("analyze-btn");
const resultEl = document.getElementById("result");
const pickerEl = document.getElementById("sample-picker");

function esc(s) {
  const div = document.createElement("div");
  div.textContent = s ?? "";
  return div.innerHTML;
}

async function loadSamples() {
  const res = await fetch("/api/samples");
  const samples = await res.json();
  samples.forEach((s, i) => {
    const opt = document.createElement("option");
    opt.value = i;
    opt.textContent = s.title;
    pickerEl.appendChild(opt);
  });
  pickerEl.addEventListener("change", () => {
    if (pickerEl.value === "") return;
    noticeEl.value = samples[pickerEl.value].text;
  });
}

function fmtDate(iso) {
  return iso ? iso : "-";
}

function renderOption(o, isRecommended) {
  const div = document.createElement("div");
  div.className = "option" + (isRecommended ? " recommended" : "");
  div.innerHTML = `
    <div class="option-head">${isRecommended ? "RECOMMENDED &rarr; " : ""}<strong>${esc(o.kind.replace("_", " "))}</strong></div>
    <div class="option-desc">${esc(o.description)}</div>
    <div class="option-tradeoff">Trade-off: ${esc(o.trade_off)}</div>
  `;
  return div;
}

function renderOrder(o) {
  const div = document.createElement("div");
  div.className = "order-card";
  const slip = o.slip_days === null ? "unquantified" : `${o.slip_days}d slip`;
  div.innerHTML = `
    <div class="order-head">
      <span class="order-id">${esc(o.order_id)}</span>
      <span class="tier tier-${esc(o.tier)}">${esc(o.tier)}</span>
      <span class="urgency">urgency ${esc(String(o.urgency_score))}</span>
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

async function analyze() {
  const notice = noticeEl.value.trim();
  if (!notice) return;

  btnEl.disabled = true;
  btnEl.textContent = "Analyzing...";
  resultEl.hidden = true;

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
    btnEl.textContent = "Analyze";
  }
}

function render(data) {
  resultEl.innerHTML = "";
  resultEl.hidden = false;

  const narrative = document.createElement("div");
  narrative.className = "narrative " + (data.no_impact ? "no-impact" : "impact");
  narrative.innerHTML = `<strong>${data.no_impact ? "NO IMPACT" : "IMPACT ASSESSMENT"}</strong><p>${esc(data.narrative)}</p>`;
  resultEl.appendChild(narrative);

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
}

btnEl.addEventListener("click", analyze);
loadSamples();
