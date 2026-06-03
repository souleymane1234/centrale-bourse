# Pré-production Ubuntu — sans domaine

**Votre cas :** Ubuntu, MySQL déjà installé, **pas de Redis**, autres apps sur le VPS, accès par **adresse IP** (pas de nom de domaine).

---

## Vue d’ensemble

```
Navigateur → http://IP_DU_VPS:8080/
                ├─ /api/*  → Gunicorn 127.0.0.1:5051
                └─ /*      → fichiers React (static/frontend)

MySQL (existant, port 3306) → base brvm_agent
Redis (à installer)          → redis://127.0.0.1:6379/0
```

Le port **8080** évite de toucher au site déjà sur le port **80**.

**Option rapide (sans Nginx)** : tout sur `http://IP:5051` via Gunicorn seul — voir [§ 8](#8-option-rapide-sans-nginx).

---

## 1. Prérequis Ubuntu

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential \
  default-libmysqlclient-dev pkg-config nginx redis-server

# Node 18+ (pour build frontend)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

redis-cli ping
# PONG

mysql --version
```

---

## 2. Redis (nouvelle installation)

```bash
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

Dans `.env` :

```env
REDIS_URL=redis://127.0.0.1:6379/0
```

> Si un autre projet utilise déjà Redis sur `/0`, passez à `/1`.

---

## 3. MySQL (base dédiée sur l’instance existante)

```bash
sudo mysql
```

```sql
CREATE DATABASE brvm_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'centrale_bourse'@'localhost' IDENTIFIED BY 'VOTRE_MOT_DE_PASSE';
GRANT ALL PRIVILEGES ON brvm_agent.* TO 'centrale_bourse'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## 4. Installer l’application

```bash
sudo adduser --disabled-password --gecos "" centralebourse
sudo mkdir -p /var/www/centrale-bourse
sudo chown centralebourse:www-data /var/www/centrale-bourse

# Depuis votre Mac (exemple rsync) :
# rsync -avz --exclude node_modules --exclude .venv --exclude .git \
#   ./ user@IP_VPS:/var/www/centrale-bourse/

sudo -u centralebourse -H bash -c '
  cd /var/www/centrale-bourse
  cp deploy/env.preprod.example .env
  nano .env
'
```

**Éditez `.env`** — remplacez `IP_DU_VPS` par l’IP réelle :

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=brvm_agent
MYSQL_USER=centrale_bourse
MYSQL_PASSWORD=...

SECRET_KEY=...   # python3 -c "import secrets; print(secrets.token_hex(32))"

# Pré-prod sans domaine : IP + port Nginx
CORS_ORIGINS=http://IP_DU_VPS:8080

REDIS_URL=redis://127.0.0.1:6379/0
GUNICORN_BIND=127.0.0.1:5051
DISABLE_SCRAPE_SCHEDULER=true
ALLOW_LIVE_QUOTE_FETCH=false
FLASK_DEBUG=false
```

Puis :

```bash
sudo -u centralebourse -H bash -c '
  cd /var/www/centrale-bourse
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  python scripts/init_database.py
  python scripts/migrate_user_billing.py
  python scripts/migrate_watchlist_alerts.py
  cd frontend && npm ci && npm run build
'
```

---

## 5. Service API (systemd)

```bash
sudo cp /var/www/centrale-bourse/deploy/centrale-bourse-api.service /etc/systemd/system/
sudo nano /etc/systemd/system/centrale-bourse-api.service
# Vérifier : User=centralebourse, WorkingDirectory=/var/www/centrale-bourse

sudo systemctl daemon-reload
sudo systemctl enable centrale-bourse-api
sudo systemctl start centrale-bourse-api
curl -s http://127.0.0.1:5051/api/health
```

---

## 6. Nginx sur le port 8080 (sans domaine)

```bash
sudo cp /var/www/centrale-bourse/deploy/nginx-preprod.conf.example \
  /etc/nginx/sites-available/centrale-bourse-preprod
sudo ln -sf /etc/nginx/sites-available/centrale-bourse-preprod \
  /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Ouvrir le pare-feu si besoin :

```bash
sudo ufw allow 8080/tcp
sudo ufw status
```

**Accès :** `http://IP_DU_VPS:8080/`

---

## 7. Cron (données marché)

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

```bash
sudo -u centralebourse mkdir -p /var/www/centrale-bourse/logs
```

---

## 8. Option rapide (sans Nginx)

Si vous voulez tester tout de suite sans configurer Nginx :

Dans `.env` :

```env
GUNICORN_BIND=0.0.0.0:5051
CORS_ORIGINS=http://IP_DU_VPS:5051
```

```bash
sudo systemctl restart centrale-bourse-api
sudo ufw allow 5051/tcp
```

**Accès :** `http://IP_DU_VPS:5051/` (API + frontend servis par Gunicorn).

---

## 9. Vérifications

| Test | Commande / URL |
|------|----------------|
| API | `curl http://127.0.0.1:5051/api/health` |
| Site | `http://IP:8080/` ou `http://IP:5051/` |
| Redis | `redis-cli ping` |
| MySQL | `mysql -u centrale_bourse -p brvm_agent -e "SHOW TABLES;"` |
| Logs API | `journalctl -u centrale-bourse-api -f` |

---

## 10. Passage en production (plus tard)

Quand vous aurez un domaine :

1. `CORS_ORIGINS=https://bourse.votredomaine.com`
2. Remplacer `nginx-preprod.conf` par `nginx-centrale-bourse.conf.example` (port 80/443)
3. `certbot --nginx -d bourse.votredomaine.com`

Voir aussi `docs/DEPLOIEMENT_VPS.md`.
