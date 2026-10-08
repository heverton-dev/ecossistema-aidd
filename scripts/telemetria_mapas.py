#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telemetria de execução dos mapas visuais (aidd-visual-maps, D12).

medir(estagio, tipo, catalogo) envolve o main() de cada estágio (catalogo, mapa,
nao-tecnico, livro), inclusive no --check, e acrescenta uma linha JSON em
secoes/medicoes/aidd-visual-maps.jsonl (pasta ignorada pelo git: não suja a árvore nem
o --check). AIDD_MEDICOES_DIR troca a pasta de destino (testes). Campos: estagio, tipo,
duracao_ms (time.perf_counter), arquivos_gravados, hash_catalogo (sha256 do catálogo no
fim do estágio), exit_code e llm_tokens = 0, explícito: o motor não usa LLM.
Falha ao gravar a medição vira [AVISO] em stderr e nunca muda o exit code do estágio.
"""
import hashlib
import json
import os
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = "aidd-visual-maps.jsonl"


@dataclass
class Medicao:
    arquivos_gravados: int = 0
    exit_code: int | None = None


def destino() -> Path:
    pasta = os.environ.get("AIDD_MEDICOES_DIR")
    return (Path(pasta) if pasta else RAIZ / "secoes" / "medicoes") / ARQUIVO


def _hash(caminho: Path) -> str | None:
    caminho = Path(caminho)
    return hashlib.sha256(caminho.read_bytes()).hexdigest() if caminho.is_file() else None


@contextmanager
def medir(estagio: str, tipo: str, catalogo: Path):
    """Mede o bloco; quem chama preenche medicao.exit_code e medicao.arquivos_gravados."""
    medicao = Medicao()
    inicio = time.perf_counter()
    try:
        yield medicao
    finally:
        linha = {"estagio": estagio, "tipo": tipo,
                 "duracao_ms": round((time.perf_counter() - inicio) * 1000, 1),
                 "arquivos_gravados": medicao.arquivos_gravados, "hash_catalogo": _hash(catalogo),
                 "exit_code": 1 if medicao.exit_code is None else medicao.exit_code, "llm_tokens": 0}
        try:
            arquivo = destino()
            arquivo.parent.mkdir(parents=True, exist_ok=True)
            with arquivo.open("a", encoding="utf-8", newline="\n") as saida:
                saida.write(json.dumps(linha, ensure_ascii=False) + "\n")
        except OSError as erro:
            print(f"[AVISO] telemetria não gravada: {erro}", file=sys.stderr)
