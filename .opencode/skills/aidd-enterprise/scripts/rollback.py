# -*- coding: utf-8 -*-
"""
Rollback transacional de aidd-enterprise (D14).

Transacao de injecao com snapshot pre-injecao e journal persistido:
  - Toda escrita tira snapshot do estado previo (conteudo ou ausencia) e e
    registrada no journal.
  - Falha no meio (erro ou exit 1) reverte arquivos modificados ao snapshot e
    purga artefatos parciais, deixando o workspace limpo (zero orfaos).
  - Crash abrupto e recuperado via journal pelo comando `rollback.py <raiz>`.
  - `workspace_limpo()` verifica a limpeza apos o rollback.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union

JOURNAL = ".ENTERPRISE-ROLLBACK-JOURNAL.json"
SNAPSHOT_DIR = ".ENTERPRISE-SNAPSHOT"
_VERSAO_JOURNAL = 1

PathLike = Union[str, Path]


def _carregar_isolamento():
    """Carrega o modulo irmao isolamento.py (guard de escrita D3)."""
    nome = "aidd_enterprise_isolamento_rollback"
    if nome in sys.modules:
        return sys.modules[nome]
    spec = importlib.util.spec_from_file_location(nome, str(Path(__file__).resolve().parent / "isolamento.py"))
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nome] = modulo
    spec.loader.exec_module(modulo)
    return modulo


class TransacaoEnterprise:
    """Transacao de escrita no alvo com snapshot pre-injecao e rollback deterministico."""

    def __init__(self, raiz: PathLike) -> None:
        self.raiz = Path(raiz).resolve()
        self.jornal = self.raiz / JOURNAL
        self.snapshot_raiz = self.raiz / SNAPSHOT_DIR
        self._arquivos: List[Path] = []
        self._dirs: List[Path] = []
        self._snapshots: Dict[str, str] = {}  # relativo -> nome do arquivo de snapshot
        self._arquivos_registrados: set = set()
        self._commitado = False

    def _persistir_jornal(self) -> None:
        dados = {
            "versao": _VERSAO_JOURNAL,
            "arquivos": [str(p.relative_to(self.raiz)) for p in self._arquivos],
            "dirs": [str(p.relative_to(self.raiz)) for p in self._dirs],
            "snapshots": dict(self._snapshots),
        }
        tmp = self.jornal.with_suffix(self.jornal.suffix + ".tmp")
        tmp.write_text(json.dumps(dados, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, self.jornal)

    def _capturar_snapshot(self, destino: Path) -> None:
        """Registra o estado previo do arquivo (conteudo ou ausencia) uma unica vez."""
        relativo = str(destino.relative_to(self.raiz))
        if relativo in self._snapshots:
            return
        if destino.is_file():
            self.snapshot_raiz.mkdir(parents=True, exist_ok=True)
            nome = f"{len(self._snapshots):04d}.bin"
            (self.snapshot_raiz / nome).write_bytes(destino.read_bytes())
            self._snapshots[relativo] = nome
        else:
            self._snapshots[relativo] = ""

    def escriturar(self, alvo_relativo: PathLike, conteudo: str) -> Path:
        """Escreve um arquivo dentro da raiz, com snapshot previo e journal para rollback."""
        isolamento = _carregar_isolamento()
        destino = (self.raiz / alvo_relativo).resolve()
        isolamento.validar_caminho_escrita(
            destino,
            repo_root=self.raiz,
            caminhos_permitidos=[str(alvo_relativo)],
            worktree_dir=None,
        )

        self._capturar_snapshot(destino)

        pai = destino.parent
        while pai != self.raiz and not pai.exists():
            self._dirs.append(pai)
            pai = pai.parent

        pai.mkdir(parents=True, exist_ok=True)
        destino.write_text(conteudo, encoding="utf-8")

        if destino not in self._arquivos_registrados:
            self._arquivos_registrados.add(destino)
            self._arquivos.append(destino)
        self._persistir_jornal()
        return destino

    def _restaurar(self, relativo: str, nome_snapshot: str, removidos: List[Path]) -> None:
        alvo = (self.raiz / relativo).resolve()
        try:
            alvo.relative_to(self.raiz)
        except ValueError:
            return
        if not nome_snapshot:
            if alvo.is_file():
                alvo.unlink()
                removidos.append(alvo)
            return
        origem = self.snapshot_raiz / nome_snapshot
        if origem.is_file():
            alvo.write_bytes(origem.read_bytes())
            removidos.append(alvo)
        elif alvo.is_file():
            alvo.unlink()
            removidos.append(alvo)

    def desfazer(self) -> List[Path]:
        """Reverte arquivos modificados ao snapshot e purga artefatos parciais (idempotente)."""
        removidos: List[Path] = []
        for relativo, nome_snapshot in list(self._snapshots.items()):
            self._restaurar(relativo, nome_snapshot, removidos)
        for diretorio in reversed(self._dirs):
            try:
                diretorio.resolve().relative_to(self.raiz)
            except ValueError:
                continue
            if diretorio.is_dir() and not any(diretorio.iterdir()):
                diretorio.rmdir()
                removidos.append(diretorio)
        self._limpar_metadados()
        return removidos

    def _limpar_metadados(self) -> None:
        if self.snapshot_raiz.is_dir():
            for arquivo in sorted(self.snapshot_raiz.glob("*")):
                arquivo.unlink(missing_ok=True)
            self.snapshot_raiz.rmdir()
        self.jornal.unlink(missing_ok=True)
        self._arquivos.clear()
        self._dirs.clear()
        self._snapshots.clear()
        self._arquivos_registrados.clear()

    def concluir(self) -> None:
        """Marca a transacao como concluida e remove journal + snapshot (commit)."""
        self._limpar_metadados()
        self._commitado = True

    def __enter__(self) -> "TransacaoEnterprise":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            self.desfazer()
        return False


def executar_com_rollback(
    raiz: PathLike,
    etapas: Sequence[Callable[[TransacaoEnterprise], None]],
) -> int:
    """
    Executa as etapas da injecao dentro de uma transacao.
    Qualquer falha -> rollback total (reversao + purga) + exit 1; sucesso -> commit + exit 0.
    """
    try:
        with TransacaoEnterprise(raiz) as tx:
            for etapa in etapas:
                etapa(tx)
            tx.concluir()
    except Exception as exc:
        print(f"[aidd-enterprise] rollback executado apos falha: {exc}", file=sys.stderr)
        return 1
    return 0


def workspace_limpo(raiz: PathLike) -> bool:
    """Verifica a limpeza pos-rollback: sem journal, sem snapshot e sem artefatos parciais."""
    base = Path(raiz).resolve()
    return not (base / JOURNAL).exists() and not (base / SNAPSHOT_DIR).exists()


def recuperar(raiz: PathLike) -> List[Path]:
    """
    Reverte um crash abrupto usando o journal + snapshot: restaura arquivos
    pre-existentes e remove artefatos parciais. Retorna a lista de itens tratados.
    """
    base = Path(raiz).resolve()
    journal = base / JOURNAL
    if not journal.is_file():
        return []
    try:
        dados = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"journal corrompido, limpeza nao garantida: {exc}") from exc
    if not isinstance(dados, dict) or dados.get("versao") != _VERSAO_JOURNAL:
        raise ValueError("journal com formato desconhecido, limpeza nao garantida")

    removidos: List[Path] = []
    snapshots: Dict[str, str] = dict(dados.get("snapshots") or {})
    snapshot_raiz = base / SNAPSHOT_DIR

    for relativo in dados.get("arquivos", []):
        if relativo in snapshots:
            continue  # tratado abaixo com o snapshot correspondente
        alvo = (base / relativo).resolve()
        try:
            alvo.relative_to(base)
        except ValueError:
            continue
        if alvo.is_file():
            alvo.unlink()
            removidos.append(alvo)

    for relativo, nome_snapshot in snapshots.items():
        alvo = (base / relativo).resolve()
        try:
            alvo.relative_to(base)
        except ValueError:
            continue
        if not nome_snapshot:
            if alvo.is_file():
                alvo.unlink()
                removidos.append(alvo)
            continue
        origem = snapshot_raiz / nome_snapshot
        if origem.is_file():
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_bytes(origem.read_bytes())
            removidos.append(alvo)
        elif alvo.is_file():
            alvo.unlink()
            removidos.append(alvo)

    for relativo in reversed(dados.get("dirs", [])):
        alvo = (base / relativo).resolve()
        try:
            alvo.relative_to(base)
        except ValueError:
            continue
        if alvo.is_dir() and not any(alvo.iterdir()):
            alvo.rmdir()
            removidos.append(alvo)

    if snapshot_raiz.is_dir():
        for arquivo in sorted(snapshot_raiz.glob("*")):
            arquivo.unlink(missing_ok=True)
        snapshot_raiz.rmdir()
        removidos.append(snapshot_raiz)
    journal.unlink(missing_ok=True)
    removidos.append(journal)
    return removidos


def main(args: Optional[List[str]] = None) -> int:
    """Entrypoint CLI: rollback.py <pasta_alvo>. exit 1 sem argumento ou com limpeza impossivel."""
    argv = list(sys.argv[1:] if args is None else args)
    if len(argv) != 1:
        print("Uso: rollback.py <pasta_alvo>", file=sys.stderr)
        return 1
    raiz = Path(argv[0])
    try:
        recuperar(raiz)
    except ValueError as exc:
        print(f"[aidd-enterprise][rollback] {exc}", file=sys.stderr)
        return 1
    if not workspace_limpo(raiz):
        print("[aidd-enterprise][rollback] workspace ainda sujo apos recuperacao.", file=sys.stderr)
        return 1
    print("[aidd-enterprise][rollback] workspace limpo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
