# Centrale Bourse — Résumé fonctionnel & hébergement

Document de synthèse pour dimensionner et gérer l’infrastructure (pré-prod / production).

---

## 1. Qu’est-ce que l’application ?

**Centrale Bourse** est une plateforme web d’**analyse et d’information** sur les sociétés cotées à la **BRVM** (Bourse régionale). Ce n’est **pas** un courtier : pas d’achat/vente d’actions.

| Couche | Technologie |
|--------|-------------|
| Frontend | React (Vite), Tailwind |
| API | Python Flask + Gunicorn |
| Base | MySQL (comptes, cours, sociétés) |
| Cache | Redis (cotations, accueil, analyses, comparer) |
| Données marché | Sikafinance, BRVM (scraping planifié) |

---

## 2. Pages et parcours utilisateur

### Site public (sans compte ou sans abonnement actif)

| Route | Contenu |
|-------|---------|
| `/bienvenue` | Landing : hero, 8 blocs fonctionnalités, tarifs, FAQ, CTA |
| `/cgu` | Conditions générales |
| `/confidentialite` | Politique de confidentialité |
| `/` | **Accueil** : palmarès, résumé marché, grille sociétés (aperçu) |
| `/profil` | Connexion / inscription |

### Plateforme (compte + accès actif : essai 5 j ou abonnement)

| Route | Contenu |
|-------|---------|
| `/` | Accueil complet (même URL, accès données selon abonnement) |
| `/societe/:ticker` | Fiche société : cours, graphiques, technique, fondamentaux, gouvernance |
| `/comparer` | Comparaison par secteur, face-à-face, classements |
| `/actualites` | Fil d’actualités BRVM |
| `/actualites/:slug` | Article détail |
| `/suivi` | Liste de suivi (watchlist) + alertes de cours |
| `/profil` | Profil, abonnement, parrainage |

### Règles d’accès (`PlatformGate`)

- Non connecté → accès limité à `/`, `/profil`, `/bienvenue` (+ pages légales) ; le reste redirige vers `/bienvenue`.
- Connecté sans abonnement/essai expiré → idem vers `/bienvenue`.
- Connecté avec essai ou abonnement actif → accès complet.

---

## 3. Fonctionnalités détaillées

### Marché & cotations

- Liste de toutes les sociétés cotées (cours, variation, secteur, volume).
- Résumé marché : indices, hausses/baisses, secteurs.
- **Palmarès** (bandeau accueil) : top hausses/baisses, rafraîchi lun–ven / snapshot week-end.
- Cotations **live** via cache Redis (pas de scrape à chaque clic visiteur en prod).

### Fiche société (`/societe/...`)

- Cours du jour, variation, OHLC, volume.
- Graphique historique (~60–120 séances, base `stock_prices`).
- **Analyse technique** : SMA 20/50, RSI, MACD, bandes, signal synthétique.
- **Fondamentaux** : CA, RN, ratios, derniers états financiers scrapés.
- Profil : secteur, gouvernance, actionnariat, liens BRVM.
- **Liste de suivi** (étoile) et **alerte de prix** (cloche, seuil haut/bas).

### Comparaison

- Matrice par **secteur** (KPI en lignes).
- **Face-à-face** : 2 sociétés du même secteur.
- **Classements sectoriels** (dividende, CAGR, marges, etc.).
- Cache serveur lourd → Redis obligatoire en prod.

### Actualités

- Liste paginée, filtres, détail par slug.
- Source : scrape / fichier `news_articles.json` + API refresh admin.

### Comptes & monétisation

| Fonction | Détail |
|----------|--------|
| Inscription / connexion | Email + mot de passe, session token |
| Essai | **5 jours** gratuits, sans carte |
| Abonnement | **2 500 FCFA / mois** (mensuel) ; affichage **annuel −20 %** sur la landing uniquement |
| Renouvellement | **Manuel** (pas de prélèvement auto) |
| Paiement | **Simulé** en dev (`PAYMENT_MOCK`) — Wave, Orange, MTN, Moov, Visa à brancher |
| Parrainage | Code parrain, **20 %** commission, solde FCFA (pas de retrait automatisé) |

### Suivi personnel

| Fonction | Limite |
|----------|--------|
| Watchlist | 50 sociétés max |
| Alertes de cours | 20 actives max ; statut « seuil atteint » ; **pas** d’email/SMS encore |

### Landing marketing

- Tarifs, FAQ, footer KS Solution, navbar sticky, CTA essai gratuit.

---

## 4. API principale (charge serveur)

| Endpoint | Usage | Cache |
|----------|-------|-------|
| `GET /api/home` | Accueil (1 appel) | Oui, ~120 s |
| `GET /api/analysis/:ticker` | Fiche société | Oui, ~30 min + overlay cours live |
| `GET /api/compare/by-sector` | Page comparer | Oui, ~300 s |
| `GET /api/news` | Actualités | Oui |
| `POST /api/auth/*` | Auth | Non |
| `GET/POST /api/user/watchlist`, `/alerts` | Suivi | Non |
| `GET /api/health` | Monitoring | Non |

Rate limiting : ~120 req/min/IP sur `/api/*` (configurable).

---

## 5. Processus en arrière-plan (hébergement)

À **ne pas** faire tourner dans le même processus que les visiteurs en production.

| Tâche | Fréquence | Ressource | Script |
|-------|-----------|-----------|--------|
| Scrape sociétés + cours | Toutes les **2 h** | CPU, réseau, I/O disque | `scrape_companies.py` |
| Palmarès Sikafinance | Lun–ven / **4 h** | Réseau | `scripts/refresh_palmares.py` |
| Pré-chauffage cache | Toutes les **5 min** | CPU léger, Redis | `scripts/warm_api_cache.py` |

Variables clés API publique :

- `ALLOW_LIVE_QUOTE_FETCH=false`
- `DISABLE_SCRAPE_SCHEDULER=true`

---

## 6. Stockage & croissance des données

| Stockage | Contenu | Croissance |
|----------|---------|------------|
| MySQL `users`, `subscriptions`, … | Comptes SaaS | Faible (10k users ≈ léger) |
| MySQL `stock_prices` | Historique cours par ticker | Moyenne (~60–120 lignes × N sociétés) |
| MySQL `companies` | Fiches JSON enrichies | Stable (~50–80 sociétés) |
| Redis | Caches API | Quelques Mo |
| Fichiers `data/` | JSON backup, snapshots palmarès, news | Modéré |

---

## 7. Comment gérer l’hébergement (votre cas)

### Pré-prod Ubuntu (sans domaine)

- **MySQL** : déjà sur le VPS → une base `brvm_agent` dédiée.
- **Redis** : à installer (`apt install redis-server`).
- **API** : Gunicorn `127.0.0.1:5051`.
- **Public** : Nginx port **8080** → `http://IP:8080` (ne pas occuper le :80 des autres apps).
- Guide : `docs/DEPLOIEMENT_PREPROD_UBUNTU.md`

### Processus minimum sur le VPS

```
┌─────────────────────────────────────────┐
│  Nginx :8080 (ou Gunicorn :5051 seul)   │
│  Gunicorn API (systemd)                 │
│  MySQL (existant)                       │
│  Redis                                  │
│  Cron : scrape + palmarès + warm        │
└─────────────────────────────────────────┘
```

### Estimation charge utilisateurs

| Phase | MAU | VPS type |
|-------|-----|----------|
| Pré-prod / test | < 100 | 4 vCPU, 8 Go (votre offre) OK |
| Lancement | 500–3 000 | Même VPS + Redis + cache + cron |
| Cible | ~10 000 | Même VPS au début si cache actif ; puis 2ᵉ instance API ou 16 Go RAM |

**Goulots probables** : scrape (CPU), analyses non cachées, comparer recalculé — d’où Redis + warm + pas de live fetch visiteur.

### Checklist exploitation

- [ ] `GET /api/health` en surveillance
- [ ] Logs : `journalctl -u centrale-bourse-api`
- [ ] Cron scrape/warm actif
- [ ] Sauvegarde MySQL + snapshot VPS
- [ ] `CORS_ORIGINS` = URL exacte (IP:port en pré-prod)
- [ ] Build frontend après chaque release : `npm run build`

---

## 8. Non implémenté (impact hébergement faible)

- Paiement réel (Mobile Money / Visa)
- Plan annuel côté API
- Notifications alertes (email / SMS / push)
- Email vérification, mot de passe oublié
- Retrait solde parrainage
- Mode sombre, multilingue
- CDN / domaine HTTPS (prévu en prod)

---

## 9. Fichiers utiles

| Document | Sujet |
|----------|--------|
| `docs/DEPLOIEMENT_PREPROD_UBUNTU.md` | IP, port 8080, Redis install |
| `docs/DEPLOIEMENT_VPS.md` | Prod avec domaine |
| `docs/ETAPE2_WORKERS.md` | Séparation API / scrape |
| `docs/SAAS_ROADMAP.md` | Scale 10k MAU |
| `deploy/*.example` | Nginx, systemd, `.env` |
