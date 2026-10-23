import os
from pathlib import Path

def aplicar_patch_compose_suite(caminho_arq: Path):
    conteudo = caminho_arq.read_text(encoding='utf-8')

    alvo = '    identidade_paleta = f"{suite_name} {\' \'.join(module_slugs)}"'
    substituicao = '''    # Carrega módulos dinamicamente do PLANNER.json para o Quarteto (Lei #10)
    if project_dir and (not module_slugs or module_slugs == ["modulo1"]):
        for p_cand in [os.path.join(project_dir, "PLANNER.json"), os.path.join(project_dir, "HANDOFF_PLANNER_ENGINE.json")]:
            if os.path.isfile(p_cand):
                try:
                    import json
                    with open(p_cand, "r", encoding="utf-8") as fp:
                        dados_pl = json.load(fp)
                        mods_pl = [m.get("slug") for m in dados_pl.get("modulos_funcionais", []) if m.get("slug")]
                        if mods_pl:
                            module_slugs = mods_pl
                            break
                except Exception:
                    pass

    identidade_paleta = f"{suite_name} {\' \'.join(module_slugs)}"'''

    if alvo in conteudo and "Carrega módulos dinamicamente do PLANNER.json" not in conteudo:
        conteudo = conteudo.replace(alvo, substituicao)
        caminho_arq.write_text(conteudo, encoding='utf-8')
        print(f"compose_suite.py atualizado: {caminho_arq}")
    else:
        print(f"Já atualizado ou não encontrado em: {caminho_arq}")

caminhos = [
    Path('modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/scripts/compose_suite.py'),
    Path('modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/scripts/compose_suite.py')
]

for c in caminhos:
    if c.exists():
        aplicar_patch_compose_suite(c)
