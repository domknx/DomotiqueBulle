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
- À la fin de chaque jalon principal (voir §10), exécuter `scripts/backup_jalon.sh "nom-du-jalon"` pour créer un point de restauration complet avant de poursuivre.
- **Toute page HTML doit être responsive** (mobile, tablette, desktop) : tester mentalement au moins un point de rupture ≤480px (iPhone) avant de livrer. Attention particulière à l'ordre des règles CSS dans la feuille de style — une règle `@media` doit toujours être placée *après* la règle de base qu'elle surcharge, sinon elle perd la bataille de spécificité/ordre sur mobile (bug vécu le 27.08.2026 : sidebar de filtres du rapport KNX qui restait en `position:sticky` plein écran et chevauchait le contenu sur iPhone, car le `@media (max-width:860px)` était placé avant la règle `.sidebar` de base).

## 7. Architecture Docker (v1)

Fichiers créés à la racine du projet : `docker-compose.yml`, `prometheus/prometheus.yml`, `grafana/provisioning/datasources/victoriametrics.yml`, `.env.example`, `.gitignore`, `README.md`. Voir `README.md` pour le détail complet (schéma, déploiement, Cloudflare Tunnel).

Services : `homeassistant`, `prometheus`, `victoriametrics`, `grafana`, `cloudflared`, tous sur un réseau Docker dédié `domotique_net`.

**Accès distant** : Cloudflare Tunnel retenu (gratuit, aucun port ouvert sur le routeur, aucun client à installer/mettre à jour sur chaque appareil — contrairement à Tailscale, utilisé actuellement et jugé contraignant par l'utilisateur). Tailscale peut rester en usage secondaire si souhaité.

**Domaine** : `malnoy.com` (registrar Gandi). La délégation d'un simple sous-domaine (`bulle.malnoy.com`) s'est révélée impossible sur le plan Cloudflare gratuit (réservé à l'Enterprise) — décision corrigée le 23.08.2026 : bascule complète de `malnoy.com` sur les nameservers Cloudflare (`colin.ns.cloudflare.com` + `sydney.ns.cloudflare.com`). Inventaire des 16 enregistrements DNS Gandi (MX, SPF, DKIM ×3, SRV email ×5, site web, et les accès existants `ha.malnoy.com`/`cloud.malnoy.com` via Tailscale) recréé et vérifié à l'identique dans Cloudflare avant bascule. Nameservers changés chez Gandi et **zone confirmée "Active" côté Cloudflare le 23.08.2026** — `malnoy.com` est maintenant géré par Cloudflare. Registrar (propriété du nom de domaine) toujours chez Gandi, seule la gestion DNS a changé de main. Le domaine racine reste sur Cloudflare (pas de sous-domaine séparé) : les services sont accessibles sur **`domotiquebulle.malnoy.com`** (Home Assistant) et **`grafanabulle.malnoy.com`** (Grafana), simples sous-domaines à un seul niveau de la zone `malnoy.com` gérée par Cloudflare — renommés le 24.08.2026 depuis `domotique.bulle.malnoy.com`/`grafana.bulle.malnoy.com` (voir incident ci-dessous et historique).

**Tunnel Cloudflare** : créé le 23.08.2026 (Zero Trust, plan Free, nommé `domotique-bulle`). Token récupéré et placé dans `.env` (`CLOUDFLARE_TUNNEL_TOKEN`, jamais commité). Hostnames publics configurés : `domotiquebulle.malnoy.com` → `homeassistant:8123`, `grafanabulle.malnoy.com` → `grafana:3000` (renommés le 24.08.2026 depuis `domotique.bulle.malnoy.com`/`grafana.bulle.malnoy.com`, non couverts par le certificat SSL gratuit — voir historique).

**Dépôt GitHub** : `git@github.com:domknx/DomotiqueBulle.git` (créé par l'utilisateur le 23.08.2026). Premier push effectué le 23.08.2026 — branche `main` synchronisée.

**Point de vigilance KNX/réseau** : le réseau bridge Docker standard fonctionne si l'interface KNX est en mode tunneling (unicast). Si elle n'est qu'en mode routage (multicast), Docker Desktop pour Mac ne relaie pas correctement le multicast — à trancher lors de l'inventaire KNX (ETS).

## 8. État actuel du projet

Stack déployée sur le Mac mini, **les 5 services tournent en continu et sont validés** (`homeassistant`, `victoriametrics`, `prometheus`, `grafana`, `cloudflared`). Onboarding Home Assistant terminé (utilisateur `fabrice`). Intégration `prometheus:` ajoutée dans `configuration.yaml`, jeton d'accès longue durée généré et stocké dans `prometheus/ha_bearer_token` (non versionné), scraping confirmé `UP`. Accès externe validé via `domotiquebulle.malnoy.com` (Home Assistant) et `grafanabulle.malnoy.com` (Grafana) — voir historique du 24.08.2026 pour le détail des bugs corrigés en route (port/montage prometheus, root_url Grafana, config réseau HA désormais via l'UI). Reste avant de clore le jalon 1 (voir §10.1) : installer HACS et le serveur Home Assistant MCP.

Incident résolu le 23–24.08.2026 : après ajout du bloc `http:`/`trusted_proxies` (nécessaire pour accepter le trafic via le futur tunnel Cloudflare), connexion à Home Assistant impossible pendant plusieurs heures, y compris après réinitialisation du mot de passe (`hass --script auth ... change_password`). Cause probable : état serveur bloqué en mémoire (les requêtes de connexion étaient systématiquement journalisées avec l'IP source `172.67.68.101`, y compris en accès direct `localhost:8123` sans aucun proxy actif), non résolu par un simple `restart` du conteneur. Résolu par un cycle complet `docker compose down` puis `up -d`. À l'occasion, `trusted_proxies` a été resserré de la plage large `172.16.0.0/12` au sous-réseau réel du réseau Docker `domotique_net` (`172.19.0.0/16`, vérifié via `docker network inspect`), par précaution avant la remise en route de `cloudflared`. Si ce blocage réapparaît après démarrage de `cloudflared`, envisager un `docker compose down && up -d` complet plutôt qu'un simple `restart`.

### Prochaines étapes

- Installer HACS et le serveur Home Assistant MCP dans Home Assistant — prérequis avant toute configuration/entité HA, KNX inclus (voir §10.1, jalon 1).
- Sauvegarde de jalon 1 (`scripts/backup_jalon.sh`) une fois HACS + MCP Server installés.
- Inventaire précis des adresses/groupes KNX existants (export ETS) pour établir le premier fichier de configuration KNX.
- Mettre en place le journal/changelog (page web accessible) — piste envisagée : GitHub Pages à partir du même dépôt.
- Concevoir les dashboards Home Assistant (Mac, iPad, iPhone, écran tactile).

## 9. Historique des décisions

- 2026-08-23 — Création du fichier de contexte initial du projet.
- 2026-08-23 — Architecture Docker v1 définie : `homeassistant` + `prometheus` + `victoriametrics` + `grafana` + `cloudflared` sur réseau `domotique_net`. Accès distant : Cloudflare Tunnel (remplace Tailscale, gratuit, sans port ouvert ni client à maintenir à jour). Domaine cible : `malnoy.com` (Gandi), avec recommandation de sous-domaine dédié pour préserver les DNS email — décision finale de l'utilisateur en attente. Dépôt GitHub pas encore créé.
- 2026-08-23 — Conteneur Home Assistant temporairement renommé `ha_claude` (conflit avec un conteneur `homeassistant` déjà présent sur le Mac mini), puis remis à `homeassistant` sur demande de l'utilisateur : il gère lui-même le renommage de l'autre instance existante.
- 2026-08-23 — Décisions validées par l'utilisateur : (1) Cloudflare Tunnel confirmé comme méthode d'accès distant ; (2) sous-domaine `bulle.malnoy.com` confirmé pour le domaine ; (3) dépôt GitHub créé par l'utilisateur : `git@github.com:domknx/DomotiqueBulle.git`, remote `origin` ajouté localement ; (4) nom du conteneur Home Assistant remis à `homeassistant`.
- 2026-08-23 — Authentification SSH GitHub mise en place pour le compte `docker` du Mac mini : ancienne clé (`Key_Github_20251025`) inutilisable (passphrase indisponible, nom de fichier non standard). Nouvelle clé dédiée `id_ed25519_domotique` générée sans passphrase, ajoutée au compte GitHub `domknx`, configurée via `~/.ssh/config`. Premier `git push -u origin main` réussi — dépôt distant synchronisé.
- 2026-08-23 — Correction de la décision domaine : la délégation d'un simple sous-domaine `bulle.malnoy.com` s'est révélée impossible gratuitement chez Cloudflare (fonctionnalité Enterprise uniquement). Bascule décidée sur le domaine racine `malnoy.com` entier. Inventaire complet des 16 enregistrements DNS Gandi établi et recréé à l'identique dans Cloudflare (dont 3 CNAME DKIM ratés par le scan automatique, ajoutés manuellement ; tous les enregistrements repassés en "DNS only"). DNSSEC activé par erreur chez Gandi puis désactivé avant la bascule (aurait cassé la résolution DNS du domaine entier). Nameservers changés chez Gandi vers `colin.ns.cloudflare.com` / `sydney.ns.cloudflare.com` — zone confirmée "Active" dans Cloudflare le jour même. Emails testés fonctionnels après bascule.
- 2026-08-23 — Tunnel Cloudflare créé (Zero Trust, plan Free, nommé `domotique-bulle`), token placé dans `.env`. Hostnames publics choisis par l'utilisateur : `domotique.bulle.malnoy.com` (Home Assistant, plutôt que la suggestion initiale `home.bulle.malnoy.com`) et `grafana.bulle.malnoy.com` (Grafana).
- 2026-08-23 — Stack déployée sur le Mac mini. Corrections apportées à `docker-compose.yml` : image VictoriaMetrics `:stable` (inexistante) fixée à `:v1.150.0`, option `--storagePath` corrigée en `--storageDataPath`. `homeassistant` et `victoriametrics` confirmés `Up`. Intégration `prometheus:` ajoutée dans `configuration.yaml`, jeton d'accès longue durée généré (`prometheus/ha_bearer_token`, non versionné).
- 2026-08-23/24 — Incident de connexion à Home Assistant après ajout du bloc `http:`/`trusted_proxies: 172.16.0.0/12` (préparation pour `cloudflared`) : connexion impossible pendant plusieurs heures malgré réinitialisation du mot de passe. Cause probable : état serveur bloqué en mémoire, indépendant des identifiants (les tentatives, même en accès direct `localhost:8123`, étaient journalisées avec une IP Cloudflare figée). Résolu par un cycle complet `docker compose down` + `up -d` (un simple `restart` n'avait pas suffi). `trusted_proxies` resserré ensuite au sous-réseau réel `172.19.0.0/16` de `domotique_net` (au lieu de `172.16.0.0/12`), sauvegarde de `configuration.yaml` faite avant modification. Mot de passe changé par l'utilisateur après résolution.
- 2026-08-24 — Accès externe via le tunnel Cloudflare validé (`domotiquebulle.malnoy.com` et `grafanabulle.malnoy.com`, confirmé en 4G). Deux bugs distincts corrigés en cours de route : (1) Grafana affichait "failed to load its application files" — `GF_SERVER_ROOT_URL` manquant dans `docker-compose.yml`, ajouté (`https://grafanabulle.malnoy.com`). (2) Home Assistant rejetait systématiquement les requêtes via le tunnel avec une erreur 400 ("HTTP integration is not set-up for reverse proxies"), **malgré** un bloc `http: use_x_forwarded_for/trusted_proxies` correct dans `configuration.yaml` et plusieurs redémarrages complets (`docker compose down && up -d`). Cause réelle, trouvée après investigation (voir recherche web) : depuis Home Assistant **2026.8.0**, ce réglage n'est plus lu depuis `configuration.yaml` (validé mais silencieusement ignoré au runtime) — il doit être configuré dans l'interface : **Paramètres > Système > Réseau > Proxy inverse**, "Faire confiance à X-Forwarded-For" activé, proxy de confiance `172.19.0.0/16`. Fait par l'utilisateur, accès externe confirmé fonctionnel immédiatement après. Le bloc `http:` obsolète a été retiré de `configuration.yaml` et remplacé par un commentaire explicatif (sauvegarde faite avant modification, conforme §6). **Point important pour la suite du projet** : toute config `http:`/réseau future doit passer par l'UI (Paramètres > Système > Réseau), pas par YAML.
- 2026-08-24 — Démarrage de `grafana` (up, datasource VictoriaMetrics provisionnée automatiquement, confirmé par l'utilisateur) puis de `cloudflared` (déjà up depuis 22h en réalité — connexion au edge Cloudflare confirmée dans les logs, 4 connexions enregistrées, routage ingress correct pour les deux hostnames). Malgré ça, aucun accès externe possible (ni Mac mini ni iPhone en 4G). Diagnostic : échec de négociation TLS confirmé (`SSLV3_ALERT_HANDSHAKE_FAILURE`). Cause : le certificat Universal SSL gratuit de Cloudflare (`*.malnoy.com`, confirmé dans Edge Certificates) ne couvre que les sous-domaines à un seul niveau — `domotique.bulle.malnoy.com`/`grafana.bulle.malnoy.com` (deux niveaux) n'étaient pas couverts. Alternative payante (Advanced Certificate Manager / Total TLS) écartée par l'utilisateur au profit du renommage en sous-domaines à un niveau, gratuit : **`domotiquebulle.malnoy.com`** et **`grafanabulle.malnoy.com`** (à reconfigurer côté Cloudflare Zero Trust — Public Hostnames du tunnel `domotique-bulle`).
- 2026-08-24 — Démarrage de `prometheus` : deux oublis corrigés dans `docker-compose.yml` (aucun des deux n'empêchait le conteneur de tourner, mais l'un cassait la vérification et l'autre le scraping) : (1) port 9090 jamais publié (`ports: - "127.0.0.1:9090:9090"`, accès local uniquement, ajouté) ; (2) fichier `prometheus/ha_bearer_token` jamais monté dans le conteneur (`volumes: - ./prometheus/ha_bearer_token:/etc/prometheus/ha_bearer_token:ro`, ajouté). Une fois le montage corrigé, le jeton existant s'est révélé invalide (401) — probablement lié au changement de mot de passe de l'incident du 23-24.08 — régénéré par l'utilisateur. Cible `home_assistant` confirmée `UP` sur `http://localhost:9090/targets`.
- 2026-08-24 — Définition des jalons principaux du projet et mise en place d'un système de sauvegarde/restauration complet (voir §10) : script `scripts/backup_jalon.sh` (tag Git + archive `.env`/`*_Data` vers `Backups/` local et le disque externe `Sauvegardes/0_Domotique/`, rétention 3 sauvegardes locales / historique complet sur le disque externe) et `scripts/backup_victoriametrics.sh` (snapshot natif hebdomadaire, indépendant des jalons, copié sur le disque externe). Ajout d'un prérequis explicite : installer HACS et le serveur Home Assistant MCP avant toute configuration HA (voir §10.1, jalon 1). Lancement d'une liste catégorisée d'intégrations/thèmes Home Assistant recommandés, publiée sur GitHub Pages et rafraîchie automatiquement tous les 3 mois (voir §10.5).

## 10. Jalons du projet et sauvegardes

### 10.1 Jalons principaux

1. ✅ **Infrastructure Docker de base opérationnelle** — CLOS et vérifié le 26.08.2026 (tag Git `jalon_jalon-1-infra-de-base_20260826_181432`, sauvegarde complète confirmée locale + disque externe). `homeassistant`, `prometheus`, `victoriametrics`, `grafana`, `cloudflared` tous démarrés en continu et validés en externe ; **HACS** installé (authentifié GitHub) et le composant **ha-mcp** (`homeassistant-ai/ha-mcp-integration`, via HACS) installé et configuré. Connexion MCP réelle testée avec succès (connecteur Claude "Home Assistant MCP" reconnecté sur la nouvelle URL webhook via le tunnel — voir mémoire projet) : Claude peut désormais interroger et configurer Home Assistant directement via les outils `mcp__Home_Assistant_Custom_MCP__*`.
2. **Intégration KNX complète** — tous les équipements des deux logements pilotables depuis Home Assistant, fichier de configuration KNX stabilisé.
3. **Accès distant sécurisé validé en production** — tunnel Cloudflare stable dans la durée (pas de régression comme l'incident du 23–24.08.2026).
4. **Intégrations complémentaires** — installation solaire, Tesla, sécurité/caméras.
5. **Dashboards complets** — Mac, iPad, iPhone, écran tactile mural.
6. **Journal/changelog publié en continu** — page web à jour (GitHub Pages).

### 10.2 Sauvegarde de jalon (point de restauration complet)

À la fin de chaque jalon validé (et avant toute modification structurelle majeure), exécuter, depuis la racine du projet sur le Mac mini :

```
./scripts/backup_jalon.sh "nom-du-jalon"
```

Ce script :
- crée un tag Git horodaté sur le commit courant (`jalon_<nom>_<horodatage>`) ;
- archive `.env` et les dossiers `*_Data` (hors `VictoriaMetrics_Data`, traité séparément — voir §10.3) dans `Backups/<date>_<nom-du-jalon>/` à la racine du projet (dossier hors Git, ignoré) ;
- copie cette archive vers le disque externe `Sauvegardes/0_Domotique/jalons/` ;
- conserve les 3 dernières sauvegardes de jalon en local (uniquement si déjà copiées sur le disque externe, par sécurité), et l'historique complet sur le disque externe.

Si le disque externe n'est pas monté au moment de l'exécution, la sauvegarde reste disponible en local et rien n'est supprimé ; le script indique la commande à relancer une fois le disque connecté.

### 10.3 Sauvegarde VictoriaMetrics (hebdomadaire, indépendante des jalons)

Les données de séries temporelles (rétention 5 ans) évoluent en continu et ne sont pas liées à l'avancement du projet. `scripts/backup_victoriametrics.sh`, exécuté chaque semaine, crée un snapshot natif VictoriaMetrics et le copie vers `Sauvegardes/0_Domotique/victoriametrics/`, puis supprime le snapshot local pour ne pas accumuler. Politique de rétention côté disque externe à définir une fois le volume réel de données observé sur quelques semaines.

### 10.4 Restauration à partir d'un jalon

1. `docker compose down`
2. Restaurer les dossiers `*_Data` et `.env` depuis l'archive choisie (`Backups/` local ou `Sauvegardes/0_Domotique/jalons/` sur le disque externe)
3. `git checkout <tag-du-jalon>` (voir `git-tag.txt` dans l'archive, ou `git tag` pour lister)
4. `docker compose up -d`
5. Vérifier chaque service (`docker compose ps`, logs, accès web sur chaque hostname)

### 10.5 Liste des intégrations et thèmes Home Assistant recommandés

Une liste catégorisée (météo, chauffage, éclairage, volets, sécurité, caméras, énergie/solaire, véhicule, multimédia, présence, thèmes/dashboards) est maintenue sur la page GitHub Pages du dépôt (`docs/integrations-recommandees.html`), et rafraîchie automatiquement tous les 3 mois par une tâche planifiée. Sert de référence avant d'installer une nouvelle intégration ou un nouveau thème via HACS.
