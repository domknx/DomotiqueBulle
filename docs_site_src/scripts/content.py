# -*- coding: utf-8 -*-

ARCH_SERVICES = [
    ("Home Assistant", "homeassistant", "domotiquebulle.malnoy.com", "c-ha",
     "Cœur domotique : bus KNX filaire, Z-Wave (Raspberry Pi dédié), solaire, intégration Tesla Fleet."),
    ("Prometheus", "prometheus", "LAN uniquement (9090)", "c-prom",
     "Scrape /api/prometheus de Home Assistant, relais remote_write vers VictoriaMetrics. Buffer 2 jours seulement."),
    ("VictoriaMetrics", "victoriametrics", "LAN uniquement (8428)", "c-vm",
     "Base de séries temporelles, stockage long terme (5 ans) — source de vérité pour l'historique domotique."),
    ("Grafana", "grafana", "grafanabulle.malnoy.com", "c-grafana",
     "Visualisation — deux sources provisionnées automatiquement : VictoriaMetrics (domotique) et TeslaMate (véhicule)."),
    ("doc-knx", "doc-knx", "docbulle.malnoy.com · Cloudflare Access", "c-cuivre",
     "Cette documentation elle-même — nginx, contenu régénéré par script, jamais édité à la main."),
    ("tesla-key", "tesla-key", "vehiculebulle.malnoy.com · public", "c-cuivre",
     "Héberge la clé publique exigée par Tesla pour l'app développeur. Volontairement sans authentification."),
    ("TeslaMate", "teslamate + db + mosquitto", "LAN uniquement (4000)", "c-cuivre",
     "Historique/analytique véhicule (trajets, charges, efficacité) via la Fleet API — dashboards dans le Grafana existant."),
    ("Tunet", "Tunet (réseau Docker séparé)", "visubulle.malnoy.com", "c-mousse",
     "Dashboard mural actif au quotidien, joint via host.docker.internal — laissé inchangé pendant le chantier dashboard sur-mesure."),
    ("dashboard-proto", "dashboard-proto", "dashboardbulle.malnoy.com", "c-mousse",
     "Maquette statique de la nouvelle page d'accueil (jalon 5). Proxifie /api/ vers dashboard-api pour la météo réelle."),
    ("dashboard-api", "dashboard-api", "interne uniquement", "c-mousse",
     "Couche applicative définitive du dashboard sur-mesure — pour l'instant limitée à un endpoint météo (proxy Open-Meteo)."),
    ("GlassHome", "glasshome", "LAN uniquement (3123)", "c-glacier",
     "Un des trois essais de dashboard comparés au jalon 5, connecté à HA par jeton longue durée."),
    ("cloudflared", "cloudflared", "tunnel sortant", "c-glacier",
     "Tunnel Cloudflare — expose les services publics sans port ouvert sur le routeur ni client à installer."),
]

ROADMAP = [
    {
        "title": "Jalons du projet",
        "color": "c-mousse",
        "items": [
            ("done", "Jalon 1 — Infrastructure Docker de base", "Clos le 26.08.2026 — 5 services validés en externe."),
            ("done", "Jalon 2 — Intégration KNX", "Clos le 28.08.2026 — 63 entités + 3 groupes, dashboard « Villa Bulle ». Corrections ETS restantes volontairement reportées, à la main de l'utilisateur."),
            ("wip", "Jalon 3 — Accès distant sécurisé en production", "Clôture visée vers le 11.09.2026. Cloudflare Access généralisée à domotiquebulle / grafanabulle / visubulle / dashboardbulle le 10.09.2026 — mise en œuvre côté Cloudflare en cours."),
            ("wip", "Jalon 4 — Intégrations complémentaires", "Tesla fait (29.08.2026). Solaire en pause (reprise plus tard). Sécurité/caméras : matériel pas encore choisi."),
            ("wip", "Jalon 5 — Dashboards complets", "Priorité actuelle. Écrans Accueil et Météo avancés (dashboard-api, tranche météo livrée le 09.09.2026) ; Pièces/Lumière/Température/Energie/Configuration restent à construire."),
            ("todo", "Jalon 6 — Journal / changelog publié en continu", "Pas commencé, au-delà de la page GitHub Pages des intégrations recommandées."),
        ],
    },
    {
        "title": "Dashboard sur mesure — points ouverts",
        "color": "c-glacier",
        "items": [
            ("todo", "Contenu de l'écran Extérieur", "Pas encore spécifié."),
            ("todo", "Contenu de l'écran Fonctions", "Scènes/actions prioritaires à définir."),
            ("todo", "Suggestions contextuelles + mode veille ambiant", "Souhaités tels quels ? À confirmer."),
            ("todo", "Effets Concept A/B dans le gabarit Boussole", "Parallax, respiration, panneau coulissant — intégration précise à trancher."),
            ("todo", "Devenir des anciennes catégories de nav", "Extérieur / Énergie / Tesla / Sécurité / Fonctions — fondues, gardées à part, ou autre ?"),
            ("todo", "Gestion fine des étages", "Sélecteur désormais intégré à l'écran Pièces — pas urgent."),
            ("todo", "Resynchronisation de Boussole", "Avec le gabarit T9/T10 révisé et la photo hero, une fois les points ci-dessus clarifiés."),
            ("todo", "Icônes de navigation et d'état", "Méthode Lucide déjà validée pour les pièces — à répéter pour nav/lampe/chauffage/volet."),
            ("todo", "Contenu réel de chaque écran", "Pièces, Lumière, Température, Energie, Configuration, Accueil — à spécifier et implémenter au fil de l'eau."),
        ],
    },
    {
        "title": "Bus KNX — points ouverts",
        "color": "c-ambre",
        "items": [
            ("todo", "Corrections côté ETS", "GA 1/0/61 dupliquée, Functions chauffage mal typées/incomplètes, DPT 5/5/13, 122 suggestions haute confiance, Studio non formalisé, volets Chambre Léane Est/Sud inversés. Décision de l'utilisateur : il fait évoluer ETS séparément, à son rythme."),
            ("todo", "Automatisations et scènes", "Ex. « tout éteindre », scènes jour/nuit — étape naturelle suivante côté Home Assistant, données déjà disponibles."),
        ],
    },
]
