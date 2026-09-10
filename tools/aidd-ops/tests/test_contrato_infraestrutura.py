# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops — Contrato PLANO-INFRAESTRUTURA.json (Item 5) — Testes de Contrato
=============================================================================
Prova de interoperabilidade determinística entre:

  PRODUTOR    aidd-ops (pipeline_ops.py / contrato_plano.py)
  CONTRATO    componentes/compartilhado/specs/plano-infraestrutura.schema.json
  CONSUMIDOR  aidd-master e aidd-enterprise (scripts/scaffold_infra.py)

Cobertura:
  1. O schema canônico é Draft 2020-12 válido e possui $id/versão versionada.
  2. Plano real do produtor (pipeline rodada de verdade) adere 100% ao contrato.
  3. Plano com falha estruturada de fase (texto ambíguo) TAMBÉM adere (early-exit
     legítimo documentado pelo contrato) e o produtor recusa gravação inconsistente.
  4. CLI standalone contrato_plano.py: aceita (exit 0) / rejeita (exit 1).
  5. Consumidores master e enterprise: aceitam plano válido (exit 0) e bloqueiam
     plano fora do contrato (exit 1, PLANO_INVALIDO_CONTRATO) antes de gerar infra.

Sem stubs: subprocess reais; nenhuma decisão via LLM (Regra de Ouro #1/#5).
"""

import json
import os
import subprocess
import sys

import pytest

from jsonschema import Draft202012Validator

TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(TOOL_ROOT, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from contrato_plano import (  # noqa: E402
    SCHEMA_CONTRATO_PATH,
    caminho_schema_contrato,
    validar_plano_contrato,
)

PIPELINE_SCRIPT = os.path.join(SCRIPTS_DIR, "pipeline_ops.py")
CONTRATO_CLI_SCRIPT = os.path.join(SCRIPTS_DIR, "contrato_plano.py")

CONSUMIDORES = {
    "aidd-master": os.path.abspath(
        os.path.join(TOOL_ROOT, "..", "aidd-master", "scripts", "scaffold_infra.py")
    ),
    "aidd-enterprise": os.path.abspath(
        os.path.join(TOOL_ROOT, "..", "aidd-enterprise", "scripts", "scaffold_infra.py")
    ),
}

# Consumidores imprimem emoji → stdout pipe no Windows é cp1252 e quebraria
# (UnicodeEncodeError) sem forçar UTF-8. Comportamento pré-existente do script,
# não do contrato.
_ENV_UTF8 = os.environ.copy()
_ENV_UTF8["PYTHONIOENCODING"] = "utf-8"


def _executar_consumidor(nome: str, plano_path: str, pasta: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, CONSUMIDORES[nome], pasta, "AIDD Suite"]
    if plano_path:
        cmd.extend(["--plano", plano_path])
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        env=_ENV_UTF8,
        cwd=os.path.dirname(CONSUMIDORES[nome]),
    )


def _run_pipeline(texto: str, pasta: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, PIPELINE_SCRIPT, texto, "--pasta", pasta],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        cwd=TOOL_ROOT,
    )


def _carregar_plano(pasta: str) -> dict:
    caminho = os.path.join(pasta, "PLANO-INFRAESTRUTURA.json")
    assert os.path.isfile(caminho), f"PLANO-INFRAESTRUTURA.json nao gerado em {pasta}"
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def _plano_corrompido(pasta: str) -> dict:
    plano = _carregar_plano(pasta)
    plano["versao"] = "999.0.0"
    plano["fase_3_sizing"] = {"saida": {"vps": {"vcpu": "nove"}}}
    return plano


# ── 1. Schema canônico é Draft 2020-12 válido e versionado ──
class TestSchemaCanonico:
    def test_schema_e_valido_draft_2020_12(self):
        with open(SCHEMA_CONTRATO_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def test_schema_versionado_e_localizavel(self):
        assert os.path.isfile(caminho_schema_contrato())
        with open(SCHEMA_CONTRATO_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)
        assert "PLANO-INFRAESTRUTURA" in schema.get("title", "")
        assert schema.get("$id", "").endswith("plano-infraestrutura.schema.json")
        assert "$defs" in schema and "fase_base" in schema["$defs"]

    def test_fases_ordenadas_por_dependent_required(self):
        with open(SCHEMA_CONTRATO_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)
        # fase N só pode existir se todas as anteriores existirem (early-exit legítimo)
        dep = schema["dependentRequired"]
        assert dep["fase_2_curadoria"] == ["fase_1_intake"]
        assert dep["fase_3_sizing"] == ["fase_1_intake", "fase_2_curadoria"]


# ── 2. Plano real do produtor adere ao contrato ──
class TestProdutor:
    def test_plano_real_adere_ao_contrato(self, tmp_path):
        pasta = str(tmp_path / "plano_ok")
        resultado = _run_pipeline("Clinica odontologica com agendamento por WhatsApp", pasta)
        assert resultado.returncode == 0, resultado.stderr or resultado.stdout
        plano = _carregar_plano(pasta)
        res = validar_plano_contrato(plano)
        assert res.sucesso, f"{res.erro} {res.detalhes}"
        assert plano["versao"] == "1.0.0"
        assert sorted(plano.keys()) == [
            "fase_1_intake",
            "fase_2_curadoria",
            "fase_3_sizing",
            "gerado_em",
            "pipeline",
            "versao",
        ]
        assert plano["fase_3_sizing"]["saida"]["vps"]["vcpu"] > 0

    def test_plano_com_erro_estruturado_de_fase_adere(self, tmp_path):
        # Texto ambíguo → pipeline falha na fase 1, mas o plano parcial gravado
        # DEVE continuar 100% aderente ao contrato (early-exit legítimo).
        pasta = str(tmp_path / "plano_ambig")
        resultado = _run_pipeline("clinica de delivery de farmacia", pasta)
        assert resultado.returncode == 1
        plano = _carregar_plano(pasta)
        res = validar_plano_contrato(plano)
        assert res.sucesso, f"{res.erro} {res.detalhes}"
        assert set(plano.keys()) == {"fase_1_intake", "gerado_em", "pipeline", "versao"}
        erro = plano["fase_1_intake"]["erro"]
        assert erro["sucesso"] is False
        assert erro["codigo"] == "NICHO_AMBIGUO"

    def test_produtor_rejeita_plano_fora_do_contrato(self, tmp_path):
        # O pipeline só escreve o que ele mesmo produz de forma correta; a prova
        # de que o gate do produtor REPROVA vem da CLI standalone (abaixo).
        pasta = str(tmp_path / "plano_ruim")
        _run_pipeline("Clinica odontologica", pasta)
        caminho_ruim = os.path.join(pasta, "PLANO-RUIM.json")
        with open(caminho_ruim, "w", encoding="utf-8") as f:
            json.dump(_plano_corrompido(pasta), f)
        res_cli = subprocess.run(
            [sys.executable, CONTRATO_CLI_SCRIPT, caminho_ruim],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=TOOL_ROOT,
        )
        assert res_cli.returncode == 1
        assert "PLANO_INVALIDO_CONTRATO" in (res_cli.stdout + res_cli.stderr)


# ── 3. CLI standalone contrato_plano.py ──
class TestCliContratoPlano:
    def test_cli_aceita_plano_valido(self, tmp_path):
        pasta = str(tmp_path / "cli_ok")
        _run_pipeline("Clinica odontologica", pasta)
        caminho = os.path.join(pasta, "PLANO-INFRAESTRUTURA.json")
        res = subprocess.run(
            [sys.executable, CONTRATO_CLI_SCRIPT, caminho],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=TOOL_ROOT,
        )
        assert res.returncode == 0, res.stderr or res.stdout
        assert "[OK]" in res.stdout

    def test_cli_rejeita_arquivo_inexistente(self):
        res = subprocess.run(
            [sys.executable, CONTRATO_CLI_SCRIPT, "/nao/existe/PLANO.json"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=TOOL_ROOT,
        )
        assert res.returncode == 1
        assert "PLANO_INVALIDO_CONTRATO" not in res.stdout


# ── 4. Consumidores master e enterprise ──
class TestConsumidores:
    @pytest.mark.parametrize("nome", sorted(CONSUMIDORES.keys()))
    def test_consumidor_aceita_plano_valido(self, nome, tmp_path):
        pasta_plano = str(tmp_path / f"{nome}_plano")
        _run_pipeline("Clinica odontologica com agendamento", pasta_plano)
        plano_path = os.path.join(pasta_plano, "PLANO-INFRAESTRUTURA.json")

        pasta_gerada = str(tmp_path / f"{nome}_saida")
        res = _executar_consumidor(nome, plano_path, pasta_gerada)

        assert res.returncode == 0, res.stdout + res.stderr
        assert "[CONTRATO] Plano validado" in res.stdout
        infra = os.path.join(pasta_gerada, "infra")
        assert os.path.isdir(infra)
        assert len([f for f in os.listdir(infra)]) > 0

    @pytest.mark.parametrize("nome", sorted(CONSUMIDORES.keys()))
    def test_consumidor_bloqueia_plano_fora_do_contrato(self, nome, tmp_path):
        pasta_plano = str(tmp_path / f"{nome}_plano_ruim")
        _run_pipeline("Clinica odontologica", pasta_plano)
        caminho_ruim = os.path.join(pasta_plano, "PLANO-RUIM.json")
        with open(caminho_ruim, "w", encoding="utf-8") as f:
            json.dump(_plano_corrompido(pasta_plano), f)

        pasta_gerada = str(tmp_path / f"{nome}_saida_ruim")
        res = _executar_consumidor(nome, caminho_ruim, pasta_gerada)

        assert res.returncode == 1
        assert "[ERRO] PLANO_INVALIDO_CONTRATO" in (res.stdout + res.stderr)
        assert not os.path.isdir(os.path.join(pasta_gerada, "infra"))

    @pytest.mark.parametrize("nome", sorted(CONSUMIDORES.keys()))
    def test_consumidor_rejeita_plano_ausente(self, nome, tmp_path):
        pasta_gerada = str(tmp_path / f"{nome}_sem_plano")
        res = _executar_consumidor(nome, "/nao/existe/PLANO.json", pasta_gerada)
        assert res.returncode == 1
        assert "PLANO_NAO_ENCONTRADO" in (res.stdout + res.stderr)
        assert not os.path.isdir(os.path.join(pasta_gerada, "infra"))