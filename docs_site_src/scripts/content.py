# -*- coding: utf-8 -*-
"""Feuille de route affichée dans la vue Roadmap — recopiée à la main depuis
dashboard/CAHIER_DES_CHARGES.md §12 et le suivi de l'intégration KNX.
La liste des services Docker et de leurs dépendances (ex-ARCH_SERVICES) vit
maintenant dans architecture_data.py, source du schéma d'architecture
unique — voir architecture_overview.py.

Depuis le 12.09.2026, ce fichier porte aussi le contenu de la vue Énergie
(ENERGIE_SECTIONS / ENERGIE_GALLERY_INTRO / ENERGIE_GALLERY / ENERGIE_TODO),
recopié à la main depuis la mémoire projet custom_dashboard_energie_screen.md
— à tenir à jour de la même façon que le reste de ce fichier à chaque
évolution notable de l'écran Énergie du dashboard."""

ROADMAP = [
    {
        "title": "Jalons du projet",
        "color": "c-mousse",
        "items": [
            ("done", "Jalon 1 — Infrastructure Docker de base", "Clos le 26.08.2026 — 5 services validés en externe."),
            ("done", "Jalon 2 — Intégration KNX", "Clos le 28.08.2026 — 63 entités + 3 groupes, dashboard « Villa Bulle ». Corrections ETS restantes volontairement reportées, à la main de l'utilisateur."),
            ("wip", "Jalon 3 — Accès distant sécurisé en production", "Clôture visée vers le 11.09.2026. Cloudflare Access généralisée à domotiquebulle / grafanabulle / visubulle / dashboardbulle le 10.09.2026 — mise en œuvre côté Cloudflare en cours."),
            ("wip", "Jalon 4 — Intégrations complémentaires", "Tesla fait (29.08.2026). Solaire : intégration myenergi installée comme contournement temporaire (12.09.2026, voir écran Énergie) ; onduleur Huawei (SUN2000 + batterie LUNA2000) hors ligne, à reconnecter pour les données réelles. Sécurité/caméras : comparatif Reolink/UniFi Protect/Tapo fait, matériel pas encore choisi."),
            ("wip", "Jalon 5 — Dashboards complets", "Priorité actuelle. Écrans Accueil et Météo avancés (dashboard-api, tranche météo livrée le 09.09.2026) ; écran Énergie livré le 12.09.2026 et enrichi le 13.09.2026 (bilan réseau réel, valeurs sur les lignes de flux, tooltip multi-séries — voir tuile Énergie) ; écran Température livré le 22.09.2026 (7 thermostats KNX, cadran « Embrasement », encore en lecture seule — voir tuile Température). Pièces/Lumière/Configuration restent à construire."),
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
            ("todo", "Contenu réel de chaque écran", "Pièces, Lumière, Configuration — à spécifier et implémenter au fil de l'eau (Accueil, Énergie et Température déjà livrés)."),
        ],
    },
    {
        "title": "Bus KNX — points ouverts",
        "color": "c-ambre",
        "items": [
            ("todo", "Corrections côté ETS", "GA 1/0/61 dupliquée, Functions chauffage mal typées/incomplètes, DPT 5/5/13, 122 suggestions haute confiance, Studio non formalisé, volets Chambre Léane Est/Sud inversés. Décision de l'utilisateur : il fait évoluer ETS séparément, à son rythme."),
            ("todo", "Automatisations et scènes", "Ex. « tout éteindre », scènes jour/nuit — étape naturelle suivante côté Home Assistant, données déjà disponibles."),
        ],
    },
]

# ---------------------------------------------------------------------------
# Vue Énergie — recopiée depuis la mémoire projet custom_dashboard_energie_screen.md
# ---------------------------------------------------------------------------

ENERGIE_SECTIONS = [
    {
        "heading": "Une intégration temporaire, en attendant l'installation réelle",
        "paragraphs": [
            "L'installation solaire de la villa (onduleur Huawei SUN2000 et batterie LUNA2000, supervisés via FusionSolar) est actuellement hors ligne : le boîtier de communication qui la relie au réseau est déconnecté. En attendant sa reconnexion, l'écran Énergie s'appuie sur l'intégration <strong>myenergi</strong> (hub domestique et borne de recharge Zappi), qui donne un accès indirect à la consommation du foyer et aux échanges avec le réseau, complétée par l'intégration <strong>Tesla Fleet</strong> pour le véhicule.",
        ],
    },
    {
        "heading": "Diagramme de flux — pulsation fluide",
        "paragraphs": [
            "Trois styles d'animation ont été comparés côte à côte (traits pointillés animés, particules en chapelet, pulsation fluide) sur trois scénarios réalistes — jour, soir, nuit — avant de retenir la <strong>pulsation fluide</strong> : un halo lumineux à traîne dégressive qui glisse le long de chaque flux, d'autant plus rapide que la puissance échangée est élevée, et dont le sens s'inverse selon que la maison importe ou exporte de l'électricité.",
            "Côté implémentation : une seule boucle d'animation (<code>requestAnimationFrame</code>), positionnement le long de la courbe via <code>path.getPointAtLength()</code> — volontairement sans SMIL ni <code>offset-path</code>, pour rester fidèle à la convention du dashboard (aucune librairie graphique externe, tout en SVG/JS natif).",
        ],
    },
    {
        "heading": "Ce qui est réel, ce qui reste estimé",
        "paragraphs": [
            "Trois des quatre flux affichés s'appuient sur des relevés réels : la consommation du foyer et les échanges avec le réseau viennent de myenergi, le véhicule de Tesla Fleet et du statut de la borne Zappi. La production solaire, elle, est <strong>approximée</strong> depuis le 12.09.2026 : en l'absence du capteur de génération dédié (resté bloqué à 0&nbsp;W, probablement une pince ampèremétrique mal assignée côté myenergi), toute puissance repartie vers le réseau est considérée comme de la production solaire — l'export cumulé du jour vient compléter cette estimation instantanée. Cette approximation ignore l'autoconsommation directe (produite et consommée sur place, invisible côté compteur réseau) : la valeur peut donc apparaître nulle en pleine production si tout est autoconsommé sur le moment.",
            "Seule la batterie domestique reste entièrement simulée : aucun capteur, réel ou approché, n'existe pour elle avant la reconnexion de la batterie Huawei LUNA2000. Les deux graphiques complémentaires — historique de consommation par période et répartition de la consommation par source — restent également des données simulées, faute d'un historique réel suffisant pour l'instant.",
        ],
    },
    {
        "heading": "Quatre premières pistes déjà mises en œuvre (13.09.2026)",
        "paragraphs": [
            "Quatre des pistes retenues plus bas ont été implémentées le lendemain de cette recherche comparative, directement avec les données myenergi déjà disponibles. La carte « Répartition de la consommation » (100&nbsp;% simulée jusque-là) devient un <strong>bilan réseau du jour</strong>&nbsp;: une barre segmentée export/import et trois totaux réels — exportée, importée, et autoconsommée pour la recharge du véhicule ou le chauffage. Ce dernier chiffre mérite une précision&nbsp;: le capteur myenergi correspondant (<code>green_energy_today</code>) ne mesure <strong>que</strong> l'énergie verte utilisée pour la recharge VE et le chauffage, pas l'autoconsommation solaire de toute la maison — faute d'un capteur de génération fiable, cette dernière reste impossible à calculer pour l'instant.",
            "Le diagramme de flux affiche désormais la puissance directement <strong>sur chaque ligne</strong>, pas seulement à ses extrémités — plus lisible à distance sur l'écran mural. Le graphique de consommation trace en plus une seconde courbe (production solaire, toujours simulée) et sa bulle de survol détaille désormais plusieurs séries et une part solaire dérivée, sur le modèle du dashboard « Origin » cité ci-dessous.",
        ],
    },
]

ENERGIE_GALLERY_INTRO = (
    "Cinq dashboards énergie grand public ont été passés en revue pour identifier d'autres "
    "idées à reprendre, au-delà du diagramme de flux déjà tranché ci-dessus."
)

# (fichier dans docs_site/assets/, titre, légende)
ENERGIE_GALLERY = [
    ("energie-inspi-mobile-overview.jpg", "Appli mobile de supervision solaire",
     "Diagramme isométrique solaire / batterie / réseau / maison, avec les kW inscrits "
     "directement sur les lignes de flux plutôt que seulement dans les pastilles — lisible "
     "d'un coup d'œil, y compris à distance sur un écran mural."),
    ("energie-inspi-solarpulse.jpg", "SolarPulse",
     "Graphe de production avec une annotation de pic toujours visible (pas seulement au "
     "survol), et un cluster de jauges de santé — disponibilité système, rendement onduleur, "
     "santé batterie."),
    ("energie-inspi-solanist.jpg", "Solanist",
     "Trio de KPI « Yield / Exported / Selfuse » et barre de répartition horizontale "
     "segmentée — transposable presque tel quel avec les données myenergi déjà disponibles "
     "(consommation, export du jour, autoconsommation approchée)."),
    ("energie-inspi-unit-monitoring.jpg", "Unit Monitoring (supervision de flotte)",
     "Pensé pour plusieurs maisons, donc peu transposable tel quel, mais son fil d'activité "
     "et d'alertes (pic de production, batterie pleine, rendement sous les attentes) est une "
     "bonne piste pour signaler automatiquement l'anomalie myenergi plutôt que de la garder "
     "seulement en note."),
    ("energie-inspi-origin.jpg", "Origin",
     "Le plus proche structurellement du diagramme déjà construit (4 tuiles autour d'un hub "
     "central). À en retenir surtout : une tooltip multi-séries enrichie sur le graphe de "
     "puissance — date, heure, plusieurs séries et métriques dérivées dans une seule bulle."),
]

ENERGIE_TODO = [
    ("todo", "Reconnecter l'onduleur Huawei",
     "Boîtier de communication actuellement hors ligne — une fois rebranché, installer "
     "l'intégration locale huawei_solar (Modbus) pour remplacer l'approximation myenergi par "
     "une vraie mesure de production et brancher la batterie LUNA2000."),
    ("todo", "Passer du relevé figé au flux live",
     "Les valeurs réelles affichées sont pour l'instant un instantané pris en lisant "
     "directement la base recorder de Home Assistant — à brancher sur un vrai flux (API ou "
     "websocket) une fois le connecteur MCP Home Assistant dédié de nouveau disponible."),
    ("todo", "Remplacer les graphiques simulés par de vrais historiques",
     "Consommation par période et répartition par source, une fois assez de profondeur "
     "d'historique disponible côté recorder Home Assistant ou côté Huawei."),
    ("todo", "Corriger l'anomalie de pince ampèremétrique myenergi",
     "Génération solaire mesurée à 0 W malgré un export réseau significatif — probable pince "
     "mal assignée, à vérifier côté câblage ou application myenergi."),
    ("done", "Bilan réseau du jour, valeurs sur les lignes, tooltip multi-séries",
     "Quatre pistes de la recherche comparative implémentées le 13.09.2026 — voir le "
     "paragraphe dédié plus haut."),
    ("todo", "Pistes restantes de la recherche comparative",
     "Cluster de jauges de santé (disponibilité système, rendement, batterie), fil "
     "d'alertes/anomalies automatique, annotation de pic toujours visible — dépendent de "
     "diagnostics pas encore disponibles (Huawei) ou d'une vraie logique de détection."),
]

# ---------------------------------------------------------------------------
# Vue Inspirations — trace des images fournies par l'utilisateur au fil des
# discussions sur le dashboard sur mesure, avec le commentaire fait au moment
# où chaque image a été montrée. Recopié à la main depuis custom_dashboard.md
# et custom_dashboard_10092026_meteo_graphes.md (mémoire projet) et CLAUDE.md
# §9 (historique des décisions) — même principe que ENERGIE_* ci-dessus :
# à compléter manuellement quand une nouvelle image de référence est fournie.
#
# Note d'exhaustivité : deux références mentionnées dans l'historique n'ont
# pas d'image ici — l'infographie "swimlanes" et la maison-à-icônes du
# 11.09.2026 (données en conversation, jamais enregistrées dans la
# bibliothèque du projet), et la comparaison de styles de mini-graphes de
# température du 10.09.2026 (note de mémoire perdue avant d'avoir pu être
# recopiée ici). Elles restent décrites en texte seul.
# ---------------------------------------------------------------------------

INSPI_INTRO = (
    "Depuis fin août 2026, plusieurs discussions sur le dashboard mural sur mesure ont démarré "
    "par des images envoyées en exemple — une esthétique à suivre, un détail à reprendre, une "
    "mauvaise idée à corriger. Cette page en garde la trace, avec le commentaire fait au moment "
    "où chaque image a été montrée, sur le même principe que la recherche comparative de la "
    "<a href=\"#energie\" onclick=\"showView('energie');return false;\">vue Énergie</a>."
)

INSPI_GROUPS = [
    {
        "date": "31.08.2026",
        "heading": "Premiers repères de style, avant la moindre ligne de code",
        "paragraphs": [
            "Dix images ont servi de planche d'inspiration pour lancer le projet : styles de "
            "dashboard à retenir ou à écarter, et surtout le <strong>format physique</strong> "
            "de l'écran — un panneau tactile mural fixe, en paysage, et non un mock de "
            "téléphone comme un premier réflexe l'avait suggéré (correction explicite de "
            "l'utilisateur).",
            "\"Sellution\" (photo réelle + verre dépoli) a été désignée <strong>préférée</strong> "
            "d'emblée (\"j'aime beaucoup\") et reste la référence la plus citée depuis. Les "
            "deux cartes météo animées du même lot ont été mises de côté ce jour-là pour "
            "resservir plus tard, lors de la construction de l'écran Météo (voir plus bas).",
        ],
        "gallery": [
            ("inspi-dash-sellution.jpg", "« Sellution » — préférée",
             "\"J'aime beaucoup\" : photo réelle du salon en fond, panneaux en verre dépoli "
             "par-dessus. Référence la plus citée du projet, reprise pour le fond photo + "
             "cartes translucides de l'écran d'accueil."),
            ("inspi-dash-multicolonne.jpg", "Dashboard desktop multi-colonnes",
             "Trois colonnes — calendrier/Spotify/alarme, pièces, climat — retenue comme "
             "exemple de dashboard \"desktop multi-colonnes\"."),
            ("inspi-dash-grec.jpg", "Dashboard HA (grec)",
             "Grille de tuiles par pièce en grec (Καθιστικό, Κουζίνα, Κρεβατοκάμαρα...), "
             "dégradé propre par pièce et dock de scènes flottant en bas d'écran."),
            ("inspi-dash-fonction.jpg", "Panneau tactile mural, groupé par fonction",
             "Un des deux \"bons référents\" pour la forme physique de l'écran (panneau fixe "
             "sur pied, pas un téléphone) : tuiles sobres groupées par fonction, icône "
             "colorée seulement quand elle est active."),
            ("inspi-dash-ambiance.jpg", "Ambiance sombre, glow orbital",
             "Dashboard sombre avec halo lumineux diffus en arrière-plan — exemple retenu "
             "pour l'ambiance générale plutôt que pour un composant précis."),
            ("inspi-thermostat-cadran.jpg", "Thermostat circulaire à dégradé",
             "Cadran circulaire dont le dégradé de couleur suit la température réglée — "
             "exemple du style de thermostat à viser, repris depuis dans plusieurs prototypes "
             "(Boussole, Bulle Console)."),
        ],
    },
    {
        "date": "01.09.2026",
        "heading": "Chauffage au sol : la piste de la braise",
        "paragraphs": [
            "L'effet de chauffage au sol de Chambre Léane a connu trois itérations avant de se "
            "stabiliser : un serpentin SVG techniquement propre mais rejeté (\"ça ne va pas\"), "
            "puis des flaques de chaleur multiples inspirées d'un rendu 3D envoyé par "
            "l'utilisateur (une pièce vide montrant des bandes de chaleur orange vif sur le "
            "parquet) — jugées finalement moins bonnes que la répartition d'origine "
            "(\"la répartition de la chaleur dans le sol était mieux\").",
            "La version retenue revient à un glow unique et large, mais <strong>animé en "
            "continu</strong> pour donner l'impression d'une braise qui s'intensifie puis "
            "s'éteint. Les deux captures ci-dessous — une carte de thermostat qui s'embrase "
            "en ambre quand le chauffage est actif, et s'éteint complètement sinon — sont la "
            "référence directe de cette animation (<code>@keyframes heat-ember</code>).",
        ],
        "gallery": [
            ("inspi-chauffage-braise-on.jpg", "Chauffage actif",
             "La carte s'embrase d'un dégradé ambre/rouge façon braise — base de l'animation "
             "heat-ember retenue pour le glow au sol."),
            ("inspi-chauffage-braise-off.jpg", "Chauffage coupé",
             "Même carte entièrement sombre à l'arrêt — sert de référence pour l'état "
             "\"éteint\" de l'effet."),
        ],
    },
    {
        "date": "06.09.2026",
        "heading": "Style « Liquid Glass » pour les sketches du cahier des charges",
        "paragraphs": [
            "Pour présenter les sketches de structure (accueil, pièce...), demande explicite de "
            "reprendre ce kit d'interface « Liquid Glass » — panneaux et pastilles translucides "
            "à reflet, sur un fond dégradé gris — avec une convention de lecture précise : un "
            "élément affichant du texte ou du contenu réel est une exigence <strong>déjà "
            "décidée</strong> ; un emplacement en verre vide à bordure pointillée est un espace "
            "réservé <strong>pas encore décidé</strong>.",
            "<code>gen_diagrams.py</code> a été réécrit en conséquence, avec un helper "
            "<code>SVG.glass()</code> reproduisant ce dégradé blanc translucide, le reflet du "
            "haut et l'ombre portée, bordure pleine ou pointillée selon l'état de décision.",
        ],
        "gallery": [
            ("inspi-liquidglass-clair.jpg", "Liquid Glass Interface — clair",
             "Panneaux, pastilles, curseurs et barre de recherche en verre translucide sur "
             "fond dégradé gris clair — kit de référence envoyé tel quel."),
            ("inspi-liquidglass-sombre.jpg", "Liquid Glass Interface — sombre",
             "Même kit sur fond sombre : a confirmé que l'effet devait fonctionner dans les "
             "deux thèmes avant d'écrire le helper CSS/SVG."),
            ("inspi-liquidglass-fond.jpg", "Fond dégradé gris",
             "Le dégradé bleu-gris utilisé comme arrière-plan des sketches \"Liquid Glass\", "
             "repris directement du fond du kit de référence."),
        ],
    },
    {
        "date": "06.09.2026",
        "heading": "Quatre photos façade/jardin, et le choix de la photo hero",
        "paragraphs": [
            "Quatre photos réelles de l'extérieur de la villa ont été envoyées le même jour : "
            "façade côté jardin sous deux angles, jardin/pergola, façade entrée/garage — "
            "rangées dans la nouvelle bibliothèque de médias du projet.",
            "Question posée en retour (deux volets) : laquelle utiliser comme photo principale "
            "de l'écran d'accueil, et ces quatre photos remplacent-elles l'ancienne photo "
            "unique \"Maison\" du 31.08&nbsp;? Réponse : <strong>la façade jardin, angle "
            "rapproché</strong> (ci-dessous, encadrée), et oui — elle fait référence pour "
            "l'accueil depuis.",
        ],
        "gallery": [
            ("inspi-facade-jardin-1.jpg", "Façade jardin — angle 1", "Une des deux prises côté jardin."),
            ("inspi-facade-jardin-2.jpg", "Façade jardin — angle 2 (retenue)",
             "Choisie comme photo hero de l'écran d'accueil — angle rapproché, réponse à la "
             "question posée le jour même."),
            ("inspi-facade-pergola.jpg", "Jardin & pergola", "Vue du jardin côté pergola."),
            ("inspi-facade-entree.jpg", "Façade entrée / garage", "Vue de la façade côté entrée et garage."),
        ],
    },
    {
        "date": "06.09.2026",
        "heading": "Un malentendu bienvenu : les widgets météo allemands",
        "paragraphs": [
            "Un fichier <code>set icones maison 1.jpg</code>, déposé le même jour dans "
            "<code>assets/icons/</code>, s'est révélé à l'ouverture être des maquettes de "
            "widgets météo <strong>en allemand</strong> (ciel nocturne, lune, pluie, neige) — "
            "et non des icônes de pièces comme son nom le laissait penser. Gardé de côté "
            "comme piste pour l'écran Météo plutôt qu'écarté, à clarifier avec l'utilisateur.",
        ],
        "gallery": [
            ("inspi-meteo-widgets-allemand.jpg", "Widgets météo (découverte, pas des icônes)",
             "\"Wolkig\" (nuageux), \"Schnee\" (neige), \"Regen\" (pluie), \"Klar\" (clair) — "
             "maquettes de cartes météo nocturnes, pas le jeu d'icônes de pièces attendu."),
        ],
    },
    {
        "date": "07.09.2026",
        "heading": "Écran Météo : les deux images qui ont tout lancé",
        "paragraphs": [
            "Détaillé directement à partir de ces deux images, citées telles quelles dans le "
            "cahier des charges (§A2) : fond de carte animé selon la condition du moment "
            "(dégradé ciel/nuit/pluie/neige/orage), température du jour en gros caractères, "
            "bloc secondaire min/max/humidité/vent, et rangée des prochains jours en dessous — "
            "repris presque à l'identique dans l'écran Météo dédié comme dans le bloc météo de "
            "l'accueil.",
        ],
        "gallery": [
            ("inspi-meteo-1.jpg", "Référence météo 1", "Carte météo animée, condition + prévision multi-jours."),
            ("inspi-meteo-2.jpg", "Référence météo 2", "Deuxième variante du même principe de carte."),
        ],
    },
    {
        "date": "09.09.2026",
        "heading": "Page Accueil : « proche du style GlassHome »",
        "paragraphs": [
            "Pour le bloc météo du jour et, à côté, le bloc de consommation d'énergie de "
            "l'écran d'accueil, la demande était explicitement de rester <strong>\"proche du "
            "style GlassHome\"</strong> — illustrée par deux images : des panneaux de verre "
            "dépoli posés sur une vraie photo de pièce floutée, et un dashboard aux cartes de "
            "verre colorées organisé par onglets de pièce.",
        ],
        "gallery": [
            ("inspi-accueil-glasshome-1.jpg", "GlassHome — verre sur photo réelle",
             "Cartes translucides (météo, température, éclairage) posées sur une photo de "
             "salon floutée — même famille visuelle que \"Sellution\"."),
            ("inspi-accueil-glasshome-2.jpg", "GlassHome — cartes colorées par onglet",
             "Onglets de pièce en bas d'écran, cartes en verre coloré (humidité, "
             "consommation, éclairage, thermostat) — direction \"GlassHome\" pour les blocs "
             "météo et énergie de l'accueil."),
        ],
    },
    {
        "date": "11.09.2026",
        "heading": "Deux références citées en conversation, sans image conservée",
        "paragraphs": [
            "Deux décisions du même jour se sont appuyées sur des images envoyées directement "
            "dans la discussion, jamais enregistrées dans la bibliothèque du projet — donc "
            "sans capture à montrer ici, seulement leur trace :",
            "— Une <strong>infographie de référence</strong> organisée en \"swimlanes\" par "
            "domaine a motivé l'abandon du schéma d'architecture à trois niveaux navigables au "
            "profit de l'infographie statique actuelle, regroupée par domaine fonctionnel "
            "(Domotique, Monitoring, Documentation, Dashboard, Véhicule, Accès distant) à "
            "l'intérieur d'un grand cadre \"Mac mini\", le bus KNX filaire restant hors de ce "
            "cadre (installation physique, pas un service Docker).",
            "— Une image de référence montrant une <strong>maison entourée d'icônes reliées "
            "par des traits</strong> a inspiré le remplacement des trois nœuds génériques du "
            "bus KNX, sur l'illustration de la page d'accueil de ce site, par des bulles "
            "d'icônes connectées (stores, prises électriques, véhicule) — redessinées en SVG "
            "vectoriel dans le style déjà en place, faute d'outil de génération d'image "
            "disponible dans cette session.",
        ],
        "gallery": [],
    },
    {
        "date": "10.09.2026",
        "heading": "Mini-graphes de température : quatre styles comparés (note perdue)",
        "paragraphs": [
            "Une comparaison à quatre styles de mini-graphes de température a bien eu lieu ce "
            "jour-là, tranchée en faveur d'un réglage \"GlassHome / Liquid Glass\" (Liquid "
            "Glass par défaut) appliqué à toutes les cartes de l'accueil — mais le détail des "
            "quatre styles comparés et le commentaire fait à l'époque ont été perdus avant de "
            "pouvoir être recopiés ici. Section gardée pour mémoire plutôt que supprimée.",
        ],
        "gallery": [],
    },
]

# ---------------------------------------------------------------------------
# Vue Température (ajoutée le 24.09.2026) — recopiée à la main depuis la
# mémoire projet custom_dashboard_temperature_screen.md et le cahier des
# charges (§8/§9), même principe que la vue Énergie. Captures prises le
# 24.09.2026 sur la v55 du dashboard (Playwright, 2560×1440), servies en
# assets statiques docs_site/assets/temp-*.jpg.
# ---------------------------------------------------------------------------

TEMP_SECTIONS = [
    {
        "heading": "Une rangée par étage, un cadran par pièce",
        "paragraphs": [
            "L'écran Température du dashboard mural présente toute la maison sur une grille de "
            "<strong>trois rangées de cinq cadrans</strong> — une rangée par étage : Sous-sol / "
            "Studio, Rez-de-chaussée, Étage. Sept emplacements correspondent à un vrai thermostat "
            "KNX&nbsp;: la Cuisine et la Salle à manger au rez-de-chaussée, le Bureau, les chambres "
            "de Léane, des parents et de Lily et la Salle de bain à l'étage.",
            "Les huit autres (Entrée, Local technique, Salon, Espace central, WC-douche et les trois "
            "pièces du studio) affichent un cadran en pointillés « non raccordé » plutôt que des "
            "valeurs inventées — soit parce qu'aucun thermostat KNX n'y existe, soit parce que "
            "l'emplacement n'est pas encore attribué côté ETS. La grille garde ainsi la même "
            "géographie que la maison, prête à se remplir au fil des raccordements.",
        ],
    },
    {
        "heading": "Le cadran « Embrasement »",
        "paragraphs": [
            "Chaque thermostat est habillé d'un cadran circulaire au relief doux (neumorphisme), "
            "conçu à part sur un canevas de design dédié puis porté tel quel dans le dashboard — "
            "le canevas reste la référence&nbsp;: toute évolution visuelle repart de lui, jamais "
            "l'inverse. L'intensité de chauffe se lit sur <strong>quatre paliers plus l'arrêt</strong>&nbsp;: "
            "un halo de braise animé, un liseré lumineux, la teinte du disque et un anneau de "
            "« flamme » s'intensifient ensemble avec le palier, du gris froid à l'orange vif.",
            "Au centre&nbsp;: le mode, la consigne en grand et la température mesurée en dessous. "
            "Sous le cadran, les quatre modes KNX (Hors-gel, Nuit, Éco, Confort), le mode actif "
            "surligné. Un petit bouton ouvre l'historique de la pièce sur 24&nbsp;heures (consigne, "
            "température mesurée, ouverture de la vanne)&nbsp;; en cas de défaut du thermostat, il "
            "est remplacé par un bouton d'alerte rouge pulsant — c'est le cas aujourd'hui de la "
            "chambre de Léane, seule pièce qui remonte un capteur d'erreur de chauffage côté KNX.",
        ],
    },
    {
        "heading": "Des graduations qui s'allument jusqu'à la consigne",
        "paragraphs": [
            "La consigne était d'abord indiquée par un anneau sombre posé sur le cadran, jugé "
            "« trop grossier ». Plusieurs pistes ont été comparées (arc fin avec point lumineux, "
            "repère sur graduation, anneau piste + progression, puis trois couleurs d'anneau — "
            "bleu glacial, émeraude, améthyste) avant de retenir une solution <strong>sans anneau "
            "du tout</strong>&nbsp;: les 40 graduations déjà présentes autour du cadran s'illuminent "
            "(cuivre vers or, avec un halo) depuis le début de l'échelle jusqu'à la position de la "
            "consigne, sur une échelle fixe de 15 à 25&nbsp;°C.",
            "Un défaut de fond a été corrigé au passage&nbsp;: le balayage suivait au départ "
            "l'ouverture de la vanne, si bien qu'une pièce à l'arrêt (vanne fermée) semblait ne "
            "plus avoir de consigne du tout. Il suit désormais la <strong>consigne</strong>, "
            "indépendamment de la chauffe réelle — une salle de bain en hors-gel à 19&nbsp;° "
            "allume ses 16 graduations comme une autre pièce réglée à 19&nbsp;°. Les graduations "
            "allumées ont enfin été élargies de moitié et leur halo renforcé, pour rester lisibles "
            "à distance sur l'écran mural. Des boutons −/+ ont été ajoutés dans le cadran pour "
            "ajuster la consigne.",
        ],
    },
    {
        "heading": "Ce qui est réel, ce qui ne l'est pas encore",
        "paragraphs": [
            "Les consignes, températures mesurées, modes et le défaut de la chambre de Léane "
            "viennent de relevés réels des sept thermostats KNX, mais figés au moment de la "
            "construction de l'écran (22.09.2026)&nbsp;: aucun rafraîchissement en direct pour "
            "l'instant. Les courbes de l'historique sont un <strong>exemple</strong> (signalé "
            "comme tel dans la fenêtre).",
            "Surtout, l'écran est encore <strong>en lecture seule</strong>&nbsp;: les boutons −/+ "
            "et les boutons de mode ont leur rendu final mais n'envoient encore aucune commande "
            "au bus KNX. Les brancher sur les entités <code>climate</code> correspondantes de Home "
            "Assistant est la prochaine étape.",
        ],
    },
]

TEMP_GALLERY_INTRO = (
    "Captures de l'écran tel qu'il tourne aujourd'hui sur le dashboard mural (version du "
    "22.09.2026), prises le 24.09.2026."
)

TEMP_GALLERY = [
    ("temp-ecran-complet.jpg", "L'écran complet",
     "Grille 3×5 par étage entre les deux barres latérales : 7 cadrans raccordés, 8 emplacements "
     "« non raccordé » en pointillés."),
    ("temp-cadran-arret.jpg", "Arrêt — Salle de bain",
     "Hors-gel, consigne 19 ° : disque gris froid, aucune braise, mais les graduations restent "
     "allumées jusqu'à la consigne."),
    ("temp-cadran-chauffe.jpg", "Chauffe moyenne — Cuisine",
     "Consigne 20 °, mode Confort : disque ambré, halo de braise et anneau de flamme modérés."),
    ("temp-cadran-fort.jpg", "Chauffe forte — Chambre des parents",
     "Consigne 22 °, 28 graduations allumées : palier maximal, disque orange vif et halo intense."),
    ("temp-cadran-erreur.jpg", "Défaut — Chambre de Léane",
     "Thermostat en erreur : température mesurée « Indisponible » et bouton d'alerte rouge "
     "pulsant à la place du bouton d'historique."),
    ("temp-historique-popup.jpg", "Historique 24 h",
     "Consigne (pointillés), température mesurée (ambre) et ouverture de vanne (bleu) — courbes "
     "d'exemple, en attendant le branchement sur l'historique réel."),
]

TEMP_INSPI_INTRO = (
    "Le cadran reprend deux références déjà gardées dans la "
    "<a href=\"#inspirations\" onclick=\"showView('inspirations');return false;\">vue "
    "Inspirations</a> : le thermostat circulaire à dégradé du 31.08.2026 et l'effet « braise » "
    "du chauffage au sol du 01.09.2026."
)

TEMP_TODO = [
    ("done", "Porter le cadran « Embrasement » dans le dashboard",
     "Grille 3×5 construite et cadran v32 (graduations illuminées, boutons −/+) porté le "
     "22.09.2026 ; rendu vérifié à l'écran le 24.09.2026."),
    ("todo", "Rendre les commandes actives",
     "Relier les boutons −/+ et les boutons de mode aux entités climate KNX de Home Assistant, "
     "pour régler la consigne directement depuis l'écran mural."),
    ("todo", "Passer du relevé figé au flux live",
     "Rafraîchir consignes, températures et défauts en direct plutôt qu'un instantané — même "
     "chantier que pour l'écran Énergie."),
    ("todo", "Brancher l'historique réel",
     "Remplacer les courbes d'exemple de la fenêtre d'historique par les vraies séries "
     "(consigne, mesure, vanne) du recorder Home Assistant ou de VictoriaMetrics."),
    ("todo", "Raccorder les emplacements restants",
     "Attribuer côté ETS les pièces encore « non attribuées » (studio, espace central, "
     "WC-douche) ; leurs cadrans s'activeront sans changer la mise en page."),
    ("wip", "Trancher le thème clair / sombre du cadran",
     "Trois variantes sombres (Obsidienne, Verre fumé, Plaque incandescente) et un essai de "
     "graduations bleu → rouge proposés le 24.09.2026 — voir « Pistes pour un cadran sombre » "
     "plus haut. Décision de l'utilisateur attendue, puis report sur le canvas avant la production."),
]

# 24.09.2026 — pistes pour un cadran sombre (décision en attente). Page d'essai
# interactive servie telle quelle sous docs_site/maquettes/cadrans-sombres.html
# (copie de l'artifact « Cadrans sombres »), captures sous docs_site/assets/
# temp-sombre-*.jpg et temp-graduations-spectre-*.jpg.
TEMP_DARK = {
    "heading": "Pistes pour un cadran sombre (24.09.2026, décision en attente)",
    "paragraphs": [
        "Le disque clair du cadran détonne dans un dashboard au thème sombre. Trois variantes "
        "ont été proposées pour en sortir, en gardant tout ce qui fait le cadran « Embrasement » : "
        "braise animée, quatre paliers de chauffe, graduations allumées jusqu'à la consigne, "
        "boutons −/+ et modes KNX.",
        "<strong>A · Obsidienne</strong> reprend le même relief doux en graphite mat ; le disque "
        "se réchauffe vers le brun cuivré puis l'ambre foncé. C'est la transposition la plus "
        "directe du cadran actuel. <strong>B · Verre fumé</strong> rend le disque translucide et "
        "flouté, dans la famille des cartes Liquid Glass : la braise se voit à travers le verre, "
        "une lueur monte du bas du disque avec le palier. <strong>C · Plaque incandescente</strong> "
        "donne une lunette en fonte noire cerclée de cuivre, et le centre du disque rougit comme "
        "une plaque de cuisson — noir à l'arrêt, orange vif au palier fort — sans couronne de flamme.",
        "En parallèle, un essai de <strong>graduations bleu → rouge</strong> : chaque graduation "
        "prend la couleur de sa position sur l'échelle de 15 à 25&nbsp;°C (bleu, cyan, vert, jaune, "
        "orange, rouge, en dégradé continu). Plus la consigne est haute, plus l'arc allumé "
        "s'étend vers les couleurs chaudes ; au-delà de la consigne, les graduations restent "
        "éteintes. L'essai se combine avec n'importe laquelle des variantes.",
        "La <a href=\"/maquettes/cadrans-sombres.html\">page d'essai interactive</a> montre les "
        "cinq mêmes pièces dans chaque variante, au format réel de l'écran mural, avec un "
        "sélecteur de cadran et un curseur de consigne pour l'essai de graduations. Rien n'est "
        "encore porté sur le canvas de référence ni sur le dashboard.",
    ],
    "gallery": [
        ("temp-sombre-obsidienne.jpg", "A · Obsidienne",
         "Chauffe forte (Chambre des parents, 22 °) : graphite mat, disque réchauffé vers l'ambre foncé."),
        ("temp-sombre-verre-fume.jpg", "B · Verre fumé",
         "Chauffe forte : disque translucide, braise visible à travers, lueur montant du bas."),
        ("temp-sombre-plaque.jpg", "C · Plaque incandescente",
         "Chauffe forte : fonte noire cerclée de cuivre, centre du disque orange vif."),
        ("temp-graduations-spectre-20.jpg", "Graduations bleu → rouge, consigne 20 °",
         "Sur la variante Obsidienne : l'arc allumé va du bleu au vert-jaune."),
        ("temp-graduations-spectre-25.jpg", "Graduations bleu → rouge, consigne 25 °",
         "Consigne au maximum de l'échelle : l'arc complet, jusqu'au rouge."),
    ],
}
