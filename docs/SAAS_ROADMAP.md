# Roadmap SaaS — optimisations

## ✅ Étape 1 — Fait (cache & charge)

- [x] `storage/cache_service.py` — Redis + mémoire, verrou anti-stampede, stale
- [x] Caches partagés : cotations, comparer, marché, palmarès, accueil, analyses
- [x] `ALLOW_LIVE_QUOTE_FETCH` — couper les scrapes côté visiteur
- [x] `GET /api/home` — 1 requête pour l'accueil
- [x] `GET /api/health`
- [x] Rate limiting (`api/rate_limit.py`)
- [x] `scripts/warm_api_cache.py` + `gunicorn.conf.py` + Redis dans `docker-compose.yml`

## ✅ Étape 2 — Workers scrape (fait)

- [x] `DISABLE_SCRAPE_SCHEDULER` sur l'API (voir `.env.api.example`)
- [x] `scrape_companies.py` — scrape + sync DB + post-hooks (warm)
- [x] `scripts/run_scrape_worker.py` — boucle scrape dédiée
- [x] `jobs/post_scrape.py` — invalidation Redis + `warm_api_caches()`
- [x] `scripts/crontab.example` — scrape */2h + warm */5min
- [x] Guide : `docs/ETAPE2_WORKERS.md`

## ✅ Palmarès accueil (slide Top hausses / baisses)

- [x] Snapshot `data/palmares_snapshot.json` (Sikafinance Variation)
- [x] **Lun–ven** : rafraîchissement toutes les **4 h** (`jobs/palmares_refresh.py`, `PALMARES_INTERVAL_HOURS=4`)
- [x] **Sam–dim** : pas de fetch — dernière sauvegarde du **vendredi**
- [x] Cron : `scripts/refresh_palmares.py` (voir `scripts/crontab.example`)

## ▶ Étape 3 — Déploiement

- [ ] Nginx + TLS + Gunicorn (`gunicorn -c gunicorn.conf.py app:app`)
- [ ] CDN pour `static/frontend`
- [ ] `ALLOW_LIVE_QUOTE_FETCH=false` sur l'API
- [ ] `REDIS_URL` obligatoire si plusieurs workers
- [ ] Sentry + alertes `/api/health`

## ▶ Étape 4 — Scale 10k MAU

- [ ] 2+ instances API + load balancer
- [ ] MySQL read replica
- [ ] Celery pour tâches lourdes
- [ ] Cloudflare cache court sur `GET /api/home` et `/api/compare/by-sector`
