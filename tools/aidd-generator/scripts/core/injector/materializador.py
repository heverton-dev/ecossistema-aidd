#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MATERIALIZADOR — Escrita transacional em disco com rollback automatico
aidd-generator — Injetor Universal de Componentes

Escreve um conjunto de arquivos primeiro em uma area de staging isolada
(`.aidd/cache/_injector_staging/<id>/`), valida que todas as escritas
tiveram sucesso, e so entao move atomicamente (`os.replace`) cada arquivo
para seu destino final. Qualquer falha durante staging ou a fase de
publicacao aciona rollback: tudo que ja foi publicado nesta transacao e
removido, sem tocar em nada pre-existente no repositorio — zero arquivos
orfaos em caso de interrupcao.
"""

import os
import shutil
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class ArquivoJaExisteError(FileExistsError):
    """Levantado quando um destino final ja existe e `force=False`."""


@dataclass
class ResultadoMaterializacao:
    """Resultado de uma transacao de materializacao."""

    sucesso: bool
    arquivos_publicados: List[str] = field(default_factory=list)
    erro: Optional[str] = None


def _staging_dir(root: Path) -> Path:
    base = root / ".aidd" / "cache" / "_injector_staging" / uuid.uuid4().hex[:12]
    base.mkdir(parents=True, exist_ok=True)
    return base


def materializar(
    root: Path,
    arquivos: Dict[str, str],
    force: bool = False,
) -> ResultadoMaterializacao:
    """
    Materializa um conjunto de arquivos de forma transacional.

    Args:
        root: diretorio raiz do projeto (destinos sao relativos a ele).
        arquivos: mapa `caminho_relativo -> conteudo_texto`.
        force: se True, permite sobrescrever destinos ja existentes.

    Returns:
        ResultadoMaterializacao. Quando `sucesso=False`, garante que nenhum
        arquivo de `arquivos_publicados` permaneceu no disco (rollback).
    """
    root = Path(root)
    staging = _staging_dir(root)
    publicados: List[str] = []

    try:
        # 1. Validacao previa: nenhum destino pode existir sem `force`.
        if not force:
            for rel_path in arquivos:
                destino = root / rel_path
                if destino.exists():
                    raise ArquivoJaExisteError(f"destino ja existe: {rel_path}")

        # 2. Escrever tudo em staging primeiro (falha aqui nao toca no repo real).
        staged_paths: Dict[str, Path] = {}
        for rel_path, conteudo in arquivos.items():
            staged_file = staging / rel_path
            staged_file.parent.mkdir(parents=True, exist_ok=True)
            staged_file.write_text(conteudo, encoding="utf-8")
            staged_paths[rel_path] = staged_file

        # 3. Publicar: mover atomicamente de staging para o destino final.
        for rel_path, staged_file in staged_paths.items():
            destino = root / rel_path
            destino.parent.mkdir(parents=True, exist_ok=True)
            os.replace(str(staged_file), str(destino))
            publicados.append(rel_path)

        return ResultadoMaterializacao(sucesso=True, arquivos_publicados=publicados)

    except Exception as exc:  # noqa: BLE001 — precisa capturar qualquer falha de I/O para rollback
        _rollback(root, publicados)
        return ResultadoMaterializacao(sucesso=False, arquivos_publicados=[], erro=str(exc))

    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _rollback(root: Path, publicados: List[str]) -> None:
    """Remove arquivos ja publicados nesta transacao (e diretorios vazios criados)."""
    for rel_path in publicados:
        destino = root / rel_path
        if destino.exists():
            destino.unlink()
        # Remove diretorios pais que ficaram vazios por causa desta transacao.
        pai = destino.parent
        while pai != root and pai.exists() and not any(pai.iterdir()):
            pai.rmdir()
            pai = pai.parent
