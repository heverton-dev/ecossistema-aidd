# -*- coding: utf-8 -*-
"""
Ticket 5 do ciclo agilidade-gates: arquivos derivados refeitos num comando só.

Regressões que estes testes seguram:
  - 29/09/2026: handoff-melhoria.json assinado com o hash do AGENTS.md em CRLF
    (Windows) reprovou o gate_final, que faz checkout em LF.
  - 30/09/2026: 'detect_secrets scan --baseline .secrets.baseline <arquivo>'
    trocou o baseline inteiro (87 arquivos) por um de 1 arquivo.
"""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import regenerar_derivados as rd  # noqa: E402

AGENTS_LF = b"# AGENTS\nregra 1\nregra 2\n"


def _raiz_com_handoff(tmp_path: Path) -> Path:
    scripts = tmp_path / ".agents" / "skills" / "aidd-improvement" / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(ROOT / ".agents" / "skills" / "aidd-improvement" / "scripts" / "handoff.py", scripts / "handoff.py")
    specs = tmp_path / "componentes" / "compartilhado" / "specs"
    specs.mkdir(parents=True)
    shutil.copy2(ROOT / "componentes" / "compartilhado" / "specs" / "handoff-melhoria.schema.json", specs)
    (tmp_path / "AGENTS.md").write_bytes(AGENTS_LF)
    dados = json.loads((ROOT / rd.HANDOFF).read_text(encoding="utf-8"))
    dados["artefatos"] = [{"caminho": "AGENTS.md", "sha256": "0" * 64}]
    (tmp_path / rd.HANDOFF).write_text(json.dumps(dados, indent=2), encoding="utf-8")
    return tmp_path


def test_handoff_assina_hash_em_lf_mesmo_com_arquivo_crlf(tmp_path, monkeypatch):
    monkeypatch.delenv("AIDD_HANDOFF_CHAVE", raising=False)
    raiz = _raiz_com_handoff(tmp_path)

    rd.regenerar_handoff(raiz)
    assinado_lf = (raiz / rd.HANDOFF).read_bytes()
    dados = json.loads(assinado_lf)
    assert dados["artefatos"][0]["sha256"] == hashlib.sha256(AGENTS_LF).hexdigest()
    assert b"\r\n" not in assinado_lf

    (raiz / "AGENTS.md").write_bytes(AGENTS_LF.replace(b"\n", b"\r\n"))  # checkout CRLF no Windows
    rd.regenerar_handoff(raiz)
    assert (raiz / rd.HANDOFF).read_bytes() == assinado_lf  # mesmo hash e mesma assinatura


def test_handoff_assinatura_confere_com_o_verificador_do_aidd_melhoria(tmp_path, monkeypatch):
    monkeypatch.delenv("AIDD_HANDOFF_CHAVE", raising=False)
    raiz = _raiz_com_handoff(tmp_path)
    rd.regenerar_handoff(raiz)

    sys.path.insert(0, str(raiz / ".agents" / "skills" / "aidd-improvement" / "scripts"))
    try:
        import handoff as modulo
        assert modulo.verificar_handoff(raiz / rd.HANDOFF, raiz) == []
    finally:
        sys.path.pop(0)


def _raiz_com_baseline(tmp_path: Path, entradas_extras: dict) -> Path:
    base = json.loads((ROOT / rd.BASELINE).read_text(encoding="utf-8"))
    base["results"] = entradas_extras
    (tmp_path / rd.BASELINE).write_text(json.dumps(base, indent=2), encoding="utf-8")
    # Mesmo formato do handoff real: 2 hashes hex de 64 caracteres que o detect-secrets acusa.
    (tmp_path / rd.HANDOFF).write_text(json.dumps({
        "artefatos": [{"caminho": "AGENTS.md", "sha256": hashlib.sha256(b"a").hexdigest()}],
        "assinatura": {"algoritmo": "sha256", "valor": hashlib.sha256(b"b").hexdigest()},
    }, indent=2) + "\n", encoding="utf-8")
    return tmp_path


def test_baseline_troca_so_as_entradas_do_derivado_e_preserva_o_resto(tmp_path):
    outro = {"outro\\arquivo.py": [{"type": "Secret Keyword", "filename": "outro\\arquivo.py",
                                    "hashed_secret": "f" * 40, "is_verified": False, "line_number": 3}]}
    raiz = _raiz_com_baseline(tmp_path, outro)

    rd.regenerar_baseline(raiz, [rd.HANDOFF])
    resultados = json.loads((raiz / rd.BASELINE).read_text(encoding="utf-8"))["results"]

    assert resultados["outro\\arquivo.py"] == outro["outro\\arquivo.py"]  # nada fora do derivado some
    assert len(resultados[rd.HANDOFF]) == 2
    assert all(s["filename"] == rd.HANDOFF for s in resultados[rd.HANDOFF])


def test_baseline_mantem_auditoria_e_e_idempotente(tmp_path):
    raiz = _raiz_com_baseline(tmp_path, {})
    rd.regenerar_baseline(raiz, [rd.HANDOFF])
    base = json.loads((raiz / rd.BASELINE).read_text(encoding="utf-8"))
    for segredo in base["results"][rd.HANDOFF]:
        segredo["is_secret"] = False  # auditado como falso positivo
    (raiz / rd.BASELINE).write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")

    rd.regenerar_baseline(raiz, [rd.HANDOFF])
    primeira = (raiz / rd.BASELINE).read_bytes()
    rd.regenerar_baseline(raiz, [rd.HANDOFF])

    assert (raiz / rd.BASELINE).read_bytes() == primeira
    assert all(s["is_secret"] is False for s in json.loads(primeira)["results"][rd.HANDOFF])
    assert b"\r\n" not in primeira


def test_achados_ciclo_grava_em_lf(tmp_path):
    saida = tmp_path / "ACHADOS.json"
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "achados_ciclo.py"), "--saida", str(saida)],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert b"\r\n" not in saida.read_bytes()


@pytest.mark.parametrize("args, esperado", [(["listar"], 0), (["regenerar", "--so", "nao/existe.json"], 1)])
def test_cli_derivados(args, esperado):
    proc = subprocess.run([sys.executable, str(ROOT / "ecossistema.py"), "derivados", *args],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert proc.returncode == esperado, proc.stdout + proc.stderr
    if esperado == 0:
        assert list(rd.DERIVADOS)[-1] in proc.stdout  # baseline por último
