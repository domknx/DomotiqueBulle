import markdown

src = open('README_no_mermaid.md', encoding='utf-8').read()
diagram_svg = open('diagram.svg', encoding='utf-8').read()

html = markdown.markdown(
    src,
    extensions=['fenced_code', 'tables', 'toc', 'sane_lists'],
    extension_configs={'toc': {'permalink': False}}
)

html = html.replace('<p>{{MERMAID_DIAGRAM}}</p>', f'<div class="diagram-embed">{diagram_svg}</div>')

open('readme_body.html', 'w', encoding='utf-8').write(html)
print(len(html), 'chars of HTML')
