#!/usr/bin/env python3
"""Configura o Orca ADE para os harnesses usarem os combos do 9Router.

Uso:
  python scripts/orca_9router.py --estado            # só lê e mostra
  python scripts/orca_9router.py --aplicar [--dry-run]

--aplicar (pela chamada interna settings.update do runtime do Orca):
  - Environment do Claude: NINEROUTER_URL/KEY/OPUS/SONNET/HAIKU (nunca ANTHROPIC_AUTH_TOKEN:
    as contas Claude gerenciadas do Orca recusam esse lançamento);
  - Arguments do Claude: troca `--model opus` por `--model sonnet` (padrão vai para code-fast);
  - Quick Commands globais: 9Router ON / OFF / ESTADO.
O Command de cada agente (claude-9router, opencode-9router, mimo-9router, omp-9router) só muda
pela tela Settings > Agents > Command; o script lista o que falta.
Saída: 0 tudo certo, 1 Orca não está rodando, 2 falta ajuste manual de Command.
"""
import argparse
import sys

from _comum import gateway, ler_env, mapa_combos, orca_rpc

AGENTES = {"claude": "claude-9router", "opencode": "opencode-9router", "mimo-code": "mimo-9router", "omp": "omp-9router"}
QUICK = [("qc-9router-on", "9Router ON", "claude-9router --ligar"),
         ("qc-9router-off", "9Router OFF", "claude-9router --desligar"),
         ("qc-9router-estado", "9Router ESTADO", "claude-9router --estado")]


def ler_settings():
    r = orca_rpc("settings.get")
    if not r.get("ok"):
        raise RuntimeError(r.get("error"))
    return r["result"]["settings"]


def mostrar(s):
    ov = s.get("agentCmdOverrides") or {}
    faltando = []
    for agente, esperado in AGENTES.items():
        atual = ov.get(agente) or "(padrão)"
        ok = atual == esperado
        faltando += [] if ok else [agente]
        print(f"  {agente:<10} Command: {atual:<18} {'ok' if ok else 'AJUSTAR para ' + esperado}")
    env = (s.get("agentDefaultEnv") or {}).get("claude", {})
    print(f"  claude env: URL={env.get('NINEROUTER_URL', '-')} chave={'preenchida' if env.get('NINEROUTER_KEY') else 'VAZIA'}")
    print(f"  claude args: {(s.get('agentDefaultArgs') or {}).get('claude')}")
    return faltando


def main():
    ap = argparse.ArgumentParser()
    modo = ap.add_mutually_exclusive_group()
    modo.add_argument("--estado", action="store_true", help="só lê e mostra (padrão)")
    modo.add_argument("--aplicar", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    try:
        s = ler_settings()
    except Exception as e:
        print(f"ERRO: Orca não respondeu ({e})", file=sys.stderr)
        return 1
    if a.aplicar:
        combos = mapa_combos()
        env = dict(s.get("agentDefaultEnv") or {})
        env["claude"] = {**{k: v for k, v in (env.get("claude") or {}).items() if not k.startswith("ANTHROPIC_")},
                         "NINEROUTER_URL": gateway(), "NINEROUTER_KEY": ler_env("NINEROUTER_KEY"),
                         "NINEROUTER_OPUS": combos["opus"], "NINEROUTER_SONNET": combos["sonnet"],
                         "NINEROUTER_HAIKU": combos["haiku"]}
        args = dict(s.get("agentDefaultArgs") or {})
        args["claude"] = (args.get("claude") or "").replace("--model opus", "--model sonnet")
        print(f"{'[DRY-RUN] ' if a.dry_run else ''}Environment e Arguments do Claude + {len(QUICK)} Quick Commands")
        if not a.dry_run:
            r = orca_rpc("settings.update", {"agentDefaultEnv": env, "agentDefaultArgs": args})
            if not r.get("ok"):
                print(f"ERRO settings.update: {r.get('error')}", file=sys.stderr)
                return 1
            for qid, rotulo, comando in QUICK:
                orca_rpc("settings.updateTerminalQuickCommands", {"mutation": {"type": "upsert", "command": {
                    "id": qid, "label": rotulo, "action": "terminal-command", "command": comando,
                    "appendEnter": True, "scope": {"type": "global"}}}})
            s = ler_settings()
    faltando = mostrar(s)
    if faltando:
        print("Ajuste manual: Settings > Agents > <agente> > Command (campo não aceito pela chamada interna).")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
