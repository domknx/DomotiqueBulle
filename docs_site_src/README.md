# Génération de `docs_site/index.html`

La page d'accueil de `docbulle.malnoy.com` (`docs_site/index.html`) est
**régénérée depuis les sources du projet, jamais éditée à la main** — même
convention que `docs_site/knx/index.html` (voir `knx/scripts/`).

Sources utilisées :

- `README.md` (racine du dépôt) — contenu de la vue « README du projet » et
  diagramme d'architecture (bloc ```mermaid``` de la §1).
- `dashboard/CAHIER_DES_CHARGES.md` §12, `docker-compose.yml`, et le suivi de
  l'intégration KNX — repris à la main dans `scripts/content.py` (liste des
  services et de la feuille de route). À mettre à jour manuellement si ces
  sources changent.
- Photo de bannière : recadrage de `maison-facade-jardin-2.jpg`, servie en
  asset statique à `docs_site/assets/villa-bulle-banner.jpg`.

## Pipeline (5 étapes)

Nécessite Python (`markdown`, `Pillow`) et Node + `@mermaid-js/mermaid-cli`
(`mmdc`) avec Chromium — pas installé sur le Mac mini. **En pratique, demander
à Claude de relancer cette génération** (il l'exécute dans son bac à sable
cloud, puis dépose le résultat dans `docs_site/`) plutôt que de l'exécuter
soi-même.

```
scripts/extract_readme.py        # README.md -> diagram.mmd + README_no_mermaid.md
mmdc -i diagram.mmd -o diagram.svg -b transparent \
     -c scripts/mermaid-theme.json -p scripts/puppeteer-config.json --width 1400
scripts/render_readme.py         # README_no_mermaid.md + diagram.svg -> readme_body.html
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
