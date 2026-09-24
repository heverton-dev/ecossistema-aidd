# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — TESTE DOS CICLOS NUMERADOS DE AUDITORIA 4F
=============================================================================
Regressão real (2026-09-24): rodar de novo o pipeline numa ferramenta já
auditada (aidd-melhoria) pulava as 4 fases pelo cache ("arquivo já existe"),
não chamava nenhum agente e imprimia "PIPELINE FINALIZADO COM SUCESSO!".

Regras:
  1. Cada rodada vive em docs/auditoria/<f>/ciclo-NN/. G_auditoria_15D.py fica
     na raiz da ferramenta (compartilhado).
  2. Scaffold: sem ciclo -> ciclo-01; ciclo vigente incompleto (sem
     LAUDO-15D-REVISADO.md) -> retoma o mesmo; ciclo concluído -> abre o próximo.
  3. Todos os output_handoff do manifesto ficam DENTRO do ciclo (cache por ciclo;
     a Fase 3 entrega RELATORIO-CONSTRUTOR.md, não um diretório de código).
  4. Ciclo >= 2: DOD herdado do anterior e Fase 1 recebe o laudo revisado
     anterior para registrar Nota Anterior -> Nota Nova.
  5. Layout plano legado é migrado para ciclo-01 com os caminhos reescritos.
  6. Orquestrador com tudo em cache NÃO declara sucesso: avisa "NADA A FAZER".
=============================================================================
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from scaffold_auditoria import criar_scaffold_auditoria, ciclo_vigente  # noqa: E402
from compilador_plano_evolucao import compilar_plano_evolucao  # noqa: E402

PAPEIS = ("inspetor", "arquiteto", "construtor", "retorno")
CONFIG = {
    "pipeline_auditoria_4f": {p: {"harness": f"h-{p}", "model": f"m-{p}", "comando_terminal": f"cmd-{p}"} for p in PAPEIS},
    "pipeline_evolucao_rotativo": [{"harness": "h1", "model": "m1", "comando_terminal": "cmd1"}],
}


def _repo(tmp_path: Path) -> Path:
    auditoria = tmp_path / "docs" / "auditoria"
    auditoria.mkdir(parents=True)
    (auditoria / "CONFIG-EXECUCAO-USUARIO.json").write_text(json.dumps(CONFIG), encoding="utf-8")
    return tmp_path


def _concluir(ciclo: Path) -> None:
    (ciclo / "LAUDO-15D-REVISADO.md").write_text("laudo revisado", encoding="utf-8")


def test_primeira_rodada_cria_ciclo_01_e_gate_na_raiz(tmp_path):
    repo = _repo(tmp_path)
    ciclo = criar_scaffold_auditoria("ferramenta-x", repo_root=repo)
    raiz = repo / "docs" / "auditoria" / "ferramenta-x"

    assert ciclo == raiz / "ciclo-01"
    assert (raiz / "G_auditoria_15D.py").exists()
    assert not (ciclo / "G_auditoria_15D.py").exists()
    for nome in ("DOD.md", "MANIFESTO-4F.json", "PROMPT-FASE-1-INSPETOR.txt", "PROMPT-FASE-2-ARQUITETO.txt",
                 "PROMPT-FASE-3-CONSTRUTOR.txt", "PROMPT-FASE-4-RETORNO.txt"):
        assert (ciclo / nome).exists(), nome


def test_ciclo_incompleto_e_retomado(tmp_path):
    repo = _repo(tmp_path)
    primeiro = criar_scaffold_auditoria("ferramenta-x", repo_root=repo)
    (primeiro / "LAUDO-15D-INICIAL.md").write_text("laudo", encoding="utf-8")

    assert criar_scaffold_auditoria("ferramenta-x", repo_root=repo) == primeiro
    assert not (primeiro.parent / "ciclo-02").exists()


def test_ciclo_concluido_abre_o_proximo_herdando_dod(tmp_path):
    repo = _repo(tmp_path)
    primeiro = criar_scaffold_auditoria("ferramenta-x", repo_root=repo)
    (primeiro / "DOD.md").write_text("# DoD evoluido no ciclo 1\n", encoding="utf-8")
    _concluir(primeiro)

    segundo = criar_scaffold_auditoria("ferramenta-x", repo_root=repo)
    assert segundo == primeiro.parent / "ciclo-02"
    assert (segundo / "DOD.md").read_text(encoding="utf-8") == "# DoD evoluido no ciclo 1\n"

    f1 = (segundo / "PROMPT-FASE-1-INSPETOR.txt").read_text(encoding="utf-8")
    assert "docs/auditoria/ferramenta-x/ciclo-01/LAUDO-15D-REVISADO.md" in f1
    assert "docs/auditoria/ferramenta-x/ciclo-02/LAUDO-15D-INICIAL.md" in f1


def test_todos_os_handoffs_do_manifesto_ficam_dentro_do_ciclo(tmp_path):
    repo = _repo(tmp_path)
    ciclo = criar_scaffold_auditoria("ferramenta-x", repo_root=repo)
    fases = json.loads((ciclo / "MANIFESTO-4F.json").read_text(encoding="utf-8"))["fases"]

    prefixo = "docs/auditoria/ferramenta-x/ciclo-01/"
    for f in fases:
        assert f["output_handoff"].startswith(prefixo), f
        assert f["input_prompt"].startswith(prefixo), f
    assert fases[2]["output_handoff"] == prefixo + "RELATORIO-CONSTRUTOR.md"


def test_layout_plano_legado_migra_para_ciclo_01(tmp_path):
    repo = _repo(tmp_path)
    raiz = repo / "docs" / "auditoria" / "ferramenta-x"
    (raiz / "prompts_tickets").mkdir(parents=True)
    (raiz / "LAUDO-15D-INICIAL.md").write_text("inicial", encoding="utf-8")
    (raiz / "LAUDO-15D-REVISADO.md").write_text("revisado", encoding="utf-8")
    (raiz / "G_auditoria_15D.py").write_text("# gate", encoding="utf-8")
    (raiz / "prompts_tickets" / "PROMPT-TICKET-01.txt").write_text("x", encoding="utf-8")
    (raiz / "MANIFESTO-4F.json").write_text(json.dumps(
        {"fases": [{"output_handoff": "docs/auditoria/ferramenta-x/LAUDO-15D-INICIAL.md",
                    "gate": "docs/auditoria/ferramenta-x/G_auditoria_15D.py"}]}), encoding="utf-8")

    ciclo = criar_scaffold_auditoria("ferramenta-x", repo_root=repo)

    migrado = raiz / "ciclo-01"
    assert (migrado / "LAUDO-15D-INICIAL.md").read_text(encoding="utf-8") == "inicial"
    assert (migrado / "prompts_tickets" / "PROMPT-TICKET-01.txt").exists()
    assert not (raiz / "LAUDO-15D-INICIAL.md").exists()
    assert (raiz / "G_auditoria_15D.py").exists()
    # ciclo-01 migrado ja estava concluido -> a nova rodada abre o ciclo-02
    assert ciclo == raiz / "ciclo-02"


def test_migracao_reescreve_caminhos_do_ciclo_mas_nao_do_gate(tmp_path):
    repo = _repo(tmp_path)
    raiz = repo / "docs" / "auditoria" / "ferramenta-x"
    raiz.mkdir(parents=True)
    (raiz / "RELATORIO-TECNICO.md").write_text(
        "python docs/auditoria/ferramenta-x/G_auditoria_15D.py docs/auditoria/ferramenta-x/LAUDO-15D-REVISADO.md\n",
        encoding="utf-8")

    criar_scaffold_auditoria("ferramenta-x", repo_root=repo)
    texto = (raiz / "ciclo-01" / "RELATORIO-TECNICO.md").read_text(encoding="utf-8")
    assert texto == ("python docs/auditoria/ferramenta-x/G_auditoria_15D.py "
                     "docs/auditoria/ferramenta-x/ciclo-01/LAUDO-15D-REVISADO.md\n")


def test_ciclo_vigente_e_o_ultimo(tmp_path):
    repo = _repo(tmp_path)
    raiz = repo / "docs" / "auditoria" / "ferramenta-x"
    assert ciclo_vigente(raiz) is None
    for n in ("ciclo-01", "ciclo-02", "ciclo-10"):
        (raiz / n).mkdir(parents=True)
    assert ciclo_vigente(raiz) == raiz / "ciclo-10"


def test_compilador_usa_nome_da_ferramenta_e_nao_do_ciclo(tmp_path):
    repo = _repo(tmp_path)
    ciclo = criar_scaffold_auditoria("ferramenta-x", repo_root=repo)
    md = ciclo / "PLANO-EVOLUCAO.md"
    md.write_text("""### Ticket 1: Ajuste (Refere-se a D11)
- **Falha 15-D:** `D11. Fallback`
- **Artefato de Handoff:** `gates/G_x.py`
- **Construtor Prompt (EN):**
  - Create gate.
""", encoding="utf-8")

    manifesto = json.loads(Path(compilar_plano_evolucao(md, repo / "docs" / "auditoria" / "CONFIG-EXECUCAO-USUARIO.json")).read_text(encoding="utf-8"))
    assert manifesto["target_tool"] == "ferramenta-x"
    assert manifesto["pipeline_id"] == "evolucao-ferramenta-x-ciclo-01"
    assert "Target tool: ferramenta-x." in (ciclo / "prompts_tickets" / "PROMPT-TICKET-01.txt").read_text(encoding="utf-8")


def test_gate_15d_sem_argumento_valida_o_ciclo_vigente(tmp_path):
    repo = _repo(tmp_path)
    ciclo = criar_scaffold_auditoria("ferramenta-x", repo_root=repo)
    gate = ciclo.parent / "G_auditoria_15D.py"

    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    (ciclo / "LAUDO-15D-INICIAL.md").write_text("vazio", encoding="utf-8")
    ruim = subprocess.run([sys.executable, str(gate)], capture_output=True, text=True, encoding="utf-8", env=env)
    assert ruim.returncode == 1
    assert "ciclo-01" in ruim.stdout

    corpo = "\n".join(f"D{i}. ok" for i in range(1, 16)) + "\nMatriz de Avaliação da Execução\n"
    (ciclo / "LAUDO-15D-INICIAL.md").write_text(corpo, encoding="utf-8")
    bom = subprocess.run([sys.executable, str(gate)], capture_output=True, text=True, encoding="utf-8", env=env)
    assert bom.returncode == 0


def test_orquestrador_com_tudo_em_cache_nao_declara_sucesso(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "base"],
                   cwd=tmp_path, check=True)
    handoff = tmp_path / "saida.md"
    handoff.write_text("ja existe", encoding="utf-8")
    manifesto = tmp_path / "m.json"
    manifesto.write_text(json.dumps({"pipeline_id": "t", "fases": [
        {"nome": "Fase_1_Inspetor", "comando_terminal": "x", "output_handoff": "saida.md", "input_prompt": "p.txt"}
    ]}), encoding="utf-8")

    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    res = subprocess.run([sys.executable, str(ROOT_DIR / "scripts" / "orquestrador_4f.py"), "--manifest", str(manifesto)],
                         cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", env=env)
    assert res.returncode == 0
    assert "NADA A FAZER" in res.stdout
    assert "FINALIZADO COM SUCESSO" not in res.stdout
    assert "scaffold_auditoria.py" in res.stdout


def test_manifestos_declaram_gate_por_fase_e_gate_final(tmp_path):
    repo = _repo(tmp_path)
    ciclo = criar_scaffold_auditoria("ferramenta-x", repo_root=repo)
    m = json.loads((ciclo / "MANIFESTO-4F.json").read_text(encoding="utf-8"))
    c = "docs/auditoria/ferramenta-x/ciclo-01"
    gate15 = "python docs/auditoria/ferramenta-x/G_auditoria_15D.py"

    assert m["gate_final"] == "python ecossistema.py audit"
    assert [f["gate_fase"] for f in m["fases"]] == [
        f"{gate15} {c}/LAUDO-15D-INICIAL.md",
        f"python scripts/compilador_plano_evolucao.py --plano {c}/PLANO-EVOLUCAO.md",
        "python -m pytest -q -p no:cacheprovider tests",
        f"{gate15} {c}/LAUDO-15D-REVISADO.md",
    ]

    md = ciclo / "PLANO-EVOLUCAO.md"
    md.write_text("""### Ticket 1: Ajuste (Refere-se a D11)
- **Falha 15-D:** `D11. Fallback`
- **Artefato de Handoff:** `gates/G_x.py`
- **Construtor Prompt (EN):**
  - Create gate.
""", encoding="utf-8")
    plano = json.loads(Path(compilar_plano_evolucao(md, repo / "docs" / "auditoria" / "CONFIG-EXECUCAO-USUARIO.json")).read_text(encoding="utf-8"))
    assert plano["gate_final"] == "python ecossistema.py audit"
    assert plano["fases"][0]["gate_fase"] == "python -m pytest -q -p no:cacheprovider tests"
