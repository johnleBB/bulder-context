
// --- light og dark mode: overstyrer systemvalget og huskes i nettleseren ---
const root = document.documentElement, themeBtn = $("#theme");
const systemDark = matchMedia("(prefers-color-scheme: dark)");
const isDark = () => root.dataset.theme ? root.dataset.theme === "dark" : systemDark.matches;
const syncThemeBtn = () => {
  const label = isDark() ? "Bytt til lyst tema" : "Bytt til mørkt tema";
  themeBtn.setAttribute("aria-label", label); themeBtn.title = label;
};
try { const saved = localStorage.getItem("bulder-theme"); if (saved) root.dataset.theme = saved; } catch {}
themeBtn.onclick = () => {
  root.dataset.theme = isDark() ? "light" : "dark";
  try { localStorage.setItem("bulder-theme", root.dataset.theme); } catch {}
  syncThemeBtn();
};
systemDark.addEventListener("change", syncThemeBtn);
syncThemeBtn();

// --- ruting: én artikkel per side, valgt med #slug ---
const pagesEl = [...document.querySelectorAll("article[data-page]")];
const drawer = $("#drawer"), openBtn = $("#menu-open");
function setMenu(open) {
  drawer.hidden = !open;
  openBtn.setAttribute("aria-expanded", open);
  if (open) {
    const cur = drawer.querySelector("a[aria-current]");
    if (cur) cur.closest("details")?.setAttribute("open", "");
    (cur || $("#menu-close")).focus();
  } else openBtn.focus();
}
openBtn.onclick = () => setMenu(true);
$("#menu-close").onclick = $("#menu-scrim").onclick = () => setMenu(false);
document.addEventListener("keydown", e => { if (e.key === "Escape" && !drawer.hidden) setMenu(false); });
drawer.addEventListener("click", e => { if (e.target.closest("a")) setMenu(false); });

function show() {
  const slug = location.hash.slice(1);
  const page = pagesEl.find(a => a.dataset.page === slug) || pagesEl[0];
  pagesEl.forEach(a => a.hidden = a !== page);
  document.title = page.dataset.page === "forside" ? "Bulder designsystem" : `${page.dataset.title} · Bulder designsystem`;
  drawer.querySelectorAll("a").forEach(a => a.toggleAttribute("aria-current", a.hash === "#" + page.dataset.page));
  window.scrollTo({ top: 0, behavior: "instant" });
}
window.addEventListener("hashchange", show);
show();

// innholdsfortegnelse: hash er opptatt av rutingen, så vi scroller i stedet for å bruke ankere
// Aktiv lenke = siste seksjon som har passert toppen. Etter et klikk beholder vi
// den valgte lenken til scrollingen er ferdig, så korte seksjoner nederst ikke blir overstyrt.
let tocLock = false, tocTimer;
const mark = (toc, id) => toc.querySelectorAll("a").forEach(a => a.classList.toggle("on", a.dataset.target === id));
function spy() {
  if (tocLock) return;
  const art = pagesEl.find(a => !a.hidden), toc = art && art.querySelector(".toc");
  if (!toc) return;
  const secs = [...art.querySelectorAll("section[id]")];
  const atEnd = innerHeight + scrollY >= document.documentElement.scrollHeight - 2;
  let cur = secs[0];
  if (atEnd) cur = secs[secs.length - 1];
  else for (const s of secs) if (s.getBoundingClientRect().top <= 120) cur = s;
  mark(toc, cur.id);
}
document.addEventListener("click", e => {
  const a = e.target.closest(".toc a[data-target]"); if (!a) return;
  mark(a.closest(".toc"), a.dataset.target);
  tocLock = true; clearTimeout(tocTimer);
  tocTimer = setTimeout(() => tocLock = false, 1200);
  document.getElementById(a.dataset.target).scrollIntoView({ block: "start" });
});
addEventListener("scrollend", () => { clearTimeout(tocTimer); tocTimer = setTimeout(() => tocLock = false, 50); });
addEventListener("scroll", () => requestAnimationFrame(spy), { passive: true });
addEventListener("hashchange", () => { tocLock = false; spy(); });
spy();

// animasjonen spilles bare når noen ber om det
document.querySelectorAll("[data-play]").forEach(b => b.onclick = () => {
  const img = document.getElementById(b.dataset.play);
  img.hidden = !img.hidden;
  b.textContent = img.hidden ? "Vis animasjonen" : "Skjul animasjonen";
});
