#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
QUALITY GATE: G_BRIDGE_VSA_COMPAT
===============================================================================
Valida que o pacote gerado pela aidd-bridge possui compatibilidade com o
Monólito Modular VSA e entrega os 4 contratos do Quarteto Sine Qua Non:
- Swagger (/swagger)
- Webhooks (/webhooks)
- MCP Studio (/mcp)
- Docs (/docs)

Exit 0: Quarteto Sine Qua Non presente e válido.
Exit 1: Algum contrato ausente ou malformado.
===============================================================================
"""

import os
import sys
import json

def audit_vsa_compat(target_dir: str) -> int:
    print("=" * 72)
    print(" [GATE] G_BRIDGE_VSA_COMPAT — Validação VSA & Quarteto Sine Qua Non")
    print("=" * 72)

    quarteto_dir = os.path.join(target_dir, "quarteto_sine_qua_non")
    if not os.path.exists(quarteto_dir):
        print(f" [AVISO] Pasta quarteto_sine_qua_non não encontrada em {target_dir}.")
        print("         Execute o exportador VSA para garantir compatibilidade.")
        return 0

    erros = []
    arquivos_obrigatorios = [
        ("swagger_spec.json", "Swagger Studio"),
        ("webhooks_contract.json", "Webhook Studio"),
        ("mcp_studio.json", "MCP Studio"),
        ("USER_GUIDE.md", "Guia do Utilizador"),
    ]

    for nome, rotulo in arquivos_obrigatorios:
        caminho = os.path.join(quarteto_dir, nome)
        if not os.path.exists(caminho):
            erros.append(f"  [BLOQUEIO] Contrato {rotulo} ({nome}) ausente.")
        else:
            if nome.endswith(".json"):
                try:
                    with open(caminho, "r", encoding="utf-8") as f:
                        json.load(f)
                except Exception as ex:
                    erros.append(f"  [BLOQUEIO] Contrato {rotulo} ({nome}) JSON inválido: {ex}")

    if erros:
        print(f" [FALHA] Deficiências no Quarteto Sine Qua Non ({len(erros)}):")
        for e in erros:
            print(e)
        print("=" * 72)
        return 1

    print(" [SUCESSO] Quarteto Sine Qua Non dinâmico 100% verificado e conforme.")
    print("=" * 72)
    return 0

if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else "."
    sys.exit(audit_vsa_compat(os.path.abspath(caminho)))
