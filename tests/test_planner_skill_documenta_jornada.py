# -*- coding: utf-8 -*-
"""ETAPA_09 (Ticket 6 da ETAPA_05): a skill e o comando do planner documentam a jornada real.

Ambiente (Mobbin 1 MCP, 2 chave, 3 nenhum + variáveis de deploy) -> grill -> spec -> `planner entrevista`
-> `planner init`. Sem isso o harness chega ao `init` e é bloqueado sem saber por quê.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SKILL = RAIZ / "componentes" / "compartilhado" / "skills" / "aidd-planner" / "SKILL.md"
COMANDO = RAIZ / "componentes" / "compartilhado" / "comandos" / "planner.md"
ENV_EXEMPLO = RAIZ / ".env.example"


def _t(p):
    return p.read_text(encoding="utf-8")


def test_skill_documenta_ambiente_com_a_ordem_dos_caminhos():
    t = _t(SKILL)
    assert "planner ambiente" in t and "--mobbin" in t
    assert t.index("MCP") < t.index("MOBBIN_API_KEY")
    for var in ("VPS_HOST", "CLOUDFLARE_ZONE_ID", "DEFAULT_ROOT_DOMAIN"):
        assert var in t


def test_skill_documenta_entrevista_spec_e_visual_direction():
    t = _t(SKILL)
    for trecho in ("planner entrevista", ".aidd/intake/grill.md", ".aidd/intake/spec.md", "Visual Direction",
                   "referencias-ui.json", "referencias-mcp.json", "autonomo"):
        assert trecho in t, trecho


def test_comando_planner_cita_ambiente_e_entrevista():
    t = _t(COMANDO)
    assert "planner ambiente" in t and "planner entrevista" in t


def test_env_example_diz_que_as_variaveis_de_deploy_bloqueiam_o_planner():
    t = _t(ENV_EXEMPLO)
    assert "bloqueia o planner" in t.lower() or "bloqueiam o planner" in t.lower()
