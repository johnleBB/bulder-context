"""Builds the Bulder designsystem site (one HTML file, one article per page).
Usage: python3 build.py <design system project dir> <out.html>
Page content lives in pages/<slug>.html; placeholder pages are generated from PLACEHOLDERS."""
import base64, html, json, mimetypes, pathlib, re, sys

HERE = pathlib.Path(__file__).parent
# --no-aeonik: Aeonik er lisensiert, så den offentlige versjonen (GitHub Pages) bygges uten fontfilene.
NO_AEONIK = "--no-aeonik" in sys.argv[3:]
proj, out = map(pathlib.Path, sys.argv[1:3])
A = proj / "assets"
tokens = json.loads((proj / "tokens.json").read_text())

# --- site map: (group, [(slug, title, lead)]) in SpareBank 1's order -------
SITE = [
    ("Visuell identitet", [
        ("needscope", "NeedScope", "Bulder er i rødt segment. Det sier hvem vi er og hvordan vi skal oppleves."),
        ("stil-og-tone", "Stil og tone", "Slik skriver og snakker vi i Bulder."),
        ("farger", "Farger", "Fargene våre gir Bulder et tydelig preg og fungerer i både light og dark mode."),
        ("ikoner", "Ikoner", "Ikonene skal hjelpe kunden å finne fram raskt og skille ulikt innhold fra hverandre."),
        ("typografi", "Typografi", "Aeonik gir Bulder en egen stemme i alt vi lager, fra appen til nettsiden."),
        ("illustrasjoner", "Illustrasjoner", "Illustrasjoner gjør tjenestene og produktene våre lettere å forstå."),
        ("animasjoner", "Animasjoner", "Animasjoner gjør grensesnittet levende og hjelper kunden å følge med."),
        ("former", "Former", "Hjørner, sirkler, skygger og mønstre som går igjen i alt vi lager."),
        ("bilder", "Bilder", "Bildene våre viser ekte mennesker og hverdagen deres."),
        ("logo", "Logo", "Logoen er det tydeligste kjennetegnet vårt. Bruk filene som de er."),
    ]),
    ("Grunnleggende", [
        ("semantiske-farger", "Semantiske farger", "Semantiske farger har navn etter hva de brukes til, ikke hvordan de ser ut."),
        ("responsiv-styling", "Responsiv styling", "Løsningene våre skal fungere på alle skjermstørrelser og tekststørrelser."),
        ("spacing", "Spacing", "Luft i og mellom komponentene er en viktig del av designet."),
        ("nettleserversjoner", "Nettleserversjoner", "Nettlesere og operativsystemer vi støtter."),
        ("theming", "Theming", "Alt i Bulder finnes i light mode og dark mode."),
    ]),
    ("Universell utforming", [
        ("uu-testing", "Testing av universell utforming", "Slik tester du kravene i WCAG 2.1 på nivå A og AA."),
        ("universell-utforming", "Universell utforming", "Løsningene våre skal være tilgjengelige og enkle å bruke for alle."),
    ]),
    ("Om designsystemet", [
        ("prinsipper", "Prinsipper", "Prinsippene designsystemet er bygget på."),
        ("faq", "FAQ", "Svar på det folk ofte lurer på."),
    ]),
    ("Bidra", [
        ("alle-kan-bidra", "Alle kan bidra", "Designsystemet holdes oppdatert når flest mulig er med på å vedlikeholde det."),
        ("meld-inn-feil", "Meld inn feil", "Har du funnet noe som ikke virker, ser rart ut eller er feil i dokumentasjonen? Si fra."),
        ("kom-med-onske", "Kom med ønske", "Mangler designsystemet noe du trenger, eller burde noe vært annerledes?"),
        ("kom-med-losningsforslag", "Kom med løsningsforslag", "Har du et konkret forslag til en endring? Slik går du fram."),
        ("guide-for-figma", "Guide for Figma", "Slik bidrar du til Figma-biblioteket Bulder library."),
        ("guide-til-github", "Guide til GitHub", "Slik bidrar du til koden i designsystemet."),
        ("guide-til-dokumentering", "Guide til dokumentering", "Slik holder vi denne siden oppdatert."),
    ]),
]

# Pages without Bulder content: (heading, what belongs there). Facts we do know go in "known".
PLACEHOLDERS = {
    "bilder": {"known": "Kortene med foto (<code>CardWithImage</code>, <code>PromoCard</code>, <code>PropertyCard</code>) tar en bilde-URL. Designsystemet har ingen egne foto.", "sections": [
        ("Bildestil", "Hvordan bildene våre skal se ut: motiv, lys, farger og beskjæring."),
        ("Se alle bildene", "Lenke til bildebanken."),
    ]},
}

# --- colour tokens ---------------------------------------------------------
ctoks = tokens["color"]["tokens"]
prim = {t["name"]: t["value"] for t in ctoks if isinstance(t["value"], str) and t["value"].startswith("#")}
sem = {t["name"]: t["value"] for t in ctoks if t["name"] not in prim}

def resolve(v, theme):
    if isinstance(v, dict):
        v = v[theme]
    if v.startswith("{"):
        name = v[1:-1]
        return resolve(prim.get(name) or sem[name], theme)
    return v

def ref(name, theme):
    v = sem.get(name, prim.get(name))
    if isinstance(v, dict):
        v = v[theme]
    return v[1:-1] if v.startswith("{") else v

def block(theme):
    css = "".join(f"--{n}:{resolve(v, theme)};" for n, v in sem.items() if not n.startswith("IK"))
    sh = {t["name"]: t["value"][theme] for t in tokens["shadow"]["tokens"]}
    return css + f"--shadow:{sh['shadow']};--shadow-botnav:{sh['shadow-botnav']};"

light, dark = block("light"), block("dark")
color_css = (
    f":root{{{light}color-scheme:light}}"
    f"@media (prefers-color-scheme: dark){{:root:not([data-theme=\"light\"]){{{dark}color-scheme:dark}}}}"
    f":root[data-theme=\"dark\"]{{{dark}color-scheme:dark}}"
    f".force-light{{{light}color-scheme:light}}.force-dark{{{dark}color-scheme:dark}}"
)

def lum(hexv):
    c = [int(hexv[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]

def ink(hexv):  # label colour for a literal swatch (navy or near-white, whichever reads better)
    l = lum(hexv)
    return prim["dark_blue-800"] if (l + .05) / (lum(prim["dark_blue-800"]) + .05) > (lum(prim["grey-100"]) + .05) / (l + .05) else prim["grey-100"]

# --- fonts -----------------------------------------------------------------
font_css = ""
for w, st, f in () if NO_AEONIK else ((400, "normal", "Regular"), (400, "italic", "RegularItalic"), (500, "normal", "Medium"), (500, "italic", "MediumItalic"), (700, "normal", "Bold")):
    b64 = base64.b64encode((proj / "fonts" / f"Aeonik-{f}.ttf").read_bytes()).decode()
    font_css += (f"@font-face{{font-family:Aeonik;font-weight:{w};font-style:{st};font-display:swap;"
                 f"src:url(data:font/ttf;base64,{b64}) format('truetype')}}")

# --- icon sprite -----------------------------------------------------------
INK = {"#fafbff", "#f6f3f3", "#f4f6ff", "#e8eaed", "white", "#fff", "#ffffff"}

def symbol(path, sid):
    svg = path.read_text()
    colours = {c.lower() for c in re.findall(r'(?:fill|stroke)="([^"]+)"', svg)} - {"none"}
    mono = colours <= INK
    if mono:
        svg = re.sub(r'((?:fill|stroke)=")([^"]+)"',
                     lambda m: m.group(0) if m.group(2) == "none" else f'{m.group(1)}currentColor"', svg)
    elif colours == {"#fe4d5b"}:
        # Single-ink red icons (navigation arrows/chevrons) stay red by default;
        # a context can recolour them by setting --ic-accent.
        svg = re.sub(r'(fill|stroke)="#FE4D5B"', r'style="\1:var(--ic-accent,#FE4D5B)"', svg, flags=re.I)
    clean = lambda s: re.sub(r"[^A-Za-z0-9_-]", "_", s)
    svg = re.sub(r'id="([^"]+)"', lambda m: f'id="{sid}-{clean(m.group(1))}"', svg)
    svg = re.sub(r'url\(#([^)]+)\)', lambda m: f'url(#{sid}-{clean(m.group(1))})', svg)
    vb = re.search(r'viewBox="([^"]+)"', svg).group(1)
    inner = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", svg, flags=re.S)
    return f'<symbol id="{sid}" viewBox="{vb}">{inner}</symbol>', mono

sprite, catalog = [], {}
def add(group, path, sid=None, name=None):
    name = name or path.stem
    sid = sid or f"i-{group}-{name}".replace(" ", "_")
    s, mono = symbol(path, sid)
    sprite.append(s)
    catalog.setdefault(group, []).append({"id": sid, "name": name, "file": path.name, "mono": mono})

for p in sorted((A / "Icons").glob("*.svg"), key=lambda p: p.stem.lower()):
    add("Icons", p)
for p in sorted((A / "Navigation").glob("*.svg")):
    add("Navigation", p)
for p in sorted((A / "Navigation" / "bottom_navigation").glob("*.svg")):
    add("Navigation", p, f"i-Navigation-bn-{p.stem}")
for d in sorted(x for x in (A / "Categories").iterdir() if x.is_dir()):
    # the folder's main icon; a few files are named off-pattern (Retail.svg, savingsaving.svg)
    main = next(p for p in sorted(d.glob("*.svg")) if p.stem.lower().endswith(d.name))
    add("Categories", main, name=d.name)
for p in sorted((A / "Payment").glob("*.svg")):
    add("Payment", p)
for p in sorted((A / "Min Bulder").glob("*.svg")):
    add("Min Bulder", p)
for n in ("bulder_logo_dark", "bulder_logo_light", "Bulderpride"):
    add("Logos", A / "Logos" / f"{n}.svg", f"logo-{n}")

# Hero pattern from Bulder library (Figma node 392:114). Its old colours are swapped for tokens (approved):
# Watermelon #FF4D5B -> Tertiary (red-500), #171E30 -> bulder, #051C2C -> dark_blue-900.
hero_svg = (HERE / "assets" / "hero-pattern.svg").read_text()
for old, new in (("#FF4D5B", "var(--Tertiary)"), ("#171E30", "var(--bulder)"), ("#051C2C", prim["dark_blue-900"])):
    hero_svg = hero_svg.replace(f'fill="{old}"', f'style="fill:{new}"')
hero_vb = re.search(r'viewBox="([^"]+)"', hero_svg).group(1)
hero_inner = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", hero_svg, flags=re.S)
hero_inner = re.sub(r'\s+id="[^"]+"', "", hero_inner)  # the export repeats id="Vector"; nothing references them
sprite.append(f'<symbol id="hero-pattern" viewBox="{hero_vb}" preserveAspectRatio="none">{hero_inner}</symbol>')

def hero(crumbs, title, lead, front=False):
    return (f'<div class="hero{" front" if front else ""}"><div class="art" aria-hidden="true"><div class="frame">'
            '<svg preserveAspectRatio="none"><use href="#hero-pattern"/></svg></div></div>'
            f'<div class="copy"><div class="crumbs">{crumbs}</div><h1>{title}</h1><p class="app-subtitle">{lead}</p></div></div>')

# --- macros used in page fragments: {{name:arg}} ---------------------------
def datauri(rel):
    p = A / rel
    mime = mimetypes.guess_type(p.name)[0] or ("image/webp" if p.suffix == ".webp" else "application/octet-stream")
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"

NO = {  # Norwegian usage notes for the semantic tokens
    "Background": "Bakgrunnen bak innhold som scroller.", "On_Background": "Tekst og ikoner på Background.",
    "Surface": "Standardflate for komponenter. Lik Background.",
    "SurfaceContainer": "Kort og grupperte rader på Background.", "SurfaceContainer_High": "Flater med mer vekt, som valgte eller trykte rader.",
    "SurfaceContainer_Highest": "Høyeste flatenivå. Lik SurfaceContainer i dag.",
    "On_Surface": "Hovedtekst og ikoner på Surface og SurfaceContainer.", "On_Surface_Variant": "Sekundærtekst: bildetekster, datoer og metadata.",
    "Outline": "Kanter på kontroller. I light mode lik Background, så den vises bare på SurfaceContainer.",
    "Outline_Variant": "Skillelinjer. Lav kontrast med vilje, så den må aldri være eneste tegn på en kontroll.",
    "Scrim": "Overlegg bak modaler og ark.", "Shadow": "Skyggefarge for hevede flater og bunnmenyen.",
    "primary": "Primærknapper, lenker og valgte kontroller. I dark mode bare som fyll.", "On_Primary": "Tekst og ikoner på primary.",
    "Primary_Container": "Tonal primærflate, samme blå som primary.", "On_Primary_Container": "Tekst på Primary_Container.",
    "Secondary": "Grønn aksent for fremhevinger og sekundære handlinger.", "On_Secondary": "Tekst og ikoner på Secondary.",
    "Secondary_Container": "Tonal sekundærflate.", "On_Secondary_Container": "Tekst på Secondary_Container.",
    "Tertiary": "Aksent i merkets farge. Brukes sparsomt.", "On_Tertiary": "Tekst på Tertiary.",
    "Tertiary_Container": "Tonal tertiærflate.", "On_Tertiary_Container": "Tekst på Tertiary_Container.",
    "Surface_Tint": "Tone på hevede komponenter. Ikke en tekstfarge.",
    "bulder": "Merkevareflaten: splash, hero og merkevarepaneler.", "on_bulder": "Merket og fremhevinger på bulder.",
    "bulder_light": "Lys merkevareflate.", "bulder_credit": "Flaten på kredittkort.", "on_bulder_credit": "Tekst på bulder_credit.",
    "bulder_metall": "Flaten på Metall-kortet.", "on_bulder_metall": "Tekst på bulder_metall.",
    "Positive": "Endringer opp og innbetalinger. Alltid med fortegn.", "Negative": "Endringer ned og utbetalinger. Alltid med fortegn.",
    "Error": "Feiltekst, feilikoner og feltkanter.", "On_Error": "Tekst på Error.",
    "Error_Container": "Fyll på feilbannere.", "On_Error_Container": "Tekst på Error_Container.",
    "Warning": "Fyll på advarsler. Aldri som tekstfarge.", "on_warning": "Tekst og ikoner på Warning.",
    "labs": "Merket for Bulder Labs.", "on_labs": "Tekst på labs.",
    "active_bottom_navigation": "Valgt ikon i bunnmenyen.", "inactive_bottom_navigation": "Ikoner og etiketter som ikke er valgt i bunnmenyen.",
    "On_Image_Fixed": "Tekst og ikoner over foto og mørk kortgrafikk, lik i begge temaer.",
}

def m_scale(name):
    cells = []
    for step in range(100, 1000, 100):
        n = f"{name}-{step}"
        h = prim[n]
        cells.append(f'<div style="background:{h};color:{ink(h)}"><b>{step}</b>{h.upper()}</div>')
    return f'<div class="scale" role="img" aria-label="Fargeskala {name}">{"".join(cells)}</div>'

def m_tiles(arg):
    out = []
    for item in arg.split(","):
        n, label = (item.split("=") + [""])[:2]
        h = prim.get(n) or resolve(sem[n], "light")
        out.append(f'<div style="background:{h};color:{ink(h)}"><b>{label or n}</b><span>{n} · {h.upper()}</span></div>')
    return f'<div class="tiles">{"".join(out)}</div>'

def m_pairs(arg):
    out = []
    for item in arg.split(","):
        fill, on = item.split("/")
        out.append(f'<div style="background:var(--{fill});color:var(--{on})"><span class="big">Aa</span><code>{fill}<br>{on}</code></div>')
    return f'<div class="pairs">{"".join(out)}</div>'

def sq(name, theme):
    h = resolve(sem.get(name, prim.get(name)), theme)
    return f'<span class="sq"><i style="background:{h}"></i>{ref(name, theme)}</span>'

def m_semantic(arg):
    rows = "".join(
        f"<tr><td><code>{n}</code></td><td>{sq(n, 'light')}</td><td>{sq(n, 'dark')}</td><td>{NO.get(n, '')}</td></tr>"
        for n in arg.split(","))
    return ('<div class="tablewrap"><table><thead><tr><th>Token</th><th>Light</th><th>Dark</th><th>Brukes til</th></tr></thead>'
            f"<tbody>{rows}</tbody></table></div>")

def m_chips(prefix):
    names = [n for n in sem if n.startswith(prefix) and "-on_" not in n]
    if prefix == "chart-":
        names.sort(key=lambda n: int(n.split("-")[1]))
    on = {"categories-": lambda n: "categories-on_Div" if n == "categories-div" else n.replace("categories-", "categories-on_"),
          "payment-": lambda n: "payment-on_payment", "min_bulder-": lambda n: "min_bulder-on_min_bulder",
          "inbox-": lambda n: "inbox-on_inbox"}.get(prefix)
    cells = []
    for n in names:
        fg = f"color:var(--{on(n)})" if on and on(n) in sem else ""
        mark = "Aa" if fg else ""
        cells.append(f'<div><i style="background:var(--{n});{fg}">{mark}</i><span>{n}</span></div>')
    return f'<div class="chips">{"".join(cells)}</div>'

TYPE_NO = {"app-LargeTitle": "Store tall, som saldo.", "app-h1": "Skjermtitler.", "app-h2": "Seksjonstitler.", "app-h3": "Titler på kort og listegrupper.",
           "app-subtitle": "Ingress og undertitler.", "app-button-medium": "Tekst i primærknapper.", "app-body": "Standard brødtekst.",
           "app-button-regular": "Tekst i sekundær- og tekstknapper.", "app-body-2": "Sekundær brødtekst og tette rader.",
           "app-caption": "Bildetekst, hjelpetekst og metadata.", "app-overline": "Små etiketter over innhold. Store bokstaver."}
ORDER = ["app-LargeTitle", "app-h1", "app-h2", "app-h3", "app-subtitle", "app-button-medium", "app-body", "app-button-regular", "app-body-2", "app-caption", "app-overline"]
WEIGHT = {400: "Regular", 500: "Medium", 700: "Bold"}

def m_typescale(_):
    styles = {s["name"]: s for g in tokens["type"]["groups"] for s in g["styles"]}
    spec, rows = [], []
    for n in ORDER:
        s = styles[n]
        px = int(s["fontSize"][:-2]); rem = f"{px / 16:g}rem"
        lh = s.get("lineHeight", "normal"); w = s["fontWeight"]
        spec.append(f'<div class="specimen"><div class="{n} spec-sample">Sparing som gir mening</div>'
                    f'<div class="meta"><code>{n}</code><span>{px} px · {rem}</span><span>{w} {WEIGHT[w]}</span><span>{TYPE_NO[n]}</span></div></div>')
        rows.append(f'<tr><td><code>{n}</code></td><td class="num">{px} px</td><td class="num">{rem}</td><td>{w} {WEIGHT[w]}</td>'
                    f'<td class="num">{lh}</td><td class="num">{s["letterSpacing"]}</td></tr>')
    table = ('<div class="tablewrap"><table><thead><tr><th>Stil</th><th>App</th><th>Web</th><th>Vekt</th><th>Linjehøyde</th><th>Sporing</th></tr></thead>'
             f'<tbody>{"".join(rows)}</tbody></table></div>')
    return f'<div>{"".join(spec)}</div>' if _ == "specimens" else table

def m_spacing(kind):
    toks = tokens["spacing"]["tokens"]
    if kind == "semantic":
        bars = [f'<div class="bar"><code>{t["name"]}</code><span class="num">{t["value"]}</span><i style="width:{t["value"]}"></i></div>'
                for t in toks if t["name"].startswith("space-")]
        return f'<div class="spbars">{"".join(bars)}</div>'
    rows = "".join(f'<tr><td><code>{t["name"]}</code></td><td class="num">{t["value"]}</td></tr>' for t in toks if t["name"].startswith("size_"))
    return f'<div class="tablewrap"><table><thead><tr><th>Primitiv</th><th>Verdi</th></tr></thead><tbody>{rows}</tbody></table></div>'

def m_gallery(arg):
    folder, cls = (arg.split("|") + [""])[:2]
    files = sorted(p for p in (A / folder).iterdir() if p.suffix.lower() in (".webp", ".png", ".svg"))
    figs = "".join(f'<figure><img src="{datauri(str(p.relative_to(A)))}" alt="{p.stem}" loading="lazy"><figcaption>{p.name}</figcaption></figure>' for p in files)
    return f'<div class="gallery {cls}">{figs}</div>'

def m_img(arg):
    rel, alt = arg.split("|")
    return f'<img src="{datauri(rel)}" alt="{html.escape(alt)}">'

MACROS = {"scale": m_scale, "tiles": m_tiles, "pairs": m_pairs, "semantic": m_semantic, "chips": m_chips,
          "type": m_typescale, "spacing": m_spacing, "gallery": m_gallery, "img": m_img, "uri": datauri,
          "include": lambda n: (HERE / "pages" / f"_{n}.html").read_text()}

def expand(s):
    return re.sub(r"\{\{(\w+):([^}]*)\}\}", lambda m: MACROS[m.group(1)](m.group(2)), s)

# --- pages -----------------------------------------------------------------
def slugify(s):
    s = s.lower().replace("æ", "ae").replace("ø", "o").replace("å", "a")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:40]

def todo_box(hint):
    return (f'<div class="todo"><div class="app-overline">Mangler innhold</div><p>Her kommer: {hint}</p></div>')

def placeholder(slug):
    ph = PLACEHOLDERS[slug]
    parts = ['<div class="callout"><svg class="ic"><use href="#i-Icons-info"/></svg><p>Denne siden mangler innhold fra Bulder. '
             'Overskriftene viser hva som skal stå her. Ta kontakt med designsystem-teamet hvis du kan fylle inn.</p></div>']
    if ph.get("known"):
        parts.append(f'<p>{ph["known"]}</p>')
    body = "".join(parts)
    secs = [f"<section><h2>{h}</h2>{todo_box(hint)}</section>" for h, hint in ph["sections"]]
    return f"<section><h2>Om denne siden</h2>{body}</section>" + "".join(secs)

group_of, pages = {}, []
for g, items in SITE:
    for slug, title, lead in items:
        group_of.setdefault(slug, g)
        if slug not in [p[0] for p in pages]:
            pages.append((slug, title, lead))

def article(slug, title, lead):
    frag = HERE / "pages" / f"{slug}.html"
    body = frag.read_text() if frag.exists() else placeholder(slug)
    body = expand(body)
    toc = []
    def sec(m):
        text = re.sub("<[^>]+>", "", m.group(2))
        sid = f"{slug}--{slugify(text)}"
        toc.append((sid, text))
        return f'<section id="{sid}">{m.group(1)}'
    body = re.sub(r"<section>(\s*<h2[^>]*>(.*?)</h2>)", sec, body, flags=re.S)
    toc_html = "".join(f'<a data-target="{i}">{html.escape(t)}</a>' for i, t in toc)
    crumbs = f"{group_of[slug]} / {title}"
    todo = not frag.exists()
    return (f'<article data-page="{slug}" data-title="{html.escape(title)}" hidden>'
            + hero(crumbs, title, lead) +
            f'<div class="page gutter"><div class="wrap"><main>{body}</main>'
            f'<aside class="toc" aria-label="Innhold på siden"><div class="app-overline">På denne siden</div><nav>{toc_html}</nav></aside>'
            f"</div></div></article>"), todo

arts, todo_slugs = [], set()
front = expand((HERE / "pages" / "_forside.html").read_text()).replace("<!--@HERO@-->", hero(
    "Bulder", "Designsystemet",
    "Felles retningslinjer, tokens og komponenter som hjelper oss å lage helhetlige, brukervennlige og inkluderende løsninger for kundene i Bulder.",
    front=True))
arts.append(f'<article data-page="forside" data-title="Designsystemet" hidden>{front}</article>')
for slug, title, lead in pages:
    a, todo = article(slug, title, lead)
    arts.append(a)
    if todo:
        todo_slugs.add(slug)

chev = '<svg class="ic"><use href="#i-Navigation-chevron_down"/></svg>'
menu = '<a class="home" href="#forside">Designsystemet</a>'
for g, items in SITE:
    lis = "".join(f'<li><a href="#{s}">{t}{" <span class=pill-todo>Mangler</span>" if s in todo_slugs else ""}</a></li>' for s, t, _ in items)
    menu += f"<details><summary>{g}{chev}</summary><ul>{lis}</ul></details>"

shell = (HERE / "shell.html").read_text()
css = (HERE / "base.css").read_text() + (HERE / "shell.css").read_text()
js = (HERE / "ikoner.js").read_text() + (HERE / "router.js").read_text()
html_out = (shell.replace("/*@CSS@*/", font_css + color_css + css)
            .replace("<!--@SPRITE@-->", '<svg class="sprite" aria-hidden="true">' + "".join(sprite) + "</svg>")
            .replace("<!--@MENU@-->", menu).replace("<!--@ARTICLES@-->", "".join(arts))
            .replace("/*@JS@*/", js.replace("/*@CATALOG@*/null", json.dumps(catalog, ensure_ascii=False))))
missing = re.findall(r"\{\{\w+:[^}]*\}\}", html_out)
assert not missing, missing
out.write_text(html_out)
print(f"{out.name} {out.stat().st_size // 1024} KB, {len(pages) + 1} pages, placeholders: {sorted(todo_slugs)}", file=sys.stderr)
