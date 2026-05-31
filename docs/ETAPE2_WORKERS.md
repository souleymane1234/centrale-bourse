# Étape 2 — Workers scrape & cache (séparés de l’API)

## Principe

| Processus | Rôle | Variables clés |
|-----------|------|----------------|
| **API** (`gunicorn app:app`) | Répond aux utilisateurs, lit Redis/DB | `DISABLE_SCRAPE_SCHEDULER=true`, `ALLOW_LIVE_QUOTE_FETCH=false` |
| **Worker scrape** | Met à jour `companies_full.json` + MySQL | `ALLOW_LIVE_QUOTE_FETCH=true`, `WARM_CACHE_AFTER_SCRAPE=true` |
| **Cron warm** (optionnel) | Rafraîchit le cache entre deux scrapes | `python scripts/warm_api_cache.py` |

## Fichier d’environnement

Tout est dans **`.env`** à la racine du projet.

- **API** : `ALLOW_LIVE_QUOTE_FETCH=false`, `DISABLE_SCRAPE_SCHEDULER=true`
- **Worker** : les scripts `scrape_companies.py`, `run_scrape_worker.py` et `warm_api_cache.py` passent automatiquement `ALLOW_LIVE_QUOTE_FETCH=true` pour leur processus

Pas besoin de `.env.worker` ni de `export $(grep ...)`.

## Lancer en local (2 terminaux)

**Infra (une fois)**

```bash
docker compose up -d mysql redis
```

**Terminal 1 — API**

```bash
cd /chemin/vers/brvm_agent
python3 app.py
```

**Terminal 2 — worker scrape (boucle toutes les 2 h)**

```bash
cd /chemin/vers/brvm_agent
python3 scripts/run_scrape_worker.py
```

**Ou scrape unique + warm :**

```bash
python scrape_companies.py
```

**Warm manuel (comme cron */5) :**

```bash
python scripts/warm_api_cache.py
```

## Cron (production sans processus worker permanent)

Voir `scripts/crontab.example` :

- Scrape : `0 */2 * * *` → `scrape_companies.py`
- Warm : `*/5 * * * *` → `scripts/warm_api_cache.py`

Créez le dossier logs : `mkdir -p logs`

## Vérifications

- `GET /api/health` → `scrape_scheduler_disabled: true` sur l’API
- `GET /api/dataset-status` → `worker_hint` avec la commande scrape
- Après scrape : les pages Comparer / Accueil se chargent vite (cache Redis chaud)
