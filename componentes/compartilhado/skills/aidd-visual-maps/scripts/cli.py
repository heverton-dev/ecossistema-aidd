# -*- coding: utf-8 -*-
"""
AIDD-Visual-Maps CLI: ponto único de entrada dos mapas visuais (ciclo-01, Ticket 13).

Subcomandos:
  catalogo [args]       -> scripts/catalogo_pecas.py [args]
  mapa <tipo> [args]    -> scripts/mapa_visual.py <tipo> [args]
  gerar                 -> catálogo -> cada mapa de MAPAS_PREVISTOS -> índice -> livro, nessa
                           ordem, numa worktree efêmera (HEAD + índice + árvore de trabalho);
                           depois o build do aidd-textbook; só os arquivos das pastas
                           permitidas (escopo_escrita_mapas) voltam ao repositório, num lote só
                           via gravar_lote, e o manifesto (handoff.py) é emitido por último.
                           Etapa com erro: nada volta. Build do livro com erro: fica registrado
                           no manifesto (exit_code) e o gerar segue.
  check                 -> frescor do catálogo, --check de cada mapa e do índice, --check do
                           livro e o manifesto (hash de cada arquivo); exit 1 no primeiro desvio.

Uso: python ecossistema.py visual-maps <subcomando>  (ou aidd-visual-maps)
Exit 0: ok. Exit 1: erro ou desvio. Exit 2: subcomando inválido.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def find_repo_root(start_path: Path | None = None) -> Path:
    """Raiz do repositório: primeira pasta acima com ecossistema.py e scripts/mapa_visual.py
    (vale para a fonte canônica e para as cópias por harness)."""
    current = (start_path or Path(__file__)).resolve()
    for parent in [current, *current.parents]:
        if (parent / "ecossistema.py").is_file() and (parent / "scripts" / "mapa_visual.py").is_file():
            return parent
    return Path(__file__).resolve().parents[4]


REPO_ROOT = find_repo_root()
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import catalogo_pecas as cp  # noqa: E402
import livro_mapas  # noqa: E402
import mapa_visual as mv  # noqa: E402
from escopo_escrita_mapas import PASTAS_PERMITIDAS  # noqa: E402
from gravacao_atomica_mapas import gravar_lote  # noqa: E402
from telemetria_mapas import destino as destino_medicoes  # noqa: E402

# Variáveis que um hook do git exporta e que apontariam os comandos da worktree efêmera
# para o repositório de quem chamou (caso real: hook vazando GIT_DIR em worktree).
GIT_VARIAVEIS_DE_CONTEXTO = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX", "GIT_COMMON_DIR")


def tipos_na_ordem() -> list[str]:
    """Ordem obrigatória dos mapas: cada tipo de MAPAS_PREVISTOS e, por último, o índice
    (o índice lê o status dos outros)."""
    return [*(tipo for tipo, _, _ in mv.MAPAS_PREVISTOS), "indice"]


def ambiente() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in GIT_VARIAVEIS_DE_CONTEXTO}
    env.setdefault("AIDD_MEDICOES_DIR", str(destino_medicoes().parent))
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _git(cwd: Path, *args: str) -> bytes:
    proc = subprocess.run(["git", *args], cwd=cwd, env=ambiente(), capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {proc.stderr.decode('utf-8', 'replace').strip()}")
    return proc.stdout


def _lista_z(saida: bytes) -> list[str]:
    return [p for p in saida.decode("utf-8").split("\0") if p]


def _script(nome: str, args: list[str]) -> int:
    return subprocess.run([sys.executable, str(SCRIPTS / nome), *args], cwd=REPO_ROOT).returncode


# --- worktree efêmera -------------------------------------------------------------------

def criar_worktree_efemera() -> Path:
    """Worktree no diretório temporário com o mesmo estado de quem chamou: árvore do índice
    (o catálogo usa git ls-files) e, por cima, os arquivos modificados, novos e apagados.
    Os SKILL.md ignorados pelo git (pastas de harness locais) também vão: o catálogo conta
    as skills em disco de cada harness."""
    arvore = _git(REPO_ROOT, "write-tree").decode().strip()
    destino = Path(tempfile.mkdtemp(prefix="aidd-visual-maps-")) / "wt"
    _git(REPO_ROOT, "worktree", "add", "--detach", "--no-checkout", str(destino), "HEAD")
    _git(destino, "read-tree", "--reset", "-u", arvore)
    copiar = _lista_z(_git(REPO_ROOT, "ls-files", "-z", "--modified", "--others", "--exclude-standard"))
    copiar += _lista_z(_git(REPO_ROOT, "ls-files", "-z", "--others", "--ignored", "--exclude-standard",
                            "--", ":(glob)**/SKILL.md"))
    for rel in copiar:
        origem = REPO_ROOT / rel
        if origem.is_file():
            (destino / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origem, destino / rel)
    for rel in _lista_z(_git(REPO_ROOT, "ls-files", "-z", "--deleted")):
        (destino / rel).unlink(missing_ok=True)
    return destino


def remover_worktree_efemera(worktree: Path) -> None:
    try:
        _git(REPO_ROOT, "worktree", "remove", "--force", str(worktree))
    except RuntimeError as erro:
        print(f"[AVISO] {erro}", file=sys.stderr)
    shutil.rmtree(worktree.parent, ignore_errors=True)
    try:
        _git(REPO_ROOT, "worktree", "prune")
    except RuntimeError as erro:
        print(f"[AVISO] {erro}", file=sys.stderr)


def _arquivos_permitidos(raiz: Path) -> set[str]:
    """Arquivos (caminho relativo) dentro das pastas que os mapas podem gravar, sem os
    temporários de gravar_lote."""
    achados = set()
    for pasta in PASTAS_PERMITIDAS:
        for arquivo in (raiz / pasta).rglob("*"):
            if arquivo.is_file() and not (arquivo.name.startswith(".") and arquivo.name.endswith(".tmp")):
                achados.add(arquivo.relative_to(raiz).as_posix())
    return achados


def etapas() -> list[tuple[str, list[str]]]:
    """Pipeline do gerar, na ordem: catálogo, mapas (índice por último), livro."""
    return [("catalogo_pecas.py", []), *(("mapa_visual.py", [tipo]) for tipo in tipos_na_ordem()),
            ("livro_mapas.py", [])]


def promover(worktree: Path, antes: set[str]) -> tuple[int, int]:
    """Copia para o repositório, num lote só, o que mudou nas pastas permitidas da worktree,
    e apaga o que o pipeline removeu lá. Devolve (gravados, removidos)."""
    depois = _arquivos_permitidos(worktree)
    pares = {}
    for rel in sorted(depois):
        novo = (worktree / rel).read_bytes()
        alvo = REPO_ROOT / rel
        if not alvo.is_file() or alvo.read_bytes() != novo:
            pares[alvo] = novo
    gravar_lote(pares)
    removidos = sorted(antes - depois)
    for rel in removidos:
        (REPO_ROOT / rel).unlink(missing_ok=True)
    return len(pares), len(removidos)


def cmd_gerar() -> int:
    import handoff  # importa este módulo: import tardio
    try:
        worktree = criar_worktree_efemera()
    except (RuntimeError, OSError) as erro:
        print(f"[ERRO] worktree efêmera não criada: {erro}")
        return 1
    try:
        antes = _arquivos_permitidos(worktree)
        for script, args in etapas():
            print(f"[ETAPA] {script} {' '.join(args)}".rstrip(), flush=True)
            rc = subprocess.run([sys.executable, str(worktree / "scripts" / script), *args],
                                cwd=worktree, env=ambiente()).returncode
            if rc != 0:
                print(f"[ERRO] etapa {script} {' '.join(args)} saiu com {rc}; nada foi promovido.")
                return 1
        exit_build = handoff.compilar_livro(worktree)
        if exit_build != 0:
            print(f"[AVISO] build do aidd-textbook saiu com {exit_build}; registrado no manifesto.")
        gravados, removidos = promover(worktree, antes)
    except (OSError, ValueError) as erro:
        print(f"[ERRO] promoção falhou (gravar_lote desfaz o lote): {erro}")
        return 1
    finally:
        remover_worktree_efemera(worktree)
    try:
        handoff.emitir_manifesto(exit_build)
    except (OSError, ValueError) as erro:
        print(f"[ERRO] manifesto não gravado: {erro}")
        return 1
    print(f"[OK] gerar: {gravados} arquivo(s) promovido(s), {removidos} removido(s).")
    return 0


def cmd_check() -> int:
    import handoff  # importa este módulo: import tardio
    em_dia, divergentes = cp.catalogo_em_dia(cp.RAIZ, cp.SAIDA_PADRAO)
    if not em_dia:
        print(f"[DESATUALIZADO] catálogo {cp.SAIDA_PADRAO} difere do repositório ({', '.join(divergentes)}). "
              "Rode: python ecossistema.py visual-maps gerar")
        return 1
    for tipo in tipos_na_ordem():
        if mv.main([tipo, "--check"]) != 0:
            return 1
    if livro_mapas.main(["--check"]) != 0:
        return 1
    desvios = handoff.conferir_manifesto()
    for desvio in desvios:
        print(f"[DESATUALIZADO] MANIFESTO-MAPAS.json: {desvio}. Rode: python ecossistema.py visual-maps gerar")
    if desvios:
        return 1
    print("[OK] visual-maps: catálogo, mapas, livro e manifesto em dia.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="visual-maps", description="Mapas visuais do Ecossistema AIDD.")
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("catalogo", help="gera (ou confere) o catálogo de peças", add_help=False)
    mapa = sub.add_parser("mapa", help="gera (ou confere) um mapa", add_help=False)
    mapa.add_argument("tipo")
    sub.add_parser("gerar", help="pipeline completo numa worktree efêmera")
    sub.add_parser("check", help="confere catálogo, mapas e livro")
    args, resto = parser.parse_known_args(argv)
    if args.comando == "catalogo":
        return _script("catalogo_pecas.py", resto)
    if args.comando == "mapa":
        return _script("mapa_visual.py", [args.tipo, *resto])
    if resto:
        parser.error(f"argumentos não reconhecidos: {' '.join(resto)}")
    return cmd_gerar() if args.comando == "gerar" else cmd_check()


if __name__ == "__main__":
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")
    sys.exit(main())
