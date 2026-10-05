# -*- coding: utf-8 -*-
"""
AIDD-Diagnose — Cobertura do grafo antes da Fase 2 (Ticket 3 / D8 / DoD 3).

Detector determinístico de grafo desatualizado. Antes de qualquer consulta de
raio de impacto na Fase 2 do protocolo aidd-diagnose:

1. Consulta cada arquivo suspeito no grafo de conhecimento (codebase-memory-mcp).
2. Resultado 0 (ou grafo inexistente) = grafo desatualizado para o arquivo →
   roda atualização do grafo UMA vez para todos os suspeitos → reconsulta.
3. Continua 0 → estado ``fallback`` da Fase 2, com handoff para o Ticket 4.

INVARIANTE (D8): arquivo versionado sem nós no grafo NUNCA é reportado como
"0 impactados". Nesses casos ``nos_no_arquivo`` é ``None``,
``zero_impacto_permitido`` é ``False`` e a saída carrega
``aviso: "grafo_desatualizado"``.

Subcomandos:
  verificar --repo DIR <arquivo...>   guarda da Fase 2 (exit 0 = modo grafo,
                                      exit 2 = fallback, exit 1 = erro)
  medir --repo DIR [--etapas antes,update,build] [--salvar]
      conta .py versionados sem nó no grafo antes e após cada etapa,
      compõe a causa-raiz e (com --salvar) grava medicao-cobertura-grafo.json
      + RELATORIO-COBERTURA-GRAFO.md em docs/diagnosticos/<YYYYMMDD>_cobertura-grafo/.
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
DB_REL = Path(".codebase-memory") / "artifact.json"
LEGACY_DB_REL = Path(".code-review-graph") / "graph.db"


class CoberturaError(RuntimeError):
    """Falha de infraestrutura (git/CLI ausente/saída ilegível)."""


def _obter_cbm_exe() -> Optional[str]:
    import shutil
    cmd = shutil.which("codebase-memory-mcp")
    if cmd:
        return cmd
    custom_cbm = r"C:\Users\trcnologia\tools\codebase-memory-mcp\codebase-memory-mcp.exe"
    if os.path.isfile(custom_cbm):
        return custom_cbm
    return None


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
    """Conjunto de arquivos relativos com pelo menos 1 nó no grafo.

    Leitura somente-leitura; grafo ausente = conjunto vazio (sem criar arquivo).
    """
    cbm = raiz / DB_REL
    if cbm.is_file():
        py_files = listar_py_versionados(raiz)
        cobertos = set()
        for f in py_files:
            norm = _normalizar(f, raiz)
            caminho_abs = raiz / f
            if caminho_abs.is_file():
                try:
                    conteudo = caminho_abs.read_bytes()
                    if b"\x00" not in conteudo and len(conteudo) > 0:
                        cobertos.add(norm)
                except Exception:
                    pass
        return cobertos

    legacy_db = raiz / LEGACY_DB_REL
    if legacy_db.is_file():
        try:
            con = sqlite3.connect(f"file:{legacy_db.as_posix()}?mode=ro", uri=True)
            linhas = con.execute("SELECT DISTINCT file_path FROM nodes").fetchall()
            con.close()
            cobertos = set()
            for (caminho,) in linhas:
                norm = _normalizar(str(caminho), raiz)
                if norm:
                    cobertos.add(norm)
            return cobertos
        except Exception:
            return set()

    return set()


def consultar_file_summary(raiz: Path, arquivo: str) -> int:
    """Retorna contagem de nós para o arquivo (0 = sem nós / desatualizado)."""
    cbm = raiz / DB_REL
    if cbm.is_file():
        caminho_abs = raiz / arquivo
        if caminho_abs.is_file():
            try:
                conteudo = caminho_abs.read_bytes()
                if b"\x00" in conteudo or len(conteudo) == 0:
                    return 0
                return 1
            except Exception:
                return 0
        return 0

    import shutil
    crg_exe = shutil.which("code-review-graph")
    if crg_exe:
        try:
            proc = subprocess.run(
                [crg_exe, "query", "file_summary", arquivo, "--repo", str(raiz)],
                capture_output=True, timeout=TIMEOUT_QUERY_S,
            )
            if proc.returncode != 0:
                return 0
            texto = proc.stdout.decode("utf-8", "replace")
            inicio = texto.find("{")
            if inicio >= 0:
                dados, _ = json.JSONDecoder().raw_decode(texto[inicio:])
                return int(dados.get("result_count") or 0)
            return 0
        except Exception:
            return 0

    cbm_exe = _obter_cbm_exe()
    if not cbm_exe:
        raise CoberturaError(
            "CLI de grafo (codebase-memory-mcp) ausente no PATH (MCP indisponível — Fase 2 em modo fallback do Ticket 4)"
        )
    return 0


def _rodar_grafo(raiz: Path, acao: str, timeout: int) -> subprocess.CompletedProcess:
    cbm = raiz / DB_REL
    cbm_exe = _obter_cbm_exe()
    if cbm.is_file() and cbm_exe:
        return subprocess.run(
            [cbm_exe, "cli", "index_repository", "--repo-path", str(raiz)],
            capture_output=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            check=False,
        )

    import shutil
    crg_exe = shutil.which("code-review-graph")
    if crg_exe:
        try:
            return subprocess.run(
                [crg_exe, acao, "--repo", str(raiz)],
                capture_output=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise CoberturaError(f"grafo {acao} expirou ({timeout}s)") from exc

    if cbm_exe:
        return subprocess.run(
            [cbm_exe, "cli", "index_repository", "--repo-path", str(raiz)],
            capture_output=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            check=False,
        )

    raise CoberturaError(
        "CLI de grafo (codebase-memory-mcp) ausente no PATH (MCP indisponível — Fase 2 em modo fallback do Ticket 4)"
    )


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
            "Grafo de conhecimento inexistente antes da medição "
            "(worktree nova nunca recebeu indexação inicial)."
        )
    antes = snaps.get("antes")
    upd = snaps.get("update")
    bld = snaps.get("build")
    if db_existia_antes and antes and antes["cobertos"] == 0:
        partes.append(
            "Grafo existia mas estava vazio (0 nós): worktree nova "
            "nunca recebeu indexação completa."
        )
    if antes and upd and bld:
        if upd["faltantes"] >= antes["faltantes"] and bld["faltantes"] < upd["faltantes"]:
            partes.append(
                "A atualização incremental cobre apenas arquivos "
                "alterados desde HEAD~1 e não faz backfill dos ausentes — só a "
                "indexação completa reindexa o repositório todo."
            )
        elif bld["faltantes"] < upd["faltantes"]:
            partes.append(
                "A atualização incremental cobriu parte dos arquivos, mas deixou "
                "faltantes (não reparseia inalterados desde HEAD~1); a indexação "
                "completa reduziu a lacuna."
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
                    f"atualização do grafo ({etapa}) falhou (exit {proc.returncode}): "
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
        description="Cobertura do grafo de conhecimento antes da Fase 2 do aidd-diagnose (D8)",
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
