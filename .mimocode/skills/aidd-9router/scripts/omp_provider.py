#!/usr/bin/env python3
"""Garante o provedor aidd9r no ~/.omp/agent/models.yml e confere se o omp o carrega.

Uso:
  python scripts/omp_provider.py [--dry-run]

- Faz backup (models.yml.bak-9router-<data>) antes de escrever.
- A chave nunca vai para o arquivo: `apiKey: NINEROUTER_KEY` é o NOME da variável.
- Um provedor inválido no arquivo desliga TODOS os provedores personalizados do omp;
  o erro de validação é mostrado para corrigir à mão (ex.: ollama sem `auth: none` e `api`).
Saída: 0 provedor carregado, 1 omp recusou o arquivo ou não está instalado.
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from _comum import PROVEDOR, gateway, ler_env, mapa_combos

ARQUIVO = Path.home() / ".omp" / "agent" / "models.yml"


def bloco(url, combos):
    linhas = [f"  # 9Router (skill aidd-9router): combos de código; chave vem da variável NINEROUTER_KEY.",
              f"  {PROVEDOR}:", f"    baseUrl: {url}/v1", "    api: openai-completions",
              "    apiKey: NINEROUTER_KEY", "    models:"]
    for combo in dict.fromkeys(combos):
        linhas += [f"      - id: {combo}", f"        name: 9Router {combo}",
                   "        contextWindow: 200000", "        maxTokens: 32000"]
    return "\n".join(linhas) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not shutil.which("omp"):
        print("ERRO: omp não instalado", file=sys.stderr)
        return 1
    texto = ARQUIVO.read_text(encoding="utf-8") if ARQUIVO.is_file() else "providers:\n"
    if f"\n  {PROVEDOR}:" in texto:
        print(f"provedor {PROVEDOR} já existe em {ARQUIVO}")
    else:
        novo = texto.rstrip("\n") + "\n" + bloco(gateway(), mapa_combos().values())
        print(f"{'[DRY-RUN] ' if a.dry_run else ''}acrescentando {PROVEDOR} em {ARQUIVO}")
        if a.dry_run:
            return 0
        if ARQUIVO.is_file():
            shutil.copy2(ARQUIVO, ARQUIVO.with_name(f"models.yml.bak-9router-{time.strftime('%Y%m%d-%H%M')}"))
        ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
        ARQUIVO.write_text(novo, encoding="utf-8")
    env = {**os.environ, "NINEROUTER_KEY": ler_env("NINEROUTER_KEY")}
    r = subprocess.run(["omp", "models", PROVEDOR], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", stdin=subprocess.DEVNULL, env=env, timeout=180, cwd=str(Path.home()))
    saida = r.stdout + r.stderr
    if "validation failed" in saida or f"No models matching" in saida:
        print("ERRO: o omp recusou o models.yml:", file=sys.stderr)
        print("\n".join(l for l in saida.splitlines() if "valid" in l.lower() or "error" in l.lower()), file=sys.stderr)
        return 1
    print(f"ok: omp carregou {PROVEDOR} ({saida.count('code-')} combos listados)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
