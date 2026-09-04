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
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COMANDOS = ["forge.md", "generate.md", "master.md", "enterprise.md"]
SKILLS = [
    "aidd-forge-runner",
    "aidd-generator-runner",
    "aidd-master-runner",
    "aidd-enterprise-runner",
]
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

    print("\n--- Comandos: .agent/commands/ vs .claude/commands/ ---")
    for cmd in COMANDOS:
        conteudo_agent = _ler(f".agent/commands/{cmd}")
        conteudo_claude = _ler(f".claude/commands/{cmd}")
        if conteudo_agent is None or conteudo_claude is None:
            erros.append(f"Comando {cmd} ausente em .agent/commands/ ou .claude/commands/.")
        elif conteudo_agent != conteudo_claude:
            erros.append(f"Comando {cmd} divergiu entre .agent/commands/ e .claude/commands/.")
        else:
            print(f"[OK] {cmd} idêntico nos dois harness.")

    print("\n--- Skills: skills/ vs .agent/skills/ ---")
    for skill in SKILLS:
        conteudo_raiz = _ler(f"skills/{skill}/SKILL.md")
        conteudo_agent = _ler(f".agent/skills/{skill}/SKILL.md")
        if conteudo_raiz is None or conteudo_agent is None:
            erros.append(f"SKILL.md de {skill} ausente em skills/ ou .agent/skills/.")
        elif conteudo_raiz != conteudo_agent:
            erros.append(f"SKILL.md de {skill} divergiu entre skills/ e .agent/skills/.")
        else:
            print(f"[OK] {skill}/SKILL.md idêntico nos dois locais.")

    print("\n--- Arquivos-ponteiro para AGENTS.md ---")
    for ponteiro, fonte in PONTEIROS:
        conteudo = _ler(ponteiro)
        if conteudo is None:
            erros.append(f"Arquivo-ponteiro {ponteiro} não existe.")
        elif fonte not in conteudo:
            erros.append(f"Arquivo-ponteiro {ponteiro} existe mas não referencia {fonte}.")
        else:
            print(f"[OK] {ponteiro} referencia {fonte} corretamente.")

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
