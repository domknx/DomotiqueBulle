# -*- coding: utf-8 -*-
"""Schéma graphique unique de l'architecture — vue d'ensemble statique,
regroupée par domaine fonctionnel (pas par réseau Docker), dans l'esprit
d'une infographie technique plutôt que d'un graphe automatique. Remplace
l'ancien système macro/détail/popup : un seul SVG, réutilisé en haut du
README et dans la vue Architecture logicielle.

Coordonnées calées à la main sur une grille — couleurs par domaine via
var(--token), connecteurs en coude routés par couloirs vérifiés libres,
labels sur fond opaque dessinés en dernier — mais sans hiérarchie de
navigation : tout est visible d'un coup, organisé en cadres de domaine à
l'intérieur d'un grand cadre « Mac mini », avec le bus KNX physique en
dehors (pas un service Docker) et les dépendances externes (Tesla,
Open-Meteo) en marge."""

from architecture_data import SERVICES, EXTERNALS, DEPS, CATEGORIES, KNX

CATEGORIES_BY_ID = {c['id']: c for c in CATEGORIES}


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


# ---------------------------------------------------------------- geometry

CANVAS_W = 1840
CANVAS_H = 1300

# cadres de domaine (x, y, w, h) — à l'intérieur du cadre Mac mini sauf acces (au-dessus)
FRAMES = {
    'acces':      dict(x=20,  y=120, w=1600, h=120),
    'domotique':  dict(x=380, y=310, w=280,  h=120),
    'documentation': dict(x=700, y=310, w=260, h=120),
    'monitoring': dict(x=380, y=460, w=1220, h=150),
    'dashboard':  dict(x=380, y=650, w=380,  h=520),
    'vehicule':   dict(x=800, y=650, w=800,  h=270),
}
MAC_FRAME = dict(x=340, y=270, w=1280, h=970)
KNX_FRAME = dict(x=20, y=250, w=300, h=110)

NODE_W, NODE_H = 200, 64

NODES = {
    # -- extérieur --
    'USER':       dict(x=40,   y=30, w=240, h=58),
    'TESLACLOUD': dict(x=1460, y=30, w=240, h=58),
    'OPENMETEO':  dict(x=440,  y=1210, w=260, h=56),
    # -- accès --
    'cloudflared': dict(x=700, y=155, w=220, h=60),
    # -- domotique --
    'homeassistant': dict(x=400, y=350, w=240, h=64),
    # -- documentation --
    'doc-knx': dict(x=720, y=350, w=220, h=64),
    # -- monitoring --
    'prometheus':      dict(x=400,  y=510, w=200, h=64),
    'victoriametrics': dict(x=620,  y=510, w=200, h=64),
    'grafana':         dict(x=1380, y=510, w=200, h=64),
    # -- dashboard --
    'glasshome':       dict(x=400, y=690, w=340, h=60),
    'tunet':           dict(x=420, y=800, w=300, h=56),
    'dashboard-proto': dict(x=400, y=910, w=340, h=56),
    'dashboard-api':   dict(x=400, y=990, w=340, h=56),
    'dashboard-web':   dict(x=400, y=1070, w=340, h=56),
    # -- véhicule --
    'tesla-key':           dict(x=820,  y=690, w=200, h=64),
    'teslamate':           dict(x=1360, y=690, w=200, h=64),
    'teslamate-db':        dict(x=1140, y=790, w=200, h=64),
    'teslamate-mosquitto': dict(x=1360, y=790, w=220, h=64),
}
TUNET_SUBFRAME = dict(x=400, y=780, w=340, h=96)

KNX_NODE = dict(x=20, y=250, w=300, h=110)


def anchor(box, side, offset=0.0):
    x, y, w, h = box['x'], box['y'], box['w'], box['h']
    pts = {'top': (x + w / 2, y), 'bottom': (x + w / 2, y + h),
           'left': (x, y + h / 2), 'right': (x + w, y + h / 2)}
    px, py = pts[side]
    if side in ('top', 'bottom'):
        return (px + offset, py)
    return (px, py + offset)


def path_d(pts):
    return 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)


def elbow(a_pt, b_pt, bend):
    """Coude à 2 segments : de a_pt, jog jusqu'à `bend` (soit 'h' = passe par
    (b.x, a.y), soit 'v' = passe par (a.x, b.y)), puis vers b_pt."""
    if bend == 'h':
        mid = (b_pt[0], a_pt[1])
    else:
        mid = (a_pt[0], b_pt[1])
    return [a_pt, mid, b_pt]


def elbow2(a_pt, mid_x, b_pt):
    """4 points : sort de a_pt à l'horizontale/verticale jusqu'à mid_x, longe
    ce couloir vertical, puis rejoint b_pt — pour contourner un cadre entre
    les deux."""
    return [a_pt, (mid_x, a_pt[1]), (mid_x, b_pt[1]), b_pt]


def label_anchor(pts, bias=0.5):
    if len(pts) == 2:
        (x1, y1), (x2, y2) = pts
        return (x1 + (x2 - x1) * bias, y1 + (y2 - y1) * bias)
    # segment médian du chemin (le plus long, en général le "couloir")
    mid_i = len(pts) // 2
    (x1, y1) = pts[mid_i - 1]
    (x2, y2) = pts[mid_i]
    if abs(x2 - x1) >= abs(y2 - y1):
        return (x1 + (x2 - x1) * bias, y1)
    return (x1, y1 + (y2 - y1) * bias)


def render_arrow_defs():
    out = ['<defs>']
    for token in ['ambre', 'glacier', 'mousse', 'cuivre', 'ink-faint']:
        out.append(
            f'<marker id="ov-arr-{token}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 Z" fill="var(--{token})"/></marker>'
        )
    out.append('</defs>')
    return '\n'.join(out)


def render_edge_line(pts, color_token, dashed=False):
    dash = ' stroke-dasharray="5 4"' if dashed else ''
    return f'<path d="{path_d(pts)}" fill="none" stroke="var(--{color_token})" stroke-width="1.6"{dash} marker-end="url(#ov-arr-{color_token})"/>'


def render_edge_label(pts, label, bias=0.5):
    if not label:
        return ''
    lx, ly = label_anchor(pts, bias)
    w = len(label) * 5.7 + 10
    return (
        f'<rect x="{lx-w/2:.1f}" y="{ly-9:.1f}" width="{w:.1f}" height="15" rx="3" fill="var(--bg)" stroke="var(--border)" stroke-width="0.6"/>'
        f'<text x="{lx:.1f}" y="{ly+3:.1f}" text-anchor="middle" class="ov-edge">{esc(label)}</text>'
    )


def render_frame(box, title, color, dashed=False, sub=None):
    dash = ' stroke-dasharray="6 5"' if dashed else ''
    x, y, w, h = box['x'], box['y'], box['w'], box['h']
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="var(--surface-2)" '
        f'fill-opacity="0.5" stroke="var(--{color})" stroke-width="1.3" stroke-opacity="0.55"{dash}/>',
        f'<text x="{x+16}" y="{y+24}" class="ov-frame-title" fill="var(--{color})">{esc(title)}</text>',
    ]
    if sub:
        out.append(f'<text x="{x+16}" y="{y+40}" class="ov-frame-sub">{esc(sub)}</text>')
    return '\n'.join(out)


def render_node(node_id):
    n = NODES[node_id]
    svc = SERVICES.get(node_id)
    x, y, w, h = n['x'], n['y'], n['w'], n['h']
    if svc:
        color = CATEGORIES_BY_ID[svc['category']]['color']
        planned = svc.get('planned', False)
        title, sub = svc['title'], svc['sub']
    else:
        color = 'ink-faint'
        planned = False
        title, sub = node_id, ''
    dash = ' stroke-dasharray="4 4"' if planned else ''
    label = title + (' — prévu' if planned else '')
    return (
        f'<g role="img" aria-label="{esc(label)}{(" — " + sub) if sub else ""}">'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="var(--surface)" stroke="var(--{color})" stroke-width="1.8"{dash}/>'
        f'<text x="{x+w/2}" y="{y+h/2 - (2 if sub else -5)}" text-anchor="middle" class="ov-title">{esc(title)}</text>'
        + (f'<text x="{x+w/2}" y="{y+h/2+15}" text-anchor="middle" class="ov-sub">{esc(sub)}</text>' if sub else '')
        + '</g>'
    )


def render_external(node_id, title, sub):
    n = NODES[node_id]
    x, y, w, h = n['x'], n['y'], n['w'], n['h']
    return (
        f'<g>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="none" stroke="var(--ink-faint)" stroke-width="1.3" stroke-dasharray="2 3"/>'
        f'<text x="{x+w/2}" y="{y+h/2-2}" text-anchor="middle" class="ov-ext-title">{esc(title)}</text>'
        f'<text x="{x+w/2}" y="{y+h/2+13}" text-anchor="middle" class="ov-ext-sub">{esc(sub)}</text>'
        f'</g>'
    )


def render_knx():
    b = KNX_NODE
    x, y, w, h = b['x'], b['y'], b['w'], b['h']
    return (
        f'<g role="img" aria-label="{esc(KNX["title"])} — {esc(KNX["sub"])} — {esc(KNX["stats"])}">'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="var(--surface)" stroke="var(--ambre)" stroke-width="1.6" stroke-dasharray="3 3"/>'
        f'<text x="{x+18}" y="{y+26}" class="ov-title" text-anchor="start">{esc(KNX["title"])}</text>'
        f'<text x="{x+18}" y="{y+44}" class="ov-sub" text-anchor="start">{esc(KNX["sub"])}</text>'
        f'<text x="{x+18}" y="{y+62}" class="ov-knx-stats" text-anchor="start">{esc(KNX["stats"])}</text>'
        f'<text x="{x+18}" y="{y+90}" class="ov-knx-note" text-anchor="start">Physique — hors Docker</text>'
        f'</g>'
    )


def render_mac_frame():
    b = MAC_FRAME
    x, y, w, h = b['x'], b['y'], b['w'], b['h']
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="none" '
        f'stroke="var(--ink-faint)" stroke-width="1.4" stroke-dasharray="2 6"/>'
        f'<text x="{x+w/2}" y="{y-14}" text-anchor="middle" class="ov-mac-label">Mac mini — hôte Docker (domotique_net)</text>'
    )


def spread_offsets(n, span_cap):
    if n <= 1:
        return [0.0]
    span = min(span_cap, (n - 1) * 60)
    step = span / (n - 1)
    return [-span / 2 + k * step for k in range(n)]


# ------------------------------------------------------------- edge routing
# Couloirs verticaux vérifiés libres de tout cadre, utilisés pour contourner
# les cadres de domaine plutôt que de tracer une diagonale qui les traverse.
GAP_ROW_A_TOP = 293       # entre le haut du cadre Mac mini (270) et la rangée A (310)
GAP_ROW_A_B = 452         # entre la rangée A (bas 430) et la rangée B (460) — sous-couloir haut
GAP_ROW_A_B_2 = 434       # même bande (430-460), sous-couloir bas — deux dépendances distinctes
                          # partagent cette bande (dashboard-api->HA, HA->TESLACLOUD) : décalées de
                          # 18px pour rester deux lignes parallèles lisibles plutôt qu'une seule.
GAP_ROW_B_C = 636         # entre la rangée B (bas 610) et la rangée C (650)
# couloir gauche : entre le bord du cadre Mac mini (340) et les cadres de
# domaine (380) — PAS le couloir tout à gauche (occupé par le bloc KNX,
# x=20-320) pour éviter de le traverser.
LANE_LEFT = 360
# couloir droit : entre le bord du cadre Mac mini (1620) et le bord du canevas
# (1740) — 4 lignes distinctes (rangées de 25px) pour que les 4 dépendances
# qui l'empruntent restent des lignes parallèles lisibles plutôt qu'un
# faisceau confondu.
LANE_RIGHT_1 = 1630          # dashboard-api -> Home Assistant (WebSocket, prévu)
LANE_RIGHT_2 = 1655          # Home Assistant -> Tesla Fleet API
LANE_RIGHT_3 = 1680          # TeslaMate -> Tesla Fleet API
LANE_RIGHT_TESLAKEY = 1705   # cloudflared -> tesla-key (vehiculebulle)


def build_edges():
    """Construit la liste des chemins à dessiner : (pts, color, label, planned, bias)."""
    edges = []

    def add(pts, color, label=None, planned=False, bias=0.5):
        edges.append((pts, color, label, planned, bias))

    # USER -> cloudflared
    add([anchor(NODES['USER'], 'bottom'), anchor(NODES['cloudflared'], 'top')], 'ambre', 'HTTPS')

    # cloudflared fan-out (accès distant) — chacune via le couloir au-dessus
    # de la rangée A (y≈293) pour ne traverser aucun cadre de domaine.
    cf_bottom = anchor(NODES['cloudflared'], 'bottom')
    fanout = [
        ('homeassistant', 'domotiquebulle'),
        ('doc-knx', 'docbulle 🔒'),
        ('grafana', 'grafanabulle'),
        ('tesla-key', 'vehiculebulle'),
        ('tunet', 'visubulle'),
        ('dashboard-proto', 'dashboardbulle'),
    ]
    cf_left = anchor(NODES['cloudflared'], 'left')
    # tunet / dashboard-proto / glasshome->HA partagent le couloir gauche —
    # décalées en x (lignes parallèles) ET en hauteur de label pour rester lisibles.
    LANE_GHOME = LANE_LEFT - 12
    LANE_TUNET = LANE_LEFT
    LANE_DPROTO = LANE_LEFT + 12
    for target, hostlabel in fanout:
        tgt = NODES[target]
        if target in ('homeassistant', 'doc-knx', 'grafana'):
            # rangées A/B : on descend jusqu'au couloir au-dessus de la rangée A,
            # on file à la bonne x, puis on entre par le haut — jamais besoin de
            # traverser un autre cadre puisque ce couloir est libre sur toute sa largeur.
            top_pt = anchor(tgt, 'top')
            pts = [cf_bottom, (cf_bottom[0], GAP_ROW_A_TOP), (top_pt[0], GAP_ROW_A_TOP), top_pt]
            add(pts, 'ambre', hostlabel)
        elif target == 'tesla-key':
            # rangée C, colonne véhicule : couloir droit dédié (hors cadres), entrée par le haut
            top_pt = anchor(tgt, 'top')
            pts = [cf_bottom, (LANE_RIGHT_TESLAKEY, cf_bottom[1] + 10), (LANE_RIGHT_TESLAKEY, GAP_ROW_B_C), (top_pt[0], GAP_ROW_B_C), top_pt]
            add(pts, 'ambre', hostlabel, bias=0.304)
        else:
            # tunet / dashboard-proto : cadre dashboard, colonne gauche — couloir gauche dédié
            lane = LANE_TUNET if target == 'tunet' else LANE_DPROTO
            side_pt = anchor(tgt, 'left')
            pts = [cf_left, (lane, cf_left[1]), (lane, side_pt[1]), side_pt]
            add(pts, 'ambre', hostlabel, bias=0.9)

    # KNX -> Home Assistant (physique, hors Docker)
    knx_right = anchor(KNX_NODE, 'right', offset=-25)
    ha_top = anchor(NODES['homeassistant'], 'top')
    add([knx_right, (knx_right[0] + 40, knx_right[1]), (ha_top[0], knx_right[1]), ha_top], 'ambre', 'bus KNX filaire')

    # Domotique -> Monitoring
    add([anchor(NODES['homeassistant'], 'bottom'), anchor(NODES['prometheus'], 'top')], 'ambre', '/api/prometheus')
    add([anchor(NODES['prometheus'], 'right'), anchor(NODES['victoriametrics'], 'left')], 'glacier', 'remote_write')
    add(elbow2(anchor(NODES['victoriametrics'], 'right'), 1000, anchor(NODES['grafana'], 'left')), 'glacier', 'datasource VictoriaMetrics')

    # Véhicule interne
    add(elbow2(anchor(NODES['tesla-key'], 'right'), 1250, anchor(NODES['teslamate'], 'left')), 'cuivre')
    add([anchor(NODES['teslamate'], 'bottom'), anchor(NODES['teslamate-mosquitto'], 'top')], 'cuivre')
    add(elbow2(anchor(NODES['teslamate'], 'bottom'), 1240, anchor(NODES['teslamate-db'], 'top')), 'cuivre')
    add(elbow2(anchor(NODES['teslamate-db'], 'left'), 1100, anchor(NODES['grafana'], 'bottom')), 'cuivre', 'datasource TeslaMate')

    # Dashboard interne
    add([anchor(NODES['glasshome'], 'bottom'), anchor(NODES['tunet'], 'top')], 'mousse')
    add([anchor(NODES['tunet'], 'bottom'), anchor(NODES['dashboard-proto'], 'top')], 'mousse')
    add([anchor(NODES['dashboard-proto'], 'bottom'), anchor(NODES['dashboard-api'], 'top')], 'mousse', 'proxy /api/, interne')
    add([anchor(NODES['dashboard-api'], 'bottom'), anchor(NODES['dashboard-web'], 'top')], 'ink-faint', 'remplacera dashboard-proto', planned=True)
    add([anchor(NODES['dashboard-api'], 'bottom'), anchor(NODES['OPENMETEO'], 'top')], 'mousse', 'proxy météo')
    add(elbow2(anchor(NODES['glasshome'], 'top'), LANE_GHOME, anchor(NODES['homeassistant'], 'bottom')), 'ambre', 'jeton longue durée')

    # dashboard-api -> Home Assistant (WebSocket, prévu) — sort par la droite,
    # remonte le couloir droit hors cadre, rentre par le couloir A/B (libre
    # sur toute sa largeur) pour ne traverser ni Véhicule ni Documentation.
    dapi_right = anchor(NODES['dashboard-api'], 'right')
    ha_bottom = anchor(NODES['homeassistant'], 'bottom')
    add([dapi_right, (LANE_RIGHT_1, dapi_right[1]), (LANE_RIGHT_1, GAP_ROW_A_B), (ha_bottom[0], GAP_ROW_A_B), ha_bottom],
        'ink-faint', 'WebSocket, jeton longue durée (prévu)', planned=True, bias=0.481)

    # Vers Tesla Fleet API (droite, hors cadre) — 2 dépendances distinctes,
    # entrées décalées sur le bord bas de TESLACLOUD pour ne pas se chevaucher,
    # et chacune sur son propre couloir/bias pour que les 4 labels du couloir
    # droit (cette paire + les deux ci-dessus) restent lisibles.
    tc = NODES['TESLACLOUD']
    off1, off2 = spread_offsets(2, 100)
    # homeassistant -> TESLACLOUD : ne sort PAS par le côté droit de Home
    # Assistant (même bande que la rangée A — traverserait le cadre
    # Documentation / le nœud doc-knx) : descend d'abord jusqu'au couloir A/B
    # (sous-décalé à 436, distinct des 442 de dashboard-api -> HA juste au-dessus,
    # pour que les deux lignes restent parallèles-mais-distinctes) avant de
    # rejoindre le couloir droit dédié.
    ha_exit = anchor(NODES['homeassistant'], 'bottom', offset=90)
    add([ha_exit, (ha_exit[0], GAP_ROW_A_B_2), (LANE_RIGHT_2, GAP_ROW_A_B_2), (LANE_RIGHT_2, tc['y'] + tc['h']), anchor(tc, 'bottom', off1)],
        'ambre', 'intégration Tesla Fleet', bias=0.5)
    tm_r = anchor(NODES['teslamate'], 'right')
    add([tm_r, (LANE_RIGHT_3, tm_r[1]), (LANE_RIGHT_3, tc['y'] + tc['h']), anchor(tc, 'bottom', off2)],
        'cuivre', 'Fleet API', bias=0.271)

    return edges


def render_overview_svg():
    frames = [render_arrow_defs(), render_mac_frame()]
    frames.append(render_frame(FRAMES['acces'], 'Accès distant — malnoy.com', 'ambre'))
    frames.append(render_frame(FRAMES['domotique'], 'Domotique — cœur', 'ambre'))
    frames.append(render_frame(FRAMES['documentation'], 'Documentation', 'cuivre'))
    frames.append(render_frame(FRAMES['monitoring'], 'Monitoring — data', 'glacier'))
    frames.append(render_frame(FRAMES['dashboard'], 'Dashboard — solutions', 'mousse'))
    frames.append(render_frame(FRAMES['vehicule'], 'Véhicule — Tesla', 'cuivre'))
    frames.append(render_frame(TUNET_SUBFRAME, 'autre réseau Docker', 'mousse', dashed=True))

    all_edges = build_edges()
    lines = [render_edge_line(pts, color, dashed=planned) for pts, color, label, planned, bias in all_edges]

    boxes = [render_knx(),
             render_external('USER', 'Utilisateurs', 'Mac · iPad · iPhone · écran mural'),
             render_external('TESLACLOUD', 'Tesla Fleet API', 'cloud Tesla'),
             render_external('OPENMETEO', 'Open-Meteo API', 'externe')]
    for nid in ['cloudflared', 'homeassistant', 'doc-knx', 'prometheus', 'victoriametrics', 'grafana',
                'glasshome', 'tunet', 'dashboard-proto', 'dashboard-api', 'dashboard-web',
                'tesla-key', 'teslamate', 'teslamate-db', 'teslamate-mosquitto']:
        boxes.append(render_node(nid))

    # les labels passent en dernier, par-dessus les cadres/nœuds, pour ne
    # jamais être recouverts par un remplissage opaque voisin.
    labels = [render_edge_label(pts, label, bias) for pts, color, label, planned, bias in all_edges]

    body = '\n'.join(frames + lines + boxes + labels)
    return (
        f'<svg viewBox="0 0 {CANVAS_W} {CANVAS_H}" role="img" '
        f'aria-label="Schéma de l\'architecture Villa Bulle : domaines fonctionnels (domotique, monitoring, '
        f'documentation, véhicule, dashboard, accès distant) hébergés sur le Mac mini, bus KNX filaire physique, '
        f'et dépendances externes Tesla / Open-Meteo.">{body}</svg>'
    )
