#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GATE: G_BLOQUEAR_SEGREDOS — Bloqueio mecânico de segredos hardcoded.

Escaneia arquivos staged (git diff --cached) por padrões de chave de
API/token/segredo em texto puro. Feito para rodar como git pre-commit
hook — BLOQUEIA o commit (exit 1) se encontrar qualquer match.

Achado real que motivou este gate (2026-08-30): um agente (harness
externo rodando o teste comparativo multi-harness) commitou um arquivo
com uma chave de API real hardcoded (run_antigravity.py, chave OpenCode
Zen). Nunca chegou a entrar no histórico porque foi pego manualmente
antes do commit — mas não havia nenhuma barreira MECÂNICA impedindo,
só sorte/atenção. Este gate existe para que isso nunca dependa de
atenção humana de novo.

Uso:
    python scripts/gates/G_BLOQUEAR_SEGREDOS.py             # escaneia staged
    python scripts/gates/G_BLOQUEAR_SEGREDOS.py --arquivo X # escaneia 1 arquivo
"""

import sys
import re
import subprocess
import argparse

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# Padrões de segredo conhecidos + um catch-all genérico para
# ATRIBUICAO_CHAVE = "valor longo". Falsos positivos são aceitáveis aqui
# (o custo de bloquear um commit legítimo é muito menor que o de vazar
# uma chave real) — em caso de falso positivo, o commit pode ser refeito
# após remover o segredo do arquivo, nunca com --no-verify.
PADROES_SEGREDO = [
    (r'sk-[A-Za-z0-9]{20,}', 'Chave estilo OpenAI/compatível (sk-...)'),
    (r'AIzaSy[A-Za-z0-9_\-]{33}', 'Chave de API do Google (AIzaSy...)'),
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key ID (AKIA...)'),
    (r'ghp_[A-Za-z0-9]{36}', 'GitHub Personal Access Token (ghp_...)'),
    (r'xox[baprs]-[A-Za-z0-9-]{10,}', 'Token do Slack (xox...)'),
    (
        r'(?i)(api[_-]?key|secret|token|password|senha|credencial)\s*[:=]\s*'
        r'["\'][A-Za-z0-9_\-./+=]{16,}["\']',
        'Atribuição genérica de chave/segredo em texto puro',
    ),
]


def arquivos_staged():
    """Lista arquivos staged para commit (git diff --cached --name-only)."""
    resultado = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    return [f for f in resultado.stdout.splitlines() if f.strip()]


def conteudo_staged(arquivo):
    """Conteúdo staged de um arquivo (não o que está em disco, o que
    será de fato commitado — importante se houver diff entre os dois)."""
    resultado = subprocess.run(
        ['git', 'show', f':{arquivo}'],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    return resultado.stdout if resultado.returncode == 0 else ''


def escanear_conteudo(conteudo, origem):
    achados = []
    for padrao, descricao in PADROES_SEGREDO:
        for m in re.finditer(padrao, conteudo):
            trecho = m.group(0)
            mascarado = trecho[:8] + '...' + trecho[-4:] if len(trecho) > 16 else '***'
            linha = conteudo[:m.start()].count('\n') + 1
            achados.append(f"  {origem}:{linha} — {descricao} — {mascarado}")
    return achados


def main():
    parser = argparse.ArgumentParser(description='Bloqueia segredos hardcoded antes do commit')
    parser.add_argument('--arquivo', help='Escanear um arquivo específico em vez do staged')
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("GATE: G_BLOQUEAR_SEGREDOS")
    print("=" * 70 + "\n")

    todos_achados = []

    if args.arquivo:
        try:
            with open(args.arquivo, 'r', encoding='utf-8', errors='replace') as f:
                conteudo = f.read()
            todos_achados.extend(escanear_conteudo(conteudo, args.arquivo))
        except OSError as e:
            print(f"❌ Não foi possível ler {args.arquivo}: {e}")
            print("   Falha ao escanear NÃO é o mesmo que 'sem segredos' — bloqueando por segurança.")
            return 1
    else:
        arquivos = arquivos_staged()
        print(f"🔍 Escaneando {len(arquivos)} arquivo(s) staged...\n")
        for arquivo in arquivos:
            conteudo = conteudo_staged(arquivo)
            todos_achados.extend(escanear_conteudo(conteudo, arquivo))

    if todos_achados:
        print("❌ SEGREDO(S) ENCONTRADO(S) — commit BLOQUEADO:\n")
        for achado in todos_achados:
            print(achado)
        print("\nRemova o segredo do arquivo (use variável de ambiente em vez de")
        print("hardcoded) e tente o commit novamente. NUNCA use --no-verify para")
        print("contornar este gate — se é um falso positivo genuíno, ajuste o")
        print("padrão em scripts/gates/G_BLOQUEAR_SEGREDOS.py com justificativa.")
        print("\n" + "=" * 70)
        print("❌ GATE FALHOU")
        print("=" * 70 + "\n")
        return 1

    print("✅ Nenhum segredo encontrado.")
    print("\n" + "=" * 70)
    print("✅ GATE PASSOU")
    print("=" * 70 + "\n")
    return 0


if __name__ == '__main__':
    sys.exit(main())
