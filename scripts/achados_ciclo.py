#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json: todos os erros e itens em
aberto encontrados pelos mapas, num formato só, base do fluxo /melhoria e dos
tickets de correção.

Duas fontes, sem nada escrito à mão no arquivo final:
  - medidos: lidos do catálogo (docs/auditoria/mapa-pecas/catalogo-pecas.json);
  - verificados: docs/auditoria/mapa-pecas/ciclo-01/achados-verificados.json,
    cada um com evidência de reprodução ou de leitura do código.

Uso:
  python scripts/achados_ciclo.py [--saida ARQ] [--check]
Exit 0: gravado (ou em dia, no --check). Exit 1: erro ou --check divergente.
"""
import argparse
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
from scripts.catalogo_pecas import DONAS_MOLDES
CICLO = RAIZ / "docs" / "auditoria" / "mapa-pecas" / "ciclo-01"
CATALOGO = RAIZ / "docs" / "auditoria" / "mapa-pecas" / "catalogo-pecas.json"
VERIFICADOS = CICLO / "achados-verificados.json"
SAIDA_PADRAO = CICLO / "ACHADOS.json"
GRAVIDADES = ("alta", "media", "baixa")
ESTADOS = ("aberto", "suspeita", "resolvido")
CAMPOS = ("id", "titulo", "gravidade", "estado", "origem", "mapa", "evidencia", "pedido_melhoria")


def _slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")[:60]


def _item(chave, titulo, gravidade, mapa, evidencia, pedido):
    return {"id": f"CAT-{_slug(chave)}", "titulo": titulo, "gravidade": gravidade, "estado": "aberto",
            "origem": "catalogo", "mapa": mapa, "evidencia": evidencia, "pedido_melhoria": pedido}


def medidos(cat: dict) -> list[dict]:
    """Um achado por defeito que o catálogo mede; as listas longas viram um achado só."""
    a = cat["achados"]
    itens = []
    for enc in cat.get("encaixes") or []:
        if not enc["encaixa"]:
            itens.append(_item(f'encaixe {enc["chamada"]}', f'Chamada da receita não encaixa: {enc["chamada"]}',
                               "alta", "encaixes", [f'{enc["etapa"]}: {p}' for p in enc["problemas"]],
                               f'Corrigir a chamada "{enc["chamada"]}" da {enc["etapa"]} do orquestrador síncrono '
                               f'para os parâmetros que a ferramenta aceita.'))
    for etapa in a.get("etapas_sem_ferramenta", []):
        itens.append(_item(f"etapa sem ferramenta {etapa}", f"Etapa da receita não chama ferramenta: {etapa}",
                           "alta", "encaixes", [f"catálogo: {etapa} com chama_alguma_ferramenta=false"],
                           f"Ligar a {etapa} do orquestrador síncrono à ferramenta que faz esse trabalho."))
    for etapa, caminhos in sorted(a.get("etapas_com_atalho_interno", {}).items()):
        itens.append(_item(f"atalho interno {etapa}", f"Etapa mexe por dentro de uma ferramenta: {etapa}",
                           "media", "encaixes", [f"{etapa}: {c}" for c in caminhos],
                           f"Fazer a {etapa} usar a CLI da ferramenta em vez de importar arquivos internos."))
    leis = cat.get("leis") or []
    gates = {g["id"]: g for g in cat["gates"]}
    invisiveis = [f'Lei #{lei["numero"]}: {p["gate"]}' for lei in leis for p in lei["portoes"] if not p["visivel"]]
    if invisiveis:
        itens.append(_item("declaracoes invisiveis", f"{len(invisiveis)} declarações de lei que o meta-guarda não lê",
                           "media", "leis", invisiveis,
                           "Fazer o G_LEI_DECLARA_PORTAO ler declarações com comentário depois do '(provado)', ou tirar os comentários do AGENTS.md."))
    fora = [f'Lei #{lei["numero"]}: {p["gate"]}' for lei in leis for p in lei["portoes"]
            if p["gate"] in gates and not gates[p["gate"]]["no_pre_commit"]]
    if fora:
        itens.append(_item("declarados fora do commit", f"{len(fora)} guardas declarados em lei que não rodam no commit",
                           "media", "leis", fora, "Colocar no pre-commit os guardas declarados nas leis, ou rebaixar a declaração."))
    declarados = {p["gate"] for lei in leis for p in lei["portoes"]}
    sem_lei = sorted(g["id"] for g in cat["gates"] if g["prova_que_morde"] is not None and g["id"] not in declarados)
    if sem_lei:
        itens.append(_item("guardas sem lei", f"{len(sem_lei)} guardas da raiz que nenhuma lei declara",
                           "baixa", "leis", sem_lei, "Amarrar cada guarda da raiz à lei que ele prova no AGENTS.md."))
    if a.get("gates_mesmo_nome_codigo_diferente"):
        itens.append(_item("gates versoes", f'{len(a["gates_mesmo_nome_codigo_diferente"])} guardas com o mesmo nome e código diferente',
                           "media", "guardas", a["gates_mesmo_nome_codigo_diferente"],
                           "Deixar uma versão só de cada guarda repetido e fazer as ferramentas chamarem a original."))
    if a.get("tarefas_com_varias_donas"):
        itens.append(_item("tarefas varias donas", f'{len(a["tarefas_com_varias_donas"])} tarefas feitas por mais de uma ferramenta',
                           "media", "ferramentas",
                           [f'{t}: {", ".join(d["donas"])}' for t, d in sorted(a["tarefas_com_varias_donas"].items())],
                           "Definir uma dona única para cada tarefa repetida e fazer as outras chamarem a dona."))
    identicos = a.get("arquivos_identicos_entre_donas") or []
    if identicos:
        itens.append(_item("arquivos identicos", f'{sum(x["arquivos"] for x in identicos)} arquivos idênticos copiados entre ferramentas',
                           "alta", "ferramentas", [f'{x["donas"]}: {x["arquivos"]}' for x in identicos],
                           "Separar aidd-master (esqueleto) de aidd-enterprise (blindagem) e tirar as cópias idênticas."))
    if a.get("verbos_cli_repetidos"):
        itens.append(_item("verbos repetidos", f'{len(a["verbos_cli_repetidos"])} verbos de CLI em mais de uma ferramenta',
                           "baixa", "ferramentas",
                           [f'{v}: {", ".join(fs)}' for v, fs in sorted(a["verbos_cli_repetidos"].items())],
                           "Revisar os verbos de CLI repetidos e manter cada comando numa ferramenta só."))
    soltos = [s["id"] for s in cat.get("scripts", []) if not s["chamado_por"]]
    if soltos:
        itens.append(_item("scripts sem chamador", f"{len(soltos)} scripts que nenhum código chama", "baixa", "scripts",
                           soltos, "Ligar ao painel ou remover os scripts de scripts/ que nenhum código chama."))
    for leg in (cat.get("harnesses") or {}).get("pastas_legadas", []):
        itens.append(_item(f'pasta legada {leg["pasta"]}', f'Pasta legada ainda versionada: {leg["pasta"]}', "media",
                           "harnesses", [f'{leg["arquivos_versionados"]} arquivos versionados'],
                           f'Remover a pasta legada {leg["pasta"]} do repositório e do auto-ingest do components sync.'))
    nomes = {}
    for m in cat.get("moldes_entrega", []):
        if m.get("molde") in DONAS_MOLDES or m.get("dona_canonica") in DONAS_MOLDES.values():
            continue
        nomes.setdefault(m["molde"], set()).add(m["ferramenta"])
    repetidos = [f'{n}: {", ".join(sorted(fs))}' for n, fs in sorted(nomes.items()) if len(fs) > 1]
    if repetidos:
        itens.append(_item("moldes repetidos", f"{len(repetidos)} moldes de entrega com o mesmo nome em várias ferramentas",
                           "media", "moldes", repetidos, "Deixar cada molde de entrega numa ferramenta dona e gerar as cópias."))
    for c in (cat.get("oficina") or {}).get("ciclos", []):
        faltam = [k for k, v in c["fases"].items() if not v]
        if faltam:
            itens.append(_item(f'ciclo {c["alvo"]} {c["ciclo"]}', f'Ciclo de auditoria sem todos os documentos: {c["alvo"]}/{c["ciclo"]}',
                               "baixa", "oficina", [f"faltam: {', '.join(faltam)}"],
                               f'Completar ou fechar o ciclo {c["alvo"]}/{c["ciclo"]}.'))
    laudos_vigentes = {}
    for laudo in (cat.get("lente_15d") or {}).get("laudos", []):
        laudos_vigentes[laudo["alvo"]] = laudo  # Ultimo ciclo prevalece
    for laudo in laudos_vigentes.values():
        falhas = sorted((k for k, v in laudo["dimensoes"].items() if v == "falha"), key=int)
        if falhas:
            itens.append(_item(f'15d {laudo["alvo"]}', f'{len(falhas)} dimensões 15-D com falha no laudo de {laudo["alvo"]}',
                               "media", "lente15d", [f'{laudo["laudo"]}: D{", D".join(falhas)}'],
                               f'Abrir o próximo ciclo 4F de {laudo["alvo"]} para as dimensões D{", D".join(falhas)}.'))
    soltos_mcp = [m["id"] for m in (cat.get("mcps") or {}).get("internos_das_ferramentas", []) if not m["registrado_em_config"]]
    if soltos_mcp:
        itens.append(_item("mcps internos", f"{len(soltos_mcp)} MCPs das ferramentas que nenhum agente deste repositório usa",
                           "baixa", "conexoes", soltos_mcp,
                           "Decidir se os MCPs internos das ferramentas devem ser registrados para o agente ou só ir com o app gerado."))
    return itens


def gerar() -> dict:
    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    verificados = json.loads(VERIFICADOS.read_text(encoding="utf-8"))["achados"]
    for v in verificados:
        v.setdefault("origem", "reproducao")
    itens = medidos(cat) + verificados
    ids = [i["id"] for i in itens]
    duplicados = sorted({i for i in ids if ids.count(i) > 1})
    if duplicados:
        raise ValueError(f"ids repetidos: {duplicados}")
    for i in itens:
        faltam = [c for c in CAMPOS if c not in i]
        if faltam or i["gravidade"] not in GRAVIDADES or i["estado"] not in ESTADOS or not i["evidencia"]:
            raise ValueError(f'achado {i.get("id")} fora do formato (faltam {faltam})')
        if i["estado"] != "resolvido" and not i["pedido_melhoria"]:
            raise ValueError(f'achado {i["id"]} em aberto sem pedido_melhoria')
    itens.sort(key=lambda i: (ESTADOS.index(i["estado"]), GRAVIDADES.index(i["gravidade"]), i["id"]))
    totais = {e: sum(1 for i in itens if i["estado"] == e) for e in ESTADOS}
    totais.update({f"abertos_{g}": sum(1 for i in itens if i["estado"] != "resolvido" and i["gravidade"] == g)
                   for g in GRAVIDADES})
    return {"versao": 1, "gerado_por": "scripts/achados_ciclo.py",
            "fontes": ["docs/auditoria/mapa-pecas/catalogo-pecas.json",
                       "docs/auditoria/mapa-pecas/ciclo-01/achados-verificados.json"],
            "como_usar": "Cada achado em aberto traz pedido_melhoria: o texto para python ecossistema.py melhoria init --pedido \"...\".",
            "totais": totais, "achados": itens}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Gera o ACHADOS.json do ciclo-01 do mapa de peças.")
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        texto = json.dumps(gerar(), ensure_ascii=False, indent=2) + "\n"
    except (ValueError, KeyError, FileNotFoundError) as erro:
        print(f"[ERRO] {erro}")
        return 1
    if args.check:
        if not args.saida.is_file() or args.saida.read_text(encoding="utf-8") != texto:
            print(f"[DESATUALIZADO] {args.saida}. Rode: python scripts/achados_ciclo.py")
            return 1
        print(f"[OK] {args.saida} em dia.")
        return 0
    args.saida.write_text(texto, encoding="utf-8", newline="\n")
    print(f"[OK] Achados gravados em {args.saida}")
    return 0


if __name__ == "__main__":
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")
    sys.exit(main())
