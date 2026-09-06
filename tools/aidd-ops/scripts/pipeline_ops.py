# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops MVP — Orquestrador Principal do Pipeline (Fases 1-3)
=============================================================================
Roda as 3 fases (Intake → Curadoria → Sizing) em sequência, grava
PLANO-INFRAESTRUTURA.json no diretório de saída acumulando o estado
de cada fase, imprime um resumo legível ao usuário.

Uso:
  python scripts/pipeline_ops.py "<texto>" --pasta <destino>
  python scripts/pipeline_ops.py --nicho <slug> --pasta <destino>

Propaga códigos de erro estruturados das fases (não mascara Result.fail).
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional

# Garantir que src/ está no path para imports
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_TOOL_ROOT = os.path.dirname(_SCRIPTS_DIR)
sys.path.insert(0, os.path.join(_TOOL_ROOT, "src"))

from core.result import Result

# Importar as 3 fases
sys.path.insert(0, _SCRIPTS_DIR)
from phases import __init__ as _phases_init  # noqa: F401
sys.path.insert(0, os.path.join(_SCRIPTS_DIR, "phases"))
from importlib import import_module as _imod

_mod_intake = _imod("01_intake")
_mod_curadoria = _imod("02_curadoria")
_mod_sizing = _imod("03_sizing")


def _timestamp_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _gravar_plano(caminho_plano: str, plano: dict) -> None:
    """Grava o plano de infraestrutura em disco como JSON."""
    os.makedirs(os.path.dirname(caminho_plano) or ".", exist_ok=True)
    with open(caminho_plano, "w", encoding="utf-8") as f:
        json.dump(plano, f, indent=2, ensure_ascii=False)


def _imprimir_resumo(plano: dict) -> None:
    """Imprime resumo legível do plano gerado."""
    print()
    print("=" * 72)
    print(" [AIDD-Ops] Plano de Infraestrutura Gerado com Sucesso")
    print("=" * 72)

    # Fase 1
    f1 = plano.get("fase_1_intake", {})
    dados_f1 = f1.get("saida", {})
    print(f"\n  Fase 1 — Intake:")
    print(f"    Nicho: {dados_f1.get('nicho_nome_exibicao', '?')} ({dados_f1.get('nicho_slug', '?')})")

    # Fase 2
    f2 = plano.get("fase_2_curadoria", {})
    dados_f2 = f2.get("saida", {})
    ferramentas = dados_f2.get("ferramentas", [])
    print(f"\n  Fase 2 — Stack Selecionada ({len(ferramentas)} ferramentas):")
    for i, ferr in enumerate(ferramentas, 1):
        print(f"    {i}. {ferr.get('nome', '?')}")

    # Fase 3
    f3 = plano.get("fase_3_sizing", {})
    dados_f3 = f3.get("saida", {})
    vps = dados_f3.get("vps", {})
    bancos = dados_f3.get("bancos_logicos", [])
    print(f"\n  Fase 3 — Sizing da VPS:")
    print(f"    vCPU:  {vps.get('vcpu', '?')}")
    print(f"    RAM:   {vps.get('ram_gb', '?')} GB")
    print(f"    Disco: {vps.get('disco_gb', '?')} GB")

    if bancos:
        print(f"\n  Bancos Lógicos ({len(bancos)}):")
        for b in bancos:
            print(f"    - {b.get('nome_banco', '?')} (para {b.get('ferramenta', '?')})")
    else:
        print(f"\n  Bancos Lógicos: nenhum necessário")

    ferr_com = dados_f3.get("ferramentas_com_banco", [])
    ferr_sem = dados_f3.get("ferramentas_sem_banco", [])
    if ferr_com:
        print(f"\n  Ferramentas COM banco relacional: {', '.join(ferr_com)}")
    if ferr_sem:
        print(f"  Ferramentas SEM banco relacional: {', '.join(ferr_sem)}")

    # Fontes
    fontes = dados_f3.get("fontes_consultadas", [])
    fontes_oficiais = [f for f in fontes if f.get("requisitos_encontrados")]
    fontes_estimadas = [f for f in fontes if not f.get("requisitos_encontrados")]
    print(f"\n  Fontes consultadas: {len(fontes)} total ({len(fontes_oficiais)} com requisitos oficiais, "
          f"{len(fontes_estimadas)} com estimativas)")

    print()
    print(f"  Arquivo: PLANO-INFRAESTRUTURA.json")
    print("=" * 72)


def executar_pipeline(texto: str, pasta_destino: str, nicho_explicito: Optional = None) -> int:
    """Executa o pipeline completo das 3 fases.

    Returns:
        exit code: 0 = sucesso, 1 = falha.
    """
    caminho_plano = os.path.join(pasta_destino, "PLANO-INFRAESTRUTURA.json")
    plano: dict = {
        "versao": "1.0.0",
        "gerado_em": _timestamp_iso(),
        "pipeline": "aidd-ops-mvp-fases-1-3",
    }

    # ── Fase 1: Intake ──
    print("[Fase 1/3] Reconhecimento de Nicho...")
    resultado_f1 = _mod_intake.reconhecer_nicho(texto, nicho_explicito=nicho_explicito)
    if not resultado_f1.sucesso:
        plano["fase_1_intake"] = {
            "entrada": {"texto": texto, "nicho_explicito": nicho_explicito},
            "saida": None,
            "erro": resultado_f1.to_dict(),
            "timestamp": _timestamp_iso(),
        }
        _gravar_plano(caminho_plano, plano)
        print(f"  [ERRO] {resultado_f1.codigo}: {resultado_f1.erro}")
        if resultado_f1.detalhes:
            print(f"  Detalhes: {json.dumps(resultado_f1.detalhes, ensure_ascii=False)}")
        return 1

    dados_f1 = resultado_f1.valor
    nicho_slug = dados_f1["nicho_slug"]
    nicho_nome = dados_f1["nicho_nome_exibicao"]
    print(f"  [OK] Nicho: {nicho_nome} ({nicho_slug})")

    plano["fase_1_intake"] = {
        "entrada": {"texto": texto, "nicho_explicito": nicho_explicito},
        "saida": dados_f1,
        "erro": None,
        "timestamp": _timestamp_iso(),
    }

    # ── Fase 2: Curadoria ──
    print("[Fase 2/3] Curadoria da Stack...")
    resultado_f2 = _mod_curadoria.curar_stack(nicho_slug, nicho_nome)
    if not resultado_f2.sucesso:
        plano["fase_2_curadoria"] = {
            "entrada": {"nicho_slug": nicho_slug, "nicho_nome_exibicao": nicho_nome},
            "saida": None,
            "erro": resultado_f2.to_dict(),
            "timestamp": _timestamp_iso(),
        }
        _gravar_plano(caminho_plano, plano)
        print(f"  [ERRO] {resultado_f2.codigo}: {resultado_f2.erro}")
        return 1

    dados_f2 = resultado_f2.valor
    n_ferr = len(dados_f2.get("ferramentas", []))
    print(f"  [OK] {n_ferr} ferramenta(s) selecionada(s)")

    plano["fase_2_curadoria"] = {
        "entrada": {"nicho_slug": nicho_slug, "nicho_nome_exibicao": nicho_nome},
        "saida": dados_f2,
        "erro": None,
        "timestamp": _timestamp_iso(),
    }

    # ── Fase 3: Sizing ──
    print("[Fase 3/3] Dimensionamento de Recursos...")
    ferramentas = dados_f2.get("ferramentas", [])
    resultado_f3 = _mod_sizing.dimensionar(ferramentas)
    if not resultado_f3.sucesso:
        plano["fase_3_sizing"] = {
            "entrada": {"ferramentas": ferramentas},
            "saida": None,
            "erro": resultado_f3.to_dict(),
            "timestamp": _timestamp_iso(),
        }
        _gravar_plano(caminho_plano, plano)
        print(f"  [ERRO] {resultado_f3.codigo}: {resultado_f3.erro}")
        return 1

    dados_f3 = resultado_f3.valor
    vps = dados_f3.get("vps", {})
    print(f"  [OK] VPS: {vps.get('vcpu', '?')} vCPU / {vps.get('ram_gb', '?')} GB RAM / {vps.get('disco_gb', '?')} GB Disco")

    plano["fase_3_sizing"] = {
        "entrada": {"ferramentas": ferramentas},
        "saida": dados_f3,
        "erro": None,
        "timestamp": _timestamp_iso(),
    }

    # ── Gravar plano final ──
    _gravar_plano(caminho_plano, plano)

    # ── Resumo ──
    _imprimir_resumo(plano)
    return 0


def cmd_bootstrap(args_list):
    """Subcomando bootstrap: executa a sequencia fechada via SSHRunner."""
    from core.ssh_runner import SSHRunner

    parser = argparse.ArgumentParser(
        prog="pipeline_ops bootstrap",
        description="AIDD-Ops — Bootstrapping remoto determinístico de VPS via SSH (Gap 1)",
    )
    parser.add_argument("host", help="IP ou hostname do servidor VPS alvo")
    parser.add_argument("--user", default="root", help="Usuário SSH (default: root)")
    parser.add_argument("--port", type=int, default=22, help="Porta SSH (default: 22)")
    parser.add_argument("--key", default=None, help="Caminho da chave privada SSH (opcional)")
    parser.add_argument("--real", action="store_true", help="Executa contra o host real (padrão é --dry-run seguro)")
    args = parser.parse_args(args_list)

    dry_run = not args.real

    print("=" * 72)
    print(" [AIDD-Ops] Bootstrapping Remoto via SSHRunner")
    print(f" Alvo: {args.user}@{args.host}:{args.port} | Modo: {'DRY-RUN (Simulação)' if dry_run else 'EXECUÇÃO REAL'}")
    print("=" * 72)

    try:
        runner = SSHRunner(
            host=args.host,
            user=args.user,
            port=args.port,
            key_path=args.key,
            dry_run=dry_run,
        )
        res = runner.executar_bootstrap_completo()
        if res.sucesso:
            print(f"\n[SUCESSO] Bootstrap concluído ({len(res.valor)} etapas homologadas):")
            for item in res.valor:
                print(f"  - {item['operacao']:<20} -> exit 0 ({item['comando'][:50]}...)")
            print("=" * 72)
            return 0
        else:
            print(f"\n[ERRO] {res.codigo}: {res.erro}")
            if res.detalhes:
                print(f"Detalhes: {res.detalhes}")
            print("=" * 72)
            return 1
    except Exception as exc:
        print(f"\n[ERRO INESPERADO]: {exc}")
        return 1


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "bootstrap":
        sys.exit(cmd_bootstrap(sys.argv[2:]))

    parser = argparse.ArgumentParser(
        prog="pipeline_ops",
        description="AIDD-Ops MVP — Pipeline determinístico de 3 fases (Intake, Curadoria, Sizing)",
    )
    parser.add_argument(
        "texto",
        nargs="?",
        default=None,
        help="Texto livre descrevendo o nicho de mercado (ex: 'Clínica odontológica com agendamento')",
    )
    parser.add_argument(
        "--nicho",
        default=None,
        help="Slug explícito do nicho (bypass do reconhecimento por texto). "
             "Valores aceitos: clinicas, delivery, farmacias, b2b_industrial, energia_solar",
    )
    parser.add_argument(
        "--pasta",
        required=True,
        help="Diretório de destino para PLANO-INFRAESTRUTURA.json (será criado se não existir)",
    )
    args = parser.parse_args()

    # Validar: precisa ter texto OU --nicho
    if args.texto is None and args.nicho is None:
        parser.error("Forneça um texto posicional ou use --nicho <slug>")

    texto_entrada = args.texto or ""

    os.makedirs(args.pasta, exist_ok=True)

    exit_code = executar_pipeline(
        texto=texto_entrada,
        pasta_destino=args.pasta,
        nicho_explicito=args.nicho,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

