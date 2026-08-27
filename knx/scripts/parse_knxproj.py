#!/usr/bin/env python3
"""Parse un fichier .knxproj (ETS6) et génère un inventaire lisible des
adresses de groupe et des fonctions par pièce, pour le projet domotique
villa Bulle.

Usage : python3 parse_knxproj.py <chemin_vers.knxproj> <dossier_de_sortie>

Écrit :
  <dossier_de_sortie>/group_addresses.csv    (une ligne par adresse de groupe)
  <dossier_de_sortie>/functions_by_room.csv  (une ligne par fonction ETS, groupée par pièce)
  <dossier_de_sortie>/knx_data.json          (export structuré complet, pour la vue HTML filtrable)

Ne modifie jamais le .knxproj source. Conçu pour être relancé à chaque
nouvelle version du projet ETS (voir knx/CHANGELOG_KNX.md).
"""
import sys
import os
import re
import csv
import json
import zipfile
import xml.etree.ElementTree as ET


def local(elem):
    """Nom de balise sans le préfixe de namespace XML."""
    tag = elem.tag
    return tag.split('}', 1)[1] if '}' in tag else tag


def gid_short(full_id):
    """'P-08D1-0_GA-10' -> 'GA-10' (les Links/RefId internes utilisent la forme courte)."""
    return full_id.rsplit('_', 1)[-1] if '_' in full_id else full_id


def find_project_xml_name(zf):
    names = zf.namelist()
    candidates = [n for n in names if re.match(r'^P-[0-9A-F]+/0\.xml$', n)]
    if not candidates:
        raise SystemExit("Impossible de trouver P-xxxx/0.xml dans l'archive .knxproj")
    return candidates[0]


def load_function_type_texts(zf):
    """Best-effort : Text des FunctionType (ex: FT-1 -> 'switchable light') depuis knx_master.xml."""
    texts = {}
    try:
        with zf.open('knx_master.xml') as f:
            data = f.read()
        for m in re.finditer(rb'<FunctionType Text="([^"]*)" Id="(FT-\d+)"', data):
            text, fid = m.group(1).decode('utf-8'), m.group(2).decode('utf-8')
            texts[fid] = text
    except KeyError:
        pass
    return texts


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    knxproj_path, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    with zipfile.ZipFile(knxproj_path) as zf:
        proj_xml_name = find_project_xml_name(zf)
        with zf.open(proj_xml_name) as f:
            root = ET.fromstring(f.read())
        ft_texts = load_function_type_texts(zf)

    installation = root.find('.//{*}Installation')
    if installation is None:
        raise SystemExit("Aucune balise <Installation> trouvée dans le projet.")

    # ---------- 1) Hiérarchie des GroupRange (structure logique des adresses telle que définie dans ETS) ----------
    range_tree = []

    def walk_ranges(elem, path, out_list):
        for child in elem:
            tag = local(child)
            if tag == 'GroupRanges':
                walk_ranges(child, path, out_list)
            elif tag == 'GroupRange':
                name = child.get('Name') or ''
                node = {
                    'name': name,
                    'start': int(child.get('RangeStart')),
                    'end': int(child.get('RangeEnd')),
                    'unfiltered': child.get('Unfiltered') == 'true',
                    'children': [],
                }
                out_list.append(node)
                walk_ranges(child, path + [name] if name else path, node['children'])
            elif tag == 'GroupAddress':
                pass  # traité séparément ci-dessous

    # ---------- 2) Adresses de groupe (même arbre, on capture aussi les GroupAddress cette fois) ----------
    ga_by_id = {}

    def walk_ga(elem, path):
        for child in elem:
            tag = local(child)
            if tag == 'GroupRanges':
                walk_ga(child, path)
            elif tag == 'GroupRange':
                name = child.get('Name') or ''
                walk_ga(child, path + [name] if name else path)
            elif tag == 'GroupAddress':
                sid = gid_short(child.get('Id'))
                raw = int(child.get('Address'))
                main, middle, sub = raw >> 11, (raw >> 8) & 0x7, raw & 0xFF
                ga_by_id[sid] = {
                    'id': sid,
                    'address': f'{main}/{middle}/{sub}',
                    'raw': raw,
                    'main': main,
                    'middle': middle,
                    'sub': sub,
                    'name': child.get('Name') or '',
                    'description': child.get('Description') or '',
                    'dpt': child.get('DatapointType') or '',
                    'group_path': ' > '.join(path),
                    'rooms_function': set(),
                    'rooms_device': set(),
                    'devices': set(),
                    'functions': set(),
                }

    ga_root = installation.find('{*}GroupAddresses')
    if ga_root is not None:
        walk_ranges(ga_root, [], range_tree)
        walk_ga(ga_root, [])

    # ---------- 3) Appareils (Topology) + leurs GA reliées (ComObjectInstanceRef/Links) ----------
    dev_by_id = {}
    dev_ga_links = {}
    for dev in installation.iter():
        if local(dev) == 'DeviceInstance':
            sid = gid_short(dev.get('Id'))
            dev_by_id[sid] = {
                'name': dev.get('Name') or '',
                'description': dev.get('Description') or '',
            }
            links = set()
            for cor in dev.iter():
                if local(cor) == 'ComObjectInstanceRef':
                    l = cor.get('Links')
                    if l:
                        links.update(l.split())
            dev_ga_links[sid] = links

    for dsid, links in dev_ga_links.items():
        dname = dev_by_id[dsid]['description'] or dev_by_id[dsid]['name'] or dsid
        for gasid in links:
            if gasid in ga_by_id:
                ga_by_id[gasid]['devices'].add(dname)

    # ---------- 4) Emplacements (Locations: Building/Floor/Room) + Functions par pièce ----------
    room_rows = []
    room_paths_seen = set()

    def walk_spaces(elem, path):
        for child in elem:
            tag = local(child)
            if tag == 'DeviceInstanceRef':
                dsid = gid_short(child.get('RefId'))
                for gasid in dev_ga_links.get(dsid, []):
                    if gasid in ga_by_id:
                        ga_by_id[gasid]['rooms_device'].add(' / '.join(path))
            elif tag == 'Function':
                fname = child.get('Name') or ''
                ftype = child.get('Type') or ''
                ftext = ft_texts.get(ftype, ftype)
                ga_refs = []
                for gc in child:
                    if local(gc) == 'GroupAddressRef':
                        gasid = gid_short(gc.get('RefId'))
                        ga_refs.append(gasid)
                        if gasid in ga_by_id:
                            ga_by_id[gasid]['rooms_function'].add(' / '.join(path))
                            label = f'{fname} ({ftext})' if fname else ftext
                            ga_by_id[gasid]['functions'].add(label)
                room_rows.append({
                    'room': ' / '.join(path),
                    'function_name': fname,
                    'function_type': ftext,
                    'group_addresses': [ga_by_id[g]['address'] for g in ga_refs if g in ga_by_id],
                })
                room_paths_seen.add(' / '.join(path))
            elif tag == 'Space':
                name = child.get('Name') or ''
                stype = child.get('Type') or ''
                new_path = path + [name] if name else path
                room_paths_seen.add(' / '.join(new_path))
                walk_spaces(child, new_path)

    loc_root = installation.find('{*}Locations')
    if loc_root is not None:
        walk_spaces(loc_root, [])

    # ---------- 5) Écriture des CSV (lisibles, diffables via Git) ----------
    ga_rows = sorted(ga_by_id.values(), key=lambda r: r['raw'])
    ga_csv_path = os.path.join(out_dir, 'group_addresses.csv')
    with open(ga_csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow([
            'adresse', 'nom', 'description', 'dpt', 'chemin_groupe',
            'piece_fonction', 'fonctions', 'appareils', 'emplacement_appareil',
        ])
        for r in ga_rows:
            w.writerow([
                r['address'], r['name'], r['description'], r['dpt'], r['group_path'],
                '; '.join(sorted(r['rooms_function'])), ' / '.join(sorted(r['functions'])),
                ' / '.join(sorted(r['devices'])), '; '.join(sorted(r['rooms_device'])),
            ])

    func_csv_path = os.path.join(out_dir, 'functions_by_room.csv')
    with open(func_csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['piece', 'fonction', 'type_fonction', 'adresses_groupe'])
        for r in sorted(room_rows, key=lambda x: (x['room'], x['function_name'])):
            w.writerow([r['room'], r['function_name'], r['function_type'], ', '.join(r['group_addresses'])])

    # ---------- 6) Export JSON structuré (pour la vue HTML filtrable) ----------
    json_ga_list = []
    for r in ga_rows:
        json_ga_list.append({
            'address': r['address'],
            'raw': r['raw'],
            'main': r['main'],
            'middle': r['middle'],
            'sub': r['sub'],
            'name': r['name'],
            'description': r['description'],
            'dpt': r['dpt'],
            'group_path': r['group_path'],
            'room': sorted(r['rooms_function'])[0] if r['rooms_function'] else '',
            'functions': sorted(r['functions']),
            'devices': sorted(r['devices']),
            'device_location': sorted(r['rooms_device'])[0] if r['rooms_device'] else '',
            'linked': bool(r['rooms_function'] or r['functions']),
            'device_linked': bool(r['devices']),
        })

    json_functions = []
    for r in sorted(room_rows, key=lambda x: (x['room'], x['function_name'])):
        json_functions.append({
            'room': r['room'],
            'name': r['function_name'],
            'type': r['function_type'],
            'group_addresses': r['group_addresses'],
        })

    n_ga = len(ga_rows)
    n_dpt = sum(1 for r in ga_rows if r['dpt'])
    n_linked = sum(1 for r in json_ga_list if r['linked'])
    n_device_only = sum(1 for r in json_ga_list if r['device_linked'] and not r['linked'])
    n_orphan = n_ga - n_linked - n_device_only

    data = {
        'meta': {
            'project': 'Villa Bulle',
            'generated_from': os.path.basename(knxproj_path),
            'stats': {
                'group_addresses': n_ga,
                'group_addresses_with_dpt': n_dpt,
                'group_addresses_linked_to_function': n_linked,
                'group_addresses_device_only': n_device_only,
                'group_addresses_orphan': n_orphan,
                'devices': len(dev_by_id),
                'functions': len(room_rows),
                'rooms': len({f['room'] for f in json_functions if f['room']}),
            },
        },
        'group_ranges': range_tree,
        'group_addresses': json_ga_list,
        'functions': json_functions,
    }
    json_path = os.path.join(out_dir, 'knx_data.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=None, separators=(',', ':'))

    # ---------- 7) Résumé ----------
    print(f"Adresses de groupe        : {n_ga}  (dont {n_dpt} avec DPT explicite)")
    print(f"  - liées à une Function ETS : {n_linked}")
    print(f"  - liées à un appareil seulement (pas de Function) : {n_device_only}")
    print(f"  - orphelines (aucun lien)   : {n_orphan}")
    print(f"Appareils (DeviceInstance) : {len(dev_by_id)}")
    n_rooms = len({f['room'] for f in json_functions if f['room']})
    print(f"Fonctions ETS              : {len(room_rows)}, réparties sur {n_rooms} pièces/zones")
    print()
    print(f"-> {ga_csv_path}")
    print(f"-> {func_csv_path}")
    print(f"-> {json_path}")


if __name__ == '__main__':
    main()
