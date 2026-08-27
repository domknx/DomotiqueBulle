#!/usr/bin/env python3
"""Assemble la page HTML interactive du bus KNX à partir de :
  - knx/scripts/report_template.html  (mise en page + logique de filtrage, avec un
    marqueur __KNX_DATA_JSON__ à la place des données)
  - knx/group_addresses/knx_data.json (généré par parse_knxproj.py)

Usage : python3 build_html_report.py [chemin_template] [chemin_json] [chemin_sortie]
Valeurs par défaut : knx/scripts/report_template.html, knx/group_addresses/knx_data.json,
                      knx/group_addresses/knx_report.html

Le fichier de sortie est autonome (données intégrées) : à publier tel quel via l'outil
Artifact pour obtenir une page hébergée et filtrable.
"""
import sys
import os
import json

DEFAULT_TEMPLATE = os.path.join('knx', 'scripts', 'report_template.html')
DEFAULT_JSON = os.path.join('knx', 'group_addresses', 'knx_data.json')
DEFAULT_OUT = os.path.join('knx', 'group_addresses', 'knx_report.html')

PLACEHOLDER = '/*__KNX_DATA_JSON__*/{}'


def main():
    template_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TEMPLATE
    json_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_JSON
    out_path = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_OUT

    with open(json_path, encoding='utf-8') as f:
        raw_json = f.read()
    json.loads(raw_json)  # valide avant d'injecter

    with open(template_path, encoding='utf-8') as f:
        template = f.read()

    if PLACEHOLDER not in template:
        raise SystemExit(f"Marqueur {PLACEHOLDER!r} introuvable dans {template_path}")

    final = template.replace(PLACEHOLDER, raw_json)

    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(final)

    print(f"-> {out_path} ({len(final)//1024} Ko)")


if __name__ == '__main__':
    main()
