import re
content = open('README.md', encoding='utf-8').read()
m = re.search(r'```mermaid\n(.*?)\n```', content, re.DOTALL)
mermaid_src = m.group(1)
open('diagram.mmd', 'w', encoding='utf-8').write(mermaid_src)

# Replace the mermaid block with a placeholder marker for later HTML injection
content_no_mermaid = content[:m.start()] + '{{MERMAID_DIAGRAM}}' + content[m.end():]
open('README_no_mermaid.md', 'w', encoding='utf-8').write(content_no_mermaid)
print("mermaid extracted:", len(mermaid_src), "chars")
print("remaining md:", len(content_no_mermaid), "chars")
