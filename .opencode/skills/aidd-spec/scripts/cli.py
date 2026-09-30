# -*- coding: utf-8 -*-
"""
CLI determinística para validação e compilação de aidd-spec (Ticket 1 / D2 / DoD 1).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import parser as spec_parser
import motor as spec_motor
import isolamento as spec_isolamento
import observabilidade as spec_observabilidade
import handoff as spec_handoff


def validar_arquivo(caminho: str) -> int:
    p = Path(caminho)
    if not p.exists():
        print(f"Erro: Arquivo '{caminho}' não encontrado.", file=sys.stderr)
        return 1

    texto = p.read_text(encoding="utf-8")
    secoes, erros_parse = spec_parser.parsear_especificacao_markdown(texto)

    if erros_parse:
        print("[FALHA] Validação estrutural rejeitou a especificação:")
        for e in erros_parse:
            print(f" - {e}")
        return 1

    resumo, erros_motor = spec_motor.validar_regras_especificacao(secoes)
    if erros_motor:
        print("[FALHA] Validação de critérios e regras rejeitou a especificação:")
        for e in erros_motor:
            print(f" - {e}")
        return 1

    print(f"[OK] Especificação válida: {resumo['total_invariantes']} invariantes e {resumo['total_criterios_binarios']} critérios binários validados.")
    return 0


def compilar_especificacao(caminho: str, output: str | None = None) -> int:
    p = Path(caminho)
    if not p.exists():
        print(f"Erro: Arquivo '{caminho}' não encontrado.", file=sys.stderr)
        return 1

    texto = p.read_text(encoding="utf-8")
    secoes, erros_parse = spec_parser.parsear_especificacao_markdown(texto)
    if erros_parse:
        print(f"[FALHA] Erro de parsing: {erros_parse}", file=sys.stderr)
        return 1

    resumo, erros_motor = spec_motor.validar_regras_especificacao(secoes)
    if erros_motor:
        print(f"[FALHA] Erro de regras: {erros_motor}", file=sys.stderr)
        return 1

    rastreador = spec_observabilidade.RastreadorSpec()
    metricas = rastreador.analisar_especificacao(secoes, resumo)

    if output:
        manager = spec_isolamento.SpecWorktreeManager(Path.cwd())
        try:
            manager.validar_caminho_escrita(output)
        except spec_isolamento.SandboxViolationError as sve:
            print(f"[FALHA] {sve}", file=sys.stderr)
            return 1

        sucesso = spec_handoff.gerar_handoff_spec(secoes, resumo, output)
        if not sucesso:
            print("[FALHA] Não foi possível gerar o handoff assinado.", file=sys.stderr)
            return 1
        print(f"[OK] Handoff compilado e assinado com sucesso em: {output}")

    print(f"[OK] Compilação finalizada com sucesso ({metricas['tempo_processamento_ms']}ms).")
    return 0


def exportar_especificacao(caminho: str, output: str) -> int:
    return compilar_especificacao(caminho, output)


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    arg_parser = argparse.ArgumentParser(description="CLI determinística de validação de aidd-spec")
    sub = arg_parser.add_subparsers(dest="subcomando", required=True)

    p_val = sub.add_parser("validar", help="Valida conformidade das 5 seções canônicas e critérios binários")
    p_val.add_argument("--arquivo", required=True, help="Arquivo markdown com a especificação")

    p_comp = sub.add_parser("compilar", help="Compila especificação e gera manifesto com telemetria")
    p_comp.add_argument("--arquivo", required=True, help="Arquivo markdown com a especificação")
    p_comp.add_argument("--output", default=None, help="Destino do manifesto assinado JSON (opcional)")

    p_exp = sub.add_parser("exportar", help="Exporta especificação compilada e assinada em JSON")
    p_exp.add_argument("--arquivo", required=True, help="Arquivo markdown com a especificação")
    p_exp.add_argument("--output", required=True, help="Destino JSON")

    parsed = arg_parser.parse_args(args)

    if parsed.subcomando == "validar":
        return validar_arquivo(parsed.arquivo)
    elif parsed.subcomando in ("compilar", "exportar"):
        return compilar_especificacao(parsed.arquivo, parsed.output)

    return 1


if __name__ == "__main__":
    sys.exit(main())
