# -*- coding: utf-8 -*-
"""
CLI de Fallback e Despacho Modular (VSA).
Dimensão D2: Input e Gatilhos.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

RAIZ_PADRAO = Path(__file__).resolve().parents[1]
if str(RAIZ_PADRAO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PADRAO))

from scripts.validador_fractalidade_vsa import validar_fractalidade_slice
from docs.padroes.contratos.manifesto_modulos import validar_manifesto_modulos


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="modularizacao-vsa",
        description="CLI de inspeção e verificação de modularização VSA."
    )
    parser.add_argument(
        "--raiz",
        default=None,
        help="Caminho raiz do repositório (padrão: raiz do projeto)",
    )
    subparsers = parser.add_subparsers(dest="subcomando", help="Subcomandos disponíveis")

    subparsers.add_parser("inspect", help="Inspeciona a estrutura modular VSA.")
    subparsers.add_parser("verify", help="Verifica a integridade das fatias verticais VSA.")
    subparsers.add_parser("status", help="Exibe o status atual da arquitetura VSA.")
    subparsers.add_parser("reconcile", help="Gera o relatório de divergências entre tools e modulos.")
    subparsers.add_parser("index-subgraphs", help="Indexa todos os subgrafos federados no codebase-memory-mcp.")

    return parser


def obter_raiz(args_raiz: Optional[str]) -> Path:
    if args_raiz:
        return Path(args_raiz).resolve()
    return Path(__file__).resolve().parents[1]


def carregar_mapa_fatias(raiz: Path) -> dict:
    mapa_path = raiz / "modulos" / "04-nucleo-compartilhado" / "contracts" / "MAPA-FATIAS.json"
    if mapa_path.exists():
        try:
            return json.loads(mapa_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"fatias": {}}


def carregar_mapa_gates(raiz: Path) -> dict:
    mapa_path = raiz / "modulos" / "04-nucleo-compartilhado" / "contracts" / "MAPA-GATES.json"
    if mapa_path.exists():
        try:
            return json.loads(mapa_path.read_text(encoding="utf-8")).get("gates", {})
        except Exception:
            pass
    return {}


def comando_inspect(raiz: Path) -> int:
    print(f"[modularizacao-vsa] Inspecionando arquitetura VSA em: {raiz}")
    mapa_fatias = carregar_mapa_fatias(raiz)
    fatias = mapa_fatias.get("fatias", {})
    mapa_gates = carregar_mapa_gates(raiz)

    if not fatias:
        modulos_dir = raiz / "modulos"
        if modulos_dir.exists():
            for d in sorted(modulos_dir.iterdir()):
                if d.is_dir():
                    fatias[d.name] = {"caminho": f"modulos/{d.name}", "ferramentas": []}

    for nome, info in fatias.items():
        caminho_rel = info.get("caminho", "")
        caminho_abs = raiz / caminho_rel
        ferramentas = info.get("ferramentas", [])
        num_arquivos = sum(1 for _ in caminho_abs.rglob("*") if _.is_file()) if caminho_abs.exists() else 0
        num_gates = sum(1 for g, ginfo in mapa_gates.items() if ginfo.get("dono") == nome)
        print(f"  - Fatia: {nome}")
        print(f"    caminho: {caminho_rel}")
        print(f"    ferramentas: {len(ferramentas)} {ferramentas}")
        print(f"    arquivos: {num_arquivos}")
        print(f"    gates: {num_gates}")
    return 0


def comando_status(raiz: Path) -> int:
    mapa_fatias = carregar_mapa_fatias(raiz)
    fatias = mapa_fatias.get("fatias", {})
    mapa_gates = carregar_mapa_gates(raiz)

    total_fatias = len(fatias)
    total_gates = len(mapa_gates)
    modulos_dir = raiz / "modulos"
    macro_modulos = [d.name for d in modulos_dir.iterdir() if d.is_dir()] if modulos_dir.exists() else []

    print("[modularizacao-vsa] Status VSA:")
    print(f"  Macro-módulos canônicos: {len(macro_modulos)} ({', '.join(sorted(macro_modulos))})")
    print(f"  Fatias verticais cadastradas: {total_fatias}")
    print(f"  Quality Gates mapeados: {total_gates}")
    return 0


def comando_verify(raiz: Path) -> int:
    print(f"[modularizacao-vsa] Verificando integridade das fatias VSA em: {raiz}")
    erros: List[str] = []

    # 1. Validar manifesto de módulos
    contrato_manifesto = raiz / "docs" / "padroes" / "contratos" / "manifesto_modulos.json"
    if contrato_manifesto.exists():
        try:
            dados = json.loads(contrato_manifesto.read_text(encoding="utf-8"))
            validar_manifesto_modulos(dados)
        except Exception as e:
            erros.append(f"Manifesto de módulos inválido: {e}")
    else:
        # Se não houver arquivo json específico, valida existência dos 4 macro-módulos canônicos
        canonicos = {
            "01-governanca-e-qualidade",
            "02-triade-motores",
            "03-plataforma-e-entrega",
            "04-nucleo-compartilhado",
        }
        modulos_dir = raiz / "modulos"
        existentes = {d.name for d in modulos_dir.iterdir() if d.is_dir()} if modulos_dir.exists() else set()
        faltantes = canonicos - existentes
        if faltantes:
            erros.append(f"Macro-módulos canônicos ausentes: {sorted(list(faltantes))}")

    # 2. Validar fractalidade das fatias
    mapa_fatias = carregar_mapa_fatias(raiz)
    fatias = mapa_fatias.get("fatias", {})
    if fatias:
        for nome, info in fatias.items():
            caminho_slice = raiz / info.get("caminho", "")
            ok, errs = validar_fractalidade_slice(caminho_slice)
            if not ok:
                erros.extend([f"[{nome}] {err}" for err in errs])
    else:
        # Se não houver mapa_fatias, checar pastas em modulos
        modulos_dir = raiz / "modulos"
        if modulos_dir.exists():
            for d in modulos_dir.iterdir():
                if d.is_dir():
                    ok, errs = validar_fractalidade_slice(d)
                    if not ok:
                        erros.extend([f"[{d.name}] {err}" for err in errs])

    # 3. Executar G_MODULO_FRONTEIRA em modo bloqueio
    gate_fronteira = raiz / "modulos" / "04-nucleo-compartilhado" / "gates" / "G_MODULO_FRONTEIRA.py"
    if gate_fronteira.exists():
        res = subprocess.run(
            [sys.executable, str(gate_fronteira), "--modo", "bloqueio"],
            cwd=str(raiz),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if res.returncode != 0:
            erros.append(f"G_MODULO_FRONTEIRA reprovou com código {res.returncode}:\n{res.stdout}\n{res.stderr}")

    # 4. Executar G_COPIA_UNICA_VSA em modo bloqueio
    gate_copia = raiz / "modulos" / "04-nucleo-compartilhado" / "gates" / "G_COPIA_UNICA_VSA.py"
    if gate_copia.exists():
        res = subprocess.run(
            [sys.executable, str(gate_copia), "--modo", "bloqueio"],
            cwd=str(raiz),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if res.returncode != 0:
            erros.append(f"G_COPIA_UNICA_VSA reprovou com código {res.returncode}:\n{res.stdout}\n{res.stderr}")

    if erros:
        print("[modularizacao-vsa] [FALHA] Violações encontradas:")
        for erro in erros:
            print(f"  - {erro}")
        return 1

    print("[modularizacao-vsa] [SUCESSO] Todas as fatias verticais VSA estao integras.")
    return 0


def comando_index_subgraphs(raiz: Path) -> int:
    sys.path.insert(0, str(raiz / "componentes" / "compartilhado" / "src-core"))
    try:
        from subgrafos_federados import SubgrafoFederadoVSA
        fed = SubgrafoFederadoVSA(raiz_repo=str(raiz))
        print("[modularizacao-vsa] Indexando subgrafos federados VSA...")
        res = fed.indexar_todos(modo="fast")
        for dom, r in res.items():
            status = "OK" if r.get("sucesso") else f"FALHA: {r.get('erro') or r.get('stderr') or r.get('exit_code')}"
            print(f"  - {dom:<25} [{status}]")
        return 0 if all(r.get("sucesso") for r in res.values()) else 1
    except Exception as e:
        print(f"[modularizacao-vsa] Erro ao indexar subgrafos: {e}")
        return 1


def comando_reconcile(raiz: Path) -> int:
    try:
        from scripts.reconciliar_copias_vsa import main as reconciliar_main
        return reconciliar_main(["--raiz", str(raiz)])
    except Exception as e:
        print(f"[modularizacao-vsa] Erro ao executar reconciliação: {e}")
        return 1


def main(args: Optional[List[str]] = None) -> int:
    if args is None:
        args = sys.argv[1:]

    parser = criar_parser()
    if not args:
        parser.print_help()
        return 0

    try:
        parsed = parser.parse_args(args)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 0

    raiz = obter_raiz(parsed.raiz)

    if parsed.subcomando == "inspect":
        return comando_inspect(raiz)
    elif parsed.subcomando == "verify":
        return comando_verify(raiz)
    elif parsed.subcomando == "status":
        return comando_status(raiz)
    elif parsed.subcomando == "reconcile":
        return comando_reconcile(raiz)
    elif parsed.subcomando == "index-subgraphs":
        return comando_index_subgraphs(raiz)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
