#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gravação atômica de um lote de arquivos dos mapas visuais (aidd-visual-maps, D14).

gravar_lote({destino: texto, ...}) grava tudo ou nada: cada texto vai primeiro para um
temporário na mesma pasta do destino; só depois que todos foram escritos é que os
destinos são trocados com os.replace. Se qualquer passo falha, os temporários são
apagados e os destinos já trocados voltam ao conteúdo de antes (cópia em memória; o
que não existia é removido), e a exceção original sobe com o atributo `arquivo`.
Os textos são gravados em UTF-8 com fim de linha LF em qualquer sistema; bytes (o PDF
do livro, promovido pelo `visual-maps gerar`) são gravados como vieram. Cada os.replace
passa por com_retry (resiliencia_mapas): arquivo preso por instantes não derruba o lote.

Usado pelo mapa_visual.py (par técnico/não técnico), pelo compilar_mapas_nao_tecnicos.py
(todos os tipos num lote só) e pelo livro_mapas.py.
"""
import os
from pathlib import Path

from escopo_escrita_mapas import garantir_escopo
from resiliencia_mapas import com_retry


def _temporario(destino: Path) -> Path:
    return destino.with_name(f".{destino.name}.{os.getpid()}.tmp")


def gravar_lote(pares: dict[Path, str | bytes]) -> list[Path]:
    """Grava todos os pares (destino -> texto) ou nenhum; devolve os destinos gravados.
    Em erro, desfaz o que já foi trocado e relança a exceção original. Todo destino passa
    antes por garantir_escopo: um só fora do escopo barra o lote inteiro, sem gravar nada."""
    destinos = [Path(d) for d in pares]
    for destino in destinos:
        garantir_escopo(destino)
    copias = {d: (d.read_bytes() if d.is_file() else None) for d in destinos}
    temporarios: list[Path] = []
    trocados: list[Path] = []
    atual = destinos[0] if destinos else None
    try:
        for destino, texto in zip(destinos, pares.values()):
            atual = destino
            destino.parent.mkdir(parents=True, exist_ok=True)
            tmp = _temporario(destino)
            temporarios.append(tmp)
            tmp.write_bytes(texto if isinstance(texto, bytes) else texto.encode("utf-8"))
        for destino, tmp in zip(destinos, temporarios):
            atual = destino
            com_retry(lambda origem=tmp, alvo=destino: os.replace(origem, alvo))
            trocados.append(destino)
    except BaseException as erro:
        for tmp in temporarios:
            tmp.unlink(missing_ok=True)
        for destino in trocados:
            if copias[destino] is None:
                destino.unlink(missing_ok=True)
            else:
                destino.write_bytes(copias[destino])
        if isinstance(erro, OSError) and not getattr(erro, "arquivo", None):
            erro.arquivo = str(atual)
        raise
    return destinos
