# -*- coding: utf-8 -*-
"""
Sincronizador determinístico do núcleo compartilhado.

Fonte única: componentes/compartilhado/src-core/
Destinos:     tools/aidd-master/src/core/ e tools/aidd-enterprise/src/core/

Uso:
    python componentes/compartilhado/src-core/sync.py            # sincroniza (copia byte-a-byte o que mudou)
    python componentes/compartilhado/src-core/sync.py verify     # verifica sem copiar (exit 1 se divergir)
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PASTA_FONTE = Path(__file__).resolve().parent
MANIFEST = PASTA_FONTE / "MANIFEST.json"


def _ler_manifesto() -> list[str]:
    with open(MANIFEST, "r", encoding="utf-8") as f:
        dados = json.load(f)
    arquivos = dados["arquivos"]
    duplicados = [a for a in set(arquivos) if arquivos.count(a) > 1]
    if duplicados:
        raise SystemExit(f"MANIFEST.json com nomes duplicados: {duplicados}")
    faltantes = [a for a in arquivos if not (PASTA_FONTE / a).is_file()]
    if faltantes:
        raise SystemExit(f"Arquivos do manifesto ausentes na fonte única: {faltantes}")
    return arquivos


def _destinos() -> list[Path]:
    with open(MANIFEST, "r", encoding="utf-8") as f:
        dados = json.load(f)
    raiz = PASTA_FONTE.parents[2]
    return [Path(raiz) / d for d in dados["destinos"]]


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def _sincronizar(arquivos: list[str], destinos: list[Path]) -> int:
    divergencias = 0
    for arquivo in arquivos:
        fonte = PASTA_FONTE / arquivo
        for destino in destinos:
            alvo = destino / arquivo
            alvo.parent.mkdir(parents=True, exist_ok=True)
            if not alvo.is_file() or _sha256(alvo) != _sha256(fonte):
                alvo.write_bytes(fonte.read_bytes())
                print(f"sync: {alvo.relative_to(Path.cwd())}")
                divergencias += 1
    return 1 if divergencias else 0


def _verificar(arquivos: list[str], destinos: list[Path]) -> int:
    falhas = 0
    for arquivo in arquivos:
        fonte = PASTA_FONTE / arquivo
        for destino in destinos:
            alvo = destino / arquivo
            if not alvo.is_file():
                print(f"verify: AUSENTE em {destino.relative_to(Path.cwd())}: {arquivo}")
                falhas += 1
            elif _sha256(alvo) != _sha256(fonte):
                print(f"verify: DIVERGENTE em {destino.relative_to(Path.cwd())}: {arquivo}")
                falhas += 1
    if falhas:
        print(f"verify: {falhas} divergência(s) — rode sync.py para corrigir.")
    else:
        print("verify: núcleo compartilhado byte-idêntico entre fonte única e todos os destinos.")
    return 1 if falhas else 0


def main() -> int:
    modo = sys.argv[1] if len(sys.argv) > 1 else "sync"
    if modo not in ("sync", "verify"):
        print(__doc__)
        return 2
    arquivos = _ler_manifesto()
    destinos = _destinos()
    return _verificar(arquivos, destinos) if modo == "verify" else _sincronizar(arquivos, destinos)


if __name__ == "__main__":
    raise SystemExit(main())