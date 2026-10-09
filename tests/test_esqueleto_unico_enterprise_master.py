# -*- coding: utf-8 -*-
"""Ticket 23 (ciclo-03 VSA, D15 / DoD 1 e DoD 4): uma cópia só do esqueleto de app.

O app de demonstração (src/ fora do núcleo vendorizado + alembic) existia byte a byte nas
duas ferramentas. Decisão do usuário (09/10): a maquete fica no aidd-master, dono da
construção (D1); o aidd-enterprise só blinda. Lista do que saiu: REMOCAO-ESQUELETO.md.

1. Nenhum arquivo de src/ ou alembic/ (nem alembic.ini / alembic_models.py) é idêntico
   entre as duas ferramentas fora de src/core, a cópia proposital de
   componentes/compartilhado/src-core vigiada pelo G_DRIFT_NUCLEO_COMPARTILHADO.
2. O enterprise não guarda o esqueleto de app.
3. allowlist_pacotes_repetidos.json só perdoa o `core` (núcleo vendorizado), exceção
   aceita pelo usuário; todo outro pacote tem nome único por fatia.
"""
from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PLATAFORMA = RAIZ / "modulos" / "03-plataforma-e-entrega"
ENTERPRISE = PLATAFORMA / "blindagem-enterprise" / "aidd-enterprise"
MASTER = PLATAFORMA / "fatiamento-master" / "aidd-master"
ALLOWLIST = RAIZ / "modulos" / "04-nucleo-compartilhado" / "contracts" / "allowlist_pacotes_repetidos.json"
ESQUELETO = ("src/__init__.py", "src/server.py", "src/modules", "src/shared", "src/static",
             "alembic", "alembic.ini", "alembic_models.py")


def _arquivos_do_esqueleto(ferramenta: Path) -> dict[str, bytes]:
    """caminho relativo -> conteúdo (fim de linha normalizado) de src/ fora de src/core e do alembic."""
    saida = {}
    candidatos = [p for base in ("src", "alembic") if (ferramenta / base).is_dir()
                  for p in (ferramenta / base).rglob("*")]
    candidatos += [ferramenta / nome for nome in ("alembic.ini", "alembic_models.py")]
    for p in candidatos:
        if not p.is_file() or "__pycache__" in p.parts:
            continue
        rel = p.relative_to(ferramenta).as_posix()
        if rel.startswith("src/core/"):
            continue
        saida[rel] = p.read_bytes().replace(b"\r\n", b"\n")
    return saida


def test_nenhum_arquivo_do_esqueleto_identico_entre_enterprise_e_master() -> None:
    ent, mas = _arquivos_do_esqueleto(ENTERPRISE), _arquivos_do_esqueleto(MASTER)
    identicos = sorted(rel for rel in set(ent) & set(mas) if ent[rel] == mas[rel])
    assert not identicos, f"{len(identicos)} arquivo(s) idêntico(s) fora de src/core: {identicos}"


def test_enterprise_nao_guarda_o_esqueleto_de_app() -> None:
    presentes = [rel for rel in ESQUELETO if (ENTERPRISE / rel).exists()]
    assert not presentes, f"esqueleto de app ainda no aidd-enterprise (dono: aidd-master): {presentes}"


def test_master_continua_com_a_maquete() -> None:
    faltando = [rel for rel in ESQUELETO if not (MASTER / rel).exists()]
    assert not faltando, f"maquete do aidd-master incompleta: {faltando}"


def test_allowlist_de_pacotes_so_perdoa_o_nucleo_vendorizado() -> None:
    entradas = json.loads(ALLOWLIST.read_text(encoding="utf-8"))["entradas"]
    assert [e["pacote"] for e in entradas] == ["core"], (
        f"só o núcleo vendorizado (core) pode repetir nome entre fatias: {[e['pacote'] for e in entradas]}"
    )
    assert set(entradas[0]["fatias"]) == {"blindagem-enterprise", "fatiamento-master"}
    assert "G_DRIFT_NUCLEO_COMPARTILHADO" in entradas[0]["motivo"]
