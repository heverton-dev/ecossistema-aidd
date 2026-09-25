# -*- coding: utf-8 -*-
"""
Fallback Operacional sem MCP - aidd-diagnose Fase 2 (Ticket 4, D11, DoD 4).

Quando o MCP `code-review-graph` estiver indisponivel, a Fase 2 do diagnostico
NAO deve abortar. Este modulo:

1. Sonda a conexao com `code-review-graph query file_summary` usando retry com
   backoff exponencial (o servidor sobe a frio em ~11 s; CONNECT_TIMEOUT de
   30 s foi observado no servidor 2026-09-23, ver docs/auditoria/aidd-diagnose/).
2. Com o MCP derrubado, executa a triagem no espirito determinista de
   Grep/Glob/Read (stdlib exclusivamente, zero dependencia externa):
     * callers -> busca AST pelo NOME da funcao em todos os .py do repositório;
     * callees -> leitura do CORPO da funcao (AST);
     * impacto -> busca de IMPORTS (quem importa o modulo do arquivo suspeito).
3. Registra em sessao.json o modo real da Fase 2: "grafo" (MCP ok) ou
   "fallback" (MCP indisponivel).

Coringa deterministico: nunca usa LLM. Sempre tipado e testado por testes reais
(tests/test_fallback_diagnose.py).
"""

import argparse
import ast
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

PROBE_MAX_TENTATIVAS = 4
PROBE_BACKOFF_BASE = 1.0
PROBE_FATOR = 3.0
PROBE_TIMEOUT_S = 45.0

DIRS_IGNORADAS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".code-review-graph",
    ".ade_tmp",
    "dist",
    "build",
}

COMANDO_PROBE = ("code-review-graph", "query", "file_summary")


class FallbackOperacionalError(Exception):
    """Falha de infraestrutura do fallback operacional (nao do sistema alvo)."""


def encontrar_raiz(inicio: Optional[Path] = None) -> Path:
    """Sobe a arvore ate a raiz do ecossistema (onde existe ecossistema.py)."""
    atual = (inicio or Path(__file__)).resolve()
    for candidato in (atual, *atual.parents):
        if (candidato / "ecossistema.py").is_file():
            return candidato
    raise FallbackOperacionalError("raiz do repositório não encontrada (ecossistema.py ausente)")


def listar_py_repo(raiz: Path) -> List[str]:
    """Todos os .py do repo, relativos a raiz, pulando dirs de infra."""
    raiz = Path(raiz)
    lista: List[str] = []
    for pasta, subpastas, arquivos in os.walk(raiz):
        subpastas[:] = [d for d in subpastas if d not in DIRS_IGNORADAS]
        for arquivo in sorted(arquivos):
            if arquivo.endswith(".py"):
                rel = Path(pasta).relative_to(raiz).as_posix()
                lista.append(f"{rel}/{arquivo}" if rel != "." else arquivo)
    return sorted(lista)


def _parse_arvore(caminho: Path) -> Optional[ast.Module]:
    try:
        return ast.parse(caminho.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, SyntaxError):
        return None


def _nome_alvo_call(func: ast.AST) -> Optional[str]:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _callees_do_corpo(no: ast.AST) -> List[Dict[str, Any]]:
    callees: List[Dict[str, Any]] = []
    for sub in ast.walk(no):
        if isinstance(sub, ast.Call):
            nome = _nome_alvo_call(sub.func)
            if nome:
                callees.append({"nome": nome, "linha": sub.lineno})
    return callees


def _extrair_imports(arvore: ast.Module) -> List[Dict[str, Any]]:
    imports: List[Dict[str, Any]] = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            for a in no.names:
                imports.append({"tipo": "import", "nome": a.name, "alias": a.asname, "linha": no.lineno})
        elif isinstance(no, ast.ImportFrom):
            imports.append({
                "tipo": "from",
                "modulo": no.module,
                "level": no.level,
                "nomes": [a.name for a in no.names],
                "linha": no.lineno,
            })
    return imports


def analisar_arquivo(raiz: Path, arquivo_rel: str, funcao: Optional[str] = None) -> Dict[str, Any]:
    """Leitura de corpo (Read/AST): imports, funcoes definidas e callees do alvo."""
    caminho = Path(raiz) / arquivo_rel
    if not caminho.is_file():
        return {"arquivo": arquivo_rel, "erro": "arquivo inexistente"}
    arvore = _parse_arvore(caminho)
    if arvore is None:
        return {"arquivo": arquivo_rel, "erro": "leitura/parse falhou"}
    funcoes: Dict[str, Any] = {}
    for no in ast.walk(arvore):
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcoes[no.name] = {"linha": no.lineno, "callees": _callees_do_corpo(no)}
    dados: Dict[str, Any] = {
        "arquivo": arquivo_rel,
        "imports": _extrair_imports(arvore),
        "funcoes_definidas": funcoes,
    }
    if funcao:
        dados["funcao_definida"] = funcao in funcoes
        dados["callees_alvo"] = funcoes.get(funcao, {}).get("callees", [])
    return dados


def buscar_callees(raiz: Path, arquivo_rel: str, funcao: str) -> List[Dict[str, Any]]:
    """Callees da funcao por leitura do corpo (AST do proprio arquivo)."""
    dados = analisar_arquivo(Path(raiz), arquivo_rel, funcao=funcao)
    return dados.get("callees_alvo", [])


class _VisitanteChamadores(ast.NodeVisitor):
    def __init__(self, nome: str) -> None:
        self.nome = nome
        self.pilha: List[str] = []
        self.ocorrencias: List[Dict[str, Any]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.pilha.append(node.name)
        self.generic_visit(node)
        self.pilha.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.pilha.append(node.name)
        self.generic_visit(node)
        self.pilha.pop()

    def visit_Call(self, node: ast.Call) -> None:
        if _nome_alvo_call(node.func) == self.nome:
            self.ocorrencias.append({
                "linha": node.lineno,
                "contexto": self.pilha[-1] if self.pilha else None,
            })
        self.generic_visit(node)


def buscar_chamadores(raiz: Path, nome_funcao: Optional[str]) -> List[Dict[str, Any]]:
    """Callers pelo NOME da funcao (espirito Grep) entre todos os .py do repo."""
    if not nome_funcao:
        return []
    ocorrencias: List[Dict[str, Any]] = []
    for rel in listar_py_repo(raiz):
        caminho = Path(raiz) / rel
        if caminho == Path(__file__).resolve() or caminho.name == "fallback.py":
            continue
        arvore = _parse_arvore(caminho)
        if arvore is None:
            continue
        visitante = _VisitanteChamadores(nome_funcao)
        visitante.visit(arvore)
        for o in visitante.ocorrencias:
            ocorrencias.append({"arquivo": rel, "linha": o["linha"], "contexto": o["contexto"]})
    return sorted(ocorrencias, key=lambda o: (o["arquivo"], o["linha"]))


def _imports_absolutos(rel: str, arvore: ast.Module) -> "set[str]":
    """Normaliza todos os imports do arquivo para nomes de modulo sem extensao."""
    partes = [p for p in rel.replace("\\", "/").split("/") if p]
    pkg_partes = partes[:-1] if partes else []
    imports: "set[str]" = set()

    def adicionar(nome: str) -> None:
        if nome and nome not in ("os", "sys"):
            imports.add(nome)

    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            alvos_pkg = [p.partition(".")[0] for p in pkg_partes if p]
            for a in no.names:
                adicionar(a.name)
                adicionar(a.name.split(".")[0])
                if a.asname and alvos_pkg:
                    adicionar(a.asname)
        elif isinstance(no, ast.ImportFrom):
            if no.level:
                up = max(0, no.level - 1)
                base_partes = pkg_partes[: max(0, len(pkg_partes) - up)] if up else pkg_partes
                base_pkg = ".".join(base_partes) if base_partes else ""
                if no.module:
                    adicionar(f"{base_pkg}.{no.module}" if base_pkg else no.module)
                    adicionar(no.module)
                for a in no.names:
                    adicionar(f"{base_pkg}.{a.name}" if base_pkg else a.name)
                    adicionar(a.name)
            else:
                if no.module:
                    adicionar(no.module)
                    adicionar(no.module.split(".")[0])
                for a in no.names:
                    adicionar(a.name)
                    if a.asname:
                        adicionar(a.asname)
    return imports


def _candidatos_modulo(arquivo_rel: str) -> "set[str]":
    """Possiveis nomes de modulo (import) que apontam para o arquivo suspeito."""
    p = arquivo_rel.replace("\\", "/")
    cands: "set[str]" = {Path(p).stem}
    if p.endswith(".py"):
        cands.add(p[:-3].replace("/", "."))
    return cands


def busca_impacto_imports(raiz: Path, arquivo_alvo: str) -> List[Dict[str, Any]]:
    """Quem importa o modulo do arquivo suspeito (impacto por IMPORTS)."""
    alvo = arquivo_alvo.replace("\\", "/")
    cands = _candidatos_modulo(alvo)
    importadores: List[Dict[str, Any]] = []
    for rel in listar_py_repo(raiz):
        if rel == alvo:
            continue
        arvore = _parse_arvore(Path(raiz) / rel)
        if arvore is None:
            continue
        achados = sorted(_imports_absolutos(rel, arvore) & cands)
        if achados:
            importadores.append({"arquivo": rel, "imports_encontrados": achados})
    return sorted(importadores, key=lambda i: i["arquivo"])


def _rodar_probe(raiz: Path, arquivo: str) -> subprocess.CompletedProcess:
    """Executa a sonda no MCP code-review-graph. Levanta OSError se o CLI não existir."""
    return subprocess.run(
        [*COMANDO_PROBE, arquivo, "--repo", str(raiz)],
        capture_output=True,
        timeout=PROBE_TIMEOUT_S,
        check=False,
    )


def _sono(segundos: float) -> None:
    time.sleep(segundos)


def probe_mcp(raiz: Path, arquivo: str) -> Dict[str, Any]:
    """Uma unica tentativa de sonda. Nunca levanta; devolve dict com ok=True/False."""
    try:
        proc = _rodar_probe(Path(raiz), arquivo)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "erro": str(exc), "classe": type(exc).__name__}
    if proc.returncode != 0:
        saida = proc.stderr or proc.stdout or b""
        texto = saida.decode("utf-8", "replace").strip()[:300]
        return {"ok": False, "erro": texto or f"retorno {proc.returncode}", "classe": "RetornoMCPInvalido"}
    saida = (proc.stdout or b"").decode("utf-8", "replace").strip()[:300]
    return {"ok": True, "erro": None, "classe": None, "returncode": proc.returncode, "saida": saida}


def probe_mcp_com_retry(
    raiz: Path,
    arquivo: str,
    max_tentativas: Optional[int] = None,
    backoff_base: Optional[float] = None,
    fator: Optional[float] = None,
) -> Dict[str, Any]:
    """Sonda com retry + backoff exponencial, aguardando o cold start (~11 s)."""
    max_tentativas = max(1, int(max_tentativas if max_tentativas is not None else PROBE_MAX_TENTATIVAS))
    backoff_base = float(backoff_base if backoff_base is not None else PROBE_BACKOFF_BASE)
    fator = float(fator if fator is not None else PROBE_FATOR)
    ultimo: Dict[str, Any] = {"ok": False}
    for tentativa in range(1, max_tentativas + 1):
        ultimo = probe_mcp(raiz, arquivo)
        if ultimo.get("ok"):
            return {
                **ultimo,
                "tentativas_usadas": tentativa,
                "max_tentativas": max_tentativas,
                "backoff_base": backoff_base,
                "fator": fator,
            }
        if tentativa < max_tentativas:
            _sono(backoff_base * (fator ** (tentativa - 1)))
    return {
        **ultimo,
        "tentativas_usadas": max_tentativas,
        "max_tentativas": max_tentativas,
        "backoff_base": backoff_base,
        "fator": fator,
    }


def obter_sessao(raiz: Path) -> Optional[Path]:
    """Ultima sessao.json em docs/diagnosticos/<slug>/ (fallback sem --sessao)."""
    diag = Path(raiz) / "docs" / "diagnosticos"
    if not diag.is_dir():
        return None
    subdirs = sorted([d for d in diag.iterdir() if d.is_dir()], reverse=True)
    for subdir in subdirs:
        sessao = subdir / "sessao.json"
        if sessao.is_file():
            return sessao
    return None


def registrar_modo_fase2(
    sessao_path: Path,
    modo: str,
    detalhes: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Registra o modo real da Fase 2 em sessao.json (escrita atomica)."""
    sessao = Path(sessao_path)
    if modo not in ("grafo", "fallback"):
        raise FallbackOperacionalError(f"modo de fase 2 inválido: {modo!r}")
    if not sessao.is_file():
        raise FallbackOperacionalError(f"sessão não encontrada: {sessao}")
    dados = json.loads(sessao.read_text(encoding="utf-8"))
    dados["fase2"] = {
        "modo": modo,
        "registrado_em": datetime.now(timezone.utc).isoformat(),
        "detalhes": detalhes or {},
    }
    tmp = sessao.with_name(sessao.name + ".tmp")
    tmp.write_text(json.dumps(dados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(sessao)
    return dados


def analisar_fase2(
    raiz: Path,
    arquivos: Iterable[str],
    funcao: Optional[str] = None,
    sessao: Optional[Path] = None,
    max_tentativas: Optional[int] = None,
    backoff_base: Optional[float] = None,
    fator: Optional[float] = None,
) -> Dict[str, Any]:
    """Executa a Fase 2: MCP com retry/backoff; sem MCP, fallback Grep/Glob/Read."""
    raiz = Path(raiz)
    if not raiz.is_dir():
        raise FallbackOperacionalError(f"repositório inexistente: {raiz}")
    arquivos = list(arquivos)
    if not arquivos:
        raise FallbackOperacionalError("nenhum arquivo suspeito informado")

    probe = probe_mcp_com_retry(
        raiz,
        arquivos[0],
        max_tentativas=max_tentativas,
        backoff_base=backoff_base,
        fator=fator,
    )
    modo = "grafo" if probe.get("ok") else "fallback"

    analise: Optional[Dict[str, Any]] = None
    if modo == "fallback":
        por_arquivo: Dict[str, Any] = {}
        for rel in arquivos:
            por_arquivo[rel] = analisar_arquivo(raiz, rel, funcao)
        analise = {
            "arquivos": por_arquivo,
            "chamadores": buscar_chamadores(raiz, funcao) if funcao else [],
            "impacto_imports": {
                rel: busca_impacto_imports(raiz, rel) for rel in arquivos
            },
        }

    sessao_path: Optional[str] = None
    if sessao is not None:
        sessao_path = str(sessao)
        registrar_modo_fase2(
            Path(sessao),
            modo,
            {"probe": probe, "arquivos": arquivos, "funcao_alvo": funcao},
        )

    return {
        "status": "ok",
        "modo_fase2": modo,
        "probe": probe,
        "arquivos": arquivos,
        "funcao_alvo": funcao,
        "analise": analise,
        "sessao": sessao_path,
        "registrado_em": datetime.now(timezone.utc).isoformat(),
    }


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fallback.py",
        description="Fallback operacional da Fase 2 do aidd-diagnose (sem MCP).",
    )
    sub = parser.add_subparsers(dest="subcomando")

    p = sub.add_parser("analisar", help="analisa a Fase 2 com retry/backoff e fallback Grep/Glob/Read")
    p.add_argument("--repo", default=None, help="raiz do repositório (auto-detectada)")
    p.add_argument("--arquivos", nargs="+", required=True, help="arquivos suspeitos (relativos à raiz)")
    p.add_argument("--funcao", default=None, help="função alvo para callers/callees")
    p.add_argument("--sessao", default=None, help="caminho de sessao.json (default: última sessão)")
    p.add_argument("--max-tentativas", type=int, default=None)
    p.add_argument("--backoff-base", type=float, default=None)
    p.add_argument("--fator", type=float, default=None)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _construir_parser().parse_args(argv if argv is not None else sys.argv[1:])
    if not getattr(args, "subcomando", None):
        _construir_parser().print_help()
        return 2
    if args.subcomando != "analisar":
        _construir_parser().print_help()
        return 2

    try:
        raiz = Path(args.repo).resolve() if args.repo else encontrar_raiz()
        if not raiz.is_dir():
            raise FallbackOperacionalError(f"repositório inexistente: {raiz}")
        sessao = Path(args.sessao).resolve() if args.sessao else obter_sessao(raiz)
        if sessao is None:
            print(
                "Erro: nenhuma sessão encontrada; inicie antes com `python ecossistema.py diagnose iniciar --sintoma <texto>`.",
                file=sys.stderr,
            )
            return 1
        resultado = analisar_fase2(
            raiz,
            args.arquivos,
            funcao=args.funcao,
            sessao=sessao,
            max_tentativas=args.max_tentativas,
            backoff_base=args.backoff_base,
            fator=args.fator,
        )
    except FallbackOperacionalError as exc:
        print(f"[fallback] ERRO: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())