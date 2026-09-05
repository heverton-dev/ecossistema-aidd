# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — GESTOR ÚNICO DE COMPONENTES MULTI-HARNESS
=============================================================================
Lê gates/manifesto_harnesses.json (fonte única de mapeamento tipo de
componente -> destinos físicos por harness) e materializa/compara
`componentes/<escopo>/<tipo>/<nome>` contra todos os destinos declarados.

Propagação sempre por cópia física byte-idêntica (nunca symlink - Windows
sem privilégio elevado/Developer Mode precisa funcionar sem configuração
extra, e symlink introduziria lock-in de SO, violando a própria Regra de
Ouro #6 que este script existe para cumprir).

`sync`   escreve: cria a pasta de destino do harness se não existir, copia
         componentes ausentes ou divergentes a partir da fonte canônica.
`verify` só lê: nunca escreve nada, retorna exit 1 se algum destino
         declarado estiver ausente ou divergir em conteúdo da fonte.

Uso:
  python scripts/gestor_componentes.py sync --tipo <tipo|todos> [--ferramenta <nome>] [--dry-run]
  python scripts/gestor_componentes.py verify --tipo <tipo|todos> [--ferramenta <nome>]
"""

from __future__ import annotations

import argparse
import filecmp
import json
import os
import shutil
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFESTO_PATH = os.path.join(ROOT_DIR, "gates", "manifesto_harnesses.json")
COMPONENTES_DIR = os.path.join(ROOT_DIR, "componentes")

TODOS_TIPOS_MARCADOR = "todos"
IGNORAR_ENTRADAS = {".gitkeep"}


def carregar_manifesto():
    with open(MANIFESTO_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _escopo_dir_nome(nome_escopo):
    return "compartilhado" if nome_escopo == "compartilhado" else nome_escopo


def _escopos_do_tipo(manifesto, tipo, ferramenta=None):
    resultado = []
    for nome_escopo, cfg in manifesto["escopos"].items():
        if ferramenta and nome_escopo != ferramenta:
            continue
        if tipo in cfg.get("tipos_aplicaveis", []):
            resultado.append(nome_escopo)
    return resultado


def _listar_componentes_fonte(manifesto, tipo, nome_escopo):
    """Lista (nome, caminho_fonte_abs, eh_diretorio) para um tipo/escopo."""
    tipo_cfg = manifesto["tipos_componente"][tipo]
    dir_fonte = os.path.join(COMPONENTES_DIR, _escopo_dir_nome(nome_escopo), tipo_cfg["pasta_fonte"])
    if not os.path.isdir(dir_fonte):
        return []

    unidade = tipo_cfg["unidade"]
    resultado = []
    for entrada in sorted(os.listdir(dir_fonte)):
        if entrada in IGNORAR_ENTRADAS:
            continue
        caminho = os.path.join(dir_fonte, entrada)
        if unidade == "diretorio" and os.path.isdir(caminho):
            resultado.append((entrada, caminho, True))
        elif unidade == "arquivo" and os.path.isfile(caminho):
            resultado.append((entrada, caminho, False))
    return resultado


def _resolver_destinos(manifesto, tipo, nome_escopo, nome):
    """Resolve a lista (sem duplicados) de caminhos absolutos de destino."""
    tipo_cfg = manifesto["tipos_componente"][tipo]
    escopo_cfg = manifesto["escopos"][nome_escopo]
    root_escopo = ROOT_DIR if escopo_cfg["root"] == "." else os.path.join(ROOT_DIR, escopo_cfg["root"])

    destinos = []

    if tipo_cfg["distribuicao"] == "multi-harness":
        template = tipo_cfg["dest_harness_template"]
        for harness in tipo_cfg.get("harnesses_aplicaveis", []):
            prefixo = manifesto["harnesses_suportados"][harness]["prefixo_pasta"]
            rel = template.format(prefixo_pasta=prefixo, nome=nome)
            destinos.append(os.path.normpath(os.path.join(root_escopo, rel)))

        chave_extra = "extra_destinos_compartilhado" if nome_escopo == "compartilhado" else "extra_destinos_por_ferramenta"
        for template_extra in tipo_cfg.get(chave_extra, []):
            rel = template_extra.format(nome=nome)
            destinos.append(os.path.normpath(os.path.join(root_escopo, rel)))
    else:  # destino-unico-por-ferramenta
        rel = tipo_cfg["dest_unico_template"].format(nome=nome)
        destinos.append(os.path.normpath(os.path.join(root_escopo, rel)))

    vistos = set()
    unicos = []
    for d in destinos:
        if d not in vistos:
            vistos.add(d)
            unicos.append(d)
    return unicos


def _copiar_diretorio(origem, destino, dry_run):
    if dry_run:
        return
    os.makedirs(destino, exist_ok=True)
    for raiz, _dirs, arquivos in os.walk(origem):
        rel_raiz = os.path.relpath(raiz, origem)
        destino_raiz = destino if rel_raiz == "." else os.path.join(destino, rel_raiz)
        os.makedirs(destino_raiz, exist_ok=True)
        for arquivo in arquivos:
            shutil.copy2(os.path.join(raiz, arquivo), os.path.join(destino_raiz, arquivo))


def _copiar_arquivo(origem, destino, dry_run):
    if dry_run:
        return
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    shutil.copy2(origem, destino)


def _tipos_a_processar(manifesto, tipo):
    if tipo == TODOS_TIPOS_MARCADOR:
        return list(manifesto["tipos_componente"].keys())
    if tipo not in manifesto["tipos_componente"]:
        tipos_validos = ", ".join(manifesto["tipos_componente"].keys())
        raise ValueError(f"tipo '{tipo}' desconhecido. Tipos validos: {tipos_validos}, {TODOS_TIPOS_MARCADOR}")
    return [tipo]


def sync(tipo, ferramenta=None, dry_run=False):
    """Materializa componentes ausentes/divergentes a partir da fonte canônica. Nunca deleta."""
    manifesto = carregar_manifesto()
    relatorio = {"pastas_criadas": [], "criados": [], "atualizados": []}

    for tipo_atual in _tipos_a_processar(manifesto, tipo):
        for nome_escopo in _escopos_do_tipo(manifesto, tipo_atual, ferramenta):
            for nome, origem, eh_dir in _listar_componentes_fonte(manifesto, tipo_atual, nome_escopo):
                for destino in _resolver_destinos(manifesto, tipo_atual, nome_escopo, nome):
                    pasta_harness = os.path.dirname(destino)
                    pasta_harness_existia = os.path.isdir(pasta_harness)
                    ja_existia = os.path.exists(destino)

                    if eh_dir:
                        _copiar_diretorio(origem, destino, dry_run)
                    else:
                        _copiar_arquivo(origem, destino, dry_run)

                    if not pasta_harness_existia:
                        relatorio["pastas_criadas"].append(pasta_harness)
                    chave = "atualizados" if ja_existia else "criados"
                    relatorio[chave].append(f"[{tipo_atual}/{nome_escopo}] {nome} -> {os.path.relpath(destino, ROOT_DIR)}")

    return relatorio


def _comparar_arquivo(origem, destino):
    return os.path.isfile(destino) and filecmp.cmp(origem, destino, shallow=False)


def _comparar_diretorio(origem, destino):
    if not os.path.isdir(destino):
        return [f"pasta ausente: {os.path.relpath(destino, ROOT_DIR)}"]
    problemas = []
    for raiz, _dirs, arquivos in os.walk(origem):
        rel_raiz = os.path.relpath(raiz, origem)
        destino_raiz = destino if rel_raiz == "." else os.path.join(destino, rel_raiz)
        for arquivo in arquivos:
            origem_arquivo = os.path.join(raiz, arquivo)
            destino_arquivo = os.path.join(destino_raiz, arquivo)
            if not os.path.isfile(destino_arquivo):
                problemas.append(f"arquivo ausente: {os.path.relpath(destino_arquivo, ROOT_DIR)}")
            elif not filecmp.cmp(origem_arquivo, destino_arquivo, shallow=False):
                problemas.append(f"conteudo divergente: {os.path.relpath(destino_arquivo, ROOT_DIR)}")
    return problemas


def verify(tipo, ferramenta=None):
    """Só lê e compara. Retorna (total_componentes_verificados, lista_de_problemas)."""
    manifesto = carregar_manifesto()
    problemas = []
    total_componentes = 0

    for tipo_atual in _tipos_a_processar(manifesto, tipo):
        for nome_escopo in _escopos_do_tipo(manifesto, tipo_atual, ferramenta):
            for nome, origem, eh_dir in _listar_componentes_fonte(manifesto, tipo_atual, nome_escopo):
                total_componentes += 1
                for destino in _resolver_destinos(manifesto, tipo_atual, nome_escopo, nome):
                    if eh_dir:
                        for problema in _comparar_diretorio(origem, destino):
                            problemas.append(f"[{tipo_atual}/{nome_escopo}/{nome}] {problema}")
                    elif not _comparar_arquivo(origem, destino):
                        problemas.append(
                            f"[{tipo_atual}/{nome_escopo}/{nome}] arquivo ausente ou divergente: "
                            f"{os.path.relpath(destino, ROOT_DIR)}"
                        )

    return total_componentes, problemas


def _cmd_sync(args_ns):
    relatorio = sync(args_ns.tipo, ferramenta=args_ns.ferramenta, dry_run=args_ns.dry_run)
    modo = "[DRY-RUN] " if args_ns.dry_run else ""
    print(f"{modo}Pastas de destino (harness) criadas: {len(relatorio['pastas_criadas'])}")
    for p in relatorio["pastas_criadas"]:
        print(f"  [NOVA PASTA] {os.path.relpath(p, ROOT_DIR)}")
    print(f"{modo}Componentes novos: {len(relatorio['criados'])}")
    for item in relatorio["criados"]:
        print(f"  [CRIADO] {item}")
    print(f"{modo}Componentes atualizados: {len(relatorio['atualizados'])}")
    for item in relatorio["atualizados"]:
        print(f"  [ATUALIZADO] {item}")
    return 0


def _cmd_verify(args_ns):
    total, problemas = verify(args_ns.tipo, ferramenta=args_ns.ferramenta)
    print(f"Componentes verificados: {total}")
    if problemas:
        print(f"[FALHA] {len(problemas)} divergencia(s):")
        for p in problemas:
            print(f"  - {p}")
        return 1
    print("[SUCESSO] Todos os componentes sincronizados com a fonte canonica.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="gestor_componentes")
    sub = parser.add_subparsers(dest="acao", required=True)

    p_sync = sub.add_parser("sync")
    p_sync.add_argument("--tipo", required=True)
    p_sync.add_argument("--ferramenta", default=None)
    p_sync.add_argument("--dry-run", action="store_true")
    p_sync.set_defaults(func=_cmd_sync)

    p_verify = sub.add_parser("verify")
    p_verify.add_argument("--tipo", required=True)
    p_verify.add_argument("--ferramenta", default=None)
    p_verify.set_defaults(func=_cmd_verify)

    args_ns = parser.parse_args(argv)
    return args_ns.func(args_ns)


if __name__ == "__main__":
    sys.exit(main())
