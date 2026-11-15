#!/usr/bin/env python3
"""Avvisa Bing (e gli altri motori che aderiscono a IndexNow) delle pagine nuove o cambiate.

Confronta la sitemap appena generata con quella di prima dell'aggiornamento e invia solo gli indirizzi nuovi
o con data cambiata. Con TUTTE=1 invia l'intero sito (da usare una volta sola).
Non serve nessun account: la chiave è un file pubblico sul sito, come previsto dal protocollo.
"""
import json, os, re, sys, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "domenicofraccalvieri.it"
KEY = (ROOT / "assets" / "indexnow-key.txt").read_text().strip()


def entries(xml):
    return dict(re.findall(r"<loc>(.*?)</loc><lastmod>(.*?)</lastmod>", xml))


new = entries((ROOT / "docs" / "sitemap.xml").read_text())
if os.environ.get("TUTTE") == "1":
    urls = list(new)
else:
    prima = Path(os.environ.get("SITEMAP_PRIMA", ""))
    old = entries(prima.read_text()) if prima.is_file() else {}
    urls = [u for u, d in new.items() if old.get(u) != d]

if not urls:
    print("IndexNow: nessuna pagina nuova da segnalare.")
    sys.exit(0)

body = json.dumps({"host": HOST, "key": KEY, "keyLocation": f"https://{HOST}/{KEY}.txt", "urlList": urls[:10000]}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json; charset=utf-8"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"IndexNow: {len(urls)} indirizzi segnalati, risposta {r.status}.")
except urllib.error.HTTPError as e:
    # non blocca la pubblicazione: al massimo Bing li troverà più tardi dalla sitemap
    print(f"IndexNow: risposta {e.code} {e.read().decode('utf-8', 'replace')[:200]}")
