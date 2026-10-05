import pytest
from pathlib import Path
import json
import tempfile
import importlib.util

def _carregar_modulo(nome, rel_path):
    p = Path(__file__).resolve().parent.parent / rel_path
    spec = importlib.util.spec_from_file_location(nome, str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

observabilidade = _carregar_modulo("aidd_planner_observabilidade", "componentes/compartilhado/skills/aidd-planner/scripts/observabilidade.py")


def test_rastreador_planner_coleta_metricas():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        arquivo_planner = dest / "PLANNER.json"
        dados = {
            "projeto": "Teste",
            "bounded_contexts": [{"nome": "Auth"}, {"nome": "Billing"}],
            "entidades": [{"nome": "Usuario"}, {"nome": "Fatura"}],
            "rotas": ["/auth/login", "/billing/checkout"],
        }
        arquivo_planner.write_text(json.dumps(dados), encoding="utf-8")

        rastreador = observabilidade.RastreadorPlanner(arquivo_planner)
        metricas = rastreador.coletar_metricas()

        assert metricas["total_bounded_contexts"] == 2
        assert metricas["total_entidades"] == 2
        assert metricas["total_rotas"] == 2
        assert metricas["tokens_estimados"] > 0
