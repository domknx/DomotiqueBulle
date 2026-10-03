# Page « Version » — suivi et mise à jour de Home Assistant

Ajoutée le 03.10.2026. La page « Version » du dashboard sur mesure (`dashboard_web_nginx/index.html`)
affiche la version installée de Home Assistant, la dernière version publiée, les principales
modifications, les problèmes connus, une recommandation, et un bouton « Sauvegarder et mettre à
jour ». Un bandeau défilant apparaît sur l'Accueil quand une nouvelle version est disponible.

## Qui fait quoi

| Élément | Rôle |
|---|---|
| `dashboard/api/app/ha_version.py` | Lit la version installée, interroge `version.home-assistant.io`, sert l'analyse, dépose les demandes de mise à jour. **Ne touche jamais à Docker.** |
| `dashboard/version/ha_release_analysis.json` | Analyse rédigée par Claude : modifications, problèmes connus, recommandation. Réécrite chaque vendredi soir par une tâche planifiée. |
| `dashboard/version/update_password.hash` | Empreinte du mot de passe de mise à jour. Non versionnée. |
| `dashboard/version/state/` | Fichiers d'état, non versionnés : cache de la dernière version, demandes, avancement, journaux. |
| `scripts/ha_update_agent.sh` | Agent launchd sur le Mac : ramasse les demandes et lance la mise à jour. Seul lien entre le dashboard et Docker. |
| `scripts/ha_update.sh` | Sauvegarde, mise à jour, vérification, retour arrière automatique. |
| `scripts/ha_restore.sh` | Retour arrière manuel à partir d'une sauvegarde. |
| `scripts/install_ha_update_agent.sh` | Installe ou désinstalle l'agent. |

## Mise en service (une seule fois, dans le Terminal du Mac mini)

```bash
cd /Users/docker/Domotique_Claude_Docker
docker compose up -d --build dashboard-api
docker compose restart dashboard-proto
bash scripts/install_ha_update_agent.sh
```

Le redémarrage de `dashboard-proto` est nécessaire : nginx garde en mémoire l'ancienne adresse de
`dashboard-api` après sa recréation. Sans l'agent, la page fonctionne mais le bouton de mise à jour
reste inactif.

Essai à blanc conseillé avant la première vraie mise à jour (contrôles et téléchargement de
l'image, sans rien modifier) :

```bash
./scripts/ha_update.sh --dry-run 2026.9.4
```

## Les trois couleurs du bouton

| Couleur | Signification |
|---|---|
| Vert | Mise à jour recommandée : aucun problème connu ne concerne l'installation. |
| Jaune | Mise à jour possible, des problèmes mineurs sont encore ouverts. |
| Rouge | Mise à jour déconseillée, ou version pas encore analysée. |

Le bouton reste cliquable en rouge : la fenêtre de confirmation rappelle l'avis défavorable. Une
version publiée après la dernière analyse est toujours rouge (« pas encore analysée ») jusqu'à la
vérification du vendredi suivant.

## Mot de passe de mise à jour

Le bouton ouvre une fenêtre qui demande un mot de passe avant d'autoriser la mise à jour. Il est
vérifié par `dashboard-api`, jamais dans la page. Seule son empreinte salée (PBKDF2-SHA256) est
conservée, dans `update_password.hash`, hors Git. Cinq erreurs de suite bloquent le bouton
pendant dix minutes. Sans fichier d'empreinte, toute mise à jour est refusée.

Pour le changer (saisie masquée, demandée deux fois) :

```bash
docker exec -it dashboard-api python -m app.set_password
```

Le mot de passe ne protège que le bouton de la page. Lancer `scripts/ha_update.sh` à la main dans
le Terminal du Mac ne le demande pas.

## Vérifications

- **Vendredi soir** : une tâche planifiée Claude relève la dernière version, relit les notes de
  version et les problèmes signalés, puis réécrit `ha_release_analysis.json` et
  `state/latest.json`. La surveillance d'une version dure 30 jours à partir de la sortie de sa
  version mensuelle (`monitoring.start`).
- **Bouton « Vérifier maintenant »** : interroge la source officielle tout de suite. Il met à jour
  les numéros de version, pas l'analyse.
- **Filet de sécurité** : si aucune vérification n'a eu lieu depuis 8 jours, la page en relance une.

## Déroulé d'une mise à jour

1. Contrôles : Docker répond, version valide et plus récente, place disque suffisante.
2. Téléchargement de la nouvelle image. Home Assistant tourne encore ; un échec ici ne change rien.
3. Arrêt de Home Assistant, puis archive complète de `HomeAssistant_Data` dans
   `Backups/ha_update/<date>_<ancienne>_vers_<nouvelle>/`. L'archive est écrite sans compression
   (plus rapide), puis compressée une fois Home Assistant reparti.
4. Démarrage de la nouvelle version (`HA_IMAGE_TAG` dans `.env`).
5. Vérification pendant 15 minutes au plus : conteneur démarré, interface joignable, bonne version,
   encore en place 60 secondes plus tard.
6. En cas d'échec : restauration de l'archive et redémarrage de l'ancienne version.

Pendant la mise à jour, la page affiche deux barres de progression, alimentées par des mesures
réelles et non par une estimation de durée :

- **Sauvegarde** : taille de l'archive déjà écrite, rapportée à la taille du dossier.
- **Mise à jour** : jalons constatés (15 % conteneur démarré, 35 % nouvelle version annoncée par
  Home Assistant, 60 % interface joignable), puis de 60 à 100 % le décompte du contrôle de
  stabilité de 60 secondes.

Le téléchargement de l'image n'a pas de barre : son avancement apparaît en nombre de couches
reçues dans le message d'état.

La sauvegarde est copiée sur le disque externe `Sauvegardes/0_Domotique/ha_update/` s'il est
branché. Les cinq dernières sauvegardes restent en local ; une plus ancienne n'est supprimée que si
elle existe sur le disque externe.

Le retour arrière automatique ne détecte que « Home Assistant ne redémarre pas ». Pour un problème
découvert plus tard :

```bash
./scripts/ha_restore.sh            # liste les sauvegardes
./scripts/ha_restore.sh <dossier>  # restaure données et version
```

## Format de `ha_release_analysis.json`

```text
version, released_at          version analysée et sa date de publication
line, line_released_at        version mensuelle (ex. 2026.9) et sa date de sortie
monitoring.start / end / days fenêtre de surveillance de 30 jours
highlights[]                  kind (new | breaking | fix), title, detail, villa
known_issues[]                severity (blocking | minor | info), title, detail, status, villa, url
recommendation                level (green | yellow | red), label, reason, after_update_checks[]
next_release                  prochaine version mensuelle attendue
sources[], history[]          pages consultées, historique des recommandations
```

Le champ `villa` dit ce que l'élément change pour cette installation précise. Tous les textes sont
affichés tels quels sur la page (échappés) : pas de HTML dedans.

## Sécurité

- `dashboard-api` n'a pas accès au socket Docker. Il ne voit de Home Assistant que le fichier
  `.HA_VERSION`, en lecture seule.
- Une demande ne peut porter que sur la dernière version connue, plus récente que la version
  installée, au format `AAAA.M.P`. L'agent revalide ce format avant d'exécuter quoi que ce soit.
- Toute personne qui peut ouvrir le dashboard voit le bouton, mais la mise à jour exige le mot de
  passe (voir plus haut). Sur le réseau local, le dashboard est servi en HTTP : le mot de passe y
  circule en clair ; par `dashboardbulle.malnoy.com`, il passe en HTTPS.
