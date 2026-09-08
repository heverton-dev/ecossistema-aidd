# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_SEGREDOS
=============================================================================
Escaneia TODOS os arquivos rastreados pelo git (na raiz do ecossistema, não
só um subprojeto) em busca de credenciais hardcoded, delegando a varredura
para o detect-secrets (Yelp) — ferramenta OSS madura com dezenas de
detectores especializados (AWS, GCP, GitHub, Slack, Stripe, JWT, chaves
privadas, alta entropia Shannon/Base64/Hex, etc). Substitui o scanner de
entropia caseiro anterior (achado NIH #1 em
docs/features/oportunidades-reaproveitamento-oss-nih.md).

Achados já revisados e catalogados no baseline .secrets.baseline (raiz do
ecossistema) — fixtures de teste, placeholders de demonstração — não
reprovam o gate; um achado novo, fora do baseline, reprova.

Para atualizar o baseline depois de revisar manualmente um achado novo:
  1. python -m detect_secrets scan --baseline .secrets.baseline
  2. python -m detect_secrets audit .secrets.baseline   (marca real/falso positivo)
  3. Commitar o .secrets.baseline atualizado.

Uso:
  python gates/G_SEGREDOS.py
      exit 0 = nenhum segredo novo fora do baseline. exit 1 = achado novo
      não catalogado (ou detect-secrets não instalado).
"""

import os
import subprocess
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE_PATH = os.path.join(ROOT_DIR, ".secrets.baseline")


def _arquivos_rastreados():
    resultado = subprocess.run(
        ["git", "ls-files"], cwd=ROOT_DIR,
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    # Detecta se o baseline usa barras invertidas (gerado no Windows) ou barras normais
    usa_backslash = False
    if os.path.isfile(BASELINE_PATH):
        try:
            import json
            with open(BASELINE_PATH, "r", encoding="utf-8") as bf:
                base_data = json.load(bf)
                keys = list(base_data.get("results", {}).keys())
                if keys and "\\" in keys[0]:
                    usa_backslash = True
        except Exception:
            pass

    arquivos = []
    for raw in resultado.stdout.splitlines():
        f = raw.strip()
        if not f or f == ".secrets.baseline":
            continue
        if usa_backslash:
            f = os.path.normpath(f)
        else:
            f = f.replace("\\", "/")
        if os.path.isfile(os.path.join(ROOT_DIR, f)):
            arquivos.append(f)
    return arquivos


def escanear():
    print("=" * 70)
    print(" [GATE] G_SEGREDOS — Varredura de credenciais hardcoded (detect-secrets)")
    print("=" * 70)

    try:
        from detect_secrets import pre_commit_hook
    except ImportError:
        print("[FALHA] Pacote 'detect-secrets' não instalado.")
        print("Instale com: pip install detect-secrets")
        return 1

    tem_baseline = os.path.exists(BASELINE_PATH)
    if tem_baseline:
        print(f"[OK] Baseline carregado de {os.path.relpath(BASELINE_PATH, ROOT_DIR)}")
        argv = ["--baseline", BASELINE_PATH]
    else:
        print("[AVISO] Nenhum .secrets.baseline encontrado — tolerância zero "
              "(qualquer achado é tratado como novo).")
        argv = []
    argv += _arquivos_rastreados()

    cwd_original = os.getcwd()
    os.chdir(ROOT_DIR)
    try:
        codigo = pre_commit_hook.main(argv)
    finally:
        os.chdir(cwd_original)

    print("\n" + "=" * 70)
    if codigo not in (0, 3):
        print(" [FALHA] Quality Gate REPROVADO — achado(s) de credencial fora do baseline.")
        print(
            "\nSe for um falso positivo real, revise e adicione ao baseline com "
            "`python -m detect_secrets scan --baseline .secrets.baseline`, audite "
            "com `python -m detect_secrets audit .secrets.baseline` e comite o "
            "baseline atualizado. Se for um segredo de verdade, remova-o do "
            "arquivo e rotacione a credencial imediatamente."
        )
        print("=" * 70)
        return 1

    if codigo == 3:
        print(" [ATENÇÃO] .secrets.baseline foi atualizado automaticamente "
              "(números de linha desatualizados). Rode `git add .secrets.baseline`.")

    print(" [SUCESSO] Quality Gate G_SEGREDOS APROVADO (100% OK)!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(escanear())
