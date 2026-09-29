#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compilador dos mapas visuais da versão NÃO-TÉCNICA (docs/mapas-visuais/nao-tecnicos).
Lê os moldes ilustrados de docs/mapas-visuais/moldes-nao-tecnicos/ e injeta os mesmos
dados factuais de catalogo-pecas.json gerados por scripts/catalogo_pecas.py.
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import mapa_visual as mv

MOLDES_NAO_TECNICOS = RAIZ / "docs" / "mapas-visuais" / "moldes-nao-tecnicos"
DESTINO = RAIZ / "docs" / "mapas-visuais" / "nao-tecnicos"
DESTINO.mkdir(parents=True, exist_ok=True)


def compilar_nao_tecnico(tipo: str, catalogo: dict, link_manual: str = "manual-montagem-aidd.html") -> str:
    molde_arq = MOLDES_NAO_TECNICOS / f"{tipo}.html"
    if not molde_arq.is_file():
        raise FileNotFoundError(f"Molde não encontrado: {molde_arq}")
    molde = molde_arq.read_text(encoding="utf-8")
    valores = {**mv.GERADORES[tipo](catalogo), "LINK_MANUAL": mv.e(link_manual)}
    marcadores = set(re.findall(r"\{\{([A-Z_]+)\}\}", molde))
    if marcadores != set(valores):
        raise ValueError(
            f"Molde e gerador desencontrados para '{tipo}': só no molde {sorted(marcadores - set(valores))}, "
            f"só no gerador {sorted(set(valores) - marcadores)}"
        )
    corpo = re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: valores[m.group(1)], molde)
    css_arq = MOLDES_NAO_TECNICOS / "base.css"
    if not css_arq.is_file():
        css_arq = RAIZ / "docs" / "mapas-visuais" / "moldes" / "base.css"
    css = css_arq.read_text(encoding="utf-8")
    cabeca = (
        f'<title>{mv.e(mv.TITULOS[tipo])} (Versão Conceitual)</title>\n'
        f'<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        f'<link rel="stylesheet" href="{mv.e(mv.FONTES)}">\n<style>\n{css}</style>\n'
    )
    return (
        '<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        f'{cabeca}</head>\n<body>\n{corpo}</body>\n</html>\n'
    )


def main():
    if not mv.CATALOGO.is_file():
        print(f"[ERRO] {mv.CATALOGO} não existe.")
        return 1
    cat = json.loads(mv.CATALOGO.read_text(encoding="utf-8"))

    # Compilar indice (mapa-00)
    html_indice = compilar_nao_tecnico("indice", cat)
    (DESTINO / "mapa-00-indice.html").write_text(html_indice, encoding="utf-8")
    print(f"[OK] Gravado {DESTINO / 'mapa-00-indice.html'}")

    # Compilar os outros 12 mapas
    for n, (tipo, _, _) in enumerate(mv.MAPAS_PREVISTOS, start=1):
        nome_arq = f"mapa-{n:02d}-{tipo}.html"
        saida = DESTINO / nome_arq
        conteudo = compilar_nao_tecnico(tipo, cat)
        saida.write_text(conteudo, encoding="utf-8")
        print(f"[OK] Gravado {saida}")

    print("\nTodos os 13 mapas não-técnicos compilados com sucesso!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
