"""Nomi da non pubblicare mai sul sito: ogni articolo, anche quelli nuovi da LinkedIn, passa da qui.

Per aggiungere un nome: una riga in REGOLE, dalla forma più specifica alla più generica.
Le sostituzioni valgono per titolo, estratto, testo e hashtag; il link dell'articolo nasce dal titolo già ripulito.
"""
import re

PERSONA = "un parlamentare"
AZIENDA = "un'azienda energetica"

# (espressione regolare, sostituzione). Le più specifiche prima.
REGOLE = [
    # persone
    (r"\b(?:Carlo\s+)?Calenda\s+stesso\b", "il parlamentare stesso"),
    (r"\b(?:al\s+senatore|a)\s+(?:Carlo\s+)?Calenda\b", "a un parlamentare"),
    (r"\b(?:di|del\s+senatore)\s+(?:Carlo\s+)?Calenda\b", "di un parlamentare"),
    (r"\b(?:il\s+senatore\s+)?(?:Carlo\s+)?Calenda\b", PERSONA),
    # aziende
    (r"\bEDF\s*/\s*Edison\b", "EDF"),
    (r"\b(?:a|ad)\s+(?:Enel|A2A|Edison)\b", "a " + AZIENDA),
    (r"\bdi\s+(?:Enel|A2A|Edison)\b", "di " + AZIENDA),
    (r"\b(?:Enel|ENEL|A2A|Edison|EDISON)\b(?:\s+(?:S\.p\.A\.|SpA|Energia|X|Green Power))?", AZIENDA),
]
_RX = [(re.compile(p, re.I if "Calenda" in p else 0), s) for p, s in REGOLE]
# hashtag con i nomi: vengono tolti, non riscritti
TAG_VIETATI = re.compile(r"calenda|^enel|a2a|edison", re.I)


def _maiuscola_a_inizio_frase(t):
    return re.sub(r"(^|[.!?]\s+|\n)(un['\s]|due\s|alcune\s)", lambda m: m.group(1) + m.group(2)[0].upper() + m.group(2)[1:], t)


def testo(t):
    if not t:
        return t
    for rx, s in _RX:
        t = rx.sub(s, t)
    t = re.sub(r"\b(un'azienda energetica)(?:,\s*\1)+(?:\s+(?:e|ed)\s+\1)?", "alcune aziende energetiche", t)
    t = re.sub(r"\b(un'azienda energetica)\s+(?:e|ed)\s+\1", "due aziende energetiche", t)
    return _maiuscola_a_inizio_frase(t)


def post(p):
    """Restituisce una copia dell'articolo senza i nomi vietati."""
    q = dict(p)
    q["titolo"] = testo(p.get("titolo", ""))
    q["estratto"] = testo(p.get("estratto", ""))
    q["testo"] = [testo(x) for x in p.get("testo", [])]
    q["hashtag"] = [h for h in p.get("hashtag", []) if not TAG_VIETATI.search(h)]
    return q


def contiene_nomi(s):
    return any(rx.search(s) for rx, _ in _RX) or bool(TAG_VIETATI.search(s))
