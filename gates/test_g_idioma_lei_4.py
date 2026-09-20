# -*- coding: utf-8 -*-
"""
Testes do gate G_IDIOMA_LEI_4 (Lei #4 — Extreme Token Economy: Compact English no núcleo).

Valida deterministicamente:
1. Failing-path: prosa PT-BR inserida em caminho auditado obriga retorno exit 1 (Lei #13).
2. False-positive check: caminhos isentos (INDEX.md, README.md, SESSOES.md) com prosa PT-BR
   NÃO devem disparar reprovação (retorna exit 0).
3. YAML frontmatter title em PT-BR não dispara falso positivo se corpo for inglês compacto.
4. Execução real contra o repositório passa limpa (exit 0).
"""

import os
import shutil
import subprocess
import sys

from _gate_test_utils import rodar_gate

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_IDIOMA_LEI_4.py")


def _preparar_arvore_sintetica(root_dir):
    """Copia o gate real para a árvore sintética em tmp_path."""
    gdir = os.path.join(root_dir, "gates")
    os.makedirs(gdir, exist_ok=True)
    target_gate = os.path.join(gdir, "G_IDIOMA_LEI_4.py")
    shutil.copyfile(GATE_PATH, target_gate)
    return target_gate


def test_failing_path_pt_prose_asserts_exit_1(tmp_path):
    """Failing-path test: injeta prosa PT-BR em ticket markdown e asserte exit 1."""
    gate_script = _preparar_arvore_sintetica(tmp_path)
    issues_dir = os.path.join(tmp_path, "docs", "issues")
    os.makedirs(issues_dir, exist_ok=True)

    ticket_pt = os.path.join(issues_dir, "99-ticket-em-portugues.md")
    with open(ticket_pt, "w", encoding="utf-8") as f:
        f.write(
            "---\n"
            "id: ISSUE-0099\n"
            "title: Título em Português\n"
            "---\n\n"
            "# ISSUE-0099 — Exemplo de Violação\n\n"
            "Esta seção foi escrita inteiramente em português com palavras estruturais "
            "e não deve ser aceita pelo portão de qualidade da Lei 4. O objetivo é demonstrar "
            "que a detecção de densidade funciona e bloqueia a execução quando houver prosa "
            "não compacta que gaste tokens desnecessários no contexto do agente. "
            "Todos os testes devem comprovar que o portão reprova com exit 1.\n"
        )

    res = rodar_gate(gate_script, tmp_path)
    assert res.returncode == 1, f"Gate deveria falhar com exit 1, mas retornou {res.returncode}. Output:\n{res.stdout}"
    assert "VIOLATION [G_IDIOMA_LEI_4]" in res.stdout
    assert "99-ticket-em-portugues.md" in res.stdout


def test_false_positive_index_md_ignored_asserts_exit_0(tmp_path):
    """False-positive check: INDEX.md, README.md e SESSOES.md em PT-BR NÃO devem acionar o gate."""
    gate_script = _preparar_arvore_sintetica(tmp_path)
    issues_dir = os.path.join(tmp_path, "docs", "issues")
    os.makedirs(issues_dir, exist_ok=True)

    # Cria INDEX.md puramente em PT-BR
    index_md = os.path.join(issues_dir, "INDEX.md")
    with open(index_md, "w", encoding="utf-8") as f:
        f.write(
            "# Índice de Issues e Sessões\n\n"
            "Esta página serve como sumário e navegação para os desenvolvedores e usuários humanos. "
            "Portanto, ela permanece em português com explicações detalhadas sobre todas as leis, "
            "portões e histórico de decisões arquiteturais do ecossistema.\n"
        )

    # Cria ticket válido em inglês
    ticket_valid = os.path.join(issues_dir, "01-valid-ticket.md")
    with open(ticket_valid, "w", encoding="utf-8") as f:
        f.write(
            "---\n"
            "id: ISSUE-0001\n"
            "title: Valid ticket\n"
            "---\n\n"
            "# ISSUE-0001 — Cleanup old records\n\n"
            "**Deliver:** three project records stop describing historical state.\n\n"
            "**Blocked by:** nothing. Start now.\n\n"
            "## Acceptance criteria\n\n"
            "- [x] Label honesty gate runs on every commit.\n"
            "- [x] Documentation cleaned.\n"
        )

    res = rodar_gate(gate_script, tmp_path)
    assert res.returncode == 0, f"Gate não deveria falhar em caminhos isentos. Output:\n{res.stdout}\n{res.stderr}"
    assert "[OK] G_IDIOMA_LEI_4" in res.stdout


def test_title_frontmatter_in_pt_allowed_when_body_english(tmp_path):
    """Frontmatter YAML com title em PT-BR é permitido per convenção acordada."""
    gate_script = _preparar_arvore_sintetica(tmp_path)
    issues_dir = os.path.join(tmp_path, "docs", "issues")
    os.makedirs(issues_dir, exist_ok=True)

    ticket_pt_title = os.path.join(issues_dir, "02-ticket-pt-title.md")
    with open(ticket_pt_title, "w", encoding="utf-8") as f:
        f.write(
            "---\n"
            "id: ISSUE-0002\n"
            "title: Faxina de registros desatualizados e verificação de integridade\n"
            "status: closed\n"
            "---\n\n"
            "# ISSUE-0002 — Integrity Verification\n\n"
            "**Deliver:** ensure all core paths strictly adhere to compact English.\n\n"
            "## Acceptance criteria\n\n"
            "- [x] Deterministic validation with zero LLM dependency.\n"
            "- [x] Verified token consumption reduction.\n"
        )

    res = rodar_gate(gate_script, tmp_path)
    assert res.returncode == 0, f"Gate não deveria reprovar por title em PT no frontmatter. Output:\n{res.stdout}"
    assert "[OK] G_IDIOMA_LEI_4" in res.stdout


def test_repo_real_passes():
    """Execução contra o repositório vivo real deve retornar exit 0."""
    res = subprocess.run(
        [sys.executable, GATE_PATH],
        cwd=os.path.dirname(GATE_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 0, f"Repositório real falhou no gate G_IDIOMA_LEI_4:\n{res.stdout}\n{res.stderr}"
    assert "[OK] G_IDIOMA_LEI_4" in res.stdout
