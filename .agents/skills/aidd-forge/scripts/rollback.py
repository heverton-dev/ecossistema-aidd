# -*- coding: utf-8 -*-
"""
Rollback transacional de aidd-forge (D14 / DoD 7).

Transacao de bootstrap com journal persistido: toda escrita e registrada e,
em caso de falha, os arquivos criados sao revertidos e os diretórios vazios
removidos, restaurando o estado limpo do alvo. Falha abrupta (crash) e
recuperada via journal pelo comando `rollback.py <pasta_alvo>`.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Union

JOURNAL = ".FORGE-ROLLBACK-JOURNAL.json"
_VERSAO_JOURNAL = 1

PathLike = Union[str, Path]


def _carregar_isolamento():
    """Carrega o modulo irmao isolamento.py (guard de escrita D3)."""
    nome = "aidd_forge_isolamento_rollback"
    if nome in sys.modules:
        return sys.modules[nome]
    spec = importlib.util.spec_from_file_location(nome, str(Path(__file__).resolve().parent / "isolamento.py"))
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nome] = modulo
    spec.loader.exec_module(modulo)
    return modulo


class TransacaoForge:
    """Transação transacional de escrita no alvo com rollback determinístico."""

    def __init__(self, raiz: PathLike) -> None:
        self.raiz = Path(raiz).resolve()
        self.jornal = self.raiz / JOURNAL
        self._arquivos: List[Path] = []
        self._dirs: List[Path] = []
        self._arquivos_registrados: set = set()
        self._commitado = False

    def _persistir_jornal(self) -> None:
        dados = {
            "versao": _VERSAO_JOURNAL,
            "arquivos": [str(p.relative_to(self.raiz)) for p in self._arquivos],
            "dirs": [str(p.relative_to(self.raiz)) for p in self._dirs],
        }
        tmp = self.jornal.with_suffix(self.jornal.suffix + ".tmp")
        tmp.write_text(json.dumps(dados, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, self.jornal)

    def escriturar(self, alvo_relativo: PathLike, conteudo: str) -> Path:
        """Escreve um arquivo dentro da raiz, registrando-o no journal para rollback."""
        isolamento = _carregar_isolamento()
        destino = (self.raiz / alvo_relativo).resolve()
        isolamento.validar_caminho_escrita(destino, repo_root=self.raiz, worktree_dir=None)

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

    def desfazer(self) -> List[Path]:
        """Reverte todos os arquivos/dirs criados por esta transação (idempotente)."""
        removidos: List[Path] = []
        for arquivo in reversed(self._arquivos):
            try:
                arquivo.resolve().relative_to(self.raiz)
            except ValueError:
                continue
            if arquivo.is_file():
                arquivo.unlink()
                removidos.append(arquivo)
        for diretorio in reversed(self._dirs):
            try:
                diretorio.resolve().relative_to(self.raiz)
            except ValueError:
                continue
            if diretorio.is_dir() and not any(diretorio.iterdir()):
                diretorio.rmdir()
                removidos.append(diretorio)
        if self.jornal.is_file():
            self.jornal.unlink()
            removidos.append(self.jornal)
        self._arquivos.clear()
        self._dirs.clear()
        self._arquivos_registrados.clear()
        return removidos

    def concluir(self) -> None:
        """Marca a transação como concluída e remove o journal (commit)."""
        if self.jornal.is_file():
            self.jornal.unlink()
        self._commitado = True

    def __enter__(self) -> "TransacaoForge":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            self.desfazer()
        return False


def executar_com_rollback(
    raiz: PathLike,
    etapas: Sequence[Callable[[TransacaoForge], None]],
) -> int:
    """
    Executa as etapas do bootstrap dentro de uma transação.
    Qualquer falha -> rollback total + exit 1; sucesso -> commit + exit 0.
    """
    try:
        with TransacaoForge(raiz) as tx:
            for etapa in etapas:
                etapa(tx)
            tx.concluir()
    except Exception as exc:
        print(f"[aidd-forge] rollback executado apos falha: {exc}", file=sys.stderr)
        return 1
    return 0


def recuperar(raiz: PathLike) -> List[Path]:
    """Remove órfãos deixados por um crash abrupto usando o journal transacional."""
    raiz = Path(raiz).resolve()
    journal = raiz / JOURNAL
    if not journal.is_file():
        return []
    try:
        dados = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        journal.unlink(missing_ok=True)
        return []

    removidos: List[Path] = []
    for relativo in dados.get("arquivos", []):
        alvo = (raiz / relativo).resolve()
        try:
            alvo.relative_to(raiz)
        except ValueError:
            continue
        if alvo.is_file():
            alvo.unlink()
            removidos.append(alvo)
    for relativo in reversed(dados.get("dirs", [])):
        alvo = (raiz / relativo).resolve()
        try:
            alvo.relative_to(raiz)
        except ValueError:
            continue
        if alvo.is_dir() and not any(alvo.iterdir()):
            alvo.rmdir()
            removidos.append(alvo)
    journal.unlink(missing_ok=True)
    removidos.append(journal)
    return removidos


def main(args: Optional[List[str]] = None) -> int:
    """Entrypoint CLI: rollback.py <pasta_alvo> — recuperação pós-crash. exit 1 sem argumento."""
    argv = list(sys.argv[1:] if args is None else args)
    if len(argv) != 1:
        print("Uso: rollback.py <pasta_alvo>", file=sys.stderr)
        return 1
    removidos = recuperar(argv[0])
    if removidos:
        print(f"[aidd-forge] rollback recuperou {len(removidos)} item(ns).")
    else:
        print("[aidd-forge] nada a recuperar (estado limpo).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
