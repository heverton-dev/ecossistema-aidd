# -*- coding: utf-8 -*-
"""Use Case: inject — Injetor Universal de componentes (com run_inject e _default_component_content)."""

import json
import os
import sys

from application.commands.setup import ensure_environment


def _core_src_path() -> str:
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(root_dir, "src", "core")


def _default_component_content(tipo: str, nome: str, descricao: str) -> str:
    """Gera um conteúdo padrão em PT-BR quando o usuário não fornece --content-file."""
    titulo = nome.replace("-", " ").title()
    descricao = descricao or ""
    if tipo == "skill":
        return (
            "---\n"
            f"name: {nome}\n"
            f"description: {descricao or f'Skill {nome}.'}\n"
            "commands:\n"
            f'  - "/{nome}"\n'
            "---\n\n"
            f"# {titulo}\n\n"
            f"{descricao or 'Descreva aqui o objetivo desta skill.'}\n\n"
            "## Uso\n\nDetalhe aqui o comportamento esperado ao ativar esta skill.\n"
        )
    if tipo == "rule":
        return f"# Regra: {titulo}\n\n{descricao or 'Descreva aqui a regra determinística.'}\n"
    if tipo == "spec":
        return f"# Especificação: {titulo}\n\n**Status:** RASCUNHO\n\n{descricao or 'Descreva aqui os requisitos técnicos.'}\n"
    if tipo == "agent":
        return f"# Agente: {titulo}\n\n## Missão\n\n{descricao or 'Descreva aqui a missão deste subagente.'}\n\n## Diretrizes\n\n- \n"
    if tipo == "hook":
        return json.dumps({"name": nome, "description": descricao, "trigger": "manual"}, indent=2, ensure_ascii=False)
    return descricao


def run_inject(tipo, nome, base_dir=".", descricao="", content=None, content_file=None,
                command=None, mcp_args=None, mcp_env=None, files_json=None, dry_run=False,
                sobrescrever=False):
    """Motor compartilhado de injeção — usado pelo comando CLI 'inject' e pelo IntentRouter PT-BR."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    src_core = os.path.join(root_dir, "src", "core")
    src_dir = os.path.join(root_dir, "src")
    for d in (src_core, src_dir):
        if d not in sys.path:
            sys.path.insert(0, d)

    from profiles_registry import resolver_destinos
    from materializador import materializar
    from sincronizador_harness import sincronizar

    component = {
        "tipo": tipo,
        "nome": nome,
        "descricao": descricao or f"Componente '{nome}' ({tipo}) injetado via CLI AIDD.",
        "alvo_projeto": "aidd-enterprise",
    }

    if tipo in ("skill", "rule", "spec", "agent", "hook"):
        if content_file:
            with open(content_file, "r", encoding="utf-8") as f:
                component["conteudo"] = f.read()
        elif content:
            component["conteudo"] = content
        else:
            component["conteudo"] = _default_component_content(tipo, nome, descricao)
    elif tipo == "mcp":
        if not command:
            print("[ERRO] type 'mcp' exige --mcp-command (ex: --mcp-command python).")
            sys.exit(1)
        component["command"] = command
        component["args"] = mcp_args or []
        component["env"] = mcp_env or {}
    elif tipo == "config":
        if not files_json:
            print("[ERRO] type 'config' exige --files-json apontando para um JSON {caminho: conteudo}.")
            sys.exit(1)
        with open(files_json, "r", encoding="utf-8") as f:
            component["arquivos"] = json.load(f)

    resolucao_result = resolver_destinos(component, base_dir)
    if not resolucao_result.sucesso:
        print("=" * 80)
        print(f"🧩 [INJECTOR] Injeção de componente: {tipo} '{nome}'")
        print("=" * 80)
        print(f"[FAIL] ❌ {resolucao_result.erro}")
        sys.exit(1)
    resolucao = resolucao_result.valor

    resultado = materializar(component, resolucao, sobrescrever=sobrescrever, dry_run=dry_run)

    print("=" * 80)
    if dry_run:
        print(f"🔍 [INJECTOR - DRY RUN] Simulação de injeção: {tipo} '{nome}'")
    else:
        print(f"🧩 [INJECTOR] Injeção de componente: {tipo} '{nome}'")
    print("=" * 80)

    if not resultado.sucesso:
        print(f"[FAIL] ❌ {resultado.erro}")
        for problema in (resultado.detalhes or {}).get("problemas", []):
            print(f"  - {problema}")
        sys.exit(1)

    if dry_run:
        destinos = resultado.valor if isinstance(resultado.valor, list) else resultado.valor.get("destinos", [])
        for caminho in destinos:
            print(f"  [+] {caminho}")
        print(f"\n[OK] SUCESSO: {len(destinos)} arquivo(s) simulados (dry-run).")
        return resultado

    arquivos = resultado.valor if isinstance(resultado.valor, list) else resultado.valor.get("arquivos_criados", [])
    for caminho in arquivos:
        print(f"  [+] {caminho}")

    sync_result = sincronizar(component, resolucao, arquivos)
    if not sync_result.sucesso:
        print(f"\n⚠️  [AVISO] Sincronização multi-harness parcial: {sync_result.erro}")

    print(f"\n[OK] SUCESSO: {len(arquivos)} arquivo(s) materializados e sincronizados.")
    return resultado


def cmd_inject(args):
    """Comando CLI 'inject' — injeta e sincroniza um componente em todos os harnesses."""
    ensure_environment()
    if getattr(args, "remover", False):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        src_core = os.path.join(root_dir, "src", "core")
        if src_core not in sys.path:
            sys.path.insert(0, src_core)
        from materializador import remover_componente
        target_dir = getattr(args, "dir", ".")
        res = remover_componente(args.tipo, args.nome, target_dir)
        if res.sucesso:
            print(f"🗑️ [SUCESSO] Componente '{args.nome}' ({args.tipo}) removido com sucesso de {target_dir}.")
            sys.exit(0)
        else:
            print(f"[FAIL] ❌ {res.codigo}: {res.erro}")
            sys.exit(1)

    mcp_args = [a for a in (args.mcp_args.split(",") if args.mcp_args else []) if a]
    mcp_env = {}
    if args.mcp_env:
        for par in args.mcp_env.split(","):
            if "=" in par:
                k, v = par.split("=", 1)
                mcp_env[k.strip()] = v.strip()
    run_inject(
        args.tipo, args.nome, base_dir=args.dir, descricao=args.descricao,
        content_file=args.content_file, command=args.mcp_command,
        mcp_args=mcp_args, mcp_env=mcp_env, files_json=args.files_json,
        dry_run=args.dry_run,
    )


def _tentar_injecao_por_linguagem_natural(raw_prompt: str, base_dir: str = ".") -> bool:
    """Reconhece pedidos PT-BR de injeção de componente antes do fallback para 'plan'."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    src_core = os.path.join(root_dir, "src", "core")
    src_dir = os.path.join(root_dir, "src")
    for d in (src_core, src_dir):
        if d not in sys.path:
            sys.path.insert(0, d)
    try:
        from intent_router import IntentRouter
        from detector_camada import detectar_de_texto
    except ImportError:
        return False

    intent = IntentRouter().parse_intent_result(raw_prompt)
    if intent.action != "inject":
        return False

    payload_result = detectar_de_texto(raw_prompt, alvo_projeto="aidd-enterprise")
    if not payload_result.sucesso:
        print(f"[ERRO] {payload_result.codigo}: {payload_result.erro}")
        candidatos = (payload_result.detalhes or {}).get("candidatos")
        if candidatos:
            print(f"        Candidatos possíveis: {', '.join(candidatos)}")
        else:
            print("        Use o comando explícito: python scripts/aidd.py inject <tipo> <nome>")
        sys.exit(1)

    payload = payload_result.valor
    print(f"[IntentRouter] Intenção detectada: inject '{payload['tipo']}' → '{payload['nome']}'")
    run_inject(
        tipo=payload["tipo"],
        nome=payload["nome"],
        base_dir=base_dir,
        descricao=payload["descricao"],
    )
    return True