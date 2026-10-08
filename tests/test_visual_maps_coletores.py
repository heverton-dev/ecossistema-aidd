# -*- coding: utf-8 -*-
"""
aidd-visual-maps ciclo-01, Ticket 4 (D4): coletores de MCPs e hooks completos.

Achados F5/N9 do laudo: o catálogo só via os MCPs dentro das ferramentas (faltava o
mobbin_mcp de componentes/compartilhado/mcps/) e só os hooks ligados no
.claude/settings.json (faltavam os scripts de .claude/hooks/ sem gatilho). O
.claude/settings.local.json não é versionado e nunca é lido.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import catalogo_pecas as cp  # noqa: E402
import mapa_visual as mv  # noqa: E402

LIGADOS = ("anti_headless_subagent_hook.py", "cbm_update.py", "cbm_session_start.py")
SOLTOS = ("regra10_check.py", "aidd_session_auto_hook.py")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / ".mcp.json").write_text(json.dumps({"mcpServers": {
        "context7": {"command": "npx", "args": ["-y", "@upstash/context7-mcp"]},
        "mobbin-mcp": {"command": "python", "args": ["componentes/compartilhado/mcps/mobbin_mcp/server.py"]},
        "mcp-gatekeeper": {"command": "python", "args": ["componentes/compartilhado/src-core/mcp_gatekeeper.py"]},
    }}), encoding="utf-8")
    for rel in ("componentes/compartilhado/mcps/mobbin_mcp/server.py", "componentes/compartilhado/src-core/mcp_gatekeeper.py"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("# servidor\n", encoding="utf-8")
    hooks = tmp_path / ".claude" / "hooks"
    hooks.mkdir(parents=True)
    for nome in LIGADOS + SOLTOS:
        (hooks / nome).write_text("# hook\n", encoding="utf-8")
    (hooks / "cbm-update.sh").write_text("# invólucro, não é hook python\n", encoding="utf-8")
    eventos = {"PreToolUse": LIGADOS[0], "PostToolUse": LIGADOS[1], "SessionStart": LIGADOS[2]}
    (tmp_path / ".claude" / "settings.json").write_text(json.dumps({"hooks": {
        evento: [{"matcher": "", "hooks": [{"type": "command", "command": f"python -u .claude/hooks/{script}"}]}]
        for evento, script in eventos.items()}}), encoding="utf-8")
    # Local, não versionado: se o coletor o lesse, o --check de frescor mudaria de máquina para máquina.
    (tmp_path / ".claude" / "settings.local.json").write_text(json.dumps({"hooks": {"Stop": [
        {"matcher": "", "hooks": [{"type": "command", "command": "python .claude/hooks/regra10_check.py"}]}]}}),
        encoding="utf-8")
    monkeypatch.setattr(cp, "RAIZ", tmp_path)
    monkeypatch.setattr(cp, "COMPARTILHADO", tmp_path / "componentes" / "compartilhado")
    return tmp_path


def _ferramentas():
    return [{"id": "aidd-ops", "mcps_proprios": ["modulos/03-x/aidd-ops/mcps/docker-mcp/server.py"]}]


def test_mcps_internos_incluem_componentes_e_mcp_json_sem_duplicar(repo):
    mcps = cp.coletar_mcps(_ferramentas())
    internos = {m["id"]: m for m in mcps["internos_das_ferramentas"]}
    assert set(internos) == {"docker-mcp", "mobbin_mcp", "mcp-gatekeeper"}
    assert internos["mobbin_mcp"]["caminho"] == "componentes/compartilhado/mcps/mobbin_mcp/server.py"
    assert internos["mobbin_mcp"]["registrado_em_config"] is True
    assert internos["mcp-gatekeeper"]["caminho"] == "componentes/compartilhado/src-core/mcp_gatekeeper.py"
    assert "context7" not in internos and "context7" in mcps["registrados_mcp_json"]


def test_hooks_listam_os_cinco_scripts_e_marcam_os_sem_gatilho(repo):
    hooks = {Path(h["script"]).name: h for h in cp.coletar_hooks()}
    assert set(hooks) == set(LIGADOS + SOLTOS)
    for nome in SOLTOS:
        assert hooks[nome]["status"] == "sem gatilho no settings.json"
    for nome in LIGADOS:
        assert hooks[nome]["status"] == "ligado no settings.json"
    assert "Stop" not in {h["evento"] for h in hooks.values()}  # settings.local.json não é lido


def test_mapa_de_conexoes_mostra_hook_sem_gatilho(repo):
    cat = {"mcps": cp.coletar_mcps(_ferramentas()), "hooks": cp.coletar_hooks()}
    valores = mv.valores_conexoes(cat)
    assert "mobbin_mcp" in valores["INTERNOS"] and "regra10_check.py" in valores["HOOKS"]
    assert "sem gatilho no settings.json" in valores["HOOKS"]


def test_catalogo_real_tem_mobbin_e_os_hooks_versionados():
    cat = json.loads((ROOT / "docs" / "auditoria" / "mapa-pecas" / "catalogo-pecas.json").read_text(encoding="utf-8"))
    assert "mobbin_mcp" in {m["id"] for m in cat["mcps"]["internos_das_ferramentas"]}
    reais = {p.name for p in (ROOT / ".claude" / "hooks").glob("*.py")}
    assert reais <= {Path(h["script"]).name for h in cat["hooks"]}
