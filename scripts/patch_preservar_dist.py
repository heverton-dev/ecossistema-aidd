from pathlib import Path

def corrigir_ignorar_build():
    # 1. provision_project.py
    p1 = Path('modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/scripts/provision_project.py')
    c1 = p1.read_text(encoding='utf-8')
    antigo1 = "return {'node_modules', 'dist', '.git', '__pycache__'}.intersection(names)"
    novo1 = "return {'node_modules', '.git', '__pycache__'}.intersection(names)"
    if antigo1 in c1:
        c1 = c1.replace(antigo1, novo1)
        p1.write_text(c1, encoding='utf-8')
        print(f"Atualizado {p1}: preservando frontend/dist na cópia do template!")
    else:
        print(f"Não encontrado em {p1}")

    # 2. tanstack_exporter.py
    p2 = Path('componentes/compartilhado/src-core/tanstack_exporter.py')
    c2 = p2.read_text(encoding='utf-8')
    antigo2 = 'return {"node_modules", "dist", ".git", "__pycache__", ".turbo"}.intersection(names)'
    novo2 = 'return {"node_modules", ".git", "__pycache__", ".turbo"}.intersection(names)'
    if antigo2 in c2:
        c2 = c2.replace(antigo2, novo2)
        p2.write_text(c2, encoding='utf-8')
        print(f"Atualizado {p2}: preservando frontend/dist na exportação TanStack!")
    else:
        print(f"Não encontrado em {p2}")

if __name__ == '__main__':
    corrigir_ignorar_build()
