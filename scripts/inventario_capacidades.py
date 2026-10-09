#!/usr/bin/env python3
"""Inventário de capacidades de modulos/ e componentes/ (fronteiras-ferramentas ciclo-01, Ticket 3).

foto      grava a foto do "antes" no ciclo, em dois arquivos:
            INVENTARIO-ANTES.json            funções, classes e testes de cada arquivo, por família
                                             de cópias (só nomes: legível e sem nada que o
                                             detect-secrets confunda com credencial).
            INVENTARIO-ANTES.linhas.json.gz  sha256 e linhas únicas de cada arquivo (hashes e linhas
                                             de teste com chave falsa reprovavam o G_SEGREDOS).
comparar  lista o que existia na foto e não existe mais em lugar nenhum; exit 1 se houver órfão.
          Mover ou renomear arquivo não gera órfão. Os nomes antigos da tabela de apelidos
          (NOMES-ANTIGOS.json, Ticket 4) são traduzidos antes de comparar; linhas comparam sem
          caixa (o nome antigo em maiúsculas é o mesmo nome) e .md fica só no nível de arquivo, porque
          a prosa é reescrita junto com o nome (195 linhas "órfãs" na Fase 4, nenhuma capacidade).
          Pasta que saiu inteira do repositório (arquivada ou lixo apagado) entra no --aceitos
          como pastas_removidas [{prefixo, motivo}]: os órfãos da foto sob o prefixo contam como
          aceitos, mas a pasta não pode existir mais em layout nenhum (ciclo-03 VSA, DoD 1).

Só entram arquivos rastreados pelo git: espelhos de harness e lixo local ficam de fora.
"""
import argparse
import ast
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ESCOPO = ("modulos", "componentes")  # tools/ saiu no ciclo-03 VSA (decisão A)
TABELA_APELIDOS = "componentes/compartilhado/specs/NOMES-ANTIGOS.json"
NOME_FOTO = "INVENTARIO-ANTES.json"
SUFIXO_LINHAS = ".linhas.json.gz"
MAX_LISTADOS = 50
TIPOS = {"funcoes": "função", "classes": "classe", "testes": "teste"}
SEM_COMPARAR_LINHAS = (".md",)


def arquivos_rastreados(raiz):
    saida = subprocess.run(["git", "ls-files", "-z", "--", *ESCOPO], cwd=raiz,
                           capture_output=True, check=True).stdout.decode("utf-8")
    return sorted(p for p in saida.split("\0") if p and (raiz / p).is_file())


def _capacidades(texto):
    try:
        arvore = ast.parse(texto)
    except (SyntaxError, ValueError):
        return [], [], []
    funcoes, classes = [], []
    for no in ast.walk(arvore):
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcoes.append(no.name)
        elif isinstance(no, ast.ClassDef):
            classes.append(no.name)
    testes = [f for f in funcoes if f.startswith("test_")]
    return sorted(set(funcoes)), sorted(set(classes)), sorted(set(testes))


def _linhas_unicas(texto):
    return sorted({linha.strip() for linha in texto.splitlines() if linha.strip()})


def levantar(raiz):
    """Devolve (indice, linhas): nomes por arquivo e sha256 + linhas únicas por arquivo."""
    indice, linhas = {}, {}
    for rel in arquivos_rastreados(raiz):
        bruto = (raiz / rel).read_bytes()
        try:
            texto = bruto.decode("utf-8")
        except UnicodeDecodeError:
            continue  # binário: sem capacidade nem linha para comparar
        funcoes, classes, testes = _capacidades(texto) if rel.endswith(".py") else ([], [], [])
        indice[rel] = {"familia": Path(rel).name, "funcoes": funcoes, "classes": classes, "testes": testes}
        linhas[rel] = {"sha256": hashlib.sha256(bruto).hexdigest(), "linhas_unicas": _linhas_unicas(texto)}
    return indice, linhas


def caminho_linhas(foto_json):
    return foto_json.with_name(foto_json.stem + SUFIXO_LINHAS)


def foto(raiz, ciclo):
    pasta = raiz / ciclo
    pasta.mkdir(parents=True, exist_ok=True)
    indice, linhas = levantar(raiz)
    destino = pasta / NOME_FOTO
    destino.write_text(json.dumps(indice, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                       encoding="utf-8", newline="\n")
    # mtime=0: a mesma árvore gera sempre os mesmos bytes.
    with gzip.GzipFile(caminho_linhas(destino), "wb", mtime=0) as gz:
        gz.write(json.dumps(linhas, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    print(f"[OK] foto: {len(indice)} arquivo(s) de {', '.join(ESCOPO)} em {destino.relative_to(raiz).as_posix()}")
    return 0


def carregar_apelidos(caminho):
    """Trocas antigo -> novo da tabela de apelidos. Comando de CLI só troca depois de
    'ecossistema.py ': 'generate' e 'bridge' são palavras comuns no resto do texto."""
    if not caminho or not caminho.is_file():
        return {}
    tabela = json.loads(caminho.read_text(encoding="utf-8"))
    comandos = {f"ecossistema.py {antigo}": f"ecossistema.py {novo}"
                for antigo, novo in tabela.get("comandos_cli", {}).items()}
    return {**tabela.get("ferramentas", {}), **tabela.get("pacotes_python", {}),
            **tabela.get("funcoes_renomeadas", {}), **comandos}


def _traduzir(texto, trocas):
    for antigo in sorted(trocas, key=len, reverse=True):  # o nome mais longo primeiro
        texto = texto.replace(antigo, trocas[antigo])
    return texto


def carregar_aceitos(caminho):
    """{(arquivo, item): motivo} de órfãos aceitos; item = "<rótulo> <nome>" ou "linha: <texto>".
    Entrada sem motivo não vale (Lei #7: toda perda aceita tem de dizer por quê)."""
    if caminho is None:
        return {}
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    return {(a["arquivo"], a["item"]): a["motivo"] for a in dados.get("aceitos", []) if a.get("motivo", "").strip()}


def carregar_pastas_removidas(caminho):
    """{prefixo/: motivo} de pastas que saíram inteiras do repositório; sem motivo não vale (Lei #7)."""
    if caminho is None:
        return {}
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    return {p["prefixo"].rstrip("/") + "/": p["motivo"] for p in dados.get("pastas_removidas", [])
            if p.get("motivo", "").strip()}


def _pasta_ainda_existe(prefixo, arquivos):
    """A foto guarda o caminho do layout de antes da VSA: a pasta segue viva se o caminho depois da
    primeira pasta aparece em algum arquivo rastreado de agora, em qualquer layout."""
    cauda = "/" + prefixo.split("/", 1)[1]
    return any(cauda in "/" + rel for rel in arquivos)


def comparar(raiz, foto_json, apelidos, aceitos=None, pastas_removidas=None):
    if not foto_json.is_file() or not caminho_linhas(foto_json).is_file():
        print(f"[-] FALHA: foto incompleta: {foto_json} e {caminho_linhas(foto_json).name} são obrigatórios.")
        return 1
    pastas = pastas_removidas or {}
    presentes = arquivos_rastreados(raiz) if pastas else []
    vivas = sorted(p for p in pastas if _pasta_ainda_existe(p, presentes))
    if vivas:
        print(f"[-] FALHA: pasta aceita como removida ainda existe no repositório: {', '.join(vivas)}")
        return 1
    antes = json.loads(foto_json.read_text(encoding="utf-8"))
    with gzip.open(caminho_linhas(foto_json), "rb") as gz:
        linhas_antes = json.loads(gz.read().decode("utf-8"))
    trocas = carregar_apelidos(apelidos)
    trocas_sem_caixa = {antigo.lower(): novo.lower() for antigo, novo in trocas.items()}
    indice, linhas = levantar(raiz)

    capacidades_agora = {(tipo, nome) for meta in indice.values()
                         for tipo in TIPOS for nome in meta[tipo]}
    linhas_agora = {linha.lower() for meta in linhas.values() for linha in meta["linhas_unicas"]}

    aceitos = aceitos or {}
    removidas = tuple(pastas)
    orfas, ja_aceitos, de_pastas = [], 0, 0
    for rel, meta in sorted(antes.items()):
        for tipo, rotulo in TIPOS.items():
            for nome in meta[tipo]:
                if (tipo, _traduzir(nome, trocas)) not in capacidades_agora:
                    if (rel, f"{rotulo} {nome}") in aceitos:
                        ja_aceitos += 1
                    elif rel.startswith(removidas):
                        de_pastas += 1
                    else:
                        orfas.append(f"{rel}: {rotulo} {nome}")
    for rel, meta in sorted(linhas_antes.items()):
        if rel.endswith(SEM_COMPARAR_LINHAS):
            continue
        for linha in meta["linhas_unicas"]:
            if _traduzir(linha.lower(), trocas_sem_caixa) not in linhas_agora:
                if (rel, f"linha: {linha}") in aceitos:
                    ja_aceitos += 1
                elif rel.startswith(removidas):
                    de_pastas += 1
                else:
                    orfas.append(f"{rel}: linha {linha[:120]!r}")

    if not orfas:
        print(f"[OK] comparar: zero órfão fora da lista ({ja_aceitos} aceito(s) com motivo; "
              f"{de_pastas} item(ns) de {len(pastas)} pasta(s) removida(s); "
              f"{len(antes)} arquivo(s) na foto, {len(indice)} agora).")
        return 0
    print(f"[-] FALHA: {len(orfas)} órfão(s): existiam na foto e não existem mais em lugar nenhum.")
    for item in orfas[:MAX_LISTADOS]:
        print(f"    {item}")
    if len(orfas) > MAX_LISTADOS:
        print(f"    ... e mais {len(orfas) - MAX_LISTADOS}.")
    return 1


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("foto", help="grava INVENTARIO-ANTES.json no ciclo")
    f.add_argument("--repo", default=".", help="raiz do repositório (padrão: .)")
    f.add_argument("--cycle", required=True, help="pasta do ciclo, relativa ao repositório")
    c = sub.add_parser("comparar", help="exit 1 se algo da foto não existe mais em lugar nenhum")
    c.add_argument("foto", help="caminho do INVENTARIO-ANTES.json")
    c.add_argument("--repo", default=".", help="raiz do repositório (padrão: .)")
    c.add_argument("--aceitos", default=None,
                   help="JSON {aceitos: [{arquivo, item, motivo}], pastas_removidas: [{prefixo, motivo}]} "
                        "de órfãos aceitos com motivo")
    c.add_argument("--apelidos", default=None,
                   help=f"tabela de nomes antigos (padrão: {TABELA_APELIDOS}, se existir)")
    args = p.parse_args(argv)

    raiz = Path(args.repo).resolve()
    if args.cmd == "foto":
        return foto(raiz, args.cycle)
    foto_json = Path(args.foto) if Path(args.foto).is_absolute() else raiz / args.foto
    apelidos = Path(args.apelidos) if args.apelidos else raiz / TABELA_APELIDOS
    aceitos_json = None
    if args.aceitos:
        aceitos_json = Path(args.aceitos) if Path(args.aceitos).is_absolute() else raiz / args.aceitos
    return comparar(raiz, foto_json, apelidos, carregar_aceitos(aceitos_json), carregar_pastas_removidas(aceitos_json))


if __name__ == "__main__":
    sys.exit(main())
