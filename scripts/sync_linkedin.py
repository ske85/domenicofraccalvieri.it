#!/usr/bin/env python3
"""Scarica i post da LinkedIn (Member Data Portability API) e aggiunge i nuovi a posts.json.

Richiede la variabile d'ambiente LINKEDIN_TOKEN (segreto del repository).
Stampa solo conteggi e titoli: i log di un repository pubblico sono visibili a tutti.
"""
import json, os, re, sys, unicodedata, urllib.request, urllib.error, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "posts.json"
API = "https://api.linkedin.com/rest/memberSnapshotData"
MIN_CHARS = 200

AREA_WORDS = {
    "Energia": ["energia", "energetic", "bollett", "pun", "arera", "gas", "ttf", "elettric", "rinnovabil", "fotovolta",
                "eolic", "petrolio", "carburant", "terna", "snam", "curtailment", "kwh", "mwh", "utility", "utilities",
                "transizione", "accumul", "rete elettrica", "luce", "energiacomune", "energia comune"],
    "Finanza": ["finanz", "cfo", "bce", "banc", "tassi", "inflazion", "debito", "deficit", "pil", "fisco", "fiscal",
                "irpef", "tasse", "cassa", "cash", "ebitda", "bilanci", "utili", "m&a", "acquisizion", "borsa",
                "piazza affari", "investiment", "previdenz", "pension", "tfr", "inps", "capitale circolante", "budget"],
    "Valori": ["leadership", "valori", "merito", "rispetto", "etica", "coerenza", "responsabilit", "gentilezza",
               "empatia", "team", "collaborator", "persone", "crescitapersonale", "mindset", "fiducia", "libertà"],
}


def log(*a):
    print(*a, flush=True)


DIAG = {}


def probe_domains(token):
    """Chiede a LinkedIn quali categorie di dati sono pronte (solo nomi e conteggi, nessun contenuto)."""
    found = {}
    for start in range(0, 40):
        qs = urllib.parse.urlencode({"q": "criteria", "start": start})
        req = urllib.request.Request(f"{API}?{qs}", headers={
            "Authorization": f"Bearer {token}", "Linkedin-Version": "202312", "X-Restli-Protocol-Version": "2.0.0"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            DIAG["probe_errore"] = f"{e.code} {e.read().decode('utf-8', 'replace')[:160]}"
            break
        els = data.get("elements", [])
        if not els:
            break
        for el in els:
            d = el.get("snapshotDomain", "?")
            found[d] = found.get(d, 0) + len(el.get("snapshotData", []))
    DIAG["categorie_disponibili"] = found


def fetch_shares(token):
    rows, start = [], 0
    while True:
        qs = urllib.parse.urlencode({"q": "criteria", "domain": "MEMBER_SHARE_INFO", "start": start})
        req = urllib.request.Request(f"{API}?{qs}", headers={
            "Authorization": f"Bearer {token}", "Linkedin-Version": "202312", "X-Restli-Protocol-Version": "2.0.0"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            if e.code in (401, 403):
                log(f"ERRORE {e.code}: il token LinkedIn non è valido o è scaduto. Generane uno nuovo e aggiorna il segreto LINKEDIN_TOKEN.")
                log("Dettaglio:", body)
                sys.exit(1)
            if e.code == 404 or "No data found" in body:
                DIAG.setdefault("risposta_post", f"{e.code} {body[:160]}")
                break
            log(f"ERRORE {e.code} da LinkedIn:", body)
            sys.exit(1)
        DIAG.setdefault("risposta_post", f"200, elementi: {len(data.get('elements', []))}")
        page = []
        for el in data.get("elements", []):
            page.extend(el.get("snapshotData", []))
        rows.extend(page)
        nxt = [l for l in data.get("paging", {}).get("links", []) if l.get("rel") == "next"]
        if not page or not nxt:
            break
        start += 1
        if start > 200:
            break
    return rows


def pick(row, *names):
    low = {k.lower().replace(" ", ""): v for k, v in row.items()}
    for n in names:
        v = low.get(n.lower().replace(" ", ""))
        if v not in (None, ""):
            return str(v)
    return ""


def paragraphs(raw):
    lines = raw.replace("\r", "").split("\n")
    wrapped = sum(1 for l in lines[1:] if l.startswith('"') and l.endswith('"'))
    quirky = len(lines) > 1 and wrapped >= (len(lines) - 1) * 0.5
    out = []
    for i, l in enumerate(lines):
        if quirky:
            if i > 0 and l.startswith('"'): l = l[1:]
            if i < len(lines) - 1 and l.endswith('"'): l = l[:-1]
        out.append(l.strip())
    tags = []
    while out and (out[-1] == "" or re.fullmatch(r"(#\S+\s*)+", out[-1])):
        tags = re.findall(r"#(\S+)", out[-1]) + tags
        out.pop()
    return [p for p in out if p], tags


def clean_title(t):
    t = t.replace("**", "").strip()
    return re.sub(r'^[^\w"“«(]+', "", t).strip()


def short(t, n):
    if len(t) <= n: return t
    return t[:n].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def slugify(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    out = ""
    for w in re.sub(r"[^a-z0-9]+", "-", t).strip("-").split("-"):
        if len(out) + len(w) + 1 > 60: break
        out = (out + "-" + w).strip("-")
    return out or "post"


def area_for(text, tags):
    hay = (text + " " + " ".join(tags)).lower()
    tagtxt = " ".join(tags).lower()
    score = {}
    for a, words in AREA_WORDS.items():
        score[a] = sum(hay.count(w) for w in words) + 3 * sum(tagtxt.count(w) for w in words)
    best = max(score, key=score.get)
    return best if score[best] >= 3 else "Attualità"


def norm_text(s):
    return re.sub(r"\W+", "", s.lower())[:160]


def main():
    token = os.environ.get("LINKEDIN_TOKEN", "").strip()
    if not token:
        log("ERRORE: manca il segreto LINKEDIN_TOKEN."); sys.exit(1)
    posts = json.load(open(POSTS, encoding="utf-8"))
    known_links = {p["linkedin"] for p in posts}
    known_text = {norm_text(" ".join(p["testo"])) for p in posts}
    slugs = {p["slug"] for p in posts}

    rows = fetch_shares(token)
    log(f"LinkedIn ha restituito {len(rows)} post.")
    if rows:
        log("Campi disponibili:", ", ".join(sorted(rows[0].keys())))

    dates = sorted(pick(r, "Date", "Created", "Created At")[:10] for r in rows)
    status = {"post_ricevuti_da_linkedin": len(rows), "campi": sorted(rows[0].keys()) if rows else [],
              "post_piu_recente_su_linkedin": dates[-1] if dates else None, "articoli_sul_sito": None}
    added = []
    for r in rows:
        link = pick(r, "ShareLink", "Share Link", "Link")
        raw = pick(r, "ShareCommentary", "Share Commentary", "Commentary", "Text")
        date = pick(r, "Date", "Created", "Created At")[:10]
        if not raw or not re.match(r"\d{4}-\d{2}-\d{2}", date):
            continue
        body, tags = paragraphs(raw)
        text = " ".join(body)
        if len(text) < MIN_CHARS or link in known_links or norm_text(text) in known_text:
            continue
        first = body[0]
        if len(first) <= 125 and len(body) > 1 and not first.startswith("http"):
            title, rest = clean_title(first), body[1:]
        else:
            if first.startswith("http") and len(body) > 1:
                body = body[1:]; first = body[0]
            title = clean_title(short(re.split(r"(?<=[.!?])\s", first)[0], 110)); rest = body
        excerpt = short(re.sub(r"https?://\S+", "", rest[0].replace("**", "")).strip(), 190)
        slug = slugify(title)
        if slug in slugs: slug = f"{slug}-{date.replace('-', '')}"
        slugs.add(slug)
        shared = pick(r, "SharedUrl", "Shared Url", "SharedURL")
        post = {"slug": slug, "data": date, "area": area_for(text, tags), "titolo": title, "estratto": excerpt,
                "testo": rest, "hashtag": tags[:6], "linkedin": link,
                "fonte": "" if "linkedin.com" in shared else shared}
        posts.append(post); added.append(post)
        known_links.add(link); known_text.add(norm_text(text))

    status["articoli_sul_sito"] = len(posts)
    if not rows:
        probe_domains(token)
    status["diagnosi"] = DIAG
    (ROOT / "stato-linkedin.json").write_text(json.dumps(status, ensure_ascii=False, indent=1) + "\n")
    if not added:
        log("Nessun post nuovo.")
        return
    posts.sort(key=lambda p: p["data"], reverse=True)
    json.dump(posts, open(POSTS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for p in added:
        log(f"Aggiunto [{p['area']}] {p['data']} · {p['titolo']}")


if __name__ == "__main__":
    main()
