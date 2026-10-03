#!/usr/bin/env python3
"""Chama o 9Router com a calibração da casa e imprime só a resposta + uso real.

Uso:
  python scripts/chamar.py "<prompt>" [--modelo code-fast] [--max 2048] [--longo] [--sistema "<txt>"]

- Lê NINEROUTER_URL e NINEROUTER_KEY do ambiente ou do .env da raiz do repo.
- Sempre "stream": false.
- Sem --longo manda X-9Router-Token-Saver: off (corta ~385 tokens reais do Caveman).
- finish_reason "length" -> repete UMA vez com o dobro de max_tokens.
- O 9Router soma +2000 fixos em prompt_tokens no relatório; aqui é descontado.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

INFLACAO_9ROUTER = 2000


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


def chamar(url, chave, corpo, longo):
    cab = {"Content-Type": "application/json"}
    if chave:
        cab["Authorization"] = f"Bearer {chave}"
    if not longo:
        cab["X-9Router-Token-Saver"] = "off"
    req = urllib.request.Request(f"{url}/v1/chat/completions", json.dumps(corpo).encode(), cab)
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--modelo", default="code-fast")
    ap.add_argument("--max", type=int, default=2048)
    ap.add_argument("--longo", action="store_true", help="resposta longa: mantém o Caveman ligado")
    ap.add_argument("--sistema", default="")
    a = ap.parse_args()

    url = (ler_env("NINEROUTER_URL") or "http://localhost:20128").rstrip("/")
    chave = ler_env("NINEROUTER_KEY")
    msgs = ([{"role": "system", "content": a.sistema}] if a.sistema else []) + [
        {"role": "user", "content": a.prompt}]
    corpo = {"model": a.modelo, "stream": False, "max_tokens": a.max, "messages": msgs}
    try:
        d = chamar(url, chave, corpo, a.longo)
        if d["choices"][0].get("finish_reason") == "length":
            corpo["max_tokens"] = a.max * 2
            d = chamar(url, chave, corpo, a.longo)
    except urllib.error.HTTPError as e:
        print(f"ERRO HTTP {e.code}: {e.read()[:300]!r}", file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"ERRO de conexão com {url}: {e}", file=sys.stderr)
        return 1
    if "error" in d:
        print(f"ERRO: {d['error']}", file=sys.stderr)
        return 1
    ch = d["choices"][0]
    u = d.get("usage") or {}
    print(ch["message"].get("content") or "")
    print(f"\n[9router] modelo={d.get('model')} fim={ch.get('finish_reason')} "
          f"in_real={max((u.get('prompt_tokens') or 0) - INFLACAO_9ROUTER, 0)} "
          f"out={u.get('completion_tokens')}", file=sys.stderr)
    return 0 if ch.get("finish_reason") != "length" else 2


if __name__ == "__main__":
    sys.exit(main())
