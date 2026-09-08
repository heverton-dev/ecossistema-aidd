# -*- coding: utf-8 -*-
"""
 =============================================================================
 ECOSSISTEMA AIDD — QUALITY GATE: G_HARNESS_COMPAT
 =============================================================================
 Materializa o gate G_HARNESS_COMPAT que o plano de execução original
 (docs/planos/PLANO-EXECUCAO-ECOSSISTEMA-AIDD.md) já declarava existir em
 gates/, mas nunca tinha sido implementado (R6 do
 PLANO-CORRECAO-RISCOS-ECOSSISTEMA-AIDD.md). Existiam apenas versões-template
 dentro de tools/*/scripts/gates/, feitas para serem copiadas para PROJETOS
 GERADOS pelas ferramentas — nada auditava a raiz do próprio ecossistema.

 O que audita aqui (evidência real coletada na auditoria, não hipotético):
 1. Detecção bidirecional de drift via SHA-256 entre fontes em componentes/
    e destinos materializados nos harnesses (Fase 4-6.4 P2):
    - MODIFICADO: fonte e destino existem mas SHA-256 difere
    - DIVERGENTE: fonte existe mas destino está ausente
    - ÓRFÃO: destino existe mas não corresponde a nenhuma fonte
 2. .claude/CLAUDE.md e .cursor/rules/aidd.md existem e referenciam
    AGENTS.md como fonte única — não duplicam conteúdo.
 3. Gates documentados em AGENTS.md vs gates/ em disco.

 Uso:
   python gates/G_HARNESS_COMPAT.py
       exit 0 = todos os pares sincronizados e ponteiros corretos.
       exit 1 = algum par divergiu ou ponteiro está ausente/quebrado.
"""

import os
import re
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))
import gestor_componentes

PONTEIROS = [
    (".claude/CLAUDE.md", "AGENTS.md"),
    (".cursor/rules/aidd.md", "AGENTS.md"),
]


def _ler(caminho_rel):
    caminho_abs = os.path.join(ROOT_DIR, caminho_rel)
    if not os.path.exists(caminho_abs):
        return None
    with open(caminho_abs, "r", encoding="utf-8-sig") as f:
        return f.read()


def checar():
    print("=" * 70)
    print(" [GATE] G_HARNESS_COMPAT — Sincronismo de artefatos multi-harness")
    print("=" * 70)

    erros = []

    print("\n--- Verificacao Bidirecional de Componentes (SHA-256) ---")
    relatorio = gestor_componentes.verify_detallado()
    print(f"Componentes verificados: {relatorio.total_componentes}")

    if relatorio.modificados:
        for item in relatorio.modificados:
            hash_info = ""
            if item.hash_fonte and item.hash_destino:
                hash_info = f" (fonte={item.hash_fonte[:12]}... destino={item.hash_destino[:12]}...)"
            erros.append(
                f"Componente MODIFICADO em {item.caminho}: "
                f"SHA-256 divergente da fonte em componentes/{hash_info}"
            )
            print(f"[MODIFICADO] [{item.componente}] {item.caminho}{hash_info}")

    if relatorio.divergentes:
        for item in relatorio.divergentes:
            erros.append(
                f"Componente DIVERGENTE: fonte '{item.componente}' existe mas "
                f"destino ausente em {item.caminho}"
            )
            print(f"[DIVERGENTE] [{item.componente}] {item.caminho}")

    if relatorio.orfaos:
        for item in relatorio.orfaos:
            erros.append(
                f"Arquivo ORFÃO em {item.caminho}: não corresponde a "
                f"nenhuma fonte declarada em componentes/"
            )
            print(f"[ORFAO] {item.caminho}")

    if relatorio.boms:
        for bom in relatorio.boms:
            erros.append(f"Arquivo com UTF-8 BOM proibido (EF BB BF): {bom}")
            print(f"[BOM] {bom}")

    if not relatorio.modificados and not relatorio.divergentes and not relatorio.orfaos and not relatorio.boms:
        print("[OK] Todos os componentes sincronizados com a fonte canonica (SHA-256 verificado).")

    print("\n--- Arquivos-ponteiro para AGENTS.md ---")
    for ponteiro, fonte in PONTEIROS:
        conteudo = _ler(ponteiro)
        if conteudo is None:
            erros.append(f"Arquivo-ponteiro {ponteiro} não existe.")
        elif fonte not in conteudo:
            erros.append(f"Arquivo-ponteiro {ponteiro} existe mas não referencia {fonte}.")
        else:
            print(f"[OK] {ponteiro} referencia {fonte} corretamente.")

    print("\n--- Gates documentados em AGENTS.md vs gates/ em disco ---")
    agents_md = _ler("AGENTS.md") or ""
    documentados = set(re.findall(r"(?<!/)gates/(G_[A-Z_]+\.py)", agents_md))
    em_disco = {
        f for f in os.listdir(os.path.join(ROOT_DIR, "gates"))
        if f.startswith("G_") and f.endswith(".py")
    }
    faltando_no_agents = em_disco - documentados
    faltando_em_disco = documentados - em_disco
    if faltando_no_agents:
        erros.append(f"Gate(s) em disco mas não documentado(s) em AGENTS.md: {', '.join(sorted(faltando_no_agents))}")
    if faltando_em_disco:
        erros.append(f"Gate(s) documentado(s) em AGENTS.md mas ausente(s) em disco: {', '.join(sorted(faltando_em_disco))}")
    if not faltando_no_agents and not faltando_em_disco:
        print(f"[OK] {len(em_disco)} gate(s) em disco, todos documentados em AGENTS.md.")

    print("\n" + "=" * 70)
    if erros:
        print(f" [FALHA] Quality Gate REPROVADO com {len(erros)} erro(s):")
        for err in erros:
            print(f"  - {err}")
        print("=" * 70)
        return 1

    print(" [SUCESSO] Quality Gate G_HARNESS_COMPAT APROVADO (100% OK)!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(checar())
