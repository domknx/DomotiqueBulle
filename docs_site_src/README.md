# Génération de `docs_site/index.html`

La page d'accueil de `docbulle.malnoy.com` (`docs_site/index.html`) est
**régénérée depuis les sources du projet, jamais éditée à la main** — même
convention que `docs_site/knx/index.html` (voir `knx/scripts/`).

Sources utilisées :

- `README.md` (racine du dépôt) — contenu de la vue « README du projet ». Le
  bloc ```mermaid``` de la §1 est extrait mais plus utilisé pour le rendu (voir
  Architecture ci-dessous) : il documente la même topologie en texte, à titre
  de sauvegarde/lecture rapide.
- `scripts/architecture_data.py` — services Docker, catégories fonctionnelles
  et dépendances entre services. Source de vérité du diagramme d'architecture
  interactif ; à mettre à jour à la main depuis `README.md` §1 /
  `docker-compose.yml` si les services ou leurs relations changent.
- `dashboard/CAHIER_DES_CHARGES.md` §12 et le suivi de l'intégration KNX —
  repris à la main dans `scripts/content.py` (feuille de route). À mettre à
  jour manuellement si ces sources changent.
- Photo de bannière : recadrage de `maison-facade-jardin-2.jpg`, servie en
  asset statique à `docs_site/assets/villa-bulle-banner.jpg`.

## Architecture : diagramme interactif

Le diagramme d'architecture n'est plus une image mermaid statique — c'est du
SVG généré en pur Python (`scripts/architecture_view.py`), thémé avec les
mêmes variables CSS que le reste du site (donc lisible en clair comme en
sombre), et navigable à trois niveaux :

1. **Vue macro** — 7 zones fonctionnelles cliquables (`render_macro_grid`),
   aussi intégrée en résumé dans la vue README.
2. **Détail par zone** — un mini-diagramme par zone (`render_category_panels`),
   avec ses dépendances vers les autres zones affichées comme des bulles
   cliquables (qui font sauter vers la zone correspondante).
3. **Popup de dépendances** — cliquer un service ouvre ses dépendances
   directes (« Dépend de » / « Utilisé par »), construites en JS depuis
   `window.ARCH_DATA` (`build_arch_data_json`).

Aucune dépendance Node/Chromium n'est nécessaire pour ce rendu.

## Pipeline (3 étapes)

Nécessite Python (`markdown`, `Pillow`) — rien d'autre. **En pratique,
demander à Claude de relancer cette génération** (il l'exécute dans son bac à
sable cloud, puis dépose le résultat dans `docs_site/`) plutôt que de
l'exécuter soi-même.

```
scripts/extract_readme.py        # README.md -> README_no_mermaid.md
scripts/render_readme.py         # README_no_mermaid.md -> readme_body.html
                                  # (intègre la vue macro de l'architecture)
scripts/build_index.py           # injecte tout dans scripts/template.html -> scripts/index.html
```

Puis copier `scripts/index.html` vers `docs_site/index.html` (le conteneur
`doc-knx` sert le dossier en lecture seule, sans étape de build ni redémarrage
nécessaire).

## Design

Identité visuelle « Villa Bulle » : palette Nuit/Ambre/Glacier/Mousse/Cuivre,
typographies Fraunces (titres) / Inter (texte) / IBM Plex Mono (données,
labels) — cohérente avec le dashboard et le diagramme d'infrastructure.
`scripts/template.html` contient le design complet (CSS + squelette HTML +
routeur JS par hash `#readme` / `#architecture` / `#roadmap`) ; les
placeholders `__XXX__` sont remplis par `build_index.py`.

Décidé le 11.09.2026 — voir `CLAUDE.md` §9.
