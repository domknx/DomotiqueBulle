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
│           └── victoriametrics.yml
├── HomeAssistant_Data/       # volume HA (config.yaml, .storage, etc.) — non versionné
├── Prometheus_Data/          # volume Prometheus — non versionné
├── VictoriaMetrics_Data/     # volume VictoriaMetrics — non versionné
└── Grafana_Data/             # volume Grafana — non versionné
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

### 4.1 Choix du domaine — décidé

Le domaine disponible est `malnoy.com` (Gandi, utilisé aujourd'hui pour les emails). **Décision validée (23.08.2026) : sous-domaine dédié `bulle.malnoy.com`.** On délègue uniquement les enregistrements NS de ce sous-domaine à Cloudflare, en créant chez Gandi des enregistrements NS pour `bulle.malnoy.com` pointant vers les deux nameservers que Cloudflare attribuera. Le domaine racine `malnoy.com` et ses enregistrements email (MX, SPF, DKIM, DMARC) restent intégralement gérés par Gandi, sans aucun risque pour la messagerie. Les services sont accessibles via `home.bulle.malnoy.com`, `grafana.bulle.malnoy.com`, etc.

Étapes chez Gandi (à faire dans l'interface web, je ne peux pas l'effectuer à ta place) : une fois le sous-domaine ajouté côté Cloudflare (§4.2 étape 1), Cloudflare indique deux nameservers (ex. `xxx.ns.cloudflare.com`) — les déclarer chez Gandi comme enregistrements NS pour l'hôte `bulle` (pas sur le domaine racine).

### 4.2 Créer le tunnel

1. Créer un compte Cloudflare gratuit si besoin, ajouter le site `bulle.malnoy.com` (Cloudflare traite un sous-domaine ajouté ainsi comme une zone à part entière ; il fournira ses propres nameservers à déclarer chez Gandi, cf. §4.1).
2. Dashboard Cloudflare → Zero Trust → Networks → Tunnels → **Create a tunnel** → type **Cloudflared** → nommer le tunnel (ex. `domotique-bulle`).
3. Choisir l'option d'installation **Docker** : Cloudflare affiche une commande contenant un token — copier uniquement ce token dans `.env` (`CLOUDFLARE_TUNNEL_TOKEN`).
4. Dans l'onglet **Public Hostnames** du tunnel, ajouter :
   - `home.bulle.malnoy.com` → Service `HTTP` → `homeassistant:8123`
   - `grafana.bulle.malnoy.com` → Service `HTTP` → `grafana:3000`
5. Démarrer le conteneur :
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

## 5. KNX et réseau Docker — point de vigilance

Le réseau utilisé ici (`domotique_net`, bridge Docker standard) fonctionne sans restriction si l'interface KNX est une **interface IP en mode tunneling** (connexion unicast vers une IP fixe — c'est le mode recommandé pour une installation en conteneur, y compris par la doc officielle de l'intégration KNX de Home Assistant).

Si l'interface KNX ne fonctionne qu'en **mode routage** (multicast `224.0.23.12`), le réseau bridge de Docker Desktop pour Mac ne relaiera pas correctement le trafic multicast (limitation connue de Docker Desktop, qui fait tourner les conteneurs dans une VM Linux légère, contrairement à Docker sur Linux natif). Dans ce cas il faudra revoir la configuration réseau (ex. réseau `macvlan`, ou passerelle KNX→IP dédiée) — point à trancher lors de l'inventaire des adresses/groupes KNX (prochaine étape listée dans `CLAUDE.md`).

## 6. Prochaines étapes

- Créer le dépôt GitHub (vide pour l'instant) et pousser ce premier commit.
- Choisir et exécuter l'option de domaine Cloudflare (§4.1).
- Inventaire précis des adresses/groupes KNX (export ETS) pour construire la config KNX de Home Assistant.
- Mettre en place le journal/changelog (page web accessible) — ex. GitHub Pages à partir de ce même dépôt.
- Dashboards Home Assistant pour Mac, iPad, iPhone, écran tactile.
