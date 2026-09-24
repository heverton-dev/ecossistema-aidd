# -*- coding: utf-8 -*-
"""
Rollback e Limpeza da Instrumentação para aidd-diagnose (Ticket 7 / D14 / DoD 7).

Critério de Rejeição (Rollback) — 3 garantias determinísticas:
1. Toda instrumentação temporária da Fase 4 é etiquetada com o marcador
   AIDD-DIAGNOSE-TEMP no fim da linha (marcar_instrumentacao_temporaria).
2. Ao fim da Fase 5 OU em exceção: varre o diff (rastreados + untracked),
   remove as linhas marcadas e descarta a worktree efêmera do Ticket 2
   (../worktrees_diagnose-<slug>/ e branches diagnose/<slug>-*).
3. Em qualquer saída não-zero, docs/diagnosticos/ fica sem arquivos parciais:
   snapshot dos arquivos pré-existentes é restaurado e temporários registrados
   são removidos (artefatos finais só sobrevivem via commit()).

Reaproveita o padrão determinístico de aidd-melhoria/scripts/rollback.py (D14).
"""

from __future__ import annotations

import contextlib
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

MARCADOR_TEMP = "AIDD-DIAGNOSE-TEMP"


def _encontrar_raiz_repo() -> Path:
    """Encontra a raiz do repositório procurando por ecossistema.py."""
    atual = Path(__file__).resolve()
    for parent in [atual, *atual.parents]:
        if (parent / "ecossistema.py").is_file():
            return parent
    return atual.parents[4]


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(repo_root), capture_output=True, text=True
    )


def marcar_instrumentacao_temporaria(linha: str) -> str:
    """
    Etiqueta UMA linha de instrumentação temporária da Fase 4 com o marcador
    AIDD-DIAGNOSE-TEMP no fim da linha (idempotente).
    """
    if MARCADOR_TEMP in linha:
        return linha
    base = linha.rstrip("\r\n")
    return f"{base}  # {MARCADOR_TEMP}"


def _linha_marcada(linha: str) -> bool:
    """Linha marcada = termina com o marcador após rstrip (convenção de tag final)."""
    return linha.rstrip("\r\n").rstrip().endswith(MARCADOR_TEMP)


def _arquivos_em_diff(repo_root: Path) -> Tuple[Set[Path], Set[Path]]:
    """Retorna (rastreados_modificados, untracked) como caminhos absolutos."""
    rastreados: Set[Path] = set()
    res = _git(repo_root, "diff", "--name-only", "HEAD")
    if res.returncode == 0:
        nomes = res.stdout.splitlines()
    else:
        # Repo sem HEAD ainda: usa worktree->index e index->HEAD separadamente.
        nomes = []
        for args in (("diff", "--name-only"), ("diff", "--cached", "--name-only")):
            parcial = _git(repo_root, *args)
            if parcial.returncode == 0:
                nomes.extend(parcial.stdout.splitlines())
    for nome in nomes:
        nome = nome.strip()
        if nome:
            rastreados.add((repo_root / nome).resolve())

    nao_rastreados: Set[Path] = set()
    res = _git(repo_root, "ls-files", "--others", "--exclude-standard")
    if res.returncode == 0:
        for nome in res.stdout.splitlines():
            nome = nome.strip()
            if nome:
                nao_rastreados.add((repo_root / nome).resolve())
    return rastreados, nao_rastreados


def remover_marcadores_diff(repo_root: Optional[str | Path] = None) -> List[Path]:
    """
    Varre o diff (rastreados modificados + untracked) e remove as linhas com o
    marcador AIDD-DIAGNOSE-TEMP. Arquivo untracked que fica vazio é deletado
    (era 100% instrumentação temporária). Retorna os caminhos alterados.
    """
    raiz = Path(repo_root).resolve() if repo_root else _encontrar_raiz_repo()
    rastreados, nao_rastreados = _arquivos_em_diff(raiz)
    alterados: List[Path] = []

    for caminho in sorted(rastreados | nao_rastreados):
        if not caminho.is_file():
            continue
        try:
            conteudo = caminho.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if MARCADOR_TEMP not in conteudo:
            continue
        linhas = conteudo.splitlines(keepends=True)
        restantes = [linha for linha in linhas if not _linha_marcada(linha)]
        if len(restantes) == len(linhas):
            continue
        if not "".join(restantes).strip() and caminho in nao_rastreados:
            caminho.unlink(missing_ok=True)
        else:
            caminho.write_text("".join(restantes), encoding="utf-8")
        alterados.append(caminho)
    return alterados


def descartar_worktree_fase4(
    repo_root: Optional[str | Path] = None,
    slug: Optional[str] = None,
) -> List[Path]:
    """
    Descarta a worktree efêmera do Ticket 2 (../worktrees_diagnose-<slug>/),
    sua branch diagnose/<slug>-* e resquícios de disco (git worktree prune).
    Com slug=None varre todas as worktrees_diagnose-* e branches diagnose/*.
    """
    raiz = Path(repo_root).resolve() if repo_root else _encontrar_raiz_repo()
    descartadas: List[Path] = []
    nome_esperado = f"worktrees_diagnose-{slug}" if slug else None

    # 1. Worktrees registradas no git.
    res = _git(raiz, "worktree", "list", "--porcelain")
    alvos: List[Tuple[Path, Optional[str]]] = []
    if res.returncode == 0:
        caminho_atual: Optional[Path] = None
        branch_atual: Optional[str] = None
        for linha in res.stdout.splitlines():
            if linha.startswith("worktree "):
                caminho_atual = Path(linha[len("worktree "):].strip())
                branch_atual = None
            elif linha.startswith("branch "):
                branch_atual = linha[len("branch "):].strip().replace("refs/heads/", "", 1)
            elif not linha.strip() and caminho_atual is not None:
                alvos.append((caminho_atual, branch_atual))
                caminho_atual = None
                branch_atual = None
        if caminho_atual is not None:
            alvos.append((caminho_atual, branch_atual))

    for caminho, branch in alvos:
        if not caminho.name.startswith("worktrees_diagnose-"):
            continue
        if nome_esperado is not None and caminho.name != nome_esperado:
            continue
        _git(raiz, "worktree", "remove", "--force", str(caminho))
        if caminho.exists():
            shutil.rmtree(caminho, ignore_errors=True)
        descartadas.append(caminho)
        if branch and branch.startswith("diagnose/"):
            _git(raiz, "branch", "-D", branch)

    # 2. Resquícios de disco não registrados (ou com registro corrompido).
    for candidato in sorted(raiz.parent.glob("worktrees_diagnose-*")):
        if nome_esperado is not None and candidato.name != nome_esperado:
            continue
        if candidato.exists():
            shutil.rmtree(candidato, ignore_errors=True)
            descartadas.append(candidato)

    # 3. Branches diagnose/<slug>-* órfãs (ou diagnose/* quando slug é None).
    padrao_branch = f"diagnose/{slug}-*" if slug else "diagnose/*"
    res = _git(raiz, "branch", "--list", padrao_branch)
    if res.returncode == 0:
        for linha in res.stdout.splitlines():
            nome = linha.strip().lstrip("*").strip()
            if nome.startswith("diagnose/"):
                _git(raiz, "branch", "-D", nome)

    _git(raiz, "worktree", "prune")
    return descartadas


class RollbackDiagnose:
    """
    Context manager determinístico da sessão de diagnose:
    - commit()  → Fase 5 concluída: remove marcadores, descarta worktree,
                  apaga temporários registrados e PRESERVA artefatos finais.
    - rollback() → saída não-zero / exceção: remove marcadores, descarta
                  worktree, restaura docs/diagnosticos/ ao snapshot do entry
                  (zero arquivos parciais) e apaga temporários.
    Sair do bloco sem commit() dispara rollback() (mesma semântica de
    aidd-melhoria GerenciadorRollback).
    """

    def __init__(
        self,
        repo_root: Optional[str | Path] = None,
        slug: Optional[str] = None,
    ) -> None:
        self.repo_root = Path(repo_root).resolve() if repo_root else _encontrar_raiz_repo()
        self.slug = slug
        self.comitado = False
        self._rollback_executado = False
        self._temporarios: Set[Path] = set()
        self._snapshot_arquivos: Dict[Path, bytes] = {}
        self._snapshot_dirs: Set[Path] = set()

    def __enter__(self) -> "RollbackDiagnose":
        diagnosticos = (self.repo_root / "docs" / "diagnosticos").resolve()
        if diagnosticos.is_dir():
            self._snapshot_dirs.add(diagnosticos)
            for item in diagnosticos.rglob("*"):
                if item.is_dir():
                    self._snapshot_dirs.add(item.resolve())
                elif item.is_file():
                    with contextlib.suppress(OSError):
                        self._snapshot_arquivos[item.resolve()] = item.read_bytes()
        return self

    def registrar_temporario(self, caminho: str | Path) -> Path:
        """Registra um arquivo intermediário para exclusão garantida em qualquer saída."""
        caminho_abs = Path(caminho).resolve()
        self._temporarios.add(caminho_abs)
        return caminho_abs

    def commit(self) -> None:
        """Fase 5 concluída com sucesso: limpa instrumentação e preserva finais."""
        if self._rollback_executado:
            return
        remover_marcadores_diff(self.repo_root)
        descartar_worktree_fase4(self.repo_root, self.slug)
        self._limpar_temporarios()
        self.comitado = True

    def rollback(self) -> None:
        """Saída não-zero / exceção: zero rastro de instrumentação ou parciais."""
        if self._rollback_executado:
            return
        remover_marcadores_diff(self.repo_root)
        descartar_worktree_fase4(self.repo_root, self.slug)
        self._restaurar_snapshot()
        self._limpar_temporarios()
        self._rollback_executado = True

    def _limpar_temporarios(self) -> None:
        for caminho in list(self._temporarios):
            with contextlib.suppress(OSError):
                Path(caminho).unlink(missing_ok=True)
        self._temporarios.clear()

    def _restaurar_snapshot(self) -> None:
        """Remove parciais criados na sessão e restaura o conteúdo prévio."""
        diagnosticos = (self.repo_root / "docs" / "diagnosticos").resolve()
        if diagnosticos.is_dir():
            atuais = {
                item.resolve()
                for item in diagnosticos.rglob("*")
                if item.is_file()
            }
            for caminho in sorted(atuais):
                if caminho in self._snapshot_arquivos:
                    if caminho.read_bytes() != self._snapshot_arquivos[caminho]:
                        caminho.write_bytes(self._snapshot_arquivos[caminho])
                else:
                    caminho.unlink(missing_ok=True)
            # Diretórios criados durante a sessão saem se ficaram vazios.
            dirs_atuais = sorted(
                (item for item in diagnosticos.rglob("*") if item.is_dir()),
                key=lambda item: len(item.parts),
                reverse=True,
            )
            for diretorio in dirs_atuais:
                if diretorio.resolve() not in self._snapshot_dirs:
                    with contextlib.suppress(OSError):
                        diretorio.rmdir()
            if (
                diagnosticos not in self._snapshot_dirs
                and not any(diagnosticos.iterdir())
            ):
                with contextlib.suppress(OSError):
                    diagnosticos.rmdir()

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if not self.comitado:
            self.rollback()
        return False


def finalizar_fase5(
    repo_root: Optional[str | Path] = None,
    slug: Optional[str] = None,
) -> int:
    """
    Fim da Fase 5: varre o diff, remove linhas marcadas e descarta a worktree
    do Ticket 2. Retorna 0 em sucesso e 1 em falha (exit code real).
    """
    raiz = Path(repo_root).resolve() if repo_root else _encontrar_raiz_repo()
    try:
        remover_marcadores_diff(raiz)
        descartar_worktree_fase4(raiz, slug)
        return 0
    except Exception as exc:  # pragma: no cover - defesa de fronteira git/FS
        sys.stderr.write(f"[ROLLBACK] Falha na finalização da Fase 5: {exc}\n")
        return 1


def executar_com_rollback(
    funcao_operacao: Callable[[RollbackDiagnose], int],
    repo_root: Optional[str | Path] = None,
    slug: Optional[str] = None,
) -> int:
    """
    Executa a operação sob RollbackDiagnose. Código 0 → commit (finais
    preservados); código != 0 → rollback (zero parciais). Exceção propaga
    após rollback determinístico.
    """
    with RollbackDiagnose(repo_root=repo_root, slug=slug) as gestor:
        codigo = funcao_operacao(gestor)
        if codigo == 0:
            gestor.commit()
        else:
            gestor.rollback()
        return codigo
