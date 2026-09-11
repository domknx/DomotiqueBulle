# -*- coding: utf-8 -*-
"""Rend le diagramme d'architecture en vue macro (7 grandes zones cliquables) +
vue détail par zone (mini-diagramme local, thème clair/sombre automatique, nœuds
cliquables) + les données JSON consommées par le popup de dépendances en JS.
Remplace le rendu Mermoid (fond fixe, illisible en clair, non interactif)."""
import json
from architecture_data import CATEGORIES, SERVICES, EXTERNALS, DEPS, deps_for

COL_W = 210
NODE_W, NODE_H = 170, 64
GHOST_W, GHOST_H = 190, 36
ROW_H = 120
MARGIN_X = 60

# grille interne (col, row) par catégorie — 0..N colonnes, 0/1 lignes
LAYOUT = {
    'domotique': {'glasshome': (0, 0), 'homeassistant': (1, 0)},
    'monitoring': {'prometheus': (0, 0), 'victoriametrics': (1, 0), 'grafana': (2, 0)},
    'documentation': {'doc-knx': (0, 0)},
    'vehicule': {'tesla-key': (0, 0), 'teslamate': (2, 0), 'teslamate-db': (1, 1), 'teslamate-mosquitto': (3, 1)},
    'dashboard': {'dashboard-proto': (0, 0), 'dashboard-api': (1, 0), 'dashboard-web': (2, 0)},
    'acces': {'cloudflared': (0, 0)},
    'externe': {'tunet': (0, 0)},
}


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def other_label(node_id):
    if node_id in EXTERNALS:
        return EXTERNALS[node_id]
    return SERVICES[node_id]['title']


def other_category(node_id):
    if node_id in EXTERNALS:
        return None
    return SERVICES[node_id]['category']


def row_positions(n, canvas_w, item_w, gap):
    total = n * item_w + (n - 1) * gap
    start_x = (canvas_w - total) / 2
    return [start_x + i * (item_w + gap) for i in range(n)]


def build_category_layout(cat_id):
    grid = LAYOUT[cat_id]
    maxrow = max(r for _, r in grid.values())
    rows = {}
    for sid, (col, row) in grid.items():
        rows.setdefault(row, []).append(sid)
    for row in rows:
        rows[row].sort(key=lambda sid: grid[sid][0])

    cross_in, cross_out = [], []
    seen = set()
    for sid in grid:
        inc, out = deps_for(sid)
        for other, label, planned, is_ext in inc:
            if other_category(other) == cat_id:
                continue  # interne, traité séparément
            key = ('in', other, sid, label)
            if key in seen:
                continue
            seen.add(key)
            cross_in.append((other, sid, label, planned, is_ext))
        for other, label, planned, is_ext in out:
            if other_category(other) == cat_id:
                continue
            key = ('out', sid, other, label)
            if key in seen:
                continue
            seen.add(key)
            cross_out.append((sid, other, label, planned, is_ext))

    n_top = len(cross_in) or 1
    n_bottom = len(cross_out) or 1
    row_widths = []
    for row in rows.values():
        row_widths.append(len(row) * NODE_W + (len(row) - 1) * 40)
    row_widths.append(n_top * GHOST_W + (n_top - 1) * 30)
    row_widths.append(n_bottom * GHOST_W + (n_bottom - 1) * 30)
    canvas_w = max(760, max(row_widths) + 2 * MARGIN_X)

    nodes = {}  # id -> dict x,y,w,h,row
    TOP_Y = 40
    base_y = TOP_Y + GHOST_H + 60
    for row, ids in rows.items():
        xs = row_positions(len(ids), canvas_w, NODE_W, 40)
        for sid, x in zip(ids, xs):
            nodes[sid] = dict(x=x, y=base_y + row * ROW_H, w=NODE_W, h=NODE_H, row=row, id=sid)

    bottom_row_y = base_y + (maxrow + 1) * ROW_H + 10
    canvas_h = bottom_row_y + GHOST_H + 50

    ghosts_top = []
    if cross_in:
        xs = row_positions(len(cross_in), canvas_w, GHOST_W, 30)
        for (other, target, label, planned, is_ext), x in zip(cross_in, xs):
            ghosts_top.append(dict(x=x, y=TOP_Y, w=GHOST_W, h=GHOST_H, row=-1,
                                    other=other, target=target, label=label, planned=planned, is_ext=is_ext))
    ghosts_bottom = []
    if cross_out:
        xs = row_positions(len(cross_out), canvas_w, GHOST_W, 30)
        for (source, other, label, planned, is_ext), x in zip(cross_out, xs):
            ghosts_bottom.append(dict(x=x, y=bottom_row_y, w=GHOST_W, h=GHOST_H, row=maxrow + 1,
                                       other=other, source=source, label=label, planned=planned, is_ext=is_ext))

    internal_edges = [(f, t, label, planned) for f, t, label, planned in DEPS
                       if f in grid and t in grid]

    return dict(canvas_w=canvas_w, canvas_h=canvas_h, nodes=nodes,
                ghosts_top=ghosts_top, ghosts_bottom=ghosts_bottom, internal_edges=internal_edges)


def anchor(n, side, offset=0.0):
    x, y, w, h = n['x'], n['y'], n['w'], n['h']
    pts = {'top': (x + w / 2, y), 'bottom': (x + w / 2, y + h),
           'left': (x, y + h / 2), 'right': (x + w, y + h / 2)}
    px, py = pts[side]
    if side in ('top', 'bottom'):
        return (px + offset, py)
    return (px, py + offset)


def spread_offsets(n, span_cap):
    """Décale n points convergeant sur la même arête d'un nœud pour éviter que
    leurs segments/labels ne se superposent visuellement en une seule ligne —
    utilisé quand plusieurs ghosts pointent vers le même nœud cible."""
    if n <= 1:
        return [0.0]
    span = min(span_cap, (n - 1) * 50)
    step = span / (n - 1)
    return [-span / 2 + k * step for k in range(n)]


def connect(a, b, offset_a=0.0, offset_b=0.0):
    if a['row'] == b['row']:
        if a['x'] < b['x']:
            return [anchor(a, 'right'), anchor(b, 'left')]
        return [anchor(a, 'left'), anchor(b, 'right')]
    if a['row'] < b['row']:
        p1, p2 = anchor(a, 'bottom', offset_a), anchor(b, 'top', offset_b)
    else:
        p1, p2 = anchor(a, 'top', offset_a), anchor(b, 'bottom', offset_b)
    midy = (p1[1] + p2[1]) / 2
    return [p1, (p1[0], midy), (p2[0], midy), p2]


def connect_row_label(a, b):
    """Comme connect() pour deux nœuds de même rangée (a -> b, la flèche
    pointe toujours vers b), mais fait passer le segment horizontal sous la
    rangée plutôt qu'au milieu — l'écart entre deux nœuds voisins (~40px) est
    souvent plus étroit que le label de l'arête ; en dégageant le segment sous
    les boîtes, le label peut déborder sans chevaucher les nœuds voisins."""
    if a['x'] < b['x']:
        p1, p4 = anchor(a, 'right'), anchor(b, 'left')
    else:
        p1, p4 = anchor(a, 'left'), anchor(b, 'right')
    y = max(a['y'] + a['h'], b['y'] + b['h']) + 18
    return [p1, (p1[0], y), (p4[0], y), p4]


def connect_side(a, b, side='right'):
    """Comme connect(), mais sort par le côté de `a` plutôt que par le bas —
    utilisé pour contourner une rangée intermédiaire plutôt que la traverser."""
    ax = anchor(a, side)
    margin = 26 if side == 'right' else -26
    mid_x = ax[0] + margin
    by = anchor(b, 'top' if a['row'] < b['row'] else 'bottom')
    return [ax, (mid_x, ax[1]), (mid_x, by[1]), by]


def path_d(pts):
    return 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)


def render_arrow_defs():
    out = ['<defs>']
    for token in ['ambre', 'glacier', 'mousse', 'cuivre', 'ink-faint']:
        out.append(
            f'<marker id="arr-{token}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 Z" fill="var(--{token})"/></marker>'
        )
    out.append('</defs>')
    return '\n'.join(out)


def label_anchor(pts, bias=0.5):
    """Point à utiliser pour poser le texte d'une arête — sur le segment
    horizontal du coude, décalé vers l'extrémité `bias` (0=début, 1=fin) pour
    éviter que plusieurs arêtes convergeant vers la même cible se chevauchent."""
    if len(pts) == 2:
        (x1, y1), (x2, y2) = pts
        return (x1 + (x2 - x1) * bias, y1 + (y2 - y1) * bias)
    (x1, y1) = pts[1]
    (x2, y2) = pts[2]
    return (x1 + (x2 - x1) * bias, y1)


def render_edge_line(pts, color_token, dashed=False):
    dash = ' stroke-dasharray="5 4"' if dashed else ''
    return f'<path d="{path_d(pts)}" fill="none" stroke="var(--{color_token})" stroke-width="1.6"{dash} marker-end="url(#arr-{color_token})"/>'


def render_edge_label(pts, label, bias=0.5):
    if not label:
        return ''
    lx, ly = label_anchor(pts, bias)
    w = len(label) * 5.9 + 10
    return (
        f'<rect x="{lx-w/2:.1f}" y="{ly-9:.1f}" width="{w:.1f}" height="15" rx="3" fill="var(--bg)" stroke="var(--border)" stroke-width="0.6"/>'
        f'<text x="{lx:.1f}" y="{ly+3:.1f}" text-anchor="middle" class="d-edge">{esc(label)}</text>'
    )


def render_node_box(n, sid):
    svc = SERVICES[sid]
    color = f"var(--{CATEGORIES_BY_ID[svc['category']]['color']})"
    planned = svc.get('planned', False)
    dash = ' stroke-dasharray="4 4"' if planned else ''
    x, y, w, h = n['x'], n['y'], n['w'], n['h']
    label = esc(svc['title'] + (' — prévu' if planned else ''))
    return (
        f'<g class="d-node" tabindex="0" role="button" aria-haspopup="dialog" '
        f'aria-label="{label} — voir les dépendances" onclick="openServiceModal(\'{sid}\')" '
        f'onkeydown="if(event.key===\'Enter\'||event.key===\' \'){{event.preventDefault();openServiceModal(\'{sid}\')}}">'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="var(--surface)" stroke="{color}" stroke-width="1.8"{dash}/>'
        f'<text x="{x+w/2}" y="{y+26}" text-anchor="middle" class="d-title">{esc(svc["title"])}</text>'
        f'<text x="{x+w/2}" y="{y+43}" text-anchor="middle" class="d-sub">{esc(svc["sub"])}</text>'
        f'</g>'
    )


def render_ghost(g, is_top):
    label = other_label(g['other'])
    clickable = other_category(g['other']) is not None
    x, y, w, h = g['x'], g['y'], g['w'], g['h']
    dash = ' stroke-dasharray="4 4"' if g.get('is_ext') else ' stroke-dasharray="2 3"'
    attrs = ''
    cls = 'd-ghost'
    if clickable:
        cat = other_category(g['other'])
        attrs = (f' tabindex="0" role="button" aria-label="Voir la zone {esc(CATEGORIES_BY_ID[cat]["title"])}" '
                  f'onclick="goArch(\'{cat}\')" onkeydown="if(event.key===\'Enter\'||event.key===\' \'){{event.preventDefault();goArch(\'{cat}\')}}"')
        cls += ' d-ghost-clickable'
    return (
        f'<g class="{cls}"{attrs}>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="none" stroke="var(--ink-faint)" stroke-width="1.3"{dash}/>'
        f'<text x="{x+w/2}" y="{y+h/2+4}" text-anchor="middle" class="d-ghost-label">{esc(label)}</text>'
        f'</g>'
    )


CATEGORIES_BY_ID = {c['id']: c for c in CATEGORIES}


def render_category_svg(cat_id):
    L = build_category_layout(cat_id)
    lines, ghosts, nodes, labels = [], [], [], []
    maxrow = max((n['row'] for n in L['nodes'].values()), default=0)

    for f, t, label, planned in L['internal_edges']:
        na, nb = L['nodes'][f], L['nodes'][t]
        same_row = na['row'] == nb['row']
        if same_row and label:
            # Le label déborde presque toujours l'écart entre deux nœuds
            # voisins (~40px) : on route sous la rangée pour lui faire de la
            # place plutôt que de le laisser chevaucher les boîtes.
            pts = connect_row_label(na, nb)
        else:
            pts = connect(na, nb)
        color = CATEGORIES_BY_ID[cat_id]['color']
        lines.append(render_edge_line(pts, color, dashed=planned))
        labels.append(render_edge_label(pts, label))

    # Plusieurs ghosts peuvent converger vers le même nœud (ou partir du même
    # nœud) : on répartit leurs points d'ancrage le long de l'arête du nœud
    # pour que les segments/labels ne se superposent pas en une ligne unique.
    top_groups = {}
    for i, g in enumerate(L['ghosts_top']):
        top_groups.setdefault(g['target'], []).append(i)
    top_offset = {}
    for target_id, idxs in top_groups.items():
        for idx, off in zip(idxs, spread_offsets(len(idxs), NODE_W - 40)):
            top_offset[idx] = off

    bottom_groups = {}
    for i, g in enumerate(L['ghosts_bottom']):
        bottom_groups.setdefault(g['source'], []).append(i)
    bottom_offset = {}
    for source_id, idxs in bottom_groups.items():
        for idx, off in zip(idxs, spread_offsets(len(idxs), NODE_W - 40)):
            bottom_offset[idx] = off

    for i, g in enumerate(L['ghosts_top']):
        target = L['nodes'][g['target']]
        pts = connect(dict(x=g['x'], y=g['y'], w=g['w'], h=g['h'], row=-1), target,
                       offset_b=top_offset[i])
        color = 'ink-faint' if (g['planned'] or g['is_ext']) else CATEGORIES_BY_ID[cat_id]['color']
        lines.append(render_edge_line(pts, color, dashed=g['planned']))
        labels.append(render_edge_label(pts, g['label'], bias=0.22))
        ghosts.append(render_ghost(g, True))

    for i, g in enumerate(L['ghosts_bottom']):
        source = L['nodes'][g['source']]
        ghost = dict(x=g['x'], y=g['y'], w=g['w'], h=g['h'], row=maxrow + 2)
        if source['row'] < maxrow:
            side = 'right' if (i % 2 == 0) else 'left'
            pts = connect_side(source, ghost, side)
        else:
            pts = connect(source, ghost, offset_a=bottom_offset[i])
        color = 'ink-faint' if (g['planned'] or g['is_ext']) else CATEGORIES_BY_ID[cat_id]['color']
        lines.append(render_edge_line(pts, color, dashed=g['planned']))
        labels.append(render_edge_label(pts, g['label'], bias=0.78))
        ghosts.append(render_ghost(g, False))

    for sid, n in L['nodes'].items():
        nodes.append(render_node_box(n, sid))

    parts = [render_arrow_defs()] + lines + ghosts + nodes + labels
    body = '\n'.join(parts)
    cat_title = CATEGORIES_BY_ID[cat_id]['title']
    return (
        f'<svg viewBox="0 0 {L["canvas_w"]:.0f} {L["canvas_h"]:.0f}" role="img" '
        f'aria-label="Détail de la zone {esc(cat_title)} : ses services et leurs dépendances directes avec le reste de la stack.">'
        f'{body}</svg>'
    )


def render_macro_grid(id_prefix=''):
    cards = []
    for c in CATEGORIES:
        n = sum(1 for s in SERVICES.values() if s['category'] == c['id'])
        cards.append(
            f'<div class="arch-tile" style="--accent:var(--{c["color"]})" tabindex="0" role="button" '
            f'aria-label="Zone {esc(c["title"])} — {esc(c["blurb"])}" '
            f'onclick="goArch(\'{c["id"]}\')" onkeydown="if(event.key===\'Enter\'||event.key===\' \'){{event.preventDefault();goArch(\'{c["id"]}\')}}">'
            f'<div class="arch-tile-count">{n} service{"s" if n>1 else ""}</div>'
            f'<h3>{esc(c["title"])}</h3>'
            f'<p>{esc(c["blurb"])}</p>'
            f'<span class="arch-tile-arrow">Explorer &rarr;</span>'
            f'</div>'
        )
    return f'<div class="arch-grid">{"".join(cards)}</div>'


def render_category_panels():
    panels = []
    for c in CATEGORIES:
        svg = render_category_svg(c['id'])
        panels.append(
            f'<div class="arch-detail" id="arch-detail-{c["id"]}" hidden>'
            f'<button class="arch-back" onclick="showArchMacro()">&larr; Toutes les zones</button>'
            f'<div class="arch-detail-head" style="--accent:var(--{c["color"]})">'
            f'<h3>{esc(c["title"])}</h3><p>{esc(c["blurb"])}</p></div>'
            f'<div class="arch-detail-diagram">{svg}</div>'
            f'</div>'
        )
    return '\n'.join(panels)


def build_arch_data_json():
    services = {}
    for sid, s in SERVICES.items():
        inc, out = deps_for(sid)
        services[sid] = dict(
            title=s['title'], sub=s['sub'], category=s['category'], desc=s['desc'],
            planned=s.get('planned', False),
            incoming=[dict(id=f, name=other_label(f), edge=(label or '—'), planned=p, cat=other_category(f)) for f, label, p, ext in inc],
            outgoing=[dict(id=t, name=other_label(t), edge=(label or '—'), planned=p, cat=other_category(t)) for t, label, p, ext in out],
        )
    cats = {c['id']: dict(title=c['title'], color=c['color']) for c in CATEGORIES}
    return json.dumps(dict(services=services, categories=cats), ensure_ascii=False)
