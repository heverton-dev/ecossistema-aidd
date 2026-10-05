import pytest
from pathlib import Path
import tempfile
import importlib.util

def _carregar_modulo(nome, rel_path):
    p = Path(__file__).resolve().parent.parent / rel_path
    spec = importlib.util.spec_from_file_location(nome, str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

observabilidade = _carregar_modulo("aidd_plan_observabilidade", "componentes/compartilhado/skills/aidd-plan/scripts/observabilidade.py")


def test_rastreador_plano_calcula_metricas():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        pasta = dest / "PLAN-0001-teste"
        pasta.mkdir()
        (pasta / "00-PROCESSO-E-DECISOES.md").write_text("# Processo\nTexto linha 2\n", encoding="utf-8")
        (pasta / "01-item.md").write_text("# Item 1\n> **Status:** [DRAFT]\n", encoding="utf-8")
        (pasta / "02-item.md").write_text("# Item 2\n> **Status:** [DRAFT]\n", encoding="utf-8")

        rastreador = observabilidade.RastreadorPlano(pasta)
        metricas = rastreador.coletar_metricas()

        assert metricas["total_itens"] == 2
        assert metricas["total_arquivos"] == 3
        assert metricas["total_linhas"] > 0
        assert metricas["tokens_estimados"] > 0
