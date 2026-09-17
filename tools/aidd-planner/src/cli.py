# -*- coding: utf-8 -*-
"""
CLI Oficial do aidd-planner
Uso:
  python -m aidd_planner.cli init --fluxo <1|2|3> --nome <nome> --pasta <destino>
  python -m aidd_planner.cli validate <caminho_plano.json>
  python -m aidd_planner.cli export <caminho_plano.json> --formato factory --saida <arquivo>
  python -m aidd_planner.cli audit [pasta]
"""

import argparse
import json
import os
import sys
from typing import List, Optional

try:
    from .core.planner_engine import (
        PlannerValidationError,
        validar_plano,
        gerar_template_plano,
        exportar_para_fluxo_factory,
    )
except ImportError:
    from src.core.planner_engine import (
        PlannerValidationError,
        validar_plano,
        gerar_template_plano,
        exportar_para_fluxo_factory,
    )

MAPA_FLUXOS = {
    "1": "fluxo_01_generator",
    "2": "fluxo_02_factory",
    "3": "fluxo_03_bridge",
    "fluxo_01_generator": "fluxo_01_generator",
    "fluxo_02_factory": "fluxo_02_factory",
    "fluxo_03_bridge": "fluxo_03_bridge",
}


def cmd_init(args: argparse.Namespace) -> int:
    fluxo_chave = str(args.fluxo).lower()
    fluxo_alvo = MAPA_FLUXOS.get(fluxo_chave)
    if not fluxo_alvo:
        print(f"[ERRO] Fluxo inválido: '{args.fluxo}'. Use 1 (generator), 2 (factory) ou 3 (bridge).", file=sys.stderr)
        return 1

    nome = args.nome or "Meu Projeto AIDD"
    slug = args.slug or nome.lower().replace(" ", "-").replace("_", "-")
    descricao = args.descricao or f"Projeto de alta robustez desenvolvido via {fluxo_alvo} no ecossistema AIDD."
    dominio = args.dominio or "logistica"
    pasta_destino = os.path.abspath(args.pasta or ".")

    os.makedirs(pasta_destino, exist_ok=True)
    arquivo_saida = os.path.join(pasta_destino, "PLANNER.json")

    if os.path.exists(arquivo_saida) and not args.force:
        print(f"[ERRO] O arquivo '{arquivo_saida}' já existe. Use --force para sobrescrever.", file=sys.stderr)
        return 1

    plano = gerar_template_plano(
        fluxo_alvo=fluxo_alvo,
        projeto_nome=nome,
        slug=slug,
        descricao=descricao,
        dominio=dominio,
    )

    valido, erros = validar_plano(plano)
    if not valido:
        print("[ERRO FATAL] O template gerado violou as regras do schema:", file=sys.stderr)
        for e in erros:
            print(f"  - {e}", file=sys.stderr)
        return 1

    with open(arquivo_saida, "w", encoding="utf-8") as f:
        json.dump(plano, f, indent=2, ensure_ascii=False)

    print("=" * 72)
    print(" [aidd-planner] PLANNER.json GERADO COM SUCESSO")
    print("=" * 72)
    print(f" Projeto:     {nome} ({slug})")
    print(f" Fluxo Alvo:  {fluxo_alvo}")
    print(f" Destino:     {arquivo_saida}")
    print(" Status:      100% Conforme (Schema + Quarteto Sine Qua Non + SDD/BDD)")
    print("=" * 72)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    caminho = os.path.abspath(args.arquivo)
    if not os.path.isfile(caminho):
        print(f"[ERRO] Arquivo de plano não encontrado: '{caminho}'", file=sys.stderr)
        return 1

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            plano = json.load(f)
    except Exception as e:
        print(f"[ERRO] Falha ao decodificar JSON em '{caminho}': {e}", file=sys.stderr)
        return 1

    valido, erros = validar_plano(plano)
    if not valido:
        print("=" * 72, file=sys.stderr)
        print(f" [aidd-planner] PLANO INVÁLIDO: {len(erros)} inconsistência(s) encontrada(s)", file=sys.stderr)
        print("=" * 72, file=sys.stderr)
        for e in erros:
            print(f"  [X] {e}", file=sys.stderr)
        print("=" * 72, file=sys.stderr)
        return 1

    print("=" * 72)
    print(f" [aidd-planner] PLANO VÁLIDO: {caminho}")
    print(f" Fluxo:   {plano['meta']['fluxo_alvo']}")
    print(f" Domínio: {plano['meta']['dominio']}")
    print(" Status:  PASS (100% Conforme)")
    print("=" * 72)
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    caminho = os.path.abspath(args.arquivo)
    if not os.path.isfile(caminho):
        print(f"[ERRO] Arquivo de plano não encontrado: '{caminho}'", file=sys.stderr)
        return 1

    with open(caminho, "r", encoding="utf-8") as f:
        plano = json.load(f)

    formato = args.formato.lower()
    if formato == "factory":
        try:
            resultado = exportar_para_fluxo_factory(plano)
        except PlannerValidationError as e:
            print(f"[ERRO] Não foi possível exportar para factory: {e}", file=sys.stderr)
            return 1

        saida_caminho = os.path.abspath(args.saida or "plano_factory.json")
        with open(saida_caminho, "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        print(f"[aidd-planner] Exportado com sucesso para aidd-factory: {saida_caminho}")
        return 0
    else:
        print(f"[ERRO] Formato de exportação não suportado: '{formato}'", file=sys.stderr)
        return 1


def cmd_audit(args: argparse.Namespace) -> int:
    """Executa os Quality Gates do aidd-planner."""
    planner_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gates_dir = os.path.join(planner_dir, "gates")

    import subprocess
    gates = [
        "G_PLANNER_SCHEMA.py",
        "G_PLANNER_SINE_QUA_NON.py",
        "G_PLANNER_COERENCIA_FLUXO.py"
    ]
    falhas = 0
    print("=" * 72)
    print(" [aidd-planner] Executando Quality Gates de Planejamento")
    print("=" * 72)

    alvo = args.pasta or os.getcwd()
    for g in gates:
        gate_path = os.path.join(gates_dir, g)
        if not os.path.isfile(gate_path):
            print(f"  - {g:<35} [ERRO: Gate não encontrado]")
            falhas += 1
            continue

        res = subprocess.run([sys.executable, gate_path, alvo], capture_output=True, text=True)
        status = "Passed" if res.returncode == 0 else "Failed"
        print(f"  - {g:<35} [{status}]")
        if res.returncode != 0:
            falhas += 1
            if res.stderr:
                print(f"    {res.stderr.strip()}")
            if res.stdout:
                print(f"    {res.stdout.strip()}")

    print("=" * 72)
    if falhas > 0:
        print(f" [aidd-planner] AUDITORIA REPROVADA ({falhas} falha(s))", file=sys.stderr)
        return 1
    print(" [aidd-planner] AUDITORIA APROVADA (100% PASS)")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="aidd-planner",
        description="AIDD-Planner: Motor Canônico de Planejamento e Combustão Primária da Tríade AIDD"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcomando init
    p_init = subparsers.add_parser("init", help="Gera um novo PLANNER.json canônico")
    p_init.add_argument("--fluxo", "-f", required=True, help="Fluxo alvo: 1 (generator), 2 (factory) ou 3 (bridge)")
    p_init.add_argument("--nome", "-n", default="Meu Projeto AIDD", help="Nome do projeto")
    p_init.add_argument("--slug", "-s", help="Identificador slug do projeto")
    p_init.add_argument("--descricao", "-d", help="Descrição do projeto")
    p_init.add_argument("--dominio", help="Domínio de negócio")
    p_init.add_argument("--pasta", "-p", default=".", help="Pasta de destino onde salvar PLANNER.json")
    p_init.add_argument("--force", action="store_true", help="Sobrescreve PLANNER.json se já existir")
    p_init.set_defaults(func=cmd_init)

    # Subcomando validate
    p_val = subparsers.add_parser("validate", help="Valida conformidade de um PLANNER.json")
    p_val.add_argument("arquivo", help="Caminho do arquivo PLANNER.json")
    p_val.set_defaults(func=cmd_validate)

    # Subcomando export
    p_exp = subparsers.add_parser("export", help="Exporta plano para formato específico de fluxo")
    p_exp.add_argument("arquivo", help="Caminho do arquivo PLANNER.json")
    p_exp.add_argument("--formato", required=True, choices=["factory"], help="Formato de destino")
    p_exp.add_argument("--saida", "-o", help="Caminho do arquivo exportado")
    p_exp.set_defaults(func=cmd_export)

    # Subcomando audit
    p_aud = subparsers.add_parser("audit", help="Executa os Quality Gates do aidd-planner")
    p_aud.add_argument("pasta", nargs="?", default=".", help="Pasta do projeto a auditar")
    p_aud.set_defaults(func=cmd_audit)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
