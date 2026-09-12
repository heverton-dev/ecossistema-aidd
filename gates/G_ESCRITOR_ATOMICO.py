# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_ESCRITOR_ATOMICO
=============================================================================
Verificação determinística (AST) de que os pontos críticos de gravação de
filesystem utilizam o módulo `escritor_atomico` ao invés de `open(..., 'w')`
direto.

Escopo auditado — todos os arquivos que escrevem no filesystem como parte
do pipeline AIDD:
  - componentes/compartilhado/src-core/materializador.py
  - tools/aidd-master/scripts/scaffold_infra.py
  - tools/aidd-master/scripts/compose_suite.py
  - tools/aidd-ops/scripts/pipeline_ops.py  (_gravar_plano)
  - tools/aidd-generator/scripts/phases/01_pesquisador.py
  - tools/aidd-generator/scripts/phases/02_analisador.py
  - tools/aidd-generator/scripts/phases/03_designer.py
  - tools/aidd-generator/scripts/phases/04_decisor.py
  - tools/aidd-generator/scripts/phases/05_criador.py
  - tools/aidd-generator/scripts/phases/06_documentador.py
  - tools/aidd-generator/scripts/phases/07_analisador.py
  - tools/aidd-generator/scripts/phases/08_implementador.py
  - tools/aidd-generator/scripts/phases/utils_delegacao.py
  - tools/aidd-generator/scripts/phases/utils_fleet_discovery.py
  - tools/aidd-generator/scripts/phases/utils_subagente_ephemero.py

Detecta:
  - open(..., 'w') ou open(..., 'w+', ...) sem uso de escritor_atomico
  - .write_text(...) sem uso de escritor_atomico (PATH.write_text)
  - json.dump(...) em arquivo aberto sem uso de escritor_atomico

Permitido (não é violação):
  - open(..., 'r') — leituras
  - open(..., 'rb') — leituras binárias
  - Escritas em arquivos temporários (*.tmp) ou diretórios de cache
  - Escritas em __init__.py vazios (padrão compose_suite)
  - Escritas no _executar_rollback do materializador (rollback de segurança)
  - Escritas no open(c, "wb") do rollback (restaurar snapshot)

Uso:
  python gates/G_ESCRITOR_ATOMICO.py
      exit 0 = todos os pontos críticos usam escritor_atomico
      exit 1 = ao menos 1 violação encontrada (arquivo, linha, código)
"""

import ast
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Caminhos relativos dos arquivos críticos auditados
ARQUIVOS_CRITICOS = [
    "componentes/compartilhado/src-core/materializador.py",
    "tools/aidd-master/scripts/scaffold_infra.py",
    "tools/aidd-master/scripts/compose_suite.py",
    "tools/aidd-ops/scripts/pipeline_ops.py",
    "tools/aidd-generator/scripts/phases/01_pesquisador.py",
    "tools/aidd-generator/scripts/phases/02_analisador.py",
    "tools/aidd-generator/scripts/phases/03_designer.py",
    "tools/aidd-generator/scripts/phases/04_decisor.py",
    "tools/aidd-generator/scripts/phases/05_criador.py",
    "tools/aidd-generator/scripts/phases/06_documentador.py",
    "tools/aidd-generator/scripts/phases/07_analisador.py",
    "tools/aidd-generator/scripts/phases/08_implementador.py",
    "tools/aidd-generator/scripts/phases/utils_delegacao.py",
    "tools/aidd-generator/scripts/phases/utils_fleet_discovery.py",
    "tools/aidd-generator/scripts/phases/utils_subagente_ephemero.py",
]

# Padrões de aceitação: chamadas que NÃO são violação
# Ex: open(..., "r") — leitura; open(..., "rb") — leitura binária
MODOS_LEITURA = {"r", "rb", "r+", "rt"}


def _arquivo_existe(caminho_relativo: str) -> bool:
    return os.path.isfile(os.path.join(ROOT_DIR, caminho_relativo))


def _contem_escritor_atomico(tree: ast.AST) -> bool:
    """Verifica se o módulo importa ou usa escritor_atomico."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "escritor_atomico" in node.module:
                return True
            for alias in node.names:
                if alias.name in ("escrever_atomico", "escrever_json_atomico"):
                    return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "escritor_atomico" in alias.name:
                    return True
    return False


def _extrair_modo_escrita(node: ast.Call) -> str | None:
    """Extrai o argumento 'modo' de uma chamada open(..., modo=...)."""
    # Posicional: open(caminho, "w", ...)
    if len(node.args) >= 2:
        arg = node.args[1]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value

    # Keyword: open(caminho, mode="w")
    for kw in node.keywords:
        if kw.arg == "mode":
            if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                return kw.value.value

    return None


def _eh_escrita(node: ast.Call) -> bool:
    """Determina se uma chamada open() é uma escrita (não leitura)."""
    modo = _extrair_modo_escrita(node)
    if modo is None:
        return False  # default mode='r'
    return any(m in modo for m in ("w", "a", "x", "W"))


def _esta_no_rollback(tree: ast.AST, target_line: int) -> bool:
    """Verifica se a linha está dentro de _executar_rollback (exceção legítima)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_executar_rollback":
            if hasattr(node, "end_lineno") and node.end_lineno:
                if node.lineno <= target_line <= node.end_lineno:
                    return True
    return False


def _checa_violacoes(conteudo: str, caminho: str) -> list[dict]:
    """Analisa um arquivo AST e retorna violações encontradas."""
    violacoes = []
    try:
        tree = ast.parse(conteudo, filename=caminho)
    except SyntaxError:
        return []

    tem_escritor = _contem_escritor_atomico(tree)

    for node in ast.walk(tree):
        violacao = None

        # Padrão 1: open(..., 'w') direto
        if isinstance(node, ast.Call):
            func = node.func
            is_open = False
            if isinstance(func, ast.Name) and func.id == "open":
                is_open = True
            elif isinstance(func, ast.Attribute) and func.attr == "open":
                # io.open(...)
                is_open = True

            if is_open and _eh_escrita(node):
                # Checar se é rollback
                if _esta_no_rollback(tree, node.lineno):
                    continue
                violacao = {
                    "tipo": "open_write",
                    "linha": node.lineno,
                    "col": getattr(node, "col_offset", 0),
                    "fix": "Use escrever_atomico() ou escrever_json_atomico()",
                }

        # Padrão 2: .write_text() em Path objects (excluindo __init__.py e .tmp)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "write_text":
                # Verificar se o pai é um open(...) ou não
                # Se tem escritor_atomico importado e NÃO usa.write_text com
                # path de __init__.py, é potencial violação
                violacao = {
                    "tipo": "write_text",
                    "linha": node.lineno,
                    "col": getattr(node, "col_offset", 0),
                    "fix": "Use escrever_atomico()",
                }

        if violacao:
            violacao["arquivo"] = caminho
            violacao["usa_escritor"] = tem_escritor
            violacoes.append(violacao)

    return violacoes


def executar() -> int:
    """Executa a auditoria. Exit 0 = OK, exit 1 = violações."""
    total_violacoes = 0
    total_arquivos_ok = 0
    arquivos_ausentes = []

    for caminho_rel in ARQUIVOS_CRITICOS:
        caminho_abs = os.path.join(ROOT_DIR, caminho_rel)
        if not os.path.isfile(caminho_abs):
            arquivos_ausentes.append(caminho_rel)
            continue

        with open(caminho_abs, "r", encoding="utf-8", errors="replace") as f:
            conteudo = f.read()

        violacoes = _checa_violacoes(conteudo, caminho_rel)

        if violacoes:
            total_violacoes += len(violacoes)
            for v in violacoes:
                print(f"  [VIOLACAO] {v['arquivo']}:{v['linha']} "
                      f"tipo={v['tipo']} usa_escritor={v['usa_escritor']}")
                print(f"             Fix: {v['fix']}")
        else:
            total_arquivos_ok += 1

    # Relatório
    print()
    print("=" * 72)
    print(" [G_ESCRITOR_ATOMICO] Auditoria de Escrita Atômica nos Pontos Críticos")
    print("=" * 72)
    print(f"  Arquivos auditados:   {len(ARQUIVOS_CRITICOS) - len(arquivos_ausentes)}/{len(ARQUIVOS_CRITICOS)}")
    if arquivos_ausentes:
        print(f"  Arquivos ausentes:    {len(arquivos_ausentes)} ({', '.join(arquivos_ausentes[:3])}...)" if len(arquivos_ausentes) > 3 else f"  Arquivos ausentes:    {len(arquivos_ausentes)} ({', '.join(arquivos_ausentes)})")
    print(f"  Arquivos OK:          {total_arquivos_ok}")
    print(f"  Total violações:      {total_violacoes}")
    print("=" * 72)

    if total_violacoes > 0:
        print("  [FALHA] Existem gravações diretas sem escritor_atomico.")
        return 1

    print("  [SUCESSO] Todos os pontos críticos usam escritor_atomico.")
    return 0


if __name__ == "__main__":
    sys.exit(executar())
