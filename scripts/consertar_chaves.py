from pathlib import Path

def consertar_chaves(caminho: Path):
    txt = caminho.read_text(encoding='utf-8')
    txt = txt.replace('{{{{ cookiecutter.suite_name }}}}', '{{ cookiecutter.suite_name }}')
    txt = txt.replace('{{{{ cookiecutter.suite_slug }}}}', '{{ cookiecutter.suite_slug }}')
    caminho.write_text(txt, encoding='utf-8')
    print(f"Corrigidas chaves em {caminho}")

for c in [
    Path('modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/cookiecutter-scaffold/suite/{{cookiecutter.suite_slug}}/server.py.j2'),
    Path('modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/templates/cookiecutter-scaffold/suite/{{cookiecutter.suite_slug}}/server.py.j2')
]:
    if c.exists():
        consertar_chaves(c)
