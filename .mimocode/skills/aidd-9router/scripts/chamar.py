#!/usr/bin/env python3
"""Chama o 9Router com a calibração da casa e imprime só a resposta + uso real.

Uso:
  python scripts/chamar.py "<prompt>" [--modelo code-fast] [--max 2048] [--longo]

- Sempre "stream": false.
- Sem --longo manda X-9Router-Token-Saver: off (corta o prompt extra do Caveman).
- finish_reason "length" -> repete UMA vez com o dobro de max_tokens.
- O 9Router soma +2000 fixos em prompt_tokens no relatório; aqui é descontado.
Saída: 0 ok, 1 erro, 2 resposta ainda cortada depois da repetição.
"""
import argparse
import sys

from _comum import INFLACAO_9ROUTER, chat

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--modelo", default="code-fast")
    ap.add_argument("--max", type=int, default=2048)
    ap.add_argument("--longo", action="store_true", help="resposta longa: mantém o Caveman ligado")
    a = ap.parse_args()

    status, d = chat(a.modelo, a.prompt, a.max, economizador=a.longo, timeout=300)
    if status == 200 and d["choices"][0].get("finish_reason") == "length":
        status, d = chat(a.modelo, a.prompt, a.max * 2, economizador=a.longo, timeout=300)
    if status != 200 or not isinstance(d, dict) or "error" in d:
        print(f"ERRO {status}: {str(d)[:300]}", file=sys.stderr)
        return 1
    ch = d["choices"][0]
    u = d.get("usage") or {}
    print(ch["message"].get("content") or "")
    print(f"\n[9router] modelo={d.get('model')} fim={ch.get('finish_reason')} "
          f"in_real={max((u.get('prompt_tokens') or 0) - INFLACAO_9ROUTER, 0)} "
          f"out={u.get('completion_tokens')}", file=sys.stderr)
    return 2 if ch.get("finish_reason") == "length" else 0


if __name__ == "__main__":
    sys.exit(main())
