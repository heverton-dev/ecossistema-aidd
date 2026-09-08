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

 `sync`         escreve: cria a pasta de destino do harness se não existir,
                copia componentes ausentes ou divergentes a partir da fonte
                canônica.
 `sync --force` restaura destinos órfãos e divergentes a partir da fonte.
 `verify`       só lê: nunca escreve nada. Compara via SHA-256. Retorna
                exit 1 se algum destino declarado estiver ausente, divergir
                em conteúdo, ou se existir arquivo órfão no destino.

 Detecção bidirecional de drift (Fase 4-6.4 P2):
   - MODIFICADO:  fonte e destino existem mas SHA-256 difere
   - DIVERGENTE:  fonte existe mas destino está ausente
   - ÓRFÃO:       destino existe mas não corresponde a nenhuma fonte

 Uso:
   python scripts/gestor_componentes.py sync --tipo <tipo|todos> [--ferramenta <nome>] [--dry-run]
   python scripts/gestor_componentes.py sync --force --tipo <tipo|todos> [--ferramenta <nome>]
   python scripts/gestor_componentes.py verify --tipo <tipo|todos> [--ferramenta <nome>]
"""

from __future__ import annotations

import argparse
import filecmp
import hashlib
import json
import os
import shutil
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFESTO_PATH = os.path.join(ROOT_DIR, "gates", "manifesto_harnesses.json")
COMPONENTES_DIR = os.path.join(ROOT_DIR, "componentes")

TODOS_TIPOS_MARCADOR = "todos"
IGNORAR_ENTRADAS = {".gitkeep"}
IGNORAR_DIRS = {"__pycache__", ".venv", "venv", ".git", "node_modules"}
NOMES_PASTA_COMPONENTE = {"commands", "skills", "mcps", "specs", "hooks", "configs", "scripts", "processes", "tests"}


# ---------------------------------------------------------------------------
# SHA-256 helpers
# ---------------------------------------------------------------------------

def _hash_file(caminho: str) -> str:
    """Computa SHA-256 hex de um arquivo. Abre em modo binário, leitura em blocos."""
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def _hash_diretorio(caminho: str) -> dict[str, str]:
    """Computa SHA-256 de cada arquivo dentro de um diretório (relativo ao root)."""
    hashes = {}
    for raiz, dirs, arquivos in os.walk(caminho):
        dirs[:] = [d for d in dirs if d not in IGNORAR_DIRS]
        for arquivo in sorted(arquivos):
            if arquivo.endswith((".pyc", ".pyo")):
                continue
            caminho_abs = os.path.join(raiz, arquivo)
            rel = os.path.relpath(caminho_abs, caminho).replace("\\", "/")
            hashes[rel] = _hash_file(caminho_abs)
    return hashes


# ---------------------------------------------------------------------------
# Estruturas de resultado do drift
# ---------------------------------------------------------------------------

@dataclass
class ItemDrift:
    """Um único item de drift detectado."""
    tipo_drift: str  # "modificado" | "divergente" | "orfao"
    componente: str  # tipo/nome do componente (vazio para órfãos)
    caminho: str     # caminho relativo ao ROOT_DIR
    hash_fonte: Optional[str] = None
    hash_destino: Optional[str] = None


@dataclass
class RelatorioDrift:
    """Relatório completo de drift bidirecional."""
    modificados: list[ItemDrift] = field(default_factory=list)
    divergentes: list[ItemDrift] = field(default_factory=list)
    orfaos: list[ItemDrift] = field(default_factory=list)
    boms: list[str] = field(default_factory=list)
    total_componentes: int = 0

    @property
    def tem_problemas(self) -> bool:
        return bool(self.modificados or self.divergentes or self.orfaos or self.boms)

    @property
    def total_erros(self) -> int:
        return len(self.modificados) + len(self.divergentes) + len(self.orfaos) + len(self.boms)


# ---------------------------------------------------------------------------
# Manifesto helpers (existentes)
# ---------------------------------------------------------------------------

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

    overrides = tipo_cfg.get("overrides_por_escopo", {}).get(nome_escopo, {})
    unidade = overrides.get("unidade", tipo_cfg["unidade"])
    resultado = []
    for entrada in sorted(os.listdir(dir_fonte)):
        if entrada in IGNORAR_ENTRADAS:
            continue
        caminho = os.path.join(dir_fonte, entrada)
        if unidade == "diretorio" and os.path.isdir(caminho):
            resultado.append((entrada, caminho, True))
        elif unidade == "arquivo":
            if os.path.isfile(caminho):
                resultado.append((entrada, caminho, False))
            elif os.path.isdir(caminho):
                sub_arquivos = [
                    f for f in sorted(os.listdir(caminho))
                    if f not in IGNORAR_ENTRADAS and os.path.isfile(os.path.join(caminho, f))
                ]
                if sub_arquivos:
                    candidato = None
                    for arq in sub_arquivos:
                        if os.path.splitext(arq)[0] == entrada:
                            candidato = arq
                            break
                    if not candidato:
                        candidato = sub_arquivos[0]
                    caminho_arq = os.path.join(caminho, candidato)
                    resultado.append((entrada, caminho_arq, False))
    return resultado


def _resolver_destinos(manifesto, tipo, nome_escopo, nome):
    """Resolve a lista (sem duplicados) de caminhos absolutos de destino."""
    tipo_cfg = manifesto["tipos_componente"][tipo]
    escopo_cfg = manifesto["escopos"][nome_escopo]
    root_escopo = ROOT_DIR if escopo_cfg["root"] == "." else os.path.join(ROOT_DIR, escopo_cfg["root"])

    destinos = []

    if tipo_cfg["distribuicao"] == "multi-harness":
        template_padrao = tipo_cfg["dest_harness_template"]
        overrides_template = tipo_cfg.get("dest_harness_template_overrides", {})
        for harness in tipo_cfg.get("harnesses_aplicaveis", []):
            prefixo = manifesto["harnesses_suportados"][harness]["prefixo_pasta"]
            template = overrides_template.get(harness, template_padrao)
            rel = template.format(prefixo_pasta=prefixo, nome=nome)
            destinos.append(os.path.normpath(os.path.join(root_escopo, rel)))

        chave_extra = "extra_destinos_compartilhado" if nome_escopo == "compartilhado" else "extra_destinos_por_ferramenta"
        for template_extra in tipo_cfg.get(chave_extra, []):
            rel = template_extra.format(nome=nome)
            destinos.append(os.path.normpath(os.path.join(root_escopo, rel)))
    else:  # destino-unico-por-ferramenta
        overrides = tipo_cfg.get("overrides_por_escopo", {}).get(nome_escopo, {})
        template_unico = overrides.get("dest_unico_template", tipo_cfg["dest_unico_template"])
        nome_formatado = nome
        ext_template = os.path.splitext(template_unico)[1]
        if ext_template and nome.endswith(ext_template):
            nome_formatado = nome[:-len(ext_template)]
        rel = template_unico.format(nome=nome_formatado)
        destinos.append(os.path.normpath(os.path.join(root_escopo, rel)))

    vistos = set()
    unicos = []
    for d in destinos:
        if d not in vistos:
            vistos.add(d)
            unicos.append(d)
    return unicos


# ---------------------------------------------------------------------------
# NOVO: manifestos extra por harness (ex: gemini-extension.json)
# Alguns harnesses (Gemini CLI) exigem um arquivo de manifesto ao lado do
# conteudo copiado, sem fonte 1:1 em componentes/ — o conteudo e derivado
# deterministicamente do nome do componente via template no proprio
# manifesto_harnesses.json (chave 'manifestos_extra_por_harness').
# ---------------------------------------------------------------------------

def _resolver_manifestos_extra(manifesto, tipo, nome_escopo, nome):
    """Resolve (caminho_abs, conteudo_esperado_dict) para cada manifesto extra
    aplicavel a este componente. Lista vazia se o tipo nao declarar nenhum."""
    tipo_cfg = manifesto["tipos_componente"][tipo]
    specs = tipo_cfg.get("manifestos_extra_por_harness", {})
    if not specs:
        return []
    escopo_cfg = manifesto["escopos"][nome_escopo]
    root_escopo = ROOT_DIR if escopo_cfg["root"] == "." else os.path.join(ROOT_DIR, escopo_cfg["root"])

    resolvidos = []
    for harness, spec in specs.items():
        if harness not in tipo_cfg.get("harnesses_aplicaveis", []):
            continue
        prefixo = manifesto["harnesses_suportados"][harness]["prefixo_pasta"]
        rel = spec["caminho_template"].format(prefixo_pasta=prefixo, nome=nome)
        caminho_abs = os.path.normpath(os.path.join(root_escopo, rel))
        conteudo = {
            chave: (valor.format(nome=nome) if isinstance(valor, str) else valor)
            for chave, valor in spec["conteudo_template"].items()
        }
        resolvidos.append((caminho_abs, conteudo))
    return resolvidos


def _gerar_manifestos_extra(manifesto, tipo, nome_escopo, nome, dry_run):
    """Materializa (cria/sobrescreve) os manifestos extra deste componente."""
    gerados = []
    for caminho_abs, conteudo in _resolver_manifestos_extra(manifesto, tipo, nome_escopo, nome):
        if not dry_run:
            os.makedirs(os.path.dirname(caminho_abs), exist_ok=True)
            with open(caminho_abs, "w", encoding="utf-8") as f:
                json.dump(conteudo, f, indent=2, ensure_ascii=False)
                f.write("\n")
        gerados.append(caminho_abs)
    return gerados


def _verificar_manifestos_extra(manifesto, tipo=None, ferramenta=None):
    """Compara manifestos extra em disco contra o conteudo esperado.
    Retorna lista de ItemDrift (ausente ou com conteudo divergente)."""
    problemas = []
    for tipo_atual in _tipos_a_processar(manifesto, tipo):
        tipo_cfg = manifesto["tipos_componente"][tipo_atual]
        if not tipo_cfg.get("manifestos_extra_por_harness"):
            continue
        for nome_escopo in _escopos_do_tipo(manifesto, tipo_atual, ferramenta):
            for nome, _origem, _eh_dir in _listar_componentes_fonte(manifesto, tipo_atual, nome_escopo):
                for caminho_abs, esperado in _resolver_manifestos_extra(manifesto, tipo_atual, nome_escopo, nome):
                    tag = f"{tipo_atual}/{nome_escopo}/{nome}"
                    caminho_rel = os.path.relpath(caminho_abs, ROOT_DIR).replace("\\", "/")
                    if not os.path.isfile(caminho_abs):
                        problemas.append(ItemDrift(
                            tipo_drift="modificado",
                            componente=tag,
                            caminho=caminho_rel,
                            hash_fonte="(gerado a partir do nome — ausente)",
                            hash_destino=None,
                        ))
                        continue
                    try:
                        with open(caminho_abs, "r", encoding="utf-8") as f:
                            atual = json.load(f)
                    except Exception:
                        atual = None
                    if atual != esperado:
                        problemas.append(ItemDrift(
                            tipo_drift="modificado",
                            componente=tag,
                            caminho=caminho_rel,
                            hash_fonte="(gerado a partir do nome)",
                            hash_destino="(conteudo em disco diverge do esperado)",
                        ))
    return problemas


def _tipos_a_processar(manifesto, tipo):
    if tipo is None or tipo == TODOS_TIPOS_MARCADOR:
        return list(manifesto["tipos_componente"].keys())
    if tipo not in manifesto["tipos_componente"]:
        tipos_validos = ", ".join(manifesto["tipos_componente"].keys())
        raise ValueError(f"tipo '{tipo}' desconhecido. Tipos validos: {tipos_validos}, {TODOS_TIPOS_MARCADOR}")
    return [tipo]


# ---------------------------------------------------------------------------
# Copia (existentes)
# ---------------------------------------------------------------------------

def _copiar_diretorio(origem, destino, dry_run):
    if dry_run:
        return
    os.makedirs(destino, exist_ok=True)
    for raiz, dirs, arquivos in os.walk(origem):
        dirs[:] = [d for d in dirs if d not in IGNORAR_DIRS]
        arquivos = [a for a in arquivos if not a.endswith(".pyc")]
        rel_raiz = os.path.relpath(raiz, origem)
        destino_raiz = destino if rel_raiz == "." else os.path.join(destino, rel_raiz)
        os.makedirs(destino_raiz, exist_ok=True)
        for arquivo in arquivos:
            if arquivo.endswith((".pyc", ".pyo")):
                continue
            shutil.copy2(os.path.join(raiz, arquivo), os.path.join(destino_raiz, arquivo))


def _copiar_arquivo(origem, destino, dry_run):
    if dry_run:
        return
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    shutil.copy2(origem, destino)


# ---------------------------------------------------------------------------
# Comparação existente (mantida para compatibilidade retroativa)
# ---------------------------------------------------------------------------

def _comparar_arquivo(origem, destino):
    return os.path.isfile(destino) and filecmp.cmp(origem, destino, shallow=False)


def _comparar_diretorio(origem, destino):
    if not os.path.isdir(destino):
        return [f"pasta ausente: {os.path.relpath(destino, ROOT_DIR)}"]
    problemas = []
    for raiz, dirs, arquivos in os.walk(origem):
        dirs[:] = [d for d in dirs if d not in IGNORAR_DIRS]
        arquivos = [a for a in arquivos if not a.endswith(".pyc")]
        rel_raiz = os.path.relpath(raiz, origem)
        destino_raiz = destino if rel_raiz == "." else os.path.join(destino, rel_raiz)
        for arquivo in arquivos:
            if arquivo.endswith((".pyc", ".pyo")):
                continue
            origem_arquivo = os.path.join(raiz, arquivo)
            destino_arquivo = os.path.join(destino_raiz, arquivo)
            if not os.path.isfile(destino_arquivo):
                problemas.append(f"arquivo ausente: {os.path.relpath(destino_arquivo, ROOT_DIR)}")
            elif not filecmp.cmp(origem_arquivo, destino_arquivo, shallow=False):
                problemas.append(f"conteudo divergente: {os.path.relpath(destino_arquivo, ROOT_DIR)}")
    return problemas


# ---------------------------------------------------------------------------
# BOM check (existente)
# ---------------------------------------------------------------------------

def _checar_bom_em_componentes():
    boms = []
    dir_componentes = os.path.join(ROOT_DIR, "componentes")
    if not os.path.isdir(dir_componentes):
        return boms
    for raiz, dirs, arquivos in os.walk(dir_componentes):
        dirs[:] = [d for d in dirs if d not in IGNORAR_DIRS]
        for arquivo in arquivos:
            caminho = os.path.join(raiz, arquivo)
            try:
                with open(caminho, "rb") as f:
                    if f.read(3) == b"\xef\xbb\xbf":
                        boms.append(os.path.relpath(caminho, ROOT_DIR))
            except Exception:
                pass
    return boms


# ---------------------------------------------------------------------------
# NOVO: Index de fontes para detecção bidirecional
# ---------------------------------------------------------------------------

ALLOWLIST_ORFAOS_PATH = os.path.join(ROOT_DIR, "gates", "allowlist_orfaos.json")


def _carregar_allowlist_orfaos() -> set[str]:
    """Arquivos presentes em pastas de destino que são legitimamente não-gerados.
    Retorna nomes relativos normalizados (posix). Nunca levanta exceção."""
    if not os.path.isfile(ALLOWLIST_ORFAOS_PATH):
        return set()
    try:
        with open(ALLOWLIST_ORFAOS_PATH, "r", encoding="utf-8") as f:
            dados = json.load(f)
        return {a.replace("\\", "/").lower() for a in dados.get("arquivos", []) if isinstance(a, str)}
    except Exception:
        return set()


def _indexar_fontes(manifesto, tipo=None, ferramenta=None):
    """Indexa todas as fontes declaradas no manifesto.
    Retorna dict: caminho_destino_abs -> (tipo, nome_escopo, nome, caminho_fonte_abs, eh_dir).
    """
    indice = {}
    for tipo_atual in _tipos_a_processar(manifesto, tipo):
        for nome_escopo in _escopos_do_tipo(manifesto, tipo_atual, ferramenta):
            for nome, origem, eh_dir in _listar_componentes_fonte(manifesto, tipo_atual, nome_escopo):
                for destino in _resolver_destinos(manifesto, tipo_atual, nome_escopo, nome):
                    indice[os.path.normpath(destino)] = (tipo_atual, nome_escopo, nome, origem, eh_dir)
    return indice


def _arquivos_em_destino(caminho_abs: str) -> dict[str, str]:
    """Lista todos os arquivos recursivamente em um destino, retornando {rel_path: abs_path}."""
    arquivos = {}
    if os.path.isfile(caminho_abs):
        arquivos[os.path.basename(caminho_abs)] = caminho_abs
    elif os.path.isdir(caminho_abs):
        for raiz, dirs, files in os.walk(caminho_abs):
            dirs[:] = [d for d in dirs if d not in IGNORAR_DIRS]
            for f in files:
                if f.endswith((".pyc", ".pyo")):
                    continue
                abs_path = os.path.join(raiz, f)
                rel = os.path.relpath(abs_path, caminho_abs).replace("\\", "/")
                arquivos[rel] = abs_path
    return arquivos


# ---------------------------------------------------------------------------
# NOVO: Detecção de drift bidirecional com SHA-256
# ---------------------------------------------------------------------------

def detectar_drift(tipo=None, ferramenta=None):
    """Detecta drift bidirecional entre fontes em componentes/ e destinos.
    Retorna um RelatorioDrift com modificados, divergentes e órfãos.
    """
    manifesto = carregar_manifesto()
    relatorio = RelatorioDrift()
    relatorio.boms = _checar_bom_em_componentes()

    indice_fontes = _indexar_fontes(manifesto, tipo, ferramenta)
    relatorio.total_componentes = len(set(
        (v[0], v[1], v[2]) for v in indice_fontes.values()
    ))

    destinos_esperados = set(indice_fontes.keys())
    destinos_encontrados = set()
    allowlist = _carregar_allowlist_orfaos()

    for destino_abs, (tipo_c, nome_escopo, nome, fonte_abs, eh_dir) in indice_fontes.items():
        destino_rel = os.path.relpath(destino_abs, ROOT_DIR).replace("\\", "/")
        tag = f"{tipo_c}/{nome_escopo}/{nome}"

        if not os.path.exists(destino_abs):
            relatorio.divergentes.append(ItemDrift(
                tipo_drift="divergente",
                componente=tag,
                caminho=destino_rel,
            ))
            continue

        if eh_dir:
            hashes_fonte = _hash_diretorio(fonte_abs)
            hashes_destino = _hash_diretorio(destino_abs)

            for rel_file, hash_f in hashes_fonte.items():
                hash_d = hashes_destino.get(rel_file)
                if hash_d is None:
                    relatorio.modificados.append(ItemDrift(
                        tipo_drift="modificado",
                        componente=tag,
                        caminho=f"{destino_rel}/{rel_file}",
                        hash_fonte=hash_f,
                        hash_destino=None,
                    ))
                elif hash_f != hash_d:
                    relatorio.modificados.append(ItemDrift(
                        tipo_drift="modificado",
                        componente=tag,
                        caminho=f"{destino_rel}/{rel_file}",
                        hash_fonte=hash_f,
                        hash_destino=hash_d,
                    ))

            arquivos_fonte = set(hashes_fonte.keys())
            arquivos_destino = set(hashes_destino.keys())
            for extra in sorted(arquivos_destino - arquivos_fonte):
                relatorio.orfaos.append(ItemDrift(
                    tipo_drift="orfao",
                    componente=tag,
                    caminho=f"{destino_rel}/{extra}",
                ))

            destinos_encontrados.add(destino_abs)
        else:
            hash_f = _hash_file(fonte_abs)
            hash_d = _hash_file(destino_abs)
            if hash_f != hash_d:
                relatorio.modificados.append(ItemDrift(
                    tipo_drift="modificado",
                    componente=tag,
                    caminho=destino_rel,
                    hash_fonte=hash_f,
                    hash_destino=hash_d,
                ))
            destinos_encontrados.add(destino_abs)

    # Detecção de órfãos em nível de pasta (componentes de unidade=arquivo):
    # arquivos que vivem na mesma pasta de um destino esperado, mas não
    # correspondem a nenhuma fonte (e não estão na allowlist).
    if ferramenta is None:
        pastas_nomeadas = {}
        for destino_abs, (tipo_c, nome_escopo, nome, fonte_abs, eh_dir) in indice_fontes.items():
            if eh_dir:
                continue
            pasta = os.path.dirname(destino_abs)
            pastas_nomeadas.setdefault(pasta, set()).add(os.path.normpath(destino_abs))

        for pasta, destinos_esperados_local in pastas_nomeadas.items():
            if not os.path.isdir(pasta):
                continue
            base_pasta = os.path.basename(os.path.normpath(pasta))
            # Só vasculha pastas de namespace de componentes (skills, commands etc.)
            if base_pasta not in NOMES_PASTA_COMPONENTE:
                continue
            for entrada in sorted(os.listdir(pasta)):
                if entrada in IGNORAR_ENTRADAS:
                    continue
                caminho_entrada = os.path.join(pasta, entrada)
                if not os.path.isfile(caminho_entrada):
                    continue
                norm = os.path.normpath(caminho_entrada)
                if norm in destinos_esperados_local:
                    continue
                rel = os.path.relpath(norm, ROOT_DIR).replace("\\", "/")
                if rel.lower() in allowlist:
                    continue
                # Arquivos já mapeados como destino de componente não são órfãos
                if norm in destinos_esperados:
                    continue
                relatorio.orfaos.append(ItemDrift(
                    tipo_drift="orfao",
                    componente="",
                    caminho=rel,
                ))

    relatorio.modificados.extend(_verificar_manifestos_extra(manifesto, tipo, ferramenta))

    return relatorio


# ---------------------------------------------------------------------------
# NOVO: Força-sync (restaura destinos divergentes e órfãos)
# ---------------------------------------------------------------------------

def force_sync(tipo=None, ferramenta=None):
    """Restaura destinos divergentes/modificados a partir da fonte e remove órfãos.
    Retorna dict com resumo do que foi restaurado.
    """
    manifesto = carregar_manifesto()
    relatorio_drift = detectar_drift(tipo, ferramenta)

    indice = _indexar_fontes(manifesto, tipo, ferramenta)
    restaurados = []
    orfaos_removidos = []
    ja_restaurados = set()

    def _restaurar(destino_abs, tipo_c, nome_escopo, nome, fonte_abs, eh_dir):
        destino_norm = os.path.normpath(destino_abs)
        if destino_norm in ja_restaurados:
            return
        if eh_dir:
            _copiar_diretorio(fonte_abs, destino_abs, dry_run=False)
        else:
            _copiar_arquivo(fonte_abs, destino_abs, dry_run=False)
        ja_restaurados.add(destino_norm)
        restaurados.append(
            f"[{tipo_c}/{nome_escopo}/{nome}] {os.path.relpath(destino_abs, ROOT_DIR)}"
        )

    for destino_abs in sorted(indice):
        tipo_c, nome_escopo, nome, fonte_abs, eh_dir = indice[destino_abs]
        if os.path.exists(destino_abs):
            continue
        _restaurar(destino_abs, tipo_c, nome_escopo, nome, fonte_abs, eh_dir)

    for item in relatorio_drift.modificados:
        tag_parts = item.componente.split("/")
        if len(tag_parts) < 3:
            continue
        tipo_c, nome_escopo, nome = tag_parts[0], tag_parts[1], tag_parts[2]
        for destino_abs, (t_c, e_c, n, fonte_abs, eh_dir) in indice.items():
            if (t_c, e_c, n) == (tipo_c, nome_escopo, nome) and os.path.exists(destino_abs):
                _restaurar(destino_abs, t_c, e_c, n, fonte_abs, eh_dir)

    for item in relatorio_drift.orfaos:
        caminho_abs = os.path.normpath(os.path.join(ROOT_DIR, item.caminho))
        if os.path.isfile(caminho_abs):
            os.remove(caminho_abs)
            orfaos_removidos.append(item.caminho)

    # Regera manifestos extra (ex: gemini-extension.json) — idempotente, sempre
    # recomputado a partir do nome do componente, nunca deletado como orfao.
    manifestos_regerados = []
    for tipo_atual in _tipos_a_processar(manifesto, tipo):
        for nome_escopo in _escopos_do_tipo(manifesto, tipo_atual, ferramenta):
            for nome, _origem, _eh_dir in _listar_componentes_fonte(manifesto, tipo_atual, nome_escopo):
                manifestos_regerados.extend(
                    _gerar_manifestos_extra(manifesto, tipo_atual, nome_escopo, nome, dry_run=False)
                )

    return {
        "manifestos_extra_regerados": manifestos_regerados,
        "restaurados": restaurados,
        "orfaos_removidos": orfaos_removidos,
        "relatorio_drift": relatorio_drift,
    }


# ---------------------------------------------------------------------------
# verify (API pública — mantém compatibilidade retroativa + enriquecida)
# ---------------------------------------------------------------------------

def verify(tipo, ferramenta=None):
    """Só lê e compara via SHA-256. Retorna (total_componentes_verificados, lista_de_problemas).
    Compatível retroativamente com chamadores existentes (G_HARNESS_COMPAT.py).
    """
    relatorio = detectar_drift(tipo, ferramenta)
    problemas = []

    for bom in relatorio.boms:
        problemas.append(f"arquivo com UTF-8 BOM proibido (EF BB BF): {bom}")

    for item in relatorio.divergentes:
        problemas.append(f"[{item.componente}] destino ausente: {item.caminho}")

    for item in relatorio.modificados:
        hash_info = ""
        if item.hash_fonte and item.hash_destino:
            hash_info = f" (fonte={item.hash_fonte[:12]}... destino={item.hash_destino[:12]}...)"
        problemas.append(f"[{item.componente}] conteudo divergente (SHA-256): {item.caminho}{hash_info}")

    for item in relatorio.orfaos:
        problemas.append(f"[ORFAO] arquivo sem fonte em componentes/: {item.caminho}")

    return relatorio.total_componentes, problemas


# ---------------------------------------------------------------------------
# verify_detallado (nova API com relatório estruturado)
# ---------------------------------------------------------------------------

def verify_detallado(tipo=None, ferramenta=None):
    """Versão enriquecida de verify que retorna o RelatorioDrift completo."""
    return detectar_drift(tipo, ferramenta)


# ---------------------------------------------------------------------------
# sync (existente — mantida)
# ---------------------------------------------------------------------------

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

                _gerar_manifestos_extra(manifesto, tipo_atual, nome_escopo, nome, dry_run)

    return relatorio


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

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
    relatorio = verify_detallado(args_ns.tipo, ferramenta=args_ns.ferramenta)

    print(f"Componentes verificados: {relatorio.total_componentes}")

    if relatorio.boms:
        print(f"\n[BOM] {len(relatorio.boms)} arquivo(s) com UTF-8 BOM proibido:")
        for b in relatorio.boms:
            print(f"  - {b}")

    if relatorio.modificados:
        print(f"\n[MODIFICADO] {len(relatorio.modificados)} arquivo(s) com SHA-256 divergente:")
        for item in relatorio.modificados:
            hash_info = ""
            if item.hash_fonte and item.hash_destino:
                hash_info = f"  fonte={item.hash_fonte[:16]}... destino={item.hash_destino[:16]}..."
            print(f"  - [{item.componente}] {item.caminho}{hash_info}")

    if relatorio.divergentes:
        print(f"\n[DIVERGENTE] {len(relatorio.divergentes)} destino(s) ausente(s) para fonte existente:")
        for item in relatorio.divergentes:
            print(f"  - [{item.componente}] {item.caminho}")

    if relatorio.orfaos:
        print(f"\n[ORFAO] {len(relatorio.orfaos)} arquivo(s) sem fonte em componentes/:")
        for item in relatorio.orfaos:
            print(f"  - {item.caminho}")

    if not relatorio.tem_problemas:
        print("\n[SUCESSO] Todos os componentes sincronizados com a fonte canonica (SHA-256 verificado).")
        return 0

    total = relatorio.total_erros
    print(f"\n[FALHA] {total} problema(s) detectado(s) na verificacao bidirecional.")
    print("  Use 'components sync --force --tipo <tipo>' para restaurar.")
    return 1


def _cmd_force_sync(args_ns):
    resultado = force_sync(args_ns.tipo, ferramenta=args_ns.ferramenta)
    relatorio = resultado["relatorio_drift"]

    print("Force-Sync concluido.")
    print(f"  Restaurados (re-copiados da fonte): {len(resultado['restaurados'])}")
    for r in resultado["restaurados"]:
        print(f"    [RESTAURADO] {r}")
    print(f"  Orfaos removidos: {len(resultado['orfaos_removidos'])}")
    for o in resultado["orfaos_removidos"]:
        print(f"    [REMOVIDO] {o}")

    print(f"\n  Resumo do drift detectado:")
    print(f"    Modificados (SHA-256 divergente): {len(relatorio.modificados)}")
    print(f"    Divergentes (destino ausente):    {len(relatorio.divergentes)}")
    print(f"    Orfaos (sem fonte):               {len(relatorio.orfaos)}")
    print(f"    BOMs proibidos:                   {len(relatorio.boms)}")

    if not resultado["restaurados"] and not resultado["orfaos_removidos"]:
        print("\n  Nenhum arquivo precisou de restauracao.")
    return 0


# ---------------------------------------------------------------------------
# main (CLI)
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(prog="gestor_componentes")
    sub = parser.add_subparsers(dest="acao", required=True)

    p_sync = sub.add_parser("sync")
    p_sync.add_argument("--tipo", required=True)
    p_sync.add_argument("--ferramenta", default=None)
    p_sync.add_argument("--dry-run", action="store_true")
    p_sync.add_argument("--force", action="store_true",
                        help="Restaura destinos divergentes e remove orfaos")
    p_sync.set_defaults(func=_cmd_sync)

    p_verify = sub.add_parser("verify")
    p_verify.add_argument("--tipo", required=True)
    p_verify.add_argument("--ferramenta", default=None)
    p_verify.set_defaults(func=_cmd_verify)

    args_ns = parser.parse_args(argv)

    if args_ns.acao == "sync" and getattr(args_ns, "force", False):
        return _cmd_force_sync(args_ns)

    return args_ns.func(args_ns)


if __name__ == "__main__":
    sys.exit(main())
