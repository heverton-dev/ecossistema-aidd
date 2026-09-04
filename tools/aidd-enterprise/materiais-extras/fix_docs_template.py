import re

with open('templates/v2/docs.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the sidebar chapters
sidebar_pattern = re.compile(r'(<aside[^>]+>\s*<div[^>]+>Capítulos do Guia</div>\s*)<a.*?(<a href="#cap11".*?</aside>)', re.DOTALL)
html = sidebar_pattern.sub(r'\1__SIDEBAR_LINKS__\n            \2', html)

# Replace the sections cap1 to cap10
sections_pattern = re.compile(r'(<!-- CAPÍTULO 1 -->.*?</section>)\s*<!-- CAPÍTULO 11: DESIGN SYSTEM OFICIAL DA PLATAFORMA -->', re.DOTALL)
html = sections_pattern.sub(r'__MODULE_DOCS__\n\n            <!-- CAPÍTULO 11: DESIGN SYSTEM OFICIAL DA PLATAFORMA -->', html)

# Limpar o Spotlight commands hardcoded
spotlight_pattern = re.compile(r'const SPOTLIGHT_COMMANDS = \[[^\]]+\];', re.DOTALL)
html = spotlight_pattern.sub('const SPOTLIGHT_COMMANDS = __SPOTLIGHT_COMMANDS__;', html)

with open('templates/v2/docs.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Template base docs.html preparado.")
