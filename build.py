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

import sys
sys.path.insert(0, str(ROOT / "scripts"))
import anonimizza  # nomi da non pubblicare mai: vale per ogni articolo, anche per quelli futuri

posts = sorted((anonimizza.post(p) for p in json.load(open(ROOT / "posts.json", encoding="utf-8"))),
               key=lambda p: p["data"], reverse=True)


def estratto_pieno(p):
    """Se l'estratto è troppo corto (es. "I numeri:"), lo allunga con i paragrafi seguenti: serve a Google e alle anteprime."""
    e = p["estratto"]
    if len(e) >= 60:
        return p
    parts = []
    for t in p["testo"]:
        t = re.sub(r"https?://\S+", "", t.replace("**", "")).strip()
        if t: parts.append(t)
        if len(" ".join(parts)) >= 150: break
    txt = " ".join(parts)
    if len(txt) > 190:
        txt = txt[:190].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return {**p, "estratto": txt or e}


posts = [estratto_pieno(p) for p in posts]

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

def ver(name):
    """Impronta del file: cambia l'indirizzo quando cambia il contenuto, così i browser non mostrano la versione vecchia."""
    import hashlib
    return hashlib.sha1((ROOT / "assets" / name).read_bytes()).hexdigest()[:8]


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
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; connect-src 'none'; object-src 'none'; base-uri 'self'; form-action 'none'">
<meta name="referrer" content="strict-origin-when-cross-origin">
<link rel="stylesheet" href="{rel}assets/style.css?v={ver('style.css')}">
<script src="{rel}assets/ora.js?v={ver('ora.js')}" defer></script>
{extra_head}
</head>
<body>
<div class="wrap">
  <header class="site">
    <a class="mark" href="{rel or './'}">{NAME}<span>.</span></a>
    <time class="now" id="adesso" hidden></time>
    <nav class="main" aria-label="Sezioni">
      <a href="{rel or './'}#archivio">Articoli</a>
      <a href="{rel}chi-sono/">Chi sono</a>
    </nav>
  </header>
  <main>
{main}
  </main>
  <footer class="site">
    <span>© {posts[0]["data"][:4]} {NAME} · Tutti i diritti riservati</span>
    <a href="{LINKEDIN}" target="_blank" rel="noopener">LinkedIn ↗</a>
    <span class="rights">Testi e immagini non possono essere copiati o ripubblicati senza autorizzazione. Puoi citarne brevi estratti indicando l'autore e il link all'articolo.</span>
    <span class="privacy">Questo sito non usa cookie, non raccoglie dati e non traccia i visitatori.</span>
  </footer>
</div>
</body>
</html>
"""

def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"

PERSON = {"@type": "Person", "name": NAME, "jobTitle": "Chief Financial Officer", "image": SITE + "/assets/ritratto.jpg",
          "worksFor": {"@type": "Organization", "name": "Ecom S.p.A. – Energia Comune"},
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

def upcoming(html_text):
    """{PROSSIMO:AAAA-MM-GG} diventa "In programma · " finché la data non è passata."""
    import datetime
    today = datetime.date.today().isoformat()
    return re.sub(r"\{PROSSIMO:(\d{4}-\d{2}-\d{2})\}",
                  lambda m: '<em class="soon">In programma</em> · ' if m.group(1) >= today else "", html_text)


SEO = {k: v for k, v in json.load(open(ROOT / "seo.json", encoding="utf-8")).items() if not k.startswith("_")} \
    if (ROOT / "seo.json").exists() else {}

STOP = set("""a ad al alla alle anche ancora che chi ci come con cosa da dal dalla dei del della delle di e ed gli ha hanno ho i il in
io la le lo loro ma mai mi ne nei nel nella noi non o per perché più può quando quanto questo questa se si sia sono su sul
sulla tra tutti tutto un una uno è era essere fa fare già oggi solo sempre poi molto ogni quello quella dove anni anno
the and of to""".split())


def _parole(t):
    return {w[:7] for w in re.findall(r"[a-zàèéìòù0-9]{4,}", t.lower()) if w not in STOP}


def correlati(posts, n=3):
    """Per ogni articolo, i 3 più vicini per hashtag e parole del titolo e dell'apertura (stessa area favorita)."""
    info = []
    for p in posts:
        info.append((set(h.lower() for h in p["hashtag"]), _parole(p["titolo"]), _parole(" ".join(p["testo"][:4]))))
    out = {}
    for i, p in enumerate(posts):
        tags, tit, body = info[i]
        scored = []
        for j, q in enumerate(posts):
            if i == j: continue
            t2, ti2, b2 = info[j]
            s = 3 * len(tags & t2) + 4 * len(tit & ti2) + 1.5 * len(tit & b2) + 1.5 * len(body & ti2) + 0.5 * len(body & b2)
            if q["area"] == p["area"]: s += 2
            scored.append((s, q["data"], j))
        scored.sort(reverse=True)
        out[p["slug"]] = [posts[j] for s, d, j in scored[:n] if s > 2]
    return out


def build():
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    shutil.copy(ROOT / "assets" / "style.css", OUT / "assets" / "style.css")
    shutil.copy(ROOT / "assets" / "site.js", OUT / "assets" / "site.js")
    shutil.copy(ROOT / "assets" / "ora.js", OUT / "assets" / "ora.js")
    shutil.copy(ROOT / "assets" / "favicon.svg", OUT / "favicon.svg")
    shutil.copy(ROOT / "assets" / "ritratto.jpg", OUT / "assets" / "ritratto.jpg")
    shutil.copy(ROOT / "assets" / "qr-linkedin.svg", OUT / "assets" / "qr-linkedin.svg")
    for f in ("carta.png", "carta-scura.png"):  # grana della carta per lo sfondo
        shutil.copy(ROOT / "assets" / f, OUT / "assets" / f)
    for i in (1, 2, 3):
        shutil.copy(ROOT / "assets" / f"evento-{i}.jpg", OUT / "assets" / f"evento-{i}.jpg")
    shutil.copytree(ROOT / "assets" / "fonts", OUT / "assets" / "fonts")
    (OUT / "CNAME").write_text("domenicofraccalvieri.it\n")
    (OUT / ".nojekyll").write_text("")
    shutil.copy(ROOT / "assets" / "BingSiteAuth.xml", OUT / "BingSiteAuth.xml")  # verifica Bing Webmaster Tools
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")

    # articoli
    rel = correlati(posts)
    for i, p in enumerate(posts):
        seo = SEO.get(p["slug"], {})
        desc = seo.get("descrizione") or p["estratto"]
        related = "".join(f'<li><a href="../{q["slug"]}/"><span class="tag">{q["area"]}</span>{inline(q["titolo"])}</a></li>' for q in rel.get(p["slug"], []))
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
    {f'<section class="related" aria-labelledby="rel-h"><h2 id="rel-h">Leggi anche</h2><ul>{related}</ul></section>' if related else ''}
    <nav class="pager" aria-label="Altri articoli">{pager}</nav>
  </article>"""
        ld = jsonld({"@context": "https://schema.org", "@type": "BlogPosting", "headline": plain(p["titolo"])[:110],
                     "description": desc, "datePublished": p["data"], "inLanguage": "it-IT",
                     "articleSection": p["area"], "keywords": p["hashtag"], "author": PERSON,
                     "copyrightHolder": {"@type": "Person", "name": NAME}, "copyrightYear": int(p["data"][:4]),
                     "mainEntityOfPage": f"{SITE}/articoli/{p['slug']}/"})
        d = OUT / "articoli" / p["slug"]; d.mkdir(parents=True)
        (d / "index.html").write_text(page(f"{seo.get('titolo') or plain(p['titolo'])} · {NAME}", desc, f"/articoli/{p['slug']}/", main,
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
  <section class="home-about" aria-label="Chi sono">
    <img src="assets/ritratto.jpg" alt="Domenico Fraccalvieri" width="96" height="96">
    <div><p class="label">Chi sono</p>
      <p class="t">Dal customer care alla direzione finanziaria di Energia Comune.</p>
      <a class="more-link" href="chi-sono/">Leggi la mia storia →</a></div>
    <div class="qr"><img src="assets/qr-linkedin.svg" alt="Codice QR del profilo LinkedIn di Domenico Fraccalvieri" width="96" height="96"><span>LinkedIn</span></div>
  </section>"""
    ld = jsonld({"@context": "https://schema.org", "@type": "WebSite", "name": NAME, "url": SITE + "/", "inLanguage": "it-IT", "author": PERSON})
    (OUT / "index.html").write_text(page(f"{NAME} · Energia, finanza e valori",
        "Domenico Fraccalvieri, CFO di Energia Comune, scrive di mercato dell'energia, bollette, finanza d'impresa e leadership.",
        "/", main, ld + '\n<meta property="og:type" content="website">\n<script src="assets/site.js?v=' + ver("site.js") + '" defer></script>'), encoding="utf-8")

    # chi sono
    d = OUT / "chi-sono"; d.mkdir()
    (d / "index.html").write_text(page(f"Chi sono · {NAME}",
        "Domenico Fraccalvieri: dal customer care alla direzione finanziaria di Ecom S.p.A. – Energia Comune. Percorso, competenze e interventi.",
        "/chi-sono/", upcoming((ROOT / "assets" / "chi-sono.html").read_text(encoding="utf-8").replace("{EC_BOX}", "")), jsonld({"@context": "https://schema.org", "@type": "ProfilePage", "mainEntity": PERSON}), depth=1), encoding="utf-8")

    # 404
    (OUT / "404.html").write_text(page(f"Pagina non trovata · {NAME}", "Pagina non trovata.", "/404.html",
        '<section class="hero"><h1>Pagina non trovata.</h1><p>Il link potrebbe essere cambiato. <a href="/">Torna agli articoli</a>.</p></section>'), encoding="utf-8")

    # sitemap
    urls = [(SITE + "/", posts[0]["data"]), (SITE + "/chi-sono/", posts[0]["data"])] + \
           [(f"{SITE}/articoli/{p['slug']}/", p["data"]) for p in posts]
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls) + "</urlset>\n")
    # llms.txt: riassunto del sito per i sistemi di intelligenza artificiale (https://llmstxt.org)
    count = {a: sum(1 for p in posts if p["area"] == a) for a in AREAS}
    lines = [
        f"# {NAME}",
        "",
        "> Sito personale e blog di Domenico Fraccalvieri, Chief Financial Officer (CFO) di Ecom S.p.A. – Energia Comune, "
        "società che vende luce e gas a famiglie e imprese. Lavora in Puglia (Italia). Scrive di mercato dell'energia, "
        "bollette, finanza d'impresa, attualità e valori della leadership. Gli articoli sono i suoi post di LinkedIn.",
        "",
        "- Ruolo: CFO di Ecom S.p.A. – Energia Comune, dal dicembre 2023. In azienda dal 2020, partito dal customer care "
        "e passato per fatturazione (Billing Manager) prima della direzione finanziaria.",
        "- In precedenza ha fondato e guidato due imprese, nelle telecomunicazioni e nei servizi.",
        "- Formazione: laurea in Ingegneria gestionale al Politecnico di Bari; certificazione Utility Manager UNI 11782:2020.",
        f"- Profilo LinkedIn: {LINKEDIN}",
        "- Questo sito riguarda solo il Domenico Fraccalvieri CFO in Puglia: non ha legami con professionisti omonimi di altri settori o Paesi.",
        f"- Articoli pubblicati: {len(posts)} (" + ", ".join(f"{a}: {count[a]}" for a in AREAS) + "), aggiornati ogni giorno.",
        "",
        "## Pagine principali",
        "",
        f"- [Chi sono]({SITE}/chi-sono/): percorso professionale, aree di responsabilità, interventi pubblici e certificazioni",
        f"- [Tutti gli articoli]({SITE}/): archivio completo, filtrabile per area",
        f"- [Mappa del sito]({SITE}/sitemap.xml): elenco di tutte le pagine",
        "",
    ]
    for a in AREAS:
        lines += [f"## Articoli recenti · {a}", ""]
        for p in [x for x in posts if x["area"] == a][:12]:
            lines.append(f"- [{plain(p['titolo'])}]({SITE}/articoli/{p['slug']}/): {p['estratto']}")
        lines.append("")
    (OUT / "llms.txt").write_text("\n".join(lines), encoding="utf-8")

    print(f"Generati {len(posts)} articoli in {OUT}")

if __name__ == "__main__":
    build()
