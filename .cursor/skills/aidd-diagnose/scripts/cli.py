# -*- coding: utf-8 -*-
"""
AIDD-Diagnose CLI: Subcomandos determinísticos para diagnosticar e registrar sintomas do ecossistema.
Padrão de delegação: espelha aidd-melhoria.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import re


def find_repo_root(start_path: Optional[Path] = None) -> Path:
    """Encontra a raiz do repositório procurando por ecossistema.py."""
    current = (start_path or Path(__file__)).resolve()
    candidates = [current] + list(current.parents)
    for parent in candidates:
        if (parent / "ecossistema.py").is_file():
            return parent
    return Path(__file__).resolve().parents[4]


REPO_ROOT = find_repo_root()


def slugificar(texto: str) -> str:
    """Converte texto para slug válido (ex: 'Meu Sintoma' -> 'meu-sintoma')."""
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9\s-]", "", texto)
    texto = re.sub(r"\s+", "-", texto)
    return texto


def obter_ultima_sessao() -> Optional[Path]:
    """Retorna o caminho da última sessão de diagnose criada."""
    diagnosticos_dir = REPO_ROOT / "docs" / "diagnosticos"
    if not diagnosticos_dir.exists():
        return None
    subdirs = sorted(diagnosticos_dir.glob("*_*"), reverse=True)
    return subdirs[0] if subdirs else None


def cmd_iniciar(sintoma: str) -> int:
    """Subcomando: iniciar --sintoma <texto>.

    Cria docs/diagnosticos/<YYYYMMDD>_<slug>/sessao.json com os dados iniciais.
    Retorna 0 se sucesso, 1 se erro.
    """
    if not sintoma:
        print("Erro: --sintoma é obrigatório")
        return 1

    # Cria diretório de diagnosticos com data e slug
    hoje = datetime.now()
    data_str = hoje.strftime("%Y%m%d")
    slug = slugificar(sintoma)[:30]  # Limita a 30 caracteres
    pasta_sessao = REPO_ROOT / "docs" / "diagnosticos" / f"{data_str}_{slug}"

    # Cria estrutura de diretórios
    pasta_sessao.mkdir(parents=True, exist_ok=True)

    # Estrutura da sessão
    sessao_data = {
        "sintoma": sintoma,
        "data_inicio": hoje.isoformat(),
        "fase_atual": 1,
        "fases_completadas": [1],
    }

    sessao_file = pasta_sessao / "sessao.json"
    try:
        with open(sessao_file, "w", encoding="utf-8") as f:
            json.dump(sessao_data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Sessão iniciada: {sessao_file}")
        return 0
    except Exception as exc:
        print(f"Erro ao criar sessão: {exc}")
        return 1


def cmd_fase(numero: int) -> int:
    """Subcomando: fase --numero <1-5>.

    Avança para a fase indicada, verificando se a fase anterior foi completada.
    Retorna 0 se sucesso, 1 se erro (ex: tentativa de pular fases).
    """
    if numero < 1 or numero > 5:
        print("Erro: --numero deve estar entre 1 e 5")
        return 1

    # Localia última sessão
    sessao_dir = obter_ultima_sessao()
    if not sessao_dir:
        print("Erro: Nenhuma sessão de diagnose encontrada. Execute 'diagnose iniciar --sintoma <texto>' primeiro.")
        return 1

    sessao_file = sessao_dir / "sessao.json"
    if not sessao_file.exists():
        print(f"Erro: Arquivo de sessão não encontrado: {sessao_file}")
        return 1

    # Lê o JSON
    try:
        with open(sessao_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        print(f"Erro ao ler sessão: {exc}")
        return 1

    # Valida se pode avançar
    fase_atual = data.get("fase_atual", 1)
    fases_completadas = data.get("fases_completadas", [])

    # Regra: só pode avançar se a fase anterior foi completada
    if numero != fase_atual and (numero - 1) not in fases_completadas:
        print(f"Erro: Não pode avançar para fase {numero}. Complete a fase {numero - 1} primeiro.")
        return 1

    # Se fase anterior foi completada, avança
    if numero != fase_atual:
        data["fase_atual"] = numero
        if numero not in fases_completadas:
            data["fases_completadas"] = sorted(set(fases_completadas + [numero]))

    try:
        with open(sessao_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Avançado para fase {numero}")
        return 0
    except Exception as exc:
        print(f"Erro ao atualizar sessão: {exc}")
        return 1


def main(args: Optional[List[str]] = None) -> int:
    """Entrypoint principal da CLI."""
    parser = argparse.ArgumentParser(
        prog="python ecossistema.py diagnose",
        description="CLI de Diagnose do Ecossistema AIDD"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Subcomandos disponíveis")

    # Subcomando: iniciar
    parser_iniciar = subparsers.add_parser("iniciar", help="Inicia uma nova sessão de diagnose")
    parser_iniciar.add_argument("--sintoma", required=True, help="Descrição do sintoma a diagnosticar")

    # Subcomando: fase
    parser_fase = subparsers.add_parser("fase", help="Avança para uma nova fase")
    parser_fase.add_argument("--numero", type=int, required=True, help="Número da fase (1-5)")

    # Parse
    parsed = parser.parse_args(args)

    if not parsed.subcommand:
        parser.print_help()
        return 0

    if parsed.subcommand == "iniciar":
        return cmd_iniciar(parsed.sintoma)
    elif parsed.subcommand == "fase":
        return cmd_fase(parsed.numero)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
