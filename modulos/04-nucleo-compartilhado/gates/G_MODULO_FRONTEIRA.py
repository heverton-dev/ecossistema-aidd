#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_MODULO_FRONTEIRA (ciclo-03 VSA / D13, DoD 4)
=============================================================================
Fronteira entre fatias que morde. Varre por AST cada .py das 7 fatias de
MAPA-FATIAS.json (menos o interface.py da fatia, único ponto cruzado permitido,
e as pastas templates/ de moldes de projeto gerado) e acusa:
  [sys.path] sys.path.insert/append com caminho para dentro de outra fatia;
  [caminho]  caminho literal (string, Path(...), os.path.join, operador /) que
             entra em outra fatia;
  [tools]    referência a tools/aidd-* (pasta extinta no Ticket 5);
  [import]   import de pacote que só existe em outra fatia.
Docstrings e comentários não contam.

Allowlist datada (04-nucleo-compartilhado/contracts/allowlist_modulo_fronteira.json):
cada entrada {arquivo, tipo, alvo, data, motivo} perdoa um acoplamento. Ela só
pode diminuir: mais entradas que o `teto`, teto maior que o do HEAD ou entrada sem
data/motivo → exit 1 em qualquer modo; entrada morta conta como violação.

Níveis (AIDD_MODULO_FRONTEIRA_MODO, precedência: --modo > variável > padrão):
  - aviso    (padrão): imprime o relatório e sai com exit 0;
  - bloqueio          : exit 1 se houver violação.
Saída binária 0/1 (Lei #2).
=============================================================================
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[3]
MODOS = ("aviso", "bloqueio")
CONTRATOS = Path("modulos") / "04-nucleo-compartilhado" / "contracts"
MAPA_FATIAS = CONTRATOS / "MAPA-FATIAS.json"
ALLOWLIST = CONTRATOS / "allowlist_modulo_fronteira.json"
PASTAS_FORA = {"__pycache__", "node_modules", "templates", ".venv", "venv"}
RE_TOOLS = re.compile(r"(^|[/\\])tools[/\\]aidd-")
CAMINHO_PY = (("os", "path", "join"), ("Path",), ("PurePath",), ("pathlib", "Path"))


class ErroConfig(Exception):
    pass


def _nome_pontuado(no: ast.AST) -> tuple:
    partes = []
    while isinstance(no, ast.Attribute):
        partes.append(no.attr)
        no = no.value
    if isinstance(no, ast.Name):
        partes.append(no.id)
        return tuple(reversed(partes))
    return ()


def _textos(no: ast.AST) -> list[str]:
    return [n.value for n in ast.walk(no) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def _segmentos(textos: list[str]) -> list[str]:
    return [s for t in textos for s in re.split(r"[/\\]+", t) if s]


class Fatias:
    def __init__(self, raiz: Path):
        arq = raiz / MAPA_FATIAS
        if not arq.is_file():
            raise ErroConfig(f"{MAPA_FATIAS.as_posix()} não existe em {raiz}")
        mapa = json.loads(arq.read_text(encoding="utf-8"))
        self.dados = mapa["fatias"]
        caixas = set(mapa.get("caixas_de_layout", []))
        self.marcas, self.caminhos, self.pacotes = {}, {}, {}
        for nome, d in self.dados.items():
            self.caminhos[nome] = d["caminho"].strip("/")
            self.marcas[nome] = {Path(d["caminho"]).name} | {Path(f).name for f in d["ferramentas"]}
            pacotes = set()
            for ferramenta in d["ferramentas"]:
                base = raiz / d["caminho"] / ferramenta
                for sub in mapa.get("raizes_import", [""]):
                    pasta = base / sub if sub else base
                    if pasta.is_dir():
                        pacotes.update(p.name for p in pasta.iterdir()
                                       if p.name not in caixas and (p / "__init__.py").is_file())
            self.pacotes[nome] = pacotes
        # Pacote que também existe na raiz do ecossistema (ex.: core/anti_lockin.py)
        # não é atribuível a uma fatia: o import pode estar falando do da raiz.
        da_raiz = {p.name for p in raiz.iterdir() if (p / "__init__.py").is_file()}
        for nome in self.pacotes:
            self.pacotes[nome] -= da_raiz

    def outras(self, dona: str):
        return [f for f in self.dados if f != dona]


def _docstrings(arvore: ast.Module) -> set[int]:
    """ids das constantes que são só texto solto (docstring ou string-comentário)."""
    return {id(n.value) for n in ast.walk(arvore)
            if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)}


def violacoes_do_arquivo(caminho: Path, rel: str, dona: str, fatias: Fatias) -> list[tuple]:
    try:
        arvore = ast.parse(caminho.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return []
    soltas = _docstrings(arvore)
    achados = set()

    def alvo_por_segmentos(segs: list[str]):
        for outra in fatias.outras(dona):
            if fatias.marcas[outra] & set(segs):
                return outra
        return None

    for no in ast.walk(arvore):
        if isinstance(no, ast.Call):
            nome = _nome_pontuado(no.func)
            if nome[-3:] in (("sys", "path", "insert"), ("sys", "path", "append")):
                alvo = alvo_por_segmentos(_segmentos([t for a in no.args for t in _textos(a)]))
                if alvo:
                    achados.add(("sys.path", alvo, no.lineno))
            elif nome in CAMINHO_PY or nome[-1:] in (("Path",),):
                alvo = alvo_por_segmentos(_segmentos([t for a in no.args for t in _textos(a)]))
                if alvo:
                    achados.add(("caminho", alvo, no.lineno))
        elif isinstance(no, ast.BinOp) and isinstance(no.op, ast.Div):
            alvo = alvo_por_segmentos(_segmentos(_textos(no)))
            if alvo:
                achados.add(("caminho", alvo, no.lineno))
        elif isinstance(no, ast.Constant) and isinstance(no.value, str) and id(no) not in soltas:
            texto = no.value.replace("\\", "/")
            if RE_TOOLS.search(texto):
                achados.add(("tools", "tools", no.lineno))
            for outra in fatias.outras(dona):
                if fatias.caminhos[outra] in texto:
                    achados.add(("caminho", outra, no.lineno))
        elif isinstance(no, (ast.Import, ast.ImportFrom)):
            nomes = [a.name for a in no.names] if isinstance(no, ast.Import) else (
                [no.module] if no.module and no.level == 0 else [])
            for mod in nomes:
                topo = mod.split(".")[0]
                if topo == "tools":
                    achados.add(("tools", "tools", no.lineno))
                    continue
                if topo in fatias.pacotes[dona]:
                    continue
                for outra in fatias.outras(dona):
                    if topo in fatias.pacotes[outra]:
                        achados.add(("import", outra, no.lineno))
    # Um achado por (arquivo, tipo, alvo); guarda a primeira linha.
    primeiro = {}
    for tipo, alvo, linha in sorted(achados, key=lambda a: a[2]):
        primeiro.setdefault((tipo, alvo), linha)
    return [(rel, tipo, alvo, linha) for (tipo, alvo), linha in primeiro.items()]


def varrer(raiz: Path, fatias: Fatias) -> list[tuple]:
    resultado = []
    for dona, caminho_fatia in fatias.caminhos.items():
        base = raiz / caminho_fatia
        for pasta, subpastas, arquivos in os.walk(base):
            subpastas[:] = [s for s in subpastas if s not in PASTAS_FORA and not s.startswith(".")]
            for arq in arquivos:
                if not arq.endswith(".py"):
                    continue
                completo = Path(pasta) / arq
                if completo.parent == base and arq == "interface.py":
                    continue
                rel = completo.relative_to(raiz).as_posix()
                resultado.extend(violacoes_do_arquivo(completo, rel, dona, fatias))
    return sorted(resultado)


def _teto_no_head(raiz: Path) -> int | None:
    proc = subprocess.run(["git", "show", f"HEAD:{ALLOWLIST.as_posix()}"], cwd=str(raiz),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        return None
    try:
        return int(json.loads(proc.stdout).get("teto"))
    except (ValueError, TypeError):
        return None


def carregar_allowlist(raiz: Path) -> list[dict]:
    arq = raiz / ALLOWLIST
    if not arq.is_file():
        raise ErroConfig(f"{ALLOWLIST.as_posix()} não existe")
    dados = json.loads(arq.read_text(encoding="utf-8"))
    entradas, teto = dados.get("entradas", []), dados.get("teto")
    if not isinstance(teto, int):
        raise ErroConfig("allowlist sem 'teto' inteiro")
    if len(entradas) > teto:
        raise ErroConfig(f"allowlist cresceu: {len(entradas)} entradas acima do teto {teto} (só pode diminuir)")
    teto_head = _teto_no_head(raiz)
    if teto_head is not None and teto > teto_head:
        raise ErroConfig(f"teto subiu de {teto_head} para {teto} (allowlist só pode diminuir)")
    for e in entradas:
        if not all(e.get(c) for c in ("arquivo", "tipo", "alvo", "data", "motivo")):
            raise ErroConfig(f"entrada sem arquivo/tipo/alvo/data/motivo: {e}")
    return entradas


def _modo(cli: str | None) -> str:
    bruto = (cli or os.environ.get("AIDD_MODULO_FRONTEIRA_MODO", "") or "aviso").strip().lower()
    if bruto not in MODOS:
        raise ErroConfig(f"AIDD_MODULO_FRONTEIRA_MODO inválido: {bruto!r} (use aviso|bloqueio)")
    return bruto


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="G_MODULO_FRONTEIRA — fronteira entre fatias que morde")
    parser.add_argument("--raiz", default=str(RAIZ))
    parser.add_argument("--modo", choices=MODOS, default=None)
    parser.add_argument("--semear", action="store_true",
                        help="grava a allowlist com os acoplamentos atuais (data de hoje); só para a semeadura inicial")
    args = parser.parse_args(argv)
    raiz = Path(args.raiz)

    try:
        modo = _modo(args.modo)
        fatias = Fatias(raiz)
        achados = varrer(raiz, fatias)
        if args.semear:
            return _semear(raiz, achados)
        entradas = carregar_allowlist(raiz)
    except (ErroConfig, OSError, ValueError, KeyError) as erro:
        print(f"[G_MODULO_FRONTEIRA] ERRO: {erro}")
        return 1

    perdoados = {(e["arquivo"], e["tipo"], e["alvo"]) for e in entradas}
    novos = [a for a in achados if a[:3] not in perdoados]
    vivos = {a[:3] for a in achados}
    mortas = sorted(p for p in perdoados if p not in vivos)

    print(f"[G_MODULO_FRONTEIRA] modo {modo}: {len(novos)} acoplamento(s) novo(s), "
          f"{len(achados) - len(novos)} perdoado(s) pela allowlist, {len(mortas)} entrada(s) morta(s).")
    for rel, tipo, alvo, linha in novos:
        print(f"  - [{tipo}] {rel}:{linha} -> {alvo}")
    for rel, tipo, alvo in mortas:
        print(f"  - [allowlist morta] {rel} [{tipo}] -> {alvo}: remova a entrada e baixe o teto")
    if (novos or mortas) and modo == "bloqueio":
        print("[G_MODULO_FRONTEIRA] REPROVADO: fatia só fala com outra pelo interface.py.")
        return 1
    return 0


def _semear(raiz: Path, achados: list[tuple]) -> int:
    from datetime import date
    hoje = date.today().isoformat()
    entradas = [{"arquivo": rel, "tipo": tipo, "alvo": alvo, "data": hoje,
                 "motivo": "acoplamento existente na semeadura do Ticket 11 (ciclo-03); migrar para interface.py"}
                for rel, tipo, alvo, _ in achados]
    arq = raiz / ALLOWLIST
    arq.parent.mkdir(parents=True, exist_ok=True)
    dados = {"descricao": "Acoplamentos entre fatias perdoados com data. So pode diminuir (G_MODULO_FRONTEIRA).",
             "teto": len(entradas), "entradas": entradas}
    with open(arq, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(dados, indent=2, ensure_ascii=False) + "\n")
    print(f"[G_MODULO_FRONTEIRA] allowlist semeada com {len(entradas)} entrada(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
