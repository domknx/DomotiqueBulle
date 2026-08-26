#!/usr/bin/env python3
"""Parse un fichier .knxproj (ETS6) et génère un inventaire lisible des
adresses de groupe et des fonctions par pièce, pour le projet domotique
villa Bulle.

Usage : python3 parse_knxproj.py <chemin_vers.knxproj> <dossier_de_sortie>

Écrit :
  <dossier_de_sortie>/group_addresses.csv   (une ligne par adresse de groupe)
  <dossier_de_sortie>/functions_by_room.csv (une ligne par fonction ETS, groupée par pièce)

Ne modifie jamais le .knxproj source. Conçu pour être relancé à chaque
nouvelle version du projet ETS (voir knx/CHANGELOG_KNX.md).
"""
import sys
import os
import re
import csv
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

    # ---------- 1) Adresses de groupe (arbre GroupRange -> GroupAddress) ----------
    ga_by_id = {}

    def walk_ranges(elem, path):
        for child in elem:
            tag = local(child)
            if tag == 'GroupRanges':
                # conteneur d'enveloppe (ETS6) sans nom propre : on descend sans changer le chemin
                walk_ranges(child, path)
            elif tag == 'GroupRange':
                name = child.get('Name') or ''
                walk_ranges(child, path + [name] if name else path)
            elif tag == 'GroupAddress':
                sid = gid_short(child.get('Id'))
                raw = int(child.get('Address'))
                main, middle, sub = raw >> 11, (raw >> 8) & 0x7, raw & 0xFF
                ga_by_id[sid] = {
                    'address': f'{main}/{middle}/{sub}',
                    'raw': raw,
                    'name': child.get('Name') or '',
                    'description': child.get('Description') or '',
                    'dpt': child.get('DatapointType') or '',
                    'group_path': ' > '.join(path),
                    'rooms_function': set(),   # pièce logique (via ETS Function) -> à utiliser pour l'area HA
                    'rooms_device': set(),     # emplacement physique de l'appareil (souvent une armoire technique)
                    'devices': set(),
                    'functions': set(),
                }

    ga_root = installation.find('{*}GroupAddresses')
    if ga_root is not None:
        walk_ranges(ga_root, [])

    # ---------- 2) Appareils (Topology) + leurs GA reliées (ComObjectInstanceRef/Links) ----------
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

    # ---------- 3) Emplacements (Locations: Building/Floor/Room) + Functions par pièce ----------
    room_rows = []

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
                    'group_addresses': ', '.join(
                        ga_by_id[g]['address'] for g in ga_refs if g in ga_by_id
                    ),
                })
            elif tag == 'Space':
                name = child.get('Name') or ''
                walk_spaces(child, path + [name] if name else path)

    loc_root = installation.find('{*}Locations')
    if loc_root is not None:
        walk_spaces(loc_root, [])

    # ---------- 4) Écriture des CSV ----------
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
            w.writerow([r['room'], r['function_name'], r['function_type'], r['group_addresses']])

    # ---------- 5) Résumé ----------
    n_ga = len(ga_rows)
    n_dpt = sum(1 for r in ga_rows if r['dpt'])
    n_dev = len(dev_by_id)
    n_func = len(room_rows)
    rooms = sorted(set(r['room'] for r in room_rows if r['room']))
    print(f"Adresses de groupe      : {n_ga}  (dont {n_dpt} avec DPT explicite, {n_ga - n_dpt} sans)")
    print(f"Appareils (DeviceInstance) : {n_dev}")
    print(f"Fonctions ETS            : {n_func}, réparties sur {len(rooms)} pièces/zones")
    print()
    print(f"-> {ga_csv_path}")
    print(f"-> {func_csv_path}")


if __name__ == '__main__':
    main()
