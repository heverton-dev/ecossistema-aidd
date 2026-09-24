# -*- coding: utf-8 -*-
"""
AIDD-Diagnose — Cobertura do grafo antes da Fase 2 (Ticket 3 / D8 / DoD 3).

Detector determinístico de grafo desatualizado. Antes de qualquer consulta de
raio de impacto na Fase 2 do protocolo aidd-diagnose:

1. Consulta cada arquivo suspeito via
   ``code-review-graph query file_summary <arquivo> --repo <raiz>``
   (equivalente CLI de ``query_graph_tool(pattern="file_summary", target=<arquivo>)``).
2. Resultado 0 (ou grafo inexistente) = grafo desatualizado para o arquivo →
   roda ``code-review-graph update --repo <raiz>`` UMA vez para todos os
   suspeitos → reconsulta os que estavam com 0.
3. Continua 0 → estado ``fallback`` da Fase 2, com handoff para o Ticket 4.

INVARIANTE (D8): arquivo versionado sem nós no grafo NUNCA é reportado como
"0 impactados". Nesses casos ``nos_no_arquivo`` é ``None``,
``zero_impacto_permitido`` é ``False`` e a saída carrega
``aviso: "grafo_desatualizado"``.

Subcomandos:
  verificar --repo DIR <arquivo...>   guarda da Fase 2 (exit 0 = modo grafo,
                                      exit 2 = fallback, exit 1 = erro)
  medir --repo DIR [--etapas antes,update,build] [--salvar]
      conta .py versionados sem nó em .code-review-graph/graph.db antes e
      após cada etapa, compõe a causa-raiz e (com --salvar) grava
      medicao-cobertura-grafo.json + RELATORIO-COBERTURA-GRAFO.md em
      docs/diagnosticos/<YYYYMMDD>_cobertura-grafo/.

Nunca modifica site-packages; só chama o CLI ``code-review-graph`` e lê o
graph.db em modo somente-leitura.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence

DB_REL = Path(".code-review-graph") / "graph.db"
ETAPAS_VALIDAS = ("antes", "update", "build")
TIMEOUT_QUERY_S = 300
TIMEOUT_UPDATE_S = 900
TIMEOUT_BUILD_S = 3600


class CoberturaError(RuntimeError):
    """Falha de infraestrutura (git/CLI ausente/saída ilegível)."""


# ---------------------------------------------------------------------------
# Raiz do repositório e utilitários de caminho
# ---------------------------------------------------------------------------

def encontrar_raiz(inicio: Optional[Path] = None) -> Path:
    """Sobe a árvore até achar .git ou ecossistema.py."""
    atual = (inicio or Path(__file__)).resolve()
    for candidato in [atual, *atual.parents]:
        if (candidato / ".git").exists() or (candidato / "ecossistema.py").is_file():
            return candidato
    raise CoberturaError("raiz do repositório não encontrada (.git/ecossistema.py ausente)")


def _normalizar(caminho: str, raiz: Path) -> Optional[str]:
    """Caminho relativo posix (case-insensitive no Windows) para comparação."""
    p = Path(caminho)
    if p.is_absolute():
        try:
            p = p.resolve().relative_to(raiz.resolve())
        except ValueError:
            return None
    texto = p.as_posix()
    while texto.startswith("./"):
        texto = texto[2:]
    return texto.lower() if os.name == "nt" else texto


# ---------------------------------------------------------------------------
# Leituras de cobertura
# ---------------------------------------------------------------------------

def listar_py_versionados(raiz: Path) -> List[str]:
    """.py versionados pelo git (git ls-files), relativos em posix."""
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=str(raiz), capture_output=True, timeout=TIMEOUT_QUERY_S,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CoberturaError(f"git ls-files indisponível: {exc}") from exc
    if proc.returncode != 0:
        raise CoberturaError(
            f"git ls-files falhou (exit {proc.returncode}): "
            f"{proc.stderr.decode('utf-8', 'replace')[:300]}"
        )
    saida = proc.stdout.decode("utf-8", "replace")
    return [f for f in saida.split("\0") if f.endswith(".py")]


def arquivos_com_nos(raiz: Path) -> set:
    """Conjunto de arquivos relativos com pelo menos 1 nó em graph.db.

    Leitura somente-leitura; grafo ausente = conjunto vazio (sem criar arquivo).
    """
    db = raiz / DB_REL
    if not db.is_file():
        return set()
    try:
        con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        raise CoberturaError(f"graph.db ilegível: {exc}") from exc
    try:
        linhas = con.execute("SELECT DISTINCT file_path FROM nodes").fetchall()
    except sqlite3.Error as exc:
        raise CoberturaError(f"graph.db sem tabela nodes: {exc}") from exc
    finally:
        con.close()
    cobertos = set()
    for (caminho,) in linhas:
        norm = _normalizar(str(caminho), raiz)
        if norm:
            cobertos.add(norm)
    return cobertos


def consultar_file_summary(raiz: Path, arquivo: str) -> int:
    """result_count de query_graph_tool(pattern='file_summary', target=<arquivo>).

    0 = sem nós para o arquivo (grafo ausente/desatualizado).
    """
    try:
        proc = subprocess.run(
            ["code-review-graph", "query", "file_summary", arquivo, "--repo", str(raiz)],
            capture_output=True, timeout=TIMEOUT_QUERY_S,
        )
    except FileNotFoundError as exc:
        raise CoberturaError(
            "CLI code-review-graph ausente no PATH (MCP indisponível — Fase 2 em modo fallback do Ticket 4)"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise CoberturaError(f"consulta file_summary expirou ({TIMEOUT_QUERY_S}s): {arquivo}") from exc

    texto = proc.stdout.decode("utf-8", "replace")
    if proc.returncode != 0:
        # Grafo nunca construído nesta árvore: "No graph found ... Run build".
        if "No graph found" in texto or "No graph found" in proc.stderr.decode("utf-8", "replace"):
            return 0
        raise CoberturaError(
            f"query file_summary falhou para {arquivo} (exit {proc.returncode}): {texto[:300]}"
        )
    inicio = texto.find("{")
    if inicio < 0:
        raise CoberturaError(f"saída de query sem JSON para {arquivo}: {texto[:300]}")
    try:
        dados, _ = json.JSONDecoder().raw_decode(texto[inicio:])
    except ValueError as exc:
        raise CoberturaError(f"JSON inválido de query para {arquivo}: {exc}") from exc
    if dados.get("status") not in (None, "ok"):
        raise CoberturaError(f"query retornou status={dados.get('status')} para {arquivo}")
    return int(dados.get("result_count") or 0)


def _rodar_grafo(raiz: Path, acao: str, timeout: int) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["code-review-graph", acao, "--repo", str(raiz)],
            capture_output=True, timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise CoberturaError(
            "CLI code-review-graph ausente no PATH (MCP indisponível — Fase 2 em modo fallback do Ticket 4)"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise CoberturaError(f"code-review-graph {acao} expirou ({timeout}s)") from exc


# ---------------------------------------------------------------------------
# verificar — guarda da Fase 2
# ---------------------------------------------------------------------------

def verificar_cobertura(arquivos: Sequence[str], raiz: Path) -> dict:
    """Checagem de cobertura dos arquivos suspeitos antes da Fase 2.

    Retorna dict com modo_fase2, handoff e o estado por arquivo. Nunca expõe
    contagem numérica de nós para arquivo sem cobertura.
    """
    if not arquivos:
        raise CoberturaError("nenhum arquivo suspeito informado")

    contagens_iniciais: Dict[str, int] = {}
    desatualizados: List[str] = []
    for arquivo in arquivos:
        n = consultar_file_summary(raiz, arquivo)
        contagens_iniciais[arquivo] = n
        if n == 0:
            desatualizados.append(arquivo)

    atualizacoes = 0
    exit_atualizacao = None
    contagens_finais: Dict[str, int] = dict(contagens_iniciais)
    if desatualizados:
        proc = _rodar_grafo(raiz, "update", TIMEOUT_UPDATE_S)
        atualizacoes = 1
        exit_atualizacao = proc.returncode
        for arquivo in desatualizados:
            contagens_finais[arquivo] = consultar_file_summary(raiz, arquivo)

    arquivos_saida: Dict[str, dict] = {}
    for arquivo in arquivos:
        n = contagens_finais[arquivo]
        if contagens_iniciais[arquivo] > 0:
            estado = "coberto"
        elif n > 0:
            estado = "coberto_apos_atualizacao"
        else:
            estado = "fallback"

        if estado == "fallback":
            arquivos_saida[arquivo] = {
                "coberto": False,
                "estado": estado,
                "nos_no_arquivo": None,
                "zero_impacto_permitido": False,
                "aviso": "grafo_desatualizado",
            }
        else:
            arquivos_saida[arquivo] = {
                "coberto": True,
                "estado": estado,
                "nos_no_arquivo": n,
                "zero_impacto_permitido": True,
            }

    todos_cobertos = all(i["coberto"] for i in arquivos_saida.values())
    modo = "grafo" if todos_cobertos else "fallback"
    return {
        "status": "ok",
        "raiz": str(raiz),
        "modo_fase2": modo,
        "atualizacoes_executadas": atualizacoes,
        "atualizacao_exit": exit_atualizacao,
        "pode_reportar_zero_impacto": todos_cobertos,
        "handoff": None if todos_cobertos else "ticket_4_fallback",
        "arquivos": arquivos_saida,
    }


# ---------------------------------------------------------------------------
# medir — contagem de faltantes antes/update/build + causa-raiz
# ---------------------------------------------------------------------------

def _snapshot(raiz: Path, py: Sequence[str], etapa: str, exit_cmd: Optional[int]) -> dict:
    cobertos_set = arquivos_com_nos(raiz)
    py_norm = {_normalizar(f, raiz) for f in py}
    cobertos = sorted(py_norm & cobertos_set)
    faltantes = sorted(py_norm - cobertos_set)
    return {
        "etapa": etapa,
        "comando_exit": exit_cmd,
        "cobertos": len(cobertos),
        "faltantes": len(faltantes),
        "amostra_faltantes": faltantes[:50],
    }


def _compor_raiz_causa(db_existia_antes: bool, snaps: Dict[str, dict]) -> str:
    partes: List[str] = []
    if db_existia_antes is False and "antes" in snaps:
        partes.append(
            "Grafo .code-review-graph/graph.db inexistente antes da medição "
            "(diretório é gitignored; worktree nova nunca recebeu build)."
        )
    antes = snaps.get("antes")
    upd = snaps.get("update")
    bld = snaps.get("build")
    if db_existia_antes and antes and antes["cobertos"] == 0:
        partes.append(
            "graph.db existia mas estava vazio (0 nós): worktree nova com "
            ".code-review-graph/ gitignored nunca recebeu build inicial."
        )
    if antes and upd and bld:
        if upd["faltantes"] >= antes["faltantes"] and bld["faltantes"] < upd["faltantes"]:
            partes.append(
                "code-review-graph update é incremental: reparseia apenas arquivos "
                "alterados desde HEAD~1 e não faz backfill dos ausentes — só o "
                "build completo (full rebuild) reindexa o repositório."
            )
        elif bld["faltantes"] < upd["faltantes"]:
            partes.append(
                "O update incremental cobriu parte dos arquivos, mas deixou "
                "faltantes (não reparseia inalterados desde HEAD~1); o build "
                "completo reduziu a lacuna."
            )
        if bld["faltantes"] > 0:
            partes.append(
                f"{bld['faltantes']} arquivo(s) continuam sem nós mesmo após o "
                "build: o parser pula binários/sem linguagem/caminho excessivo — "
                "esses arquivos nunca podem sair como '0 impactados' "
                "(Fase 2 = fallback, Ticket 4)."
            )
    elif antes and not upd and not bld and antes["faltantes"] > 0:
        partes.append(
            "Medição apenas 'antes': sem update/build nesta execução, o grafo "
            "atual já indica a lacuna inicial."
        )
    if not partes:
        partes.append("Nenhum faltante: o grafo cobre todos os .py versionados.")
    return " ".join(partes)


def _render_relatorio_md(medicao: dict) -> str:
    linhas = [
        "# Relatório de Cobertura do Grafo — aidd-diagnose Ticket 3 (D8)",
        "",
        f"- Repositório: `{medicao['raiz']}`",
        f"- Data (UTC): {medicao['data_utc']}",
        f"- `.py` versionados: {medicao['py_versionados']}",
        f"- Sessão: `{medicao['sessao_dir']}`",
        "",
        "## Contagens por etapa",
        "",
        "| etapa | exit | cobertos | faltantes |",
        "|---|---|---|---|",
    ]
    for snap in medicao["etapas"]:
        linhas.append(
            f"| {snap['etapa']} | {snap['comando_exit']} | "
            f"{snap['cobertos']} | {snap['faltantes']} |"
        )
    linhas += ["", "## Causa-raiz", "", medicao["raiz_causa"], ""]
    ultimo = medicao["etapas"][-1]
    if ultimo["amostra_faltantes"]:
        linhas += [
            f"## Amostra de faltantes após '{ultimo['etapa']}' (até 50)",
            "",
        ]
        linhas += [f"- `{c}`" for c in ultimo["amostra_faltantes"]]
        linhas.append("")
    linhas += [
        "> Nunca reporte '0 impactados' para arquivo sem nós no grafo:",
        "> use `cobertura_grafo.py verificar` antes da Fase 2.",
        "",
    ]
    return "\n".join(linhas)


def medir_cobertura(raiz: Path, etapas: Sequence[str], salvar: bool = False) -> dict:
    """Conta .py versionados sem nó antes e após cada etapa; compõe causa-raiz."""
    for etapa in etapas:
        if etapa not in ETAPAS_VALIDAS:
            raise CoberturaError(f"etapa inválida: {etapa} (válidas: {', '.join(ETAPAS_VALIDAS)})")
    if not etapas:
        raise CoberturaError("nenhuma etapa informada")

    py = listar_py_versionados(raiz)
    db_existia_antes = (raiz / DB_REL).is_file()

    snaps: Dict[str, dict] = {}
    ordem: List[dict] = []
    for etapa in etapas:
        if etapa == "antes":
            snap = _snapshot(raiz, py, "antes", None)
        else:
            proc = _rodar_grafo(raiz, etapa, TIMEOUT_BUILD_S if etapa == "build" else TIMEOUT_UPDATE_S)
            if proc.returncode != 0:
                raise CoberturaError(
                    f"code-review-graph {etapa} falhou (exit {proc.returncode}): "
                    + proc.stderr.decode("utf-8", "replace")[:300]
                )
            snap = _snapshot(raiz, py, etapa, proc.returncode)
        snaps[etapa] = snap
        ordem.append(snap)

    sessao_dir: Optional[str] = None
    if salvar:
        hoje = datetime.now().strftime("%Y%m%d")
        sessao = raiz / "docs" / "diagnosticos" / f"{hoje}_cobertura-grafo"
        sessao.mkdir(parents=True, exist_ok=True)
        sessao_dir = str(sessao)

    medicao = {
        "status": "ok",
        "raiz": str(raiz),
        "data_utc": datetime.now().isoformat(timespec="seconds"),
        "py_versionados": len(py),
        "graph_db_existia_antes": db_existia_antes,
        "etapas": ordem,
        "raiz_causa": _compor_raiz_causa(db_existia_antes, snaps),
        "sessao_dir": sessao_dir,
    }

    if salvar and sessao_dir:
        sessao = Path(sessao_dir)
        with open(sessao / "medicao-cobertura-grafo.json", "w", encoding="utf-8") as f:
            json.dump(medicao, f, indent=2, ensure_ascii=False)
        (sessao / "RELATORIO-COBERTURA-GRAFO.md").write_text(
            _render_relatorio_md(medicao), encoding="utf-8"
        )
    return medicao


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cobertura_grafo.py",
        description="Cobertura do code-review-graph antes da Fase 2 do aidd-diagnose (D8)",
    )
    sub = parser.add_subparsers(dest="subcomando", required=True)

    p_ver = sub.add_parser("verificar", help="checa cobertura dos arquivos suspeitos (guarda da Fase 2)")
    p_ver.add_argument("--repo", default=None, help="raiz do repositório (auto-detecta)")
    p_ver.add_argument("arquivos", nargs="+", help="arquivos suspeitos (relativos à raiz)")

    p_med = sub.add_parser("medir", help="conta .py versionados sem nó antes/update/build")
    p_med.add_argument("--repo", default=None, help="raiz do repositório (auto-detecta)")
    p_med.add_argument(
        "--etapas", default="antes,update,build",
        help="ordem das etapas válidas: antes,update,build (padrão: antes,update,build)",
    )
    p_med.add_argument(
        "--salvar", action="store_true",
        help="grava medicao-cobertura-grafo.json e RELATORIO-COBERTURA-GRAFO.md em docs/diagnosticos/",
    )

    args = parser.parse_args(argv)
    try:
        raiz = Path(args.repo).resolve() if args.repo else encontrar_raiz()
        if not raiz.is_dir():
            raise CoberturaError(f"repositório inexistente: {raiz}")

        if args.subcomando == "verificar":
            dados = verificar_cobertura(args.arquivos, raiz)
            print(json.dumps(dados, indent=2, ensure_ascii=False))
            return 0 if dados["modo_fase2"] == "grafo" else 2

        etapas = [e.strip() for e in args.etapas.split(",") if e.strip()]
        dados = medir_cobertura(raiz, etapas, salvar=args.salvar)
        print(json.dumps(dados, indent=2, ensure_ascii=False))
        return 0
    except CoberturaError as exc:
        print(f"[cobertura_grafo] ERRO: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"[cobertura_grafo] ERRO: JSON inválido: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
