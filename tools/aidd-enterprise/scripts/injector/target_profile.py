# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — TARGET PROFILE (Adapter) do Universal Component Injector
=============================================================================
Mapeia cada `type` de componente para as rotas físicas reais deste repositório
(aidd-master-enterprise). Esta é a camada de "adapter": conhece a topologia
concreta de diretórios (harnesses, templates/, docs/), enquanto o núcleo
(`aidd_core_injector`) permanece agnóstico a ela.
"""

import os
import sys
import json
from typing import Any, Dict

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.dirname(_THIS_DIR)
_REPO_ROOT = os.path.dirname(_SCRIPTS_DIR)
_SRC_DIR = os.path.join(_REPO_ROOT, "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from core.result import Result

# Diretórios de fan-out multi-harness (skills e hooks são replicados byte-a-byte
# em todos eles). ".skills"/".hooks" seguem a convenção "flat" já usada pelo
# repositório para skills (sem aninhamento "skills/" adicional).
HARNESS_SKILL_DIRS = [
    ".claude/skills",
    ".agent/skills",
    ".mimocode/skills",
    ".gemini/skills",
    ".skills",
]

HARNESS_HOOK_DIRS = [
    ".claude/hooks",
    ".agent/hooks",
    ".mimocode/hooks",
    ".gemini/hooks",
    ".hooks",
]


def _to_bytes(texto: str) -> bytes:
    return texto.encode("utf-8")


def _caminho_seguro(rel: str) -> bool:
    """Rejeita caminhos absolutos ou que tentem escapar do diretório base."""
    if not rel or not rel.strip():
        return False
    if os.path.isabs(rel):
        return False
    partes = rel.replace("\\", "/").split("/")
    return ".." not in partes and "" not in partes


def build_file_map(component: Dict[str, Any], base_dir: str) -> Result:
    """Resolve um componente já validado para um mapa {caminho_relativo: bytes}.

    Caminhos são relativos a `base_dir` e usam sempre "/" como separador
    (normalizados para o separador do SO pelo chamador na hora de escrever).
    """
    tipo = component["type"]
    nome = component["name"]

    if tipo == "skill":
        conteudo = _to_bytes(component["content"])
        mapa = {f"{d}/{nome}/SKILL.md": conteudo for d in HARNESS_SKILL_DIRS}
        return Result.ok(mapa)

    if tipo == "hook":
        conteudo = _to_bytes(component["content"])
        mapa = {f"{d}/{nome}.json": conteudo for d in HARNESS_HOOK_DIRS}
        return Result.ok(mapa)

    if tipo == "agent":
        return Result.ok({f"templates/agents/{nome}.md": _to_bytes(component["content"])})

    if tipo == "rule":
        return Result.ok({f"templates/rules/{nome}.md": _to_bytes(component["content"])})

    if tipo == "spec":
        return Result.ok({f"docs/specs/{nome}.md": _to_bytes(component["content"])})

    if tipo == "mcp":
        mcp_path = os.path.join(base_dir, "mcp.json")
        dados = {"mcpServers": {}}
        if os.path.exists(mcp_path):
            try:
                with open(mcp_path, "r", encoding="utf-8") as f:
                    existente = json.load(f)
                if isinstance(existente, dict) and isinstance(existente.get("mcpServers"), dict):
                    dados = existente
            except Exception as e:
                return Result.fail(f"mcp.json existente é inválido: {e}", codigo="MCP_JSON_INVALIDO")

        entrada_mcp = component["mcp"]
        dados["mcpServers"][nome] = {
            "command": entrada_mcp["command"],
            "args": entrada_mcp.get("args", []),
            "env": entrada_mcp.get("env", {}),
        }
        conteudo = json.dumps(dados, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
        return Result.ok({"mcp.json": conteudo})

    if tipo == "config":
        arquivos = component["files"]
        mapa: Dict[str, bytes] = {}
        for rel, conteudo_texto in arquivos.items():
            rel_norm = rel.replace("\\", "/").lstrip("/")
            if not _caminho_seguro(rel_norm):
                return Result.fail(
                    f"Caminho de arquivo inválido/inseguro em 'files': '{rel}'.",
                    codigo="PATH_TRAVERSAL_REJEITADO",
                )
            mapa[rel_norm] = _to_bytes(conteudo_texto)
        return Result.ok(mapa)

    return Result.fail(f"Nenhuma rota de Target Profile definida para type '{tipo}'.", codigo="TYPE_SEM_ROTA")
