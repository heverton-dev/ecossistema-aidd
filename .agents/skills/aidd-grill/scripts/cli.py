# -*- coding: utf-8 -*-
"""
CLI determinística para validação e consolidação de aidd-grill (Ticket 1 / D2 / DoD 1).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import parser as grill_parser
import motor as grill_motor
import isolamento as grill_isolamento
import observabilidade as grill_observabilidade
import handoff as grill_handoff
import fallback as grill_fallback


def validar_arquivo(caminho: str) -> int:
    p = Path(caminho)
    if not p.exists():
        print(f"Erro: Arquivo '{caminho}' não encontrado.", file=sys.stderr)
        return 1

    texto = p.read_text(encoding="utf-8")
    perguntas, erros_parse = grill_parser.parsear_rodada_socratica(texto)

    if erros_parse:
        print("[FALHA] Validação estrutural rejeitou a rodada socrática:")
        for e in erros_parse:
            print(f" - {e}")
        return 1

    resumo, erros_motor = grill_motor.validar_perguntas_socromaticas(perguntas)
    if erros_motor:
        print("[FALHA] Validação de recomendações e justificativas rejeitou a rodada:")
        for e in erros_motor:
            print(f" - {e}")
        return 1

    print(f"[OK] Rodada socrática válida: {len(perguntas)} perguntas numeradas com recomendações justificadas.")
    return 0


def consolidar_rodada(caminho: str, output: str | None = None, headless: bool = False) -> int:
    p = Path(caminho)
    if not p.exists():
        print(f"Erro: Arquivo '{caminho}' não encontrado.", file=sys.stderr)
        return 1

    texto = p.read_text(encoding="utf-8")
    if headless:
        bloco, premissas, avisos = grill_fallback.sintetizar_premissas_headless(texto)
        print(bloco)
        return 0

    perguntas, erros_parse = grill_parser.parsear_rodada_socratica(texto)
    if erros_parse:
        print(f"[FALHA] Erro de parsing: {erros_parse}", file=sys.stderr)
        return 1

    resumo, erros_motor = grill_motor.validar_perguntas_socromaticas(perguntas)
    if erros_motor:
        print(f"[FALHA] Erro de justificativa: {erros_motor}", file=sys.stderr)
        return 1

    rastreador = grill_observabilidade.RastreadorGrill()
    metricas = rastreador.analisar_rodada(perguntas, resumo)

    if output:
        manager = grill_isolamento.GrillWorktreeManager(Path.cwd())
        try:
            manager.validar_caminho_escrita(output)
        except grill_isolamento.SandboxViolationError as sve:
            print(f"[FALHA] {sve}", file=sys.stderr)
            return 1

        sucesso = grill_handoff.gerar_handoff_grill(perguntas, resumo, output)
        if not sucesso:
            print("[FALHA] Não foi possível gerar o handoff assinado.", file=sys.stderr)
            return 1
        print(f"[OK] Handoff de premissas assinado com sucesso em: {output}")

    print(f"[OK] Consolidação finalizada com sucesso ({metricas['tempo_processamento_ms']}ms).")
    return 0


def exportar_rodada(caminho: str, output: str) -> int:
    return consolidar_rodada(caminho, output)


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    arg_parser = argparse.ArgumentParser(description="CLI determinística de validação de aidd-grill")
    sub = arg_parser.add_subparsers(dest="subcomando", required=True)

    p_val = sub.add_parser("validar", help="Valida conformidade de perguntas numeradas e recomendações justificadas")
    p_val.add_argument("--arquivo", required=True, help="Arquivo markdown com a rodada socrática")

    p_cons = sub.add_parser("consolidar", help="Consolida premissas e gera telemetria")
    p_cons.add_argument("--arquivo", required=True, help="Arquivo markdown com a rodada socrática")
    p_cons.add_argument("--output", default=None, help="Destino do manifesto assinado JSON (opcional)")
    p_cons.add_argument("--headless", action="store_true", help="Ativa modo fallback autônomo")

    p_exp = sub.add_parser("exportar", help="Exporta premissas consolidadas e assinadas em JSON")
    p_exp.add_argument("--arquivo", required=True, help="Arquivo markdown com a rodada socrática")
    p_exp.add_argument("--output", required=True, help="Destino JSON")

    parsed = arg_parser.parse_args(args)

    if parsed.subcomando == "validar":
        return validar_arquivo(parsed.arquivo)
    elif parsed.subcomando == "consolidar":
        return consolidar_rodada(parsed.arquivo, parsed.output, parsed.headless)
    elif parsed.subcomando == "exportar":
        return exportar_rodada(parsed.arquivo, parsed.output)

    return 1


if __name__ == "__main__":
    sys.exit(main())
