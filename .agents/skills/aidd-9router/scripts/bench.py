#!/usr/bin/env python3
"""Mede modelos/combos do 9Router com tarefa de código conferida por testes reais.

Uso:
  python scripts/bench.py codigo  <modelo> [<modelo>...] [--saida bench.json]
  python scripts/bench.py harness <modelo> [<modelo>...]

codigo : pede a função calc() (parser de expressões, sem eval) e roda 21 testes no código devolvido.
harness: abre o Claude Code roteado (claude -p) e pede para ler AGENTS.md com a ferramenta Read;
         passa se responder o primeiro título. Prova contexto grande + chamada de ferramenta.
Use a lista de modelos de GET /v1/models (ids) ou nomes de combo.
Saída: 0 sempre (é medição); o resultado vai na tela e em --saida.
"""
import argparse
import concurrent.futures as cf
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from _comum import INFLACAO_9ROUTER, achar_env, chat, gateway, ler_env, mapa_combos

TAREFA = (
    "Write a Python function `calc(expr: str) -> float` that evaluates arithmetic expressions WITHOUT using "
    "eval/exec/ast/compile or any parsing library. Support: numbers (ints and decimals like 2.5), + - * /, "
    "^ for power (right-associative, binds tighter than unary minus, so -2^2 == -4 and 2^3^2 == 512), "
    "unary minus (e.g. 2*-3 == -6, --2 == 2), parentheses, arbitrary whitespace. Division by zero must raise "
    "ZeroDivisionError. Any malformed input (empty, unbalanced parens, dangling operator, unknown char, "
    "two numbers in a row like '1 2') must raise ValueError. "
    "Reply with only the code in one ```python block, no explanation."
)
TESTES = [
    ("2+3*4", 14), ("(2+3)*4", 20), ("-3+5", 2), ("2*-3", -6), ("10/4", 2.5), ("2^3^2", 512),
    ("-2^2", -4), (" 1 +  2 ", 3), ("--2", 2), ("2.5*2", 5), ("((1))", 1), ("8/2/2", 2), ("2-3-4", -5),
    ("", ValueError), ("2+", ValueError), ("(1", ValueError), ("1)", ValueError), ("a", ValueError),
    ("1 2", ValueError), ("*3", ValueError), ("1/0", ZeroDivisionError),
]
PROIBIDO = re.compile(r"(?<![.\w])(eval|exec|compile)\s*\(|import ast")


def avaliar(codigo):
    if PROIBIDO.search(codigo):
        return 0, "usou eval/ast"
    ns = {}
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            exec(codigo, ns)
            f = ns["calc"]
        except Exception as e:
            return 0, f"falhou ao carregar: {type(e).__name__}"
        acertos = 0
        for entrada, esperado in TESTES:
            try:
                r = f(entrada)
                acertos += isinstance(esperado, (int, float)) and abs(r - esperado) < 1e-9
            except Exception as e:
                acertos += isinstance(esperado, type) and type(e) is esperado
    return acertos, ""


def medir_codigo(modelo):
    t0 = time.time()
    status, d = chat(modelo, TAREFA, 8000, timeout=300)
    res = {"modelo": modelo, "seg": round(time.time() - t0, 1)}
    if status != 200 or not isinstance(d, dict) or "choices" not in d:
        return {**res, "erro": f"HTTP {status} {str(d)[:120]}"}
    ch, u = d["choices"][0], d.get("usage") or {}
    txt = ch["message"].get("content") or ""
    m = re.search(r"```(?:python)?\s*\n(.*?)```", txt, re.S)
    acertos, obs = avaliar(m.group(1) if m else txt)
    return {**res, "acertos": f"{acertos}/{len(TESTES)}", "fim": ch.get("finish_reason"),
            "in_real": max((u.get("prompt_tokens") or 0) - INFLACAO_9ROUTER, 0), "out": u.get("completion_tokens"),
            **({"obs": obs} if obs else {})}


def medir_harness(modelo):
    env_arquivo = achar_env()
    raiz = env_arquivo.parent if env_arquivo else Path.cwd()
    agents = raiz / "AGENTS.md"
    esperado = next((l.strip() for l in agents.read_text(encoding="utf-8").splitlines() if l.startswith("# ")), "")
    combos = mapa_combos()
    env = {**os.environ, "ANTHROPIC_BASE_URL": gateway(), "ANTHROPIC_AUTH_TOKEN": ler_env("NINEROUTER_KEY"),
           "ANTHROPIC_API_KEY": "", "ANTHROPIC_DEFAULT_OPUS_MODEL": combos["opus"],
           "ANTHROPIC_DEFAULT_SONNET_MODEL": combos["sonnet"], "ANTHROPIC_DEFAULT_HAIKU_MODEL": combos["haiku"]}
    t0 = time.time()
    r = subprocess.run([shutil.which("claude"), "-p", "Use the Read tool to read AGENTS.md, then answer with only its "
                        "first markdown heading line.", "--model", modelo, "--output-format", "json", "--max-turns", "4"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, cwd=str(raiz),
                       stdin=subprocess.DEVNULL, timeout=600)
    res = {"modelo": modelo, "seg": round(time.time() - t0, 1)}
    try:
        d = json.loads(r.stdout)
    except Exception:
        return {**res, "erro": (r.stderr or r.stdout)[-150:]}
    texto = str(d.get("result") or "").strip().strip("`").strip()
    return {**res, "passou": (not d.get("is_error")) and texto == esperado,
            "usou": list((d.get("modelUsage") or {}).keys()), **({"erro": texto[:120]} if d.get("is_error") else {})}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["codigo", "harness"])
    ap.add_argument("modelos", nargs="+")
    ap.add_argument("--saida")
    a = ap.parse_args()
    fn = medir_codigo if a.modo == "codigo" else medir_harness
    with cf.ThreadPoolExecutor(4) as ex:
        resultados = list(ex.map(fn, a.modelos))
    for r in resultados:
        print(json.dumps(r, ensure_ascii=False))
    if a.saida:
        Path(a.saida).write_text(json.dumps(resultados, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
