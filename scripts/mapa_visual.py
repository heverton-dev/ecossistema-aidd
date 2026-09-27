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
           "comandos": "Mapa dos Comandos Slash", "conexoes": "Mapa das Conexões",
           "leis": "Mapa das Leis",
           "lente15d": "Mapa da Lente 15D",
           "oficina": "Mapa da Oficina",
           "scripts": "Mapa dos Scripts",
           "moldes": "Mapa dos Moldes de Entrega",
           "harnesses": "Mapa dos Harnesses"}
# Os mapas que o ecossistema precisa ter, na ordem de criação. O índice mostra
# cada um como concluído (arquivo em dia com o catálogo), desatualizado ou a criar.
MAPAS_PREVISTOS = (
    ("guardas", "Mapa dos guardas", "todos os guardas, onde moram e quem prova que morde"),
    ("skills", "Mapa das skills", "todas as skills nossas, os terceiros e como criar uma"),
    ("encaixes", "Mapa dos encaixes", "as etapas da Tríade, os contratos entre elas e onde cada fluxo quebra"),
    ("ferramentas", "Mapa das ferramentas", "as 8 ferramentas, seus comandos de CLI e as tarefas com mais de uma dona"),
    ("comandos", "Mapa dos comandos slash", "o que você digita e qual skill cada comando chama"),
    ("conexoes", "Mapa das conexões", "os MCPs (telefones para fora) e os hooks (alarmes)"),
    ("leis", "Mapa das leis", "cada lei do AGENTS.md e o guarda que a prova, e onde a prova é fraca"),
    ("lente15d", "Mapa da lente 15D", "as 15 dimensões de auditoria e como cada ferramenta se saiu"),
    ("oficina", "Mapa da oficina", "todos os planos e ciclos de auditoria, com as fases cumpridas"),
    ("scripts", "Mapa dos scripts", "cada script de scripts/, o que faz e quem o chama"),
    ("moldes", "Mapa dos moldes de entrega", "o que cada ferramenta entrega junto com o app gerado"),
    ("harnesses", "Mapa dos harnesses", "para onde cada peça é copiada em cada programa de agente"),
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


def valores_conexoes(cat: dict) -> dict[str, str]:
    registrados = cat["mcps"]["registrados_mcp_json"]
    internos = cat["mcps"]["internos_das_ferramentas"]
    hooks = cat["hooks"]
    lista_internos = "".join(
        f'<article class="item" style="--c:var(--c-trabalha)" data-busca="{e(m["id"])}"><span class="nome">{e(m["id"])}</span>'
        f'<p class="desc">da ferramenta {e(m["ferramenta"])}</p>'
        f'<div class="chips"><span class="chip {"ok" if m["registrado_em_config"] else "lei"}">'
        f'{"registrado para o agente" if m["registrado_em_config"] else "vai com o app gerado"}</span></div>'
        f'<span class="onde">{e(m["caminho"])}</span></article>' for m in internos)
    lista_hooks = "".join(
        f'<article class="item" style="--c:var(--c-guarda)" data-busca="{e(h["evento"])}"><span class="nome">{e(h["evento"])}</span>'
        f'<p class="desc">filtro: {e(h["matcher"] or "qualquer ferramenta")}</p>'
        f'<span class="onde">{e(h["script"])}</span></article>' for h in hooks)
    vazio = '<p class="vazio">Nenhum hoje.</p>'
    return {
        "TOTAIS": _totais([
            (len(registrados), "MCPs que o agente usa", ""),
            (len(internos), "MCPs dentro das ferramentas", ""),
            (len(hooks), "hooks", ""),
        ]),
        "REGISTRADOS": _lista_curta(registrados, "Nenhum MCP registrado."),
        "INTERNOS": f'<div class="grupo"><div class="itens">{lista_internos}</div></div>' if internos else vazio,
        "HOOKS": f'<div class="grupo"><div class="itens">{lista_hooks}</div></div>' if hooks else vazio,
    }


def valores_leis(cat: dict) -> dict[str, str]:
    leis = cat["leis"]
    gates = {g["id"]: g for g in cat["gates"]}
    invisiveis, fora, sem_prova, cartoes = [], [], [], []
    declarados = set()
    for lei in leis:
        linhas = []
        for pt in lei["portoes"]:
            g = gates.get(pt["gate"], {})
            declarados.add(pt["gate"])
            chips = [f'<code>{e(pt["gate"])}</code>']
            if not g:
                chips.append('<span class="chip falha">guarda não existe</span>')
            if not pt["visivel"]:
                chips.append('<span class="chip falha">meta-guarda não lê</span>')
                invisiveis.append(f'Lei #{lei["numero"]}: {pt["gate"]}')
            if g and not g.get("no_pre_commit"):
                chips.append('<span class="chip aviso">fora do commit</span>')
                fora.append(f'Lei #{lei["numero"]}: {pt["gate"]}')
            if g and g.get("prova_que_morde") is False:
                chips.append('<span class="chip falha">sem prova</span>')
                sem_prova.append(f'Lei #{lei["numero"]}: {pt["gate"]}')
            if g and g.get("prova_que_morde") and g.get("no_pre_commit") and pt["visivel"]:
                chips.append('<span class="chip ok">prova válida</span>')
            linhas.append(f'<div class="chips" style="display:flex;flex-wrap:wrap;gap:6px">{"".join(chips)}</div>')
        if lei["sem_gate"]:
            linhas.append('<p class="vazio">sem gate — cumprimento por convenção</p>')
        if not linhas:
            linhas.append('<p class="vazio">Nenhuma declaração.</p>')
        cartoes.append(f'<article class="item" style="--c:var(--c-regra)" data-busca="{e(lei["titulo"].lower())}">'
                       f'<span class="nome">Lei #{lei["numero"]} · {e(lei["titulo"])}</span>{"".join(linhas)}</article>')
    sem_lei = sorted(g["id"] for g in cat["gates"] if g["prova_que_morde"] is not None and g["id"] not in declarados)
    total_decl = sum(len(lei["portoes"]) for lei in leis)
    return {
        "TOTAIS": _totais([
            (len(leis), "leis", ""),
            (total_decl, "declarações de guarda", ""),
            (len(invisiveis), "o meta-guarda não lê", "falha" if invisiveis else ""),
            (len(fora), "declarados fora do commit", "aviso" if fora else ""),
            (len(sem_lei), "guardas da raiz sem lei", "aviso" if sem_lei else ""),
        ]),
        "INVISIVEIS": _lista_curta(invisiveis, "Nenhuma hoje."),
        "FORA_COMMIT": _lista_curta(fora, "Todos os guardas declarados rodam no commit."),
        "SEM_PROVA": _lista_curta(sem_prova, "Todos os guardas declarados têm prova que morde."),
        "SEM_LEI": _lista_curta(sem_lei, "Todo guarda da raiz está ligado a uma lei."),
        "LISTA": f'<div class="grupo"><div class="itens">{"".join(cartoes)}</div></div>',
    }


def valores_harnesses(cat: dict) -> dict[str, str]:
    dados = cat["harnesses"]
    cartoes = []
    for h in dados["harnesses"]:
        destinos = "".join(f'<div class="chips"><span class="chip lei">{e(t)}</span><code>{e(d)}</code></div>'
                           for t, d in sorted(h["destinos"].items()))
        chips = [f'<span class="chip {"ok" if h["confirmado"] else "aviso"}">'
                 f'{"confirmado em doc oficial" if h["confirmado"] else "não confirmado"}</span>',
                 f'<span class="chip ok">{h["skills_em_disco"] - h.get("terceiros_em_disco", 0)} nossas</span>',
                 f'<span class="chip lei">{h.get("terceiros_em_disco", 0)} de terceiros</span>']
        if h.get("nossas_faltando"):
            chips.append(f'<span class="chip falha">faltam {len(h["nossas_faltando"])} nossas</span>')
        if h["config_mcp"]:
            chips.append(f'<code>{e(h["config_mcp"])}</code>')
        cartoes.append(f'<article class="item" style="--c:var(--c-liga)" data-busca="{e(h["id"])}">'
                       f'<span class="nome">{e(h["id"])}</span><p class="desc">pasta <code>{e(h["prefixo"])}/</code></p>'
                       f'<div class="chips" style="display:flex;flex-wrap:wrap;gap:6px">{"".join(chips)}</div>{destinos}</article>')
    legadas = [f'{x["pasta"]} ({x["arquivos_versionados"]} arquivos)' for x in dados["pastas_legadas"]]
    faltando = [f'{h["id"]}: {", ".join(h["nossas_faltando"])}' for h in dados["harnesses"] if h.get("nossas_faltando")]
    return {
        "TOTAIS": _totais([
            (len(dados["harnesses"]), "harnesses", ""),
            (sum(1 for h in dados["harnesses"] if h["confirmado"]), "confirmados em doc oficial", ""),
            (len(faltando), "harnesses sem todas as nossas skills", "falha" if faltando else ""),
            (len(legadas), "pastas legadas versionadas", "aviso" if legadas else ""),
        ]),
        "LEGADAS": _lista_curta(legadas, "Nenhuma pasta legada versionada."),
        "FALTANDO": _lista_curta(faltando, "Todos os harnesses têm todas as nossas skills."),
        "LISTA": f'<div class="grupo"><div class="itens">{"".join(cartoes)}</div></div>',
    }

def valores_moldes(cat: dict) -> dict[str, str]:
    moldes = cat["moldes_entrega"]
    por_ferramenta = defaultdict(list)
    for m in moldes:
        por_ferramenta[m["ferramenta"]].append(m)
    grupos = []
    for f, itens in sorted(por_ferramenta.items()):
        cartoes = "".join(
            f'<article class="item" style="--c:var(--brick)" data-busca="{e(m["molde"])}"><span class="nome">{e(m["molde"])}</span>'
            f'<p class="desc">{m["arquivos"]} arquivos</p><span class="onde">{e(m["caminho"])}</span></article>' for m in itens)
        grupos.append(f'<div class="grupo"><h3>{e(f)} <small>{len(itens)} moldes · '
                      f'{sum(m["arquivos"] for m in itens)} arquivos</small></h3><div class="itens">{cartoes}</div></div>')
    nomes = defaultdict(set)
    for m in moldes:
        nomes[m["molde"]].add(m["ferramenta"])
    repetidos = [f'{n}: {", ".join(sorted(fs))}' for n, fs in sorted(nomes.items()) if len(fs) > 1]
    return {
        "TOTAIS": _totais([
            (len(por_ferramenta), "ferramentas com moldes", ""),
            (len(moldes), "moldes", ""),
            (sum(m["arquivos"] for m in moldes), "arquivos de molde", ""),
            (len(repetidos), "moldes com o mesmo nome em várias ferramentas", "aviso" if repetidos else ""),
        ]),
        "REPETIDOS": _lista_curta(repetidos, "Nenhum molde repetido hoje."),
        "LISTA": "".join(grupos),
    }

ORDEM_CHAMADORES = ("painel", "commit", "guardas", "scripts", "testes")


def valores_scripts(cat: dict) -> dict[str, str]:
    scripts = cat["scripts"]
    soltos = [s["id"] for s in scripts if not s["chamado_por"]]
    so_testes = [s["id"] for s in scripts if s["chamado_por"] == ["testes"]]
    cartoes = []
    for s in scripts:
        chips = "".join(f'<span class="chip lei">{e(c)}</span>' for c in ORDEM_CHAMADORES if c in s["chamado_por"])
        if not s["chamado_por"]:
            chips = '<span class="chip falha">ninguém chama</span>'
        elif s["chamado_por"] == ["testes"]:
            chips += '<span class="chip aviso">só os testes</span>'
        cartoes.append(f'<article class="item" style="--c:var(--c-trabalha)" data-busca="{e((s["id"] + " " + s["descricao"]).lower())}">'
                       f'<span class="nome">{e(s["id"])}.py</span><p class="desc">{e(s["descricao"] or "sem docstring")}</p>'
                       f'<div class="chips" style="display:flex;flex-wrap:wrap;gap:6px">{chips}</div></article>')
    return {
        "TOTAIS": _totais([
            (len(scripts), "scripts em scripts/", ""),
            (sum(1 for s in scripts if "painel" in s["chamado_por"]), "chamados pelo painel", ""),
            (sum(1 for s in scripts if "commit" in s["chamado_por"]), "rodam no commit", ""),
            (len(so_testes), "só os testes chamam", "aviso" if so_testes else ""),
            (len(soltos), "ninguém chama", "falha" if soltos else ""),
        ]),
        "SOLTOS": _lista_curta(soltos, "Todo script tem quem o chame."),
        "SO_TESTES": _lista_curta(so_testes, "Nenhum hoje."),
        "LISTA": f'<div class="grupo"><div class="itens">{"".join(cartoes)}</div></div>',
    }

NOMES_FASES = {"laudo_inicial": "laudo inicial", "plano_evolucao": "plano de evolução",
               "laudo_revisado": "laudo revisado", "dod": "pronto (DoD)"}
ORDEM_ESTADOS = (("rascunho", "Rascunho", "aviso"), ("a-fazer", "A fazer", "lei"),
                 ("fazendo", "Fazendo", "aviso"), ("feitos", "Feitos", "ok"))


def _chip_itens(n: int) -> str:
    return f'<span class="chip">{n} itens</span>' if n else ""


def valores_oficina(cat: dict) -> dict[str, str]:
    of = cat["oficina"]
    grupos = []
    for estado, rotulo, cls in ORDEM_ESTADOS:
        itens = [p for p in of["planos"] if p["estado"] == estado]
        if not itens:
            continue
        cartoes = "".join(
            f'<article class="item" style="--c:var(--c-pensa)" data-busca="{e(p["id"])}"><span class="nome">{e(p["id"])}</span>'
            f'<div class="chips"><span class="chip {cls}">{rotulo}</span>{_chip_itens(p["itens"])}</div></article>'
            for p in itens)
        grupos.append(f'<div class="grupo"><h3>{e(rotulo)} <small>{len(itens)}</small></h3><div class="itens">{cartoes}</div></div>')
    ciclos = []
    for c in of["ciclos"]:
        fases = "".join(f'<span class="chip {"ok" if feito else "falha"}">{e(NOMES_FASES[k])}</span>' for k, feito in c["fases"].items())
        nota = f'<span class="chip lei">nota {e(c["nota"])}/10</span>' if c["nota"] else ""
        ciclos.append(f'<article class="item" style="--c:var(--c-guarda)" data-busca="{e(c["alvo"])}">'
                      f'<span class="nome">{e(c["alvo"])} · {e(c["ciclo"])}</span>'
                      f'<div class="chips" style="display:flex;flex-wrap:wrap;gap:6px">{fases}{nota}</div>'
                      f'<span class="onde">{e(c["caminho"])}</span></article>')
    incompletos = [f'{c["alvo"]}/{c["ciclo"]}' for c in of["ciclos"] if not all(c["fases"].values())]
    parados = [p["id"] for p in of["planos"] if p["estado"] == "fazendo"]
    return {
        "TOTAIS": _totais([
            (len(of["planos"]), "planos", ""),
            (len(parados), "em execução", "aviso" if len(parados) > 3 else ""),
            (len(of["ciclos"]), "ciclos de auditoria", ""),
            (len(incompletos), "ciclos sem os 4 documentos", "aviso" if incompletos else ""),
            (of["relatorios_melhoria"], "relatórios de melhoria", ""),
        ]),
        "FAZENDO": _lista_curta(parados, "Nenhum plano em execução."),
        "INCOMPLETOS": _lista_curta(incompletos, "Todos os ciclos têm os 4 documentos."),
        "PLANOS": "".join(grupos),
        "CICLOS": f'<div class="grupo"><div class="itens">{"".join(ciclos)}</div></div>',
    }

ROTULO_DIMENSAO = {"ok": ("implementado", "ok"), "parcial": ("parcial", "aviso"), "falha": ("falha", "falha"),
                   "descrito": ("descrito", "lei"), "": ("sem registro", "")}


def valores_lente15d(cat: dict) -> dict[str, str]:
    lente = cat["lente_15d"]
    cabeca = "".join(f'<th scope="col">{e(l["alvo"])}<br><small>{e(l["ciclo"])}</small></th>' for l in lente["laudos"])
    linhas = []
    falhas = defaultdict(int)
    for d in lente["dimensoes"]:
        celulas = []
        for l in lente["laudos"]:
            classe = l["dimensoes"].get(str(d["numero"]), "")
            rotulo, cls = ROTULO_DIMENSAO[classe]
            if classe == "falha":
                falhas[d["numero"]] += 1
            celulas.append(f'<td><span class="chip {cls}">{rotulo}</span></td>')
        linhas.append(f'<tr><th scope="row">D{d["numero"]} · {e(d["titulo"])}</th>{"".join(celulas)}</tr>')
    tabela = (f'<div class="tab-scroll"><table><thead><tr><th scope="col">Dimensão</th>{cabeca}</tr></thead>'
              f'<tbody>{"".join(linhas)}</tbody></table></div>')
    total_falhas = sum(falhas.values())
    mais_falhas = [f'D{n} · {t}' for n, t in ((d["numero"], d["titulo"]) for d in lente["dimensoes"]) if falhas[n] >= 1]
    return {
        "TOTAIS": _totais([
            (len(lente["dimensoes"]), "dimensões na lente", ""),
            (len(lente["laudos"]), "laudos lidos", ""),
            (total_falhas, "marcações de falha nos laudos", "falha" if total_falhas else ""),
        ]),
        "DIMENSOES": "".join(f'<li><b>D{d["numero"]}</b> · {e(d["titulo"])}</li>' for d in lente["dimensoes"]),
        "FALHAS": _lista_curta(mais_falhas, "Nenhuma dimensão marcada como falha nos laudos lidos."),
        "TABELA": tabela if lente["laudos"] else '<p class="vazio">Nenhum laudo encontrado.</p>',
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
             "comandos": valores_comandos, "conexoes": valores_conexoes,
             "leis": valores_leis,
             "lente15d": valores_lente15d,
             "oficina": valores_oficina,
             "scripts": valores_scripts,
             "moldes": valores_moldes,
             "harnesses": valores_harnesses}


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
