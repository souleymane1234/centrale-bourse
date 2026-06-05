# Centrale Bourse — Système complet & déploiement VPS

Document de référence unique pour comprendre l’application et la mettre en ligne sur votre VPS Ubuntu.

**Marque :** Centrale Bourse (ex-BRVM Agent) — édité par KS Solution.

---

## 1. En une phrase

Plateforme web d’**analyse et d’information** sur les sociétés cotées à la **BRVM** : cours, graphiques, comparatifs sectoriels, actualités, suivi personnel. **Ce n’est pas un courtier** — aucun ordre d’achat/vente.

---

## 2. Architecture globale

```
┌─────────────────────────────────────────────────────────────────────────┐
│  NAVIGATEUR (utilisateur)                                               │
│  React (SPA) — routes /, /societe/…, /comparer, /actualites, /profil   │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ HTTP
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  NGINX (recommandé en prod)                                             │
│  • Port public : 8080 (pré-prod IP) ou 80/443 (domaine + HTTPS)       │
│  • Sert static/frontend/ (fichiers React buildés)                     │
│  • Proxy /api/* → Gunicorn 127.0.0.1:5051                               │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  API PYTHON — Gunicorn (systemd : centrale-bourse-api)                  │
│  Flask app.py — routes /api/home, /api/analysis, /api/auth, …         │
│  • Ne scrape PAS à chaque clic visiteur (prod)                          │
│  • Lit MySQL + Redis                                                    │
└───────┬─────────────────────────────┬───────────────────────────────────┘
        │                             │
        ▼                             ▼
┌───────────────┐             ┌───────────────────┐
│  MySQL        │             │  Redis            │
│  brvm_agent   │             │  Cache API        │
│  comptes,     │             │  (cotations,      │
│  cours,       │             │   accueil,        │
│  sociétés,    │             │   analyses…)      │
│  actualités   │             └───────────────────┘
└───────────────┘
        ▲
        │ écritures planifiées
┌───────┴─────────────────────────────────────────────────────────────────┐
│  TÂCHES ARRIÈRE-PLAN (cron ou worker séparé — PAS dans Gunicorn)        │
│  • scrape_companies.py      → sociétés + cours + fondamentaux (2 h)   │
│  • refresh_palmares.py      → top hausses/baisses (lun–ven, 4 h)      │
│  • warm_api_cache.py        → pré-chauffe Redis (5 min)               │
│  • migrate_news_articles.py → import actualités JSON → MySQL (1×)     │
└─────────────────────────────────────────────────────────────────────────┘
        ▲
        │ sources externes
┌───────┴─────────────────────────────────────────────────────────────────┐
│  Sikafinance, BRVM.org (scraping)                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Option sans Nginx (test rapide)

Gunicorn peut écouter directement sur `0.0.0.0:5051` et servir API + frontend. Moins recommandé en production, mais utile pour valider le VPS.

---

## 3. Stack technique

| Couche | Technologie | Rôle |
|--------|-------------|------|
| Frontend | React 18 + Vite + Tailwind | Interface utilisateur (SPA) |
| Build frontend | `npm run build` → `static/frontend/` | Fichiers statiques servis par Nginx ou Flask |
| API | Python 3 + Flask | Logique métier, JSON REST |
| Serveur WSGI | Gunicorn (`gunicorn.conf.py`) | Production multi-workers |
| ORM | SQLAlchemy | Modèles MySQL |
| Cache serveur | Redis (`storage/cache_service.py`) | Réponses API rapides |
| Cache navigateur | Mémoire JS (10 min) | Fiches société sans rechargement visible |
| Base | MySQL 8 (`brvm_agent`) | Données persistantes |
| Dev local | Docker Compose | MySQL (port 3307) + Redis (6379) |

---

## 4. Structure du projet (dossiers importants)

```
brvm_agent/
├── app.py                    # Point d'entrée Flask + routes API principales
├── gunicorn.conf.py          # Config Gunicorn (bind, workers, threads)
├── requirements.txt          # Dépendances Python
├── .env                      # Configuration (NE PAS committer)
├── scrape_companies.py       # Scrape complet marché → MySQL + JSON
│
├── frontend/                 # Code React source
│   └── src/
│       ├── pages/            # HomePage, CompanyPage, ComparePage…
│       ├── api/              # client.js, auth.js, cache mémoire
│       └── components/
│
├── static/frontend/          # Build de production (généré par npm run build)
│
├── storage/                  # DB, cache, auth, abonnements, actualités
│   ├── models.py             # Tables SQLAlchemy
│   ├── cache_service.py      # Redis get_or_build
│   └── news_store.py         # CRUD table news_articles
│
├── api/                      # Blueprints Flask (auth, news, watchlist)
├── collectors/               # Scrapers Sikafinance / BRVM
├── analysis/                 # Technique, fondamentaux, comparer
├── jobs/                     # Planificateurs palmarès (dans le process API)
├── scripts/                  # Migrations, warm cache, cron
├── data/                     # JSON backup (companies_full, news, palmarès)
├── deploy/                   # systemd, nginx, .env exemples VPS
└── docs/                     # Documentation (ce fichier inclus)
```

---

## 5. Pages et parcours utilisateur

### Routes publiques (sans compte)

| URL | Page |
|-----|------|
| `/bienvenue` | Landing marketing (fonctionnalités, accès, FAQ) |
| `/cgu` | Conditions générales |
| `/confidentialite` | Politique de confidentialité |
| `/profil` | Connexion / inscription |

### Routes plateforme (compte requis)

| URL | Page |
|-----|------|
| `/` | Accueil : palmarès, indices, grille sociétés |
| `/societe/:ticker` | Fiche société (analyse complète) |
| `/comparer` | Comparaison sectorielle + face-à-face |
| `/actualites` | Fil d’actualités |
| `/actualites/:slug` | Détail article |
| `/suivi` | Watchlist + alertes de cours |
| `/profil` | Profil utilisateur |

### Règles d’accès (`PlatformGate`)

| Mode | Comportement |
|------|--------------|
| `PAYMENTS_ENABLED=false` (actuel) | Connecté = accès complet à la plateforme |
| `PAYMENTS_ENABLED=true` (futur) | Essai 5 j puis abonnement 2 500 FCFA/mois |

Non connecté → redirection vers `/bienvenue` pour les pages protégées.

---

## 6. API REST principale

| Endpoint | Usage | Cache Redis |
|----------|-------|-------------|
| `GET /api/health` | Santé + état cache | Non |
| `GET /api/home` | Accueil (sociétés + marché) | ~120 s |
| `GET /api/companies` | Liste sociétés | Mémoire app |
| `GET /api/analysis/:ticker` | Fiche société complète | ~30 min |
| `GET /api/compare/by-sector` | Page comparer | ~300 s |
| `GET /api/market-summary` | Résumé marché | ~120 s |
| `GET /api/news` | Actualités paginées | DB MySQL |
| `GET /api/auth/config` | Config publique (`payments_enabled`) | Non |
| `POST /api/auth/register` | Inscription | Non |
| `POST /api/auth/login` | Connexion | Non |
| `GET /api/user/watchlist` | Liste de suivi | Non |
| `GET /api/user/alerts` | Alertes cours | Non |

Rate limiting : `RATE_LIMIT_PER_MINUTE=120` par IP sur `/api/*`.

---

## 7. Base de données MySQL — tables

Base recommandée : **`brvm_agent`** (utf8mb4).

| Table | Contenu |
|-------|---------|
| `companies` | Fiches sociétés (JSON enrichi) |
| `stock_prices` | Historique cours par ticker/date |
| `company_financials` | États financiers scrapés |
| `market_indices` | Indices BRVM |
| `fundamentals` | Ratios fondamentaux |
| `scrape_runs` | Journal des scrapes |
| `users` | Comptes utilisateurs |
| `user_sessions` | Tokens de session |
| `subscription_plans` | Plans (essai, mensuel) |
| `subscriptions` | Abonnements actifs/expirés |
| `referral_earnings` | Commissions parrainage |
| `user_watchlist` | Sociétés suivies |
| `user_price_alerts` | Alertes de seuil |
| `news_articles` | Actualités (remplace le JSON en prod) |

**Création des tables :**

```bash
python scripts/init_database.py
python scripts/migrate_user_billing.py
python scripts/migrate_watchlist_alerts.py
python scripts/migrate_news_articles.py   # importe data/news_articles.json
```

Au démarrage, `app.py` appelle aussi `db.create_all()` si `DB_AUTO_CREATE=true`.

---

## 8. Processus en arrière-plan (critique pour le VPS)

> **Règle d’or :** l’API Gunicorn ne doit **pas** scraper Sikafinance à chaque visiteur.

| Tâche | Fréquence | Commande | Rôle |
|-------|-----------|----------|------|
| Scrape sociétés | Toutes les **2 h** | `python scrape_companies.py` | Met à jour cours, fiches, MySQL |
| Palmarès | Lun–ven / **4 h** | `python scripts/refresh_palmares.py` | Top hausses/baisses accueil |
| Warm cache | Toutes les **5 min** | `python scripts/warm_api_cache.py` | Garde Redis chaud |
| Worker continu (option) | Boucle 2 h | `python scripts/run_scrape_worker.py` | Alternative au cron scrape |

Variables API (dans `.env` du service Gunicorn) :

```env
DISABLE_SCRAPE_SCHEDULER=true    # pas de scrape dans Gunicorn
SCRAPE_ON_STARTUP=false
ALLOW_LIVE_QUOTE_FETCH=false     # pas de fetch Sikafinance par clic visiteur
PALMARES_ON_STARTUP=true         # charge le palmarès au boot API (OK)
```

Les scripts de scrape/warm activent eux-mêmes `ALLOW_LIVE_QUOTE_FETCH=true` le temps de leur exécution.

---

## 9. Variables `.env` expliquées

Copier un modèle :

```bash
cp deploy/env.preprod.example .env    # VPS sans domaine
# ou
cp .env.example .env                  # dev local + Docker
```

### Base de données

| Variable | Exemple local | Exemple VPS |
|----------|---------------|-------------|
| `DB_ENGINE` | `mysql` | `mysql` |
| `MYSQL_HOST` | `127.0.0.1` | `127.0.0.1` |
| `MYSQL_PORT` | `3307` (Docker) | `3306` |
| `MYSQL_DATABASE` | `brvm_agent` | `brvm_agent` |
| `MYSQL_USER` | `root` | `centrale_bourse` |
| `MYSQL_PASSWORD` | … | mot de passe fort |

### API & sécurité

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Clé Flask — **obligatoire en prod** (`secrets.token_hex(32)`) |
| `PORT` | Port dev Flask (`5050`) |
| `GUNICORN_BIND` | `127.0.0.1:5051` derrière Nginx |
| `GUNICORN_WORKERS` | `3` sur VPS 4 vCPU |
| `CORS_ORIGINS` | URL exacte du site (`http://IP:8080` ou `https://domaine`) |
| `FLASK_DEBUG` | `false` en prod |

### Redis & cache

| Variable | Description |
|----------|-------------|
| `REDIS_URL` | `redis://127.0.0.1:6379/0` — utiliser `/1` si `/0` pris |
| `HOME_CACHE_TTL_SECONDS` | Cache accueil (120) |
| `ANALYSIS_CACHE_TTL_SECONDS` | Cache fiche société (1800) |
| `COMPARE_CACHE_TTL_SECONDS` | Cache comparer (300) |

### Comptes & paiement

| Variable | Valeur actuelle | Description |
|----------|-----------------|-------------|
| `PAYMENTS_ENABLED` | `false` | Accès gratuit ; masque UI paiement |
| `PAYMENT_MOCK` | `true` | Paiement simulé si réactivé |
| `TRIAL_DURATION_DAYS` | `5` | Essai si paiements activés |
| `MAX_WATCHLIST_ITEMS` | `50` | Limite watchlist |
| `MAX_PRICE_ALERTS` | `20` | Limite alertes |

### Actualités

| Variable | Description |
|----------|-------------|
| `NEWS_USE_DATABASE` | `true` — lit `news_articles` en MySQL |
| `NEWS_REFRESH_ADMIN_KEY` | Clé pour `POST /api/news/refresh` |

---

## 10. Développement local (votre Mac)

```bash
# 1. Infra
docker compose up -d mysql redis

# 2. Config
cp .env.example .env
# MYSQL_PORT=3307 dans .env

# 3. Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/init_database.py
python scripts/migrate_news_articles.py

# 4. Frontend
cd frontend && npm ci && npm run build && cd ..

# 5. API (terminal 1)
python3 app.py
# → http://127.0.0.1:5050

# 6. Worker scrape (terminal 2 — optionnel)
python3 scripts/run_scrape_worker.py
```

En dev, le frontend buildé est servi par Flask depuis `static/frontend/`.

---

## 11. Déploiement VPS — guide pas à pas

### Votre contexte typique

- Ubuntu sur VPS (4 vCPU / 8 Go)
- MySQL **déjà installé** (port 3306)
- **Pas de Redis** → à installer
- Autres apps sur le port 80 → Centrale Bourse sur **8080**
- Accès par **IP** (pas de domaine pour l’instant)

### Étape A — Prérequis système

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential \
  default-libmysqlclient-dev pkg-config nginx redis-server

curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

sudo systemctl enable redis-server
redis-cli ping   # PONG
```

### Étape B — Base MySQL

```sql
CREATE DATABASE brvm_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'centrale_bourse'@'localhost' IDENTIFIED BY 'MOT_DE_PASSE_FORT';
GRANT ALL PRIVILEGES ON brvm_agent.* TO 'centrale_bourse'@'localhost';
FLUSH PRIVILEGES;
```

### Étape C — Utilisateur système & code

```bash
sudo adduser --disabled-password --gecos "" centralebourse
sudo mkdir -p /var/www/centrale-bourse
sudo chown centralebourse:www-data /var/www/centrale-bourse
```

Transférer le code depuis votre Mac :

```bash
rsync -avz --exclude node_modules --exclude .venv --exclude .git \
  ./ user@IP_VPS:/var/www/centrale-bourse/
```

### Étape D — Installation applicative

```bash
sudo -u centralebourse -H bash -c '
  cd /var/www/centrale-bourse
  cp deploy/env.preprod.example .env
  nano .env
'
```

**Points à modifier dans `.env` :**

```env
MYSQL_PASSWORD=...
SECRET_KEY=...                    # python3 -c "import secrets; print(secrets.token_hex(32))"
CORS_ORIGINS=http://VOTRE_IP:8080
REDIS_URL=redis://127.0.0.1:6379/0
GUNICORN_BIND=127.0.0.1:5051
PAYMENTS_ENABLED=false
NEWS_USE_DATABASE=true
DISABLE_SCRAPE_SCHEDULER=true
ALLOW_LIVE_QUOTE_FETCH=false
```

Puis :

```bash
sudo -u centralebourse -H bash -c '
  cd /var/www/centrale-bourse
  bash deploy/install-vps.sh
'
```

Ou manuellement :

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/init_database.py
python scripts/migrate_user_billing.py
python scripts/migrate_watchlist_alerts.py
python scripts/migrate_news_articles.py
cd frontend && npm ci && npm run build
mkdir -p logs
```

### Étape E — Service systemd

```bash
sudo cp /var/www/centrale-bourse/deploy/centrale-bourse-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable centrale-bourse-api
sudo systemctl start centrale-bourse-api
curl -s http://127.0.0.1:5051/api/health | python3 -m json.tool
```

Logs : `journalctl -u centrale-bourse-api -f`

### Étape F — Nginx (port 8080)

```bash
sudo cp /var/www/centrale-bourse/deploy/nginx-preprod.conf.example \
  /etc/nginx/sites-available/centrale-bourse-preprod
sudo ln -sf /etc/nginx/sites-available/centrale-bourse-preprod \
  /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo ufw allow 8080/tcp
```

**Accès :** `http://IP_DU_VPS:8080/`

### Étape G — Cron (données fraîches)

```bash
sudo crontab -u centralebourse -e
```

```cron
SHELL=/bin/bash
PATH=/var/www/centrale-bourse/.venv/bin:/usr/bin:/bin
PROJECT=/var/www/centrale-bourse

0 */2 * * * cd $PROJECT && .venv/bin/python scrape_companies.py >> logs/scrape.log 2>&1
0 */4 * * 1-5 cd $PROJECT && .venv/bin/python scripts/refresh_palmares.py >> logs/palmares.log 2>&1
*/5 * * * * cd $PROJECT && .venv/bin/python scripts/warm_api_cache.py >> logs/warm.log 2>&1
```

Premier scrape manuel (recommandé juste après install) :

```bash
sudo -u centralebourse -H bash -c '
  cd /var/www/centrale-bourse && source .venv/bin/activate
  python scrape_companies.py
  python scripts/refresh_palmares.py
  python scripts/warm_api_cache.py
'
```

---

## 12. Mise à jour après modification du code

```bash
# Sur le VPS, en tant que centralebourse
cd /var/www/centrale-bourse
git pull   # ou rsync depuis le Mac

source .venv/bin/activate
pip install -r requirements.txt          # si deps changées
python scripts/migrate_news_articles.py  # si migrations nouvelles
cd frontend && npm ci && npm run build && cd ..

sudo systemctl restart centrale-bourse-api
```

> **Important :** toujours `npm run build` après changement frontend — Gunicorn sert `static/frontend/`, pas le code source React.

---

## 13. Passage en production (avec domaine)

Quand vous aurez un nom de domaine :

1. `CORS_ORIGINS=https://bourse.votredomaine.com`
2. Remplacer `nginx-preprod.conf` par `deploy/nginx-centrale-bourse.conf.example`
3. Certificat HTTPS : `sudo certbot --nginx -d bourse.votredomaine.com`
4. Pare-feu : fermer 8080 public, ouvrir 80/443

Guide détaillé : `docs/DEPLOIEMENT_VPS.md`

---

## 14. Surveillance & sauvegardes

### Checks quotidiens

```bash
curl -s http://127.0.0.1:5051/api/health
systemctl is-active centrale-bourse-api redis-server mysql nginx
tail -20 /var/www/centrale-bourse/logs/scrape.log
```

### Sauvegardes recommandées

| Quoi | Comment |
|------|---------|
| MySQL | `mysqldump brvm_agent > backup_$(date +%F).sql` (cron quotidien) |
| Fichiers `data/` | Snapshot ou rsync |
| `.env` | Copie chiffrée hors serveur |
| VPS entier | Snapshot fournisseur (OVH, etc.) |

---

## 15. Dépannage fréquent

| Symptôme | Cause probable | Solution |
|----------|----------------|----------|
| Page blanche | Frontend pas buildé | `cd frontend && npm run build` |
| Erreur CORS | `CORS_ORIGINS` incorrect | Mettre l’URL exacte (IP:port) |
| API 502 | Gunicorn arrêté | `systemctl restart centrale-bourse-api` |
| Données vides | Pas de scrape | Lancer `scrape_companies.py` + cron |
| Lent au comparer | Redis absent | Installer Redis + `warm_api_cache.py` |
| Table absente | Migration non faite | `python scripts/init_database.py` |
| Actualités vides | Table non importée | `python scripts/migrate_news_articles.py` |
| MySQL connexion refusée | Mauvais port/user | Vérifier `.env` (3306 sur VPS, pas 3307) |
| Port 8080 inaccessible | Pare-feu | `ufw allow 8080/tcp` |

### Vérifier quelle base l’app utilise

```bash
cd /var/www/centrale-bourse && source .venv/bin/activate
python3 -c "
from dotenv import load_dotenv; load_dotenv('.env')
from storage.config import get_db_engine, get_mysql_url
print(get_db_engine(), get_mysql_url().split('@')[-1])
"
```

---

## 16. État actuel du produit (mai 2026)

| Fonctionnalité | Statut |
|----------------|--------|
| Analyse marché BRVM | ✅ |
| Comparaison sectorielle | ✅ |
| Actualités en MySQL | ✅ |
| Watchlist + alertes | ✅ (pas de push/email) |
| Paiement réel | ❌ désactivé (`PAYMENTS_ENABLED=false`) |
| Parrainage UI | Masqué tant que paiements off |
| HTTPS / domaine | À faire en prod |
| Notifications alertes | Non implémenté |

---

## 17. Index des documents & fichiers

| Fichier | Sujet |
|---------|--------|
| **Ce document** | Vue d’ensemble + déploiement VPS |
| `docs/DEPLOIEMENT_PREPROD_UBUNTU.md` | Pré-prod IP:8080 (détaillé) |
| `docs/DEPLOIEMENT_VPS.md` | Production avec domaine |
| `docs/ETAPE2_WORKERS.md` | Séparation API / scrape |
| `docs/RESUME_APPLICATION_HEBERGEMENT.md` | Synthèse hébergement |
| `deploy/install-vps.sh` | Script d’installation |
| `deploy/centrale-bourse-api.service` | Service systemd |
| `deploy/nginx-preprod.conf.example` | Nginx port 8080 |
| `deploy/env.preprod.example` | Modèle `.env` VPS |
| `scripts/crontab.example` | Exemple tâches planifiées |

---

## 18. Checklist finale avant mise en ligne

- [ ] MySQL : base `brvm_agent` + utilisateur dédié
- [ ] Redis installé et `PONG`
- [ ] `.env` édité (SECRET_KEY, CORS, MySQL, Redis)
- [ ] `python scripts/init_database.py` + migrations
- [ ] `npm run build` → `static/frontend/` présent
- [ ] `systemctl start centrale-bourse-api` + `/api/health` OK
- [ ] Nginx configuré (8080 ou domaine)
- [ ] Cron scrape + palmarès + warm actif
- [ ] Premier `scrape_companies.py` exécuté
- [ ] Pare-feu : port public ouvert
- [ ] Sauvegarde MySQL planifiée

---

*Document généré pour le projet Centrale Bourse — à mettre à jour lors des évolutions majeures (paiement, domaine, workers).*
