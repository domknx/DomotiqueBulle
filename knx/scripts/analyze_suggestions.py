#!/usr/bin/env python3
"""Analyse les adresses de groupe non rattachées à une Function ETS et propose,
pour chacune, une pièce et une fonction plausibles — à valider par l'utilisateur
directement dans ETS (ce script ne modifie jamais knx_data.json ni le .knxproj).

Usage : python3 analyze_suggestions.py <knx_data.json> <suggestions.json>
"""
import sys
import json
import unicodedata
import re
from collections import Counter, defaultdict

LEGACY_DOMAINS = {'chauffage_old', 'Nouveau groupe principal'}

DOMAIN_LABEL = {
    'Lumière': 'éclairage',
    'Ouvrant Volet': 'volet roulant (protection solaire)',
    'Ouvrant Store': 'store / brise-soleil',
    'Chauffage': 'chauffage (variable en continu)',
    'Chauffage Mode': 'chauffage — mode',
    'chauffage_old': 'chauffage (ancienne plage — probablement obsolète)',
    'Prise': 'prise commandée',
    'Ventilation': 'ventilation',
    'Sécurité': 'sécurité',
    'Général': 'général / capteur',
    'Nouveau groupe principal': 'plage non nommée dans ETS (à qualifier)',
}

ROOM_TOKENS = [
    ("Bureau et Bibliothèque", "Villa Bulle / Maison principale / 1_RDC / Bureau et Bibliothèque"),
    ("Bureau et Bibliotheque", "Villa Bulle / Maison principale / 1_RDC / Bureau et Bibliothèque"),
    ("Salle de Bain invité", "Villa Bulle / Maison principale / 1_RDC / Salle de Bain invité"),
    ("Salle de Bain invite", "Villa Bulle / Maison principale / 1_RDC / Salle de Bain invité"),
    ("Salle de Bain principale", "Villa Bulle / Maison principale / 2_Etage / Salle de Bain principale"),
    ("Salle à Manger", "Villa Bulle / Maison principale / 1_RDC / Salle à Manger"),
    ("Salle a Manger", "Villa Bulle / Maison principale / 1_RDC / Salle à Manger"),
    ("Escalier Sous-Sol RDC", "Villa Bulle / Maison principale / Escalier Sous-Sol RDC"),
    ("Escalier vers RDC", "Villa Bulle / Maison principale / 0_Sous-Sol / Escalier vers RDC"),
    ("Local Technique", "Villa Bulle / Maison principale / 0_Sous-Sol / Local Technique"),
    ("Chambre Lily", "Villa Bulle / Maison principale / 2_Etage / Chambre Lily"),
    ("Chambre Léane", "Villa Bulle / Maison principale / 2_Etage / Chambre Léane"),
    ("Chambre Leane", "Villa Bulle / Maison principale / 2_Etage / Chambre Léane"),
    ("Chambre Parents", "Villa Bulle / Maison principale / 2_Etage / Chambre Parents"),
    ("Dressing", "Villa Bulle / Maison principale / 2_Etage / Dressing"),
    ("Cuisine", "Villa Bulle / Maison principale / 1_RDC / Cuisine"),
    ("Garage", "Villa Bulle / Maison principale / 0_Sous-Sol / Garage"),
    ("Entrée", "Villa Bulle / Maison principale / 0_Sous-Sol / Entrée"),
    ("Entree", "Villa Bulle / Maison principale / 0_Sous-Sol / Entrée"),
    ("Parking", "Villa Bulle / Maison principale / 4_Extérieur / Parking"),
    ("Salon", "Villa Bulle / Maison principale / 1_RDC / Salon"),
    ("Bureau", None),
    ("Salle de Bain", None),
    ("Escalier", None),
    ("Studio", "Studio (zone non déclarée dans ETS)"),
    ("Etage", "Villa Bulle / Maison principale / 2_Etage"),
    ("RDC", "Villa Bulle / Maison principale / 1_RDC"),
    ("Sous-Sol", "Villa Bulle / Maison principale / 0_Sous-Sol"),
    ("Sous Sol", "Villa Bulle / Maison principale / 0_Sous-Sol"),
    ("Extérieur", "Villa Bulle / Maison principale / 4_Extérieur"),
    ("Exterieur", "Villa Bulle / Maison principale / 4_Extérieur"),
]
ROOM_TOKENS.sort(key=lambda t: -len(t[0]))

SUB_LIEU_TOKENS = [
    "Salle à Manger", "Salle a Manger", "Chambre", "Salon", "Cuisine",
    "Reserve", "Réserve", "Entrée", "Entree", "Terrasse", "Garage",
]
SUB_LIEU_TOKENS.sort(key=lambda t: -len(t))


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))


def norm(s):
    return strip_accents(s).lower()


def find_room(name):
    n = norm(name)
    for token, room in ROOM_TOKENS:
        if norm(token) in n:
            if room is None:
                return None, token, True
            if token == "Studio":
                for sub in SUB_LIEU_TOKENS:
                    if norm(sub) in n and norm(sub) != norm(token):
                        return f"Studio / {sub}", f"Studio + {sub}", False
                return room, token, False
            return room, token, False
    return None, None, False


def room_leaf(room_label):
    if not room_label:
        return '?'
    return room_label.rstrip(')').split('(')[0].strip().split(' / ')[-1]


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    data = json.load(open(sys.argv[1], encoding='utf-8'))
    gas = data['group_addresses']
    unlinked = [g for g in gas if not g['linked']]

    clusters = defaultdict(list)
    for g in unlinked:
        domain = (g['group_path'] or '').split(' > ')[0] or 'Sans domaine'
        clusters[(domain, g['main'], g['sub'])].append(g)

    out_clusters = []
    for (domain, main, sub), members in clusters.items():
        members = sorted(members, key=lambda g: g['middle'])
        room_guesses = []
        ambiguous_any = False
        matched_tokens = set()
        for g in members:
            room, token, ambig = find_room(g['name'])
            room_guesses.append(room)
            if ambig:
                ambiguous_any = True
                matched_tokens.add(token)
            elif token:
                matched_tokens.add(token)

        non_null = [r for r in room_guesses if r]
        room_counter = Counter(non_null)
        proposed_room = room_counter.most_common(1)[0][0] if room_counter else None
        consistent = len(room_counter) <= 1

        legacy = domain in LEGACY_DOMAINS

        if legacy:
            confidence = 'faible'
        elif proposed_room and consistent and not ambiguous_any:
            confidence = 'haute'
        elif proposed_room and (ambiguous_any or not consistent):
            confidence = 'moyenne'
        else:
            confidence = 'faible'

        domain_label = DOMAIN_LABEL.get(domain, domain)
        proposed_function = f"{room_leaf(proposed_room)} — {domain_label}"

        roles = sorted({(g['group_path'].split(' > ')[-1] if ' > ' in g['group_path'] else g['group_path']) for g in members})

        out_clusters.append({
            'domain': domain,
            'main': main,
            'sub': sub,
            'legacy': legacy,
            'addresses': [g['address'] for g in members],
            'members': [{'address': g['address'], 'name': g['name'], 'dpt': g['dpt']} for g in members],
            'roles': roles,
            'matched_tokens': sorted(matched_tokens),
            'ambiguous_room': ambiguous_any,
            'consistent_room': consistent,
            'proposed_room': proposed_room,
            'proposed_function': proposed_function,
            'confidence': confidence,
        })

    conf_order = {'haute': 0, 'moyenne': 1, 'faible': 2}
    out_clusters.sort(key=lambda c: (conf_order[c['confidence']], c['domain'], c['main'], c['sub']))

    stats = {
        'total_group_addresses': len(gas),
        'total_unlinked': len(unlinked),
        'total_clusters': len(out_clusters),
        'clusters_haute': sum(1 for c in out_clusters if c['confidence'] == 'haute'),
        'clusters_moyenne': sum(1 for c in out_clusters if c['confidence'] == 'moyenne'),
        'clusters_faible': sum(1 for c in out_clusters if c['confidence'] == 'faible'),
        'addresses_haute': sum(len(c['addresses']) for c in out_clusters if c['confidence'] == 'haute'),
        'addresses_moyenne': sum(len(c['addresses']) for c in out_clusters if c['confidence'] == 'moyenne'),
        'addresses_faible': sum(len(c['addresses']) for c in out_clusters if c['confidence'] == 'faible'),
    }

    out = {'generated_from': data['meta'].get('generated_from', ''), 'stats': stats, 'clusters': out_clusters}
    with open(sys.argv[2], 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))

    print(f"Adresses non rattachées : {stats['total_unlinked']} / {stats['total_group_addresses']}")
    print(f"Regroupées en {stats['total_clusters']} propositions :")
    print(f"  - confiance haute   : {stats['clusters_haute']} propositions ({stats['addresses_haute']} adresses)")
    print(f"  - confiance moyenne : {stats['clusters_moyenne']} propositions ({stats['addresses_moyenne']} adresses)")
    print(f"  - confiance faible  : {stats['clusters_faible']} propositions ({stats['addresses_faible']} adresses)")
    print(f"-> {sys.argv[2]}")


if __name__ == '__main__':
    main()
