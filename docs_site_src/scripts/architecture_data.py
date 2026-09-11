# -*- coding: utf-8 -*-
"""Données de l'architecture — source de vérité pour le schéma graphique unique
du site (vue d'ensemble en haut du README + vue Architecture logicielle). À
mettre à jour à la main si les services ou leurs relations changent
(README.md §1 / docker-compose.yml), même logique que content.py.

Regroupement par domaine fonctionnel (pas par réseau Docker) : Home Assistant
seul au centre du domaine « Domotique », les solutions dashboard (GlassHome,
Tunet, dashboard-*) réunies dans un domaine dédié, etc. — voir
architecture_overview.py pour le rendu et le placement des domaines sur le
schéma (cadre « Mac mini », domaine KNX hors Docker)."""

CATEGORIES = [
    dict(id='domotique', title='Domotique — cœur', color='ambre',
         blurb="Home Assistant, seul : bus KNX filaire, Z-Wave, solaire, intégration Tesla Fleet."),
    dict(id='monitoring', title='Monitoring — data', color='glacier',
         blurb="Collecte, stockage long terme et visualisation des métriques domotique."),
    dict(id='documentation', title='Documentation', color='cuivre',
         blurb="Cette documentation elle-même, régénérée depuis les sources du projet."),
    dict(id='vehicule', title='Véhicule — Tesla', color='cuivre',
         blurb="Clé publique développeur et historique trajets/charges."),
    dict(id='dashboard', title='Dashboard — solutions', color='mousse',
         blurb="Les trois écrans muraux comparés : GlassHome, Tunet, et le projet sur-mesure."),
    dict(id='acces', title='Accès distant — malnoy.com', color='ambre',
         blurb="Tunnel Cloudflare — distribue six sous-domaines, Cloudflare Access en garde l'accès."),
]

SERVICES = {
    'homeassistant': dict(title='Home Assistant', sub=':8123', category='domotique',
        desc="Cœur domotique : bus KNX filaire, Z-Wave (Raspberry Pi dédié), solaire, intégration Tesla Fleet. Exposé sur domotiquebulle.malnoy.com."),
    'prometheus': dict(title='Prometheus', sub=':9090 · LAN', category='monitoring',
        desc="Scrape /api/prometheus de Home Assistant, relais remote_write vers VictoriaMetrics. Ne garde localement que 2 jours (buffer)."),
    'victoriametrics': dict(title='VictoriaMetrics', sub=':8428 · LAN', category='monitoring',
        desc="Base de séries temporelles, stockage long terme (5 ans configurés) — source de vérité pour l'historique domotique."),
    'grafana': dict(title='Grafana', sub=':3000', category='monitoring',
        desc="Visualisation — deux sources provisionnées automatiquement : VictoriaMetrics (domotique) et TeslaMate (véhicule). Exposé sur grafanabulle.malnoy.com."),
    'doc-knx': dict(title='doc-knx', sub=':8090 · nginx', category='documentation',
        desc="Cette documentation elle-même — contenu régénéré par script, jamais édité à la main. Exposé sur docbulle.malnoy.com, protégé par Cloudflare Access."),
    'tesla-key': dict(title='tesla-key', sub=':8091 · nginx', category='vehicule',
        desc="Héberge la clé publique exigée par l'app développeur Tesla. Volontairement sans authentification. Exposé sur vehiculebulle.malnoy.com."),
    'teslamate': dict(title='TeslaMate', sub=':4000 · LAN', category='vehicule',
        desc="Historique/analytique véhicule (trajets, charges, efficacité) via la Fleet API — dashboards importés dans le Grafana existant."),
    'teslamate-db': dict(title='teslamate-db', sub='Postgres', category='vehicule',
        desc="Base de données de TeslaMate."),
    'teslamate-mosquitto': dict(title='teslamate-mosquitto', sub='MQTT interne', category='vehicule',
        desc="Broker MQTT interne à TeslaMate — pas lié à la Fleet Telemetry Tesla (non supportée sur Model S pré-2021)."),
    'glasshome': dict(title='GlassHome', sub=':3123 · LAN', category='dashboard',
        desc="Un des trois essais de dashboard comparés au jalon 5, connecté à Home Assistant par jeton longue durée. LAN uniquement."),
    'tunet': dict(title='Tunet', sub=':3002 · autre réseau Docker', category='dashboard',
        desc="Dashboard mural actif au quotidien, sur un réseau Docker séparé (même Mac mini), joint via host.docker.internal. Exposé sur visubulle.malnoy.com."),
    'dashboard-proto': dict(title='dashboard-proto', sub=':8092 · nginx', category='dashboard',
        desc="Maquette statique de la nouvelle page d'accueil (jalon 5). Proxifie /api/ vers dashboard-api pour la météo réelle. Exposé sur dashboardbulle.malnoy.com."),
    'dashboard-api': dict(title='dashboard-api', sub='interne · FastAPI', category='dashboard',
        desc="Couche applicative définitive du dashboard sur-mesure — pour l'instant limitée à un endpoint météo (proxy Open-Meteo)."),
    'dashboard-web': dict(title='dashboard-web', sub='prévu · Vue 3', category='dashboard', planned=True,
        desc="Remplacera dashboard-proto une fois construit. Pas encore commencé."),
    'cloudflared': dict(title='cloudflared', sub='tunnel sortant', category='acces',
        desc="Tunnel Cloudflare — expose les services publics sur Internet sans port ouvert sur le routeur ni client à installer."),
}

# Domaine physique, hors Docker : bus KNX filaire + configuration ETS. Pas un
# service de architecture_overview.SERVICES (rendu à part, en dehors du cadre
# « Mac mini » sur le schéma) — chiffres repris de la doc KNX (/knx/).
KNX = dict(
    title='Bus KNX filaire', sub='Configuration ETS',
    stats='975 adresses · 59 fonctions · 19 pièces',
    desc="Installation physique — câblage KNX filaire + Raspberry Pi Z-Wave dédié, configurés dans ETS (logiciel du fabricant, hors Docker). Home Assistant s'y connecte en tant que passerelle.",
)

EXTERNALS = {
    'USER': 'Utilisateurs (Mac · iPad · iPhone · écran mural)',
    'TESLACLOUD': 'Tesla Fleet API (cloud Tesla)',
    'OPENMETEO': 'Open-Meteo API (externe)',
}

# (from, to, label, planned)
DEPS = [
    ('USER', 'cloudflared', 'HTTPS', False),
    ('cloudflared', 'homeassistant', 'domotiquebulle', False),
    ('cloudflared', 'grafana', 'grafanabulle', False),
    ('cloudflared', 'doc-knx', 'docbulle 🔒', False),
    ('cloudflared', 'tesla-key', 'vehiculebulle', False),
    ('cloudflared', 'tunet', 'visubulle', False),
    ('cloudflared', 'dashboard-proto', 'dashboardbulle', False),
    ('glasshome', 'homeassistant', 'jeton longue durée', False),
    ('homeassistant', 'prometheus', '/api/prometheus', False),
    ('prometheus', 'victoriametrics', 'remote_write', False),
    ('victoriametrics', 'grafana', 'datasource VictoriaMetrics', False),
    ('teslamate-db', 'grafana', 'datasource TeslaMate', False),
    ('teslamate', 'teslamate-db', None, False),
    ('teslamate', 'teslamate-mosquitto', None, False),
    ('teslamate', 'TESLACLOUD', 'Fleet API', False),
    ('homeassistant', 'TESLACLOUD', 'intégration Tesla Fleet', False),
    ('dashboard-proto', 'dashboard-api', 'proxy /api/, interne', False),
    ('dashboard-api', 'dashboard-web', 'remplacera dashboard-proto', True),
    ('dashboard-api', 'homeassistant', 'WebSocket, jeton longue durée', True),
    ('dashboard-api', 'OPENMETEO', 'proxy météo', False),
]


def deps_for(service_id):
    """Retourne (incoming, outgoing) : listes de (autre_id, label, planned, is_external)."""
    incoming, outgoing = [], []
    for f, t, label, planned in DEPS:
        if t == service_id:
            incoming.append((f, label, planned, f in EXTERNALS))
        if f == service_id:
            outgoing.append((t, label, planned, t in EXTERNALS))
    return incoming, outgoing
