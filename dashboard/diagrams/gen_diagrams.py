#!/usr/bin/env python3
"""Sketches de structure — style "Liquid Glass" : les éléments décidés portent
du texte/contenu sur du verre dépoli ; les éléments PAS ENCORE décidés sont des
emplacements en verre vides (bordure pointillée, aucun contenu). À mettre à
jour au fur et à mesure que les points ouverts du cahier des charges se
tranchent."""

import os
import io
import base64
from PIL import Image

OUT_DIR = os.path.dirname(__file__)
ASSETS_PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "photos")


def photo_b64(filename, target_w, target_h, quality=68):
    """Charge une photo réelle depuis assets/photos/, la recadre/redimensionne au
    format demandé et la renvoie en JPEG base64 — pour l'illustrer directement
    dans un sketch une fois qu'une photo est décidée pour un emplacement."""
    path = os.path.join(ASSETS_PHOTOS_DIR, filename)
    im = Image.open(path).convert("RGB")
    w, h = im.size
    target_ratio = target_w / target_h
    src_ratio = w / h
    if src_ratio > target_ratio:
        new_w = int(h * target_ratio)
        x0 = (w - new_w) // 2
        im = im.crop((x0, 0, x0 + new_w, h))
    else:
        new_h = int(w / target_ratio)
        y0 = (h - new_h) // 2
        im = im.crop((0, y0, w, y0 + new_h))
    im = im.resize((target_w, target_h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()

# ---------- page de documentation (hors écran) ----------
PAPER = "#f7f6f2"
INK = "#2a2f3d"
INK_DIM = "#6b7280"

# ---------- écran : fond dégradé + verre ----------
BG1 = "#aab0bd"
BG2 = "#5c6472"
GLASS_STROKE_DECIDED = "rgba(255,255,255,0.55)"
GLASS_STROKE_OPEN = "rgba(255,255,255,0.40)"
TEXT_WHITE = "#ffffff"
TEXT_DIM = "rgba(255,255,255,0.70)"
ACCENT = "#ffb27a"
ACCENT_GLASS_TOP = "rgba(255,178,122,0.38)"
ACCENT_GLASS_BOTTOM = "rgba(255,178,122,0.14)"
TAG_BG = "rgba(18,20,26,0.55)"
TAG_TEXT = "#ffd2a8"

FONT = "Arial, Helvetica, sans-serif"
FONT_MONO = "Consolas, 'Courier New', monospace"
FONT_SERIF = "Georgia, 'Times New Roman', serif"

SCREEN_X, SCREEN_Y, SCREEN_W, SCREEN_H = 44, 110, 1192, 610
LEFT_W = 216
RIGHT_W = 268
BOTTOM_H = 34

LEFT = dict(x=SCREEN_X, y=SCREEN_Y, w=LEFT_W, h=SCREEN_H)
RIGHT = dict(x=SCREEN_X + SCREEN_W - RIGHT_W, y=SCREEN_Y, w=RIGHT_W, h=SCREEN_H)
BOTTOM = dict(x=SCREEN_X + LEFT_W, y=SCREEN_Y + SCREEN_H - BOTTOM_H, w=SCREEN_W - LEFT_W - RIGHT_W, h=BOTTOM_H)
MAIN = dict(x=SCREEN_X + LEFT_W, y=SCREEN_Y, w=SCREEN_W - LEFT_W - RIGHT_W, h=SCREEN_H - BOTTOM_H)

VB_W, VB_H = 1280, 820

_uid = [0]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class SVG:
    def __init__(self):
        self.parts = []
        self.defs = []

    def raw(self, s):
        self.parts.append(s)

    def new_id(self, base):
        _uid[0] += 1
        return f"{base}{_uid[0]}"

    def glass(self, x, y, w, h, rx=16, decided=True, tint=None):
        """Panneau/pastille en verre. decided=False => vide, bordure pointillée."""
        gid = self.new_id("g")
        top = (tint[0] if tint else "rgba(255,255,255,0.32)")
        bot = (tint[1] if tint else "rgba(255,255,255,0.10)")
        self.defs.append(
            f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bot}"/></linearGradient>'
        )
        stroke = GLASS_STROKE_DECIDED if decided else GLASS_STROKE_OPEN
        dash = "" if decided else ' stroke-dasharray="6,5"'
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
                  f'fill="url(#{gid})" stroke="{stroke}" stroke-width="1.6"{dash} '
                  f'filter="url(#glassShadow)"/>')
        # léger reflet en haut
        self.raw(f'<rect x="{x+w*0.06:.1f}" y="{y+h*0.08:.1f}" width="{w*0.5:.1f}" height="{max(h*0.16,4):.1f}" '
                  f'rx="{rx*0.6:.1f}" fill="rgba(255,255,255,0.16)"/>')

    def glass_circle(self, cx, cy, r, decided=True, tint=None):
        gid = self.new_id("gc")
        top = (tint[0] if tint else "rgba(255,255,255,0.34)")
        bot = (tint[1] if tint else "rgba(255,255,255,0.10)")
        self.defs.append(
            f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bot}"/></linearGradient>'
        )
        stroke = GLASS_STROKE_DECIDED if decided else GLASS_STROKE_OPEN
        dash = "" if decided else ' stroke-dasharray="5,4"'
        self.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="url(#{gid})" '
                  f'stroke="{stroke}" stroke-width="1.5"{dash} filter="url(#glassShadow)"/>')

    def photo(self, x, y, w, h, b64_jpeg, rx=16):
        """Carte photo réelle (décidée) : image recadrée en plein cadre + voile
        sombre en bas pour la lisibilité du texte posé dessus (même principe que
        --scrim-rgb dans les autres prototypes du projet)."""
        cid = self.new_id("clip")
        gid = self.new_id("scrim")
        self.defs.append(f'<clipPath id="{cid}"><rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}"/></clipPath>')
        self.defs.append(
            f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="rgba(8,10,16,0.10)"/><stop offset="1" stop-color="rgba(5,7,12,0.75)"/></linearGradient>'
        )
        self.raw(f'<g clip-path="url(#{cid})">'
                  f'<image x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                  f'href="data:image/jpeg;base64,{b64_jpeg}" preserveAspectRatio="xMidYMid slice"/>'
                  f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="url(#{gid})"/>'
                  f'</g>')
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="none" '
                  f'stroke="{GLASS_STROKE_DECIDED}" stroke-width="1.6" filter="url(#glassShadow)"/>')

    def line(self, x1, y1, x2, y2, stroke="rgba(255,255,255,0.28)", sw=1.2):
        self.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}"/>')

    def icon(self, cx, cy, size, paths, stroke="rgba(255,255,255,0.92)", sw=2):
        """Icône Lucide (viewBox 24x24, contour seul, licence ISC) centrée en
        (cx,cy), mise à l'échelle à `size` px. `paths` = liste de `d` copiés
        tels quels depuis lucide.dev (stroke-linecap/linejoin round)."""
        scale = size / 24.0
        tx = cx - size / 2
        ty = cy - size / 2
        self.raw(f'<g transform="translate({tx:.1f},{ty:.1f}) scale({scale:.4f})" '
                  f'fill="none" stroke="{stroke}" stroke-width="{sw/scale:.3f}" '
                  f'stroke-linecap="round" stroke-linejoin="round">')
        for d in paths:
            self.raw(f'<path d="{esc(d)}"/>')
        self.raw('</g>')

    def text(self, x, y, s, size=13, fill=TEXT_WHITE, family=FONT, weight="400", anchor="start", spacing=None, style=None):
        sp = f' letter-spacing="{spacing}"' if spacing else ""
        st = f' font-style="{style}"' if style else ""
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
                  f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{sp}{st}>{esc(s)}</text>')

    def tag(self, x, y, s):
        w = 12 + 8 * len(s)
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="19" rx="9.5" fill="{TAG_BG}"/>')
        self.text(x + w / 2, y + 13.5, s, size=10.5, fill=TAG_TEXT, family=FONT_MONO, weight="700", anchor="middle")
        return w

    def out(self):
        defs = "".join(sorted(set(self.defs)))
        return f'<defs>{defs}</defs>\n' + "\n".join(self.parts)


def base_canvas(s, title, subtitle):
    s.raw(f'<rect x="0" y="0" width="{VB_W}" height="{VB_H}" fill="{PAPER}"/>')
    s.text(44, 36, title, size=22, fill=INK, family=FONT_SERIF, weight="700")
    s.text(44, 56, subtitle, size=13, fill=INK_DIM, family=FONT)

    s.defs.append(
        f'<linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{BG1}"/><stop offset="1" stop-color="{BG2}"/></linearGradient>'
    )
    s.defs.append(
        '<filter id="glassShadow" x="-40%" y="-40%" width="180%" height="180%">'
        '<feDropShadow dx="0" dy="5" stdDeviation="7" flood-color="#000000" flood-opacity="0.28"/>'
        '</filter>'
    )
    s.raw(f'<rect x="{SCREEN_X-10}" y="{SCREEN_Y-10}" width="{SCREEN_W+20}" height="{SCREEN_H+20}" rx="24" '
          f'fill="#3a3f4a"/>')
    s.raw(f'<rect x="{SCREEN_X}" y="{SCREEN_Y}" width="{SCREEN_W}" height="{SCREEN_H}" rx="16" fill="url(#bgGrad)"/>')


def legend(s):
    y = SCREEN_Y + SCREEN_H + 66
    x = SCREEN_X
    s.raw(f'<rect x="{x}" y="{y-14}" width="30" height="18" rx="8" fill="rgba(120,124,132,0.14)" '
          f'stroke="{GLASS_STROKE_DECIDED}" stroke-width="1.4"/>')
    s.raw(f'<text x="{x+38}" y="{y}" font-family="{FONT}" font-size="11.5" fill="{INK_DIM}">contenu = décidé</text>')
    x2 = x + 190
    s.raw(f'<rect x="{x2}" y="{y-14}" width="30" height="18" rx="8" fill="rgba(120,124,132,0.10)" '
          f'stroke="{GLASS_STROKE_OPEN}" stroke-width="1.4" stroke-dasharray="5,4"/>')
    s.raw(f'<text x="{x2+38}" y="{y}" font-family="{FONT}" font-size="11.5" fill="{INK_DIM}">vide = pas encore décidé</text>')


def reserved_bottom(s):
    z = BOTTOM
    s.glass(z["x"], z["y"], z["w"], z["h"], rx=8, decided=False)


def left_sidebar(s, active_key):
    z = LEFT
    s.glass(z["x"] + 8, z["y"] + 8, z["w"] - 16, z["h"] - 16, rx=20, decided=True)
    x0 = z["x"] + 26
    y = z["y"] + 44
    s.text(x0, y, "DIMANCHE", size=13, fill=TEXT_WHITE, family=FONT, weight="700", spacing="0.5px")
    y += 38
    s.text(x0, y, "10:42", size=30, fill=TEXT_WHITE, family=FONT_SERIF, weight="700")
    y += 24
    s.text(x0, y, "Fête : Ste Reine", size=11, fill=TEXT_DIM, family=FONT)
    y += 22
    s.glass_circle(x0 + 8, y - 4, 8, decided=False)
    s.text(x0 + 22, y, "Anniversaire : Léane", size=11, fill=ACCENT, family=FONT, weight="700")
    y += 34
    s.line(x0, y, z["x"] + z["w"] - 26, y)
    y += 24

    items = [("home", "Accueil"), ("pieces", "Pièces"), ("lumiere", "Lumière"),
             ("temperature", "Température"), ("energie", "Energie"), ("meteo", "Météo"),
             ("config", "Configuration")]
    row_h = 58
    for key, label in items:
        active = (key == active_key)
        if active:
            s.glass(z["x"] + 12, y - 10, z["w"] - 40, row_h - 12, rx=14, decided=True,
                    tint=(ACCENT_GLASS_TOP, ACCENT_GLASS_BOTTOM))
        s.glass_circle(x0 + 16, y + 8, 16, decided=False)
        s.text(x0 + 44, y + 13, label, size=13, fill=(ACCENT if active else TEXT_WHITE), family=FONT,
               weight=("700" if active else "400"))
        y += row_h

    s.text(z["x"] + z["w"] / 2, z["y"] + z["h"] + 26, "Barre gauche — persistante (T9)", size=12.5, fill=INK,
           family=FONT, weight="700", anchor="middle")


PEOPLE = [
    ("Fab", "F", [("Lun", "9h", "Point chantier"), ("Jeu", "18h", "Dîner Marc & Léa")]),
    ("Léane", "L", [("Mar", "16h", "Anniversaire Zoé"), ("Sam", "10h", "Cours de tennis")]),
]


def right_sidebar(s, people):
    z = RIGHT
    s.glass(z["x"] + 8, z["y"] + 8, z["w"] - 16, z["h"] - 16, rx=20, decided=True)
    x0 = z["x"] + 24
    y = z["y"] + 40
    s.text(x0, y, "MÉTÉO", size=10.5, fill=TEXT_DIM, family=FONT_MONO, spacing="1px")
    y += 16
    s.glass_circle(x0 + 20, y + 18, 18, decided=False)
    s.text(x0 + 52, y + 16, "18°C", size=19, fill=TEXT_WHITE, family=FONT, weight="700")
    s.text(x0 + 52, y + 34, "Dégagé", size=11, fill=TEXT_DIM, family=FONT)
    y += 56
    dw = (z["w"] - 48 - 2 * 10) / 3
    dx = x0
    for _ in range(3):
        s.glass(dx, y, dw, 40, rx=8, decided=False)
        dx += dw + 10
    y += 58
    s.line(x0, y, z["x"] + z["w"] - 24, y)
    y += 24
    s.text(x0, y, "CETTE SEMAINE — par invité", size=10.5, fill=TEXT_DIM, family=FONT_MONO, spacing="0.5px")
    y += 22

    for name, initial, events in people:
        s.glass_circle(x0 + 10, y, 11, decided=True)
        s.text(x0 + 10, y + 4, initial, size=10, fill=TEXT_WHITE, family=FONT_MONO, weight="700", anchor="middle")
        s.text(x0 + 28, y + 4, name, size=12.5, fill=TEXT_WHITE, family=FONT, weight="700")
        y += 24
        for day, time_, title in events:
            s.text(x0 + 12, y, f"{day} {time_}", size=10, fill=TEXT_DIM, family=FONT_MONO)
            s.text(x0 + 76, y, title, size=10.5, fill=TEXT_WHITE, family=FONT)
            y += 18
        y += 10

    s.tag(x0, y, "T10")
    s.text(z["x"] + z["w"] / 2, z["y"] + z["h"] + 26, "Barre droite — persistante (T9/T10)", size=12.5, fill=INK,
           family=FONT, weight="700", anchor="middle")


def shutter_icon(s, x, y, size, closed_frac):
    """Pictogramme volet schématique : cadre + lattes, avec un voile qui monte
    depuis le haut proportionnellement à closed_frac (0 = ouvert, 1 = fermé,
    0.5 = intermédiaire). Évite de trancher le glyphe final tout en montrant
    clairement l'état — le nombre de volets s'affiche à côté."""
    s.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{size:.1f}" height="{size:.1f}" rx="3" '
          f'fill="rgba(255,255,255,0.14)" stroke="{GLASS_STROKE_DECIDED}" stroke-width="1.3"/>')
    for j in range(1, 4):
        yy = y + size * j / 4
        s.line(x + 2, yy, x + size - 2, yy, stroke="rgba(255,255,255,0.35)", sw=1)
    if closed_frac > 0:
        oh = size * closed_frac
        s.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{size:.1f}" height="{oh:.1f}" rx="3" '
              f'fill="rgba(20,22,28,0.55)"/>')


# Icônes de pièces — Lucide (lucide.dev, licence ISC, libre et gratuite),
# choisies par Fab le 06.09.2026 après une exploration en 4 itérations
# (voir custom_dashboard.md). Chemins copiés tels quels depuis lucide.dev.
ROOM_ICONS = {
    "chambre": [  # bed-double
        "M2 20v-8a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v8",
        "M4 10V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v4",
        "M12 4v6",
        "M2 18h20",
    ],
    "cuisine": [  # chef-hat
        "M17 21a1 1 0 0 0 1-1v-5.35c0-.457.316-.844.727-1.041a4 4 0 0 0-2.134-7.589 "
        "5 5 0 0 0-9.186 0 4 4 0 0 0-2.134 7.588c.411.198.727.585.727 1.041V20a1 1 0 0 0 1 1Z",
        "M6 17h12",
    ],
    "salon": [  # sofa
        "M20 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v3",
        "M2 16a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-5a2 2 0 0 0-4 0v1.5a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5V11a2 2 0 0 0-4 0z",
        "M4 18v2",
        "M20 18v2",
        "M12 4v9",
    ],
    "salle-de-bain": [  # bath
        "M10 4 8 6",
        "M17 19v2",
        "M2 12h20",
        "M7 19v2",
        "M9 5 7.621 3.621A2.121 2.121 0 0 0 4 5v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5",
    ],
    "douche": [  # shower-head
        "m4 4 2.5 2.5",
        "M13.5 6.5a4.95 4.95 0 0 0-7 7",
        "M15 5 5 15",
        "M14 17v.01",
        "M10 16v.01",
        "M13 13v.01",
        "M16 10v.01",
        "M11 20v.01",
        "M17 14v.01",
        "M20 11v.01",
    ],
    "bureau": [  # laptop
        "M18 5a2 2 0 0 1 2 2v8.526a2 2 0 0 0 .212.897l1.068 2.127a1 1 0 0 1-.9 1.45H3.62a1 1 0 0 1-.9-1.45"
        "l1.068-2.127A2 2 0 0 0 4 15.526V7a2 2 0 0 1 2-2z",
        "M20.054 15.987H3.946",
    ],
    "salle-a-manger": [  # utensils
        "M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2",
        "M7 2v20",
        "M21 15V2a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7",
    ],
}


def room_block(s, x, y, w, h, name, temp, lamps_on, lamps_total, heating_on, volets_total, volets_closed_frac, icon_key=None):
    """Bloc résumé pièce/personne (A9) : icone (glyphe pas encore décidé) + nom
    + température + lampe (teinte chaude si ≥1 allumée, avec le nombre) +
    chauffage (teinte chaude si actif) + volet (remplissage = fermeture, avec
    le nombre de volets). L'état lui-même est décidé ; seul le glyphe des
    icones reste ouvert (§12)."""
    s.glass(x, y, w, h, rx=14, decided=True)
    s.glass_circle(x + 22, y + 22, 13, decided=icon_key is not None)
    if icon_key:
        s.icon(x + 22, y + 22, 17, ROOM_ICONS[icon_key])
    s.text(x + 42, y + 19, name, size=12.5, fill=TEXT_WHITE, family=FONT, weight="700")
    s.text(x + w - 14, y + 27, temp, size=15, fill=TEXT_WHITE, family=FONT, weight="700", anchor="end")

    iy = y + h - 20
    lamp_on = lamps_on > 0
    s.glass_circle(x + 20, iy, 10, decided=True, tint=(ACCENT_GLASS_TOP, ACCENT_GLASS_BOTTOM) if lamp_on else None)
    s.text(x + 34, iy + 4, str(lamps_on), size=11, fill=(ACCENT if lamp_on else TEXT_DIM), family=FONT, weight="700")

    hx = x + w * 0.42
    s.glass_circle(hx, iy, 10, decided=True, tint=(ACCENT_GLASS_TOP, ACCENT_GLASS_BOTTOM) if heating_on else None)

    vx = x + w - 38
    shutter_icon(s, vx, iy - 10, 20, volets_closed_frac)
    s.text(vx + 26, iy + 4, str(volets_total), size=11, fill=TEXT_DIM, family=FONT, weight="700")


ROOMS_EXAMPLE = [
    # name, temp, lamps_on, lamps_total, heating_on, volets_total, volets_closed_frac, icon_key
    ("Cuisine", "21.2°", 2, 2, False, 2, 0.5, "cuisine"),
    ("Salon", "20.8°", 1, 3, True, 2, 0.0, "salon"),
    ("Salle de Bain", "22.5°", 0, 1, True, 1, 1.0, "salle-de-bain"),
    ("Lily", "21.0°", 1, 1, False, 2, 1.0, "chambre"),
    ("Léane", "20.5°", 2, 2, True, 2, 0.5, "chambre"),
    ("Bureau", "19.9°", 0, 2, False, 1, 0.0, "bureau"),
]


def write(name, s):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VB_W} {VB_H}" '
           f'width="{VB_W}" height="{VB_H}">\n{s.out()}\n</svg>')
    with open(path, "w") as f:
        f.write(svg)
    print("wrote", path)


# ============================================================= ACCUEIL =====
def build_accueil():
    s = SVG()
    base_canvas(s, "Structure — Écran d'accueil",
                "Style verre — texte = décidé, verre vide = pas encore décidé · T7, A1–A9")
    left_sidebar(s, "home")
    right_sidebar(s, PEOPLE)
    reserved_bottom(s)

    m = MAIN
    hero_b64 = photo_b64("maison-facade-jardin-2.jpg", 700, 92)
    s.photo(m["x"] + 8, m["y"] + 8, m["w"] - 16, 92, hero_b64, rx=16)
    s.text(m["x"] + 32, m["y"] + 44, "Bonsoir, Fab.", size=24, fill=TEXT_WHITE, family=FONT_SERIF, weight="700")
    s.text(m["x"] + 32, m["y"] + 68, "Le salon est ensoleillé et vide — fermer le volet ?", size=11.5, fill=TEXT_DIM, family=FONT)
    s.tag(m["x"] + 32, m["y"] + 82, "A4")

    tiles = [("21.4°", "Temp. maison", "A5"), ("87%", "Batterie solaire", "A6"),
             ("62%", "Batterie voiture", "A7"), ("2.8 kW", "Production solaire", "A8")]
    tw = (m["w"] - 16 - 3 * 14) / 4
    tx = m["x"] + 8
    ty = m["y"] + 118
    for val, label, tid in tiles:
        s.glass(tx, ty, tw, 94, rx=14, decided=True)
        s.glass_circle(tx + 20, ty + 22, 12, decided=False)
        s.text(tx + 14, ty + 56, val, size=18, fill=TEXT_WHITE, family=FONT, weight="700")
        s.text(tx + 14, ty + 74, label, size=9.5, fill=TEXT_DIM, family=FONT)
        s.tag(tx + tw - 30, ty + 8, tid)
        tx += tw + 14

    s.text(m["x"] + 32, m["y"] + 246, "SCÈNES RAPIDES — contenu à définir (§12)", size=10, fill="rgba(255,255,255,0.55)",
           family=FONT_MONO, spacing="0.5px")
    sx = m["x"] + 8
    for _ in range(3):
        s.glass(sx, m["y"] + 260, 132, 44, rx=14, decided=False)
        sx += 146
    s.tag(m["x"] + 8, m["y"] + 310, "A3")

    header_y = m["y"] + 352
    s.text(m["x"] + 8, header_y, "PIÈCES — APERÇU RAPIDE", size=10, fill="rgba(255,255,255,0.55)",
           family=FONT_MONO, spacing="0.5px")
    s.tag(m["x"] + m["w"] - 36, header_y - 14, "A9")

    grid_y = header_y + 14
    row_h, gap = 64, 8
    bw = (m["w"] - 16 - 2 * 14) / 3
    bx0 = m["x"] + 8
    for i, (name, temp, lamps_on, lamps_total, heating_on, volets_total, closed_frac, icon_key) in enumerate(ROOMS_EXAMPLE):
        col, row = i % 3, i // 3
        bx = bx0 + col * (bw + 14)
        by = grid_y + row * (row_h + gap)
        room_block(s, bx, by, bw, row_h, name, temp, lamps_on, lamps_total, heating_on, volets_total, closed_frac, icon_key)

    s.glass(m["x"] + 8, m["y"] + m["h"] - 60, m["w"] - 16, 40, rx=12, decided=False)
    s.tag(m["x"] + 16, m["y"] + m["h"] - 54, "T6")

    legend(s)
    write("structure-accueil.svg", s)


# ======================================================= ÉTAGE / RDC =======
def build_etage():
    s = SVG()
    base_canvas(s, "Structure — Vue d'étage / RDC (overview)",
                "Style verre — texte = décidé, verre vide = pas encore décidé · E0–E4")
    left_sidebar(s, "pieces")
    right_sidebar(s, PEOPLE)
    reserved_bottom(s)

    m = MAIN
    zx = m["x"] + 8
    zy = m["y"] + 8
    zone_w = 96
    for _ in range(3):
        s.glass(zx, zy, zone_w, 36, rx=18, decided=False)
        zx += zone_w + 10
    s.tag(zx + 4, zy + 8, "E0")

    s.text(m["x"] + 8, m["y"] + 76, "Étage", size=19, fill=TEXT_WHITE, family=FONT_SERIF, weight="700")
    s.text(m["x"] + 8, m["y"] + 94, "4 pièces", size=10.5, fill=TEXT_DIM, family=FONT_MONO)

    rooms = [("Chambre Léane", "21.3°", True, "62%"), ("Salon", "20.8°", True, "40%"),
             ("Bureau", None, None, None), ("Salle de bain", "22.1°", False, "100%")]
    tile_w, tile_h, gap = (m["w"] - 16 - 20) / 2, 128, 20
    x0 = m["x"] + 8
    y0 = m["y"] + 112
    for i, (name, temp, lit, volet) in enumerate(rooms):
        col = i % 2
        row = i // 2
        x = x0 + col * (tile_w + gap)
        y = y0 + row * (tile_h + gap)
        muted = temp is None
        s.glass(x, y, tile_w, tile_h, rx=16, decided=not muted)
        s.text(x + 16, y + 30, name, size=13.5, fill=TEXT_WHITE, family=FONT, weight="700")
        if muted:
            s.text(x + 16, y + 52, "mode maquette — pas d'entité (E4)", size=9.5, fill=TEXT_DIM, family=FONT, style="italic")
        else:
            s.text(x + 16, y + 76, temp, size=13, fill=TEXT_WHITE, family=FONT_MONO)
            s.glass_circle(x + 22, y + 96, 6, decided=False)
            s.glass_circle(x + 44, y + 96, 6, decided=False)
            s.text(x + tile_w - 44, y + tile_h - 16, "E1/E2", size=8.5, fill="rgba(255,255,255,0.5)", family=FONT_MONO)
        if i == 0:
            s.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{tile_w:.1f}" height="{tile_h:.1f}" rx="16" '
                  f'fill="none" stroke="{ACCENT}" stroke-width="2.4"/>')

    s.text(x0, y0 + 2 * (tile_h + gap) - gap + 26, "→ toucher une tuile ouvre la vue détaillée (E3)",
           size=10.5, fill=ACCENT, family=FONT)

    legend(s)
    write("structure-etage.svg", s)


# ============================================================ PIÈCE ========
def build_piece():
    s = SVG()
    base_canvas(s, "Structure — Vue pièce (ex. Chambre Léane)",
                "Style verre — texte = décidé, verre vide = pas encore décidé · P1–P6")
    left_sidebar(s, "pieces")
    right_sidebar(s, PEOPLE)
    reserved_bottom(s)

    m = MAIN
    rooms = ["Chambre Léane", "Salon", "Bureau"]
    rx = m["x"] + 8
    ry = m["y"] + 8
    for i, r in enumerate(rooms):
        active = i == 0
        w = 26 + 9 * len(r)
        s.glass(rx, ry, w, 34, rx=17, decided=True, tint=(ACCENT_GLASS_TOP, ACCENT_GLASS_BOTTOM) if active else None)
        s.text(rx + w / 2, ry + 22, r, size=11, fill=(ACCENT if active else TEXT_WHITE), family=FONT, anchor="middle")
        rx += w + 10

    vy = m["y"] + 58
    vh = m["h"] - 58 - 8
    vw = m["w"] * 0.46
    vx = m["x"] + 8
    s.glass(vx, vy, vw, vh, rx=18, decided=False)
    s.glass(vx + 14, vy + 14, 100, 30, rx=15, decided=True)
    s.text(vx + 40, vy + 33, "Iso", size=10.5, fill=TEXT_WHITE, family=FONT, weight="700", anchor="middle")
    s.text(vx + 80, vy + 33, "Photo", size=10.5, fill=TEXT_DIM, family=FONT, anchor="middle")
    s.tag(vx + 14, vy + 50, "P5/P6")
    s.raw(f'<ellipse cx="{vx+vw/2:.1f}" cy="{vy+vh-36:.1f}" rx="{vw*0.26:.1f}" ry="20" fill="{ACCENT}" opacity="0.22"/>')
    s.text(vx + vw / 2, vy + vh - 14, "glow chauffage (P4)", size=9.5, fill=TEXT_DIM, family=FONT, anchor="middle", style="italic")

    px = vx + vw + 20
    pw = m["x"] + m["w"] - 8 - px
    py = vy
    ph = vh
    s.glass(px, py, pw, ph, rx=18, decided=True)
    s.text(px + 18, py + 30, "Chambre Léane", size=15, fill=TEXT_WHITE, family=FONT_SERIF, weight="700")

    icons = ["Temp", "Lumière", "Volet", "Confort"]
    ix = px + 16
    iy = py + 50
    icw = (pw - 32 - 3 * 8) / 4
    for i, ic in enumerate(icons):
        active = i == 0
        s.glass(ix, iy, icw, 40, rx=10, decided=True, tint=(ACCENT_GLASS_TOP, ACCENT_GLASS_BOTTOM) if active else None)
        s.text(ix + icw / 2, iy + 25, ic, size=9.5, fill=(ACCENT if active else TEXT_WHITE), family=FONT, anchor="middle")
        ix += icw + 8
    s.tag(px + 16, iy + 48, "P1–P4")

    cx, cy, r = px + pw / 2, py + ph / 2 + 30, 60
    s.glass_circle(cx, cy, r, decided=True)
    s.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" stroke="{ACCENT}" stroke-width="8" '
          f'stroke-linecap="round" stroke-dasharray="{2*3.14159*r*0.62:.0f} {2*3.14159*r:.0f}" '
          f'transform="rotate(-215 {cx:.1f} {cy:.1f})"/>')
    s.text(cx, cy - 2, "21.5°", size=18, fill=TEXT_WHITE, family=FONT, weight="700", anchor="middle")
    s.text(cx, cy + 16, "consigne", size=9.5, fill=TEXT_DIM, family=FONT_MONO, anchor="middle")

    legend(s)
    write("structure-piece.svg", s)


if __name__ == "__main__":
    build_accueil()
    build_etage()
    build_piece()
