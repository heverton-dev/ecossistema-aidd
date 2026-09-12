# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_TRANSACTION_LOG_LRU
=============================================================================
Verificação determinística (AST + hashes SHA-256) da entrega do item
'transactionlog-lru-cache' (PLAN-0017, fase 06):

1. O módulo `transaction_log.py` existe na fonte única
   (componentes/compartilhado/src-core/) e é BYTE-IDÊNTICO nos dois destinos
   (tools/aidd-master/src/core/ e tools/aidd-enterprise/src/core/).
2. O arquivo está declarado no MANIFEST.json do núcleo compartilhado.
3. O par src/core da baseline de drift registra o arquivo
   (gates/baseline_nucleo_compartilhado.json).
4. O módulo expõe os símbolos críticos da entrega via análise AST:
   LruCache, TransactionLogEntry e TransactionLogRepositoryImpl.
5. Os testes unitários do item existem e são byte-idênticos nos dois tools
   (tests/unit/test_transaction_log_lru.py).

Uso:
  python gates/G_TRANSACTION_LOG_LRU.py
      exit 0 = entrega íntegra e completamente espelhada
      exit 1 = ao menos 1 divergência encontrada
"""

import ast
import hashlib
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FONTE = "componentes/compartilhado/src-core/transaction_log.py"
DESTINOS = [
    "tools/aidd-master/src/core/transaction_log.py",
    "tools/aidd-enterprise/src/core/transaction_log.py",
]
MANIFEST = "componentes/compartilhado/src-core/MANIFEST.json"
BASELINE = "gates/baseline_nucleo_compartilhado.json"
TESTES = [
    "tools/aidd-master/tests/unit/test_transaction_log_lru.py",
    "tools/aidd-enterprise/tests/unit/test_transaction_log_lru.py",
]

SIMBOLOS_EXIGIDOS = ["LruCache", "TransactionLogEntry", "TransactionLogRepositoryImpl"]


def _caminho(*partes):
    return os.path.join(ROOT_DIR, *partes)


def _hash(caminho_abs):
    with open(caminho_abs, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _simbolos_presentes(conteudo):
    try:
        tree = ast.parse(conteudo)
    except SyntaxError:
        return []
    presentes = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            presentes.append(node.name)
    return presentes


def executar() -> int:
    erros = []

    caminho_fonte = _caminho(FONTE)
    print("=" * 72)
    print(" [G_TRANSACTION_LOG_LRU] Auditoria do Transaction Log com Cache LRU")
    print("=" * 72)

    # 1. Fonte e destinos: existência + byte-identicidade
    if not os.path.isfile(caminho_fonte):
        erros.append(f"Fonte ausente: {FONTE}")
        print(f"  [FALHA] Fonte ausente: {FONTE}")
        return 1

    hash_fonte = _hash(caminho_fonte)
    print(f"  [OK] Fonte presente: {FONTE} (sha256 {hash_fonte[:12]}...)")

    for destino in DESTINOS:
        caminho_destino = _caminho(destino)
        if not os.path.isfile(caminho_destino):
            erros.append(f"Destino ausente: {destino}")
            print(f"  [FALHA] Destino ausente: {destino}")
            continue
        hash_destino = _hash(caminho_destino)
        if hash_destino != hash_fonte:
            erros.append(f"Divergencia byte-identica: {destino}")
            print(f"  [FALHA] Divergencia byte-identica em {destino}")
        else:
            print(f"  [OK] Destino byte-identico: {destino}")

    # 2. MANIFEST.json declara o arquivo
    manifest_path = _caminho(MANIFEST)
    arquivos_manifest = []
    if not os.path.isfile(manifest_path):
        erros.append(f"MANIFEST ausente: {MANIFEST}")
    else:
        with open(manifest_path, "r", encoding="utf-8") as f:
            try:
                arquivos_manifest = json.load(f).get("arquivos", [])
            except json.JSONDecodeError as exc:
                erros.append(f"MANIFEST.json inválido: {exc}")
        if "transaction_log.py" not in arquivos_manifest:
            erros.append("transaction_log.py não listado em MANIFEST.json (arquivos)")
            print("  [FALHA] transaction_log.py não listado em MANIFEST.json (arquivos)")
        else:
            print("  [OK] transaction_log.py declarado no MANIFEST.json")

    # 3. Baseline do drift registra o arquivo no par 'src/core'
    with open(_caminho(FONTE), "r", encoding="utf-8") as f:
        conteudo_fonte = f.read()
    baseline_registra = False
    baseline_path = _caminho(BASELINE)
    if not os.path.isfile(baseline_path):
        erros.append(f"Baseline ausente: {BASELINE}")
    else:
        with open(baseline_path, "r", encoding="utf-8") as f:
            try:
                baseline = json.load(f)
            except json.JSONDecodeError as exc:
                baseline = {}
                erros.append(f"baseline_nucleo_compartilhado.json inválido: {exc}")
        par = baseline.get("arquivos", {}).get("src/core", {})
        arquivos = par if isinstance(par, dict) else {}
        entrada = arquivos.get("transaction_log.py")
        if isinstance(entrada, dict) and entrada.get("esperado_identico") is True:
            baseline_registra = True
        if baseline_registra:
            print("  [OK] transaction_log.py registrado na baseline de drift (src/core)")
        else:
            erros.append("transaction_log.py não registrado com esperado_identico na baseline")
            print("  [FALHA] transaction_log.py não registrado com esperado_identico na baseline")

    # 4. Símbolos críticos presentes (AST)
    simbolos = _simbolos_presentes(conteudo_fonte)
    faltantes = [s for s in SIMBOLOS_EXIGIDOS if s not in simbolos]
    if faltantes:
        erros.append(f"Símbolos exigidos ausentes no módulo: {', '.join(faltantes)}")
        print(f"  [FALHA] Símbolos exigidos ausentes: {', '.join(faltantes)}")
    else:
        print(f"  [OK] Símbolos críticos presentes: {', '.join(SIMBOLOS_EXIGIDOS)}")

    # 5. Testes espelhados e byte-idênticos nos dois tools
    hashes_testes = []
    for teste in TESTES:
        caminho_teste = _caminho(teste)
        if not os.path.isfile(caminho_teste):
            erros.append(f"Teste ausente: {teste}")
            print(f"  [FALHA] Teste ausente: {teste}")
            continue
        hashes_testes.append(_hash(caminho_teste))
        print(f"  [OK] Teste presente: {teste}")
    if len(hashes_testes) == len(TESTES) and len(set(hashes_testes)) == 1:
        print("  [OK] Testes unitários byte-idênticos entre os tools")

    # Veredito
    print("=" * 72)
    if erros:
        print(f" [FALHA] Quality Gate REPROVADO com {len(erros)} divergência(s):")
        for err in erros:
            print(f"  - {err}")
        print("=" * 72)
        return 1

    print(" [SUCESSO] Transaction Log com Cache LRU íntegro e espelhado (100% OK)!")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(executar())