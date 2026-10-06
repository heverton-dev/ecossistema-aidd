# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_ISOLATION_AUDIT
=============================================================================
Auditoria estática de isolamento de fatias verticais (Vertical Slice Architecture - VSA).

Regra Inviolável de Arquitetura:
  Fatias verticais em 'src/features/<dominio>/' devem ser 100% autônomas e
  mutuamente isoladas. É terminantemente proibido que uma fatia importe código
  diretamente de outra fatia (ex: 'from src.features.outra import ...' ou
  'import features.outra').

  Comunicação inter-fatias deve ocorrer exclusivamente por:
    1. Eventos assíncronos via 'src/core/events.py' (EventGateway / Mediator).
    2. Contratos e infraestrutura horizontal compartilhada em 'src/core/'.

Saída:
  exit 0 = Fatias VSA 100% isoladas (nenhuma dependência cruzada direta).
  exit 1 = Violação detectada (arquivo, fatia de origem, fatia alvo e linha).
"""

import ast
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def extrair_modulo_e_fatia(caminho_arquivo: str) -> tuple[str, str] | None:
    """Extrai o nome da fatia a partir do caminho físico do arquivo.

    Exemplo:
      .../src/features/encomendas/services.py -> fatia = 'encomendas'
    """
    norm = caminho_arquivo.replace("\\", "/")
    partes = norm.split("/")
    if "features" in partes:
        idx = partes.index("features")
        if idx + 1 < len(partes):
            fatia = partes[idx + 1]
            if fatia and not fatia.endswith(".py") and fatia != "__pycache__":
                return norm, fatia
    return None


def analisar_imports_arquivo(caminho_arquivo: str, fatia_atual: str) -> list[tuple[int, str, str]]:
    """Analisa nós AST de importação buscando referências cruzadas a outras fatias.

    Retorna lista de (linha, fatia_alvo, declaracao).
    """
    violacoes = []
    try:
        with open(caminho_arquivo, "r", encoding="utf-8", errors="replace") as f:
            conteudo = f.read()
        arvore = ast.parse(conteudo, filename=caminho_arquivo)
    except SyntaxError:
        return violacoes
    except Exception as exc:
        violacoes.append((1, "ERRO_LEITURA", str(exc)))
        return violacoes

    for node in ast.walk(arvore):
        # Caso 1: from src.features.outra import ... ou from features.outra import ...
        if isinstance(node, ast.ImportFrom) and node.module:
            modulo = node.module
            partes = modulo.split(".")
            if "features" in partes:
                idx = partes.index("features")
                if idx + 1 < len(partes):
                    fatia_alvo = partes[idx + 1]
                    if fatia_alvo != fatia_atual:
                        linha = getattr(node, "lineno", 1)
                        violacoes.append(
                            (linha, fatia_alvo, f"from {modulo} import ...")
                        )

        # Caso 2: import src.features.outra ou import features.outra
        elif isinstance(node, ast.Import):
            for alias in node.names:
                partes = alias.name.split(".")
                if "features" in partes:
                    idx = partes.index("features")
                    if idx + 1 < len(partes):
                        fatia_alvo = partes[idx + 1]
                        if fatia_alvo != fatia_atual:
                            linha = getattr(node, "lineno", 1)
                            violacoes.append(
                                (linha, fatia_alvo, f"import {alias.name}")
                            )

    return violacoes


def scan_isolation_violations(target_dir: str) -> list[dict]:
    """Varre target_dir procurando arquivos dentro de features/ e checando isolamento."""
    todas_violacoes = []
    for root, dirs, files in os.walk(target_dir):
        # Ignora pastas de cache, controle de versão e ambientes virtuais
        dirs[:] = [
            d for d in dirs
            if d not in {".git", ".pytest_cache", "__pycache__", "node_modules", "venv", ".venv"}
            and not d.startswith("wt-")
        ]

        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                info = extrair_modulo_e_fatia(full_path)
                if not info:
                    continue
                _, fatia_origem = info
                violacoes = analisar_imports_arquivo(full_path, fatia_origem)
                for linha, fatia_alvo, trecho in violacoes:
                    todas_violacoes.append({
                        "arquivo": full_path,
                        "linha": linha,
                        "fatia_origem": fatia_origem,
                        "fatia_alvo": fatia_alvo,
                        "trecho": trecho,
                    })
    return todas_violacoes


def main() -> int:
    print("=" * 72)
    print(" [GATE] G_ISOLATION_AUDIT — Auditoria de Isolamento Estrito VSA")
    print("=" * 72)

    diretorios_alvo = [
        os.path.join(ROOT_DIR, "tools"),
        os.path.join(ROOT_DIR, "testes"),
    ]

    violacoes = []
    for d in diretorios_alvo:
        if os.path.exists(d):
            violacoes.extend(scan_isolation_violations(d))

    if violacoes:
        print(f"\n[FALHA] Detectada(s) {len(violacoes)} violação(ões) de isolamento inter-fatias:\n")
        for v in violacoes:
            rel = os.path.relpath(v["arquivo"], ROOT_DIR)
            print(f"  - {rel}:{v['linha']}")
            print(f"    Fatia Origem: '{v['fatia_origem']}' -> Fatia Alvo: '{v['fatia_alvo']}'")
            print(f"    Declaração  : {v['trecho']}")
            print("    Correção    : Fatias não devem acoplar-se. Use EventGateway ou src/core/.\n")
        print("=" * 72)
        return 1

    print("\n[SUCESSO] Quality Gate G_ISOLATION_AUDIT APROVADO — Fatias VSA 100% isoladas!")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
