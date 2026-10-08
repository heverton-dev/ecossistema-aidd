#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compilador dos mapas visuais da versão NÃO-TÉCNICA (docs/mapas-visuais/nao-tecnicos).
Lê os moldes ilustrados de docs/mapas-visuais/moldes-nao-tecnicos/ e injeta os mesmos
dados factuais do catálogo de peças (scripts/catalogo_pecas.py), montados pela mesma
aplicar_molde da versão técnica (scripts/mapa_visual.py).

Os números e listas são os da versão técnica; só os campos de descrição mudam, e
sempre para PT-BR: a descrição de cada skill vem do comando slash que a chama (já
escrito em PT-BR) ou, sem comando, de moldes-nao-tecnicos/descricoes-pt.json. Skill
sem nenhuma das duas é erro (exit 1): o mapa nunca volta para o inglês da SKILL.md
nem inventa texto.

Uso:
  python scripts/compilar_mapas_nao_tecnicos.py    # grava a versão não técnica de todos os mapas
Exit 0: gravados. Exit 1: catálogo ausente, molde ausente ou descrição PT-BR faltando.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import mapa_visual as mv  # noqa: E402
from gravacao_atomica_mapas import gravar_lote  # noqa: E402
from resiliencia_mapas import ler_texto, relatar_falha  # noqa: E402
from telemetria_mapas import Medicao, medir  # noqa: E402

MOLDES_NAO_TECNICOS = RAIZ / "docs" / "mapas-visuais" / "moldes-nao-tecnicos"
DESTINO = RAIZ / "docs" / "mapas-visuais" / "nao-tecnicos"
DESCRICOES_PT = MOLDES_NAO_TECNICOS / "descricoes-pt.json"
GATILHO_PT = 'gatilho "quando usar"'


def descricoes_pt(catalogo: dict) -> dict[str, str]:
    """skill -> descrição em PT-BR, nesta ordem: o comando slash de mesmo nome (sem o prefixo
    aidd-), senão o primeiro comando (por nome) que chama a skill, senão descricoes-pt.json.
    Levanta ValueError com a lista das skills sem nenhuma das fontes."""
    extras = json.loads(ler_texto(DESCRICOES_PT)) if DESCRICOES_PT.is_file() else {}
    comandos = defaultdict(list)
    for c in sorted(catalogo.get("comandos_slash", []), key=lambda c: c["id"]):
        if c.get("skill") and c.get("descricao"):
            comandos[c["skill"]].append(c)
    resultado, faltando = {}, []
    for s in catalogo["skills"]:
        if s.get("terceiro"):
            continue
        candidatos = comandos.get(s["id"], [])
        mesmo_nome = [c for c in candidatos if c["id"] == s["id"].removeprefix("aidd-")]
        escolhido = (mesmo_nome or candidatos or [None])[0]
        texto = escolhido["descricao"] if escolhido else extras.get(s["id"], "")
        if texto:
            resultado[s["id"]] = texto
        else:
            faltando.append(s["id"])
    if faltando:
        raise ValueError(f"skills sem descrição em PT-BR (nem comando slash, nem {DESCRICOES_PT.name}): "
                         f"{', '.join(sorted(faltando))}")
    return resultado


def valores_nao_tecnicos_skills(catalogo: dict) -> dict[str, str]:
    """Mesmos números e listas do mapa técnico de skills, com as descrições em PT-BR."""
    return mv.valores_skills(catalogo, descricoes=descricoes_pt(catalogo), gatilho=GATILHO_PT)


# Tipo cujo mapa não técnico troca campos de descrição; os demais usam os valores técnicos
# tal como estão (os textos deles já são PT-BR: docstrings, READMEs e comandos).
TROCAS_DE_DESCRICAO = {"skills": valores_nao_tecnicos_skills}


def valores_nao_tecnicos(tipo: str, catalogo: dict) -> dict[str, str]:
    troca = TROCAS_DE_DESCRICAO.get(tipo)
    return troca(catalogo) if troca else mv.valores_do_tipo(tipo, catalogo)


def compilar_nao_tecnico(tipo: str, catalogo: dict, link_manual: str = mv.MANUAL) -> str:
    valores = {**valores_nao_tecnicos(tipo, catalogo), "LINK_MANUAL": mv.e(link_manual)}
    return mv.aplicar_molde(MOLDES_NAO_TECNICOS / f"{tipo}.html", valores,
                            f"{mv.TITULOS[tipo]} (Versão Conceitual)", fragmento=False)


def destino(tipo: str) -> Path:
    """Arquivo da versão não técnica: mesmo nome da técnica, na pasta nao-tecnicos/."""
    return DESTINO / mv.arquivo_mapa(tipo)


def main() -> int:
    with medir("nao-tecnico", "todos", mv.CATALOGO) as medicao:
        medicao.exit_code = _compilar_todos(medicao)
    return medicao.exit_code


def _compilar_todos(medicao: Medicao) -> int:
    if not mv.CATALOGO.is_file():
        print(f"[ERRO] {mv.CATALOGO} não existe.")
        return 1
    tipos = ["indice", *(tipo for tipo, _, _ in mv.MAPAS_PREVISTOS)]
    try:
        cat = json.loads(ler_texto(mv.CATALOGO))
        # Todos os tipos montados em memória e gravados num lote só: tudo ou nada.
        gravados = gravar_lote({destino(tipo): compilar_nao_tecnico(tipo, cat) for tipo in tipos})
        medicao.arquivos_gravados = len(gravados)
    except (OSError, ValueError) as erro:
        return relatar_falha(erro, "nao-tecnico", "todos", mv.CATALOGO)
    print(f"\nTodos os {len(tipos)} mapas não-técnicos compilados com sucesso!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
