# -*- coding: utf-8 -*-
"""
Testes para o módulo observabilidade.py do aidd-diagnose.
REGRA: Teste falhando primeiro (TDD).
"""

import json
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
SCRIPT_OBS = ROOT / ".agents" / "skills" / "aidd-diagnose" / "scripts" / "observabilidade.py"


def _carregar_obs():
    """Carrega o observabilidade.py do diagnose com nome único (não colide com o do aidd-melhoria)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("aidd_diagnose_observabilidade_teste", str(SCRIPT_OBS))
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo  # @dataclass exige o módulo registrado
    spec.loader.exec_module(modulo)
    return modulo


OBS = _carregar_obs()


class TestObservabilidadeDiagnose:
    """Testes para o módulo observabilidade.py do aidd-diagnose."""

    def test_modulo_observabilidade_existe(self):
        """Verifica se observabilidade.py existe."""
        assert SCRIPT_OBS.exists(), f"Arquivo {SCRIPT_OBS} não encontrado"

    def test_rastreador_execucao_com_contexto(self):
        """Verifica se RastreadorExecucao funciona como context manager."""
        RastreadorExecucao = OBS.RastreadorExecucao

        with RastreadorExecucao(etapa="teste_contexto") as rastreador:
            rastreador.registrar_entrada("entrada de teste")
            rastreador.registrar_saida("saída de teste")

        metricas = rastreador.metricas
        assert metricas is not None
        assert metricas.etapa == "teste_contexto"
        assert metricas.tokens_entrada > 0
        assert metricas.tokens_saida > 0
        assert metricas.status == "SUCESSO"

    def test_registrador_fase_com_completo(self, tmp_path):
        """Verifica se RegistradorFase registra completo."""
        RegistradorFase = OBS.RegistradorFase

        diretorio_log = tmp_path / "diagnosticos"
        diretorio_log.mkdir()

        with RegistradorFase(numero=1, diretorio_sessao=str(diretorio_log)) as reg_fase:
            reg_fase.registrar_inicio()
            reg_fase.registrar_comando_reproducao("comando teste")
            reg_fase.registrar_hipotese("hipótese 1")
            reg_fase.registrar_descartada("hipótese 2", "não se aplica")
            reg_fase.registrar_fim()

        # Verifica se arquivo de log foi criado
        logs = list(diretorio_log.glob("fase_*.log"))
        assert len(logs) > 0, "Nenhum log de fase foi criado"

        conteudo = logs[0].read_text(encoding="utf-8")
        assert "FASE 1" in conteudo
        assert "hip" in conteudo and "tese 1" in conteudo
        assert "hip" in conteudo and "tese 2" in conteudo

    def test_relatorio_causa_raiz_gerado(self, tmp_path):
        """Verifica se relatório de causa raiz é gerado ao final."""
        RegistradorFase = OBS.RegistradorFase
        gerar_relatorio_causa_raiz = OBS.gerar_relatorio_causa_raiz

        diretorio_sessao = tmp_path / "diagnosticos" / "20260924_teste"
        diretorio_sessao.mkdir(parents=True)

        # Simula execução de 5 fases
        fases_data = {}
        for num_fase in range(1, 6):
            with RegistradorFase(numero=num_fase, diretorio_sessao=str(diretorio_sessao)) as reg_fase:
                reg_fase.registrar_inicio()
                reg_fase.registrar_comando_reproducao(f"comando fase {num_fase}")
                if num_fase <= 3:
                    reg_fase.registrar_hipotese(f"hipótese {num_fase}")
                reg_fase.registrar_fim()
                fases_data[f"fase_{num_fase}"] = reg_fase.dados

        # Gera relatório
        relatorio_path = gerar_relatorio_causa_raiz(
            diretorio_sessao=str(diretorio_sessao),
            slug="teste"
        )

        assert relatorio_path.exists(), f"Relatório {relatorio_path} não foi criado"

        conteudo = relatorio_path.read_text(encoding="utf-8")
        assert "RELATORIO-CAUSA-RAIZ" in conteudo
        assert "Fase 1" in conteudo or "Fase 2" in conteudo
        assert "Conclus" in conteudo  # Conclusões (com ç)

    def test_observabilidade_com_relatorio_retorna_0(self, tmp_path):
        """Verifica que com relatório gerado retorna exit 0."""
        RegistradorFase = OBS.RegistradorFase
        gerar_relatorio_causa_raiz = OBS.gerar_relatorio_causa_raiz

        diretorio_sessao = tmp_path / "diagnosticos" / "20260924_teste_sucesso"
        diretorio_sessao.mkdir(parents=True)

        try:
            # Simula todas as fases
            for num_fase in range(1, 6):
                with RegistradorFase(numero=num_fase, diretorio_sessao=str(diretorio_sessao)) as reg_fase:
                    reg_fase.registrar_inicio()
                    reg_fase.registrar_comando_reproducao(f"cmd {num_fase}")
                    reg_fase.registrar_fim()

            # Gera relatório
            relatorio_path = gerar_relatorio_causa_raiz(
                diretorio_sessao=str(diretorio_sessao),
                slug="teste_sucesso"
            )

            assert relatorio_path.exists()
            # Se chegou aqui, sucesso
            assert True
        except Exception as e:
            pytest.fail(f"Exceção não esperada: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
