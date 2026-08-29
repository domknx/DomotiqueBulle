# Domotique Villa Bulle — Architecture Docker

Stack domotique pour la villa (habitation principale + studio annexe), entièrement en Docker sur le Mac mini M1. Voir `CLAUDE.md` pour le contexte complet du projet.

## 1. Vue d'ensemble

```
                        Internet
                            │
                    Cloudflare Tunnel
                    (pas de port ouvert
                     sur le routeur)
                            │
                     ┌──────┴──────┐
                     │ cloudflared │
                     └──────┬──────┘
                            │  domotique_net (réseau Docker)
        ┌───────────────────┼────────────────────┐
        │                   │                     │
┌───────┴────────┐  ┌───────┴────────┐   ┌────────┴────────┐
│ Home Assistant  │  │   Prometheus    │──▶│  VictoriaMetrics │
│  (bus KNX)      │  │ (scrape + relai)│   │ (stockage long   │
└─────────────────┘  └────────────────┘   │  terme, 5 ans)   │
                                            └────────┬────────┘
                                                     │
                                              ┌──────┴──────┐
                                              │   Grafana   │
                                              └─────────────┘
```

- **Home Assistant** : cœur domotique (KNX, solaire, Tesla, futurs capteurs).
- **Prometheus** : interroge l'endpoint `/api/prometheus` de Home Assistant et relaie (`remote_write`) toutes les métriques vers VictoriaMetrics. Ne garde localement que 2 jours de données (buffer), ce n'est pas la base de stockage.
- **VictoriaMetrics** : base de séries temporelles indépendante, stockage long terme (5 ans configurés), source de vérité pour l'historique.
- **Grafana** : visualisation, branché sur VictoriaMetrics (API compatible Prometheus).
- **cloudflared** : tunnel sortant vers Cloudflare, expose Home Assistant et Grafana sur Internet sans ouvrir aucun port sur la box/le routeur et sans app cliente à installer/maintenir à jour sur chaque appareil (contrairement à Tailscale).

## 2. Structure des dossiers

```
Domotique_Claude_Docker/
├── docker-compose.yml
├── .env                      # secrets, non versionné (copier depuis .env.example)
├── .env.example
├── .gitignore
├── CLAUDE.md
├── README.md
├── prometheus/
│   ├── prometheus.yml
│   └── ha_bearer_token       # à créer manuellement, non versionné
├── grafana/
│   └── provisioning/
│       └── datasources/
│           ├── victoriametrics.yml
│           └── teslamate.yml
├── tesla/
│   └── private/
│       └── private-key.pem   # clé privée Tesla, non versionnée
├── tesla_key_nginx/
│   └── .well-known/appspecific/com.tesla.3p.public-key.pem
├── HomeAssistant_Data/       # volume HA (config.yaml, .storage, etc.) — non versionné
├── Prometheus_Data/          # volume Prometheus — non versionné
├── VictoriaMetrics_Data/     # volume VictoriaMetrics — non versionné
├── Grafana_Data/             # volume Grafana — non versionné
├── TeslaMate_DB_Data/        # volume Postgres TeslaMate — non versionné
└── TeslaMate_Mosquitto_Data/ # volume Mosquitto TeslaMate — non versionné
```

Convention respectée : chaque conteneur a son propre dossier de données `NomDuConteneur_Data`.

## 3. Déploiement initial

1. Sur le Mac mini, dans ce dossier :
   ```bash
   cp .env.example .env
   ```
   Puis éditer `.env` et renseigner `GRAFANA_ADMIN_PASSWORD` (le `CLOUDFLARE_TUNNEL_TOKEN` viendra à l'étape 5).

2. Démarrer Home Assistant, Prometheus et VictoriaMetrics dans un premier temps (Grafana et cloudflared peuvent attendre) :
   ```bash
   docker compose up -d homeassistant victoriametrics
   ```

3. Terminer l'onboarding Home Assistant sur `http://localhost:8123` (ou `http://<IP-du-Mac-mini>:8123` depuis un autre appareil du réseau local).

4. Activer l'intégration Prometheus dans Home Assistant :
   - Ajouter dans `HomeAssistant_Data/configuration.yaml` :
     ```yaml
     prometheus:
     ```
   - Créer un jeton d'accès longue durée : Profil (en bas à gauche) → Sécurité → Jetons d'accès longue durée → Créer un jeton.
   - Copier ce jeton dans un fichier `prometheus/ha_bearer_token` (juste le token, sans retour à la ligne superflu).
   - Redémarrer Home Assistant (avec confirmation, cf. règles de travail dans `CLAUDE.md`) puis démarrer Prometheus :
     ```bash
     docker compose up -d prometheus
     ```
   - Vérifier que Prometheus scrape bien HA : `http://localhost:9090/targets` (si le port 9090 est publié — sinon `docker compose logs prometheus`).

5. Démarrer Grafana :
   ```bash
   docker compose up -d grafana
   ```
   Se connecter sur `http://localhost:3000` (admin / mot de passe défini dans `.env`). La source de données VictoriaMetrics est provisionnée automatiquement.

## 4. Accès distant sécurisé — Cloudflare Tunnel

Remplace l'usage actuel de Tailscale pour l'accès à Home Assistant et Grafana : gratuit, aucun port à ouvrir, aucun client à installer/mettre à jour sur les appareils (accès via navigateur classique). Tailscale peut rester en usage secondaire (administration directe) si souhaité — les deux ne sont pas incompatibles.

### 4.1 Choix du domaine — décidé (corrigé le 23.08.2026)

Le domaine disponible est `malnoy.com` (Gandi, utilisé aussi pour les emails). La piste initiale (déléguer uniquement un sous-domaine `bulle.malnoy.com` via NS chez Gandi, sans toucher au reste) s'est révélée **impossible** : ce "subdomain setup" est réservé au plan Cloudflare Enterprise, le formulaire "Add a Site" de Cloudflare rejette toute saisie de sous-domaine.

**Décision finale : bascule complète de `malnoy.com` sur les nameservers Cloudflare** (seule option gratuite). Fait le 23.08.2026 :
1. Inventaire complet des 16 enregistrements DNS existants chez Gandi (MX, SPF, DKIM ×3, SRV email ×5, site web, plus deux enregistrements existants `domotique.bulle`/`cloud` en Tailscale — voir mémoire du projet pour le détail).
2. Domaine racine `malnoy.com` ajouté dans Cloudflare (plan Free), les 16 enregistrements recréés à l'identique (proxy désactivé partout, "DNS only") pour ne rien changer au comportement existant.
3. DNSSEC vérifié désactivé chez Gandi avant la bascule (l'activer en cours de route aurait cassé la résolution DNS du domaine entier).
4. Nameservers changés chez Gandi vers ceux fournis par Cloudflare. Zone confirmée **"Active"** côté Cloudflare le jour même. Emails testés et fonctionnels après la bascule (SPF/DKIM/MX intacts).

Le registrar (propriété du nom de domaine, facturation) reste chez Gandi — seule la gestion DNS a changé de main. `malnoy.com` étant désormais le domaine racine sur Cloudflare, les nouveaux services sont de simples sous-domaines : **`domotique.bulle.malnoy.com`** (Home Assistant) et **`grafana.bulle.malnoy.com`** (Grafana).

### 4.2 Créer le tunnel — fait le 23.08.2026

1. Compte Cloudflare (le même que pour la zone `malnoy.com`).
2. Dashboard Cloudflare → **Zero Trust** (plan **Free**, suffisant : jusqu'à 50 utilisateurs, Cloudflare Tunnel est gratuit sans limite indépendamment du plan Zero Trust) → **Networks** → **Tunnels** → **Create a tunnel** → type **Cloudflared** → nommé `domotique-bulle`.
3. Option d'installation **Docker** : token copié directement dans `.env` (`CLOUDFLARE_TUNNEL_TOKEN`) — fait.
4. Dans l'onglet **Public Hostnames** du tunnel :
   - `domotique.bulle.malnoy.com` → Service `HTTP` → `homeassistant:8123`
   - `grafana.bulle.malnoy.com` → Service `HTTP` → `grafana:3000`
5. Démarrer le conteneur (à faire lors du déploiement complet de la stack) :
   ```bash
   docker compose up -d cloudflared
   ```
6. Dans Home Assistant, ajouter le domaine externe dans `configuration.yaml` (sinon HA refuse les requêtes avec une erreur 400) :
   ```yaml
   http:
     use_x_forwarded_for: true
     trusted_proxies:
       - 172.16.0.0/12   # plage par défaut des réseaux Docker
   ```

### 4.3 Section documentation du projet — `docbulle.malnoy.com` (ajouté au jalon 2, KNX)

Sert le contenu de `docs_site/` (page d'accueil + inventaire KNX interactif régénéré par
`knx/scripts/build_html_report.py`) via un conteneur `doc-knx` (nginx) dédié, séparé du
dossier `docs/` utilisé pour les GitHub Pages publiques — cette documentation contient la
structure du bus KNX (pièces, adresses de groupe) et n'est donc pas destinée à être publique.

1. Démarrer le conteneur (inclus dans la stack, rien de spécifique à faire au-delà du
   déploiement habituel) :
   ```bash
   docker compose up -d doc-knx
   ```
2. Dashboard Cloudflare → **Zero Trust** → **Networks** → **Tunnels** → `domotique-bulle` →
   **Public Hostnames** → **Add a public hostname** :
   - Subdomain : `docbulle`
   - Domain : `malnoy.com`
   - Service : `HTTP` → `doc-knx:80`
3. **Zero Trust** → **Access** → **Applications** → **Add an application** → **Self-hosted** :
   - Domain : `docbulle.malnoy.com`
   - Policy **Allow** → Include → **Emails** → l'adresse email à autoriser
   - Session duration : selon préférence (ex. 24h)
   - À la première visite : code à 6 chiffres envoyé par email, valable 15 minutes.
4. Accès direct sur le réseau local (sans passer par le tunnel) : `http://<IP du Mac mini>:8090`.

### 4.4 Hébergement de la clé publique Tesla — `teslabulle.malnoy.com` (ajouté au jalon 4, Tesla)

Héberge le fichier exigé par Tesla pour l'enregistrement de l'app développeur
(`developer.tesla.com`), via un conteneur `tesla-key` (nginx) dédié, même modèle que
`doc-knx`. Nécessaire même si la Model S (pré-2021) ne nécessite pas la signature de
commandes (clé virtuelle) pour le contrôle de base — Tesla vérifie ce fichier lors de
l'enregistrement de l'app quel que soit le véhicule. Détails complets : §6.

1. Démarrer le conteneur :
   ```bash
   docker compose up -d tesla-key
   ```
2. Vérifier en local que le fichier est bien servi : `http://<IP du Mac mini>:8091/.well-known/appspecific/com.tesla.3p.public-key.pem`
3. Dashboard Cloudflare → **Zero Trust** → **Networks** → **Tunnels** → `domotique-bulle` →
   **Public Hostnames** → **Add a public hostname** :
   - Subdomain : `teslabulle`
   - Domain : `malnoy.com`
   - Service : `HTTP` → `tesla-key:80`
4. Accès public sans Cloudflare Access (contrairement à `docbulle.malnoy.com`) : ce fichier
   doit être accessible sans authentification pour que Tesla puisse le lire.

## 5. KNX et réseau Docker — point de vigilance

Le réseau utilisé ici (`domotique_net`, bridge Docker standard) fonctionne sans restriction si l'interface KNX est une **interface IP en mode tunneling** (connexion unicast vers une IP fixe — c'est le mode recommandé pour une installation en conteneur, y compris par la doc officielle de l'intégration KNX de Home Assistant).

Si l'interface KNX ne fonctionne qu'en **mode routage** (multicast `224.0.23.12`), le réseau bridge de Docker Desktop pour Mac ne relaiera pas correctement le trafic multicast (limitation connue de Docker Desktop, qui fait tourner les conteneurs dans une VM Linux légère, contrairement à Docker sur Linux natif). Dans ce cas il faudra revoir la configuration réseau (ex. réseau `macvlan`, ou passerelle KNX→IP dédiée) — point à trancher lors de l'inventaire des adresses/groupes KNX (prochaine étape listée dans `CLAUDE.md`).

## 6. Intégration Tesla — Model S (jalon 4)

Contrôle/automatisations dans Home Assistant (intégration officielle **Tesla Fleet**) +
historique/dashboards dans le Grafana existant via **TeslaMate** (datasource `TeslaMate`
provisionnée automatiquement, voir `grafana/provisioning/datasources/teslamate.yml`).

**Véhicule** : Model S antérieure à 2021 → ne supporte ni la signature de commandes (clé
virtuelle) ni la Fleet Telemetry (streaming temps réel). Conséquences : pas de pairage de
clé virtuelle nécessaire sur le véhicule lui-même, mais l'intégration HA interroge le
véhicule par polling régulier (empêche la mise en veille — HA met en pause le polling après
15 min d'inactivité). TeslaMate doit utiliser la Fleet API classique, pas le streaming
(désactiver "Use Fleet Telemetry" dans ses réglages après le premier login).

### 6.1 Créer l'app développeur Tesla (une seule fois, partagée HA + TeslaMate)

1. https://developer.tesla.com/request → se connecter avec le compte Tesla du propriétaire
   du véhicule.
2. Nom/description de l'app (ex. "Domotique Villa Bulle"), grant type **Authorization Code
   and Machine-to-Machine**.
3. **Allowed Origin URL(s)** : `https://teslabulle.malnoy.com/`
4. **Allowed Redirect URI(s)** :
   - `https://my.home-assistant.io/redirect/oauth` (si l'intégration "My Home Assistant" est
     activée dans HA — recommandé, le plus simple), ou
   - `https://domotiquebulle.malnoy.com/auth/external/callback` sinon.
5. **Allowed Returned URL(s)** : laisser vide.
6. Scopes : au minimum Vehicle Information + Vehicle Commands + Vehicle Location (cocher
   aussi Energy Product Information si utile plus tard pour le solaire, jalon 4 également).
7. Noter le **Client ID** et le **Client Secret** générés.
8. Renseigner `TESLA_CLIENT_ID` dans `.env`.
9. Démarrer `tesla-key` et créer le hostname Cloudflare **avant** de valider l'app côté Tesla
   (§4.4) — Tesla doit pouvoir lire le fichier `.well-known` pendant la vérification du
   domaine. La clé a déjà été générée dans `tesla/private/private-key.pem` /
   `tesla_key_nginx/.well-known/appspecific/com.tesla.3p.public-key.pem`.

### 6.2 Intégration Home Assistant — "Tesla Fleet"

Pas besoin d'ajouter les identifiants d'application séparément au préalable — l'assistant
de configuration de l'intégration les demande directement à la première étape.

1. Paramètres → Appareils et services → **Ajouter une intégration** → **Tesla Fleet**.
2. Saisir le **Client ID** et le **Client Secret** de l'app créée en §6.1 (étape sautée
   automatiquement si un identifiant est déjà enregistré).
3. Connexion/autorisation sur le compte Tesla (flux OAuth).
4. Redirection vers Home Assistant.
5. Saisie du domaine (`teslabulle.malnoy.com`) et enregistrement de la clé publique.
6. Vérifier l'apparition des entités du véhicule (charge, climatisation, verrouillage,
   position...).

### 6.3 TeslaMate — historique et dashboards Grafana

1. Compléter `.env` : `TESLAMATE_DB_PASSWORD` et `TESLAMATE_ENCRYPTION_KEY` (générer par ex.
   avec `openssl rand -base64 32`).
2. Démarrer la pile TeslaMate :
   ```bash
   docker compose up -d teslamate-db teslamate-mosquitto teslamate
   ```
3. Ouvrir `http://<IP du Mac mini>:4000`, suivre l'assistant de connexion Tesla (même app
   développeur qu'en §6.1).
4. Dans les réglages TeslaMate : **désactiver "Use Fleet Telemetry"** (non supporté par cette
   Model S) — la synchronisation se fera par interrogation régulière (polling).
5. Importer les dashboards TeslaMate dans le Grafana existant (`grafanabulle.malnoy.com`) :
   Dashboards → New → Import → coller l'URL/JSON brut d'un dashboard du dépôt
   [teslamate-org/teslamate](https://github.com/teslamate-org/teslamate/tree/main/grafana/dashboards)
   → sélectionner la datasource **TeslaMate** pour chacun.

## 7. Prochaines étapes

- Créer le dépôt GitHub (vide pour l'instant) et pousser ce premier commit.
- Choisir et exécuter l'option de domaine Cloudflare (§4.1).
- Inventaire précis des adresses/groupes KNX (export ETS) pour construire la config KNX de Home Assistant.
- Mettre en place le journal/changelog (page web accessible) — ex. GitHub Pages à partir de ce même dépôt.
- Dashboards Home Assistant pour Mac, iPad, iPhone, écran tactile.
