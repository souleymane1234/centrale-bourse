# BRVM Agent — Dashboard

Architecture **API Flask** + **frontend React** (Vite).

## Développement (recommandé)

Deux terminaux :

```bash
# Terminal 1 — API
pip install -r requirements.txt
python3 app.py
```

```bash
# Terminal 2 — Frontend (hot reload)
cd frontend
npm install
npm run dev
```

Ouvrir **http://127.0.0.1:5173** — Vite proxy les appels `/api/*` vers Flask (`5050`).

Routes : `/` (liste des sociétés), `/societe/SONATEL` (fiche détaillée partageable).

## Production (SaaS)

```bash
docker compose up -d mysql redis
cd frontend && npm install && npm run build && cd ..
pip install -r requirements.txt

# API sans scrape intégré (voir .env.api.example)
export DISABLE_SCRAPE_SCHEDULER=true
export ALLOW_LIVE_QUOTE_FETCH=false
gunicorn -c gunicorn.conf.py app:app

# Worker scrape (autre terminal / autre machine — voir .env.worker.example)
python scripts/run_scrape_worker.py
# ou scrape unique : python scrape_companies.py

# Cron warm entre deux scrapes (voir scripts/crontab.example)
python scripts/warm_api_cache.py

# API (Gunicorn)
export ALLOW_LIVE_QUOTE_FETCH=false
export REDIS_URL=redis://127.0.0.1:6379/0
gunicorn -c gunicorn.conf.py app:app
```

Ouvrir **http://127.0.0.1:5050** — Flask/Gunicorn sert le build React depuis `static/frontend/`.

Endpoints utiles : `GET /api/health`, `GET /api/home` (accueil en 1 requête).

Guide workers (étape 2) : [docs/ETAPE2_WORKERS.md](docs/ETAPE2_WORKERS.md).

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Santé API + état Redis |
| `GET /api/home` | Accueil (sociétés + marché, cache) |
| `GET /api/companies` | Liste des sociétés |
| `GET /api/market-summary` | Vue marché globale |
| `GET /api/analysis/<ticker>` | Analyse complète |
| `GET /api/refresh/<ticker>` | Rafraîchir le cache d'analyse |

## Variables d'environnement

- `CORS_ORIGINS` — origines autorisées (séparées par des virgules). Défaut : `*`.
- `SCRAPE_INTERVAL_HOURS` — intervalle entre deux scrapes complets. Défaut : `2`.
- `SCRAPE_ON_STARTUP` — lancer un scrape au démarrage de l'API (`true` / `false`). Défaut : `true`.
- `DISABLE_SCRAPE_SCHEDULER` — désactiver le planificateur (`1` / `true`). Défaut : désactivé.
- `REDIS_URL` — cache partagé (obligatoire multi-workers). Ex. `redis://127.0.0.1:6379/0`.
- `ALLOW_LIVE_QUOTE_FETCH` — `false` en prod API : pas de scrape Sikafinance par visiteur.
- `DISABLE_SCRAPE_SCHEDULER` — `true` sur l'API publique ; scrape sur worker/cron.
- `RATE_LIMIT_PER_MINUTE` — limite requêtes `/api/*` par IP (défaut `120`).
- `LISTED_COMPANIES_CACHE_TTL` — cache des cotations (secondes). Défaut : `300`.
- `PALMARES_CACHE_TTL` — cache du palmarès (secondes). Défaut : `300`.
- `COMPARE_CACHE_TTL_SECONDS` — cache comparer (défaut `300`).
- `ANALYSIS_CACHE_TTL_SECONDS` — cache fiche société (défaut `1800`).

Le scrape complet (`data/companies_full.json`) tourne en arrière-plan tant que Flask est lancé.
Scrape manuel ponctuel : `python scrape_companies.py`.

## Base de données

### MySQL (Docker — recommandé)

1. Copier la configuration :

```bash
cp .env.example .env
```

2. Démarrer MySQL (ou utiliser votre conteneur existant avec les mêmes variables) :

```bash
docker compose up -d mysql
```

3. Installer les dépendances et créer les tables :

```bash
pip install -r requirements.txt
python scripts/init_database.py
python scripts/backfill_prices.py
```

4. Lancer l’API avec `DB_ENGINE=mysql` dans `.env`.

### Tables principales

| Table | Rôle |
|-------|------|
| `companies` | Sociétés + fiche complète (`raw_payload` JSON) |
| `stock_prices` | Cours quotidiens (graphiques) |
| `company_financials` | Historique financier BRVM |
| `market_indices` | Indices BRVM |
| `users` | Comptes utilisateurs |
| `user_sessions` | Jetons de connexion |
| `subscription_plans` | Offres (Gratuit, Pro…) |
| `subscriptions` | Abonnements actifs |
| `scrape_runs` | Journal des synchronisations |

### SQLite (développement sans Docker)

`.env` : `DB_ENGINE=sqlite` — fichier `data/brvm.db`.

### API données & comptes

| Endpoint | Description |
|----------|-------------|
| `GET /api/prices/<ticker>` | Historique des cours |
| `GET /api/dataset-status` | État base + scrape |
| `POST /api/auth/register` | Créer un compte |
| `POST /api/auth/login` | Connexion (retourne un token) |
| `GET /api/auth/me` | Profil (`Authorization: Bearer <token>`) |
| `GET /api/subscriptions/plans` | Liste des offres |

Migration SQLite → MySQL : `python scripts/migrate_sqlite_to_mysql.py`

### Historique des cours (graphiques réels)

Les séances passées sont importées depuis Sikafinance (`/marches/historiques/{code}`) :

```bash
python scripts/backfill_price_history.py
```

Environ 60 séances par société. Les graphiques utilisent ensuite `stock_prices` en priorité.
Au premier chargement d'une fiche, l'historique est complété automatiquement si la base est incomplète.
