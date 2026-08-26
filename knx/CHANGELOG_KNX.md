# Changelog KNX — projet ETS villa Bulle

Résumé humain de chaque import du projet ETS (`.knxproj`) dans ce dépôt. Le fichier `.knxproj` lui-même n'est pas versionné dans Git (voir `.gitignore`) — son historique complet vit dans `Backups/knx_versions/` (local) et sur le disque externe de sauvegarde. Ce changelog et les CSV dans `knx/group_addresses/` sont la trace consultable directement sur GitHub.

## 2026-08-26 — Premier import (V10.0, ETS 6.4.8718.0)

- Fichier reçu : `Villa Bulle-ETS6-V10.0_Export.knxproj` (35 Mo), renommé `villa_bulle.knxproj`.
- Interface IP KNX confirmée : Siemens N148 IP/KNX, `192.168.1.10`, IP Tunneling, port 3671.
- Script `knx/scripts/parse_knxproj.py` écrit et validé sur ce projet.
- Statistiques extraites :
  - **975 adresses de groupe** au total, dont 524 avec un DPT explicite dans ETS et 451 sans.
  - **339 adresses de groupe** effectivement rattachées à une pièce/fonction ETS ; **636 non rattachées** (probablement des adresses historiques/de test, à clarifier avec l'utilisateur avant tout nettoyage).
  - **41 appareils** (DeviceInstance) dans la topologie.
  - **59 fonctions ETS** réparties sur **19 pièces/zones**, par type : 24 éclairage commutable (*switchable light*), 20 protection solaire/volets (*sun protection*), 14 chauffage variable continu, 1 éclairage variateur (*dimmable light*).
- Livrables générés : `knx/group_addresses/group_addresses.csv` (une ligne par GA) et `knx/group_addresses/functions_by_room.csv` (une ligne par fonction ETS, groupée par pièce).
- Pas encore de génération de `knx.yaml`/entités Home Assistant à ce stade — en attente de validation de l'inventaire avec l'utilisateur et de la décision sur la cadence de déploiement (progressif vs global).
