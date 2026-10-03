#!/usr/bin/env python3
"""Abre o Claude Code roteado pelos combos do 9Router (liga/desliga por sessão).

Uso:
  python scripts/claude_9router.py [argumentos do claude...]
  python scripts/claude_9router.py --mapa      # só mostra o roteamento e sai
  python scripts/claude_9router.py --desligar  # próximas aberturas viram Claude puro
  python scripts/claude_9router.py --ligar     # volta a rotear pelos combos
  python scripts/claude_9router.py --estado

Desligado (marcador ~/.aidd/9router-desligado) = abre `claude` puro, sem tocar no ambiente.
Nada é gravado em settings.json: o roteamento vale só para o processo aberto aqui.

Roteamento (opus/sonnet/haiku do Claude Code -> combo do 9Router):
  opus   -> code-pro   (planejar, arquitetar, revisar)
  sonnet -> code-fast  (implementar, padrão)
  haiku  -> code-free  (buscar, ler, resumir, subagentes leves)
Troca de combo por nível: NINEROUTER_OPUS / NINEROUTER_SONNET / NINEROUTER_HAIKU no .env.
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PADRAO = {"opus": "code-pro", "sonnet": "code-fast", "haiku": "code-free"}
MARCADOR_DESLIGADO = Path.home() / ".aidd" / "9router-desligado"


def ler_env(nome):
    if os.environ.get(nome):
        return os.environ[nome]
    for pasta in [Path.cwd(), *Path(__file__).resolve().parents]:
        env = pasta / ".env"
        if env.is_file():
            m = re.search(rf'^{nome}=["\']?([^"\'\r\n]*)', env.read_text(encoding="utf-8"), re.M)
            if m:
                return m.group(1).strip()
    return ""


def main():
    args = sys.argv[1:]
    if args[:1] == ["--desligar"]:
        MARCADOR_DESLIGADO.parent.mkdir(parents=True, exist_ok=True)
        MARCADOR_DESLIGADO.touch()
        print("9Router DESLIGADO: os próximos Claude abrem puros (assinatura Anthropic).")
        return 0
    if args[:1] == ["--ligar"]:
        MARCADOR_DESLIGADO.unlink(missing_ok=True)
        print("9Router LIGADO: os próximos Claude passam pelos combos.")
        return 0
    desligado = MARCADOR_DESLIGADO.exists()
    if args[:1] == ["--estado"]:
        print("9Router", "DESLIGADO" if desligado else "LIGADO")
        return 0

    url = (ler_env("NINEROUTER_URL") or "http://localhost:20128").rstrip("/")
    chave = ler_env("NINEROUTER_KEY")
    mapa = {nivel: ler_env(f"NINEROUTER_{nivel.upper()}") or combo for nivel, combo in PADRAO.items()}
    if "--mapa" in args:
        for nivel, combo in mapa.items():
            print(f"{nivel:<7}-> {combo}")
        print(f"gateway: {url}", "(DESLIGADO: Claude puro)" if desligado else "")
        return 0
    claude = shutil.which("claude")
    if not claude:
        print("ERRO: comando claude não encontrado no PATH", file=sys.stderr)
        return 1
    if desligado:
        return subprocess.call([claude, *args])
    if not chave:
        print("ERRO: NINEROUTER_KEY vazia no .env", file=sys.stderr)
        return 1
    env = dict(os.environ)
    env.update({
        "ANTHROPIC_BASE_URL": url,
        "ANTHROPIC_AUTH_TOKEN": chave,
        "ANTHROPIC_API_KEY": "",
        "ANTHROPIC_DEFAULT_OPUS_MODEL": mapa["opus"],
        "ANTHROPIC_DEFAULT_SONNET_MODEL": mapa["sonnet"],
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": mapa["haiku"],
    })
    return subprocess.call([claude, *args], env=env)


if __name__ == "__main__":
    sys.exit(main())
