# -*- coding: utf-8 -*-
"""
G_FACTORY_ANALYSIS — Valida factory_analysis.json.

Verifica:
  1. JSON valido
  2. Campos obrigatorios presentes
  3. Pelo menos 1 ferramenta
  4. Pelo menos 1 bloco com compose existente
  5. VPS com recursos minimos
"""
import json
import sys
import os

_FACTORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _validar_analysis(caminho: str) -> list:
    """Valida factory_analysis.json."""
    problemas = []

    if not os.path.isfile(caminho):
        return [f"Arquivo nao encontrado: {caminho}"]

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except json.JSONDecodeError as exc:
        return [f"JSON invalido: {exc}"]

    # Campos obrigatorios
    for campo in ["nicho_slug", "nicho_nome_exibicao", "ferramentas", "blocos", "vps"]:
        if campo not in dados:
            problemas.append(f"Campo ausente: {campo}")

    # Ferramentas
    ferramentas = dados.get("ferramentas", [])
    if len(ferramentas) == 0:
        problemas.append("Nenhuma ferramenta listada")

    # Blocos
    blocos = dados.get("blocos", [])
    blocos_compose = [b for b in blocos if b.get("compose_existe")]
    if len(blocos_compose) == 0:
        problemas.append("Nenhum bloco com compose existente")

    # VPS
    vps = dados.get("vps", {})
    if vps.get("vcpu", 0) < 1:
        problemas.append("VPS com vcpu < 1")
    if vps.get("ram_gb", 0) < 0.5:
        problemas.append("VPS com ram < 0.5 GB")

    return problemas


def executar(caminho: str = None) -> int:
    """Executa o gate."""
    print("=" * 72)
    print(" [G_FACTORY_ANALYSIS] Validacao de factory_analysis.json")
    print("=" * 72)

    if caminho is None:
        caminho = os.path.join(_FACTORY_ROOT, "output", "factory_analysis.json")
    elif os.path.isdir(caminho):
        caminho = os.path.join(caminho, "factory_analysis.json")

    problemas = _validar_analysis(caminho)

    if problemas:
        print(f"\n[FALHA] {len(problemas)} problema(s):")
        for p in problemas:
            print(f"  - {p}")
        return 1

    print(f"\n[SUCESSO] {caminho} validado.")
    return 0


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(executar(path))
