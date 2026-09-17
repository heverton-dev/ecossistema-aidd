# -*- coding: utf-8 -*-
"""
AIDD-Factory — Pipeline Orchestrator (CLI Click).

Orquestra TODAS as 9 fases do factory:
  Fase 1: Analisador (le PLANO-INFRAESTRUTURA -> factory_analysis.json)
  Fase 2: Gateway (LLM -> src/gateway/*.py)
  Fase 3: Frontend (LLM -> frontend/ Next.js)
  Fase 4: Compose Unificado (merge templates -> docker-compose.yml)
  Fase 5: Init DB (bancos_logicos -> init-multiple-databases.sh)
  Fase 6: Env (.env per service)
  Fase 7: Webhooks (LLM -> webhooks/)
  Fase 8: Swagger (deterministico -> openapi.json + README.md)
  Fase 9: Validacao Cross-Service (pass/fail)

Uso:
  python scripts/pipeline_factory.py --plano <PLANO-INFRAESTRUTURA.json> --pasta <destino>
  python ecossistema.py factory --plano <path> --pasta <dest>
"""
import click
import json
import os
import sys
from datetime import datetime, timezone

_FACTORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "src"))
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "scripts", "phases"))
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "..", "..", "componentes", "compartilhado", "src-core"))

from core.result import Result
from core.escritor_atomico import escrever_json_atomico

# Importar fases
from importlib import import_module as _imod
_mod_analisador = _imod("01_analisador")
_mod_compose = _imod("04_compose")
_mod_init_db = _imod("05_init_db")
_mod_env = _imod("06_env")
_mod_validacao = _imod("09_integracao")

# Engines LLM (import preguicoso — so carrega se fases LLM habilitadas)
_gateway_gen = None
_frontend_gen = None
_swagger_gen = None


def _timestamp_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _carregar_plano(caminho: str) -> Result:
    """Carrega e valida PLANO-INFRAESTRUTURA.json."""
    if not os.path.isfile(caminho):
        return Result.fail(
            f"Arquivo nao encontrado: {caminho}",
            codigo="PLANO_NAO_ENCONTRADO",
        )
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return Result.fail(
            f"Erro ao ler plano: {exc}",
            codigo="PLANO_JSON_INVALID",
        )

    # Validar contrato
    from contrato_factory import validar_plano_factory
    res = validar_plano_factory(dados)
    if not res.sucesso:
        return res
    return Result.ok(dados)


def _salvar_artefato(pasta: str, nome: str, dados) -> str:
    """Salva artefato no diretorio de saida. Retorna caminho."""
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, nome)
    if isinstance(dados, dict) or isinstance(dados, list):
        escrever_json_atomico(caminho, dados)
    else:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(dados)
    return caminho


def executar_pipeline(plano_path: str, pasta_destino: str, incluir_llm: bool = True) -> int:
    """Executa o pipeline COMPLETO do factory (9 fases).

    Args:
        plano_path: Caminho para PLANO-INFRAESTRUTURA.json
        pasta_destino: Diretorio de saida
        incluir_llm: Se True, executa fases 2, 3, 7 (LLM). Se False, apenas deterministicas.
    """
    total_fases = 9 if incluir_llm else 6
    fase_num = 0

    print("=" * 72)
    print(f" [AIDD-Factory] Pipeline Completo ({total_fases} fases)")
    print(f" Modo: {'COMPLETO (inclui LLM)' if incluir_llm else 'DETERMINISTICO (sem LLM)'}")
    print("=" * 72)

    # Pre-flight: Carregar plano
    print(f"\n[Pre-flight] Carregando PLANO-INFRAESTRUTURA.json...")
    res_plano = _carregar_plano(plano_path)
    if not res_plano.sucesso:
        print(f"  [ERRO] {res_plano.codigo}: {res_plano.erro}")
        return 1
    plano = res_plano.valor

    nicho = plano["fase_1_intake"]["saida"]
    ferramentas = plano["fase_2_curadoria"]["saida"]["ferramentas"]
    sizing = plano["fase_3_sizing"]["saida"]

    print(f"  [OK] Nicho: {nicho['nicho_nome_exibicao']} ({nicho['nicho_slug']})")
    print(f"  [OK] {len(ferramentas)} ferramenta(s)")
    print(f"  [OK] VPS: {sizing['vps']['vcpu']}vCPU / {sizing['vps']['ram_gb']}GB RAM")

    artefatos = []
    erros = 0

    # Fase 1: Analisador
    fase_num += 1
    print(f"\n[{fase_num}/{total_fases}] Fase 1 - Analisador Deterministico...")
    res_analysis = _mod_analisador.analisar(plano)
    if res_analysis.sucesso:
        caminho = _salvar_artefato(pasta_destino, "factory_analysis.json", res_analysis.valor)
        artefatos.append({"tipo": "analysis", "caminho": caminho, "status": "gerado"})
        print(f"  [OK] factory_analysis.json gerado")
    else:
        artefatos.append({"tipo": "analysis", "caminho": "", "status": "erro", "detalhes": res_analysis.erro})
        print(f"  [ERRO] {res_analysis.codigo}: {res_analysis.erro}")
        erros += 1

    # Fase 2: Gateway (LLM)
    if incluir_llm and res_analysis.sucesso:
        fase_num += 1
        print(f"\n[{fase_num}/{total_fases}] Fase 2 - Gateway FastAPI (LLM)...")
        try:
            from core.gateway_generator import gerar_gateway
            res_gw = gerar_gateway(res_analysis.valor, pasta_destino)
            if res_gw.sucesso:
                artefatos.append({"tipo": "gateway", "caminho": os.path.join(pasta_destino, "src", "gateway"), "status": "gerado"})
                print(f"  [OK] Gateway FastAPI gerado ({len(res_gw.valor)} arquivos)")
            else:
                artefatos.append({"tipo": "gateway", "caminho": "", "status": "erro", "detalhes": res_gw.erro})
                print(f"  [ERRO] {res_gw.codigo}: {res_gw.erro}")
                erros += 1
        except Exception as exc:
            artefatos.append({"tipo": "gateway", "caminho": "", "status": "erro", "detalhes": str(exc)})
            print(f"  [ERRO] Gateway: {exc}")
            erros += 1

    # Fase 3: Frontend (LLM)
    if incluir_llm and res_analysis.sucesso:
        fase_num += 1
        print(f"\n[{fase_num}/{total_fases}] Fase 3 - Frontend Next.js (LLM)...")
        try:
            from core.frontend_generator import gerar_frontend
            res_fe = gerar_frontend(res_analysis.valor, pasta_destino)
            if res_fe.sucesso:
                artefatos.append({"tipo": "frontend", "caminho": os.path.join(pasta_destino, "frontend"), "status": "gerado"})
                print(f"  [OK] Frontend Next.js gerado ({len(res_fe.valor)} arquivos)")
            else:
                artefatos.append({"tipo": "frontend", "caminho": "", "status": "erro", "detalhes": res_fe.erro})
                print(f"  [ERRO] {res_fe.codigo}: {res_fe.erro}")
                erros += 1
        except Exception as exc:
            artefatos.append({"tipo": "frontend", "caminho": "", "status": "erro", "detalhes": str(exc)})
            print(f"  [ERRO] Frontend: {exc}")
            erros += 1

    # Fase 4: Compose Unificado
    fase_num += 1
    print(f"\n[{fase_num}/{total_fases}] Fase 4 - Compose Unificado...")
    if res_analysis.sucesso:
        res_compose = _mod_compose.gerar_compose(res_analysis.valor, pasta_destino)
        if res_compose.sucesso:
            caminho = _salvar_artefato(pasta_destino, "docker-compose.yml", res_compose.valor)
            artefatos.append({"tipo": "compose", "caminho": caminho, "status": "gerado"})
            print(f"  [OK] docker-compose.yml gerado")
        else:
            artefatos.append({"tipo": "compose", "caminho": "", "status": "erro", "detalhes": res_compose.erro})
            print(f"  [ERRO] {res_compose.codigo}: {res_compose.erro}")
            erros += 1
    else:
        print("  [SKIP] Pulo por falta de analysis")

    # Fase 5: Init DB
    fase_num += 1
    print(f"\n[{fase_num}/{total_fases}] Fase 5 - Init DB Dinamico...")
    if res_analysis.sucesso:
        res_init = _mod_init_db.gerar_init_db(res_analysis.valor, pasta_destino)
        if res_init.sucesso:
            caminho = _salvar_artefato(pasta_destino, "init-multiple-databases.sh", res_init.valor)
            artefatos.append({"tipo": "init_db", "caminho": caminho, "status": "gerado"})
            print(f"  [OK] init-multiple-databases.sh gerado")
        else:
            artefatos.append({"tipo": "init_db", "caminho": "", "status": "erro", "detalhes": res_init.erro})
            print(f"  [ERRO] {res_init.codigo}: {res_init.erro}")
            erros += 1
    else:
        print("  [SKIP] Pulo por falta de analysis")

    # Fase 6: Env
    fase_num += 1
    print(f"\n[{fase_num}/{total_fases}] Fase 6 - Gerador de .env...")
    if res_analysis.sucesso:
        res_env = _mod_env.gerar_env(res_analysis.valor, pasta_destino)
        if res_env.sucesso:
            for env_info in res_env.valor:
                artefatos.append({"tipo": "env", "caminho": env_info["caminho"], "status": "gerado"})
            print(f"  [OK] {len(res_env.valor)} arquivo(s) .env gerado(s)")
        else:
            artefatos.append({"tipo": "env", "caminho": "", "status": "erro", "detalhes": res_env.erro})
            print(f"  [ERRO] {res_env.codigo}: {res_env.erro}")
            erros += 1
    else:
        print("  [SKIP] Pulo por falta de analysis")

    # Fase 7: Webhooks (LLM)
    if incluir_llm and res_analysis.sucesso:
        fase_num += 1
        print(f"\n[{fase_num}/{total_fases}] Fase 7 - Webhooks (LLM)...")
        try:
            # Webhook generation — stub deterministico por enquanto
            webhook_dir = os.path.join(pasta_destino, "webhooks")
            os.makedirs(webhook_dir, exist_ok=True)
            webhook_contrato = {
                "servicos": [
                    {"nome": f["nome"], "slug": f["nome"].lower().replace(" ", "-")}
                    for f in res_analysis.valor.get("ferramentas", [])
                ],
                "eventos": ["created", "updated", "deleted"],
            }
            _salvar_artefato(webhook_dir, "webhook_contrato.json", webhook_contrato)
            artefatos.append({"tipo": "webhooks", "caminho": webhook_dir, "status": "gerado"})
            print(f"  [OK] Webhook contrato gerado")
        except Exception as exc:
            artefatos.append({"tipo": "webhooks", "caminho": "", "status": "erro", "detalhes": str(exc)})
            print(f"  [ERRO] Webhooks: {exc}")
            erros += 1

    # Fase 8: Swagger/OpenAPI
    if res_analysis.sucesso:
        fase_num += 1
        print(f"\n[{fase_num}/{total_fases}] Fase 8 - Swagger/OpenAPI...")
        try:
            from core.swagger_generator import gerar_swagger
            res_sw = gerar_swagger(res_analysis.valor, pasta_destino)
            if res_sw.sucesso:
                artefatos.append({"tipo": "swagger", "caminho": pasta_destino, "status": "gerado"})
                print(f"  [OK] OpenAPI + README gerados ({len(res_sw.valor)} arquivos)")
            else:
                artefatos.append({"tipo": "swagger", "caminho": "", "status": "erro", "detalhes": res_sw.erro})
                print(f"  [ERRO] {res_sw.codigo}: {res_sw.erro}")
                erros += 1
        except Exception as exc:
            artefatos.append({"tipo": "swagger", "caminho": "", "status": "erro", "detalhes": str(exc)})
            print(f"  [ERRO] Swagger: {exc}")
            erros += 1

    # Fase 9: Validacao Cross-Service
    fase_num += 1
    print(f"\n[{fase_num}/{total_fases}] Fase 9 - Validacao Cross-Service...")
    res_val = _mod_validacao.validar_tudo(pasta_destino)
    if res_val.sucesso:
        artefatos.append({"tipo": "validacao", "caminho": pasta_destino, "status": "gerado"})
        print(f"  [OK] Validacao cross-service: todos os checks passaram")
    else:
        artefatos.append({"tipo": "validacao", "caminho": "", "status": "erro", "detalhes": res_val.erro})
        print(f"  [ERRO] {res_val.codigo}: {res_val.erro}")
        erros += 1

    # FACTORY_OUTPUT.json
    factory_output = {
        "versao": "1.0.0",
        "gerado_em": _timestamp_iso(),
        "nicho": {
            "slug": nicho["nicho_slug"],
            "nome_exibicao": nicho["nicho_nome_exibicao"],
        },
        "artefatos": artefatos,
        "resumo": {
            "total_artefatos": len(artefatos),
            "gerados": len([a for a in artefatos if a["status"] == "gerado"]),
            "erros": erros,
        },
    }
    output_path = _salvar_artefato(pasta_destino, "FACTORY_OUTPUT.json", factory_output)

    # Resumo final
    print()
    print("=" * 72)
    print(" [AIDD-Factory] Pipeline Concluido")
    print(f" Artefatos: {factory_output['resumo']['gerados']}/{factory_output['resumo']['total_artefatos']} gerados")
    if erros:
        print(f" Erros: {erros}")
    print(f" Saida: {pasta_destino}")
    print(f" Output: {output_path}")
    print("=" * 72)

    return 1 if erros else 0


# ── CLI ──

CONTEXT = {"help_option_names": ["-h", "--help"]}


@click.command("factory", context_settings=CONTEXT)
@click.option("--plano", required=True, help="Caminho para PLANO-INFRAESTRUTURA.json")
@click.option("--pasta", required=True, help="Diretorio de saida para artefatos")
@click.option("--sem-llm", is_flag=True, default=False, help="Modo deterministico (sem fases LLM)")
def cli(plano, pasta, sem_llm):
    """AIDD-Factory — Gerador de Aplicacao e Integracao."""
    os.makedirs(pasta, exist_ok=True)
    codigo = executar_pipeline(plano, pasta, incluir_llm=not sem_llm)
    raise SystemExit(codigo)


if __name__ == "__main__":
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")
    cli()
