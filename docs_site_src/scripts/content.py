# -*- coding: utf-8 -*-
"""Feuille de route affichée dans la vue Roadmap — recopiée à la main depuis
dashboard/CAHIER_DES_CHARGES.md §12 et le suivi de l'intégration KNX.
La liste des services Docker et de leurs dépendances (ex-ARCH_SERVICES) vit
maintenant dans architecture_data.py, source du diagramme d'architecture
interactif — voir architecture_view.py."""

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
