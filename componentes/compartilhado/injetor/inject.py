# -*- coding: utf-8 -*-
"""Use Case: inject — Injetor Universal de componentes (com run_inject e _default_component_content)."""
# Peça única do almoxarifado (fronteiras-ferramentas ciclo-01, Ticket 8): base aidd-enterprise, dono do
# conteúdo do injetor (D3), mais o motor por payload do aidd-master (resolver -> materializar ->
# sincronizar). cmd_inject atende as duas CLIs: --content-file com listas por vírgula (enterprise) e
# --conteudo-file/--projeto com --mcp-args/--mcp-env em JSON (master).

import importlib
import json
import os
from pathlib import Path
import sys


def ensure_environment():
    """Use Case `setup` da ferramenta que carregou a peça. A âncora (`__file__`) é
    <ferramenta>/<pacote de Use Cases>/commands/inject.py, e o pacote tem nome único por fatia
    (`application` no aidd-master, `application_enterprise` no aidd-enterprise; ciclo-03 T23)."""
    pacote = Path(__file__).resolve().parent.parent.name
    return importlib.import_module(f"{pacote}.commands.setup").ensure_environment()


def _core_src_path() -> str:
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(root_dir, "src", "core")


def _projeto_padrao() -> str:
    """aidd-master ou aidd-enterprise, pela localização física do módulo (a peça serve aos dois)."""
    return "aidd-master" if "aidd-master" in Path(__file__).resolve().parts else "aidd-enterprise"


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


def _cmd_inject_por_payload(args):
    """CLI do aidd-master: --conteudo-file, --projeto, --sobrescrever e --mcp-args/--mcp-env em JSON."""
    core_src = _core_src_path()
    if core_src not in sys.path:
        sys.path.insert(0, core_src)
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

    if hasattr(args, "conteudo_file") or hasattr(args, "projeto"):
        return _cmd_inject_por_payload(args)

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


def _tentar_injecao_por_payload(raw_prompt: str, base_dir: str = ".") -> bool:
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


def _tentar_injecao_por_linguagem_natural(raw_prompt: str, base_dir: str = ".") -> bool:
    """Reconhece pedidos PT-BR de injeção de componente antes do fallback para 'plan'."""
    if _projeto_padrao() == "aidd-master":
        return _tentar_injecao_por_payload(raw_prompt, base_dir)
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