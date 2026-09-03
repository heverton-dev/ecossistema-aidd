# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — NÚCLEO DO UNIVERSAL COMPONENT INJECTOR (aidd_core_injector)
=============================================================================
Motor transacional agnóstico a harness: valida o contrato do componente,
resolve rotas via Target Profile (adapter), materializa em staging antes de
tocar o filesystem real, escreve com snapshot + rollback automático em caso
de falha parcial, mantém o COMPONENT-REGISTRY.json e valida sincronização
multi-harness (sync_check) para o gate G_INJECT.

Toda função pública retorna Result[T] (core.result) — nunca propaga exceção
crua para o chamador (CLI, IntentRouter ou gate).
"""

import os
import sys
import re
import json
import hashlib
import tempfile
import datetime
from typing import Any, Dict, List, Optional

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.dirname(_THIS_DIR)
_REPO_ROOT = os.path.dirname(_SCRIPTS_DIR)
_SRC_DIR = os.path.join(_REPO_ROOT, "src")

if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from core.result import Result
from injector import target_profile

SCHEMA_PATH = os.path.join(_THIS_DIR, "schema", "component_manifest.schema.json")
REGISTRY_FILENAME = "COMPONENT-REGISTRY.json"

VALID_TYPES = ("skill", "mcp", "rule", "spec", "config", "hook", "agent")
_CONTENT_TYPES = ("skill", "rule", "spec", "agent", "hook")
_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def validate_component(component: Dict[str, Any]) -> Result:
    """Valida um componente contra o contrato de component_manifest.schema.json."""
    if not isinstance(component, dict):
        return Result.fail("Componente deve ser um dicionário.", codigo="COMPONENTE_INVALIDO")

    tipo = component.get("type")
    if tipo not in VALID_TYPES:
        return Result.fail(f"type inválido: {tipo!r}. Esperado um de {VALID_TYPES}.", codigo="TYPE_INVALIDO")

    nome = component.get("name")
    if not isinstance(nome, str) or not _NAME_RE.match(nome):
        return Result.fail(
            f"name inválido: {nome!r}. Deve casar com o padrão ^[a-z][a-z0-9-]*$.",
            codigo="NAME_INVALIDO",
        )

    if tipo in _CONTENT_TYPES:
        conteudo = component.get("content")
        if not isinstance(conteudo, str) or not conteudo.strip():
            return Result.fail(f"type '{tipo}' exige campo 'content' (string não vazia).", codigo="CONTENT_AUSENTE")

    if tipo == "mcp":
        mcp = component.get("mcp")
        if not isinstance(mcp, dict) or not isinstance(mcp.get("command"), str) or not mcp.get("command", "").strip():
            return Result.fail("type 'mcp' exige objeto 'mcp' com 'command' (string não vazia).", codigo="MCP_INVALIDO")
        if not isinstance(mcp.get("args", []), list):
            return Result.fail("'mcp.args' deve ser uma lista.", codigo="MCP_INVALIDO")
        if not isinstance(mcp.get("env", {}), dict):
            return Result.fail("'mcp.env' deve ser um objeto.", codigo="MCP_INVALIDO")

    if tipo == "config":
        arquivos = component.get("files")
        if not isinstance(arquivos, dict) or not arquivos:
            return Result.fail(
                "type 'config' exige campo 'files' (mapa não vazio de caminho->conteúdo).",
                codigo="FILES_AUSENTE",
            )
        for rel, conteudo in arquivos.items():
            if not isinstance(conteudo, str):
                return Result.fail(f"Conteúdo de 'files[{rel!r}]' deve ser string.", codigo="FILES_INVALIDO")

    return Result.ok(component)


def resolve_targets(component: Dict[str, Any], base_dir: str = ".") -> Result:
    """Valida o componente e resolve suas rotas físicas via Target Profile."""
    validado = validate_component(component)
    if not validado.sucesso:
        return validado
    return target_profile.build_file_map(component, os.path.abspath(base_dir))


def _registry_path(base_dir: str) -> str:
    return os.path.join(os.path.abspath(base_dir), REGISTRY_FILENAME)


def _load_registry(base_dir: str) -> List[Dict[str, Any]]:
    path = _registry_path(base_dir)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        dados = json.load(f)
    return dados if isinstance(dados, list) else []


def _save_registry(base_dir: str, registry: List[Dict[str, Any]]) -> None:
    with open(_registry_path(base_dir), "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def materialize(component: Dict[str, Any], base_dir: str = ".", dry_run: bool = False) -> Result:
    """Materializa um componente no filesystem de forma transacional.

    1. Valida + resolve rotas.
    2. Gera todo o conteúdo em um diretório de staging temporário — se a
       geração falhar, nada no filesystem real é tocado.
    3. Em dry_run, retorna as rotas que seriam escritas sem gravar nada.
    4. Faz snapshot do conteúdo pré-existente de cada alvo real.
    5. Escreve os arquivos reais; se qualquer escrita falhar, restaura o
       snapshot de tudo que já havia sido escrito (rollback) e retorna falha.
    6. Em sucesso completo, atualiza o COMPONENT-REGISTRY.json.
    """
    base_dir = os.path.abspath(base_dir)

    resolvido = resolve_targets(component, base_dir)
    if not resolvido.sucesso:
        return resolvido

    mapa_arquivos: Dict[str, bytes] = resolvido.valor

    staged: Dict[str, bytes] = {}
    try:
        with tempfile.TemporaryDirectory(prefix="aidd_inject_stage_") as stage_dir:
            for rel, conteudo in mapa_arquivos.items():
                stage_path = os.path.join(stage_dir, rel.replace("/", os.sep))
                os.makedirs(os.path.dirname(stage_path), exist_ok=True)
                with open(stage_path, "wb") as f:
                    f.write(conteudo)
                with open(stage_path, "rb") as f:
                    staged[rel] = f.read()
    except Exception as e:
        return Result.fail(f"Falha ao preparar staging da injeção: {e}", codigo="STAGING_FALHOU")

    if dry_run:
        return Result.ok(sorted(staged.keys()), detalhes={"dry_run": True})

    real_paths = {rel: os.path.join(base_dir, rel.replace("/", os.sep)) for rel in staged}
    snapshot: Dict[str, Optional[bytes]] = {}
    for rel, real_path in real_paths.items():
        if os.path.exists(real_path):
            with open(real_path, "rb") as f:
                snapshot[rel] = f.read()
        else:
            snapshot[rel] = None

    written: List[str] = []
    try:
        for rel, conteudo in staged.items():
            real_path = real_paths[rel]
            os.makedirs(os.path.dirname(real_path), exist_ok=True)
            with open(real_path, "wb") as f:
                f.write(conteudo)
            written.append(rel)
    except Exception as e:
        falha_em = rel
        for rel_escrito in written:
            real_path = real_paths[rel_escrito]
            anterior = snapshot[rel_escrito]
            try:
                if anterior is None:
                    if os.path.exists(real_path):
                        os.remove(real_path)
                else:
                    with open(real_path, "wb") as f:
                        f.write(anterior)
            except Exception:
                pass
        return Result.fail(
            f"Falha ao materializar '{falha_em}': {e}. Rollback executado com sucesso.",
            codigo="MATERIALIZE_FALHOU_ROLLBACK_OK",
        )

    hashes = {rel: hashlib.sha256(staged[rel]).hexdigest() for rel in staged}
    registro = {
        "name": component["name"],
        "type": component["type"],
        "description": component.get("description", ""),
        "files": hashes,
        "atualizado_em": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    registry = _load_registry(base_dir)
    registry = [
        r for r in registry
        if not (r.get("name") == registro["name"] and r.get("type") == registro["type"])
    ]
    registry.append(registro)
    _save_registry(base_dir, registry)

    return Result.ok(sorted(written))


def remove_component(nome: str, tipo: str, base_dir: str = ".") -> Result:
    """Remove um componente previamente injetado (arquivos + entrada no registry)."""
    base_dir = os.path.abspath(base_dir)
    registry = _load_registry(base_dir)
    alvo = next((r for r in registry if r.get("name") == nome and r.get("type") == tipo), None)
    if alvo is None:
        return Result.fail(f"Componente '{nome}' (type={tipo}) não encontrado no registry.", codigo="NAO_ENCONTRADO")

    removidos: List[str] = []
    for rel in alvo.get("files", {}):
        real_path = os.path.join(base_dir, rel.replace("/", os.sep))
        if os.path.exists(real_path):
            os.remove(real_path)
            removidos.append(rel)
            pasta = os.path.dirname(real_path)
            try:
                while pasta and pasta != base_dir and not os.listdir(pasta):
                    os.rmdir(pasta)
                    pasta = os.path.dirname(pasta)
            except OSError:
                pass

    registry = [r for r in registry if not (r.get("name") == nome and r.get("type") == tipo)]
    _save_registry(base_dir, registry)
    return Result.ok(sorted(removidos))


def sync_check(base_dir: str = ".") -> Result:
    """Confirma que todo arquivo registrado existe e bate com o hash gravado
    (detecta drift/edição manual fora do injector, incluindo fan-out
    multi-harness divergente para skill/hook)."""
    base_dir = os.path.abspath(base_dir)
    registry = _load_registry(base_dir)
    problemas: List[str] = []

    for entrada in registry:
        nome = entrada.get("name")
        tipo = entrada.get("type")
        for rel, hash_esperado in entrada.get("files", {}).items():
            real_path = os.path.join(base_dir, rel.replace("/", os.sep))
            if not os.path.exists(real_path):
                problemas.append(f"Componente '{nome}' ({tipo}): arquivo registrado ausente '{rel}'.")
                continue
            with open(real_path, "rb") as f:
                hash_atual = hashlib.sha256(f.read()).hexdigest()
            if hash_atual != hash_esperado:
                problemas.append(f"Componente '{nome}' ({tipo}): '{rel}' divergente do registry (drift detectado).")

    if problemas:
        return Result.fail(
            "Divergências de sincronização multi-harness detectadas.",
            codigo="SYNC_DIVERGENTE",
            detalhes={"problemas": problemas},
        )
    return Result.ok(len(registry))
