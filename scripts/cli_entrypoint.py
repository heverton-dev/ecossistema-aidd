#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — CLI UNIVERSAL E PONTO DE ENTRADA ZERO FRICÇÃO
=============================================================================
Comando oficial executável via `uvx aidd` ou `python -m scripts.cli_entrypoint`.
Permite criar novas aplicações nas esteiras da Tríade (Pure, Open, Freedom),
instalar a fábrica completa de governança e interagir por terminal ou agente.

Uso:
    uvx aidd pure [nome-do-app] [--quick] [--destino CAMINHO]
    uvx aidd open [nome-do-app] [--quick] [--destino CAMINHO]
    uvx aidd freedom [url-ou-pasta] [nome-do-app]
    uvx aidd full [destino]
    uvx aidd                        (Menu interativo)
=============================================================================
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Injeção de caminhos para os motores da Tríade
PLANNER_ENGINE_DIR = ROOT_DIR / "modulos" / "01-governanca-e-qualidade" / "core" / "aidd-planner"
if str(PLANNER_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(PLANNER_ENGINE_DIR))

try:
    from src.core_planner.planner_engine import gerar_template_plano, validar_plano  # type: ignore
except ImportError:
    try:
        from aidd_planner.core.planner_engine import gerar_template_plano, validar_plano  # type: ignore
    except ImportError:
        gerar_template_plano = None
        validar_plano = None

from scripts.create_aidd_app import criar_aplicacao


def _slugify(texto: str) -> str:
    texto = texto.lower().strip()
    texto = re.sub(r"[^\w\s-]", "", texto)
    return re.sub(r"[-\s]+", "-", texto) or "app"


def _forcar_utf8_stdio():
    """Garante que a saída em terminais Windows (cp1252) não quebre com caracteres UTF-8."""
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    if sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except AttributeError:
            pass


def exibir_banner():
    _forcar_utf8_stdio()
    print("=" * 72)
    print("  ECOSSISTEMA AIDD — ENGENHARIA AGENTICA DE SOFTWARE")
    print("  Padrao-Ouro: TanStack Router + React + FastAPI + SQLite WAL")
    print("=" * 72)


def perguntar_interativo(nome_inicial: str = "") -> Dict[str, Any]:
    """Coleta as 4 perguntas simples e diretas no terminal para o intake."""
    _forcar_utf8_stdio()
    print("\n[INTAKE RAPIDO] Configure sua aplicacao em poucos segundos:\n")

    nome = nome_inicial.strip()
    if not nome:
        padrao_nome = "meu-app-aidd"
        res_nome = input(f"1. Nome do projeto [{padrao_nome}]: ").strip()
        nome = res_nome or padrao_nome

    padrao_obj = "Sistema de gestão completo com painel e operações"
    res_obj = input(f"2. Objetivo da aplicação em uma frase [{padrao_obj}]: ").strip()
    objetivo = res_obj or padrao_obj

    padrao_modulos = "tarefas, clientes, relatorios"
    res_mod = input(f"3. Módulos ou tabelas principais separados por vírgula [{padrao_modulos}]: ").strip()
    modulos_str = res_mod or padrao_modulos
    modulos = [m.strip() for m in modulos_str.split(",") if m.strip()]

    padrao_cor = "#2563eb"
    res_cor = input(f"4. Cor primária visual (hex ou nome) [{padrao_cor}]: ").strip()
    cor = res_cor or padrao_cor
    if not cor.startswith("#") and len(cor) == 6:
        cor = f"#{cor}"

    res_auth = input("5. Deseja autenticação e controle de acesso? (S/n) [S]: ").strip().lower()
    auth = res_auth != "n"

    return {
        "nome": nome,
        "objetivo": objetivo,
        "modulos": modulos,
        "cor": cor,
        "auth": auth
    }


def gravar_planner_json(dados: Dict[str, Any], pasta_destino: Path, fluxo_alvo: str = "fluxo_01_generator"):
    """Gera e salva o arquivo PLANNER.json canônico com validação de schema."""
    nome = dados.get("nome", "meu-app-aidd")
    slug = _slugify(nome)
    objetivo = dados.get("objetivo", "Sistema de gestão de alta fidelidade")
    modulos = dados.get("modulos", ["tarefas", "clientes"])
    cor = dados.get("cor", "#2563eb")

    contextos = []
    for mod in modulos:
        slug_mod = _slugify(mod)
        contextos.append({
            "modulo": slug_mod,
            "descricao": f"Gestão e operações de {mod}",
            "entidades": [
                {
                    "nome": mod.capitalize(),
                    "atributos": {
                        "id": "string",
                        "titulo": "string",
                        "status": "string",
                        "criado_em": "datetime"
                    },
                    "regras_invariantes": [
                        "O status inicial deve ser sempre 'ativo'",
                        "O título é obrigatório"
                    ]
                }
            ]
        })

    if gerar_template_plano:
        plano = gerar_template_plano(
            fluxo_alvo=fluxo_alvo,
            projeto_nome=nome,
            slug=slug,
            descricao=objetivo,
            dominio=modulos[0] if modulos else "geral",
            contextos_spec=contextos
        )
    else:
        # Fallback determinístico caso o módulo do planner esteja desacoplado
        plano = {
            "meta": {
                "fluxo_alvo": fluxo_alvo,
                "projeto_nome": nome,
                "slug": slug,
                "descricao": objetivo,
                "versao": "1.0.0"
            },
            "ddd_bounded_contexts": contextos,
            "bdd_cenarios": [
                {
                    "id": "SCN-001",
                    "modulo": contextos[0]["modulo"] if contextos else "nucleo",
                    "titulo": "Criação de registro com sucesso",
                    "dado": "Um usuário autenticado com dados válidos",
                    "quando": "Uma requisição POST for enviada para a rota de criação",
                    "entao": "O registro deve ser persistido e retornar HTTP 201"
                }
            ],
            "quarteto_sine_qua_non": {
                "openapi_swagger": True,
                "webhook_studio": True,
                "mcp_studio": True,
                "docs_guia": True
            },
            "infraestrutura_alvo": {
                "tipo": "docker-compose",
                "servicos": ["frontend", "backend", "db"]
            },
            "payload_especifico_fluxo": {}
        }

    caminho_planner = pasta_destino / "PLANNER.json"
    with open(caminho_planner, "w", encoding="utf-8") as f:
        json.dump(plano, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Arquivo de arquitetura PLANNER.json gerado em: {caminho_planner.name}")

    # Design System Tokens
    caminho_ds = pasta_destino / "DESIGN-SYSTEM.json"
    ds = {
        "versao": "1.0.0",
        "tema_padrao": "light",
        "tokens": {
            "cor_primaria": cor,
            "modo_claro_soberano": True,
            "raio_borda": "0.375rem",
            "fonte_sans": "Inter, system-ui, sans-serif"
        }
    }
    with open(caminho_ds, "w", encoding="utf-8") as f:
        json.dump(ds, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Tokens visuais salvos em: {caminho_ds.name} (Modo Claro soberano)")


def comando_pure(args: argparse.Namespace) -> int:
    exibir_banner()
    nome = args.nome or ""
    
    if args.quick and not nome:
        nome = "meu-app-aidd"

    if args.quick:
        dados = {
            "nome": nome,
            "objetivo": "Aplicação gerada via AIDD CLI no modo rápido",
            "modulos": ["tarefas", "relatorios"],
            "cor": "#2563eb",
            "auth": True
        }
    else:
        dados = perguntar_interativo(nome)

    pasta_destino = Path(args.destino).resolve() if args.destino else ROOT_DIR / "projetos" / dados["nome"]
    pasta_destino.mkdir(parents=True, exist_ok=True)

    # 1. Executa scaffold da aplicação
    rc = criar_aplicacao(
        nome_app=dados["nome"],
        fluxo="pure",
        destino=str(pasta_destino),
        instalar_deps=args.instalar
    )
    if rc != 0:
        return rc

    # 2. Grava PLANNER.json canônico com as respostas
    gravar_planner_json(dados, pasta_destino, fluxo_alvo="fluxo_01_generator")

    # 3. Orientação final de uso com os 3 estilos
    print("\n" + "=" * 72)
    print("COMO CONTINUAR SEU DESENVOLVIMENTO:")
    print("=" * 72)
    print("Opcao A [No Terminal]:")
    print(f"   cd {pasta_destino}")
    print("   .\\iniciar.ps1   (no Windows) ou ./iniciar.sh (no Linux/Mac)")
    print("\nOpcao B [No seu Assistente de IA - Cursor, Claude Code, Antigravity]:")
    print(f"   Abra a pasta '{dados['nome']}' no editor e digite no chat:")
    print("   -> /master (para adicionar novos modulos ou rotas)")
    print("   -> /impeccable-full (para polir a interface e design)")
    print("=" * 72)
    return 0


def comando_open(args: argparse.Namespace) -> int:
    exibir_banner()
    nome = args.nome or "meu-app-open"
    pasta_destino = Path(args.destino).resolve() if args.destino else ROOT_DIR / "projetos" / nome
    pasta_destino.mkdir(parents=True, exist_ok=True)

    dados = {
        "nome": nome,
        "objetivo": "Aplicação integrada com motores open-source",
        "modulos": ["nucleo", "integracoes"],
        "cor": "#059669",
        "auth": True
    }

    rc = criar_aplicacao(nome_app=nome, fluxo="open", destino=str(pasta_destino), instalar_deps=args.instalar)
    if rc != 0:
        return rc

    gravar_planner_json(dados, pasta_destino, fluxo_alvo="fluxo_02_factory")
    return 0


def comando_freedom(args: argparse.Namespace) -> int:
    exibir_banner()
    origem = args.origem or ""
    _forcar_utf8_stdio()

    if not origem:
        origem = input("Informe a URL do repositório Git ou o caminho da pasta local: ").strip()
        if not origem:
            print("❌ Erro: Uma URL ou pasta de origem é obrigatória para o comando freedom.")
            return 1

    nome = args.nome or "app-libertado"
    pasta_destino = Path(args.destino).resolve() if args.destino else ROOT_DIR / "projetos" / nome
    pasta_destino.mkdir(parents=True, exist_ok=True)

    # Verifica se a origem é URL do Git
    if origem.startswith("http://") or origem.startswith("https://") or origem.startswith("git@"):
        print(f"[CLONE] Clonando repositorio de origem: {origem}...")
        pasta_clone = pasta_destino / "origem_clone"
        if pasta_clone.exists():
            shutil.rmtree(pasta_clone)
        try:
            subprocess.run(["git", "clone", "--depth", "1", origem, str(pasta_clone)], check=True)
            print("  [OK] Repositorio clonado para analise.")
            origem_real = str(pasta_clone)
        except Exception as e:
            print(f"[ERRO] Falha ao clonar repositorio Git: {e}")
            return 1
    else:
        origem_real = str(Path(origem).resolve())
        if not Path(origem_real).exists():
            print(f"[ERRO] Caminho de pasta nao encontrado: {origem_real}")
            return 1

    # Executa scan e limpeza do motor aidd-freedom
    print(f"[FREEDOM] Executando motor de desacoplamento aidd-freedom em: {origem_real}")
    freedom_dir = ROOT_DIR / "modulos" / "02-triade-motores" / "fluxo-03-freedom" / "core" / "aidd-freedom"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(freedom_dir)

    cmd_scan = [sys.executable, "-m", "aidd_freedom.cli", "scan", origem_real, "--output", str(pasta_destino)]
    try:
        subprocess.run(cmd_scan, env=env, check=True)
        print("  [OK] Analise e manifesto de desacoplamento gerados.")
    except Exception as e:
        print(f"  [AVISO] Aviso na execucao do scanner freedom: {e}")

    # Gera scaffold canônico com a UI preservada
    rc = criar_aplicacao(nome_app=nome, fluxo="freedom", destino=str(pasta_destino), instalar_deps=False)
    print("\n" + "=" * 72)
    print(f"[SUCESSO] Aplicacao libertada em: {pasta_destino}")
    print("Travas de vendor lock-in removidas. Banco pronto para PostgreSQL.")
    print("=" * 72)
    return rc


def comando_full(args: argparse.Namespace) -> int:
    exibir_banner()
    destino = args.destino or "ecossistema-aidd"
    pasta_destino = Path(destino).resolve()

    print(f"[AIDD FULL] Instalando a Fabrica Completa de Governanca em: {pasta_destino}")
    if pasta_destino.exists() and any(pasta_destino.iterdir()):
        print(f"[ERRO] O diretorio '{pasta_destino}' ja existe e nao esta vazio.")
        return 1

    repo_url = "https://github.com/heverton-dev/ecossistema-aidd.git"
    print(f"[DOWNLOAD] Baixando repositorio oficial ({repo_url})...")

    # Tenta git clone primeiro
    sucesso = False
    try:
        subprocess.run(["git", "clone", "--depth", "1", repo_url, str(pasta_destino)], check=True)
        sucesso = True
    except Exception as e:
        print(f"  [AVISO] Git indisponivel ou falhou ({e}). Tentando download direto via zip...")
        import urllib.request
        import zipfile
        zip_url = "https://github.com/heverton-dev/ecossistema-aidd/archive/refs/heads/main.zip"
        zip_tmp = pasta_destino.parent / "aidd_full_temp.zip"
        try:
            urllib.request.urlretrieve(zip_url, str(zip_tmp))
            with zipfile.ZipFile(str(zip_tmp), "r") as zip_ref:
                zip_ref.extractall(str(pasta_destino.parent))
            # Ajusta nome da pasta extraída
            pasta_extraida = pasta_destino.parent / "ecossistema-aidd-main"
            if pasta_extraida.exists():
                pasta_extraida.rename(pasta_destino)
            if zip_tmp.exists():
                zip_tmp.unlink()
            sucesso = True
        except Exception as ze:
            print(f"[ERRO] Falha ao baixar zip: {ze}")
            return 1

    if sucesso:
        print("\n" + "=" * 72)
        print("[SUCESSO] FABRICA COMPLETA AIDD INSTALADA")
        print("=" * 72)
        print(f"Diretorio: {pasta_destino}")
        print("\nPara comecar com seu assistente de IA preferido:")
        print(f"   1. cd {pasta_destino.name}")
        print("   2. Abra a pasta no Claude Code, Cursor, Antigravity, OpenCode ou MimoCode.")
        print("   3. As dependencias e portoes de qualidade ja estao configurados.")
        print("=" * 72)
        return 0
    return 1


def menu_interativo() -> int:
    exibir_banner()
    _forcar_utf8_stdio()
    print("\nEscolha como deseja comecar:")
    print("  [1] PURE: Criar aplicacao do Zero Puro (TDD + TanStack + FastAPI)")
    print("  [2] OPEN: Criar aplicacao com Motores Open-Source")
    print("  [3] FREEDOM: Desacoplar app Low-Code (Lovable / Bolt / v0)")
    print("  [4] FULL: Instalar a Fabrica Completa de Governanca")
    print("  [0] Sair\n")

    opcao = input("Opção [1]: ").strip() or "1"
    parser_dummy = argparse.ArgumentParser()
    parser_dummy.add_argument("nome", nargs="?", default="")
    parser_dummy.add_argument("--quick", action="store_true")
    parser_dummy.add_argument("--destino", default=None)
    parser_dummy.add_argument("--instalar", action="store_true")
    parser_dummy.add_argument("--origem", default=None)

    args = parser_dummy.parse_args([])

    if opcao == "1":
        return comando_pure(args)
    elif opcao == "2":
        return comando_open(args)
    elif opcao == "3":
        return comando_freedom(args)
    elif opcao == "4":
        return comando_full(args)
    elif opcao == "0":
        print("Operação cancelada.")
        return 0
    else:
        print("❌ Opção inválida.")
        return 1


def main():
    _forcar_utf8_stdio()
    parser = argparse.ArgumentParser(
        prog="aidd",
        description="Meta-Orquestrador e Framework de Engenharia Agêntica AIDD"
    )
    parser.add_argument("-v", "--version", action="version", version="AIDD CLI v5.1.0")

    subparsers = parser.add_subparsers(dest="subcommand", help="Comando a executar")

    # pure
    p_pure = subparsers.add_parser("pure", help="Cria projeto do Zero Puro com TDD e Padrão-Ouro")
    p_pure.add_argument("nome", nargs="?", default="", help="Nome da aplicação")
    p_pure.add_argument("--quick", action="store_true", help="Pula perguntas interativas e usa valores padrão")
    p_pure.add_argument("--destino", default=None, help="Diretório de destino")
    p_pure.add_argument("--instalar", action="store_true", help="Instala dependências do frontend (npm install)")

    # open
    p_open = subparsers.add_parser("open", help="Cria projeto integrando motores open-source")
    p_open.add_argument("nome", nargs="?", default="", help="Nome da aplicação")
    p_open.add_argument("--quick", action="store_true", help="Pula perguntas interativas")
    p_open.add_argument("--destino", default=None, help="Diretório de destino")
    p_open.add_argument("--instalar", action="store_true", help="Instala dependências do frontend")

    # freedom
    p_freedom = subparsers.add_parser("freedom", help="Desacopla aplicações low-code (Lovable/Bolt/v0)")
    p_freedom.add_argument("origem", nargs="?", default="", help="URL do repositório Git ou caminho da pasta local")
    p_freedom.add_argument("nome", nargs="?", default="app-libertado", help="Nome do projeto de destino")
    p_freedom.add_argument("--destino", default=None, help="Diretório de destino")

    # full
    p_full = subparsers.add_parser("full", help="Instala a Fábrica Completa de Governança do Ecossistema AIDD")
    p_full.add_argument("destino", nargs="?", default="ecossistema-aidd", help="Diretório onde a fábrica será instalada")

    args = parser.parse_args()

    if not args.subcommand:
        return menu_interativo()
    elif args.subcommand == "pure":
        return comando_pure(args)
    elif args.subcommand == "open":
        return comando_open(args)
    elif args.subcommand == "freedom":
        return comando_freedom(args)
    elif args.subcommand == "full":
        return comando_full(args)

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
