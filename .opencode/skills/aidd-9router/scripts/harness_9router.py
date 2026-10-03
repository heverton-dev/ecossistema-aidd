#!/usr/bin/env python3
"""Abre um harness roteado pelos combos do 9Router, com liga/desliga global.

Uso:
  python scripts/harness_9router.py <claude|opencode|mimo|omp> [argumentos do harness...]
  python scripts/harness_9router.py --ligar | --desligar | --estado
  python scripts/harness_9router.py <harness> --mapa

Desligado (marcador ~/.aidd/9router-desligado) = abre o harness puro, argumentos intactos.
Nada é gravado na configuração do harness; o roteamento vale só para o processo aberto aqui.
Exceção: o omp precisa do provedor `aidd9r` no ~/.omp/agent/models.yml (ver SKILL.md).

Roteamento por nível (troca por nível: NINEROUTER_OPUS / NINEROUTER_SONNET / NINEROUTER_HAIKU):
  opus   -> code-pro   (planejar, arquitetar, revisar)
  sonnet -> code-fast  (implementar, padrão)
  haiku  -> code-free  (buscar, ler, resumir, tarefas leves)
"""
import json
import os
import shutil
import subprocess
import sys

from _comum import MARCADOR_DESLIGADO, PROVEDOR, gateway, ler_env, mapa_combos

HARNESSES = ("claude", "opencode", "mimo", "omp")


def sem_flags(args, flags):
    """Remove flags de modelo nas formas `--flag valor` e `--flag=valor`."""
    saida, pular = [], False
    for a in args:
        if pular:
            pular = False
            continue
        if a in flags:
            pular = True
            continue
        if any(a.startswith(f + "=") for f in flags):
            continue
        saida.append(a)
    return saida


def config_opencode(url, mapa):
    modelos = {combo: {"name": combo, "limit": {"context": 200000, "output": 32000}} for combo in mapa.values()}
    return json.dumps({
        "provider": {PROVEDOR: {
            "name": "9Router (aidd)",
            "npm": "@ai-sdk/openai-compatible",
            "options": {"baseURL": f"{url}/v1", "apiKey": "{env:NINEROUTER_KEY}"},
            "models": modelos,
        }},
        "small_model": f"{PROVEDOR}/{mapa['haiku']}",
    })


def montar(harness, args, url, chave, mapa):
    """Devolve (argumentos, variáveis extras) do harness ligado ao 9Router."""
    if harness == "claude":
        return args, {
            "ANTHROPIC_BASE_URL": url,
            "ANTHROPIC_AUTH_TOKEN": chave,
            "ANTHROPIC_API_KEY": "",
            "ANTHROPIC_DEFAULT_OPUS_MODEL": mapa["opus"],
            "ANTHROPIC_DEFAULT_SONNET_MODEL": mapa["sonnet"],
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": mapa["haiku"],
        }
    if harness in ("opencode", "mimo"):
        variavel = "OPENCODE_CONFIG_CONTENT" if harness == "opencode" else "MIMOCODE_CONFIG_CONTENT"
        novos = sem_flags(args, ("-m", "--model")) + ["-m", f"{PROVEDOR}/{mapa['sonnet']}"]
        return novos, {"NINEROUTER_KEY": chave, variavel: config_opencode(url, mapa)}
    novos = sem_flags(args, ("--model", "--smol", "--plan", "--slow")) + [
        "--model", f"{PROVEDOR}/{mapa['sonnet']}", "--smol", f"{PROVEDOR}/{mapa['haiku']}",
        "--plan", f"{PROVEDOR}/{mapa['opus']}", "--slow", f"{PROVEDOR}/{mapa['opus']}"]
    return novos, {"NINEROUTER_KEY": chave}


def main():
    args = sys.argv[1:]
    if len(args) == 2 and args[0] in HARNESSES and args[1] in ("--ligar", "--desligar", "--estado"):
        args = args[1:]
    if args[:1] == ["--desligar"]:
        MARCADOR_DESLIGADO.parent.mkdir(parents=True, exist_ok=True)
        MARCADOR_DESLIGADO.touch()
        print("9Router DESLIGADO: os próximos agentes abrem puros.")
        return 0
    if args[:1] == ["--ligar"]:
        MARCADOR_DESLIGADO.unlink(missing_ok=True)
        print("9Router LIGADO: os próximos agentes passam pelos combos.")
        return 0
    desligado = MARCADOR_DESLIGADO.exists()
    if args[:1] == ["--estado"]:
        print("9Router", "DESLIGADO" if desligado else "LIGADO")
        return 0
    if not args or args[0] not in HARNESSES:
        print(f"Uso: harness_9router.py <{'|'.join(HARNESSES)}> [argumentos...]", file=sys.stderr)
        return 2
    harness, args = args[0], args[1:]

    url = gateway()
    chave = ler_env("NINEROUTER_KEY")
    mapa = mapa_combos()
    if "--mapa" in args:
        for nivel, combo in mapa.items():
            print(f"{nivel:<7}-> {combo}")
        print(f"gateway: {url}", f"(DESLIGADO: {harness} puro)" if desligado else "")
        return 0
    binario = shutil.which(harness)
    if not binario:
        print(f"ERRO: comando {harness} não encontrado no PATH", file=sys.stderr)
        return 1
    if desligado:
        return subprocess.call([binario, *args])
    if not chave:
        print("ERRO: NINEROUTER_KEY vazia no .env", file=sys.stderr)
        return 1
    novos, extras = montar(harness, args, url, chave, mapa)
    return subprocess.call([binario, *novos], env={**os.environ, **extras})


if __name__ == "__main__":
    sys.exit(main())
