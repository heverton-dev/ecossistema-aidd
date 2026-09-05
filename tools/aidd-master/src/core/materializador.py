# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — Injetor Universal: Motor de Materialização Transacional
=============================================================================
Escreve o artefato principal e seus espelhos multi-harness em um buffer
atômico: ou todos os arquivos da operação são criados com sucesso, ou
nenhum arquivo órfão permanece em disco (rollback automático em falha de I/O).
"""

from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from result import Result
except ImportError:
    from core.result import Result


def _timestamp() -> str:
    return datetime.datetime.now().isoformat()


def gerar_conteudo_hook(nome: str, descricao: str) -> str:
    return (
        "#!/usr/bin/env bash\n"
        f"# Hook: {nome}\n"
        f"# Descrição: {descricao}\n"
        f"# Gerado em: {_timestamp()}\n"
        "set -euo pipefail\n\n"
        f'echo "[HOOK] Executando hook \'{nome}\'..."\n'
        "exit 0\n"
    )


def gerar_conteudo_skill(nome: str, descricao: str) -> str:
    titulo = nome.replace("-", " ").title()
    return (
        "---\n"
        f"name: {nome}\n"
        f"description: {descricao}\n"
        "---\n\n"
        f"# Skill: {titulo}\n\n"
        "## Objetivo\n"
        f"{descricao}\n\n"
        "## Quando usar\n"
        f"Acione esta skill sempre que a tarefa do usuário estiver relacionada a \"{nome.replace('-', ' ')}\".\n\n"
        "## Fluxo de Execução\n"
        "1. Entenda o pedido do usuário e reúna o contexto necessário do repositório.\n"
        f"2. Execute as ações determinísticas relevantes a \"{titulo}\" (leitura, análise ou geração de artefatos).\n"
        "3. Valide o resultado observando a saída real (arquivo gerado, comando executado, teste passando).\n"
        "4. Reporte o resultado ao usuário em Português do Brasil, de forma objetiva.\n\n"
        "## Gerado por\n"
        f"Injetor Universal AIDD (`aidd inject skill {nome}`) em {_timestamp()}.\n"
    )


def gerar_conteudo_mcp(nome: str, descricao: str) -> str:
    slug = nome.replace("-", "_")
    return (
        "# -*- coding: utf-8 -*-\n"
        '"""\n'
        f"Ferramenta MCP injetada: {nome}\n"
        f"{descricao}\n"
        "Carregada dinamicamente por MCPServer.register_injected_tools() a partir de src/core/mcp/.\n"
        '"""\n\n'
        "from typing import Any, Dict\n\n"
        "TOOL_DEF: Dict[str, Any] = {\n"
        f'    "name": "{slug}",\n'
        f'    "description": "{descricao}",\n'
        '    "input_schema": {\n'
        '        "type": "object",\n'
        '        "properties": {\n'
        '            "parametro": {"type": "string", "description": "Parâmetro livre de entrada da ferramenta."}\n'
        "        }\n"
        "    }\n"
        "}\n\n\n"
        "def handler(params: Dict[str, Any]) -> Dict[str, Any]:\n"
        f'    """Executa a ferramenta MCP \'{slug}\' e retorna um payload estruturado."""\n'
        '    parametro = params.get("parametro", "")\n'
        "    return {\n"
        f'        "ferramenta": "{slug}",\n'
        f'        "descricao": "{descricao}",\n'
        '        "parametro_recebido": parametro,\n'
        '        "status": "executado",\n'
        "    }\n"
    )


def gerar_conteudo_rule(nome: str, descricao: str) -> str:
    titulo = nome.replace("-", " ").title()
    return (
        f"# 📐 Regra: {titulo}\n\n"
        f"> {descricao}\n\n"
        "## Aplicação\n"
        "- Esta regra é vinculada automaticamente em `AGENTS.md` e nos templates multi-harness "
        "(`templates/core/AGENTS.md`, `templates/core/CLAUDE.md`, `templates/core/GEMINI.md`) pelo "
        "Sincronizador de Harness.\n"
        "- Todo agente de IA operando neste ecossistema DEVE respeitar esta regra em conjunto com os "
        "Quality Gates existentes.\n\n"
        "## Critério de Verificação\n"
        f"Determinístico: revisão de código/PR deve citar `{nome}.md` sempre que a regra for aplicável.\n"
    )


def gerar_conteudo_spec(nome: str, descricao: str) -> str:
    titulo = nome.replace("-", " ").title()
    return (
        f"# Especificação Técnica: {titulo}\n\n"
        "**Status:** PLANEJADO\n"
        f"**Gerado em:** {_timestamp()}\n\n"
        "## Contexto\n"
        f"{descricao}\n\n"
        "## Escopo\n"
        f"- Definir o comportamento funcional de \"{titulo}\".\n"
        "- Mapear módulos/kernels afetados em `src/`.\n"
        "- Definir critério de aceite mecânico (gate ou teste que prova o comportamento).\n\n"
        "## Critério de Aceite\n"
        "Descrever aqui o comando/teste que, ao rodar com exit 0, homologa esta especificação.\n"
    )


def gerar_conteudo_config(nome: str, descricao: str) -> str:
    return json.dumps(
        {"nome": nome, "descricao": descricao, "gerado_em": _timestamp(), "parametros": {}},
        ensure_ascii=False,
        indent=2,
    )


def gerar_conteudo_agent(nome: str, descricao: str) -> str:
    titulo = nome.replace("-", " ").title()
    return (
        f"# Agente: {titulo}\n\n"
        f"**Papel:** {descricao}\n\n"
        "## Responsabilidades\n"
        f"- Executar tarefas relacionadas a \"{nome.replace('-', ' ')}\" dentro do ecossistema AIDD.\n"
        "- Reportar resultados factuais (nunca hipotéticos) ao orquestrador.\n\n"
        "## Integração\n"
        "Registrado como padrão de intenção em `src/core/intent_router.py` pelo Sincronizador de Harness.\n"
    )


_GERADORES = {
    "skill": gerar_conteudo_skill,
    "mcp": gerar_conteudo_mcp,
    "rule": gerar_conteudo_rule,
    "spec": gerar_conteudo_spec,
    "config": gerar_conteudo_config,
    "agent": gerar_conteudo_agent,
    "hook": gerar_conteudo_hook,
}

CANONICAL_TEMPLATES: Dict[str, str] = {
    "hook": "componentes/{alvo_projeto}/hooks/{nome}/hook.sh",
}


def _default_ecossistema_root() -> Path:
    """Raiz real do monorepo ecossistema-aidd.

    Isolada para monkeypatch em testes (mesmo padrão do aidd-forge).
    """
    return Path(__file__).resolve().parents[4]


def resolve_canonical_destination(
    tipo: str,
    nome: str,
    alvo_projeto: str = "aidd-master",
    ecossistema_root: Optional[Path] = None,
) -> Optional[Path]:
    """Resolve o caminho canônico do componente no monorepo."""
    if tipo not in CANONICAL_TEMPLATES:
        return None
    if ecossistema_root is None:
        ecossistema_root = _default_ecossistema_root()
    return Path(ecossistema_root) / CANONICAL_TEMPLATES[tipo].format(nome=nome, alvo_projeto=alvo_projeto)


def sincronizar_componente(
    tipo: str,
    ferramenta: str = "aidd-master",
    ecossistema_root: Optional[Path] = None,
) -> int:
    """Dispara a sincronização multi-harness via ecossistema.py ou fallback."""
    if ecossistema_root is None:
        ecossistema_root = _default_ecossistema_root()

    script_ecossistema = ecossistema_root / "ecossistema.py"
    if script_ecossistema.exists():
        cmd = [
            sys.executable,
            str(script_ecossistema),
            "components",
            "sync",
            "--tipo",
            tipo,
            "--ferramenta",
            ferramenta,
        ]
        try:
            res = subprocess.run(cmd, cwd=str(ecossistema_root), capture_output=True, text=True)
            return res.returncode
        except Exception:
            pass

    try:
        scripts_dir = str(ecossistema_root / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import gestor_componentes
        gestor_componentes.sync(tipo=tipo, ferramenta=ferramenta)
        return 0
    except Exception:
        return 1


def resolver_conteudo(payload: Dict[str, Any]) -> str:
    """Retorna o 'conteudo' explícito do payload, ou gera um scaffold completo (nunca stub)."""
    if payload.get("conteudo"):
        return payload["conteudo"]
    gerador = _GERADORES[payload["tipo"]]
    return gerador(payload["nome"], payload["descricao"])


def _caminho_seguro(rel: str) -> bool:
    """Valida se o caminho relativo é estritamente seguro contra path traversal."""
    if not rel or not isinstance(rel, str):
        return False
    if os.path.isabs(rel) or ":" in rel:
        return False
    norm = rel.replace("\\", "/")
    if norm.startswith("/"):
        return False
    partes = norm.split("/")
    for p in partes:
        if p in ("..", ".", ""):
            return False
    return True


def remover_componente(tipo: str, nome: str, root_dir: str = ".") -> Result:
    """Remove um componente registrado em CAPABILITIES.json e limpa arquivos e diretórios vazios."""
    root_dir = os.path.abspath(root_dir)
    registry_path = os.path.join(root_dir, "CAPABILITIES.json")
    if not os.path.isfile(registry_path):
        return Result.fail(
            f"Registro CAPABILITIES.json não encontrado em {root_dir}.",
            codigo="COMPONENTE_NAO_ENCONTRADO",
        )

    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            catalogo = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return Result.fail(
            f"Falha ao ler registry {registry_path}: {exc}",
            codigo="REGISTRY_INVALIDO",
        )

    lista = catalogo.get(tipo, [])
    componente = None
    for c in lista:
        if isinstance(c, dict) and c.get("nome") == nome:
            componente = c
            break

    if componente is None:
        return Result.fail(
            f"Componente '{nome}' do tipo '{tipo}' não encontrado no catálogo.",
            codigo="COMPONENTE_NAO_ENCONTRADO",
        )

    arquivos_remover: List[str] = []
    if "arquivos_hashes" in componente and isinstance(componente["arquivos_hashes"], dict):
        arquivos_remover = [os.path.join(root_dir, p) for p in componente["arquivos_hashes"].keys()]
    elif "arquivos" in componente and isinstance(componente["arquivos"], list):
        arquivos_remover = [
            p if os.path.isabs(p) else os.path.join(root_dir, p)
            for p in componente["arquivos"]
        ]

    # Destino canônico (ex.: componentes/{alvo_projeto}/hooks/{nome}/hook.sh) é escrito
    # por materializar() fora da lista "arquivos_criados"/"arquivos_hashes" (melhor
    # esforço, não falha a operação) — sem isso aqui, remover_componente() deixaria
    # esse arquivo órfão. Testa as duas raízes possíveis (ecossistema real e root_dir
    # do teste/projeto) porque materializar() também escreve nas duas quando aplicável.
    alvo_projeto = componente.get("alvo_projeto", "aidd-master")
    for candidato_root in (_default_ecossistema_root(), Path(root_dir)):
        try:
            canonical = resolve_canonical_destination(
                tipo, nome, alvo_projeto=alvo_projeto, ecossistema_root=candidato_root
            )
        except Exception:
            canonical = None
        if canonical is not None:
            arquivos_remover.append(str(canonical))

    removidos: List[str] = []
    for arq in arquivos_remover:
        abs_p = os.path.abspath(arq)
        if os.path.isfile(abs_p):
            try:
                os.remove(abs_p)
                removidos.append(abs_p)
            except OSError:
                pass

        # Limpeza de diretórios vazios subindo até root_dir
        d = os.path.dirname(abs_p)
        while d != root_dir and d.startswith(root_dir) and os.path.isdir(d):
            try:
                if not os.listdir(d):
                    os.rmdir(d)
                    d = os.path.dirname(d)
                else:
                    break
            except OSError:
                break

    catalogo[tipo] = [c for c in lista if c.get("nome") != nome]
    try:
        with open(registry_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(catalogo, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except OSError as exc:
        return Result.fail(
            f"Falha ao persistir registry atualizado: {exc}",
            codigo="REGISTRY_FALHOU",
        )

    return Result.ok({"removidos": removidos, "nome": nome, "tipo": tipo})


def _executar_rollback(
    criados: List[str],
    dirs_criados: List[str],
    snapshot: Dict[str, Optional[bytes]],
) -> None:
    for c in reversed(criados):
        try:
            old_bytes = snapshot.get(c)
            if old_bytes is None:
                if os.path.isfile(c):
                    os.remove(c)
            else:
                with open(c, "wb") as f_roll:
                    f_roll.write(old_bytes)
        except OSError:
            pass
    for d in reversed(dirs_criados):
        try:
            if os.path.isdir(d) and not os.listdir(d):
                os.rmdir(d)
        except OSError:
            pass


def materializar(
    payload: Dict[str, Any],
    resolucao: Dict[str, Any],
    sobrescrever: bool = False,
    dry_run: bool = False,
) -> Result:
    """Escreve o artefato principal e seus espelhos multi-harness de forma transacional.

    Se qualquer escrita falhar no meio da operação, o estado prévio exato de
    cada destino é restaurado (rollback de snapshot completo).
    """
    root_dir = resolucao.get("root_dir")
    if not root_dir:
        root_dir = os.path.abspath(".")

    # Rota especial: config com mapa arbitrário de arquivos
    if payload.get("tipo") == "config" and payload.get("arquivos"):
        mapa_arquivos = payload["arquivos"]
        for rel in mapa_arquivos:
            if not _caminho_seguro(rel):
                return Result.fail(
                    f"Caminho inseguro detectado: {rel}",
                    codigo="PATH_TRAVERSAL_REJEITADO",
                    detalhes={"caminho": rel},
                )

        destinos = [os.path.join(root_dir, rel) for rel in mapa_arquivos.keys()]
        if dry_run:
            return Result.ok(destinos, detalhes={"dry_run": True})

        if not sobrescrever:
            existentes = [d for d in destinos if os.path.isfile(d)]
            if existentes:
                return Result.fail(
                    f"Destino já existe (use sobrescrever=True para forçar): {existentes[0]}",
                    codigo="DESTINO_JA_EXISTE",
                    detalhes={"existentes": existentes},
                )

        snapshot: Dict[str, Optional[bytes]] = {}
        for d in destinos:
            if os.path.isfile(d):
                try:
                    with open(d, "rb") as f_snap:
                        snapshot[d] = f_snap.read()
                except OSError:
                    snapshot[d] = None
            else:
                snapshot[d] = None

        criados: List[str] = []
        dirs_criados: List[str] = []
        try:
            for rel, cont in mapa_arquivos.items():
                dest = os.path.join(root_dir, rel)
                parent = os.path.dirname(dest)
                if parent and not os.path.isdir(parent):
                    os.makedirs(parent, exist_ok=True)
                    dirs_criados.append(parent)
                with open(dest, "w", encoding="utf-8", newline="\n") as f:
                    f.write(cont)
                criados.append(dest)
            return Result.ok({"arquivos_criados": criados, "conteudo": mapa_arquivos})
        except Exception as e:
            _executar_rollback(criados, dirs_criados, snapshot)
            return Result.fail(
                f"Falha na materialização, rollback executado: {e}",
                codigo="MATERIALIZACAO_FALHOU",
                detalhes={"arquivos_removidos_no_rollback": criados},
            )

    # Rota especial: MCP externo com command (registra em mcp.json no projeto alvo)
    if payload.get("tipo") == "mcp" and payload.get("command"):
        mcp_path = os.path.join(root_dir, "mcp.json")
        if dry_run:
            return Result.ok([mcp_path], detalhes={"dry_run": True})

        dados: Dict[str, Any] = {"mcpServers": {}}
        conteudo_antigo: Optional[str] = None
        existia_antes = os.path.isfile(mcp_path)

        if existia_antes:
            try:
                with open(mcp_path, "r", encoding="utf-8") as f:
                    conteudo_antigo = f.read()
                existente = json.loads(conteudo_antigo)
                if not isinstance(existente, dict):
                    return Result.fail(
                        "mcp.json existente não é um objeto JSON válido.",
                        codigo="MCP_JSON_INVALIDO",
                    )
                dados = existente
                if "mcpServers" not in dados or not isinstance(dados["mcpServers"], dict):
                    dados["mcpServers"] = {}
            except Exception as exc:
                return Result.fail(
                    f"mcp.json existente é inválido: {exc}",
                    codigo="MCP_JSON_INVALIDO",
                )

        dados["mcpServers"][payload["nome"]] = {
            "command": payload["command"],
            "args": payload.get("args", []),
            "env": payload.get("env", {}),
        }

        novo_conteudo = json.dumps(dados, indent=2, ensure_ascii=False) + "\n"
        try:
            with open(mcp_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(novo_conteudo)
            return Result.ok({"arquivos_criados": [mcp_path], "conteudo": novo_conteudo})
        except OSError as exc:
            if existia_antes and conteudo_antigo is not None:
                try:
                    with open(mcp_path, "w", encoding="utf-8", newline="\n") as f:
                        f.write(conteudo_antigo)
                except OSError:
                    pass
            elif not existia_antes and os.path.exists(mcp_path):
                try:
                    os.remove(mcp_path)
                except OSError:
                    pass
            return Result.fail(
                f"Falha ao escrever mcp.json, rollback executado: {exc}",
                codigo="MATERIALIZACAO_FALHOU",
            )

    destinos: List[str] = [resolucao["dest_principal"]] + list(resolucao.get("mirrors", []))
    conteudo = resolver_conteudo(payload)

    if dry_run:
        return Result.ok(destinos, detalhes={"dry_run": True})

    if not sobrescrever:
        existentes = [d for d in destinos if os.path.isfile(d)]
        if existentes:
            return Result.fail(
                f"Destino já existe (use sobrescrever=True para forçar): {existentes[0]}",
                codigo="DESTINO_JA_EXISTE",
                detalhes={"existentes": existentes},
            )

    snapshot = {}
    for d in destinos:
        if os.path.isfile(d):
            try:
                with open(d, "rb") as f_snap:
                    snapshot[d] = f_snap.read()
            except OSError:
                snapshot[d] = None
        else:
            snapshot[d] = None

    criados = []
    dirs_criados = []
    try:
        for destino in destinos:
            parent = os.path.dirname(destino)
            if parent and not os.path.isdir(parent):
                os.makedirs(parent, exist_ok=True)
                dirs_criados.append(parent)
            with open(destino, "w", encoding="utf-8", newline="\n") as f:
                f.write(conteudo)
            criados.append(destino)

        # Integração canônica Package 7 (ex.: hook)
        alvo_projeto = payload.get("alvo_projeto", "aidd-master")
        canonical_dest = resolve_canonical_destination(
            payload["tipo"], payload["nome"], alvo_projeto=alvo_projeto
        )
        if canonical_dest is not None and str(canonical_dest) not in destinos:
            try:
                canonical_dest.parent.mkdir(parents=True, exist_ok=True)
                canonical_dest.write_text(conteudo, encoding="utf-8")
            except Exception:
                pass

        if (Path(root_dir) / "componentes").is_dir():
            target_canonical = resolve_canonical_destination(
                payload["tipo"],
                payload["nome"],
                alvo_projeto=alvo_projeto,
                ecossistema_root=Path(root_dir),
            )
            if target_canonical is not None and str(target_canonical) not in destinos:
                try:
                    target_canonical.parent.mkdir(parents=True, exist_ok=True)
                    target_canonical.write_text(conteudo, encoding="utf-8")
                except Exception:
                    pass

        if payload["tipo"] in CANONICAL_TEMPLATES:
            sincronizar_componente(payload["tipo"], ferramenta=alvo_projeto)

        return Result.ok({"arquivos_criados": criados, "conteudo": conteudo})

    except Exception as e:
        _executar_rollback(criados, dirs_criados, snapshot)
        return Result.fail(
            f"Falha na materialização, rollback executado: {e}",
            codigo="MATERIALIZACAO_FALHOU",
            detalhes={"arquivos_removidos_no_rollback": criados},
        )
