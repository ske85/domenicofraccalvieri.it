# domenicofraccalvieri.it

Sito personale e blog di Domenico Fraccalvieri. I post vengono da LinkedIn.

- `posts.json`: tutti gli articoli (un oggetto per post)
- `build.py`: genera il sito in `docs/` (`python3 build.py`)
- `assets/`: stile, script e icona
- `docs/`: il sito pubblicato da GitHub Pages (non modificare a mano)

## Aggiornamento automatico da LinkedIn

Ogni mattina `.github/workflows/linkedin.yml` esegue `scripts/sync_linkedin.py`,
che legge i post tramite la Member Data Portability API di LinkedIn (segreto
`LINKEDIN_TOKEN`), aggiunge i nuovi a `posts.json`, rigenera `docs/` e pubblica.
Se il token scade, il workflow fallisce e GitHub invia un'email: basta generarne
uno nuovo e aggiornare il segreto.
