#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_FRONTEIRA_FERRAMENTAS (Ciclo 01 / D1)
=============================================================================
Gate de fronteira das 8 ferramentas em modo aviso (Ticket 6).

Fontes de dados:
  - componentes/compartilhado/specs/MAPA-DONOS-FERRAMENTAS.json (mapa de donos:
    pode_conter / nunca_conter / zona_escrita_no_projeto por ferramenta).
  - docs/auditoria/mapa-pecas/catalogo-pecas.json (catálogo de peças; indexa o
    sha256 de cada peça canônica para detectar cópias dentro das ferramentas).

Varredura (modo estático, ESPEC-CONTRATOS-E-GATE.md):
  1. `git ls-files modulos` → cada arquivo sob a pasta da ferramenta (campo `pasta`) que bate no
     `nunca_conter` da própria ferramenta é violação;
  2. cujo sha256 bate com peça do catálogo de outro dono é cópia de peça
     (o almoxarifado é do aidd-forge; quem copiou deveria consumir, não guardar).

Cada violação imprime: arquivo, ferramenta atual e dono certo.

Níveis (AIDD_FRONTEIRA_MODO, precedência: --modo > variável > padrão):
  - aviso    (padrão): imprime o relatório e sai com exit 0;
  - bloqueio          : exit 1 se restar violação fora de
                        gates/allowlist_fronteira.json (lista datada que só
                        pode diminuir — reprovação garantida por
                        gates/test_g_fronteira_ferramentas.py).
  Valor desconhecido, mapa/catálogo/allowlist ilegível ou git fora de repo →
  exit 1 em qualquer modo (erro de infraestrutura).
=============================================================================
"""

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
MAPA_PADRAO = RAIZ / "componentes" / "compartilhado" / "specs" / "MAPA-DONOS-FERRAMENTAS.json"
CATALOGO_PADRAO = RAIZ / "docs" / "auditoria" / "mapa-pecas" / "catalogo-pecas.json"
ALLOWLIST_PADRAO = RAIZ / "gates" / "allowlist_fronteira.json"

DONO_ALMOXARIFADO = "aidd-forge"
RE_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ErroGate(Exception):
    """Erro de infraestrutura do gate (mapa/catálogo/allowlist/git/modo)."""


def bate(padrao: str, caminho: str) -> bool:
    """fnmatchcase determinístico; `**/x` também casa `x` na raiz."""
    if fnmatch.fnmatchcase(caminho, padrao):
        return True
    if padrao.startswith("**/") and fnmatch.fnmatchcase(caminho, padrao[3:]):
        return True
    return False


def carregar_json(caminho: Path, rotulo: str) -> dict:
    if not caminho.is_file():
        raise ErroGate(f"{rotulo} não encontrado: {caminho}")
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 — qualquer falha de decodificação é infra
        raise ErroGate(f"{rotulo} ilegível ({caminho}): {exc}") from exc
    if not isinstance(dados, dict):
        raise ErroGate(f"{rotulo} inválido (não é objeto JSON): {caminho}")
    return dados


def resolver_modo(cli: Optional[str]) -> str:
    bruto = cli if cli else os.environ.get("AIDD_FRONTEIRA_MODO", "")
    bruto = str(bruto).strip().lower() or "bloqueio"
    if bruto not in ("aviso", "bloqueio"):
        raise ErroGate(
            f"AIDD_FRONTEIRA_MODO inválido: {bruto!r} (use aviso|bloqueio)"
        )
    return bruto


def carregar_mapa(caminho: Path) -> Dict[str, dict]:
    mapa = carregar_json(caminho, "MAPA-DONOS-FERRAMENTAS")
    return {k: v for k, v in mapa.items() if isinstance(v, dict)}


def carregar_allowlist(caminho: Path) -> Dict[str, str]:
    dados = carregar_json(caminho, "Allowlist de fronteira (gates/allowlist_fronteira.json)")
    violacoes = dados.get("violacoes")
    if not isinstance(violacoes, list):
        raise ErroGate(f"Allowlist inválida (chave 'violacoes' deve ser lista): {caminho}")
    permitidas: Dict[str, str] = {}
    for entrada in violacoes:
        if not isinstance(entrada, dict):
            raise ErroGate(f"Allowlist com entrada que não é objeto: {entrada!r}")
        arquivo = entrada.get("arquivo")
        data = entrada.get("data", "")
        if not isinstance(arquivo, str) or not arquivo:
            raise ErroGate(f"Allowlist com entrada sem 'arquivo': {entrada!r}")
        if not isinstance(data, str) or not RE_DATA.match(data):
            raise ErroGate(
                f"Allowlist sem data válida (YYYY-MM-DD) em '{arquivo}': {data!r}"
            )
        permitidas[arquivo] = data
    return permitidas


def ferramenta_e_resto(mapa: Dict[str, dict], rel_repo: str) -> Tuple[Optional[str], str]:
    """(ferramenta dona pela pasta canônica do mapa, caminho relativo à pasta) ou (None, '')."""
    for nome, dados in mapa.items():
        pasta = dados.get("pasta") if isinstance(dados, dict) else None
        if pasta and rel_repo.startswith(pasta + "/"):
            return nome, rel_repo[len(pasta) + 1:]
    return None, ""


def listar_arquivos_ferramentas(raiz: Path) -> List[str]:
    proc = subprocess.run(
        ["git", "ls-files", "modulos"],
        cwd=str(raiz),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise ErroGate(f"git ls-files modulos falhou: {proc.stderr.strip() or proc.stdout.strip()}")
    return [
        linha.strip().replace("\\", "/")
        for linha in proc.stdout.splitlines()
        if linha.strip()
    ]


def _strings(valor) -> List[str]:
    if isinstance(valor, str):
        yield valor
    elif isinstance(valor, list):
        for item in valor:
            yield from _strings(item)
    elif isinstance(valor, dict):
        for item in valor.values():
            yield from _strings(item)


def indexar_catalogo(catalogo: dict, raiz: Path, mapa: Dict[str, dict]) -> Tuple[Dict[str, List[Tuple[str, str]]], Set[str]]:
    """sha256 → [(caminho_canônico, dono)] apenas de peças existentes e não vazias."""
    indice: Dict[str, List[Tuple[str, str]]] = {}
    conhecidos: Set[str] = set()
    for bruto in set(_strings(catalogo)):
        if not isinstance(bruto, str) or "\\" in bruto or bruto.startswith("/") or "/" not in bruto:
            continue
        caminho = raiz / bruto
        if not caminho.is_file():
            continue
        ferramenta, _ = ferramenta_e_resto(mapa, bruto)
        if bruto.startswith("modulos/"):
            if ferramenta is None:
                continue
            dono = ferramenta
        else:
            dono = DONO_ALMOXARIFADO
        conteudo = caminho.read_bytes()
        if not conteudo:
            continue
        digest = hashlib.sha256(conteudo).hexdigest()
        indice.setdefault(digest, []).append((bruto, dono))
        conhecidos.add(bruto)
    for lista in indice.values():
        lista.sort()
    return indice, conhecidos


def bate_em_algum_trecho(padrao: str, caminho: str) -> bool:
    """Casa o padrão contra o caminho inteiro e contra qualquer sufixo de segmentos."""
    if bate(padrao, caminho):
        return True
    partes = caminho.split("/")
    return any(bate(padrao, "/".join(partes[i:])) for i in range(1, len(partes)))


def dono_certo(mapa: Dict[str, dict], rel_repo: str, rel_ferramenta: str) -> str:
    """Dono canônico: ferramenta que não proíbe o padrão; zona de escrita tem
    prioridade sobre pode_conter, porque a zona declara a responsabilidade."""
    zona: List[str] = []
    pode: List[str] = []
    for nome in sorted(mapa):
        dados = mapa[nome]
        if any(bate(p, rel_repo) or bate(p, rel_ferramenta) for p in dados.get("nunca_conter", [])):
            continue
        if any(
            bate_em_algum_trecho(p, rel_ferramenta) or bate_em_algum_trecho(p, rel_repo)
            for p in dados.get("zona_escrita_no_projeto", [])
        ):
            zona.append(nome)
        elif any(bate_em_algum_trecho(p, rel_ferramenta) for p in dados.get("pode_conter", [])):
            pode.append(nome)
    candidatos = zona or pode
    if not candidatos:
        return "desconhecido"
    return "+".join(candidatos)


def coletar_violacoes(
    arquivos: List[str],
    mapa: Dict[str, dict],
    indice: Dict[str, List[Tuple[str, str]]],
    conhecidos: Set[str],
    raiz: Path,
) -> List[Dict[str, str]]:
    violacoes: List[Dict[str, str]] = []
    for rel_repo in arquivos:
        ferramenta, rel_ferramenta = ferramenta_e_resto(mapa, rel_repo)
        if ferramenta is None:
            continue
        dados = mapa[ferramenta]

        for padrao in dados.get("nunca_conter", []):
            if bate(padrao, rel_repo) or bate(padrao, rel_ferramenta):
                violacoes.append(
                    {
                        "arquivo": rel_repo,
                        "ferramenta_atual": ferramenta,
                        "dono_certo": dono_certo(mapa, rel_repo, rel_ferramenta),
                        "regra": f"nunca_conter({padrao})",
                    }
                )
                break

        if rel_repo in conhecidos:
            continue
        caminho = raiz / rel_repo
        if not caminho.is_file():
            continue
        conteudo = caminho.read_bytes()
        if not conteudo:
            continue
        digest = hashlib.sha256(conteudo).hexdigest()
        if digest in indice:
            pecas = indice[digest]
            donos = {dono for _, dono in pecas}
            if ferramenta in donos:
                # a própria ferramenta tem essa peça catalogada — não é cópia intrusa
                continue
            peca, dono = pecas[0]
            violacoes.append(
                {
                    "arquivo": rel_repo,
                    "ferramenta_atual": ferramenta,
                    "dono_certo": dono,
                    "regra": f"copia_peca_catalogo({peca})",
                }
            )
    violacoes.sort(key=lambda v: (v["arquivo"], v["regra"]))
    return violacoes


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Quality Gate G_FRONTEIRA_FERRAMENTAS (D1 — fronteiras em modo aviso)"
    )
    parser.add_argument(
        "--modo",
        choices=["aviso", "bloqueio"],
        default=None,
        help="Nível do gate (padrão: variável AIDD_FRONTEIRA_MODO ou bloqueio)",
    )
    args = parser.parse_args(argv)

    print("=" * 70)
    print(" [GATE] G_FRONTEIRA_FERRAMENTAS — Fronteiras das ferramentas (D1)")
    print("=" * 70)

    try:
        modo = resolver_modo(args.modo)
        mapa = carregar_mapa(MAPA_PADRAO)
        catalogo = carregar_json(CATALOGO_PADRAO, "Catálogo de peças (catalogo-pecas.json)")
        permitidas = carregar_allowlist(ALLOWLIST_PADRAO)
        arquivos = listar_arquivos_ferramentas(RAIZ)
        indice, conhecidos = indexar_catalogo(catalogo, RAIZ, mapa)
        violacoes = coletar_violacoes(arquivos, mapa, indice, conhecidos, RAIZ)
    except ErroGate as exc:
        print(f" [FALHA] {exc}")
        print("=" * 70)
        return 1

    perdoadas = [v for v in violacoes if v["arquivo"] in permitidas]
    restantes = [v for v in violacoes if v["arquivo"] not in permitidas]

    for v in perdoadas:
        print(
            f" [PERDOADA] arquivo={v['arquivo']} ferramenta_atual={v['ferramenta_atual']} "
            f"dono_certo={v['dono_certo']} regra={v['regra']} data={permitidas[v['arquivo']]}"
        )
    for v in restantes:
        print(
            f" [VIOLACAO] arquivo={v['arquivo']} ferramenta_atual={v['ferramenta_atual']} "
            f"dono_certo={v['dono_certo']} regra={v['regra']}"
        )

    print(
        f" [RESUMO] violacoes={len(violacoes)} perdoadas={len(perdoadas)} "
        f"restantes={len(restantes)} modo={modo}"
    )

    if modo == "aviso":
        print(" [SUCESSO] modo aviso — relatório emitido, nada foi bloqueado (exit 0)")
        print("=" * 70)
        return 0

    if restantes:
        print(
            f" [FALHA] modo bloqueio — {len(restantes)} violação(ões) fora de "
            f"allowlist_fronteira.json"
        )
        print("=" * 70)
        return 1

    print(" [SUCESSO] modo bloqueio — nenhuma violação perdoável restante (exit 0)")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
