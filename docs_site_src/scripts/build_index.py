# -*- coding: utf-8 -*-
"""Régénère docs_site/index.html à partir des sources du projet.

Pipeline complet (à exécuter dans cet ordre, depuis docs_site_src/scripts/) :
  1. extract_readme.py   -> extrait le diagramme mermaid de README.md
                             (produit diagram.mmd + README_no_mermaid.md)
  2. mmdc (mermaid-cli)  -> rend diagram.mmd en diagram.svg, thème Villa Bulle
                             mmdc -i diagram.mmd -o diagram.svg -b transparent \
                                  -c mermaid-theme.json -p puppeteer-config.json --width 1400
  3. render_readme.py    -> convertit README_no_mermaid.md + diagram.svg en readme_body.html
  4. build_index.py (ce script) -> injecte tout dans template.html -> docs_site/index.html

content.py contient les données éditoriales (liste des services, jalons, points
ouverts) recopiées à la main depuis README.md / docker-compose.yml /
dashboard/CAHIER_DES_CHARGES.md — à mettre à jour manuellement si ces sources
changent, exactement comme on met à jour un README.

Ce script ne doit jamais être court-circuité par une édition manuelle de
docs_site/index.html : voir docs_site_src/README.md.
"""
import html
import os
from content import ARCH_SERVICES, ROADMAP

# ---------------------------------------------------------------- house SVG
HOUSE_SVG = '''<svg viewBox="0 0 340 350" role="img" aria-label="Coupe de la maison sur trois niveaux reliée au bus KNX filaire, avec les appareils qu'il commande : volets, prises électriques et véhicule">
  <polygon class="h-outline" points="95,72 170,20 245,72" />
  <rect class="h-outline" x="110" y="72" width="120" height="188" />
  <line class="h-floorline" x1="110" y1="134" x2="230" y2="134" />
  <line class="h-floorline" x1="110" y1="197" x2="230" y2="197" />

  <rect class="h-window" x="128" y="88" width="20" height="26" />
  <rect class="h-window" x="192" y="88" width="20" height="26" />

  <rect class="h-window" x="128" y="150" width="20" height="26" />
  <rect class="h-window" x="157" y="163" width="26" height="34" />

  <rect class="h-window" x="128" y="208" width="20" height="18" />
  <rect class="h-window" x="192" y="208" width="20" height="18" />

  <line class="h-ground" x1="20" y1="262" x2="320" y2="262" />
  <circle class="h-tree" cx="300" cy="233" r="17" />
  <rect class="h-tree" x="297" y="248" width="6" height="14" opacity="0.8" />

  <path class="h-bus" d="M138,255 L138,220 L200,220 L200,165 L162,165 L162,95 L162,58" />
  <circle class="h-node" cx="138" cy="220" r="3.6" />
  <circle class="h-node-pulse" cx="138" cy="220" r="3.6" />
  <circle class="h-node" cx="200" cy="165" r="3.6" />
  <circle class="h-node-pulse" cx="200" cy="165" r="3.6" />
  <circle class="h-node" cx="162" cy="95" r="3.6" />
  <circle class="h-node-pulse" cx="162" cy="95" r="3.6" />

  <text class="h-label" x="236" y="107">Étage</text>
  <text class="h-label" x="236" y="169">Rez</text>
  <text class="h-label" x="236" y="231">Sous-sol</text>

  <!-- Store (volet roulant) -->
  <g class="h-bubble-store">
    <path class="h-conn" d="M80,95 L95,95 L95,72" />
    <circle class="h-bubble" cx="55" cy="95" r="25" />
    <rect class="h-icon" x="44" y="84" width="22" height="5" rx="1.5" />
    <line class="h-icon" x1="44" y1="93" x2="66" y2="93" />
    <line class="h-icon" x1="44" y1="99" x2="66" y2="99" />
    <line class="h-icon" x1="44" y1="105" x2="66" y2="105" />
    <text class="h-label" x="55" y="136" text-anchor="middle">Stores</text>
  </g>

  <!-- Prise électrique (norme suisse, 3 broches) -->
  <g class="h-bubble-prise">
    <path class="h-conn" d="M260,95 L245,95 L245,72" />
    <circle class="h-bubble" cx="285" cy="95" r="25" />
    <rect class="h-icon" x="275" y="85" width="20" height="20" rx="4" />
    <circle class="h-icon-fill" cx="281" cy="93" r="1.8" />
    <circle class="h-icon-fill" cx="289" cy="93" r="1.8" />
    <circle class="h-icon-fill" cx="285" cy="100" r="1.8" />
    <text class="h-label" x="285" y="136" text-anchor="middle">Prises</text>
  </g>

  <!-- Véhicule (Tesla / portail) -->
  <g class="h-bubble-car">
    <path class="h-conn" d="M170,277 L170,262" />
    <circle class="h-bubble" cx="170" cy="309" r="28" />
    <path class="h-icon" d="M152,313 L152,309 L157,309 L161,302 L179,302 L184,309 L188,309 L188,313 Z" />
    <circle class="h-icon-fill" cx="160" cy="314" r="3.2" />
    <circle class="h-icon-fill" cx="180" cy="314" r="3.2" />
    <text class="h-label" x="170" y="346" text-anchor="middle">Véhicule</text>
  </g>
</svg>'''

# ---------------------------------------------------------------- icons
ICON_README = '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 3h7l4 4v14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v4h4"/><path d="M9 13h7M9 17h7M9 9h3"/></svg>'''

ICON_ARCH = '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 3 8l9 5 9-5-9-5z"/><path d="M3 13l9 5 9-5"/><path d="M3 18l9 5 9-5"/></svg>'''

ICON_KNX = '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="12" cy="19" r="2"/><circle cx="12" cy="12" r="2"/><path d="M6.8 6.3 10.3 10.7M17.2 6.3 13.7 10.7M12 14v3"/></svg>'''

ICON_ROADMAP = '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M15 9l-2 6-6 2 2-6 6-2z"/></svg>'''

# ---------------------------------------------------------------- token -> css var
TOKEN_CSS = {
    "c-ha": "var(--ambre)",
    "c-prom": "var(--glacier)",
    "c-vm": "var(--glacier)",
    "c-grafana": "var(--glacier)",
    "c-cuivre": "var(--cuivre)",
    "c-mousse": "var(--mousse)",
    "c-glacier": "var(--glacier)",
    "c-ambre": "var(--ambre)",
}

STATUS_LABEL = {"done": "Fait", "wip": "En cours", "todo": "À faire"}


def esc(s):
    return html.escape(s, quote=False)


def build_arch_services():
    out = []
    for name, container, host, token, desc in ARCH_SERVICES:
        css = TOKEN_CSS.get(token, "var(--ink-faint)")
        out.append(
            '<div class="svc-card" style="--sc:{css}">'
            '<h4><span class="dot"></span>{name}</h4>'
            '<div class="host">{container} &middot; {host}</div>'
            '<p>{desc}</p>'
            '</div>'.format(
                css=css, name=esc(name), container=esc(container),
                host=esc(host), desc=esc(desc),
            )
        )
    return "\n".join(out)


def build_roadmap():
    out = []
    for group in ROADMAP:
        css = TOKEN_CSS.get(group["color"], "var(--ink-faint)")
        items = []
        for status, title, desc in group["items"]:
            items.append(
                '<div class="rm-item">'
                '<span class="rm-status {status}">{label}</span>'
                '<div><h4>{title}</h4><p>{desc}</p></div>'
                '</div>'.format(
                    status=status, label=STATUS_LABEL[status],
                    title=esc(title), desc=esc(desc),
                )
            )
        out.append(
            '<div class="rm-group" style="--gcolor:{css}">'
            '<h3>{title}</h3>'
            '<div class="rm-list">{items}</div>'
            '</div>'.format(css=css, title=esc(group["title"]), items="".join(items))
        )
    return "\n".join(out)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    template = open(os.path.join(here, 'template.html'), encoding='utf-8').read()
    readme_body = open(os.path.join(here, 'readme_body.html'), encoding='utf-8').read()
    diagram_svg = open(os.path.join(here, 'diagram.svg'), encoding='utf-8').read()

    out = template
    # Photo bannière : asset statique servi par nginx (docs_site/assets/), pas de base64.
    assert out.count('data:image/jpeg;base64,__BANNER_B64__') == 1
    out = out.replace('data:image/jpeg;base64,__BANNER_B64__', '/assets/villa-bulle-banner.jpg')

    replacements = {
        '__ICON_README__': ICON_README,
        '__ICON_ARCH__': ICON_ARCH,
        '__ICON_KNX__': ICON_KNX,
        '__ICON_ROADMAP__': ICON_ROADMAP,
        '__HOUSE_SVG__': HOUSE_SVG,
        '__README_BODY__': readme_body,
        '__DIAGRAM_SVG__': diagram_svg,
        '__ARCH_SERVICES__': build_arch_services(),
        '__ROADMAP__': build_roadmap(),
    }
    for key, val in replacements.items():
        count = out.count(key)
        assert count == 1, f"placeholder {key} trouvé {count} fois"
        out = out.replace(key, val)

    out_path = os.path.join(here, 'index.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(out)
    print("écrit", out_path, ":", len(out), "caractères")
    print("-> à copier ensuite vers docs_site/index.html")


if __name__ == '__main__':
    main()
