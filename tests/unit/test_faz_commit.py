# -*- coding: utf-8 -*-
"""
Testes unitários para o script determinístico faz-commit.
"""

import sys
import os
import subprocess
from unittest.mock import patch, MagicMock

# Adiciona diretório scripts ao path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))

import faz_commit


def test_fallback_mensagem_vazia():
    msg = faz_commit.fallback_mensagem("")
    assert msg == "chore: atualizar alterações no repositório"


def test_fallback_mensagem_arquivo_unico():
    msg = faz_commit.fallback_mensagem("M docs/readme.md")
    assert "readme.md" in msg
    assert msg.startswith("chore:")


def test_fallback_mensagem_multiplos_arquivos():
    msg = faz_commit.fallback_mensagem("M file1.py\nA file2.py")
    assert "file1.py" in msg
    assert "mais 1 arquivo(s)" in msg


def test_obter_diff_resumido_nao_vazio():
    res = faz_commit.obter_diff_resumido()
    assert "STATUS DOS ARQUIVOS:" in res
    assert "ESTATÍSTICAS:" in res


# --- Diagnóstico cirúrgico de falhas ------------------------------------------

import io

SAIDA_PRE_COMMIT_FALHA = (
    "[pre-commit] Rodando quality gates (framework pre-commit)...\n"
    "\x1b[1mG_ECOSSISTEMA_INTEGRIDADE (ferramentas/skills/commands/AST)\x1b[0m"
    "..........\x1b[42mPassed\x1b[m\n"
    "- hook id: g-ecossistema-integridade\n"
    "docs/aviso.md:3: aviso qualquer de gate aprovado\n"
    "G_TESTES_REAIS (pytest real das ferramentas)........................\x1b[41mFailed\x1b[m\n"
    "- hook id: g-testes-reais\n"
    "- exit code: 1\n"
    "tests/unit/test_calc.py:14: AssertionError\n"
    "FAILED tests/unit/test_calc.py::test_soma - assert 3 == 4\n"
    "G_SEGREDOS (detect-secrets sobre git ls-files vs baseline)..........Failed\n"
    "- hook id: g-segredos\n"
    "- exit code: 1\n"
    "Traceback (most recent call last):\n"
    '  File "gates/G_SEGREDOS.py", line 88, in <module>\n'
    "    main()\n"
    '  File "C:\\Python314\\Lib\\json\\__init__.py", line 346, in loads\n'
    "    return _default_decoder.decode(s)\n"
    "json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)\n"
    "G_HADOLINT (melhores praticas OCI via Hadolint)......................Failed\n"
    "- hook id: g-hadolint\n"
    "- exit code: 1\n"
    "[pre-commit] ERRO: quality gates reprovaram. Corrija antes do commit.\n"
)


def test_diagnostico_aponta_gates_reprovados_com_comando():
    diag = faz_commit.diagnosticar("commit", SAIDA_PRE_COMMIT_FALHA)
    assert [g.nome for g in diag.gates] == ["G_TESTES_REAIS", "G_SEGREDOS", "G_HADOLINT"]
    assert diag.gates[0].comando == "python -m pre_commit run g-testes-reais"


def test_diagnostico_extrai_arquivo_linha_e_teste_pytest():
    gate = faz_commit.diagnosticar("commit", SAIDA_PRE_COMMIT_FALHA).gates[0]
    refs = [str(l) for l in gate.locais]
    assert "tests/unit/test_calc.py:14  AssertionError" in refs
    assert "tests/unit/test_calc.py::test_soma  assert 3 == 4" in refs


def test_diagnostico_traceback_pega_frame_do_projeto_nao_da_biblioteca():
    gate = faz_commit.diagnosticar("commit", SAIDA_PRE_COMMIT_FALHA).gates[1]
    assert len(gate.locais) == 1
    assert gate.locais[0].arquivo == "gates/G_SEGREDOS.py"
    assert gate.locais[0].linha == "88"
    assert "JSONDecodeError" in gate.locais[0].mensagem


def test_diagnostico_ignora_saida_de_gate_aprovado():
    diag = faz_commit.diagnosticar("commit", SAIDA_PRE_COMMIT_FALHA)
    todos = [l.arquivo for g in diag.gates for l in g.locais]
    assert "docs/aviso.md" not in todos


def test_diagnostico_gate_sem_local_nao_inventa():
    gate = faz_commit.diagnosticar("commit", SAIDA_PRE_COMMIT_FALHA).gates[2]
    assert gate.locais == []


def test_diagnostico_push_rejeitado_sugere_rebase():
    stderr = (
        " ! [rejected]        main -> main (fetch first)\n"
        "error: failed to push some refs to 'github.com:x/y.git'\n"
    )
    diag = faz_commit.diagnosticar("push", stderr, "main")
    assert "commits que você ainda não tem" in diag.causa
    assert diag.comando == "git pull --rebase origin main && git push origin main"


def test_diagnostico_sem_padrao_conhecido_usa_ultima_linha():
    diag = faz_commit.diagnosticar("git add", "fatal: Unable to create '.git/index.lock': File exists.\n")
    assert diag.causa.startswith("fatal: Unable to create")


def test_ler_shortstat():
    assert faz_commit.ler_shortstat(" 3 files changed, 10 insertions(+), 2 deletions(-)") == (3, 10, 2)
    assert faz_commit.ler_shortstat(" 1 file changed, 1 insertion(+)") == (1, 1, 0)


def test_estilo_sem_cor_nao_emite_ansi_nem_linhas_extras():
    out, err = io.StringIO(), io.StringIO()
    estilo = faz_commit.Estilo(cor=False, stream=out, stream_erro=err)
    diag = faz_commit.diagnosticar("commit", SAIDA_PRE_COMMIT_FALHA)
    faz_commit.imprimir_falha(diag, faz_commit.time.time(), estilo)
    texto = err.getvalue()
    assert "\x1b[" not in texto
    assert "FALHOU na etapa: commit" in texto
    assert "gates/G_SEGREDOS.py:88" in texto


def test_estilo_com_cor_emite_ansi():
    out = io.StringIO()
    faz_commit.Estilo(cor=True, stream=out).ok("feito")
    assert "\x1b[" in out.getvalue()


def test_estilo_no_color_desliga_cor(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.delenv("FAZ_COMMIT_COR", raising=False)
    assert faz_commit.Estilo(stream=io.StringIO()).cor is False


def test_estilo_ignora_force_color_de_harness_em_pipe(monkeypatch):
    monkeypatch.setenv("FORCE_COLOR", "3")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("FAZ_COMMIT_COR", raising=False)
    assert faz_commit.Estilo(stream=io.StringIO()).cor is False


def test_estilo_faz_commit_cor_forca(monkeypatch):
    monkeypatch.setenv("FAZ_COMMIT_COR", "1")
    assert faz_commit.Estilo(stream=io.StringIO()).cor is True


def test_diagnostico_arquivo_linha_no_fim_usa_motivo_da_linha_anterior():
    saida = (
        "G_ENV_ROT (prevencao de environment rot)........Failed\n"
        "- hook id: g-env-rot\n"
        "  [DINAMICO] scripts/outro.py:43 -> k\n"
        "  [CHAVE FALTANTE] FAZ_COMMIT_COR\n"
        "    -> Em scripts/faz_commit.py:282\n"
    )
    gate = faz_commit.diagnosticar("commit", saida).gates[0]
    assert [str(l) for l in gate.locais] == ["scripts/faz_commit.py:282  [CHAVE FALTANTE] FAZ_COMMIT_COR"]


def test_dry_run_preserva_stage_que_o_usuario_ja_tinha(tmp_path):
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, capture_output=True, text=True, check=True).stdout

    git("init", "-q")
    (tmp_path / "preparado.txt").write_text("ja estava no stage\n", encoding="utf-8")
    (tmp_path / "solto.txt").write_text("nao estava no stage\n", encoding="utf-8")
    git("add", "preparado.txt")

    res = subprocess.run(
        [sys.executable, os.path.join(ROOT_DIR, "scripts", "faz_commit.py"), "--dry-run", "-m", "chore: teste"],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8",
    )

    assert res.returncode == 0, res.stderr
    assert "stage restaurado" in res.stdout
    assert git("diff", "--cached", "--name-only").split() == ["preparado.txt"]
    assert "?? solto.txt" in git("status", "--short")
