#!/usr/bin/env python3
"""Genera il sito statico in docs/ a partire da posts.json.

Uso:  python3 build.py
Per aggiungere un post: aggiungi un oggetto in cima a posts.json con i campi
slug, data (AAAA-MM-GG), area (Energia | Finanza | Valori | Attualità),
titolo, estratto, testo (lista di paragrafi), hashtag, linkedin, fonte.
"""
import json, re, shutil, html
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
SITE = "https://domenicofraccalvieri.it"
NAME = "Domenico Fraccalvieri"
LINKEDIN = "https://www.linkedin.com/in/domenico-fraccalvieri/"
AREAS = ["Energia", "Finanza", "Valori", "Attualità"]
MESI = ["gennaio","febbraio","marzo","aprile","maggio","giugno","luglio","agosto","settembre","ottobre","novembre","dicembre"]
MS = ["gen","feb","mar","apr","mag","giu","lug","ago","set","ott","nov","dic"]

posts = sorted(json.load(open(ROOT / "posts.json", encoding="utf-8")), key=lambda p: p["data"], reverse=True)

esc = lambda s: html.escape(str(s), quote=True)
def fmt(d):
    y, m, g = d.split("-"); return f"{int(g)} {MS[int(m)-1]} {y}"
def mese(d):
    y, m, _ = d.split("-"); return f"{MESI[int(m)-1]} {y}"
def minuti(p):
    return max(1, round(len(" ".join(p["testo"]).split()) / 200))

def inline(t):
    h = esc(t)
    h = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", h)
    h = re.sub(r'(^|[\s(«"])\*([^*\s][^*]*?)\*(?=[\s.,;:!?)»"]|$)', r"\1<em>\2</em>", h)
    def link(m):
        u = m.group(1)
        return f'<a href="{u}" target="_blank" rel="noopener">{re.sub(r"^https?://", "", u)}</a>'
    return re.sub(r"(https?://[^\s<]+[^\s<.,;:!?)\]\"'])", link, h)

def plain(t):
    return re.sub(r"\*+", "", t)

LIST = re.compile(r"^\s*(?:→|👉|•|-|–|▪️|✅|🔹|🔸)\s*(.+)$")
def body_html(paras):
    out, lst = [], []
    def flush():
        if lst:
            out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in lst) + "</ul>"); lst.clear()
    for para in paras:
        m = LIST.match(para)
        if m: lst.append(m.group(1))
        else: flush(); out.append(f"<p>{inline(para)}</p>")
    flush()
    return "\n".join(out)

def page(title, desc, path, main, extra_head="", depth=0):
    rel = "../" * depth
    canonical = SITE + path
    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{NAME}">
<meta property="og:locale" content="it_IT">
<link rel="icon" href="{rel}favicon.svg" type="image/svg+xml">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; connect-src 'none'; object-src 'none'; base-uri 'self'; form-action 'none'; upgrade-insecure-requests">
<meta name="referrer" content="strict-origin-when-cross-origin">
<link rel="stylesheet" href="{rel}assets/style.css">
{extra_head}
</head>
<body>
<div class="wrap">
  <header class="site">
    <a class="mark" href="{rel or './'}">{NAME}<span>.</span></a>
    <nav class="main" aria-label="Sezioni">
      <a href="{rel or './'}#archivio">Articoli</a>
      <a href="{rel}chi-sono/">Chi sono</a>
    </nav>
  </header>
  <main>
{main}
  </main>
  <footer class="site">
    <span>© {posts[0]["data"][:4]} {NAME}</span>
    <a href="{LINKEDIN}" target="_blank" rel="noopener">LinkedIn ↗</a>
    <span class="privacy">Questo sito non usa cookie, non raccoglie dati e non traccia i visitatori.</span>
  </footer>
</div>
</body>
</html>
"""

def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"

PERSON = {"@type": "Person", "name": NAME, "jobTitle": "Chief Financial Officer",
          "worksFor": {"@type": "Organization", "name": "Energia Comune (Ecom S.p.A.)"},
          "url": SITE + "/", "sameAs": [LINKEDIN],
          "knowsAbout": ["Mercato dell'energia", "Bollette luce e gas", "Finanza aziendale", "Leadership"]}

ABOUT_BODY = f"""
      <p>Sono Domenico Fraccalvieri, Chief Financial Officer di Ecom S.p.A. (Energia Comune), azienda che vende luce e gas. Lavoro in Puglia.</p>
      <p>In Energia Comune sono entrato nel 2020 dal back office. Da lì sono passato per il customer care, la formazione, la selezione del personale e la fatturazione, fino al ruolo di CFO nel dicembre 2023. Prima avevo co-fondato una piccola impresa.</p>
      <p>Su LinkedIn scrivo soprattutto di energia: prezzi, bollette, reti e transizione, visti da chi deve far quadrare i conti. Scrivo anche di finanza d'impresa e pubblica, di attualità e dei valori che dovrebbero guidare chi guida le persone.</p>
      <dl>
        <dt>Ruolo</dt><dd>CFO, Ecom S.p.A. – Energia Comune</dd>
        <dt>Energia</dt><dd>PUN e mercato elettrico, gas, bollette, reti e rinnovabili</dd>
        <dt>Finanza</dt><dd>Cassa e capitale circolante, banche e M&amp;A, fisco, finanza pubblica</dd>
        <dt>Valori</dt><dd>Leadership, merito, responsabilità, lavoro</dd>
      </dl>
      <a class="btn" href="{LINKEDIN}" target="_blank" rel="noopener">Seguimi su LinkedIn ↗</a>"""
QUOTE = "«Ogni giorno non sarà mai per me un arrivo ma una partenza sempre più sprint.»"

def about_section(h="h2"):
    return f"""<section class="about" id="chi-sono">
    <div><{h}>Chi sono</{h}><blockquote>{QUOTE}</blockquote></div>
    <div class="body">{ABOUT_BODY}
    </div>
  </section>"""

def build():
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    shutil.copy(ROOT / "assets" / "style.css", OUT / "assets" / "style.css")
    shutil.copy(ROOT / "assets" / "site.js", OUT / "assets" / "site.js")
    shutil.copy(ROOT / "assets" / "favicon.svg", OUT / "favicon.svg")
    shutil.copytree(ROOT / "assets" / "fonts", OUT / "assets" / "fonts")
    (OUT / "CNAME").write_text("domenicofraccalvieri.it\n")
    (OUT / ".nojekyll").write_text("")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")

    # articoli
    for i, p in enumerate(posts):
        newer = posts[i-1] if i > 0 else None
        older = posts[i+1] if i + 1 < len(posts) else None
        tags = "".join(f"<span>#{esc(t)}</span>" for t in p["hashtag"])
        fonte = f'<a href="{esc(p["fonte"])}" target="_blank" rel="noopener">Fonte citata ↗</a>' if p["fonte"] else ""
        pager = (f'<a href="../{older["slug"]}/"><span class="label">← Precedente</span>{inline(older["titolo"])}</a>' if older else "<span></span>") + \
                (f'<a class="next" href="../{newer["slug"]}/"><span class="label">Successivo →</span>{inline(newer["titolo"])}</a>' if newer else "<span></span>")
        main = f"""<article class="post" data-area="{p['area']}">
    <a class="back" href="../../#archivio">← Tutti gli articoli</a>
    <div class="meta"><time class="date" datetime="{p['data']}">{fmt(p['data'])}</time><span class="tag">{p['area']}</span><span class="date">{minuti(p)} min di lettura</span></div>
    <h1>{inline(p['titolo'])}</h1>
    <div class="body">
{body_html(p['testo'])}
    </div>
    {f'<div class="hashtags">{tags}</div>' if tags else ''}
    <div class="origin"><span>Pubblicato su LinkedIn il {fmt(p['data'])}</span>{fonte}<a href="{esc(p['linkedin'])}" target="_blank" rel="noopener">Post originale ↗</a></div>
    <nav class="pager" aria-label="Altri articoli">{pager}</nav>
  </article>"""
        ld = jsonld({"@context": "https://schema.org", "@type": "BlogPosting", "headline": plain(p["titolo"])[:110],
                     "description": p["estratto"], "datePublished": p["data"], "inLanguage": "it-IT",
                     "articleSection": p["area"], "keywords": p["hashtag"], "author": PERSON,
                     "mainEntityOfPage": f"{SITE}/articoli/{p['slug']}/"})
        d = OUT / "articoli" / p["slug"]; d.mkdir(parents=True)
        (d / "index.html").write_text(page(f"{plain(p['titolo'])} · {NAME}", p["estratto"], f"/articoli/{p['slug']}/", main,
                                           ld + '\n<meta property="og:type" content="article">', depth=2), encoding="utf-8")

    # home
    count = {a: sum(1 for p in posts if p["area"] == a) for a in AREAS}
    energy = [p for p in posts if p["area"] == "Energia"][:3]
    cards = "".join(f'<a class="card" href="articoli/{p["slug"]}/" data-area="Energia"><span class="tag">Energia</span><h3>{inline(p["titolo"])}</h3><p>{esc(p["estratto"])}</p><time class="date" datetime="{p["data"]}">{fmt(p["data"])}</time></a>' for p in energy)
    rows, last = [], None
    for p in posts:
        m = mese(p["data"])
        if m != last:
            if last: rows.append("</ul>")
            rows.append(f'<h3 class="month" data-month>{m}</h3><ul class="list">'); last = m
        search = re.sub(r"\s+", " ", (plain(p["titolo"]) + " " + " ".join(p["testo"]) + " " + " ".join(p["hashtag"])).lower())
        rows.append(f'<li data-area="{p["area"]}" data-q="{esc(search)}"><a class="row" href="articoli/{p["slug"]}/"><time class="date" datetime="{p["data"]}">{fmt(p["data"])}</time><span><span class="tag">{p["area"]}</span><h2>{inline(p["titolo"])}</h2><p>{esc(p["estratto"])}</p></span></a></li>')
    rows.append("</ul>")
    years = sorted({p["data"][:4] for p in posts})
    filters = f'<button type="button" data-area="Tutti" aria-pressed="true">Tutti <span class="n">{len(posts)}</span></button>' + \
              "".join(f'<button type="button" data-area="{a}" aria-pressed="false">{a} <span class="n">{count[a]}</span></button>' for a in AREAS)
    main = f"""<section class="hero">
    <h1><em>Energia</em>,<br>numeri e valori.</h1>
    <p><strong>Lo sguardo di un CFO</strong> sul mercato dell'energia, sulla finanza d'impresa e sulla responsabilità di chi decide. I miei post di LinkedIn, raccolti in un unico archivio.</p>
    <div class="stats"><span><b>{len(posts)}</b> articoli</span><span><b>{years[0]}–{years[-1]}</b></span><span><b>4</b> aree</span></div>
  </section>
  <section class="featured" data-area="Energia">
    <div class="head"><p class="label">In evidenza · Energia</p><button type="button" id="all-energy">Tutti gli articoli sull'energia →</button></div>
    <div class="cards">{cards}</div>
  </section>
  <div class="tools" id="archivio">
    <div class="topics" role="group" aria-label="Filtra per area">{filters}</div>
    <label class="search"><input id="q" type="search" placeholder="Cerca: PUN, BCE, leadership…" aria-label="Cerca negli articoli"></label>
  </div>
  <div id="list">
  {"".join(rows)}
  </div>
  <p class="empty" id="empty" hidden>Nessun articolo trovato. Prova con un'altra parola o un'altra area.</p>
  <div class="more"><button type="button" id="more" hidden>Mostra altri</button></div>
  {about_section()}"""
    ld = jsonld({"@context": "https://schema.org", "@type": "WebSite", "name": NAME, "url": SITE + "/", "inLanguage": "it-IT", "author": PERSON})
    (OUT / "index.html").write_text(page(f"{NAME} · Energia, finanza e valori",
        "Domenico Fraccalvieri, CFO di Energia Comune, scrive di mercato dell'energia, bollette, finanza d'impresa e leadership.",
        "/", main, ld + '\n<meta property="og:type" content="website">\n<script src="assets/site.js" defer></script>'), encoding="utf-8")

    # chi sono
    d = OUT / "chi-sono"; d.mkdir()
    (d / "index.html").write_text(page(f"Chi sono · {NAME}",
        "Domenico Fraccalvieri, Chief Financial Officer di Ecom S.p.A. (Energia Comune). Scrive di energia, finanza e valori.",
        "/chi-sono/", about_section("h1"), jsonld({"@context": "https://schema.org", "@type": "ProfilePage", "mainEntity": PERSON}), depth=1), encoding="utf-8")

    # 404
    (OUT / "404.html").write_text(page(f"Pagina non trovata · {NAME}", "Pagina non trovata.", "/404.html",
        '<section class="hero"><h1>Pagina non trovata.</h1><p>Il link potrebbe essere cambiato. <a href="/">Torna agli articoli</a>.</p></section>'), encoding="utf-8")

    # sitemap
    urls = [(SITE + "/", posts[0]["data"]), (SITE + "/chi-sono/", posts[0]["data"])] + \
           [(f"{SITE}/articoli/{p['slug']}/", p["data"]) for p in posts]
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls) + "</urlset>\n")
    print(f"Generati {len(posts)} articoli in {OUT}")

if __name__ == "__main__":
    build()
