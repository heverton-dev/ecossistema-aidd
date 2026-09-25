# -*- coding: utf-8 -*-
"""
AIDD-Diagnose CLI: Subcomandos determinísticos para diagnosticar e registrar sintomas do ecossistema.
Padrão de delegação: espelha aidd-melhoria.

Ponto único de entrada dos módulos da skill:
  iniciar / fase        -> sessao.json (Ticket 1)
  registrar / relatorio -> observabilidade.py (Ticket 5)
  worktree              -> isolamento.py (Ticket 2)
  limpar                -> rollback.py (Ticket 7)
O handoff (Ticket 8) tem CLI própria em handoff.py.

A raiz onde docs/diagnosticos/ é gravado pode ser trocada pela variável
AIDD_DIAGNOSE_RAIZ (usada pelos testes para nunca tocar o repositório real).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Optional, List
import re

VAR_RAIZ = "AIDD_DIAGNOSE_RAIZ"
SCRIPTS_DIR = Path(__file__).resolve().parent


def find_repo_root(start_path: Optional[Path] = None) -> Path:
    """Encontra a raiz do repositório procurando por ecossistema.py."""
    current = (start_path or Path(__file__)).resolve()
    candidates = [current] + list(current.parents)
    for parent in candidates:
        if (parent / "ecossistema.py").is_file():
            return parent
    return Path(__file__).resolve().parents[4]


REPO_ROOT = find_repo_root()


def raiz_diagnose() -> Path:
    """Raiz efetiva: AIDD_DIAGNOSE_RAIZ quando definida, senão a raiz do repositório."""
    override = os.environ.get(VAR_RAIZ)
    return Path(override).resolve() if override else REPO_ROOT


def _carregar_modulo(nome: str) -> ModuleType:
    """Carrega um módulo irmão desta pasta com nome único (evita colisão com aidd-melhoria)."""
    nome_unico = f"aidd_diagnose_{nome}"
    if nome_unico in sys.modules:
        return sys.modules[nome_unico]
    spec = importlib.util.spec_from_file_location(nome_unico, str(SCRIPTS_DIR / f"{nome}.py"))
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nome_unico] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def slugificar(texto: str) -> str:
    """Converte texto para slug válido (ex: 'Meu Sintoma' -> 'meu-sintoma')."""
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9\s-]", "", texto)
    texto = re.sub(r"\s+", "-", texto)
    return texto


def _momento_inicio(pasta: Path) -> tuple:
    """Chave de ordenação: data_inicio do sessao.json; mtime como desempate/fallback."""
    sessao = pasta / "sessao.json"
    data_inicio = ""
    try:
        data_inicio = str(json.loads(sessao.read_text(encoding="utf-8")).get("data_inicio") or "")
    except (OSError, ValueError, AttributeError):
        pass
    return (data_inicio, sessao.stat().st_mtime)


def localizar_ultima_sessao(repo_root: Optional[Path] = None) -> Optional[Path]:
    """Retorna a sessão de diagnose iniciada por último (pela data de início, não pelo nome)."""
    diagnosticos_dir = Path(repo_root or raiz_diagnose()) / "docs" / "diagnosticos"
    if not diagnosticos_dir.is_dir():
        return None
    sessoes = [d for d in diagnosticos_dir.glob("*_*") if (d / "sessao.json").is_file()]
    return max(sessoes, key=_momento_inicio) if sessoes else None


def _sessao_ou_erro() -> Optional[Path]:
    sessao_dir = localizar_ultima_sessao()
    if not sessao_dir:
        print("Erro: Nenhuma sessão de diagnose encontrada. Execute 'diagnose iniciar --sintoma <texto>' primeiro.")
    return sessao_dir


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
    pasta_sessao = raiz_diagnose() / "docs" / "diagnosticos" / f"{data_str}_{slug}"

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

    sessao_dir = _sessao_ou_erro()
    if not sessao_dir:
        return 1

    sessao_file = sessao_dir / "sessao.json"
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
        print(f"[OK] Avançado para fase {numero} ({sessao_dir.name})")
        return 0
    except Exception as exc:
        print(f"Erro ao atualizar sessão: {exc}")
        return 1


def cmd_registrar(parsed: argparse.Namespace) -> int:
    """Subcomando: registrar --fase N [...] -> grava fase_NN_<ts>.log na sessão atual."""
    sessao_dir = _sessao_ou_erro()
    if not sessao_dir:
        return 1
    if bool(parsed.descartada) != bool(parsed.prova):
        print("Erro: --descartada e --prova andam juntos.")
        return 1
    obs = _carregar_modulo("observabilidade")
    with obs.RegistradorFase(
        numero=parsed.fase, diretorio_sessao=str(sessao_dir), modo_fase2=parsed.modo_fase2
    ) as reg:
        if parsed.comando:
            reg.registrar_comando_reproducao(parsed.comando)
        if parsed.hipotese:
            reg.registrar_hipotese(parsed.hipotese)
        if parsed.descartada:
            reg.registrar_descartada(parsed.descartada, parsed.prova)
    print(f"[OK] Fase {parsed.fase} registrada em {sessao_dir}")
    return 0


def cmd_relatorio(parsed: argparse.Namespace) -> int:
    """Subcomando: relatorio -> RELATORIO-CAUSA-RAIZ.md consolidado (entrada do G_aidd_diagnose)."""
    sessao_dir = _sessao_ou_erro()
    if not sessao_dir:
        return 1
    obs = _carregar_modulo("observabilidade")
    caminho = obs.gerar_relatorio_causa_raiz(
        sessao_dir,
        execucoes=parsed.execucoes,
        teste_regressao=parsed.teste_regressao,
        exit_antes_fix=parsed.exit_antes,
    )
    print(f"[OK] Relatório gerado: {caminho}")
    return 0


def cmd_worktree(slug: str) -> int:
    """Subcomando: worktree --slug S -> cria ../worktrees_diagnose-<slug>/ para a Fase 4."""
    iso = _carregar_modulo("isolamento")
    try:
        caminho = iso.criar_worktree_fase4(raiz_diagnose(), slugificar(slug))
    except RuntimeError as exc:
        print(f"Erro: {exc}")
        return 1
    print(f"[OK] Worktree da Fase 4: {caminho}")
    return 0


def cmd_limpar(slug: Optional[str]) -> int:
    """Subcomando: limpar [--slug S] -> remove marcadores AIDD-DIAGNOSE-TEMP e descarta a worktree."""
    rb = _carregar_modulo("rollback")
    codigo = rb.finalizar_fase5(raiz_diagnose(), slugificar(slug) if slug else None)
    if codigo == 0:
        print("[OK] Instrumentação temporária removida e worktree descartada.")
    return codigo


def main(args: Optional[List[str]] = None) -> int:
    """Entrypoint principal da CLI."""
    parser = argparse.ArgumentParser(
        prog="python ecossistema.py diagnose",
        description="CLI de Diagnose do Ecossistema AIDD"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Subcomandos disponíveis")

    parser_iniciar = subparsers.add_parser("iniciar", help="Inicia uma nova sessão de diagnose")
    parser_iniciar.add_argument("--sintoma", required=True, help="Descrição do sintoma a diagnosticar")

    parser_fase = subparsers.add_parser("fase", help="Avança para uma nova fase")
    parser_fase.add_argument("--numero", type=int, required=True, help="Número da fase (1-5)")

    parser_reg = subparsers.add_parser("registrar", help="Registra comando/hipóteses de uma fase (log)")
    parser_reg.add_argument("--fase", type=int, required=True, choices=range(1, 6))
    parser_reg.add_argument("--comando", help="Comando de reprodução executado")
    parser_reg.add_argument("--hipotese", help="Hipótese ativa (uma por vez)")
    parser_reg.add_argument("--descartada", help="Hipótese descartada")
    parser_reg.add_argument("--prova", help="Prova que descartou a hipótese")
    parser_reg.add_argument("--modo-fase2", dest="modo_fase2", choices=["grafo", "fallback"])

    parser_rel = subparsers.add_parser("relatorio", help="Gera RELATORIO-CAUSA-RAIZ.md da sessão atual")
    parser_rel.add_argument("--execucoes", type=int, default=0, help="Vezes que a reprodução rodou igual")
    parser_rel.add_argument("--teste-regressao", dest="teste_regressao", help="Arquivo do teste de regressão")
    parser_rel.add_argument("--exit-antes", dest="exit_antes", type=int, help="Exit code do teste antes do fix")

    parser_wt = subparsers.add_parser("worktree", help="Cria a worktree isolada da Fase 4")
    parser_wt.add_argument("--slug", required=True)

    parser_limpar = subparsers.add_parser("limpar", help="Fim da Fase 5: tira instrumentação e worktree")
    parser_limpar.add_argument("--slug", default=None)

    parsed = parser.parse_args(args)

    if not parsed.subcommand:
        parser.print_help()
        return 0

    if parsed.subcommand == "iniciar":
        return cmd_iniciar(parsed.sintoma)
    if parsed.subcommand == "fase":
        return cmd_fase(parsed.numero)
    if parsed.subcommand == "registrar":
        return cmd_registrar(parsed)
    if parsed.subcommand == "relatorio":
        return cmd_relatorio(parsed)
    if parsed.subcommand == "worktree":
        return cmd_worktree(parsed.slug)
    if parsed.subcommand == "limpar":
        return cmd_limpar(parsed.slug)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
