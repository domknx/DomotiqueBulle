"""Définit ou change le mot de passe du bouton « Sauvegarder et mettre à jour » (page Version).

Usage, dans le Terminal du Mac mini :

    docker exec -it dashboard-api python -m app.set_password

Le mot de passe est demandé deux fois, sans affichage. Seule son empreinte salée est écrite dans
dashboard/version/update_password.hash (hors Git) ; le blocage en cours après des essais ratés
est levé.
"""

from __future__ import annotations

import getpass
import sys

from . import ha_version


def main() -> int:
    first = getpass.getpass("Nouveau mot de passe de mise à jour : ")
    if len(first) < 6:
        print("Mot de passe trop court (6 caractères au minimum). Rien n'a été modifié.", file=sys.stderr)
        return 1
    if getpass.getpass("Confirmer : ") != first:
        print("Les deux saisies diffèrent. Rien n'a été modifié.", file=sys.stderr)
        return 1
    ha_version._write_atomic(ha_version.PASSWORD_PATH, ha_version.hash_password(first) + "\n")
    try:
        ha_version.AUTH_STATE_PATH.unlink()
    except OSError:
        pass
    print("Mot de passe enregistré.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
