#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_SKILL_ROT (ISSUE-0016 / Lei Canônica #9)
=============================================================================
Quality Gate determinístico de prevenção a Skill & Tool Rot.
Audita e resolve estaticamente todo caminho de arquivo, referência a script,
link markdown, comando CLI e ponto de entrada de ambiente (runtime/venv)
declarados nos arquivos SKILL.md do ecossistema.

Regra Canônica (ISSUE-0016 / Lei #9 Tool Testing Discipline / Ferramental Agêntico):
  Instruções de agentes e skills cujos textos apontam para scripts renomeados,
  caminhos inexistentes, subcomandos inválidos de CLI ou ambientes virtuais
  isolados inacessíveis geram quebras silenciosas em tempo de execução
  (como comprovado na regressão histórica da skill sandeco-token-reduce).
  Este portão bloqueia commits (exit 1) na ocorrência de qualquer referência
  estática que não resolva fisicamente.

Estratégia Canônica de Espelhos (Mirror Strategy):
  - Fonte Canônica da Verdade (Source of Truth): 'componentes/compartilhado/skills/'
    (e diretórios de origem canônica declarados em 'manifesto_harnesses.json').
  - Destinos de Harness (Mirrors): '.claude/skills/', '.cursor/skills/',
    '.gemini/.../skills/', '.opencode/skills/', '.mimocode/skills/', '.agents/skills/'.
  - Prevenção de Duplicatas: O gate avalia a resolução estática sobre a
    fonte canônica, reportando cada defeito real exatamente UMA vez (evitando
    as 6 replicações idênticas por harness). Em paralelo, valida que nenhum
    harness possui skills órfãs desconectadas da fonte canônica.

Critérios Determinísticos:
  1. Resolução Estática de Links Markdown: Alvos locais devem existir.
  2. Resolução de Comandos CLI: Subcomandos de 'ecossistema.py' devem existir.
  3. Resolução de Scripts Executáveis: Scripts (.py, .sh, .js, .cmd) invocados
     em comandos devem existir na pasta da skill ou no repositório.
  4. Resolução de Caminhos de Repositório: Diretórios e arquivos sob 'docs/',
     'tools/', 'gates/', 'componentes/', etc., devem existir no disco.
  5. Detecção de Ponto de Entrada / Ambiente Virtual Inacessível (Caso Sandeco):
     Referências a binários de ambientes virtuais (.venv, <venv-python>) não
     distribuídos ou inexistentes são bloqueadas.
  6. Ausência de Skills Órfãs em Harnesses: Toda skill em harness deve ter
     origem na fonte canônica.

Saída:
  exit 0 = 100% das referências de skills resolvem estaticamente.
  exit 1 = Ao menos uma referência estática não resolve no disco.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Diretórios canônicos
CANONICAL_SKILLS_DIR = os.path.join(ROOT_DIR, "componentes", "compartilhado", "skills")
MANIFESTO_PATH = os.path.join(ROOT_DIR, "gates", "manifesto_harnesses.json")

# Subcomandos suportados pelo CLI ecossistema.py
def obter_subcomandos_ecossistema() -> Set[str]:
    subcomandos = set()
    try:
        import ecossistema
        for attr in dir(ecossistema):
            if attr.startswith("cmd_"):
                subcomandos.add(attr[4:].replace("_", "-"))
    except Exception:
        # Fallback defensivo estático
        subcomandos = {
            "aidd-bridge", "audit", "bridge", "components", "dependencia",
            "enterprise", "factory", "forge", "freedom", "generate",
            "harness", "livro", "master", "melhoria", "open", "ops",
            "orchestrate", "plan", "planner", "preflight-host", "pure",
            "run-fluxo", "status"
        }
    return subcomandos


class ReferenciaSkill:
    def __init__(self, tipo: str, texto: str, linha: int):
        self.tipo = tipo
        self.texto = texto.strip()
        self.linha = linha

    def __repr__(self):
        return f"<Ref {self.tipo} L{self.linha}: {self.texto}>"


def extrair_referencias_skill_md(skill_md_path: str) -> List[ReferenciaSkill]:
    """Extrai todas as referências de paths, links e comandos de um arquivo SKILL.md."""
    if not os.path.isfile(skill_md_path):
        return []

    with open(skill_md_path, "r", encoding="utf-8", errors="replace") as f:
        linhas = f.readlines()

    referencias: List[ReferenciaSkill] = []
    re_link = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    re_inline = re.compile(r'`([^`\n]+)`')

    in_code_block = False
    block_lang = ""

    for idx, line in enumerate(linhas, start=1):
        stripped = line.strip()

        if stripped.startswith("```"):
            if not in_code_block:
                in_code_block = True
                block_lang = stripped[3:].strip().lower()
            else:
                in_code_block = False
            continue

        if in_code_block:
            if block_lang in ["bash", "sh", "shell", "powershell", "cmd", "python", ""]:
                if stripped and not stripped.startswith("#"):
                    referencias.append(ReferenciaSkill("code_block_cmd", stripped, idx))
            continue

        # Fora de blocos de código
        for match in re_link.finditer(line):
            target = match.group(2).strip()
            if not target.startswith(("http://", "https://", "mailto:", "#")):
                referencias.append(ReferenciaSkill("md_link", target, idx))

        for match in re_inline.finditer(line):
            val = match.group(1).strip()
            referencias.append(ReferenciaSkill("inline_code", val, idx))

    return referencias


def resolver_referencia_estatica(
    skill_name: str,
    skill_dir: str,
    ref: ReferenciaSkill,
    repo_root: str,
    subcomandos_validos: Set[str],
) -> Tuple[str, str]:
    """
    Resolve estaticamente uma referência.
    Retorna (status, motivo) onde status é:
      - 'OK': Resolvido com sucesso no disco / contrato CLI.
      - 'FAIL': Referência que não resolve (quebrada).
      - 'IGNORE': Conteúdo que não representa uma referência a arquivo/comando.
    """
    texto = ref.texto

    # Normalizar prefixos de lista ou tabela
    if texto.startswith(("|", "- ", "* ")):
        texto = texto.lstrip("|- *").strip()

    # 1. Links Markdown locais ou relativos
    if ref.tipo == "md_link":
        clean_target = texto.split("#")[0].strip()
        if not clean_target:
            return "OK", "âncora na mesma página"
        p_skill = os.path.normpath(os.path.join(skill_dir, clean_target))
        if os.path.exists(p_skill):
            return "OK", f"arquivo local existe: {clean_target}"
        p_repo = os.path.normpath(os.path.join(repo_root, clean_target))
        if os.path.exists(p_repo):
            return "OK", f"arquivo no repositório existe: {clean_target}"
        return "FAIL", f"Link markdown aponta para arquivo inexistente: '{clean_target}'"

    # 2. Comandos CLI: ecossistema.py <subcmd>
    if "ecossistema.py" in texto:
        m_eco = re.search(r'ecossistema\.py\s+([a-zA-Z0-9_\-]+)', texto)
        if m_eco:
            subcmd = m_eco.group(1)
            if subcmd in subcomandos_validos:
                return "OK", f"subcomando válido de ecossistema.py: '{subcmd}'"
            else:
                return "FAIL", f"Subcomando desconhecido do ecossistema.py: '{subcmd}'"
        return "OK", "referência genérica a ecossistema.py"

    # 3. Referências a placeholders de pasta da skill: <skill-dir>/... ou <skill-base-dir>/...
    m_placeholder = re.search(r'<(?:skill-dir|skill-base-dir)>/([^\"\s`\)]+)', texto)
    if m_placeholder:
        subpath = m_placeholder.group(1)
        p = os.path.normpath(os.path.join(skill_dir, subpath))
        if os.path.exists(p):
            return "OK", f"caminho sob placeholder existe: '{subpath}'"
        return "FAIL", f"Caminho sob placeholder <skill-dir> não existe no disco: '{subpath}'"

    # 4. Caso Regression Fixture Sandeco / Ambiente Virtual Inacessível
    # Detecta instruções que exigem interpretador .venv isolado quando este não existe no disco
    if "<venv-python>" in texto or ((".venv" in texto) and any(w in texto for w in ["Scripts", "bin", "python.exe", "python"])):
        venv_dir = os.path.join(skill_dir, ".venv")
        if not os.path.isdir(venv_dir):
            return "FAIL", f"Referência a interpretador em ambiente isolado (.venv) inexistente no repositório: '{texto}'"
        venv_py = (
            os.path.join(venv_dir, "Scripts", "python.exe")
            if os.name == "nt"
            else os.path.join(venv_dir, "bin", "python")
        )
        if not os.path.exists(venv_py):
            return "FAIL", f"Executável do interpretador virtual ausente em .venv: '{venv_py}'"
        return "OK", "interpretador virtual resolvido"

    # 5. Caminhos explícitos com diretórios canônicos do repositório
    m_repo_path = re.search(
        r'(?:^|[\s\"\'\(])((?:docs|tools|gates|componentes|secoes|\.orca|\.claude|\.agents|\.cursor|scripts)/[^\s\"\'\)`]+)',
        texto,
    )
    if m_repo_path:
        raw_path = m_repo_path.group(1).rstrip(".,;:!?'\"")
        # Se contiver wildcards ou placeholders dinâmicos (ex: <nome>, *)
        if "<" in raw_path or "*" in raw_path or "[" in raw_path:
            prefix = raw_path.split("<")[0].split("*")[0].split("[")[0]
            static_dir = (
                os.path.dirname(prefix.rstrip("/\\"))
                if not prefix.endswith(("/", "\\"))
                else prefix.rstrip("/\\")
            )
            parent_p = os.path.normpath(os.path.join(repo_root, static_dir)) if static_dir else repo_root
            if os.path.exists(parent_p):
                return "OK", f"diretório ancestral '{static_dir}' existe"
            return "FAIL", f"Diretório ancestral de '{raw_path}' não existe no repositório: '{static_dir}'"
        else:
            p_repo = os.path.normpath(os.path.join(repo_root, raw_path))
            p_skill = os.path.normpath(os.path.join(skill_dir, raw_path))
            if os.path.exists(p_repo) or os.path.exists(p_skill):
                return "OK", f"caminho resolvido: '{raw_path}'"
            return "FAIL", f"Caminho não existe no repositório nem na skill: '{raw_path}'"

    # 6. Invocação de scripts dentro de comandos executáveis
    if ref.tipo == "code_block_cmd" or re.search(r'(?:python|sh|bash|\./)\s+[a-zA-Z0-9_\-\./\\]+', texto):
        m_exec = re.search(
            r'(?:python|sh|bash|\./)\s+[\"\']?([a-zA-Z0-9_\-\./\\]+\.(?:py|sh|js|ts|cmd|bat))[\"\']?',
            texto,
        )
        if m_exec:
            script_target = m_exec.group(1)
            candidates = [
                os.path.normpath(os.path.join(skill_dir, script_target)),
                os.path.normpath(os.path.join(skill_dir, "scripts", script_target)),
                os.path.normpath(os.path.join(repo_root, script_target)),
                os.path.normpath(os.path.join(repo_root, "scripts", script_target)),
            ]
            if any(os.path.exists(c) for c in candidates):
                return "OK", f"script executável resolvido: '{script_target}'"
            return "FAIL", f"Script executável invocado não encontrado no disco: '{script_target}'"

    return "IGNORE", ""


def auditar_skills(
    skills_root: str = CANONICAL_SKILLS_DIR,
    repo_root: str = ROOT_DIR,
) -> Tuple[int, List[Dict[str, any]], List[Dict[str, any]], int]:
    """
    Audita estaticamente todas as skills no diretório especificado.
    Retorna (codigo_saida, falhas, conformes, total_referencias).
    """
    if not os.path.isdir(skills_root):
        return 1, [{"skill": "GLOBAL", "linha": 0, "texto": skills_root, "motivo": f"Diretório de skills não encontrado: {skills_root}"}], [], 0

    subcomandos_validos = obter_subcomandos_ecossistema()

    falhas: List[Dict[str, any]] = []
    conformes: List[Dict[str, any]] = []
    total_referencias = 0

    skills = sorted(os.listdir(skills_root))

    for s_name in skills:
        skill_dir = os.path.join(skills_root, s_name)
        skill_md = os.path.join(skill_dir, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue

        refs = extrair_referencias_skill_md(skill_md)
        for ref in refs:
            status, motivo = resolver_referencia_estatica(
                s_name, skill_dir, ref, repo_root, subcomandos_validos
            )
            if status == "FAIL":
                total_referencias += 1
                falhas.append({
                    "skill": s_name,
                    "linha": ref.linha,
                    "tipo": ref.tipo,
                    "texto": ref.texto,
                    "motivo": motivo,
                    "skill_md": skill_md,
                })
            elif status == "OK":
                total_referencias += 1
                conformes.append({
                    "skill": s_name,
                    "linha": ref.linha,
                    "tipo": ref.tipo,
                    "texto": ref.texto,
                    "motivo": motivo,
                })

    codigo_saida = 0 if not falhas else 1
    return codigo_saida, falhas, conformes, total_referencias


def auditar_orfaos_em_mirrors(repo_root: str = ROOT_DIR) -> List[str]:
    """
    Verifica se existem skills em pastas de harness que não possuem origem
    na fonte canônica compartilhada.
    """
    orfaos: List[str] = []
    canonical_skills_path = os.path.join(repo_root, "componentes", "compartilhado", "skills")
    if not os.path.isdir(canonical_skills_path):
        return orfaos

    canonical_skills = {
        s for s in os.listdir(canonical_skills_path)
        if os.path.isdir(os.path.join(canonical_skills_path, s))
    }

    # Harnesses padrões a checar
    harnesses_dirs = [
        os.path.join(repo_root, ".claude", "skills"),
        os.path.join(repo_root, ".cursor", "skills"),
        os.path.join(repo_root, ".opencode", "skills"),
        os.path.join(repo_root, ".mimocode", "skills"),
        os.path.join(repo_root, ".agents", "skills"),
        os.path.join(repo_root, ".codebuddy", "skills"),
    ]

    for h_dir in harnesses_dirs:
        if not os.path.isdir(h_dir):
            continue
        for s in os.listdir(h_dir):
            s_path = os.path.join(h_dir, s)
            if os.path.isdir(s_path) and os.path.isfile(os.path.join(s_path, "SKILL.md")):
                if s not in canonical_skills:
                    orfaos.append(f"Skill órfã em harness sem fonte canônica: '{os.path.relpath(s_path, repo_root)}'")

    return orfaos


def main() -> int:
    parser = argparse.ArgumentParser(description="G_SKILL_ROT: Auditoria estática de resolução de referências em SKILL.md.")
    parser.add_argument("--skills-dir", default=CANONICAL_SKILLS_DIR, help="Caminho alternativo para diretório canônico de skills")
    parser.add_argument("--repo-root", default=ROOT_DIR, help="Caminho raiz do repositório")
    args = parser.parse_args()

    print("=" * 76)
    print(" [GATE] G_SKILL_ROT — Prevenção a Skill & Tool Rot (ISSUE-0016 / Lei #9)")
    print("=" * 76)

    codigo, falhas, conformes, total_refs = auditar_skills(args.skills_dir, args.repo_root)

    # Validar também orfãos nos mirrors apenas se estiver rodando contra o repo real
    orfaos = []
    if os.path.normpath(args.repo_root) == os.path.normpath(ROOT_DIR):
        orfaos = auditar_orfaos_em_mirrors(args.repo_root)
        if orfaos:
            codigo = 1

    print(f"\n[ESTATÍSTICAS] Referências analisadas: {total_refs} | Conformes: {len(conformes)} | Falhas: {len(falhas)}")

    if conformes and not falhas and not orfaos:
        print(f"  [OK] Todas as referências estáticas de skills resolvem 100% fisicamente no disco.")

    if orfaos:
        print("\n" + "=" * 76)
        print(f" [FALHA] {len(orfaos)} skill(s) órfã(s) encontrada(s) nos harnesses:")
        print("=" * 76)
        for orf in orfaos:
            print(f"  [ÓRFÃ] {orf}")

    if falhas:
        print("\n" + "=" * 76)
        print(f" [FALHA] {len(falhas)} referência(s) estática(s) não resolvida(s) encontrada(s):")
        print("=" * 76)
        # Agrupar por skill
        falhas_por_skill: Dict[str, List[Dict[str, any]]] = {}
        for f in falhas:
            falhas_por_skill.setdefault(f["skill"], []).append(f)

        for s_name, s_falhas in falhas_por_skill.items():
            print(f"\n -> Skill '{s_name}' ({len(s_falhas)} falhas):")
            for f in s_falhas:
                print(f"    - L{f['linha']:03d} [{f['tipo']}]: '{f['texto']}'")
                print(f"       ERRO: {f['motivo']}")

        print("\n" + "=" * 76)
        print(" REGRA CANÔNICA VIOLADA (ISSUE-0016 / Lei #9):")
        print(" Todas as referências a scripts, caminhos e comandos CLI declaradas")
        print(" em corpos de SKILL.md devem resolver estaticamente no disco.")
        print("=" * 76)

    return codigo


if __name__ == "__main__":
    sys.exit(main())
