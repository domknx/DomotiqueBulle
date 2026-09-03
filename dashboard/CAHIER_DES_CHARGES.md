# Cahier des charges — Dashboard sur-mesure Villa Bulle

Document vivant, tenu à jour par Claude au fil des décisions. Complète les notes de mémoire projet (`custom_dashboard.md` côté Claude, qui garde l'historique détaillé des itérations visuelles) sans les remplacer : ce fichier est la référence structurelle versionnée dans le repo.

Statut : **v2 (nuit du 02→03.09.2026)** — élargi sur demande explicite de l'utilisateur ("ne pas se limiter à ce qui a été proposé, documente-toi, propose une solution innovante en navigation et fonctionnalités, réfléchis à des effets de scroll et à des effets d'ouverture/fermeture de volets, construis le cahier des charges et plusieurs maquettes pendant la nuit"). Contient à la fois les fondations déjà validées (§1-2) et des propositions non encore validées (§3-6, marquées comme telles).

## 1. Fondations déjà validées (rappel de la v1)

- **Contexte** : projet parallèle à Tunet (qui reste actif au quotidien), codé de A à Z par Claude, sans fork. Intégration Docker future une fois la direction visuelle validée.
- **Périmètre appareils** : écran mural tactile (référence) + responsive tablette/iPad et mobile/iPhone via un seul jeu de composants et des breakpoints CSS. Mac hors périmètre pour l'instant (point encore ouvert).
- **Système visuel figé** : palette Nuit `#0b0e16`, Brume `#eef1f6`, Ambre `#ff9c54`, Glacier `#5ac8fa`, Mousse `#6fcf97`, Cuivre `#caa06b` ; typo Fraunces/Inter/IBM Plex Mono ; thème sombre unique assumé.
- **Écrans déjà prototypés** : Maison (accueil), Étage, RDC, Extérieur, Fonctions — plus les sections ajoutées le 02.09.2026 : Énergie/Solaire, Tesla, Sécurité/Caméras, Météo, accès Grafana.
- **Contrainte technique** : prototype = Artifact Claude, fichier HTML autonome, CSS/JS inline, images en data URI. Données statiques pour l'instant, branchement HA réel volontairement reporté.
- **Modèle de navigation proposé en v1** (nav gauche à 5 icônes + hub "Système" en swipe horizontal) : reste une option valable, voir comparatif §3.

## 2. Sources d'inspiration consultées cette nuit

Recherche volontairement brève et orientée principe, pas benchmark exhaustif :

- Le constat qui structure le plus les propositions ci-dessous : un panneau mural fonctionne différemment d'une app téléphone. Un article sur les displays domotiques muraux insiste sur le fait qu'"un écran mural fonctionne parce qu'il reste visible en permanence" et que les habitants passent devant plusieurs fois par jour — l'enjeu n'est donc pas de naviguer vite dans des menus, mais de rendre l'état de la maison lisible sans avoir à cliquer ([Home Assistant Display Panel — The Wall Is Becoming the Interface](https://smartnmagic.com/blogs/solutions/home-assistant-display-panel-the-wall-is-becoming-the-interface)). C'est l'argument central du Concept B (§3).
- Un article sur les dashboards Home Assistant avancés recommande de sortir de la grille de tuiles uniforme : mise en page asymétrique façon magazine (colonne centrale pour les contrôles principaux, colonnes latérales pour l'info en un coup d'œil), regroupement contextuel par pièce ou par fonction, et des cartes qui changent de couleur/icône selon l'état réel du device plutôt qu'un simple bouton statique ([Home Assistant Dashboards: Beyond Smart Displays](https://thehomesmarthome.com/beyond-smart-display-home-assistant-dashboards-wall-panels/)). Repris dans les gabarits d'écran révisés (§5).
- Pour l'effet volet (§4) : la technique CSS classique de "venetian blinds" anime des lattes horizontales en combinant `translateY` et `scaleY` de façon échelonnée pour simuler une descente progressive ([CSS Blinds animation effect](https://animania.info/css/blinds), [Venetian Blinds Animation (CSS only)](https://codepen.io/jamesnimlos/pen/NbGKOV)) — adaptée ici pour être pilotée par un pourcentage réel (pas juste une boucle décorative) et couplée aux effets `.light-fx`/`.heat-fx` déjà en place sur les pièces.
- Le scroll/parallax multi-couches (arrière-plans qui défilent à des vitesses différentes pour donner une impression de profondeur) est une technique de site web bien établie, largement documentée sur les galeries d'inspiration ([exemples de scroll parallax — Awwwards](https://www.awwwards.com/websites/parallax/), [21 Best Parallax Scrolling Websites — Colorlib](https://colorlib.com/wp/parallax-scrolling-websites/)) — reprise pour le Concept A (§3) où le ciel/la montagne/la maison défilent à des vitesses différentes pendant le scroll vertical entre les étages.

## 3. Deux directions de navigation innovantes (à comparer, non tranchées)

Le modèle v1 (nav gauche fixe + swipe horizontal étage→pièces, hub "Système" en swipe) reste une option sûre et cohérente avec le prototype déjà validé visuellement. Voici deux alternatives plus audacieuses, chacune illustrée par une maquette Artifact séparée (voir §7) :

### Concept A — "Strates" (navigation spatiale par défilement continu)

Idée : au lieu de pages qui se succèdent par swipe, la maison est représentée comme un **empilement vertical continu** — ciel/montagne en fond, toiture et extérieur, étage, RDC — qu'on parcourt par un scroll vertical unique, avec un effet de **parallax multi-couches** (le ciel défile plus lentement que la maison, qui défile plus lentement que le sol/jardin). Pas de pages discrètes : on "descend" physiquement dans la maison comme on descendrait un escalier.

- Entrer dans une pièce ne se fait plus par swipe latéral mais par un **zoom-through** : on touche une tuile de pièce dans la vue d'étage, elle grossit et remplit l'écran (transition d'échelle, pas de translation).
- La navigation persistante devient un **indicateur d'ascenseur** fin sur le bord (pas une colonne d'icônes) : une ligne verticale avec des repères (Maison / Étage / RDC / Extérieur), la position actuelle mise en évidence, chaque repère tapable pour sauter directement.
- Le hub "Système" (Énergie/Tesla/Sécurité/Météo/Grafana) devient une **strate séparée** accessible en scrollant au-delà de l'extérieur (sous la maison, façon "sous-sol technique") plutôt qu'un hub latéral.
- Avantage : cohérent avec le geste naturel du doigt sur un écran mural vertical, effet "waouh" fort, renforce la métaphore spatiale (on est vraiment dans la maison). Risque : plus complexe à rendre fluide en responsive mobile (le scroll vertical continu doit cohabiter avec le scroll de contenu à l'intérieur d'une pièce) — à valider avec une vraie maquette avant de trancher.

### Concept B — "Respiration" (hub ambiant + cartes contextuelles)

Idée, directement inspirée du constat "le mur fonctionne parce qu'il reste visible" : l'écran d'accueil n'est plus une simple photo + horloge, mais un **hub vivant** qui expose en permanence, sans qu'on ait à naviguer, les informations qui comptent maintenant — météo du jour, alerte sécurité s'il y en a une, état énergie/batterie, ETA Tesla si le véhicule rentre. Mise en page asymétrique façon magazine : une colonne centrale plus grande pour la maison/les scènes, deux colonnes latérales plus fines pour les cartes contextuelles.

- Les pièces se parcourent comme un **carrousel horizontal de tuiles qui "respirent"** : chaque tuile pulse doucement (échelle/luminosité) au rythme de la pièce elle-même — pièce chauffée et occupée = pulsation plus chaude et plus rapide, pièce vide et froide = quasi immobile. L'état est visible sans toucher l'écran.
- Toucher une pièce ne change pas d'écran plein cadre : une **carte "bottom sheet"** glisse depuis le bas et recouvre le tiers inférieur de l'écran avec les contrôles détaillés, pendant que le fond de la pièce reste visible en haut. Ce même pattern fonctionne nativement en portrait sur iPhone (contrairement à la carte latérale actuelle, pensée pour le paysage).
- La navigation devient un **dock contextuel en bas**, qui change de contenu selon la section (dock "pièces" quand on est dans la maison, dock "système" quand on est dans Énergie/Tesla/Sécurité/Météo) plutôt qu'une colonne fixe à gauche.
- Avantage : colle le mieux à la philosophie "panneau mural = objet ambiant, pas une app" et se transpose le plus naturellement en responsive mobile (le dock bas et la bottom sheet sont déjà des patterns mobiles). Risque : moins spectaculaire visuellement que le Concept A, la réussite dépend beaucoup du soin apporté aux micro-animations de "respiration".

## 4. Effets de scroll et de transition (transversal aux deux concepts)

- **Parallax multi-couches** : au moins 3 profondeurs (ciel/montagne, maison/toiture, sol/jardin) défilant à des vitesses différentes lors d'un scroll ou d'un swipe — déjà partiellement présent avec la photo de la maison en fond assombri, à structurer en couches distinctes.
- **Bleed lumineux entre écrans adjacents** : pendant une transition (swipe pièce à pièce ou scroll de strate), la teinte ambrée/glacier de l'écran suivant commence à apparaître en bord de cadre avant que la transition soit terminée, comme un rai de lumière sous une porte qui s'ouvre — renforce la continuité spatiale plutôt qu'un cut sec entre deux écrans.
- **Profondeur de champ au scroll** : les éléments qui sortent du cadre (haut ou bas selon le sens du scroll) se floutent légèrement et s'assombrissent avant de disparaître, plutôt que de sortir nets — effet cinématique déjà utilisé dans beaucoup de sites à parallax.
- **Zoom-through pièce** (Concept A) : transition d'échelle plutôt que de position lorsqu'on entre dans une pièce depuis la vue d'étage.
- Toutes ces animations respectent `prefers-reduced-motion` (déjà la règle sur ce projet pour le glow de chauffage) : bascule directe à l'état final, sans les étapes intermédiaires.

## 5. Effet d'ouverture/fermeture des volets (nouveau, détaillé)

Objectif : un volet qui se ferme ou s'ouvre doit se voir et se ressentir sur le fond de la pièce (iso ET photo), pas seulement sur une icône de commande — dans le même esprit que `.light-fx`/`.heat-fx` déjà en place.

- **Lattes animées** : une rangée de lattes horizontales (SVG ou divs) superposée sur la zone fenêtre du fond de pièce. Chaque latte descend avec un `translateY` + `scaleY` échelonné (léger décalage de timing entre lattes successives) pour un mouvement de descente réaliste, plutôt que toutes les lattes bougeant en même temps.
- **Piloté par un pourcentage, pas juste ouvert/fermé** : la position des lattes est calculée à partir de l'état réel du volet (0-100 % fermé), pas une simple animation binaire — cohérent avec le fait que les volets KNX se pilotent en position, pas juste tout-ou-rien.
- **Effet lumière couplé** : plus le volet se ferme, plus `.light-fx` s'assombrit progressivement (au lieu du binaire actuel allumé/éteint) et une **bande d'ombre** progresse sur le sol en écho aux lattes, réutilisant le même système de calque que le glow de chauffage déjà validé. À l'ouverture, une lumière du jour progressive balaie la pièce dans l'autre sens.
- **Accessibilité** : `prefers-reduced-motion` fait sauter directement à l'état final (lattes + ombre + luminosité dans leur position finale, sans les étapes intermédiaires) — même règle que pour le chauffage.
- Techniquement démontrable dans une maquette statique (curseur de démonstration 0-100 % actionnable à la main), en attendant un vrai branchement à l'état KNX du volet.

## 6. Fonctionnalités innovantes proposées (au-delà de la liste v1)

- **Suggestions contextuelles** : bandeau discret et non intrusif qui propose une action selon le contexte (ex. "Il fait soleil et la Chambre Léane est vide — fermer les volets ?"), jamais automatique sans confirmation.
- **Teinte globale réactive à la météo** : au-delà de la carte Météo dédiée, une légère variation de l'ambiance visuelle de tout le dashboard selon le temps réel (grisaille plus froide un jour de pluie, chaleur plus marquée un jour ensoleillé) — discret, jamais au point de nuire à la lisibilité.
- **Plan de chaleur énergie sur la vue d'étage** : dans la grille de tuiles pièces, une légère teinte de fond par tuile reflétant sa consommation relative du moment — lien visuel direct avec la donnée qui alimente aussi Grafana, sans dupliquer un graphique.
- **Scènes "respirées"** : transitions progressives sur plusieurs minutes pour les scènes qui le justifient (lever du jour simulé, tombée de la nuit) plutôt qu'un changement d'état instantané.
- **Mode veille ambiant** : après une période d'inactivité, l'écran mural (allumé en continu) bascule vers un affichage minimal — horloge + météo — pour économiser l'attention visuelle sans s'éteindre, cohérent avec la philosophie "objet ambiant" du Concept B.
- **Mode invité simplifié** : accès restreint (pièces communes, pas de sécurité/Tesla) pour un panneau mural potentiellement visible par des visiteurs.

## 7. Maquettes visuelles (livrées cette nuit)

Deux Artifacts distincts, chacun démontrant un des deux concepts de navigation sur un sous-ensemble représentatif d'écrans (accueil, une vue d'étage, une pièce avec le nouvel effet volet, un aperçu du hub système) — pas une reconstruction complète des 10 écrans, l'objectif est de trancher la direction avant d'investir dans la construction exhaustive :

- **Concept A "Strates"** : [lien à compléter après publication]
- **Concept B "Respiration"** : [lien à compléter après publication]

## 8. Ce qui reste hors scope

- Branchement réel à Home Assistant (données live).
- Persistance côté serveur.
- Matériel sécurité/caméras (pas encore installé) → section maquette uniquement.
- Photos réelles des pièces autres que Chambre Léane (pas encore fournies).
- Intégration comme service Docker.
- Retour haptique/sonore réel sur les volets (prévu conceptuellement en §5, non simulable dans un Artifact statique).

## 9. Points ouverts à trancher ensemble

1. **Choix de direction de navigation** : garder le modèle v1 (nav gauche + hub Système), ou basculer sur le Concept A ("Strates"), ou le Concept B ("Respiration") — voir les deux maquettes avant de décider.
2. Contenu précis de l'écran **Extérieur** : terrasse, éclairage, volets, piscine, jardin ?
3. Le **Mac** doit-il être un format cible, ou reste-t-il hors périmètre ?
4. Contenu de l'écran **Fonctions** : quelles scènes/actions prioritaires ?
5. Les suggestions contextuelles et le mode veille ambiant (§6) sont-ils souhaités, ou jugés superflus/intrusifs ?
