# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_FRONTEND_LAYERS
=============================================================================
Validação estática de separação de camadas nas entregas e templates de Frontend.
Imposição de Arquitetura:
  1. Componentes visuais puros (Dumb Components em 'components/ui/') são
     estritamente de apresentação. É proibido executar chamadas de rede
     diretas ('fetch(', 'axios.', 'ky(') em seu interior.
  2. Chamadas de rede e orquestração de dados devem residir exclusivamente
     em Hooks ('hooks/'), Services ('services/') ou API Clients ('lib/api').

Saída:
  exit 0 = Nenhuma violação de camadas no frontend detectada.
  exit 1 = Violação detectada (arquivo e trecho infrator são exibidos).
"""

import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Padrões proibidos em componentes puramente visuais (UI dumb components)
FORBIDDEN_NETWORK_PATTERNS = [
    (re.compile(r"\bfetch\s*\("), "Chamada direta a fetch() em componente visual puro"),
    (re.compile(r"\baxios\.(?:get|post|put|delete|patch)\s*\("), "Uso direto de axios em componente visual puro"),
    (re.compile(r"\bky\.(?:get|post|put|delete|patch)\s*\("), "Uso direto de ky em componente visual puro"),
]


def audit_frontend_file(file_path: str) -> list:
    """Verifica se um arquivo de componente de UI viola as regras de camadas."""
    violacoes = []
    # Só analisa componentes dentro de components/ui/
    norm_path = file_path.replace("\\", "/")
    if "/components/ui/" not in norm_path and not norm_path.startswith("components/ui/"):
        return violacoes

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for idx, line in enumerate(f, start=1):
                # Ignora comentários
                stripped = line.strip()
                if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                    continue
                for pattern, msg in FORBIDDEN_NETWORK_PATTERNS:
                    if pattern.search(line):
                        violacoes.append((file_path, idx, msg, stripped))
    except Exception as e:
        violacoes.append((file_path, 0, f"Erro ao ler arquivo: {e}", ""))
    return violacoes


def scan_frontend_layers(target_root: str) -> list:
    """Varre diretórios de deliverables e templates procurando violações em UI."""
    todas_violacoes = []
    for root, _, files in os.walk(target_root):
        # Ignora node_modules, build, dist e .git
        if any(skip in root for skip in ["node_modules", ".git", "dist", ".next", "__pycache__"]):
            continue
        for file in files:
            if file.endswith((".tsx", ".jsx", ".ts", ".js")):
                full_path = os.path.join(root, file)
                todas_violacoes.extend(audit_frontend_file(full_path))
    return todas_violacoes


def main():
    print("=" * 72)
    print(" [GATE] G_FRONTEND_LAYERS — Auditoria de Separação de Camadas no Frontend")
    print("=" * 72)

    alvos = [
        os.path.join(ROOT_DIR, "tools"),
        os.path.join(ROOT_DIR, "componentes")
    ]

    violacoes = []
    for alvo in alvos:
        if os.path.exists(alvo):
            violacoes.extend(scan_frontend_layers(alvo))

    if violacoes:
        print(f"\n[FALHA] Foram encontradas {len(violacoes)} violação(ões) de camadas no frontend:\n")
        for fpath, lnum, msg, code in violacoes:
            rel = os.path.relpath(fpath, ROOT_DIR)
            print(f"  - {rel}:{lnum}")
            print(f"    Regra: {msg}")
            print(f"    Linha: {code}\n")
        print("=" * 72)
        sys.exit(1)

    print("\n[SUCESSO] Quality Gate G_FRONTEND_LAYERS APROVADO — Camadas do Frontend 100% isoladas!")
    print("=" * 72)
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
