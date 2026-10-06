# -*- coding: utf-8 -*-
"""
Testes do gate G_ESCRITOR_ATOMICO.
"""

import os
import sys
import subprocess

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE_PATH = os.path.join(ROOT_DIR, "gates", "G_ESCRITOR_ATOMICO.py")


class TestGEscritorAtomico:
    def test_gate_exit_0(self):
        """O gate deve passar com exit 0 quando todos os pontos críticos usam escritor_atomico."""
        resultado = subprocess.run(
            [sys.executable, GATE_PATH],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            timeout=30,
        )
        assert resultado.returncode == 0, (
            f"Gate falhou com exit {resultado.returncode}.\n"
            f"STDOUT:\n{resultado.stdout}\n"
            f"STDERR:\n{resultado.stderr}"
        )
        assert "SUCESSO" in resultado.stdout or "Total violações:      0" in resultado.stdout

    def test_gate_detecta_violacao(self, tmp_path, monkeypatch):
        """Lei #13: Prova que o gate morde (exit 1) se houver open('w') direto em arquivo crítico."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("g_escritor_atomico", GATE_PATH)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)

        # Simula arquivo crítico com violação direta dentro de tmp_path
        violacao_dir = tmp_path / "componentes" / "compartilhado" / "src-core"
        violacao_dir.mkdir(parents=True)
        violacao_file = violacao_dir / "materializador.py"
        violacao_file.write_text(
            'import json\n'
            'def _gravar_plano(caminho, plano):\n'
            '    with open(caminho, "w") as f:\n'
            '        json.dump(plano, f)\n',
            encoding="utf-8",
        )

        monkeypatch.setattr(modulo, "ROOT_DIR", str(tmp_path))
        monkeypatch.setattr(modulo, "ARQUIVOS_CRITICOS", ["componentes/compartilhado/src-core/materializador.py"])

        exit_code = modulo.executar()
        assert exit_code == 1

