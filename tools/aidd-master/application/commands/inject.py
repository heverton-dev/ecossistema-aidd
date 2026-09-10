# -*- coding: utf-8 -*-
"""Use Case: inject — Injetor Universal de componentes (resolver -> materializar -> sincronizar)."""

import json
import os
import sys

from application.commands.setup import ensure_environment


def _core_src_path() -> str:
    master_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(master_root, "src", "core")


def _executar_injecao(payload, target_dir: str, sobrescrever: bool = False, dry_run: bool = False) -> int:
    """Executa o pipeline completo do Injetor Universal: resolver -> materializar -> sincronizar."""
    core_src = _core_src_path()
    if core_src not in sys.path:
        sys.path.insert(0, core_src)
    from profiles_registry import resolver_destinos
    from materializador import materializar
    from sincronizador_harness import sincronizar

    prefixo = "[DRY-RUN] " if dry_run else ""
    print("=" * 80)
    print(f"🧩 {prefixo}[AIDD INJECT] Injetando '{payload.get('tipo')}' -> '{payload.get('nome')}'")
    print(f"📁 Diretório Alvo: {os.path.abspath(target_dir)}")
    print("=" * 80)

    resolucao_result = resolver_destinos(payload, target_dir)
    if not resolucao_result.sucesso:
        print(f"[ERRO] {resolucao_result.codigo}: {resolucao_result.erro}")
        return 1
    resolucao = resolucao_result.valor

    materializacao_result = materializar(
        payload, resolucao, sobrescrever=sobrescrever, dry_run=dry_run
    )
    if not materializacao_result.sucesso:
        print(f"[ERRO] {materializacao_result.codigo}: {materializacao_result.erro}")
        return 1

    if dry_run:
        destinos = (
            materializacao_result.valor
            if isinstance(materializacao_result.valor, list)
            else materializacao_result.valor.get("destinos", [])
        )
        print("\n🔍 [DRY-RUN] Destinos que seriam escritos (nenhum arquivo modificado):")
        for d in destinos:
            print(f"   - {d}")
        print("\n✨ [DRY-RUN]: Simulação concluída com sucesso!")
        return 0

    arquivos = (
        materializacao_result.valor
        if isinstance(materializacao_result.valor, list)
        else materializacao_result.valor.get("arquivos_criados", [])
    )
    print("\n📄 Arquivos materializados:")
    for a in arquivos:
        print(f"   - {a}")

    sync_result = sincronizar(payload, resolucao, arquivos)
    if sync_result.sucesso:
        passos = sync_result.valor["passos_sincronizados"] or ["registry"]
        print(f"\n🔗 Sincronização multi-harness: {', '.join(str(p) for p in passos)}")
    else:
        print(f"\n⚠️  [AVISO] Sincronização multi-harness parcial: {sync_result.erro}")

    print("\n🏆 [SUCESSO]: Componente injetado e integrado ao ecossistema AIDD!")
    return 0


def cmd_inject(args):
    """Fase 5 do Injetor Universal: subcomando explícito 'aidd inject <tipo> <nome>'."""
    ensure_environment()
    core_src = _core_src_path()
    if core_src not in sys.path:
        sys.path.insert(0, core_src)

    if getattr(args, "remover", False):
        from materializador import remover_componente
        target_dir = getattr(args, "dir", ".")
        res = remover_componente(args.tipo, args.nome, target_dir)
        if res.sucesso:
            print(f"🗑️ [SUCESSO] Componente '{args.nome}' ({args.tipo}) removido com sucesso de {target_dir}.")
            sys.exit(0)
        else:
            print(f"[ERRO] {res.codigo}: {res.erro}")
            sys.exit(1)

    from detector_camada import construir_request

    conteudo = None
    conteudo_file = getattr(args, "conteudo_file", None)
    if conteudo_file:
        with open(conteudo_file, "r", encoding="utf-8") as f:
            conteudo = f.read()

    descricao = args.descricao or f"Componente '{args.nome}' ({args.tipo}) injetado via CLI AIDD."

    mcp_command = getattr(args, "mcp_command", None)
    mcp_args = None
    mcp_env = None
    if mcp_command:
        raw_args = getattr(args, "mcp_args", None)
        if raw_args:
            try:
                parsed_args = json.loads(raw_args)
                if not isinstance(parsed_args, list) or not all(isinstance(x, str) for x in parsed_args):
                    print("[ERRO] ARGUMENTO_INVALIDO: --mcp-args deve ser uma lista JSON de strings.")
                    sys.exit(1)
                mcp_args = parsed_args
            except json.JSONDecodeError as e:
                print(f"[ERRO] JSON_INVALIDO: Falha ao decodificar --mcp-args: {e}")
                sys.exit(1)

        raw_env = getattr(args, "mcp_env", None)
        if raw_env:
            try:
                parsed_env = json.loads(raw_env)
                if not isinstance(parsed_env, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in parsed_env.items()):
                    print("[ERRO] ARGUMENTO_INVALIDO: --mcp-env deve ser um objeto JSON de chave/valor string.")
                    sys.exit(1)
                mcp_env = parsed_env
            except json.JSONDecodeError as e:
                print(f"[ERRO] JSON_INVALIDO: Falha ao decodificar --mcp-env: {e}")
                sys.exit(1)

    payload_result = construir_request(
        tipo=args.tipo,
        nome=args.nome,
        descricao=descricao,
        alvo_projeto=getattr(args, "projeto", "aidd-master"),
        conteudo=conteudo,
        command=mcp_command,
        args=mcp_args,
        env=mcp_env,
    )
    if not payload_result.sucesso:
        print(f"[ERRO] {payload_result.codigo}: {payload_result.erro}")
        sys.exit(1)

    sys.exit(_executar_injecao(
        payload_result.valor,
        getattr(args, "dir", "."),
        sobrescrever=getattr(args, "sobrescrever", False),
        dry_run=getattr(args, "dry_run", False),
    ))


def _tentar_injecao_por_linguagem_natural(raw_prompt: str, base_dir: str = ".") -> bool:
    """Reconhece pedidos PT-BR de injeção de componente antes do fallback para 'plan'.

    Retorna True (e termina o processo) se o texto foi reconhecido como um
    pedido de injeção; retorna False para deixar o fluxo cair no
    comportamento existente (planejamento de módulos de negócio via 'plan').
    """
    core_src = _core_src_path()
    if core_src not in sys.path:
        sys.path.insert(0, core_src)
    try:
        from intent_router import IntentRouter
        from detector_camada import detectar_de_texto
    except ImportError:
        return False

    intent = IntentRouter().parse_intent_result(raw_prompt)
    if intent.action != "inject":
        return False

    payload_result = detectar_de_texto(raw_prompt)
    if not payload_result.sucesso:
        print(f"[ERRO] {payload_result.codigo}: {payload_result.erro}")
        candidatos = (payload_result.detalhes or {}).get("candidatos")
        if candidatos:
            print(f"        Candidatos possíveis: {', '.join(candidatos)}")
        else:
            print("        Use o comando explícito: python scripts/aidd.py inject <tipo> <nome>")
        sys.exit(1)

    sys.exit(_executar_injecao(payload_result.valor, base_dir))