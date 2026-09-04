# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_SEGREDOS
=============================================================================
Escaneia TODOS os arquivos rastreados pelo git (na raiz do ecossistema, não
só um subprojeto) em busca de padrões de credenciais hardcoded. Materializa
o gate G_SEGREDOS que o plano de execução original (docs/planos/
PLANO-EXECUCAO-ECOSSISTEMA-AIDD.md) já declarava existir em gates/, mas
nunca tinha sido implementado (R6 do PLANO-CORRECAO-RISCOS-ECOSSISTEMA-AIDD.md).

Reaproveita a mesma classe de padrões de
tools/aidd-generator/scripts/gates/G_BLOQUEAR_SEGREDOS.py (git pre-commit
hook local daquele subprojeto), mas em escopo de auditoria de todo o
ecossistema via `git ls-files` em vez de só arquivos staged.

Falsos positivos conhecidos (fixtures de teste, placeholders de demo) estão
documentados em gates/allowlist_segredos.json com justificativa — nunca
silenciados sem registro.

Uso:
  python gates/G_SEGREDOS.py
      exit 0 = nenhum segredo novo encontrado. exit 1 = achado não
      catalogado no allowlist.
"""

import json
import os
import re
import subprocess
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWLIST_PATH = os.path.join(ROOT_DIR, "gates", "allowlist_segredos.json")

PADROES_SEGREDO = [
    (r'sk-[A-Za-z0-9]{20,}', 'Chave estilo OpenAI/compatível (sk-...)'),
    (r'AIzaSy[A-Za-z0-9_\-]{33}', 'Chave de API do Google (AIzaSy...)'),
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key ID (AKIA...)'),
    (r'ghp_[A-Za-z0-9]{36}', 'GitHub Personal Access Token (ghp_...)'),
    (r'xox[baprs]-[A-Za-z0-9-]{10,}', 'Token do Slack (xox...)'),
    (r'-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----', 'Chave privada PEM'),
    (
        r'(?i)(api[_-]?key|secret|token|password|senha|credencial)\s*[:=]\s*'
        r'["\'][A-Za-z0-9_\-./+=]{16,}["\']',
        'Atribuição genérica de chave/segredo em texto puro',
    ),
]


def _arquivos_rastreados():
    resultado = subprocess.run(
        ["git", "ls-files"], cwd=ROOT_DIR,
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return [f for f in resultado.stdout.splitlines() if f.strip()]


def _carregar_allowlist():
    if not os.path.exists(ALLOWLIST_PATH):
        return {}
    with open(ALLOWLIST_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("arquivos", {})


def escanear():
    print("=" * 70)
    print(" [GATE] G_SEGREDOS — Varredura de credenciais hardcoded")
    print("=" * 70)

    allowlist = _carregar_allowlist()
    achados_novos = []
    achados_conhecidos = 0

    for caminho_rel in _arquivos_rastreados():
        # O proprio allowlist cita os valores fake nas justificativas para
        # documentar cada achado com precisao — isso bate nos padroes por
        # definicao. Excluido do scan, nao do motivo de existir.
        if caminho_rel == "gates/allowlist_segredos.json":
            continue
        caminho_abs = os.path.join(ROOT_DIR, caminho_rel)
        if not os.path.isfile(caminho_abs):
            continue
        try:
            with open(caminho_abs, "r", encoding="utf-8", errors="ignore") as f:
                conteudo = f.read()
        except Exception:
            continue

        for padrao, nome in PADROES_SEGREDO:
            m = re.search(padrao, conteudo)
            if not m:
                continue
            if caminho_rel in allowlist:
                achados_conhecidos += 1
            else:
                achados_novos.append((caminho_rel, nome, m.group(0)[:40]))
            break  # 1 achado por arquivo já basta para classificar

    print(f"[OK] {achados_conhecidos} achado(s) já catalogado(s) em allowlist_segredos.json (fixtures/placeholders auditados).")

    print("\n" + "=" * 70)
    if achados_novos:
        print(f" [FALHA] Quality Gate REPROVADO com {len(achados_novos)} achado(s) não catalogado(s):")
        for caminho_rel, nome, trecho in achados_novos:
            print(f"  - {caminho_rel}: {nome} ({trecho}...)")
        print("\nSe for um falso positivo real, adicione o arquivo a "
              "gates/allowlist_segredos.json com justificativa. Se for um "
              "segredo de verdade, remova-o do arquivo e rotacione a "
              "credencial imediatamente.")
        print("=" * 70)
        return 1

    print(" [SUCESSO] Quality Gate G_SEGREDOS APROVADO (100% OK)!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(escanear())
