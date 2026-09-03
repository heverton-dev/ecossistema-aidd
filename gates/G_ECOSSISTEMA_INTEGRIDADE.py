# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_ECOSSISTEMA_INTEGRIDADE
=============================================================================
Validação determinística de integridade do meta-repositório ecossistema-aidd.
Audita:
1. Existência e integridade estrutural das 4 ferramentas em tools/
2. Existência e conformidade das 4 skills universais (YAML frontmatter)
3. Presença dos Slash Commands para multi-harness (.agent/ e .claude/)
4. Validação sintática (ast.parse) dos scripts centrais
5. Presença de governança canônica (AGENTS.md, .gitignore)

Saída: exit 0 (Aprovado) ou exit 1 (Bloqueado).
"""

import os
import sys
import ast
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TOOLS_REQUIRED = [
    "aidd-forge",
    "aidd-generator",
    "aidd-master",
    "aidd-master-enterprise"
]

SKILLS_REQUIRED = [
    "aidd-forge-runner",
    "aidd-generator-runner",
    "aidd-master-runner",
    "aidd-enterprise-runner"
]

COMMANDS_REQUIRED = [
    "forge.md",
    "generate.md",
    "master.md",
    "enterprise.md"
]

def audit():
    print("=" * 70)
    print(" [GATE] G_ECOSSISTEMA_INTEGRIDADE — Auditoria do Ecossistema AIDD")
    print("=" * 70)
    
    erros = []
    
    # 1. Checagem de Governança Raiz
    agents_path = os.path.join(ROOT_DIR, "AGENTS.md")
    gitignore_path = os.path.join(ROOT_DIR, ".gitignore")
    
    if not os.path.exists(agents_path):
        erros.append("Arquivo AGENTS.md não encontrado na raiz.")
    else:
        print("[OK] AGENTS.md canônico presente.")
        
    if not os.path.exists(gitignore_path):
        erros.append("Arquivo .gitignore não encontrado na raiz.")
    else:
        print("[OK] .gitignore presente.")

    # 2. Checagem das 4 ferramentas em tools/
    print("\n--- Verificando Ferramentas Integradas (tools/) ---")
    for tool in TOOLS_REQUIRED:
        tool_dir = os.path.join(ROOT_DIR, "tools", tool)
        if not os.path.isdir(tool_dir):
            erros.append(f"Diretório da ferramenta tools/{tool} não encontrado.")
            continue
        
        # Verificar que não contém .git acidental
        git_dir = os.path.join(tool_dir, ".git")
        if os.path.exists(git_dir):
            erros.append(f"Diretório .git encontrado indevidamente dentro de tools/{tool}!")
        
        # Verificar README e testes
        readme = os.path.join(tool_dir, "README.md")
        if not os.path.exists(readme):
            erros.append(f"README.md ausente em tools/{tool}")
        else:
            print(f"[OK] tools/{tool} presente e documentado.")

    # 3. Checagem das 4 Skills Universais
    print("\n--- Verificando Skills Universais (skills/) ---")
    frontmatter_re = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    for skill in SKILLS_REQUIRED:
        skill_file = os.path.join(ROOT_DIR, "skills", skill, "SKILL.md")
        if not os.path.exists(skill_file):
            erros.append(f"Skill {skill_file} não encontrada.")
            continue
        
        with open(skill_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        match = frontmatter_re.match(content)
        if not match:
            erros.append(f"Frontmatter YAML inválido ou ausente em {skill_file}.")
        else:
            print(f"[OK] Skill {skill} válida com YAML frontmatter.")

    # 4. Checagem de Slash Commands (.agent/ e .claude/)
    print("\n--- Verificando Slash Commands Multi-Harness ---")
    for harness_dir in [".agent/commands", ".claude/commands"]:
        for cmd in COMMANDS_REQUIRED:
            cmd_path = os.path.join(ROOT_DIR, harness_dir, cmd)
            if not os.path.exists(cmd_path):
                erros.append(f"Comando {cmd_path} não encontrado.")
            else:
                print(f"[OK] Comando {harness_dir}/{cmd} configurado.")

    # 5. Validação Sintática AST em Arquivos Python Raiz e Gates
    print("\n--- Validação Sintática (AST parse) ---")
    py_files_to_check = [
        os.path.join(ROOT_DIR, "gates", "G_ECOSSISTEMA_INTEGRIDADE.py")
    ]
    cli_path = os.path.join(ROOT_DIR, "ecossistema.py")
    if os.path.exists(cli_path):
        py_files_to_check.append(cli_path)
        
    for py_file in py_files_to_check:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                source = f.read()
            ast.parse(source, filename=py_file)
            print(f"[OK] Sintaxe Python verificada: {os.path.basename(py_file)}")
        except Exception as e:
            erros.append(f"Erro de sintaxe em {py_file}: {e}")

    # Conclusão e veredito
    print("\n" + "=" * 70)
    if erros:
        print(f" [FALHA] Quality Gate REPROVADO com {len(erros)} erro(s):")
        for err in erros:
            print(f"  - {err}")
        print("=" * 70)
        sys.exit(1)
    else:
        print(" [SUCESSO] Quality Gate G_ECOSSISTEMA_INTEGRIDADE APROVADO (100% OK)!")
        print("=" * 70)
        sys.exit(0)

if __name__ == "__main__":
    audit()