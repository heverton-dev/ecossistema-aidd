# -*- coding: utf-8 -*-
"""
Testes do gate G_HONESTIDADE_ROTULO — valida deteccao de linguagem de
marketing em mensagens de print()/raise() de scripts de gate, executando o
gate real (copiado) contra uma arvore sintetica isolada em tmp_path (nunca
contra o repositorio de producao — ver regra de isolamento em
docs/planos/a-fazer/02-direcionamento-estrategico-anti-nih/
00-PROCESSO-E-DECISOES.md §4).

Cada teste E a reproducao exigida pela Definicao de Pronto do item: insere
um termo proibido temporario (fixture sintetica), roda o gate, confirma que
ele pega, e o tmp_path e descartado pelo pytest ao final (reversao
automatica).
"""

import os
import shutil

from _gate_test_utils import rodar_gate

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_HONESTIDADE_ROTULO.py")
TERMOS_PATH = os.path.join(GATE_DIR, "termos_proibidos_marketing.json")


def _preparar_gates_sintetico(root_dir):
    """Copia o gate real + a lista de termos pra gates/ dentro do tmp_path."""
    gdir = os.path.join(root_dir, "gates")
    os.makedirs(gdir, exist_ok=True)
    shutil.copyfile(GATE_PATH, os.path.join(gdir, "G_HONESTIDADE_ROTULO.py"))
    shutil.copyfile(TERMOS_PATH, os.path.join(gdir, "termos_proibidos_marketing.json"))
    return gdir


def test_gate_limpo_aprova(tmp_path):
    gdir = _preparar_gates_sintetico(tmp_path)
    outro_gate = os.path.join(gdir, "G_EXEMPLO.py")
    with open(outro_gate, "w", encoding="utf-8") as f:
        f.write(
            "# -*- coding: utf-8 -*-\n"
            "def checar():\n"
            "    print('[OK] Auditoria de Configuracao — 4/21 checks funcionais.')\n"
            "    return 0\n"
        )

    res = rodar_gate(os.path.join(gdir, "G_HONESTIDADE_ROTULO.py"), tmp_path)
    assert res.returncode == 0
    assert "Quality Gate G_HONESTIDADE_ROTULO APROVADO" in res.stdout


def test_termo_proibido_em_print_e_detectado(tmp_path):
    gdir = _preparar_gates_sintetico(tmp_path)
    gate_com_marketing = os.path.join(gdir, "G_EXEMPLO.py")
    # Termo proibido inserido TEMPORARIAMENTE só nesta fixture sintetica de
    # tmp_path — nunca no repositorio real. Reproduz literalmente o achado
    # real de tools/*/scripts/gates/G_SEGURANCA.py.
    with open(gate_com_marketing, "w", encoding="utf-8") as f:
        f.write(
            "# -*- coding: utf-8 -*-\n"
            "def checar():\n"
            "    print('Score de Blindagem: 100.0% (NOTA A+)')\n"
            "    return 0\n"
        )

    res = rodar_gate(os.path.join(gdir, "G_HONESTIDADE_ROTULO.py"), tmp_path)
    assert res.returncode == 1
    assert "Quality Gate REPROVADO" in res.stdout
    assert "G_EXEMPLO.py:3" in res.stdout
    assert "'nota a+'" in res.stdout
    # tmp_path e descartado pelo pytest ao fim do teste — reversao automatica.


def test_termo_proibido_em_raise_e_detectado(tmp_path):
    gdir = _preparar_gates_sintetico(tmp_path)
    gate_com_marketing = os.path.join(gdir, "G_EXEMPLO.py")
    with open(gate_com_marketing, "w", encoding="utf-8") as f:
        f.write(
            "# -*- coding: utf-8 -*-\n"
            "def checar():\n"
            "    raise RuntimeError('Aplicacao homologada para producao global')\n"
        )

    res = rodar_gate(os.path.join(gdir, "G_HONESTIDADE_ROTULO.py"), tmp_path)
    assert res.returncode == 1
    assert "'homologado para producao global'" in res.stdout or "'homologada para producao global'" in res.stdout


def test_termo_em_docstring_ou_comentario_nao_e_falso_positivo(tmp_path):
    gdir = _preparar_gates_sintetico(tmp_path)
    gate_com_comentario = os.path.join(gdir, "G_EXEMPLO.py")
    with open(gate_com_comentario, "w", encoding="utf-8") as f:
        f.write(
            "# -*- coding: utf-8 -*-\n"
            '"""Este docstring so MENCIONA blindagem militar como exemplo do que NAO fazer."""\n'
            "# comentario tambem citando nota a+ como exemplo proibido\n"
            "def checar():\n"
            "    print('[OK] tudo certo')\n"
            "    return 0\n"
        )

    res = rodar_gate(os.path.join(gdir, "G_HONESTIDADE_ROTULO.py"), tmp_path)
    assert res.returncode == 0
    assert "Quality Gate G_HONESTIDADE_ROTULO APROVADO" in res.stdout


def test_arquivo_de_teste_e_utilitario_sao_ignorados(tmp_path):
    gdir = _preparar_gates_sintetico(tmp_path)
    # test_*.py e _privado.py nao sao o script do gate em si — nao devem ser
    # auditados, mesmo contendo termo proibido.
    with open(os.path.join(gdir, "test_g_exemplo.py"), "w", encoding="utf-8") as f:
        f.write("def test_algo():\n    print('nota a+')\n")
    with open(os.path.join(gdir, "_util.py"), "w", encoding="utf-8") as f:
        f.write("def helper():\n    print('nota a+')\n")

    res = rodar_gate(os.path.join(gdir, "G_HONESTIDADE_ROTULO.py"), tmp_path)
    assert res.returncode == 0
    assert "Quality Gate G_HONESTIDADE_ROTULO APROVADO" in res.stdout
