# Déploiement Centrale Bourse sur un VPS (avec autres apps déjà installées)

> **Pré-prod Ubuntu, MySQL OK, pas de Redis, sans domaine :** voir le guide dédié  
> **[DEPLOIEMENT_PREPROD_UBUNTU.md](./DEPLOIEMENT_PREPROD_UBUNTU.md)** (`http://IP:8080`).

Ce guide suppose un VPS Linux (Ubuntu/Debian), **Nginx** déjà présent, et éventuellement **MySQL** / **Redis** utilisés par d’autres projets.

## Principe : ne pas perturber les apps existantes

| Ressource | Stratégie |
|-----------|-----------|
| **Port HTTP public** | Nouveau `server_name` (sous-domaine) ou nouveau site Nginx — pas le port 80 en double |
| **API Python** | Gunicorn sur **`127.0.0.1:5051`** (local uniquement) |
| **MySQL** | Nouvelle base `brvm_agent` + utilisateur dédié sur l’instance MySQL **existante** |
| **Redis** | Instance existante, **DB logique différente** (`/1`, `/2`…) — pas la même que les autres apps |
| **Frontend** | Build statique → `static/frontend/`, servi par Nginx ou Gunicorn |

---

## 1. Audit rapide sur le VPS

```bash
# Ports déjà utilisés
sudo ss -tlnp | grep -E ':80|:443|:3306|:6379|:5050|:5051'

# Nginx
sudo nginx -t
ls /etc/nginx/sites-enabled/

# MySQL / Redis
mysql --version
redis-cli ping

# Python
python3 --version
```

Notez un port libre pour l’API interne (ex. **5051** si 5050 est pris).

---

## 2. MySQL (base dédiée)

Si MySQL tourne déjà (souvent port **3306**) :

```bash
sudo mysql
```

```sql
CREATE DATABASE brvm_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'centrale_bourse'@'localhost' IDENTIFIED BY 'MOT_DE_PASSE_FORT';
GRANT ALL PRIVILEGES ON brvm_agent.* TO 'centrale_bourse'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Dans `.env` :

```env
DB_ENGINE=mysql
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=brvm_agent
MYSQL_USER=centrale_bourse
MYSQL_PASSWORD=MOT_DE_PASSE_FORT
```

> Si vous n’avez **pas** MySQL sur le VPS : `docker compose up -d mysql` **uniquement** si le port 3306 (ou 3307) est libre, ou mappez un autre port.

---

## 3. Redis (index séparé)

Si Redis existe déjà :

```bash
redis-cli ping
# PONG
```

Utilisez une **autre base logique** (0 est souvent prise) :

```env
REDIS_URL=redis://127.0.0.1:6379/2
```

> Ne lancez pas un second Redis sur 6379 si un service l’utilise déjà.

---

## 4. Installer le projet

```bash
# Utilisateur dédié (recommandé)
sudo adduser --disabled-password --gecos "" centralebourse
sudo usermod -aG www-data centralebourse

# Code (adapter : git clone ou rsync depuis votre machine)
sudo mkdir -p /var/www/centrale-bourse
sudo chown centralebourse:www-data /var/www/centrale-bourse
sudo -u centralebourse git clone VOTRE_REPO /var/www/centrale-bourse
# ou : rsync -avz --exclude node_modules --exclude .venv ./ user@vps:/var/www/centrale-bourse/

cd /var/www/centrale-bourse
```

### Environnement Python

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential \
  default-libmysqlclient-dev pkg-config

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Fichier `.env` production

```bash
cp .env.api.example .env
nano .env
```

Exemple minimal (à adapter) — voir aussi `deploy/env.production.example` :

```env
DB_ENGINE=mysql
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=brvm_agent
MYSQL_USER=centrale_bourse
MYSQL_PASSWORD=...

SECRET_KEY=generer-une-longue-chaine-aleatoire
CORS_ORIGINS=https://bourse.votredomaine.com
FLASK_DEBUG=false

REDIS_URL=redis://127.0.0.1:6379/2

DISABLE_SCRAPE_SCHEDULER=true
SCRAPE_ON_STARTUP=false
ALLOW_LIVE_QUOTE_FETCH=false

GUNICORN_BIND=127.0.0.1:5051
GUNICORN_WORKERS=4
GUNICORN_THREADS=2

PAYMENT_MOCK=false
RATE_LIMIT_ENABLED=true
```

Générer `SECRET_KEY` :

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Initialiser la base

```bash
source .venv/bin/activate
python scripts/init_database.py
python scripts/migrate_user_billing.py
python scripts/migrate_watchlist_alerts.py
```

---

## 5. Build du frontend

Sur le VPS (Node 18+) **ou** en local puis upload du dossier `static/frontend` :

```bash
cd frontend
npm ci
npm run build
cd ..
ls static/frontend/index.html
```

Le build Vite sort dans `static/frontend/` (config `vite.config.js`).

---

## 6. Service systemd (API Gunicorn)

```bash
sudo cp deploy/centrale-bourse-api.service /etc/systemd/system/
sudo nano /etc/systemd/system/centrale-bourse-api.service
# Vérifier User, WorkingDirectory, EnvironmentFile

sudo systemctl daemon-reload
sudo systemctl enable centrale-bourse-api
sudo systemctl start centrale-bourse-api
sudo systemctl status centrale-bourse-api
curl -s http://127.0.0.1:5051/api/health | python3 -m json.tool
```

---

## 7. Nginx (nouveau site, sans toucher aux autres)

Créez un **nouveau** fichier de site (ne modifiez pas les apps existantes sauf si vous ajoutez un sous-domaine) :

```bash
sudo cp deploy/nginx-centrale-bourse.conf.example /etc/nginx/sites-available/centrale-bourse
sudo nano /etc/nginx/sites-available/centrale-bourse
# Remplacer bourse.votredomaine.com et les chemins

sudo ln -s /etc/nginx/sites-available/centrale-bourse /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

TLS (Let’s Encrypt) :

```bash
sudo certbot --nginx -d bourse.votredomaine.com
```

### Schéma

```
Internet → Nginx (443) → /api/*  → 127.0.0.1:5051 (Gunicorn)
                      → /       →  static/frontend (SPA)
```

---

## 8. Tâches planifiées (cron)

Ne pas lancer le scrape dans le processus API.

```bash
sudo -u centralebourse mkdir -p /var/www/centrale-bourse/logs
sudo crontab -u centralebourse -e
```

Coller (adapter `PROJECT`) :

```cron
SHELL=/bin/bash
PATH=/var/www/centrale-bourse/.venv/bin:/usr/local/bin:/usr/bin:/bin
PROJECT=/var/www/centrale-bourse

0 */2 * * * cd $PROJECT && .venv/bin/python scrape_companies.py >> logs/scrape.log 2>&1
0 */4 * * 1-5 cd $PROJECT && .venv/bin/python scripts/refresh_palmares.py >> logs/palmares.log 2>&1
*/5 * * * * cd $PROJECT && .venv/bin/python scripts/warm_api_cache.py >> logs/warm.log 2>&1
```

---

## 9. Checklist après déploiement

- [ ] `https://bourse.votredomaine.com` affiche la landing / app React  
- [ ] `https://bourse.votredomaine.com/api/health` → `"status": "ok"`  
- [ ] Connexion / inscription sur `/profil`  
- [ ] `GET /api/home` rapide (Redis connecté)  
- [ ] Logs : `journalctl -u centrale-bourse-api -f`  
- [ ] Snapshot : activer la sauvegarde VPS + dump MySQL périodique  

---

## 10. Mise à jour (release)

```bash
cd /var/www/centrale-bourse
sudo -u centralebourse git pull
source .venv/bin/activate
pip install -r requirements.txt
cd frontend && npm ci && npm run build && cd ..
sudo systemctl restart centrale-bourse-api
```

---

## Dépannage

| Problème | Piste |
|----------|--------|
| 502 Bad Gateway | API down : `systemctl status centrale-bourse-api` |
| CORS | `CORS_ORIGINS` = URL exacte du site (https, sans slash final) |
| Redis error | `REDIS_URL`, `redis-cli -n 2 ping` |
| MySQL refused | `MYSQL_HOST`, user, firewall local |
| Page blanche | `npm run build`, `static/frontend/index.html` présent |
| Conflit port | Changer `GUNICORN_BIND` et le `proxy_pass` Nginx |

---

## Coexistence avec Docker sur le même VPS

- **Option A** : MySQL/Redis **système** (recommandé si déjà là) + app en venv.  
- **Option B** : MySQL/Redis en Docker sur ports **non standards** (`3307`, `6380`) et `.env` adapté — sans republier 3306/6379 si déjà pris.

Ne pas exposer Gunicorn sur `0.0.0.0:5051` publiquement : toujours **127.0.0.1** + Nginx devant.
