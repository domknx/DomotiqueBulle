import markdown
from architecture_view import render_macro_grid

src = open('README_no_mermaid.md', encoding='utf-8').read()

html = markdown.markdown(
    src,
    extensions=['fenced_code', 'tables', 'toc', 'sane_lists'],
    extension_configs={'toc': {'permalink': False}}
)

# Le diagramme mermaid statique du README est remplacé par la même vue macro
# interactive que la page Architecture — cliquer une zone y bascule direct
# (goArch), pas besoin de la régénérer séparément.
arch_embed = (
    '<div class="diagram-embed">'
    '<p class="arch-embed-hint">Vue macro interactive — cliquez une zone pour '
    'explorer ses services et leurs dépendances (détail complet dans '
    '<a href="#architecture" onclick="showView(\'architecture\');return false;">'
    'Architecture logicielle</a>).</p>'
    + render_macro_grid() +
    '</div>'
)
html = html.replace('<p>{{MERMAID_DIAGRAM}}</p>', arch_embed)

open('readme_body.html', 'w', encoding='utf-8').write(html)
print(len(html), 'chars of HTML')
