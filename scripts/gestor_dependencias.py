# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — GESTOR DE DEPENDÊNCIAS EXTERNAS (SKILLS + MCPS DE TERCEIROS)
=============================================================================
Lê gates/dependencias_externas.json (fonte única declarativa) e garante que
cada skill/MCP de terceiro declarado esteja de fato instalado/registrado
nesta máquina — pensado para rodar uma vez após `git clone` e sempre que uma
nova dependência for adicionada via `/dependencia`.

Diferente de scripts/gestor_componentes.py: aquele espelha componentes
AUTORAIS deste repositório (skills/comandos internos) por cópia física.
Este trata dependências de TERCEIROS que já têm seu próprio instalador
(ex.: `npx <pacote> install`) ou que só precisam de uma entrada de config
(MCP servers, mesclada em `.mcp.json`, nunca sobrescrevendo o que já existe).

Harnesses de MCP com schema confirmado nesta v1 (via doc oficial de cada
ferramenta, nunca por suposição):
  - "claude-code"  -> `.mcp.json`              {"mcpServers": {...}}
  - "opencode"     -> `opencode.jsonc`         {"mcp": {...}}
  - "cursor"       -> `.cursor/mcp.json`       {"mcpServers": {...}}
  - "gemini-cli"   -> `.gemini/settings.json`  {"mcpServers": {...}}
  - "mimocode"     -> `mimocode.jsonc`         {"mcp": {...}} (arquivo PRÓPRIO,
    distinto de opencode.jsonc mesmo sendo fork do OpenCode)
  - "antigravity"  -> `.agents/mcp_config.json` {"mcpServers": {...}}
Outros harnesses ficam como TODO explícito — não adivinhar schema sem
confirmar.

Cada MCP declarado tem "tipo": "stdio" (padrão, comando local — chaves
`comando`/`args`/`env`) ou "tipo": "remote" (servidor HTTP remoto — chave
`url`, sem processo local). O schema de saída por harness é adaptado a
partir dessas mesmas chaves (ex.: remoto vira {"type":"http","url":...} em
`.mcp.json` e {"type":"remote","url":...,"enabled":true} em `opencode.jsonc`).

Uso:
  python scripts/gestor_dependencias.py bootstrap [--tipo skills|mcps|todos] [--dry-run]
  python scripts/gestor_dependencias.py add-skill --nome <nome> --pacote <pacote> --instalar "<comando>" [--verificar <caminho>] [--gitignore "padrao1,padrao2"]
  python scripts/gestor_dependencias.py add-mcp --nome <nome> --pacote <pacote> --comando <cmd> --args "a,b,c" [--env VAR1,VAR2] [--harnesses claude-code,opencode]
  python scripts/gestor_dependencias.py add-mcp --nome <nome> --pacote <pacote> --tipo remote --url <url> [--harnesses claude-code,opencode]
  python scripts/gestor_dependencias.py list
  python scripts/gestor_dependencias.py verify
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFESTO_PATH = os.path.join(ROOT_DIR, "gates", "dependencias_externas.json")
GITIGNORE_PATH = os.path.join(ROOT_DIR, ".gitignore")

# Harnesses com schema de MCP config confirmado nesta v1 (ver docstring acima).
# "schema_inicial": chaves extras mescladas apenas na PRIMEIRA criação do arquivo
# (nunca sobrescreve um arquivo já existente).
DESTINOS_MCP = {
    "claude-code": {"caminho": os.path.join(ROOT_DIR, ".mcp.json"), "chave": "mcpServers"},
    "opencode": {
        "caminho": os.path.join(ROOT_DIR, "opencode.jsonc"), "chave": "mcp",
        "schema_inicial": {"$schema": "https://opencode.ai/config.json"},
    },
    "cursor": {"caminho": os.path.join(ROOT_DIR, ".cursor", "mcp.json"), "chave": "mcpServers"},
    "gemini-cli": {"caminho": os.path.join(ROOT_DIR, ".gemini", "settings.json"), "chave": "mcpServers"},
    "mimocode": {
        "caminho": os.path.join(ROOT_DIR, "mimocode.jsonc"), "chave": "mcp",
        "schema_inicial": {"$schema": "https://mimo.xiaomi.com/mimocode/config.json"},
    },
    "antigravity": {"caminho": os.path.join(ROOT_DIR, ".agents", "mcp_config.json"), "chave": "mcpServers"},
}


def carregar_manifesto():
    if not os.path.exists(MANIFESTO_PATH):
        return {"versao": "1.0.0", "descricao": "", "skills": {}, "mcps": {}}
    with open(MANIFESTO_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _salvar_manifesto(manifesto):
    tmp_path = MANIFESTO_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(manifesto, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp_path, MANIFESTO_PATH)


MSG_ERRO_NPX_AUSENTE = "Node.js/npx ausente. Instale Node.js LTS ou execute preflight-host --fix"


def _npx_disponivel() -> bool:
    """Verifica se npx ou npx.cmd está disponível no PATH do host."""
    if shutil.which("npx"):
        return True
    if os.name == "nt" and shutil.which("npx.cmd"):
        return True
    return False


def _comando_requer_npx(comando: str) -> bool:
    """Verifica se o comando invoca npx."""
    partes = comando.replace("&&", " ").replace("||", " ").replace(";", " ").split()
    return any(p == "npx" or p.endswith("/npx") or p.endswith("\\npx") or p == "npx.cmd" for p in partes)


def _skill_instalada(cfg):
    caminho = os.path.join(ROOT_DIR, cfg["verificar"])
    return os.path.exists(caminho)


def bootstrap_skills(apenas=None, dry_run=False):
    """Roda o instalador de cada skill declarada ainda não verificada. Nunca reinstala à toa."""
    manifesto = carregar_manifesto()
    relatorio = {"ja_instaladas": [], "instaladas": [], "falhas": []}

    for nome, cfg in manifesto.get("skills", {}).items():
        if apenas and nome != apenas:
            continue
        if _skill_instalada(cfg):
            relatorio["ja_instaladas"].append(nome)
            continue
        if dry_run:
            relatorio["instaladas"].append(f"[DRY-RUN] {nome}: {cfg['instalar']}")
            continue

        comando = cfg["instalar"]
        if _comando_requer_npx(comando) and not _npx_disponivel():
            relatorio["falhas"].append(f"{nome} ({MSG_ERRO_NPX_AUSENTE})")
            continue

        try:
            if os.name == "nt":
                # No Windows, 'npx' e outros instaladores costumam ser shims .cmd,
                # que CreateProcess (subprocess sem shell=True) nao resolve sozinho.
                proc = subprocess.run(
                    comando,
                    cwd=ROOT_DIR,
                    shell=True,
                    capture_output=True,
                    text=True,
                )
                codigo = proc.returncode
                if codigo != 0:
                    saida_erro = (proc.stderr or "") + (proc.stdout or "")
                    if (
                        "not recognized" in saida_erro.lower()
                        or "não é reconhecido" in saida_erro.lower()
                    ) and _comando_requer_npx(comando):
                        relatorio["falhas"].append(f"{nome} ({MSG_ERRO_NPX_AUSENTE})")
                        continue
                    relatorio["falhas"].append(f"{nome} (exit {codigo})")
                    continue
            else:
                proc = subprocess.run(
                    shlex.split(comando),
                    cwd=ROOT_DIR,
                    capture_output=True,
                    text=True,
                )
                codigo = proc.returncode
                if codigo != 0:
                    relatorio["falhas"].append(f"{nome} (exit {codigo})")
                    continue
        except FileNotFoundError:
            if _comando_requer_npx(comando):
                relatorio["falhas"].append(f"{nome} ({MSG_ERRO_NPX_AUSENTE})")
            else:
                relatorio["falhas"].append(f"{nome} (comando nao encontrado)")
            continue
        except OSError as e:
            relatorio["falhas"].append(f"{nome} (erro de sistema: {e})")
            continue

        if codigo == 0:
            relatorio["instaladas"].append(nome)

    return relatorio


def _carregar_mcp_config(caminho, chave, schema_inicial=None):
    if not os.path.exists(caminho):
        dados = dict(schema_inicial or {})
        dados[chave] = {}
        return dados
    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)
    dados.setdefault(chave, {})
    return dados


def _mcp_presente(nome, caminho, chave):
    if not os.path.exists(caminho):
        return False
    dados = _carregar_mcp_config(caminho, chave)
    return nome in dados[chave]


def _construir_entrada_mcp(cfg, harness):
    """Adapta as chaves declarativas do manifesto (tipo/comando/args/env/url) para o
    schema de config nativo de cada harness (schemas confirmados via doc oficial de
    cada ferramenta — ver docstring do módulo)."""
    tipo = cfg.get("tipo", "stdio")

    if tipo == "remote":
        url = cfg["url"]
        if harness == "claude-code":
            return {"type": "http", "url": url}
        if harness == "opencode":
            return {"type": "remote", "url": url, "enabled": True}
        if harness == "cursor":
            return {"url": url}
        if harness == "gemini-cli":
            return {"httpUrl": url}
        if harness == "mimocode":
            return {"type": "remote", "url": url, "enabled": True}
        if harness == "antigravity":
            return {"serverUrl": url}
        raise ValueError(f"harness '{harness}' sem schema de MCP remoto confirmado nesta v1")

    entrada_env = {var: f"${{{var}}}" for var in cfg["env"]} if cfg.get("env") else None
    if harness == "claude-code":
        entrada = {"command": cfg["comando"], "args": cfg.get("args", [])}
        if entrada_env:
            entrada["env"] = entrada_env
        return entrada
    if harness == "opencode":
        return {"type": "local", "command": [cfg["comando"]] + list(cfg.get("args", []))}
    if harness == "cursor":
        entrada = {"command": cfg["comando"], "args": cfg.get("args", [])}
        if entrada_env:
            entrada["env"] = entrada_env
        return entrada
    if harness == "gemini-cli":
        entrada = {"command": cfg["comando"], "args": cfg.get("args", [])}
        if entrada_env:
            entrada["env"] = entrada_env
        return entrada
    if harness == "mimocode":
        entrada = {"type": "local", "command": [cfg["comando"]] + list(cfg.get("args", [])), "enabled": True}
        if entrada_env:
            entrada["environment"] = entrada_env
        return entrada
    if harness == "antigravity":
        entrada = {"command": cfg["comando"], "args": cfg.get("args", [])}
        if entrada_env:
            entrada["env"] = entrada_env
        return entrada
    raise ValueError(f"harness '{harness}' sem schema de MCP local confirmado nesta v1")


def _mesclar_mcp(nome, cfg, harness, caminho, chave, dry_run, schema_inicial=None):
    dados = _carregar_mcp_config(caminho, chave, schema_inicial=schema_inicial)
    dados[chave][nome] = _construir_entrada_mcp(cfg, harness)

    if dry_run:
        return
    tmp_path = caminho + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp_path, caminho)


def bootstrap_mcps(apenas=None, dry_run=False):
    """Garante que cada MCP declarado esteja mesclado no config do(s) harness(es)-alvo."""
    manifesto = carregar_manifesto()
    relatorio = {"ja_registrados": [], "registrados": [], "harnesses_sem_suporte": []}

    for nome, cfg in manifesto.get("mcps", {}).items():
        if apenas and nome != apenas:
            continue
        for harness in cfg.get("harnesses_alvo", []):
            if harness not in DESTINOS_MCP:
                relatorio["harnesses_sem_suporte"].append(f"{nome} -> {harness} (schema nao confirmado, TODO)")
                continue
            destino = DESTINOS_MCP[harness]
            if _mcp_presente(nome, destino["caminho"], destino["chave"]):
                relatorio["ja_registrados"].append(f"{nome} ({harness})")
                continue
            _mesclar_mcp(
                nome, cfg, harness, destino["caminho"], destino["chave"], dry_run,
                schema_inicial=destino.get("schema_inicial"),
            )
            relatorio["registrados"].append(f"{nome} ({harness})" + (" [DRY-RUN]" if dry_run else ""))

    return relatorio


def _adicionar_padroes_gitignore(padroes):
    if not padroes:
        return []
    conteudo_atual = ""
    if os.path.exists(GITIGNORE_PATH):
        with open(GITIGNORE_PATH, "r", encoding="utf-8") as f:
            conteudo_atual = f.read()

    linhas_existentes = set(conteudo_atual.splitlines())
    novos = [p for p in padroes if p not in linhas_existentes]
    if not novos:
        return []

    with open(GITIGNORE_PATH, "a", encoding="utf-8") as f:
        if conteudo_atual and not conteudo_atual.endswith("\n"):
            f.write("\n")
        f.write("\n# Dependencias externas instaladas via 'python ecossistema.py dependencia bootstrap'\n")
        for p in novos:
            f.write(p + "\n")
    return novos


def adicionar_skill(nome, pacote, instalar, verificar, gitignore_patterns, dry_run=False):
    manifesto = carregar_manifesto()
    manifesto.setdefault("skills", {})
    ja_existia = nome in manifesto["skills"]
    manifesto["skills"][nome] = {
        "pacote": pacote,
        "instalar": instalar,
        "verificar": verificar,
        "gitignore": gitignore_patterns,
    }
    if not dry_run:
        _salvar_manifesto(manifesto)
        novos_ignore = _adicionar_padroes_gitignore(gitignore_patterns)
    else:
        novos_ignore = list(gitignore_patterns)

    relatorio_bootstrap = bootstrap_skills(apenas=nome, dry_run=dry_run)
    return {"ja_existia_no_manifesto": ja_existia, "gitignore_adicionado": novos_ignore, "bootstrap": relatorio_bootstrap}


def adicionar_mcp(nome, pacote, tipo, comando, args, env, url, harnesses, dry_run=False):
    manifesto = carregar_manifesto()
    manifesto.setdefault("mcps", {})
    ja_existia = nome in manifesto["mcps"]
    if tipo == "remote":
        entrada_manifesto = {"pacote": pacote, "tipo": "remote", "url": url, "harnesses_alvo": harnesses}
    else:
        entrada_manifesto = {
            "pacote": pacote,
            "comando": comando,
            "args": args,
            "env": env,
            "harnesses_alvo": harnesses,
        }
    manifesto["mcps"][nome] = entrada_manifesto
    if not dry_run:
        _salvar_manifesto(manifesto)

    relatorio_bootstrap = bootstrap_mcps(apenas=nome, dry_run=dry_run)
    return {"ja_existia_no_manifesto": ja_existia, "bootstrap": relatorio_bootstrap}


def listar():
    manifesto = carregar_manifesto()
    linhas = []
    linhas.append("Skills externas:")
    for nome, cfg in manifesto.get("skills", {}).items():
        status = "[OK] instalada" if _skill_instalada(cfg) else "[FALTA] nao instalada"
        linhas.append(f"  - {nome:<24} {status}  ({cfg['pacote']})")

    linhas.append("MCPs externos:")
    for nome, cfg in manifesto.get("mcps", {}).items():
        for harness in cfg.get("harnesses_alvo", []):
            if harness not in DESTINOS_MCP:
                linhas.append(f"  - {nome:<24} [SEM SUPORTE] harness '{harness}' sem schema confirmado nesta v1")
                continue
            destino = DESTINOS_MCP[harness]
            status = "[OK] registrado" if _mcp_presente(nome, destino["caminho"], destino["chave"]) else "[FALTA] nao registrado"
            linhas.append(f"  - {nome:<24} {status}  ({harness}, {cfg['pacote']})")
    return linhas


def verificar():
    """Só lê. Retorna (total_declarado, lista_de_problemas)."""
    manifesto = carregar_manifesto()
    problemas = []
    total = 0

    for nome, cfg in manifesto.get("skills", {}).items():
        total += 1
        if not _skill_instalada(cfg):
            problemas.append(f"[skill/{nome}] nao instalada (esperado em {cfg['verificar']})")

    for nome, cfg in manifesto.get("mcps", {}).items():
        for harness in cfg.get("harnesses_alvo", []):
            total += 1
            if harness not in DESTINOS_MCP:
                problemas.append(f"[mcp/{nome}] harness '{harness}' sem schema de config confirmado nesta v1")
                continue
            destino = DESTINOS_MCP[harness]
            if not _mcp_presente(nome, destino["caminho"], destino["chave"]):
                problemas.append(f"[mcp/{nome}] nao registrado em {os.path.relpath(destino['caminho'], ROOT_DIR)} ({harness})")

    return total, problemas


def _ativar_git_hooks(dry_run=False):
    """Aponta core.hooksPath para .githooks/ (pre-commit auto-sync de componentes/). Idempotente."""
    atual = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"], cwd=ROOT_DIR, capture_output=True, text=True
    ).stdout.strip()
    if atual == ".githooks":
        return "ja_ativo"
    if dry_run:
        return "[DRY-RUN] ativaria core.hooksPath=.githooks"
    subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=ROOT_DIR, check=True)
    return "ativado"


def _cmd_bootstrap(args_ns):
    resultado_hooks = _ativar_git_hooks(dry_run=args_ns.dry_run)
    print(f"Git hooks (pre-commit auto-sync de componentes/): {resultado_hooks}")

    tipo = args_ns.tipo
    if tipo in ("skills", "todos"):
        rel_skills = bootstrap_skills(dry_run=args_ns.dry_run)
        print(f"Skills ja instaladas: {len(rel_skills['ja_instaladas'])} ({', '.join(rel_skills['ja_instaladas']) or '-'})")
        print(f"Skills instaladas agora: {len(rel_skills['instaladas'])}")
        for item in rel_skills["instaladas"]:
            print(f"  [INSTALADA] {item}")
        for item in rel_skills["falhas"]:
            print(f"  [FALHA] {item}")
    if tipo in ("mcps", "todos"):
        rel_mcps = bootstrap_mcps(dry_run=args_ns.dry_run)
        print(f"MCPs ja registrados: {len(rel_mcps['ja_registrados'])} ({', '.join(rel_mcps['ja_registrados']) or '-'})")
        print(f"MCPs registrados agora: {len(rel_mcps['registrados'])}")
        for item in rel_mcps["registrados"]:
            print(f"  [REGISTRADO] {item}")
        for item in rel_mcps["harnesses_sem_suporte"]:
            print(f"  [SEM SUPORTE] {item}")
    return 0


def _cmd_add_skill(args_ns):
    gitignore_patterns = [p.strip() for p in (args_ns.gitignore or "").split(",") if p.strip()]
    resultado = adicionar_skill(
        args_ns.nome, args_ns.pacote, args_ns.instalar, args_ns.verificar, gitignore_patterns
    )
    if resultado["ja_existia_no_manifesto"]:
        print(f"[ATUALIZADA] '{args_ns.nome}' ja existia no manifesto, entrada sobrescrita.")
    else:
        print(f"[REGISTRADA] '{args_ns.nome}' adicionada ao manifesto.")
    for p in resultado["gitignore_adicionado"]:
        print(f"  [.gitignore] +{p}")
    for item in resultado["bootstrap"]["ja_instaladas"]:
        print(f"  [JA INSTALADA] {item}")
    for item in resultado["bootstrap"]["instaladas"]:
        print(f"  [INSTALADA] {item}")
    for item in resultado["bootstrap"]["falhas"]:
        print(f"  [FALHA] {item}")
        return 1
    return 0


def _cmd_add_mcp(args_ns):
    if args_ns.tipo == "remote":
        if not args_ns.url:
            print("[FALHA] --url e obrigatorio quando --tipo remote.")
            return 1
    elif not args_ns.comando:
        print("[FALHA] --comando e obrigatorio quando --tipo stdio (padrao).")
        return 1

    args_lista = [a.strip() for a in (args_ns.args or "").split(",") if a.strip()]
    env_lista = [e.strip() for e in (args_ns.env or "").split(",") if e.strip()]
    harnesses_lista = [h.strip() for h in (args_ns.harnesses or "claude-code").split(",") if h.strip()]
    resultado = adicionar_mcp(
        args_ns.nome, args_ns.pacote, args_ns.tipo, args_ns.comando, args_lista, env_lista, args_ns.url, harnesses_lista
    )
    if resultado["ja_existia_no_manifesto"]:
        print(f"[ATUALIZADO] '{args_ns.nome}' ja existia no manifesto, entrada sobrescrita.")
    else:
        print(f"[REGISTRADO] '{args_ns.nome}' adicionado ao manifesto.")
    for item in resultado["bootstrap"]["ja_registrados"]:
        print(f"  [JA REGISTRADO] {item}")
    for item in resultado["bootstrap"]["registrados"]:
        print(f"  [REGISTRADO] {item}")
    for item in resultado["bootstrap"]["harnesses_sem_suporte"]:
        print(f"  [SEM SUPORTE] {item}")
    return 0


def _cmd_list(args_ns):
    for linha in listar():
        print(linha)
    return 0


def _cmd_verify(args_ns):
    total, problemas = verificar()
    print(f"Dependencias declaradas: {total}")
    if problemas:
        print(f"[FALHA] {len(problemas)} pendencia(s):")
        for p in problemas:
            print(f"  - {p}")
        return 1
    print("[SUCESSO] Todas as dependencias externas declaradas estao instaladas/registradas.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="gestor_dependencias")
    sub = parser.add_subparsers(dest="acao", required=True)

    p_bootstrap = sub.add_parser("bootstrap")
    p_bootstrap.add_argument("--tipo", choices=["skills", "mcps", "todos"], default="todos")
    p_bootstrap.add_argument("--dry-run", action="store_true")
    p_bootstrap.set_defaults(func=_cmd_bootstrap)

    p_add_skill = sub.add_parser("add-skill")
    p_add_skill.add_argument("--nome", required=True)
    p_add_skill.add_argument("--pacote", required=True)
    p_add_skill.add_argument("--instalar", required=True)
    p_add_skill.add_argument("--verificar", required=True)
    p_add_skill.add_argument("--gitignore", default="")
    p_add_skill.set_defaults(func=_cmd_add_skill)

    p_add_mcp = sub.add_parser("add-mcp")
    p_add_mcp.add_argument("--nome", required=True)
    p_add_mcp.add_argument("--pacote", required=True)
    p_add_mcp.add_argument("--tipo", choices=["stdio", "remote"], default="stdio")
    p_add_mcp.add_argument("--comando", default=None)
    p_add_mcp.add_argument("--args", default="")
    p_add_mcp.add_argument("--env", default="")
    p_add_mcp.add_argument("--url", default=None)
    p_add_mcp.add_argument("--harnesses", default="claude-code")
    p_add_mcp.set_defaults(func=_cmd_add_mcp)

    p_list = sub.add_parser("list")
    p_list.set_defaults(func=_cmd_list)

    p_verify = sub.add_parser("verify")
    p_verify.set_defaults(func=_cmd_verify)

    args_ns = parser.parse_args(argv)
    return args_ns.func(args_ns)


if __name__ == "__main__":
    sys.exit(main())
