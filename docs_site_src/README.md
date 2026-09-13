# Génération de `docs_site/index.html`

La page d'accueil de `docbulle.malnoy.com` (`docs_site/index.html`) est
**régénérée depuis les sources du projet, jamais éditée à la main** — même
convention que `docs_site/knx/index.html` (voir `knx/scripts/`).

Sources utilisées :

- `README.md` (racine du dépôt) — contenu de la vue « README du projet ». Le
  bloc ```mermaid``` de la §1 est extrait mais plus utilisé pour le rendu (voir
  Architecture ci-dessous) : il documente la même topologie en texte, à titre
  de sauvegarde/lecture rapide.
- `scripts/architecture_data.py` — services Docker, domaines fonctionnels
  et dépendances entre services. Source de vérité du schéma d'architecture ;
  à mettre à jour à la main depuis `README.md` §1 / `docker-compose.yml` si
  les services ou leurs relations changent.
- `dashboard/CAHIER_DES_CHARGES.md` §12 et le suivi de l'intégration KNX —
  repris à la main dans `scripts/content.py` (feuille de route). À mettre à
  jour manuellement si ces sources changent.
- Mémoire projet `custom_dashboard_energie_screen.md` — reprise à la main dans
  `scripts/content.py` (`ENERGIE_SECTIONS` / `ENERGIE_GALLERY` / `ENERGIE_TODO`,
  vue Énergie, ajoutée le 12.09.2026). Même principe que la feuille de route
  ci-dessus : à mettre à jour manuellement à chaque évolution notable de
  l'écran Énergie du dashboard, plutôt que de renvoyer vers la mémoire projet
  qui n'est pas publique.
- Photo de bannière : recadrage de `maison-facade-jardin-2.jpg`, servie en
  asset statique à `docs_site/assets/villa-bulle-banner.jpg`. Les captures
  d'inspiration de la vue Énergie suivent la même convention (`docs_site/assets/
  energie-inspi-*.jpg`, redimensionnées à ~1400px de large).
- Mémoire projet `custom_dashboard.md` (et fichiers liés) — reprise à la main
  dans `scripts/content.py` (`INSPI_INTRO` / `INSPI_GROUPS`, vue Inspirations,
  ajoutée le 13.09.2026) : trace des images envoyées en exemple (style,
  dashboard, photos...) au fil des discussions du dashboard sur mesure, avec
  le commentaire fait au moment de chaque envoi. Même principe que la vue
  Énergie ci-dessus. Images sous `docs_site/assets/inspi-*.jpg`, même
  convention (~1400px de large). Deux décisions du 11.09.2026 et une
  comparaison du 10.09.2026 sont documentées en texte seul (pas d'image
  fiable conservée, ou note perdue — voir la vue elle-même).

## Architecture : schéma unique

Le diagramme d'architecture n'est plus une image mermaid statique — c'est du
SVG généré en pur Python (`scripts/architecture_overview.py`), thémé avec les
mêmes variables CSS que le reste du site (donc lisible en clair comme en
sombre). C'est une infographie statique unique, pas un diagramme navigable :
tout est visible d'un coup, regroupé par **domaine fonctionnel** (pas par
réseau Docker) — Domotique (Home Assistant seul), Monitoring, Documentation,
Dashboard, Véhicule, Accès distant — à l'intérieur d'un grand cadre « Mac
mini » représentant la solution matérielle, avec le bus KNX filaire (physique,
hors Docker) en dehors de ce cadre et les dépendances externes (Tesla Fleet
API, Open-Meteo) en marge. Le même SVG (`render_overview_svg()`) est réutilisé
tel quel en haut de la vue README et dans la vue Architecture logicielle, via
`render_overview_frame(uid)` qui l'enveloppe dans un petit widget de zoom/pan
(molette, glisser, pincement tactile, boutons +/-/reset — voir
`initArchZoomInstances()` dans `template.html`) : le schéma est dense, il doit
pouvoir s'agrandir sans perdre la mise en page générale (ajouté le 12.09.2026,
retour utilisateur).

Les coordonnées des cadres/nœuds sont calées à la main sur une grille
(`architecture_overview.py`), avec les connecteurs routés par couloirs
verticaux/horizontaux vérifiés libres de tout cadre plutôt que par un routeur
automatique. Aucune dépendance Node/Chromium n'est nécessaire pour ce rendu.

## Pipeline (3 étapes)

Nécessite Python (`markdown`, `Pillow`) — rien d'autre. **En pratique,
demander à Claude de relancer cette génération** (il l'exécute dans son bac à
sable cloud, puis dépose le résultat dans `docs_site/`) plutôt que de
l'exécuter soi-même.

```
scripts/extract_readme.py        # README.md -> README_no_mermaid.md
scripts/render_readme.py         # README_no_mermaid.md -> readme_body.html
                                  # (intègre le schéma d'architecture unique)
scripts/build_index.py           # injecte tout dans scripts/template.html -> scripts/index.html
```

Puis copier `scripts/index.html` vers `docs_site/index.html` (le conteneur
`doc-knx` sert le dossier en lecture seule, sans étape de build ni redémarrage
nécessaire).

## Design

Identité visuelle « Villa Bulle » : palette Nuit/Ambre/Glacier/Mousse/Cuivre/
Teal (Teal ajouté le 12.09.2026 pour la tuile Énergie), typographies Fraunces
(titres) / Inter (texte) / IBM Plex Mono (données, labels) — cohérente avec le
dashboard et le diagramme d'infrastructure. `scripts/template.html` contient
le design complet (CSS + squelette HTML + routeur JS par hash `#readme` /
`#architecture` / `#roadmap` / `#energie` / `#inspirations`) ; les
placeholders `__XXX__` sont remplis par `build_index.py`.

12.09.2026 (retour utilisateur) : largeur de page portée de 1180px à 1600px
(`--page-w`) et polices de lecture agrandies (README, feuille de route, vue
Énergie) — la page laissait trop de largeur inutilisée sur grand écran.

Décidé le 11.09.2026 — voir `CLAUDE.md` §9. Cinquième tuile (Énergie) et
zoom du schéma d'architecture ajoutés le 12.09.2026. Sixième tuile
(Inspirations) ajoutée le 13.09.2026, même principe de mise en page pleine
largeur que la tuile Énergie (`--c-inspi` / violet).
