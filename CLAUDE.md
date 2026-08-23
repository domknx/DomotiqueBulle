# Domotique Villa Bulle — Contexte du projet

Ce fichier sert de référence de contexte pour toute intervention de Claude sur ce projet. Il doit être tenu à jour au fil de l'avancement (architecture, décisions, état du système).

## 1. Objectif du projet

Concevoir, déployer, maintenir et documenter le serveur domotique de la villa familiale à Bulle (Fribourg, Suisse). La propriété comprend deux unités d'habitation distinctes :

- l'habitation principale ;
- le studio annexe.

Le système doit à terme piloter l'ensemble des équipements des deux logements depuis une infrastructure centralisée, avec accès distant sécurisé et visualisation des données historiques.

## 2. Matériel (hardware)

### 2.1 Installation KNX

Le cœur de l'installation domotique est un bus **KNX filaire**. Il gère aujourd'hui :

- l'éclairage (lampes) ;
- les prises commandées ;
- les volets roulants ;
- le chauffage.

Extensions prévues : capteurs et actionneurs de sécurité (caméras, détecteurs), et potentiellement d'autres capteurs au fil du temps.

### 2.2 Serveur

- **Mac mini M1, 16 Go de RAM.**
- Tous les services tournent en conteneurs **Docker** sur cette machine (aucune installation "nue" en dehors de Docker).

### 2.3 Autres intégrations matérielles prévues

- Installation solaire (production photovoltaïque).
- Véhicule Tesla (données/état/charge).
- Autres capteurs/actionneurs de sécurité à définir (caméras, etc.).

## 3. Logiciel (software)

### 3.1 Plateforme domotique — Home Assistant

- **Home Assistant** est le cœur logiciel de la domotique, exécuté en Docker.
- Il doit interagir avec l'ensemble des composants de la maison : KNX, installation solaire, Tesla, et futurs capteurs/actionneurs.
- Home Assistant doit être **entièrement configuré par Claude**, notamment via la gestion d'un **fichier de configuration KNX** maintenu et mis à disposition régulièrement par Claude.
- Accès depuis l'extérieur (Internet) requis, de manière sécurisée.

### 3.2 Historisation des données — VictoriaMetrics + Prometheus

- Toutes les données produites par Home Assistant doivent être dupliquées dans une **base de données indépendante** (découplée du stockage interne de Home Assistant).
- Solution retenue : **VictoriaMetrics** comme base de séries temporelles, alimentée via **Prometheus** qui expose/collecte les métriques depuis Home Assistant.
- Objectif : permettre la visualisation historique et l'accès à ces données depuis l'extérieur, indépendamment de Home Assistant.

### 3.3 Visualisation — Grafana

- **Grafana** est utilisé pour visualiser les données stockées dans VictoriaMetrics.
- Doit être accessible depuis l'extérieur (Internet).

### 3.4 Tableaux de bord Home Assistant

Plusieurs dashboards Home Assistant doivent être créés, adaptés à différents supports :

- Mac (navigateur / app) ;
- iPad ;
- iPhone ;
- écran tactile mural dédié.

## 4. Principes d'architecture et de gestion

- **Tout doit tourner en Docker.** Chaque service (Home Assistant, VictoriaMetrics, Prometheus, Grafana, reverse proxy, etc.) est un conteneur, orchestré via ce dossier de projet.
- **Versioning** : toute modification liée aux conteneurs (configuration, docker-compose, fichiers KNX, etc.) doit être **commitée sur GitHub**.
- **Documentation / journal** : chaque changement doit être documenté sous forme de **journal** (changelog), publié sur une **page web accessible**.
- **Accès externe** : Home Assistant et Grafana doivent être accessibles depuis Internet (sécurisé via Cloudflare Tunnel, voir §7).

## 5. Rôle de Claude sur ce projet

- concevoir le serveur domotique de zéro
- Concevoir et maintenir la stack Docker avec docker-compose pour l'ensemble des services.
- Configurer et maintenir Home Assistant dans son intégralité, y compris le fichier de configuration KNX, mis à jour régulièrement.
- Committer toute modification sur GitHub avec des messages clairs.
- Tenir à jour le journal de bord des modifications (page web).
- Concevoir les dashboards Home Assistant pour les différents supports (Mac, iPad, iPhone, écran tactile).

## 6. Règles de travail 
- Toujours faire une sauvegarde de config avant une modification structurelle (ha_manage_backup)
- Ne jamais redémarrer Home Assistant sans confirmation explicite
- Avant de pousser une config YAML générée, montrer un extrait (5–10 entités) pour validation avant d'appliquer à l'ensemble
- Nommage des entités : cohérent avec les noms de pièces déjà utilisés dans l'export ETS
- Éviter de dupliquer une entité déjà migrée — vérifier l'existant avant création
- Les données des container doivent toujours se trouver dans un répertoire dédié du type: ContainerName_Data (examples: HomeAssistant_Data, Grafana_Data, ...)

## 7. Architecture Docker (v1)

Fichiers créés à la racine du projet : `docker-compose.yml`, `prometheus/prometheus.yml`, `grafana/provisioning/datasources/victoriametrics.yml`, `.env.example`, `.gitignore`, `README.md`. Voir `README.md` pour le détail complet (schéma, déploiement, Cloudflare Tunnel).

Services : `homeassistant`, `prometheus`, `victoriametrics`, `grafana`, `cloudflared`, tous sur un réseau Docker dédié `domotique_net`.

**Accès distant** : Cloudflare Tunnel retenu (gratuit, aucun port ouvert sur le routeur, aucun client à installer/mettre à jour sur chaque appareil — contrairement à Tailscale, utilisé actuellement et jugé contraignant par l'utilisateur). Tailscale peut rester en usage secondaire si souhaité.

**Domaine** : `malnoy.com` (Gandi, actuellement utilisé pour les emails). Décision validée (23.08.2026) : sous-domaine dédié `bulle.malnoy.com` délégué à Cloudflare via enregistrements NS chez Gandi, pour ne pas toucher aux enregistrements email existants sur le domaine racine (voir README §4.1).

**Dépôt GitHub** : `git@github.com:domknx/DomotiqueBulle.git` (créé par l'utilisateur le 23.08.2026). Premier push effectué le 23.08.2026 — branche `main` synchronisée.

**Point de vigilance KNX/réseau** : le réseau bridge Docker standard fonctionne si l'interface KNX est en mode tunneling (unicast). Si elle n'est qu'en mode routage (multicast), Docker Desktop pour Mac ne relaie pas correctement le multicast — à trancher lors de l'inventaire KNX (ETS).

## 8. État actuel du projet

Architecture Docker v1 conçue, confirmée et poussée sur GitHub (`main` synchronisé, 4 commits). Décisions accès distant, domaine et nommage du conteneur Home Assistant toutes validées. Stack pas encore déployée sur le Mac mini (`docker compose up -d` pas encore lancé).

### Prochaines étapes

- Créer la zone `bulle.malnoy.com` sur Cloudflare, récupérer les nameservers, les déclarer chez Gandi pour l'hôte `bulle`.
- Créer le tunnel Cloudflare (Zero Trust → Tunnels) et récupérer le `CLOUDFLARE_TUNNEL_TOKEN` (README §4.2).
- Déployer la stack sur le Mac mini (`docker compose up -d`) et terminer l'onboarding Home Assistant.
- Inventaire précis des adresses/groupes KNX existants (export ETS) pour établir le premier fichier de configuration KNX.
- Mettre en place le journal/changelog (page web accessible) — piste envisagée : GitHub Pages à partir du même dépôt.
- Concevoir les dashboards Home Assistant (Mac, iPad, iPhone, écran tactile).

## 9. Historique des décisions

- 2026-08-23 — Création du fichier de contexte initial du projet.
- 2026-08-23 — Architecture Docker v1 définie : `homeassistant` + `prometheus` + `victoriametrics` + `grafana` + `cloudflared` sur réseau `domotique_net`. Accès distant : Cloudflare Tunnel (remplace Tailscale, gratuit, sans port ouvert ni client à maintenir à jour). Domaine cible : `malnoy.com` (Gandi), avec recommandation de sous-domaine dédié pour préserver les DNS email — décision finale de l'utilisateur en attente. Dépôt GitHub pas encore créé.
- 2026-08-23 — Conteneur Home Assistant temporairement renommé `ha_claude` (conflit avec un conteneur `homeassistant` déjà présent sur le Mac mini), puis remis à `homeassistant` sur demande de l'utilisateur : il gère lui-même le renommage de l'autre instance existante.
- 2026-08-23 — Décisions validées par l'utilisateur : (1) Cloudflare Tunnel confirmé comme méthode d'accès distant ; (2) sous-domaine `bulle.malnoy.com` confirmé pour le domaine ; (3) dépôt GitHub créé par l'utilisateur : `git@github.com:domknx/DomotiqueBulle.git`, remote `origin` ajouté localement ; (4) nom du conteneur Home Assistant remis à `homeassistant`.
- 2026-08-23 — Authentification SSH GitHub mise en place pour le compte `docker` du Mac mini : ancienne clé (`Key_Github_20251025`) inutilisable (passphrase indisponible, nom de fichier non standard). Nouvelle clé dédiée `id_ed25519_domotique` générée sans passphrase, ajoutée au compte GitHub `domknx`, configurée via `~/.ssh/config`. Premier `git push -u origin main` réussi — dépôt distant synchronisé.
