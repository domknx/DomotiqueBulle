# Cahier des charges — Dashboard sur-mesure Villa Bulle

Document vivant, tenu à jour par Claude au fil des décisions. Complète les notes de mémoire projet (`custom_dashboard.md` côté Claude) sans les remplacer : ce fichier est la référence versionnée dans le repo, la mémoire garde l'historique des itérations et des essais rejetés.

Statut : brouillon v1 (02.09.2026) — plusieurs points restent ouverts, voir §9.

## 1. Contexte et objectifs

Projet parallèle au dashboard Tunet (qui reste la solution active au quotidien pendant que ce dashboard sur-mesure est développé). Codé de A à Z par Claude, sans fork d'un projet existant. Intégration future comme service Docker indépendant, une fois la direction visuelle et l'architecture d'écrans validées (pas encore le cas — voir §7).

## 2. Périmètre appareils & stratégie responsive

- **Écran mural tactile** (panneau fixe, format paysage) : forme physique de référence, c'est sur ce gabarit que la direction visuelle a été validée jusqu'ici (grandes cibles tactiles, pas de bordures de fenêtre à gérer).
- **iPad / tablette** : même architecture visuelle et mêmes gabarits, adaptés par points de rupture CSS plutôt que par un code séparé. Probablement paysage également, avec une densité de grille resserrée.
- **iPhone / mobile** : portrait à prévoir. Rupture structurelle attendue : la navigation verticale à gauche devient une barre de navigation basse (plus naturelle au pouce), et les cartes "verre dépoli" latérales des écrans pièce passent en plein largeur bas d'écran ou en accordéon.
- **Mac / desktop** : hors périmètre pour l'instant. Le Mac garde Tunet et/ou les dashboards natifs HA ; ce dashboard sur-mesure ne cible pas explicitement le format desktop large aujourd'hui (à confirmer — voir §9).

Principe retenu : un seul jeu de composants et un seul état applicatif, réarrangés par media queries — pas de version dupliquée par appareil.

## 3. Architecture de l'information (écrans)

Écrans déjà prototypés (5 positions verticales) :

0. **Maison** — écran d'accueil, photo réelle de la villa en fond, horloge live.
1. **Étage** — vue d'ensemble grille des pièces de l'étage, puis swipe horizontal vers chaque pièce (fond iso/photo + effets lumière/chauffage + carte de contrôle).
2. **RDC** — même logique que l'étage.
3. **Extérieur** — contenu détaillé pas encore défini (voir §9).
4. **Fonctions** — scènes et actions transversales (à préciser : scènes prédéfinies type "Mode nuit", "Tout éteindre", "Mode absence").

Nouvelles sections à intégrer à l'architecture dès maintenant (mock/vide tant que les données réelles ne sont pas branchées) :

5. **Énergie / Solaire** — production instantanée, consommation, état de la batterie ; données qui alimentent aussi Grafana en parallèle.
6. **Tesla** — état de charge, autonomie, climatisation, position — en lien avec l'intégration Tesla Fleet API (jalon 4).
7. **Sécurité / Caméras** — extension future du bus KNX, pas encore de matériel installé : section maquette pour l'instant.
8. **Météo** — cartes météo animées mises de côté au moment du choix de direction visuelle (images de référence 8-9), à intégrer quelque part dans la navigation.
9. **Accès Grafana** — pas une reconstruction des graphiques dans le dashboard, mais un point de lancement vers les dashboards Grafana existants (`grafanabulle.malnoy.com`).

## 4. Modèle de navigation (proposition à valider)

La nav actuelle (colonne d'icônes persistante à gauche + swipe) a été pensée pour 5 destinations. Avec 9-10 destinations, l'empiler telle quelle dans une seule colonne casserait la lisibilité tactile. Proposition : réutiliser le modèle déjà validé "étage → pièces" (nav de premier niveau, puis swipe horizontal de second niveau) pour regrouper les nouvelles sections plutôt que d'allonger la colonne de gauche :

- **Niveau 1 (nav gauche persistante, 5 icônes)** : Maison · Intérieur · Extérieur · Système · Fonctions.
- **Intérieur** : regroupe Étage et RDC (sélecteur d'étage, puis swipe horizontal vers les pièces — inchangé par rapport au prototype actuel).
- **Système (nouveau hub)** : swipe horizontal entre Énergie/Solaire, Tesla, Sécurité/Caméras, Météo, et la tuile de lancement Grafana — même mécanique de swipe que la vue d'étage.

À valider avec l'utilisateur avant de commencer l'implémentation visuelle (voir §9).

## 5. Gabarits de mise en page (position des éléments)

**A. Écran Maison (accueil)**
Fond : photo pleine page de la villa, assombrie en dégradé bas→haut pour la lisibilité. Horloge + date en évidence. Nav gauche persistante. Pas de scroll, swipe vers les autres sections.

**B. Écran vue d'étage / RDC (grille de pièces)**
Fond neutre nuit ou photo maison assombrie. Titre de l'étage en haut. Grille de tuiles pièces (vignette iso/photo + nom + indicateur d'état résumé : température, lumière allumée). Nav gauche persistante. Swipe horizontal → pièce individuelle.

**C. Écran pièce** (déjà en place, à conserver)
Fond plein cadre (iso ou photo) avec `.light-fx` et `.heat-fx`. Carte "verre dépoli" latérale : nom de la pièce, température actuelle/cible, interrupteurs, contrôle chauffage, volets si présents. Toggle Iso/Photo en dock bas. Nav gauche persistante.

**D. Écrans du hub Système** (nouveaux gabarits à concevoir)
Sous-nav horizontale par swipe, même mécanique que étage→pièces.
- *Énergie/Solaire* : jauges (production instantanée, batterie %, consommation), courbe du jour, tuile "voir plus → Grafana".
- *Tesla* : carte état de charge (%, autonomie), mini-carte position si disponible, icônes climatisation/verrouillage.
- *Sécurité/Caméras* : grille de vignettes caméra (maquette tant qu'il n'y a pas de matériel), statut portes/fenêtres.
- *Météo* : carte animée (une des images de référence 8-9), prévisions J+1/J+2 compactes.
- *Grafana* : tuile de lancement (ouvre `grafanabulle.malnoy.com`), pas de duplication de graphiques.

**E. Écran Extérieur** — gabarit à définir une fois le contenu précisé (§9).

**F. Écran Fonctions** — liste/grille de scènes et actions rapides transversales.

## 6. Système visuel (rappel, déjà figé — à réutiliser pour les nouvelles sections)

Palette : Nuit `#0b0e16`, Brume `#eef1f6`, Ambre `#ff9c54`, Glacier `#5ac8fa`, Mousse `#6fcf97`, Cuivre `#caa06b`.
Typo : Fraunces / Inter / IBM Plex Mono. Thème sombre unique assumé (pas de mode clair prévu).

## 7. Contraintes techniques actuelles

- Prototype hébergé comme Artifact Claude : fichier HTML autonome, CSS/JS inline, images en data URI (les Artifacts ne chargent pas d'image externe).
- Données statiques/maquette pour l'instant — **le branchement réel à Home Assistant est volontairement reporté** (décision du 02.09.2026) : on continue à itérer sur la direction visuelle et l'architecture d'écrans avant de définir comment le futur service Docker parlera à HA (API REST/WebSocket, auth, polling vs push).
- `prefers-reduced-motion` déjà géré pour les animations existantes (glow de chauffage) — à généraliser à toute nouvelle animation (jauges énergie, carte météo animée).
- Toute nouvelle interaction complexe (swipe, effet dynamique) doit être vérifiée par un test Playwright headless réel (clics rejoués + capture, ou lecture de `getComputedStyle` dans le temps) avant d'être annoncée comme corrigée — une relecture de code seule a déjà laissé passer des bugs sur ce projet.

## 8. Hors scope / reporté

- Branchement réel à Home Assistant (données live).
- Persistance côté serveur.
- Matériel sécurité/caméras (pas encore installé) → section maquette uniquement.
- Photos réelles des pièces autres que Chambre Léane (pas encore fournies).
- Intégration comme service Docker (prévue une fois la direction visuelle validée).

## 9. Points ouverts à trancher ensemble

1. Le modèle de navigation à 2 niveaux proposé au §4 (hub "Système" regroupant Énergie/Tesla/Sécurité/Météo/Grafana) convient-il, ou préfère-t-on une autre organisation (ex. sections séparées en tête de nav, ou une nav secondaire différente) ?
2. Contenu précis de l'écran **Extérieur** : terrasse, éclairage extérieur, volets, piscine, jardin — quels éléments KNX y placer ?
3. Le Mac doit-il aussi être un format cible pour ce dashboard sur-mesure, ou reste-t-il volontairement hors périmètre (Tunet/HA natif suffisent sur desktop) ?
4. Contenu de l'écran **Fonctions** : quelles scènes/actions rapides prioritaires ?
