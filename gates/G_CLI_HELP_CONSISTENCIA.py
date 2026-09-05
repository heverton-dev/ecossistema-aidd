# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_CLI_HELP_CONSISTENCIA
=============================================================================
Detecta divergência entre flags de CLI realmente definidas via
`argparse.add_argument(...)` e flags citadas em mensagens de erro/print
dentro do mesmo arquivo (Pacote 1 — docs/planos/evolucao-notas-auditoria/
01-transparencia-e-gates.md). Origem real: aidd-enterprise/scripts/aidd.py
dizia "exige --command" numa mensagem de erro quando a flag de verdade,
definida no argparse, era "--mcp-command" — usuário seguia a mensagem de
erro e recebia "unrecognized arguments".

Usa `ast.parse` (não regex ingênua) e restringe a checagem a strings que são
o argumento de uma chamada `print(...)` ou de uma exceção dentro de um
`raise ...(...)` — é exatamente esse o formato de TODA mensagem voltada ao
usuário nestes 19 arquivos (confirmado por auditoria manual: nenhum usa
`parser.error()` ou `sys.exit(f"...")`, todos seguem `print(...); sys.exit(1)`
ou `raise Exception(...)`).

Essa restrição de escopo — não "qualquer string com --" — é o que elimina,
por construção, as 3 classes de falso positivo encontradas durante o
diagnóstico do Pacote 1 sem precisar de heurística frágil por classe:
1. Flags de FERRAMENTA EXTERNA citadas em `subprocess.run([...])`
   (ex.: `git log --oneline`) — nunca são argumento de print/raise.
2. Variáveis CSS (`--primary: #2563eb;`, `var(--primary)`) — vivem em
   templates HTML gravados em arquivo (`f.write(...)`), nunca impressas.
3. Docstrings e comentários de documentação que mencionam comandos de
   exemplo — não são argumento de print/raise.

Uso:
  python gates/G_CLI_HELP_CONSISTENCIA.py
      exit 0 = toda flag citada em texto do usuário tem `add_argument`
               correspondente, em todos os arquivos auditados.
      exit 1 = alguma flag citada em texto não é definida no argparse do
               mesmo arquivo (arquivo, linha e trecho são impressos).
"""

import ast
import json
import os
import re
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWLIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "allowlist_cli_help.json")

ARQUIVOS_AUDITADOS = [
    "tools/aidd-forge/aidd_forge/cli.py",
    "tools/aidd-master/scripts/aidd.py",
    "tools/aidd-enterprise/scripts/aidd.py",
    "tools/aidd-generator/scripts/aidd_inject.py",
    "tools/aidd-generator/scripts/pipeline_completo.py",
    "tools/aidd-generator/scripts/verificar_gates.py",
    "tools/aidd-generator/scripts/phases/01_pesquisador.py",
    "tools/aidd-generator/scripts/phases/02_analisador.py",
    "tools/aidd-generator/scripts/phases/03_designer.py",
    "tools/aidd-generator/scripts/phases/04_decisor.py",
    "tools/aidd-generator/scripts/phases/05_criador.py",
    "tools/aidd-generator/scripts/phases/06_documentador.py",
    "tools/aidd-generator/scripts/phases/07_analisador.py",
    "tools/aidd-generator/scripts/phases/08_implementador.py",
    "tools/aidd-generator/scripts/core/caveman_linter.py",
    "tools/aidd-generator/scripts/gates/G_INTEGRACAO_CROSS_SCRIPT.py",
    "tools/aidd-generator/scripts/gates/G_CYBERSECURITY_OWASP.py",
    "tools/aidd-generator/scripts/gates/AUDITAR_COMPARATIVO_HARNESS.py",
    "tools/aidd-generator/scripts/gates/G_BLOQUEAR_SEGREDOS.py",
]

# Flags que o próprio argparse injeta automaticamente ou que são universais
# demais para exigir um add_argument correspondente no mesmo arquivo.
FLAGS_UNIVERSAIS = {"--help"}

RE_FLAG = re.compile(r"--[a-zA-Z][a-zA-Z0-9-]*")


def _e_mensagem_ao_usuario(ancestrais):
    """True se a string está dentro de um print(...), em qualquer profundidade
    (cobre f-strings e concatenação), ou é/contém a construção da exceção de
    um `raise Excecao(...)`. Docstrings, comentários, templates gravados em
    arquivo (f.write) e chamadas subprocess.* nunca satisfazem nenhuma das
    duas condições, então ficam fora por construção — não por heurística
    específica para cada um."""
    calls_no_caminho = [n for n in ancestrais if isinstance(n, ast.Call)]

    for chamada in calls_no_caminho:
        func = chamada.func
        nome = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if nome == "print":
            return True

    if calls_no_caminho:
        # Chamada mais próxima da string (a que de fato constrói a
        # exceção) — se o pai dela é `raise`, é mensagem ao usuário.
        construcao_excecao = calls_no_caminho[-1]
        idx = ancestrais.index(construcao_excecao)
        pai_da_chamada = ancestrais[idx - 1] if idx > 0 else None
        if isinstance(pai_da_chamada, ast.Raise):
            return True

    return False


def _extrair_flags_definidas(arvore):
    definidas = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Call):
            func = no.func
            nome = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if nome != "add_argument":
                continue
            for arg in no.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if arg.value.startswith("--"):
                        definidas.add(arg.value)
    return definidas


def _extrair_flags_citadas(arvore):
    """Retorna [(flag, linha, trecho)] citadas em print(...) ou raise Excecao(...)."""
    citadas = []
    pais_por_no = {}
    pilha = [(arvore, [])]
    while pilha:
        no, ancestrais = pilha.pop()
        pais_por_no[id(no)] = ancestrais
        for filho in ast.iter_child_nodes(no):
            pilha.append((filho, ancestrais + [no]))

    for no in ast.walk(arvore):
        if not (isinstance(no, ast.Constant) and isinstance(no.value, str)):
            continue
        texto = no.value
        if "--" not in texto:
            continue
        ancestrais = pais_por_no.get(id(no), [])
        if not _e_mensagem_ao_usuario(ancestrais):
            continue
        for match in RE_FLAG.finditer(texto):
            flag = match.group(0)
            if flag in FLAGS_UNIVERSAIS:
                continue
            citadas.append((flag, getattr(no, "lineno", "?"), texto.strip()[:80]))
    return citadas


def _carregar_allowlist():
    if not os.path.exists(ALLOWLIST_PATH):
        return set()
    with open(ALLOWLIST_PATH, "r", encoding="utf-8") as f:
        dados = json.load(f)
    return set(dados.get("entradas", {}).keys())


def _auditar_arquivo(caminho_rel):
    caminho_abs = os.path.join(ROOT_DIR, caminho_rel)
    if not os.path.exists(caminho_abs):
        return None, [f"Arquivo declarado na auditoria não existe: {caminho_rel}"]

    with open(caminho_abs, "r", encoding="utf-8") as f:
        fonte = f.read()

    try:
        arvore = ast.parse(fonte, filename=caminho_rel)
    except SyntaxError as exc:
        return None, [f"{caminho_rel}: SyntaxError ao fazer parse — {exc}"]

    definidas = _extrair_flags_definidas(arvore)
    if not definidas:
        # Arquivo sem nenhum add_argument não tem CLI própria para auditar
        # (ex.: módulo utilitário importado por outro que tem argparse).
        return 0, []

    citadas = _extrair_flags_citadas(arvore)
    allowlist = _carregar_allowlist()
    erros = []
    for flag, linha, trecho in citadas:
        if flag in definidas:
            continue
        chave_allowlist = f"{caminho_rel}:{flag}"
        if chave_allowlist in allowlist:
            continue
        erros.append(
            f"{caminho_rel}:{linha} — flag '{flag}' citada mas não definida via "
            f"add_argument neste arquivo. Trecho: \"{trecho}\""
        )
    return len(citadas), erros


def checar():
    print("=" * 70)
    print(" [GATE] G_CLI_HELP_CONSISTENCIA — Flags de CLI vs. mensagens ao usuário")
    print("=" * 70)

    erros_totais = []
    for caminho_rel in ARQUIVOS_AUDITADOS:
        total_citadas, erros = _auditar_arquivo(caminho_rel)
        if total_citadas is None:
            erros_totais.extend(erros)
            print(f"[ERRO] {caminho_rel}")
            continue
        if erros:
            erros_totais.extend(erros)
            print(f"[FALHA] {caminho_rel} — {len(erros)} flag(s) inconsistente(s)")
        else:
            print(f"[OK] {caminho_rel} ({total_citadas} citação(ões) de flag verificada(s))")

    print("\n" + "=" * 70)
    if erros_totais:
        print(f" [FALHA] Quality Gate REPROVADO com {len(erros_totais)} erro(s):")
        for err in erros_totais:
            print(f"  - {err}")
        print("=" * 70)
        return 1

    print(" [SUCESSO] Quality Gate G_CLI_HELP_CONSISTENCIA APROVADO (100% OK)!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(checar())
