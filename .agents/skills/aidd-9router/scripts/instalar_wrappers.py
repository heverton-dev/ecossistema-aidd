#!/usr/bin/env python3
"""Cria os atalhos <harness>-9router (bash e .cmd) que chamam o harness_9router.py.

Uso:
  python scripts/instalar_wrappers.py [--pasta ~/.local/bin] [--dry-run]

A pasta precisa estar no PATH do terminal do Orca (Git Bash) e do Windows.
Saída: 0 ok, 1 pasta fora do PATH ou erro de escrita.
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

HARNESSES = ("claude", "opencode", "mimo", "omp")
LAUNCHER = Path(__file__).resolve().parent / "harness_9router.py"


def conteudos(harness):
    bash = (f"#!/usr/bin/env bash\n# {harness} roteado pelos combos do 9Router (skill aidd-9router)."
            f" Liga/desliga: Quick Commands 9Router ON/OFF.\n"
            f'exec python "{LAUNCHER.as_posix()}" {harness} "$@"\n')
    cmd = (f"@echo off\r\nrem {harness} roteado pelos combos do 9Router (skill aidd-9router).\r\n"
           f'python "{LAUNCHER}" {harness} %*\r\n')
    return bash, cmd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta", default=str(Path.home() / ".local" / "bin"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    pasta = Path(os.path.expanduser(a.pasta))
    no_path = any(Path(p).resolve() == pasta.resolve() for p in os.environ.get("PATH", "").split(os.pathsep) if p)
    for h in HARNESSES:
        bash, cmd = conteudos(h)
        if not shutil.which(h):
            print(f"[AVISO] {h} não está instalado; o atalho fica pronto para quando estiver.")
        for nome, texto in ((f"{h}-9router", bash), (f"{h}-9router.cmd", cmd)):
            print(f"{'[DRY-RUN] ' if a.dry_run else ''}{pasta / nome}")
            if not a.dry_run:
                pasta.mkdir(parents=True, exist_ok=True)
                (pasta / nome).write_bytes(texto.encode("utf-8"))
                os.chmod(pasta / nome, 0o755)
    if not no_path:
        print(f"[ERRO] {pasta} não está no PATH; o Orca não vai achar os atalhos.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
