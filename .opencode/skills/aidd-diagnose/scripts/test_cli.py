# -*- coding: utf-8 -*-
"""
Testes para aidd-diagnose CLI.
REGRA: Teste falhando primeiro (TDD).
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import pytest


def repo_root():
    """Encontra a raiz do repositório."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "ecossistema.py").is_file():
            return parent
    raise RuntimeError("Repositório não encontrado (ecossistema.py ausente)")


ROOT = repo_root()


class TestDiagnoseIniciar:
    """Testes do subcomando 'iniciar --sintoma'."""

    def test_iniciar_com_sintoma_cria_sessao_json(self, tmp_path):
        """Verifica se 'diagnose iniciar --sintoma "x"' cria docs/diagnosticos/<date>_<slug>/sessao.json."""
        # Monta o comando
        cmd = [
            sys.executable, str(ROOT / "ecossistema.py"), "diagnose",
            "iniciar", "--sintoma", "Teste de diagnose"
        ]

        # Executa
        result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)

        # Assertions
        assert result.returncode == 0, f"Comando falhou: {result.stderr}"

        # Verifica se sessao.json foi criado
        diagnosticos_dir = ROOT / "docs" / "diagnosticos"
        assert diagnosticos_dir.exists(), f"Diretório {diagnosticos_dir} não existe"

        # Deve haver um subdiretório com data e slug
        subdirs = list(diagnosticos_dir.glob("*_*"))
        assert len(subdirs) > 0, "Nenhum subdiretório com padrão <date>_<slug> criado"

        sessao_file = subdirs[0] / "sessao.json"
        assert sessao_file.exists(), f"Arquivo {sessao_file} não foi criado"

        # Valida conteúdo do JSON
        with open(sessao_file) as f:
            data = json.load(f)
        assert data["sintoma"] == "Teste de diagnose"
        assert data["fase_atual"] == 1

    def test_iniciar_sem_sintoma_falha(self):
        """Verifica se 'diagnose iniciar' sem --sintoma retorna exit 1."""
        cmd = [
            sys.executable, str(ROOT / "ecossistema.py"), "diagnose",
            "iniciar"
        ]
        result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        assert result.returncode != 0, "Comando deveria ter falhado"


class TestDiagnoseFase:
    """Testes do subcomando 'fase --numero'."""

    def test_fase_rejeita_sem_sessao_anterior(self):
        """Verifica se 'diagnose fase --numero 2' sem ter feito fase 1 retorna exit 1."""
        # Limpa diagnosticos anteriores
        diagnosticos_dir = ROOT / "docs" / "diagnosticos"
        if diagnosticos_dir.exists():
            import shutil
            shutil.rmtree(diagnosticos_dir)

        # Tenta pular fase
        cmd = [
            sys.executable, str(ROOT / "ecossistema.py"), "diagnose",
            "fase", "--numero", "2"
        ]
        result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        assert result.returncode != 0, "Comando deveria ter falhado ao pular fase"

    def test_fase_aceita_progressao_sequencial(self, tmp_path):
        """Verifica se pode progressar de fase 1 -> 2 -> 3 sequencialmente."""
        # Inicializa com sintoma
        cmd_init = [
            sys.executable, str(ROOT / "ecossistema.py"), "diagnose",
            "iniciar", "--sintoma", "Test sequence"
        ]
        result = subprocess.run(cmd_init, cwd=str(ROOT), capture_output=True, text=True)
        assert result.returncode == 0

        # Tenta avançar para fase 2
        cmd_fase2 = [
            sys.executable, str(ROOT / "ecossistema.py"), "diagnose",
            "fase", "--numero", "2"
        ]
        result = subprocess.run(cmd_fase2, cwd=str(ROOT), capture_output=True, text=True)
        assert result.returncode == 0, f"Falha ao avançar para fase 2: {result.stderr}"

        # Tenta avançar para fase 3
        cmd_fase3 = [
            sys.executable, str(ROOT / "ecossistema.py"), "diagnose",
            "fase", "--numero", "3"
        ]
        result = subprocess.run(cmd_fase3, cwd=str(ROOT), capture_output=True, text=True)
        assert result.returncode == 0, f"Falha ao avançar para fase 3: {result.stderr}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
