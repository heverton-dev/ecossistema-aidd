# -*- coding: utf-8 -*-
"""
gates/_escopo_commit.py — Escopo de ferramentas do G_TESTES_REAIS por commit.

Em modo 'rapido' (padrão) o gate G_TESTES_REAIS roda pytest somente nas
ferramentas atingidas pelos arquivos staged no git; em modo 'completo'
(AIDD_GATES_MODO) roda todas. O escopo nunca encolhe para vazio: sem
arquivo staged, com ferramenta desconhecida em tools/, ou com o próprio
gate/orçamento de skipped staged (comportamento do gate em disputa),
retorna todas as ferramentas. Ferramenta forçada via
AIDD_TESTES_REAIS_FERRAMENTAS continua sendo decisão do próprio gate.

Uso:
    import _escopo_commit
    alvos = _escopo_commit.ferramentas_afetadas(
        _escopo_commit.arquivos_staged(), FERRAMENTAS)
"""

import os
import subprocess

MODO_RAPIDO = "rapido"
MODO_COMPLETO = "completo"

_GATES_DIR = os.path.dirname(os.path.abspath(__file__))
_RAIZ_PADRAO = os.path.dirname(_GATES_DIR)

# Arquivos cujo staged invalida qualquer escopo parcial: mudam as próprias
# regras com que o gate decide o que é teste autorizado.
_ARQUIVOS_GLOBAIS_DO_GATE = (
    "gates/G_TESTES_REAIS.py",
    "gates/allowlist_skipped_testes.json",
)


def modo():
    """Retorna 'completo' só quando AIDD_GATES_MODO diz completo; senão 'rapido'."""
    valor = os.environ.get("AIDD_GATES_MODO", "").strip().lower()
    return MODO_COMPLETO if valor == MODO_COMPLETO else MODO_RAPIDO


def arquivos_staged(raiz=None):
    """Lista os caminhos (relativos, separados por '/') staged no índice git.

    `raiz` é a árvore de trabalho; padrão é a raiz do repositório deste módulo.
    Sem repositório, sem git ou sem staged retorna lista vazia — quem consome
    decide o que fazer com escopo indeterminável (ver ferramentas_afetadas).
    """
    if raiz is None:
        raiz = _RAIZ_PADRAO
    try:
        proc = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "-z"],
            cwd=str(raiz),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []
    return [caminho for caminho in proc.stdout.split("\0") if caminho]


def ferramentas_afetadas(arquivos, todas):
    """Ferramentas a executar para os `arquivos` staged, preservando a ordem de `todas`.

    Retorna `todas` quando: o modo é 'completo'; algum arquivo sob tools/ não
    corresponde a nenhuma ferramenta de `todas`; gates/G_TESTES_REAIS.py ou
    gates/allowlist_skipped_testes.json está staged; ou nenhum arquivo staged
    mapeia ferramenta (escopo indeterminável — nunca aprovar sem rodar nada).
    """
    if modo() == MODO_COMPLETO:
        return list(todas)

    afetadas = set()
    for bruto in arquivos:
        caminho = str(bruto).replace("\\", "/")
        while caminho.startswith("./"):
            caminho = caminho[2:]
        partes = caminho.split("/")
        if partes[0] == "tools":
            if len(partes) < 2 or partes[1] not in todas:
                return list(todas)
            afetadas.add(partes[1])
        elif caminho in _ARQUIVOS_GLOBAIS_DO_GATE:
            return list(todas)

    if not afetadas:
        return list(todas)
    return [ferramenta for ferramenta in todas if ferramenta in afetadas]
