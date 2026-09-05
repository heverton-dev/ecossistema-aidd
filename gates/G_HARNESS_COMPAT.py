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
1. .agent/commands/*.md e .claude/commands/*.md devem ser idênticos —
   é o mesmo contrato de slash command exposto a dois harness diferentes
   (AGENTS.md §3: "Cada comando possui contrato formal executável em
   qualquer harness").
2. skills/<runner>/SKILL.md e .agent/skills/<runner>/SKILL.md devem ser
   idênticos — mesma skill exposta em dois locais que harness diferentes
   carregam (Claude Code lê skills/, MimoCode/Antigravity/OpenCode lê
   .agent/skills/ conforme AGENTS.md §5).
3. Arquivos-ponteiro (.claude/CLAUDE.md, .cursor/rules/aidd.md) existem e
   referenciam AGENTS.md como fonte única — não duplicam conteúdo, então
   não têm o problema de drift dos itens 1 e 2, só precisam existir e
   apontar certo.

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

    print("\n--- Verificacao Universal de Componentes (gates/manifesto_harnesses.json) ---")
    total_verificados, problemas = gestor_componentes.verify("todos")
    print(f"Componentes verificados: {total_verificados}")
    if problemas:
        for p in problemas:
            erros.append(f"Componente divergente ou ausente em harness: {p}")
            print(f"[ERRO] {p}")
    else:
        print("[OK] Todos os componentes sincronizados com a fonte canonica em todos os harnesses.")

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
    documentados = set(re.findall(r"gates/(G_[A-Z_]+\.py)", agents_md))
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
