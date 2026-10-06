# -*- coding: utf-8 -*-
"""
 =============================================================================
 ECOSSISTEMA AIDD — QUALITY GATE: G_UNIVERSAL_HARNESS
 =============================================================================
 Audita a garantia SINE QUA NON de que todo componente, skill, MCP e hook
 esteja universalmente sincronizado, configurado e disponível de forma
 agnóstica para qualquer harness e sistema operacional (Windows, Linux, macOS).

 O que audita:
 1. Universalidade de Skills: toda skill em componentes/compartilhado/skills/
    deve estar presente em todos os 7 harnesses suportados.
 2. Universalidade de MCPs: todo MCP declarado em dependencias_externas.json
    deve estar registrado nos arquivos de config de todos os seus harnesses-alvo.
 3. Hooks Multiplataforma: hooks compartilhados devem possuir implementação
    agnóstica em Python (.py), executável tanto em Windows quanto em Unix.

 Uso:
   python gates/G_UNIVERSAL_HARNESS.py
       exit 0 = 100% universal e sincronizado.
       exit 1 = ausência, divergência ou drift em qualquer harness.
"""

import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))
import gestor_componentes
import gestor_dependencias

MANIFESTO_HARNESSES = os.path.join(ROOT_DIR, "gates", "manifesto_harnesses.json")
MANIFESTO_DEPS = os.path.join(ROOT_DIR, "gates", "dependencias_externas.json")


def checar():
    print("=" * 70)
    print(" [GATE] G_UNIVERSAL_HARNESS — Paridade Universal de Skills, MCPs e Hooks")
    print("=" * 70)

    erros = []

    # 1. Auditoria de Skills Multi-Harness
    print("\n--- 1. Auditoria de Paridade de Skills Multi-Harness ---")
    fonte_skills = os.path.join(ROOT_DIR, "componentes", "compartilhado", "skills")
    skills_canonicas = [
        s for s in os.listdir(fonte_skills)
        if os.path.isdir(os.path.join(fonte_skills, s)) and s not in gestor_componentes.IGNORAR_DIRS
    ] if os.path.isdir(fonte_skills) else []

    with open(MANIFESTO_HARNESSES, "r", encoding="utf-8") as f:
        harnesses_cfg = json.load(f)

    harnesses = harnesses_cfg.get("harnesses_suportados", {})
    skills_faltando = 0

    for skill in skills_canonicas:
        for h_nome, h_info in harnesses.items():
            prefixo = h_info.get("prefixo_pasta")
            if not prefixo:
                continue
            if h_nome == "gemini-cli":
                dest = os.path.join(ROOT_DIR, prefixo, "extensions", skill, "skills", skill, "SKILL.md")
            else:
                dest = os.path.join(ROOT_DIR, prefixo, "skills", skill, "SKILL.md")

            if not os.path.isfile(dest):
                erros.append(f"[SKILL AUSENTE] {skill} falta no harness '{h_nome}' ({dest})")
                skills_faltando += 1

    if skills_faltando == 0:
        print(f"[OK] {len(skills_canonicas)} skills canonicas presentes em todos os {len(harnesses)} harnesses.")

    # 2. Auditoria de Configurações de MCPs
    print("\n--- 2. Auditoria de Wiring Universal de MCPs ---")
    deps = gestor_dependencias.carregar_manifesto()
    mcps_declarados = deps.get("mcps", {})
    mcps_faltando = 0

    for mcp_nome, mcp_cfg in mcps_declarados.items():
        for h_alvo in mcp_cfg.get("harnesses_alvo", []):
            if h_alvo not in gestor_dependencias.DESTINOS_MCP:
                continue
            destino = gestor_dependencias.DESTINOS_MCP[h_alvo]
            caminho = destino["caminho"]
            chave = destino["chave"]
            if not gestor_dependencias._mcp_presente(mcp_nome, caminho, chave):
                erros.append(f"[MCP NAO REGISTRADO] {mcp_nome} nao registrado em {os.path.relpath(caminho, ROOT_DIR)} ({h_alvo})")
                mcps_faltando += 1

    if mcps_faltando == 0:
        print(f"[OK] {len(mcps_declarados)} MCPs declarados registrados em todos os harnesses-alvo.")

    # 3. Auditoria de Hooks Multiplataforma
    print("\n--- 3. Auditoria de Hooks Multiplataforma (Cross-Platform) ---")
    hooks_dir = os.path.join(ROOT_DIR, "componentes", "compartilhado", "hooks")
    if os.path.isdir(hooks_dir):
        hooks_py = [f for f in os.listdir(hooks_dir) if f.endswith(".py")]
        for h in hooks_py:
            # Validar sintaxe python
            caminho_hook = os.path.join(hooks_dir, h)
            try:
                with open(caminho_hook, "r", encoding="utf-8") as f:
                    compile(f.read(), caminho_hook, "exec")
            except Exception as e:
                erros.append(f"[HOOK SINTAXE INVALIDA] {h}: {e}")

        print(f"[OK] {len(hooks_py)} hooks Python agnosticos validados sintaticamente.")

    print("\n" + "=" * 70)
    if erros:
        print(f" [FALHA] Quality Gate G_UNIVERSAL_HARNESS REPROVADO com {len(erros)} erro(s):")
        for err in erros:
            print(f"  - {err}")
        print("=" * 70)
        return 1

    print(" [SUCESSO] Quality Gate G_UNIVERSAL_HARNESS APROVADO (100% OK)!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(checar())
