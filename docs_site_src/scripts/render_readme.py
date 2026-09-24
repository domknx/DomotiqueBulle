import markdown
from architecture_overview import render_overview_frame

src = open('README_no_mermaid.md', encoding='utf-8').read()

html = markdown.markdown(
    src,
    extensions=['fenced_code', 'tables', 'toc', 'sane_lists'],
    extension_configs={'toc': {'permalink': False}}
)

# Le diagramme mermaid statique du README est remplacé par le même schéma
# unique (SVG statique, regroupé par domaine) que la vue Architecture
# logicielle — pas besoin de le régénérer séparément. Enveloppé dans le
# widget de zoom/pan (12.09.2026) ; uid distinct de la vue Architecture
# puisque les deux instances coexistent dans le DOM (vues cachées, pas
# détruites).
arch_embed = render_overview_frame('readme')
html = html.replace('<p>{{MERMAID_DIAGRAM}}</p>', arch_embed)

open('readme_body.html', 'w', encoding='utf-8').write(html)
print(len(html), 'chars of HTML')
