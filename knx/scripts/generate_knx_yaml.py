#!/usr/bin/env python3
"""Génère knx.yaml (entités Home Assistant) à partir des Functions ETS
confirmées dans knx_data.json — voir knx/scripts/parse_knxproj.py pour la
provenance des données.

Règles de mapping (validées manuellement sur le pilote Chambre Léane le
27.08.2026, voir knx_integration.md dans la mémoire projet) :
  - switchable light / dimmable light -> light (regroupé par sous-groupe
    "instance" pour gérer les Functions à plusieurs circuits)
  - sun protection -> cover (ignore les commandes groupées "tous" ;
    Volet -> device_class shutter, Store -> device_class blind, avec
    gestion des lamelles si présentes)
  - heating (continuous variable) -> climate, consigne en température
    absolue (décision utilisateur du 27.08.2026)

Chambre Léane est explicitement exclue (déjà déployée manuellement) pour
ne pas recréer les entités déjà validées avec un YAML légèrement différent.

Usage : python3 generate_knx_yaml.py <knx_data.json> <sortie.yaml>
Écrit aussi <sortie.yaml>.report.txt (ce qui a été généré / ignoré et pourquoi).
"""
import sys
import json

ROOM_TO_AREA = {
    'Entrée': 'entree',
    'Escalier vers RDC': 'escalier_vers_rdc',
    'Garage': 'garage',
    'Local Technique': 'local_technique',
    'Bureau et Bibliothèque': 'bureau_et_bibliotheque',
    'Cuisine': 'cuisine',
    'Salle de Bain invité': 'salle_de_bain_invite',
    'Salle à Manger': 'salle_a_manger',
    'Salon': 'salon',
    'Bureau': 'bureau',
    'Chambre Lily': 'chambre_lily',
    'Chambre Léane': 'chambre_leane',
    'Chambre Parents': 'chambre_parents',
    'Dressing': 'dressing',
    'Salle de Bain principale': 'salle_de_bain_principale',
    'Parking': 'parking',
    'Escalier Sous-Sol RDC': 'escalier_sous_sol_rdc',
}

COVER_ROLE_MAP = {
    'volet ouvert-fermé': 'move_long_address',
    'volet stop': 'stop_address',
    'volet position absolue': 'position_address',
    'volet statut position actuelle': 'position_state_address',
    'store ouvert-fermé': 'move_long_address',
    'store stop': 'stop_address',
    'store position absolue': 'position_address',
    'store statut position actuelle': 'position_state_address',
    'store position absolue lamelles': 'angle_address',
    'store statut position lamelles actuelle': 'angle_state_address',
}

CLIMATE_ROLE_MAP = {
    'chauffage température actuelle': 'temperature_address',
    'chauffage température cible': 'target_temperature_address',
    'chauffage température cible actuelle': 'target_temperature_state_address',
    'chauffage position valve': 'command_value_state_address',
    'chauffage statut commande chauffage': 'active_state_address',
    'chauffage mode sélection': 'operation_mode_address',
}


def leaf_room(path):
    return path.split(' / ')[-1]


def clean(s):
    return ' '.join(str(s).split())


def yaml_str(s):
    s = clean(s).replace('"', '\\"')
    return f'"{s}"'


def main():
    data_path, out_path = sys.argv[1], sys.argv[2]
    data = json.load(open(data_path, encoding='utf-8'))
    gas = {g['address']: g for g in data['group_addresses']}

    lights, covers, climates, skipped = [], [], [], []

    for f in data['functions']:
        room_path = f['room']
        leaf = leaf_room(room_path)
        if leaf == 'Chambre Léane':
            continue
        area = ROOM_TO_AREA.get(leaf)
        if not f['group_addresses']:
            skipped.append((f['type'], room_path, f['name'], 'Function ETS vide (aucune adresse de groupe)'))
            continue

        if f['type'] in ('switchable light', 'dimmable light'):
            by_sub = {}
            for a in f['group_addresses']:
                g = gas.get(a)
                if g:
                    by_sub.setdefault(g['sub'], []).append((a, g))
            if not by_sub:
                skipped.append((f['type'], room_path, f['name'], 'aucune adresse résolue dans knx_data.json'))
                continue
            for sub, items in sorted(by_sub.items()):
                addr = state = label = None
                for a, g in items:
                    role = g['group_path'].split(' > ')[-1].strip()
                    if role == 'On-Off':
                        addr, label = a, g['name']
                    elif role == 'Etat On-Off':
                        state = a
                if not addr:
                    skipped.append((f['type'], room_path, f"{f['name']} (sous-groupe {sub})", "pas d'adresse de commande On-Off"))
                    continue
                base = label.rsplit(' - ', 1)[0] if label and ' - ' in label else (label or f['name'])
                name = base if leaf.lower() in base.lower() else f"{leaf} - {base}"
                entry = {'name': name, 'address': addr, 'area': area}
                if state:
                    entry['state_address'] = state
                lights.append(entry)

        elif f['type'] == 'sun protection':
            if 'tous' in f['name'].lower():
                skipped.append((f['type'], room_path, f['name'], 'commande groupée "tous" (agrégateur, pas de retour de position) — non exposée'))
                continue
            fields, domain_top = {}, None
            for a in f['group_addresses']:
                g = gas.get(a)
                if not g:
                    continue
                domain_top = g['group_path'].split(' > ')[0]
                role = g['group_path'].split(' > ')[-1].strip().lower()
                field = COVER_ROLE_MAP.get(role)
                if field:
                    fields[field] = a
            if 'move_long_address' not in fields:
                skipped.append((f['type'], room_path, f['name'], 'pas de commande Ouvert-Fermé exploitable'))
                continue
            name = f['name'] if leaf.lower() in f['name'].lower() else f"{leaf} - {f['name']}"
            device_class = 'shutter' if domain_top == 'Ouvrant Volet' else ('blind' if domain_top == 'Ouvrant Store' else None)
            entry = {'name': name, 'area': area, **fields}
            if device_class:
                entry['device_class'] = device_class
            covers.append(entry)

        elif f['type'] == 'heating (continuous variable)':
            fields = {}
            for a in f['group_addresses']:
                g = gas.get(a)
                if not g:
                    continue
                role = g['group_path'].split(' > ')[-1].strip().lower()
                field = CLIMATE_ROLE_MAP.get(role)
                if field:
                    fields[field] = a
            if 'temperature_address' not in fields or 'target_temperature_address' not in fields:
                skipped.append((f['type'], room_path, f['name'], 'pas assez de champs exploitables (température actuelle et/ou cible manquante) — Function ETS probablement incomplète, à vérifier'))
                continue
            if 'target_temperature_state_address' not in fields:
                fields['target_temperature_state_address'] = fields['target_temperature_address']
            climates.append({'room_path': room_path, 'leaf': leaf, 'area': area, 'func_name': f['name'], **fields, 'min_temp': 15, 'max_temp': 26})

        else:
            skipped.append((f['type'], room_path, f['name'], f"type de fonction non géré par ce générateur ({f['type']})"))

    # ---- disambiguation des noms climate (plusieurs zones de chauffage dans une même pièce) ----
    from collections import Counter
    room_counts = Counter(c['leaf'] for c in climates)
    for c in climates:
        if room_counts[c['leaf']] > 1:
            suffix = c['func_name']
            for prefix in ('chauffage ', 'Chauffage '):
                if suffix.startswith(prefix):
                    suffix = suffix[len(prefix):]
            c['name'] = f"{c['leaf']} - {suffix}".strip()
        else:
            c['name'] = c['leaf']

    # Détection de doublons d'adresse physique (même adresse KNX utilisée par
    # deux Functions ETS différentes = vraie erreur de configuration ETS, pas
    # un bug du générateur) — on garde la première occurrence rencontrée et on
    # signale la seconde comme ignorée, pour que l'utilisateur corrige dans ETS
    # lequel des deux libellés / quelle pièce est la bonne.
    def dedup_by_key(items, key, kind_label):
        seen, kept = {}, []
        for e in items:
            k = e.get(key)
            if k and k in seen:
                skipped.append((kind_label, e.get('area', '?'), e['name'],
                    f"adresse {k} déjà utilisée par l'entité générée \"{seen[k]}\" "
                    f"(Function ETS différente) — adresse de groupe physique partagée "
                    f"entre deux Functions ETS, à corriger dans ETS"))
                continue
            if k:
                seen[k] = e['name']
            kept.append(e)
        return kept

    lights = dedup_by_key(lights, 'address', 'switchable/dimmable light')
    covers = dedup_by_key(covers, 'move_long_address', 'sun protection')
    climates = dedup_by_key(climates, 'temperature_address', 'heating (continuous variable)')

    # ---- écriture YAML ----
    out = []
    out.append('# ---------------------------------------------------------------------------')
    out.append('# Entités KNX générées automatiquement (voir knx/scripts/generate_knx_yaml.py).')
    out.append("# Chambre Léane n'est PAS ici : pilote déployé manuellement, laissé tel quel.")
    out.append('# ---------------------------------------------------------------------------')
    out.append('')
    out.append('light:')
    for e in lights:
        out.append(f"  - name: {yaml_str(e['name'])}")
        out.append(f"    address: {yaml_str(e['address'])}")
        if 'state_address' in e:
            out.append(f"    state_address: {yaml_str(e['state_address'])}")
    out.append('')
    out.append('cover:')
    for e in covers:
        out.append(f"  - name: {yaml_str(e['name'])}")
        for k in ('move_long_address', 'stop_address', 'position_address', 'position_state_address', 'angle_address', 'angle_state_address'):
            if k in e:
                out.append(f"    {k}: {yaml_str(e[k])}")
        if 'device_class' in e:
            out.append(f"    device_class: {e['device_class']}")
    out.append('')
    out.append('climate:')
    for e in climates:
        out.append(f"  - name: {yaml_str(e['name'])}")
        for k in ('temperature_address', 'target_temperature_address', 'target_temperature_state_address',
                  'command_value_state_address', 'active_state_address', 'operation_mode_address'):
            if k in e:
                out.append(f"    {k}: {yaml_str(e[k])}")
        out.append(f"    min_temp: {e['min_temp']}")
        out.append(f"    max_temp: {e['max_temp']}")
    out.append('')

    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out))

    # ---- rapport ----
    rep = []
    rep.append(f"Générées : {len(lights)} lumières, {len(covers)} volets/stores, {len(climates)} chauffages")
    rep.append(f"Ignorées : {len(skipped)}")
    rep.append('')
    for kind, room, name, reason in skipped:
        rep.append(f"  [{kind}] {room} | {name}\n      -> {reason}")
    rep.append('')
    rep.append('Areas utilisées (nom pièce -> area_id) :')
    for room, area in sorted(ROOM_TO_AREA.items()):
        rep.append(f"  {room} -> {area}")
    with open(out_path + '.report.txt', 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(rep))

    print('\n'.join(rep[:3]))
    print(f"-> {out_path}")
    print(f"-> {out_path}.report.txt")
    mapping = {'light': lights, 'cover': covers, 'climate': climates}
    with open(out_path + '.entities.json', 'w', encoding='utf-8') as fh:
        json.dump(mapping, fh, ensure_ascii=False)


if __name__ == '__main__':
    main()
