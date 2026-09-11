import markdown
from architecture_overview import render_overview_svg

src = open('README_no_mermaid.md', encoding='utf-8').read()

html = markdown.markdown(
    src,
    extensions=['fenced_code', 'tables', 'toc', 'sane_lists'],
    extension_configs={'toc': {'permalink': False}}
)

# Le diagramme mermaid statique du README est remplacé par le même schéma
# unique (SVG statique, regroupé par domaine) que la vue Architecture
# logicielle — pas besoin de le régénérer séparément.
arch_embed = '<div class="arch-overview-frame">' + render_overview_svg() + '</div>'
html = html.replace('<p>{{MERMAID_DIAGRAM}}</p>', arch_embed)

open('readme_body.html', 'w', encoding='utf-8').write(html)
print(len(html), 'chars of HTML')
