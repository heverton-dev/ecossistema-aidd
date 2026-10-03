#!/usr/bin/env python3
"""Diagnóstico de ponta a ponta do 9Router da casa. Só lê; nunca muda nada.

Uso:
  python scripts/doctor.py [--rapido]

Confere: gateway no ar, chave obrigatória (401 sem chave), cada combo respondendo,
atalhos <harness>-9router no PATH, estado do liga/desliga, provedor aidd9r no omp
e os Commands dos agentes no Orca. --rapido pula as chamadas de chat.
Saída: 0 tudo ok, 1 algo crítico falhou (gateway, chave ou combo).
"""
import argparse
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

from _comum import INFLACAO_9ROUTER, MARCADOR_DESLIGADO, PROVEDOR, chat, gateway, ler_env, mapa_combos, orca_rpc

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def linha(ok, texto, critico=True):
    marca = "ok  " if ok else ("FALHA" if critico else "aviso")
    print(f"[{marca}] {texto}")
    return ok or not critico


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true")
    a = ap.parse_args()
    url, chave, combos = gateway(), ler_env("NINEROUTER_KEY"), mapa_combos()
    tudo = True

    try:
        with urllib.request.urlopen(f"{url}/api/health", timeout=15) as r:
            vivo = json.loads(r.read()).get("ok") is True
    except Exception:
        vivo = False
    tudo &= linha(vivo, f"gateway {url}/api/health")
    tudo &= linha(bool(chave), "NINEROUTER_KEY preenchida no .env")
    if vivo and not a.rapido:
        status, _ = chat(combos["sonnet"], "oi", 5, chave="")
        tudo &= linha(status == 401, f"chat sem chave recusado (HTTP {status}, esperado 401)")
        for nivel, combo in combos.items():
            status, d = chat(combo, "Responda apenas: ok", 300)
            ok = status == 200 and isinstance(d, dict) and "choices" in d
            extra = ""
            if ok:
                u = d.get("usage") or {}
                extra = f"-> {d.get('model')}, in_real={max((u.get('prompt_tokens') or 0) - INFLACAO_9ROUTER, 0)}"
            tudo &= linha(ok, f"{nivel:<6} {combo:<10} HTTP {status} {extra}")

    for h in ("claude", "opencode", "mimo", "omp"):
        tem_harness = shutil.which(h) is not None
        linha(not tem_harness or shutil.which(f"{h}-9router") is not None,
              f"atalho {h}-9router no PATH" + ("" if tem_harness else f" ({h} não instalado)"), critico=False)
    linha(True, f"roteamento {'DESLIGADO' if MARCADOR_DESLIGADO.exists() else 'LIGADO'} (marcador {MARCADOR_DESLIGADO})", critico=False)

    if shutil.which("omp"):
        modelos = Path.home() / ".omp" / "agent" / "models.yml"
        tem = modelos.is_file() and f"\n  {PROVEDOR}:" in modelos.read_text(encoding="utf-8")
        valido = True
        if tem:
            r = subprocess.run(["omp", "models", PROVEDOR], capture_output=True, text=True, encoding="utf-8", errors="replace",
                               stdin=subprocess.DEVNULL, timeout=180, cwd=str(Path.home()))
            valido = "validation failed" not in r.stdout + r.stderr
        linha(tem and valido, f"omp: provedor {PROVEDOR} {'carregado' if tem and valido else 'ausente ou models.yml inválido'}"
              " (scripts/omp_provider.py)", critico=False)

    try:
        s = orca_rpc("settings.get")["result"]["settings"]
        ov = s.get("agentCmdOverrides") or {}
        for agente, esperado in (("claude", "claude-9router"), ("opencode", "opencode-9router"),
                                 ("mimo-code", "mimo-9router"), ("omp", "omp-9router")):
            linha(ov.get(agente) == esperado, f"Orca Command {agente} = {ov.get(agente) or '(padrão)'}", critico=False)
        env_url = ((s.get("agentDefaultEnv") or {}).get("claude") or {}).get("NINEROUTER_URL")
        linha(env_url == url, f"Orca Environment do Claude aponta para {env_url}", critico=False)
    except Exception:
        linha(False, "Orca não respondeu (rodando fora do Orca?)", critico=False)

    print("RESULTADO:", "ok" if tudo else "FALHA crítica")
    return 0 if tudo else 1


if __name__ == "__main__":
    sys.exit(main())
