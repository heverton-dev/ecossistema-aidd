#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador dos mapas visuais (docs/mapas-visuais), um por tipo de peça.

Cada mapa junta duas partes:
  - o texto fixo de "como construir", em docs/mapas-visuais/moldes/<tipo>.html;
  - as listas e números, lidos de docs/auditoria/mapa-pecas/catalogo-pecas.json
    (gerado por scripts/catalogo_pecas.py). Nada da lista é escrito à mão.

O molde marca onde entra cada parte com {{MARCADOR}}. Marcador sem valor ou
valor sem marcador é erro (exit 1), para o molde e o gerador não se desencontrarem.

Uso:
  python scripts/mapa_visual.py <tipo> [--saida ARQ] [--fragmento] [--link-manual URL] [--check]
    <tipo>         indice | guardas | skills | ... (ver MAPAS_PREVISTOS)
    --saida        destino (padrão: docs/mapas-visuais/mapa-<tipo>.html)
    --fragmento    grava sem <!doctype>/<head> (formato de publicação do Artifact)
    --link-manual  destino do link "voltar ao manual" (padrão: manual-montagem-aidd.html)
    --check        não grava; exit 1 se o arquivo existente estiver desatualizado
Exit 0: mapa gravado (ou em dia, no --check). Exit 1: erro ou --check divergente.
"""
import argparse
import html
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MAPAS = RAIZ / "docs" / "mapas-visuais"
MOLDES = MAPAS / "moldes"
CATALOGO = RAIZ / "docs" / "auditoria" / "mapa-pecas" / "catalogo-pecas.json"
FONTES = ("https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;"
          "12..96,700;12..96,800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500"
          "&display=swap")
TITULOS = {"guardas": "Mapa dos Guardas", "skills": "Mapa das Skills", "indice": "Mapas do Ecossistema",
           "encaixes": "Mapa dos Encaixes", "ferramentas": "Mapa das Ferramentas",
           "comandos": "Mapa dos Comandos Slash"}
# Os mapas que o ecossistema precisa ter, na ordem de criação. O índice mostra
# cada um como concluído (arquivo em dia com o catálogo), desatualizado ou a criar.
MAPAS_PREVISTOS = (
    ("guardas", "Mapa dos guardas", "todos os guardas, onde moram e quem prova que morde"),
    ("skills", "Mapa das skills", "todas as skills nossas, os terceiros e como criar uma"),
    ("encaixes", "Mapa dos encaixes", "as etapas da Tríade, os contratos entre elas e onde cada fluxo quebra"),
    ("ferramentas", "Mapa das ferramentas", "as 8 ferramentas, seus comandos de CLI e as tarefas com mais de uma dona"),
    ("comandos", "Mapa dos comandos slash", "o que você digita e qual skill cada comando chama"),
    ("conexoes", "Mapa das conexões", "os MCPs (telefones para fora) e os hooks (alarmes)"),
)
META_LINHAS_SKILL = 150
META_GUARDAS = ("G_PORTAO_PROVA_QUE_MORDE", "G_LEI_DECLARA_PORTAO")
ORDEM_CASAS = ("meta", "ecossistema", "ferramenta", "entrega", "componente")
NOMES_CASAS = {
    "meta": ("Meta-guardas", "vigiam os outros guardas", "var(--c-pensa)"),
    "ecossistema": ("Guardas do ecossistema", "gates/ · rodam no commit", "var(--c-guarda)"),
    "ferramenta": ("Guardas das ferramentas", "tools/<f>/gates · scripts/gates", "var(--c-trabalha)"),
    "entrega": ("Só nos moldes de entrega", "templates/gates · vão junto com o app", "var(--brick)"),
    "componente": ("Guardas de componentes", "componentes/", "var(--c-regra)"),
}


def e(texto) -> str:
    return html.escape(str(texto), quote=True)


def _dona(caminho: str) -> str:
    partes = caminho.split("/")
    return partes[1].replace("aidd-", "") if partes[0] == "tools" else partes[0]


def _casa(gate: dict) -> str:
    if gate["id"] in META_GUARDAS:
        return "meta"
    papeis = {c["papel"] for c in gate["copias"]}
    return next(c for c in ORDEM_CASAS[1:] if c in papeis)


def _lista_curta(itens: list[str], vazio: str) -> str:
    if not itens:
        return f'<p class="vazio">{e(vazio)}</p>'
    return '<p class="chips" style="display:flex;flex-wrap:wrap;gap:6px">' + "".join(
        f'<code>{e(i)}</code>' for i in itens) + "</p>"


def _chips(g: dict) -> str:
    chips = []
    if g["no_pre_commit"]:
        chips.append('<span class="chip ok">no commit</span>')
    elif g["prova_que_morde"] is not None:
        chips.append('<span class="chip aviso">fora do commit</span>')
    if g["prova_que_morde"] is True:
        chips.append('<span class="chip ok">prova que morde</span>')
    elif g["prova_que_morde"] is False:
        chips.append('<span class="chip falha">sem prova</span>')
    chips += [f'<span class="chip lei">Lei #{n}</span>' for n in g["leis"]]
    if g["versoes_distintas"] > 1:
        chips.append(f'<span class="chip aviso">{g["versoes_distintas"]} versões</span>')
    return "".join(chips)


def _item(g: dict, casa: str) -> str:
    onde = defaultdict(list)
    for c in g["copias"]:
        onde[c["papel"]].append(_dona(c["caminho"]))
    onde_txt = " · ".join(f'{papel}: {", ".join(sorted(set(donas)))}' for papel, donas in sorted(onde.items()))
    busca = " ".join([g["id"], g["descricao"], onde_txt]).lower()
    atributos = {
        "busca": busca,
        "versoes": int(g["versoes_distintas"] > 1),
        "semlei": int(not g["leis"]),
        "foracommit": int(g["prova_que_morde"] is not None and not g["no_pre_commit"]),
    }
    dados = " ".join(f'data-{k}="{e(v)}"' for k, v in atributos.items())
    return (f'<article class="item" style="--c:{NOMES_CASAS[casa][2]}" {dados}>'
            f'<span class="nome">{e(g["id"])}</span>'
            f'<p class="desc">{e(g["descricao"] or "sem descrição no docstring")}</p>'
            f'<div class="chips">{_chips(g)}</div>'
            f'<span class="onde">{e(onde_txt)}</span></article>')


def _totais(itens: list[tuple[str, str, str]]) -> str:
    return '<div class="totais">' + "".join(
        f'<div class="total {cls}"><b>{e(n)}</b><span>{e(rot)}</span></div>' for n, rot, cls in itens) + "</div>"


def valores_guardas(cat: dict) -> dict[str, str]:
    gates = cat["gates"]
    raiz = [g for g in gates if g["prova_que_morde"] is not None]
    divergentes = [g["id"] for g in gates if g["versoes_distintas"] > 1]
    fora = [g["id"] for g in raiz if not g["no_pre_commit"]]
    invisiveis = cat["achados"].get("declaracoes_de_lei_invisiveis_ao_meta_gate", [])
    grupos = defaultdict(list)
    for g in gates:
        grupos[_casa(g)].append(g)
    lista = []
    for casa in ORDEM_CASAS:
        if not grupos[casa]:
            continue
        nome, dica, _ = NOMES_CASAS[casa]
        lista.append(f'<div class="grupo"><h3>{e(nome)} <small>{len(grupos[casa])} · {e(dica)}</small></h3>'
                     f'<div class="itens">{"".join(_item(g, casa) for g in grupos[casa])}</div></div>')
    return {
        "TOTAIS": _totais([
            (len(gates), "guardas (nomes)", ""),
            (sum(len(g["copias"]) for g in gates), "arquivos", ""),
            (len(raiz), "no ecossistema", ""),
            (sum(1 for g in raiz if g["no_pre_commit"]), "rodam no commit", ""),
            (sum(1 for g in raiz if g["prova_que_morde"]), f"de {len(raiz)} com prova que morde", ""),
            (sum(1 for g in gates if g["leis"]), "ligados a uma lei", ""),
            (len(divergentes), "com versões diferentes", "aviso"),
            (len(invisiveis), "declarações invisíveis", "falha"),
        ]),
        "DIVERGENTES": _lista_curta(divergentes, "Nenhum caso hoje."),
        "INVISIVEIS": _lista_curta(invisiveis, "Nenhuma declaração invisível hoje."),
        "FORA_COMMIT": _lista_curta(fora, "Todos os guardas de ecossistema rodam no commit."),
        "LISTA": "".join(lista),
    }


def _usa_quando(descricao: str) -> bool:
    return "use when" in (descricao or "").lower()


def _item_skill(s: dict) -> str:
    acima = s["linhas"] > META_LINHAS_SKILL
    chips = [f'<span class="chip {"aviso" if acima else "ok"}">{s["linhas"]} linhas</span>']
    if not _usa_quando(s["descricao"]):
        chips.append('<span class="chip falha">sem "Use when"</span>')
    atributos = {"busca": f'{s["id"]} {s["descricao"]}'.lower(), "acima": int(acima),
                 "semuse": int(not _usa_quando(s["descricao"]))}
    dados = " ".join(f'data-{k}="{e(v)}"' for k, v in atributos.items())
    return (f'<article class="item" style="--c:var(--c-trabalha)" {dados}>'
            f'<span class="nome">{e(s["id"])}</span>'
            f'<p class="desc">{e(s["descricao"] or "sem descrição")}</p>'
            f'<div class="chips">{"".join(chips)}</div></article>')


def valores_skills(cat: dict) -> dict[str, str]:
    skills = [s for s in cat["skills"] if not s.get("terceiro")]
    copiadas = [s["id"] for s in cat["skills"] if s.get("terceiro")]
    terceiros = cat.get("skills_terceiros", [])
    acima = [f'{s["id"]} ({s["linhas"]})' for s in skills if s["linhas"] > META_LINHAS_SKILL]
    grupos = [("Até a meta de 150 linhas", [s for s in skills if s["linhas"] <= META_LINHAS_SKILL]),
              ("Acima da meta", [s for s in skills if s["linhas"] > META_LINHAS_SKILL])]
    lista = "".join(
        f'<div class="grupo"><h3>{e(nome)} <small>{len(itens)}</small></h3>'
        f'<div class="itens">{"".join(_item_skill(s) for s in itens)}</div></div>'
        for nome, itens in grupos if itens)
    return {
        "TOTAIS": _totais([
            (len(skills), "skills nossas", ""),
            (len(terceiros), "nomes de terceiros registrados", ""),
            (len(copiadas), "terceiros copiados para a fonte", "falha" if copiadas else ""),
            (sum(1 for s in skills if _usa_quando(s["descricao"])), f"de {len(skills)} com \"Use when\"", ""),
            (len(acima), "acima de 150 linhas", "aviso" if acima else ""),
            (len(cat["achados"].get("skills_mesma_descricao", [])), "pares com a mesma descrição", ""),
        ]),
        "TERCEIROS": _lista_curta(terceiros, "Nenhuma skill de terceiros registrada."),
        "ACIMA_META": _lista_curta(acima, "Nenhuma skill acima da meta hoje."),
        "MESMA_DESCRICAO": _lista_curta([" = ".join(p) for p in cat["achados"].get("skills_mesma_descricao", [])],
                                        "Nenhum par hoje."),
        "LISTA": lista,
    }


def _nome_etapa(etapa: str) -> str:
    m = re.match(r"etapa_(\d+)_(.+)", etapa)
    return f"{int(m.group(1))} · {m.group(2)}" if m else etapa


def valores_encaixes(cat: dict) -> dict[str, str]:
    etapas = cat["receita_triade"]["etapas"]
    encaixes = cat.get("encaixes") or []
    achados = cat["achados"]
    por_chamada = {x["chamada"]: x for x in encaixes}
    fluxo_de = {}
    for et in etapas:
        for fluxo, chamadas in et["chamadas_por_fluxo"].items():
            for tokens in chamadas:
                fluxo_de["ecossistema.py " + " ".join(tokens)] = fluxo
    cartoes = []
    for et in etapas:
        linhas = []
        for tokens in et["chamadas_cli"]:
            chamada = "ecossistema.py " + " ".join(tokens)
            enc = por_chamada.get(chamada)
            if enc is None:
                chip = '<span class="chip aviso">não conferida</span>'
            elif enc["encaixa"]:
                chip = '<span class="chip ok">encaixa</span>'
            else:
                chip = '<span class="chip falha">quebra</span>'
            fluxo = f'<span class="chip lei">só {e(fluxo_de[chamada])}</span>' if chamada in fluxo_de else ""
            linhas.append(f'<div class="chips"><code>{e(chamada)}</code>{chip}{fluxo}</div>')
        if not linhas:
            linhas.append('<p class="vazio">Não chama nenhuma ferramenta.</p>')
        for atalho in et["atalhos_internos"]:
            linhas.append(f'<div class="chips"><code>{e(atalho)}</code><span class="chip aviso">atalho por dentro</span></div>')
        cor = "var(--c-trabalha)" if et["chama_alguma_ferramenta"] else "var(--brick)"
        cartoes.append(f'<article class="item" style="--c:{cor}" data-busca="{e(et["etapa"])}">'
                       f'<span class="nome">{e(_nome_etapa(et["etapa"]))}</span>'
                       f'<p class="desc">{e(et["descricao"])}</p>{"".join(linhas)}</article>')
    quebrados = [f'{_nome_etapa(x["etapa"])}: {x["chamada"]} ({"; ".join(x["problemas"])})'
                 for x in encaixes if not x["encaixa"]]
    atalhos = [f'{_nome_etapa(et)}: {", ".join(cam)}' for et, cam in achados.get("etapas_com_atalho_interno", {}).items()]
    contratos = "".join(
        f'<article class="item" style="--c:var(--brick)" data-busca="{e(c["id"])}"><span class="nome">{e(c["id"])}</span>'
        f'<p class="desc">{e(c["titulo"])}</p><span class="onde">{e(" · ".join(c["usado_por"]))}</span></article>'
        for c in cat["contratos"])
    return {
        "TOTAIS": _totais([
            (len(etapas), "etapas na receita", ""),
            (len(encaixes), "chamadas conferidas", ""),
            (len(quebrados), "chamadas que quebram", "falha" if quebrados else ""),
            (len(achados.get("etapas_sem_ferramenta", [])), "etapas sem ferramenta", "aviso" if achados.get("etapas_sem_ferramenta") else ""),
            (len(cat["contratos"]), "contratos", ""),
        ]),
        "RECEITA": f'<div class="grupo"><div class="itens">{"".join(cartoes)}</div></div>',
        "QUEBRADOS": _lista_curta(quebrados, "Todas as chamadas encaixam hoje."),
        "SEM_FERRAMENTA": _lista_curta([_nome_etapa(x) for x in achados.get("etapas_sem_ferramenta", [])],
                                       "Toda etapa chama uma ferramenta."),
        "ATALHOS": _lista_curta(atalhos, "Nenhum atalho por dentro hoje."),
        "CONTRATOS": f'<div class="grupo"><div class="itens">{contratos}</div></div>',
    }


def valores_ferramentas(cat: dict) -> dict[str, str]:
    ferramentas = cat["ferramentas"]
    achados = cat["achados"]
    verbos = achados.get("verbos_cli_repetidos", {})
    donas = achados.get("tarefas_com_varias_donas", {})
    identicos = achados.get("arquivos_identicos_entre_donas", [])
    cartoes = []
    for f in ferramentas:
        chips = "".join(
            f'<code>{e(c)}</code>' if c not in verbos else f'<code>{e(c)}</code><span class="chip aviso">repetido</span>'
            for c in f["comandos"])
        extras = [f'{len(f["comandos"])} comandos', f'{len(f["gates_proprios"])} guardas próprios',
                  f'{f["arquivos_py"]} arquivos .py']
        if f["mcps_proprios"]:
            extras.append(f'{len(f["mcps_proprios"])} MCPs')
        busca = " ".join([f["id"], f["descricao"], " ".join(f["comandos"])]).lower()
        cartoes.append(f'<article class="item" style="--c:var(--c-trabalha)" data-busca="{e(busca)}">'
                       f'<span class="nome">{e(f["id"])}</span>'
                       f'<p class="desc">{e(f["descricao"] or "sem descrição no README")}</p>'
                       f'<div class="chips" style="display:flex;flex-wrap:wrap;gap:6px">{chips or "<span class=vazio>sem comandos</span>"}</div>'
                       f'<span class="onde">{e(f["chamada"])} · {e(" · ".join(extras))}</span></article>')
    return {
        "TOTAIS": _totais([
            (len(ferramentas), "ferramentas", ""),
            (sum(len(f["comandos"]) for f in ferramentas), "comandos de CLI", ""),
            (len(verbos), "verbos em mais de uma ferramenta", "aviso" if verbos else ""),
            (len(donas), "tarefas com várias donas", "aviso" if donas else ""),
            (sum(x["arquivos"] for x in identicos), "arquivos idênticos copiados", "aviso" if identicos else ""),
        ]),
        "VERBOS": _lista_curta([f'{v}: {", ".join(fs)}' for v, fs in sorted(verbos.items())], "Nenhum verbo repetido hoje."),
        "DONAS": _lista_curta([f'{t}: {", ".join(d["donas"])}' for t, d in sorted(donas.items())],
                              "Nenhuma tarefa com mais de uma dona hoje."),
        "IDENTICOS": _lista_curta([f'{x["donas"]}: {x["arquivos"]}' for x in identicos], "Nenhuma cópia hoje."),
        "LISTA": f'<div class="grupo"><div class="itens">{"".join(cartoes)}</div></div>',
    }


def valores_comandos(cat: dict) -> dict[str, str]:
    comandos = cat["comandos_slash"]
    quebrados = [f'/{c["id"]} → {c["skill"]}' for c in comandos if c.get("skill") and not c.get("skill_existe")]
    sem_skill = [f'/{c["id"]}' for c in comandos if not c.get("skill")]
    cartoes = []
    for c in comandos:
        if not c.get("skill"):
            chip = '<span class="chip aviso">sem skill</span>'
        elif c.get("skill_existe"):
            chip = f'<code>{e(c["skill"])}</code><span class="chip ok">existe</span>'
        else:
            chip = f'<code>{e(c["skill"])}</code><span class="chip falha">não existe</span>'
        cartoes.append(f'<article class="item" style="--c:var(--c-regra)" data-busca="{e(c["id"])}">'
                       f'<span class="nome">/{e(c["id"])}</span>'
                       f'<p class="desc">{e(c.get("descricao") or "sem descrição")}</p>'
                       f'<div class="chips">{chip}</div><span class="onde">{e(c["caminho"])}</span></article>')
    return {
        "TOTAIS": _totais([
            (len(comandos), "comandos slash", ""),
            (sum(1 for c in comandos if c.get("skill_existe")), "apontam para uma skill que existe", ""),
            (len(quebrados), "apontam para skill que não existe", "falha" if quebrados else ""),
            (len(sem_skill), "não dizem qual skill chamam", "aviso" if sem_skill else ""),
        ]),
        "QUEBRADOS": _lista_curta(quebrados, "Nenhum hoje."),
        "SEM_SKILL": _lista_curta(sem_skill, "Nenhum hoje."),
        "LISTA": f'<div class="grupo"><div class="itens">{"".join(cartoes)}</div></div>',
    }


def status_mapa(tipo: str, cat: dict) -> str:
    """concluido = arquivo existe e está em dia com o catálogo; desatualizado = existe e
    difere; a-criar = sem gerador ou sem arquivo."""
    arquivo = MAPAS / f"mapa-{tipo}.html"
    if tipo not in GERADORES or not arquivo.is_file():
        return "a-criar"
    em_dia = arquivo.read_text(encoding="utf-8") == montar(tipo, cat, "manual-montagem-aidd.html", False)
    return "concluido" if em_dia else "desatualizado"


ROTULO_STATUS = {"concluido": ("concluído", "ok"), "desatualizado": ("desatualizado", "aviso"),
                 "a-criar": ("a criar", "falha")}


def valores_indice(cat: dict) -> dict[str, str]:
    linhas = []
    contagem = defaultdict(int)
    for n, (tipo, titulo, para_que) in enumerate(MAPAS_PREVISTOS, 1):
        status = status_mapa(tipo, cat)
        contagem[status] += 1
        rotulo, cls = ROTULO_STATUS[status]
        link = (f'<a class="mapa-link" href="mapa-{e(tipo)}.html">abrir →</a>' if status != "a-criar"
                else '<span class="vazio">ainda não existe</span>')
        linhas.append(f'<article class="item" style="--c:var(--c-trabalha)" data-busca="{e((titulo + " " + para_que).lower())}">'
                      f'<span class="nome">{n}. {e(titulo)}</span><p class="desc">{e(para_que)}</p>'
                      f'<div class="chips"><span class="chip {cls}">{rotulo}</span></div>{link}</article>')
    total = len(MAPAS_PREVISTOS)
    return {
        "TOTAIS": _totais([
            (contagem["concluido"], f"de {total} mapas concluídos", ""),
            (contagem["desatualizado"], "desatualizados", "aviso" if contagem["desatualizado"] else ""),
            (contagem["a-criar"], "a criar", "falha" if contagem["a-criar"] else ""),
        ]),
        "LISTA": f'<div class="grupo"><div class="itens">{"".join(linhas)}</div></div>',
    }


GERADORES = {"guardas": valores_guardas, "skills": valores_skills, "indice": valores_indice,
             "encaixes": valores_encaixes, "ferramentas": valores_ferramentas,
             "comandos": valores_comandos}


def montar(tipo: str, cat: dict, link_manual: str, fragmento: bool) -> str:
    molde = (MOLDES / f"{tipo}.html").read_text(encoding="utf-8")
    valores = {**GERADORES[tipo](cat), "LINK_MANUAL": e(link_manual)}
    marcadores = set(re.findall(r"\{\{([A-Z_]+)\}\}", molde))
    if marcadores != set(valores):
        raise ValueError(f"molde e gerador desencontrados: só no molde {sorted(marcadores - set(valores))}, "
                         f"só no gerador {sorted(set(valores) - marcadores)}")
    corpo = re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: valores[m.group(1)], molde)
    css = (MOLDES / "base.css").read_text(encoding="utf-8")
    cabeca = (f'<title>{e(TITULOS[tipo])}</title>\n<link rel="preconnect" href="https://fonts.googleapis.com">\n'
              f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
              f'<link rel="stylesheet" href="{e(FONTES)}">\n<style>\n{css}</style>\n')
    if fragmento:
        return cabeca + corpo
    return ('<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'{cabeca}</head>\n<body>\n{corpo}</body>\n</html>\n')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gera um mapa visual a partir do catálogo de peças.")
    parser.add_argument("tipo", choices=sorted(GERADORES))
    parser.add_argument("--saida", type=Path)
    parser.add_argument("--fragmento", action="store_true")
    parser.add_argument("--link-manual", default="manual-montagem-aidd.html")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if not CATALOGO.is_file():
        print(f"[ERRO] {CATALOGO} não existe. Rode antes: python scripts/catalogo_pecas.py")
        return 1
    try:
        texto = montar(args.tipo, json.loads(CATALOGO.read_text(encoding="utf-8")),
                       args.link_manual, args.fragmento)
    except ValueError as erro:
        print(f"[ERRO] {erro}")
        return 1
    saida = args.saida or MAPAS / f"mapa-{args.tipo}.html"
    if args.check:
        if not saida.is_file() or saida.read_text(encoding="utf-8") != texto:
            print(f"[DESATUALIZADO] {saida} difere do catálogo. Rode: python scripts/mapa_visual.py {args.tipo}")
            return 1
        print(f"[OK] {saida} em dia com o catálogo.")
        return 0
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(texto, encoding="utf-8")
    print(f"[OK] Mapa gravado em {saida}")
    return 0


if __name__ == "__main__":
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")
    sys.exit(main())
