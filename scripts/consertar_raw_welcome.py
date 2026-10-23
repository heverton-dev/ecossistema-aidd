from pathlib import Path

def consertar_raw_welcome(caminho: Path):
    txt = caminho.read_text(encoding='utf-8')
    antigo = '                html_welcome = f"""<!DOCTYPE html>'
    novo = '                {% raw %}html_welcome = f"""<!DOCTYPE html>'
    if antigo in txt and "{% raw %}html_welcome" not in txt:
        txt = txt.replace(antigo, novo)

    antigo_fim = '        <a href="/openapi.json" class="card"><div class="title">📊 OpenAPI Spec (/openapi.json)</div><div class="desc">JSON OpenAPI 3.1</div></a>\n    </div>\n</body>\n</html>"""'
    novo_fim = '        <a href="/openapi.json" class="card"><div class="title">📊 OpenAPI Spec (/openapi.json)</div><div class="desc">JSON OpenAPI 3.1</div></a>\n    </div>\n</body>\n</html>"""{% endraw %}'
    if antigo_fim in txt:
        txt = txt.replace(antigo_fim, novo_fim)

    caminho.write_text(txt, encoding='utf-8')
    print(f"Adicionado raw em welcome para: {caminho}")

for c in [
    Path('modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/cookiecutter-scaffold/suite/{{cookiecutter.suite_slug}}/server.py.j2'),
    Path('modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/templates/cookiecutter-scaffold/suite/{{cookiecutter.suite_slug}}/server.py.j2')
]:
    if c.exists():
        consertar_raw_welcome(c)
