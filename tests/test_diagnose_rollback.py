# -*- coding: utf-8 -*-
"""
Testes do Ticket 7 (D14 / DoD 7) - Limpeza da Instrumentação e Rollback para aidd-diagnose.

Exige o entregável .agents/skills/aidd-diagnose/scripts/rollback.py:
- Toda instrumentação temporária da Fase 4 é marcada com AIDD-DIAGNOSE-TEMP.
- Ao fim da Fase 5 (ou em exceção): varre o diff, remove linhas marcadas e
  descarta a worktree efêmera do Ticket 2 (worktrees_diagnose-<slug>).
- Em qualquer saída não-zero: zero arquivos parciais em docs/diagnosticos/.
"""

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPT = ROOT_DIR / ".agents" / "skills" / "aidd-diagnose" / "scripts" / "rollback.py"


def carregar_rollback():
    """Importa rollback.py do entregável (mesmo padrão de test_fallback_diagnose)."""
    assert SCRIPT.exists(), f"Entregável ausente: {SCRIPT}"
    spec = importlib.util.spec_from_file_location("aidd_diagnose_rollback", str(SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True, check=True
    )


def _novo_repo_git(tmp_path: Path) -> Path:
    """Mini-repo determinístico com um commit rastreado (alvo da instrumentação)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "audit@aidd.dev")
    _git(repo, "config", "user.name", "Audit Runner")
    (repo / "app.py").write_text("def process():\n    return 1\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    return repo


def _injetar_linha_marcada(arquivo: Path) -> None:
    """Injeta instrumentação temporária marcada (padrão da Fase 4)."""
    rb = carregar_rollback()
    linha = rb.marcar_instrumentacao_temporaria("print('instrumentacao_fase4')")
    arquivo.write_text(
        arquivo.read_text(encoding="utf-8") + linha + "\n", encoding="utf-8"
    )


def test_marcar_instrumentacao_temporaria_adiciona_marcador():
    """Toda linha de instrumentação temporária recebe o marcador da Fase 4."""
    rb = carregar_rollback()
    linha = rb.marcar_instrumentacao_temporaria("print('probe')")
    assert rb.MARCADOR_TEMP in linha
    assert linha.rstrip().endswith(rb.MARCADOR_TEMP)
    # Idempotente: já marcada não duplica o marcador.
    assert rb.marcar_instrumentacao_temporaria(linha) == linha


def test_fase5_final_remove_marcador_do_git_diff(tmp_path):
    """Injetar linha marcada e encerrar a Fase 5 => git diff sem o marcador."""
    rb = carregar_rollback()
    repo = _novo_repo_git(tmp_path)
    alvo = repo / "app.py"
    _injetar_linha_marcada(alvo)

    diff_antes = _git(repo, "diff").stdout
    assert rb.MARCADOR_TEMP in diff_antes, "pré-condição: diff contém a linha marcada"

    codigo = rb.finalizar_fase5(repo_root=repo)
    assert codigo == 0

    diff_depois = _git(repo, "diff").stdout
    assert rb.MARCADOR_TEMP not in diff_depois
    # Conteúdo rastreado restaurado ao estado original (só a linha marcada saiu).
    assert alvo.read_text(encoding="utf-8") == "def process():\n    return 1\n"


def test_excecao_no_meio_tambem_remove_marcador_do_diff(tmp_path):
    """Exceção no meio da execução: marcador sai do diff (mesmo caminho da Fase 5)."""
    rb = carregar_rollback()
    repo = _novo_repo_git(tmp_path)
    alvo = repo / "app.py"
    _injetar_linha_marcada(alvo)

    class CrashFase4(RuntimeError):
        pass

    with pytest.raises(CrashFase4):
        with rb.RollbackDiagnose(repo_root=repo):
            raise CrashFase4("crash no meio da Fase 4")

    diff = _git(repo, "diff").stdout
    assert rb.MARCADOR_TEMP not in diff


def test_crash_no_meio_zera_parciais_em_docs_diagnosticos(tmp_path):
    """Crash no meio da execução: zero arquivos parciais em docs/diagnosticos/."""
    rb = carregar_rollback()
    repo = _novo_repo_git(tmp_path)
    sessao = repo / "docs" / "diagnosticos" / "20260924_teste"
    sessao.mkdir(parents=True)
    sessao_json = sessao / "sessao.json"
    sessao_json.write_text('{"fase_atual": 4}\n', encoding="utf-8")
    original = sessao_json.read_bytes()

    parcial = sessao / "RELATORIO-CAUSA-RAIZ.md"
    parcial_parcial = sessao / "rascunho.tmp"
    arquivo_orfao = repo / "instrumentacao_orfa.py"

    class CrashFase4(RuntimeError):
        pass

    with pytest.raises(CrashFase4):
        with rb.RollbackDiagnose(repo_root=repo) as gestor:
            parcial.write_text("relatorio incompleto\n", encoding="utf-8")
            parcial_parcial.write_text("buffer parcial\n", encoding="utf-8")
            # Linha marcada também em arquivo rastreado do repo principal.
            _injetar_linha_marcada(repo / "app.py")
            # Arquivo novo untracked contendo APENAS instrumentação marcada.
            rb_mod = carregar_rollback()
            arquivo_orfao.write_text(
                rb_mod.marcar_instrumentacao_temporaria("print('orfao')") + "\n",
                encoding="utf-8",
            )
            gestor.registrar_temporario(parcial_parcial)
            raise CrashFase4("falha no meio da execução")

    assert not parcial.exists(), "arquivo parcial sobreviveu ao crash"
    assert not parcial_parcial.exists(), "temporário registrado sobreviveu ao crash"
    assert not arquivo_orfao.exists(), "arquivo untracked só-marcado sobreviveu ao crash"
    assert sessao_json.exists(), "arquivo pré-existente não pode ser deletado"
    assert sessao_json.read_bytes() == original, "conteúdo pré-existente deve ser restaurado"
    assert rb.MARCADOR_TEMP not in _git(repo, "diff").stdout


def test_saida_nao_zero_zera_parciais_em_docs_diagnosticos(tmp_path):
    """executar_com_rollback com código != 0: zero parciais + exit code real preservado."""
    rb = carregar_rollback()
    repo = _novo_repo_git(tmp_path)
    sessao = repo / "docs" / "diagnosticos" / "20260924_saida_nz"
    sessao.mkdir(parents=True)

    def operacao(gestor) -> int:
        parcial = sessao / "RELATORIO-CAUSA-RAIZ.md"
        parcial.write_text("parcial sem conclusão\n", encoding="utf-8")
        gestor.registrar_temporario(parcial)
        return 1

    codigo = rb.executar_com_rollback(operacao, repo_root=repo)

    assert codigo == 1
    assert not (sessao / "RELATORIO-CAUSA-RAIZ.md").exists()
    assert list(sessao.iterdir()) == [], "docs/diagnosticos deve ficar sem parciais"


def test_sucesso_preserva_relatorio_final_e_remove_temporarios(tmp_path):
    """Sucesso (exit 0): artefato final preservado, temporários removidos."""
    rb = carregar_rollback()
    repo = _novo_repo_git(tmp_path)
    sessao = repo / "docs" / "diagnosticos" / "20260924_sucesso"
    sessao.mkdir(parents=True)

    def operacao(gestor) -> int:
        final = sessao / "RELATORIO-CAUSA-RAIZ.md"
        final.write_text("RELATORIO-CAUSA-RAIZ completo\n", encoding="utf-8")
        temp = sessao / "buffer.tmp"
        temp.write_text("transitório\n", encoding="utf-8")
        gestor.registrar_temporario(temp)
        _injetar_linha_marcada(repo / "app.py")
        return 0

    codigo = rb.executar_com_rollback(operacao, repo_root=repo)

    assert codigo == 0
    assert (sessao / "RELATORIO-CAUSA-RAIZ.md").exists()
    assert not (sessao / "buffer.tmp").exists(), "temporário deve sair no commit"
    assert rb.MARCADOR_TEMP not in _git(repo, "diff").stdout


def test_descarta_worktree_efemera_do_ticket2(tmp_path):
    """Fase 5 / exceção descartam a worktree efêmera do Ticket 2 e sua branch."""
    rb = carregar_rollback()
    repo = _novo_repo_git(tmp_path)
    slug = "falha-conexao-banco"
    worktree = tmp_path / f"worktrees_diagnose-{slug}"
    _git(
        repo,
        "worktree",
        "add",
        "-b",
        f"diagnose/{slug}-abc123",
        str(worktree),
        "HEAD",
    )
    assert worktree.exists()

    codigo = rb.finalizar_fase5(repo_root=repo, slug=slug)

    assert codigo == 0
    assert not worktree.exists(), "worktree efêmera do Ticket 2 deve ser descartada"
    assert not (worktree.parent / f"worktrees_diagnose-{slug}").exists()
    branches = _git(repo, "branch", "--list").stdout
    assert f"diagnose/{slug}-abc123" not in branches


def test_worktree_descartada_tambem_em_excecao(tmp_path):
    """Caminho de exceção também descarta a worktree efêmera do Ticket 2."""
    rb = carregar_rollback()
    repo = _novo_repo_git(tmp_path)
    slug = "regressao-isolada"
    worktree = tmp_path / f"worktrees_diagnose-{slug}"
    _git(
        repo,
        "worktree",
        "add",
        "-b",
        f"diagnose/{slug}-def456",
        str(worktree),
        "HEAD",
    )

    class CrashFase4(RuntimeError):
        pass

    with pytest.raises(CrashFase4):
        with rb.RollbackDiagnose(repo_root=repo, slug=slug):
            raise CrashFase4("crash durante a instrumentação")

    assert not worktree.exists()
    branches = _git(repo, "branch", "--list").stdout
    assert f"diagnose/{slug}-def456" not in branches
