#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera as partes do livro corporativo dos mapas (docs/livros/mapas-aidd/) a partir
do catálogo de peças e do ACHADOS.json, na mesma ordem de leitura dos mapas
(MAPAS_PREVISTOS em scripts/mapa_visual.py). O texto fixo de cada capítulo mora
aqui; números e listas vêm dos dados. A compilação (pandoc + typst) é do motor
da skill aidd-textbook.

Uso:
  python scripts/livro_mapas.py            # grava as partes e o manifesto
  python scripts/livro_mapas.py --check    # exit 1 se alguma parte estiver desatualizada
Depois: python componentes/compartilhado/skills/aidd-textbook/scripts/livro.py build docs/livros/mapas-aidd
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import mapa_visual as mv  # noqa: E402

LIVRO = RAIZ / "docs" / "livros" / "mapas-aidd"
CATALOGO = RAIZ / "docs" / "auditoria" / "mapa-pecas" / "catalogo-pecas.json"
ACHADOS = RAIZ / "docs" / "auditoria" / "mapa-pecas" / "ciclo-01" / "ACHADOS.json"
SEP_ESQ = ":" + "-" * 38
SEP_DIR = ":" + "-" * 44
GRAVIDADE = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}


def _txt(texto: str) -> str:
    """Escapa '--' para o pandoc não trocar por travessão (ex.: flags como --dir)."""
    return texto.replace("--", r"\-\-")

PARTES = (
    ("I", "AS REGRAS E AS FÁBRICAS", "O nível macro: as leis que governam a casa, as fábricas que produzem e a receita que as liga.",
     ("leis", "ferramentas", "encaixes")),
    ("II", "AS PEÇAS DO DIA A DIA", "O nível meso: quem confere, quem ensina, os botões, as conexões e para onde tudo é copiado.",
     ("guardas", "skills", "comandos", "conexoes", "harnesses")),
    ("III", "O QUE VAI JUNTO E AS MÁQUINAS", "O nível micro: os moldes que viajam com o app e os scripts que fazem o trabalho mecânico.",
     ("moldes", "scripts")),
    ("IV", "A OFICINA", "Onde a fábrica é consertada: os planos, os ciclos de auditoria e a lente que os inspeciona.",
     ("oficina", "lente15d")),
)

TEXTO = {
    "leis": ("Uma lei é uma regra do `AGENTS.md`. Sozinha, ela é um pedido; vira trava quando um guarda a prova. "
             "Cada lei declara, numa linha própria, o guarda que a prova.",
             "o meta-guarda `G_LEI_DECLARA_PORTAO` e o `G_PORTAO_PROVA_QUE_MORDE`", "`AGENTS.md`, seção 2"),
    "ferramentas": ("Uma ferramenta é uma pequena fábrica especialista em `modulos/<fatia>/.../aidd-<nome>/`, chamada pelo painel "
                    "`ecossistema.py`. Cada uma deveria fazer um trabalho só.",
                    "o `G_TESTES_REAIS` (pytest de cada ferramenta) e o `G_DISCIPLINA_TESTE_FERRAMENTA`", "`tools/`"),
    "encaixes": ("Um encaixe é o formato combinado entre duas peças: a chamada que a receita da Tríade faz a cada "
                 "ferramenta e o contrato JSON Schema que passa de uma etapa para a outra.",
                 "o `G_ORQUESTRADOR_SINCRONO` e a conferência de chamadas do `scripts/catalogo_pecas.py`",
                 "`scripts/orquestrador_sincrono.py` e `componentes/compartilhado/specs/`"),
    "guardas": ("Um guarda é um script sem LLM que confere uma coisa só e responde 0 (passa) ou 1 (para tudo). "
                "É o que transforma regra em trava.",
                "o próprio pre-commit e o `G_PORTAO_PROVA_QUE_MORDE`", "`gates/` e `tools/<f>/gates/`"),
    "skills": ("Uma skill é um manual de tarefa: o agente lê o nome e a descrição de todas e abre o manual inteiro "
               "só quando a tarefa combina. A descrição é o gatilho.",
               "o `G_SKILL_FORMATO`, o `G_SKILL_ROT` e o `G_IDIOMA_LEI_4`", "`componentes/compartilhado/skills/`"),
    "comandos": ("Um comando slash é o botão que a pessoa aperta no chat (`/pure`, `/melhoria`). Ele não trabalha: "
                 "só chama a skill certa.",
                 "a conferência de skill por comando do `scripts/catalogo_pecas.py`", "`componentes/compartilhado/comandos/`"),
    "conexoes": ("O MCP é um telefone para fora: dá ao agente uma ferramenta que mora em outro programa. O hook é um "
                 "alarme que toca sozinho num momento combinado.",
                 "o `dependencia verify` para os MCPs de terceiros", "`.mcp.json` e `.claude/settings.json`"),
    "harnesses": ("Um harness é o programa onde o agente trabalha (Claude Code, OpenCode, Cursor e outros). Cada um lê "
                  "as peças de uma pasta própria, gerada a partir de uma fonte única.",
                  "o `components verify`, o `G_HARNESS_COMPAT` e o `G_UNIVERSAL_HARNESS`", "`gates/manifesto_harnesses.json`"),
    "moldes": ("Um molde é a forma de onde sai o app gerado. Ele mora dentro da ferramenta, em `templates/`, e vai junto "
               "com o que ela entrega ao cliente.",
               "os guardas de entrega gerados por `scripts/gerador_templates_gates.py`", "`tools/<f>/templates/`"),
    "scripts": ("Um script é uma máquina sem cérebro: faz um trabalho mecânico sem LLM. Os de `scripts/` servem o "
                "ecossistema inteiro.",
                "nenhum guarda específico; o mapa mede quem cita cada script", "`scripts/`"),
    "oficina": ("A Tríade é a fábrica; a oficina é onde a fábrica é consertada. Ela tem duas trilhas: os planos "
                "(`/melhoria`, `/plan`, `/orchestrate`) e os ciclos de auditoria em quatro fases (4F).",
                "o `scripts/atualizar_index_planos.py` e o guarda G_auditoria_15D de cada ferramenta auditada (docs/auditoria/<ferramenta>/)",
                "`docs/planos/` e `docs/auditoria/`"),
    "lente15d": ("A lente 15-D é a lista de 15 perguntas que o Inspetor faz a uma ferramenta num ciclo de auditoria, "
                 "de contratos e gatilhos até a entrega final.",
                 "o Inspetor do ciclo 4F, com o guarda G_auditoria_15D de cada ferramenta", "`docs/auditoria/TEMPLATE-AUDITORIA-FERRAMENTA.md`"),
}

FONTES_CATALOGO = {
    "leis": "coletar_leis", "ferramentas": "coletar_ferramentas", "encaixes": "verificar_encaixes",
    "guardas": "coletar_gates", "skills": "coletar_skills", "comandos": "coletar_comandos_slash",
    "conexoes": "coletar_mcps", "harnesses": "coletar_harnesses", "moldes": "coletar_moldes_entrega",
    "scripts": "coletar_scripts", "oficina": "coletar_oficina", "lente15d": "coletar_lente_15d",
}


def numeros(tipo: str, cat: dict) -> list[tuple[str, int]]:
    """Os mesmos números que o mapa mostra, lidos do catálogo."""
    a = cat["achados"]
    if tipo == "leis":
        decl = [p for lei in cat["leis"] for p in lei["portoes"]]
        return [("leis", len(cat["leis"])), ("declarações de guarda", len(decl)),
                ("declarações que o meta-guarda não lê", sum(1 for p in decl if not p["visivel"]))]
    if tipo == "ferramentas":
        return [("ferramentas", len(cat["ferramentas"])),
                ("comandos de CLI", sum(len(f["comandos"]) for f in cat["ferramentas"])),
                ("verbos em mais de uma ferramenta", len(a["verbos_cli_repetidos"])),
                ("tarefas com várias donas", len(a["tarefas_com_varias_donas"]))]
    if tipo == "encaixes":
        return [("etapas na receita", len(cat["receita_triade"]["etapas"])),
                ("chamadas conferidas", len(cat["encaixes"])),
                ("chamadas que quebram", sum(1 for x in cat["encaixes"] if not x["encaixa"])),
                ("etapas sem ferramenta", len(a["etapas_sem_ferramenta"])), ("contratos", len(cat["contratos"]))]
    if tipo == "guardas":
        raiz = [g for g in cat["gates"] if g["prova_que_morde"] is not None]
        return [("guardas (nomes)", len(cat["gates"])), ("no ecossistema", len(raiz)),
                ("rodam no commit", sum(1 for g in raiz if g["no_pre_commit"])),
                ("com versões diferentes", len(a["gates_mesmo_nome_codigo_diferente"]))]
    if tipo == "skills":
        nossas = [s for s in cat["skills"] if not s.get("terceiro")]
        return [("skills nossas", len(nossas)), ("nomes de terceiros registrados", len(cat["skills_terceiros"])),
                ("com \"Use when\"", sum(1 for s in nossas if "use when" in s["descricao"].lower()))]
    if tipo == "comandos":
        c = cat["comandos_slash"]
        return [("comandos slash", len(c)), ("apontam para skill que existe", sum(1 for x in c if x.get("skill_existe")))]
    if tipo == "conexoes":
        return [("MCPs que o agente usa", len(cat["mcps"]["registrados_mcp_json"])),
                ("MCPs dentro das ferramentas", len(cat["mcps"]["internos_das_ferramentas"])), ("hooks", len(cat["hooks"]))]
    if tipo == "harnesses":
        h = cat["harnesses"]
        return [("harnesses", len(h["harnesses"])), ("pastas legadas versionadas", len(h["pastas_legadas"]))]
    if tipo == "moldes":
        m = cat["moldes_entrega"]
        return [("moldes", len(m)), ("arquivos de molde", sum(x["arquivos"] for x in m))]
    if tipo == "scripts":
        s = cat["scripts"]
        return [("scripts", len(s)), ("chamados pelo painel", sum(1 for x in s if "painel" in x["chamado_por"])),
                ("nenhum código chama", sum(1 for x in s if not x["chamado_por"]))]
    if tipo == "oficina":
        o = cat["oficina"]
        return [("planos", len(o["planos"])), ("em execução", sum(1 for p in o["planos"] if p["estado"] == "fazendo")),
                ("ciclos de auditoria", len(o["ciclos"]))]
    if tipo == "lente15d":
        lente = cat["lente_15d"]
        return [("dimensões", len(lente["dimensoes"])), ("laudos lidos", len(lente["laudos"])),
                ("marcações de falha", sum(1 for x in lente["laudos"] for v in x["dimensoes"].values() if v == "falha"))]
    return []


def tabela(cab: tuple[str, str], linhas: list[tuple[str, str]]) -> str:
    corpo = "\n".join(f"| {a} | {b} |" for a, b in linhas)
    return f"| {cab[0]} | {cab[1]} |\n| {SEP_ESQ} | {SEP_DIR} |\n{corpo}\n"


def capitulo(n: int, tipo: str, titulo: str, para_que: str, cat: dict, achados: list[dict]) -> str:
    oque, quem, onde = TEXTO[tipo]
    arquivo = mv.arquivo_mapa(tipo)
    do_mapa = [x for x in achados if x["mapa"] == tipo and x["estado"] != "resolvido"]
    resolvidos = [x for x in achados if x["mapa"] == tipo and x["estado"] == "resolvido"]
    ficha = (f'```{{=typst}}\n#ficha(\n  ("Mapa", "{arquivo}"),\n  ("Para que serve", "{para_que}"),\n'
             f'  ("Achados em aberto", "{len(do_mapa)}"),\n)\n```\n')
    falhas = "\n".join(f"- **{GRAVIDADE[x['gravidade']]}** · {_txt(x['titulo'])} (`{x['id']}`)." for x in do_mapa) \
        or "Nenhum achado em aberto para este mapa."
    feito = ("\n\nJá resolvido:\n\n" + "\n".join(f"- {_txt(x['titulo'])} (commit `{x.get('resolvido_em', '')}`)." for x in resolvidos)) \
        if resolvidos else ""
    fontes = [f"docs/mapas-visuais/{arquivo}", f"docs/mapas-visuais/moldes/{tipo}.html",
              "docs/auditoria/mapa-pecas/catalogo-pecas.json", "docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json",
              "scripts/catalogo_pecas.py", "scripts/mapa_visual.py"]
    return (f"# Capítulo {n} — {titulo}\n\n{ficha}\n## {n}.1 O que é\n\n{oque}\n\n"
            f"Onde mora: {onde}. Quem confere: {quem}.\n\n"
            f"## {n}.2 Os números de hoje\n\n{tabela(('Medida', 'Valor'), [(r, str(v)) for r, v in numeros(tipo, cat)])}\n"
            f"Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `{FONTES_CATALOGO[tipo]}`), "
            f"os mesmos do mapa `{arquivo}`.\n\n"
            f"## {n}.3 O que falta consertar\n\n{falhas}{feito}\n\n"
            f"O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.\n\n"
            f"## {n}.4 Rastreabilidade do capítulo\n\n" + "\n".join(f"- `{f}`" for f in fontes) + "\n")


def frontmatter(cat: dict, dados: dict) -> str:
    t = dados["totais"]
    return f"""---
title: "Mapas do Ecossistema AIDD"
subtitle: "As peças, onde moram e o que falta consertar"
author:
  - Ecossistema AIDD
date: "26/09/2026"
lang: pt-BR
institute: "Ecossistema AIDD · mapa de peças, ciclo 01"
eyebrow: "LIVRO DIDÁTICO"
tagline: |
  Os {len(mv.MAPAS_PREVISTOS)} mapas visuais do ecossistema, na ordem de leitura, com os números medidos e cada defeito encontrado.
toc: true
toc-depth: 2
abstract: |
  Este livro percorre o ecossistema do geral para o particular: primeiro as leis, as fábricas e a receita
  que as liga; depois as peças do dia a dia; por fim os moldes, as máquinas e a oficina onde tudo é consertado.
  Cada capítulo corresponde a um mapa visual, na mesma ordem dos arquivos em docs/mapas-visuais/.

  Nada aqui é estimado. Os números vêm do catálogo de peças e os defeitos vêm do arquivo de achados, que
  hoje registra {t['aberto']} achados em aberto, {t['suspeita']} sob suspeita e {t['resolvido']} resolvidos.
---

# Como ler este livro

## A quem este livro se destina

A quem desenvolve no ecossistema e precisa saber onde cada peça mora antes de mexer, e a quem vai decidir
o que consertar primeiro. Quem só quer a lista de defeitos pode ir direto ao Apêndice B.

## A estrutura

{tabela(('Parte', 'Capítulos'), [(f'Parte {r} — {nome.capitalize()}', ', '.join(str(mv.arquivo_mapa(t)[5:7]) for t in tipos)) for r, nome, _, tipos in PARTES])}
Cada capítulo responde sempre às mesmas quatro perguntas: o que é, os números de hoje, o que falta consertar e
de onde vieram as afirmações. O índice dos mapas, com o estado de cada um, está em `docs/mapas-visuais/mapa-00-indice.html`.

## As convenções visuais

```{{=typst}}
#painel("Números medidos")[
  Todo número deste livro foi lido do catálogo de peças no dia da geração. Se o catálogo mudar, o livro é
  gerado de novo pelo scripts/livro_mapas.py; nenhum número é digitado à mão.
]
```
"""


def parte(romano: str, nome: str, abertura: str) -> str:
    return f"# PARTE {romano} — {nome}\n\n{abertura}\n\n"


def apendices(dados: dict) -> list[tuple[str, str]]:
    glossario = tabela(("Termo", "Significado"), [
        ("Guarda (gate)", "script sem LLM que responde 0 (passa) ou 1 (para tudo)"),
        ("Skill", "manual de tarefa que o agente abre quando a descrição combina"),
        ("Comando slash", "botão do chat que chama uma skill"),
        ("MCP", "telefone para fora: ferramenta que mora em outro programa"),
        ("Hook", "alarme que toca sozinho num momento combinado"),
        ("Harness", "programa onde o agente trabalha"),
        ("Contrato (schema)", "formato combinado do que passa de uma etapa para outra"),
        ("Tríade", "a receita de 7 etapas que produz um app pelos Fluxos 01, 02 e 03"),
        ("Ciclo 4F", "auditoria em quatro fases: Inspetor, Arquiteto, Construtor e Retorno"),
        ("Lente 15-D", "as 15 perguntas do Inspetor"),
    ])
    linhas = defaultdict(list)
    for x in dados["achados"]:
        linhas[x["estado"]].append(x)
    blocos = []
    for estado, titulo in (("aberto", "Em aberto"), ("suspeita", "Sob suspeita"), ("resolvido", "Resolvidos")):
        itens = linhas.get(estado, [])
        if not itens:
            continue
        blocos.append(f"## {titulo} ({len(itens)})\n\n" + tabela(
            ("Achado", "Gravidade · mapa"),
            [(f"{_txt(x['titulo'])} (`{x['id']}`)", f"{GRAVIDADE[x['gravidade']]} · {x['mapa']}") for x in itens]))
    t = dados["totais"]
    estado = (f"# Apêndice B — Estado honesto\n\nTabela consolidada de todos os achados dos mapas, gerada de "
              f"`docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`. Em aberto por gravidade: {t['abertos_alta']} alta, "
              f"{t['abertos_media']} média, {t['abertos_baixa']} baixa. Cada achado em aberto traz no arquivo o texto "
              f"pronto para abrir o fluxo de melhoria (`pedido_melhoria`).\n\n" + "\n".join(blocos))
    return [("90-apendice-glossario.md", f"# Apêndice A — Glossário\n\n{glossario}"), ("91-apendice-estado.md", estado)]


def gerar() -> dict[str, str]:
    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    dados = json.loads(ACHADOS.read_text(encoding="utf-8"))
    titulos = {t: (titulo, para_que) for t, titulo, para_que in mv.MAPAS_PREVISTOS}
    arquivos = {"00-frontmatter.md": frontmatter(cat, dados)}
    for romano, nome, abertura, tipos in PARTES:
        texto = parte(romano, nome, abertura)
        for tipo in tipos:
            n = int(mv.arquivo_mapa(tipo)[5:7])
            titulo, para_que = titulos[tipo]
            texto += capitulo(n, tipo, titulo, para_que, cat, dados["achados"]) + "\n"
        arquivos[f"{10 * (1 + [p[0] for p in PARTES].index(romano)):02d}-parte-{romano.lower()}.md"] = texto
    arquivos.update(dict(apendices(dados)))
    return arquivos


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Gera as partes do livro dos mapas.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    partes = gerar()
    pasta = LIVRO / "partes"
    if args.check:
        velhas = [n for n, t in partes.items() if not (pasta / n).is_file() or (pasta / n).read_text(encoding="utf-8") != t]
        if velhas:
            print(f"[DESATUALIZADO] {', '.join(velhas)}. Rode: python scripts/livro_mapas.py")
            return 1
        print("[OK] Partes do livro em dia.")
        return 0
    manifesto = LIVRO / "livro.json"
    if not manifesto.is_file():
        print(f"[ERRO] {manifesto} não existe. Crie antes com livro.py init {LIVRO}")
        return 1
    pasta.mkdir(parents=True, exist_ok=True)
    for velho in pasta.glob("*.md"):
        if velho.name not in partes:
            velho.unlink()
    for nome, texto in partes.items():
        (pasta / nome).write_text(texto, encoding="utf-8", newline="\n")
    dados = json.loads(manifesto.read_text(encoding="utf-8"))
    dados["partes"] = sorted(partes)
    manifesto.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] {len(partes)} partes gravadas em {pasta}")
    return 0


if __name__ == "__main__":
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")
    sys.exit(main())
