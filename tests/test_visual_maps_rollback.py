# -*- coding: utf-8 -*-
"""
aidd-visual-maps ciclo-01, Ticket 9 (D14): gravação atômica do par técnico/não técnico.

Achado N3 do laudo: sem o molde não técnico de guardas, `mapa_visual.py guardas` saía
com FileNotFoundError cru e o mapa técnico já tinha sido regravado (escrita parcial).
Agora as duas versões são montadas em memória antes de qualquer gravação; erro de molde
vira linha [ERRO] com exit 1, o técnico fica byte a byte igual e não sobra temporário.
"""
import hashlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_mapas import copiar_repo, rodar  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def _ga():
    import gravacao_atomica_mapas
    return gravacao_atomica_mapas


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _temporarios(pasta: Path) -> list[str]:
    return sorted(str(p) for p in pasta.rglob("*.tmp"))


def test_molde_nao_tecnico_ausente_nao_regrava_o_tecnico(tmp_path):
    repo = copiar_repo(tmp_path / "repo")
    tecnico = repo / "docs" / "mapas-visuais" / "mapa-04-guardas.html"
    tecnico.write_text("versão anterior do mapa técnico\n", encoding="utf-8", newline="\n")
    antes = _sha(tecnico)
    (repo / "docs" / "mapas-visuais" / "moldes-nao-tecnicos" / "guardas.html").unlink()

    proc = rodar(repo, "scripts/mapa_visual.py", "guardas")

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "[ERRO]" in proc.stdout
    assert "Traceback" not in proc.stdout + proc.stderr
    assert _sha(tecnico) == antes
    assert _temporarios(repo / "docs") == []


def test_gravar_lote_troca_todos_ou_nenhum(tmp_path, monkeypatch):
    ga = _ga()
    a, b = tmp_path / "a.html", tmp_path / "sub" / "b.html"
    a.write_text("A velho", encoding="utf-8")
    original = os.replace

    def replace_que_falha_em_b(origem, destino):
        if Path(destino) == b:
            raise PermissionError(13, "arquivo preso", str(destino))
        return original(origem, destino)

    monkeypatch.setattr(ga.os, "replace", replace_que_falha_em_b)
    with pytest.raises(OSError):
        ga.gravar_lote({a: "A novo", b: "B novo"})
    assert a.read_text(encoding="utf-8") == "A velho"  # restaurado da cópia em memória
    assert not b.exists()  # não existia antes: some no rollback
    assert _temporarios(tmp_path) == []


def test_gravar_lote_grava_em_lf_e_devolve_os_destinos(tmp_path):
    destinos = _ga().gravar_lote({tmp_path / "x.html": "linha 1\nlinha 2\n"})
    assert destinos == [tmp_path / "x.html"]
    assert (tmp_path / "x.html").read_bytes() == b"linha 1\nlinha 2\n"
