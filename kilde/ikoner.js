const CATALOG = /*@CATALOG@*/null;
const $ = s => document.querySelector(s);
const svg = (id, s) => `<svg class="ic"${s ? ` style="--s:${s}px"` : ""} aria-hidden="true"><use href="#${id}"/></svg>`;

// colour token for each badge
const catToken = n => ({ house_home: "house", div: "div" }[n] || n);
const badgeColors = {
  Categories: n => [`categories-${catToken(n)}`, n === "div" ? "categories-on_Div" : `categories-on_${catToken(n)}`],
  Payment: n => [`payment-${n}`, "payment-on_payment"],
  "Min Bulder": n => [`min_bulder-${n}`, "min_bulder-on_min_bulder"],
};
const badge = (group, it, size) => {
  const [bg, fg] = badgeColors[group](it.name);
  return `<span class="badge" style="--b:${size}px;background:var(--${bg});color:var(--${fg})">${svg(it.id)}</span>`;
};

for (const g of Object.keys(badgeColors)) {
  document.getElementById("b-" + g).innerHTML = CATALOG[g].map(it =>
    `<figure>${badge(g, it, 40)}<figcaption>${badgeColors[g](it.name)[0]}</figcaption></figure>`).join("");
}

// mest brukte
const USAGE = [
  ["settings", "Til alt som fører til innstillinger."],
  ["search", "Til søk."],
  ["filter", "Til å filtrere eller sortere en liste."],
  ["add", "Til å legge til noe nytt."],
  ["edit", "Til å redigere innhold."],
  ["delete", "Til å slette."],
  ["copy", "Til å kopiere, for eksempel et kontonummer."],
  ["close", "Til å lukke et ark, en pop-up eller en melding."],
  ["more", "Til flere valg i en meny."],
  ["info", "Til å vise mer informasjon om noe."],
  ["help", "Til hjelp og veiledning."],
  ["chat", "Til å starte en chat med kundeservice."],
  ["notification", "Til varsler."],
  ["external_link", "Til lenker som åpnes utenfor appen."],
  ["eye", "Til å vise skjult innhold, som saldo."],
  ["hidde_eye", "Til å skjule innhold."],
];
$("#usage").innerHTML = USAGE.map(([n, d]) =>
  `<div><dt>${svg("i-Icons-" + n)}${n}</dt><dd>${d}</dd></div>`).join("");

// alle ikoner
const GROUPS = ["Icons", "Navigation", "Categories", "Payment", "Min Bulder"];
const SIZES = [["medium", 24], ["large", 28], ["32 lerret", 32], ["xLarge", 60]];
let group = "Icons", size = 60;
const chips = (el, items, cur, on) => {
  el.innerHTML = items.map(([label, v]) => `<button class="chip" aria-pressed="${v === cur}" data-v="${v}">${label}</button>`).join("");
  el.onclick = e => { const b = e.target.closest(".chip"); if (!b) return; on(b.dataset.v); };
};
const drawChips = () => {
  chips($("#groups"), GROUPS.map(g => [g, g]), group, v => { group = v; drawChips(); draw(); });
  chips($("#sizes"), SIZES.map(([l, v]) => [`${l} ${v === 32 ? "" : v}`.trim(), String(v)]), String(size), v => { size = +v; drawChips(); draw(); });
};
function draw() {
  const q = $("#q").value.trim().toLowerCase();
  const pool = q ? GROUPS.flatMap(g => CATALOG[g].map(it => [g, it])) : CATALOG[group].map(it => [group, it]);
  const hits = pool.filter(([, it]) => it.name.toLowerCase().includes(q));
  $("#count").textContent = q ? `${hits.length} treff i alle grupper` : `${hits.length} ikoner i ${group}`;
  $("#grid").innerHTML = hits.length ? hits.map(([g, it]) => {
    const art = badgeColors[g] ? badge(g, it, size) : `<span class="base" style="--s:${size}px">${svg(it.id, size)}</span>`;
    return `<button class="tile" data-file="${it.file}" title="Kopier ${it.file}"><span class="stage">${art}</span><span class="name">${it.name}</span></button>`;
  }).join("") : `<p class="empty app-caption">Fant ingen ikoner som heter «${q.replace(/[<>&]/g, "")}». Prøv et engelsk ord, som card eller arrow.</p>`;
}
$("#grid").onclick = async e => {
  const t = e.target.closest(".tile"); if (!t) return;
  const name = t.querySelector(".name"), old = name.textContent;
  try { await navigator.clipboard.writeText(t.dataset.file); name.textContent = "Kopiert"; }
  catch { name.textContent = t.dataset.file; }
  t.classList.add("copied");
  setTimeout(() => { name.textContent = old; t.classList.remove("copied"); }, 1200);
};
$("#q").oninput = draw;
$("#base-lib").onchange = e => $("#grid").classList.toggle("no-base", !e.target.checked);
$("#base-demo").onchange = e => $("#ld").classList.toggle("no-base", !e.target.checked);
$("#grid").classList.add("no-base");
drawChips(); draw();
