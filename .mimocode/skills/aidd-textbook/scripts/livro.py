# -*- coding: utf-8 -*-
"""
=============================================================================
aidd-livro-texto — MOTOR DETERMINISTICO DE LIVRO-TEXTO CORPORATIVO
=============================================================================
CLI autocontida (Python puro + stdlib) que cria, compila, audita e atualiza
livros-texto em PDF via pandoc + typst.

Zero token de LLM: todo trabalho aqui e mecanico (I/O, concatenacao, regex,
subprocess). O agente escreve APENAS o conteudo das partes em Markdown; este
script faz o resto e devolve exit code real (0 = ok, 1 = falha).

Subcomandos:
  doctor                      Verifica pandoc, typst e fontes do template.
  init <pasta>                Cria o esqueleto de uma obra nova (partes + manifesto).
  build [<pasta>]             Concatena as partes e compila o PDF.
  check [<pasta>]             Auditoria deterministica do fonte (nao compila).
  preview [<pasta>]           Renderiza paginas em PNG para inspecao visual.
  status [<pasta>]            Estado da obra: partes, palavras, hash, PDF atualizado?
  update [<pasta>]            Reconstroi apenas se o fonte mudou; registra a revisao.
  add-parte [<pasta>] --nome  Cria uma parte nova ja registrada no manifesto.

Agnostico a harness e a sistema operacional: nao importa nada fora da stdlib,
nao assume shell POSIX e nao depende de nenhum repositorio especifico.
=============================================================================
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

DIR_SKILL = Path(__file__).resolve().parent.parent
TEMPLATE_PADRAO = DIR_SKILL / "ativos" / "livro.typst"
NOME_MANIFESTO = "livro.json"
NOME_PARTES = "partes"

LARGURA_CORPO_CHARS = 175   # largura util aproximada do corpo A4 em caracteres
VERSAO_TYPST_MINIMA = (0, 11, 0)   # o template usa `context`, introduzido no typst 0.11
COLUNAS_PANDOC = 72         # abaixo disso o writer typst nao emite larguras relativas

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Utilitarios
# ---------------------------------------------------------------------------

def _imprimir(msg: str, destino) -> None:
    """Escreve sem morrer quando o outro lado fecha o cano.

    `livro.py doctor | head -3` fecha o pipe antes do fim; no Windows isso chega como
    OSError errno 22 (e nao BrokenPipeError). Uma ferramenta de linha de comando nao
    deve explodir com traceback so porque alguem filtrou a saida dela.
    """
    try:
        print(msg, file=destino, flush=True)
    except (BrokenPipeError, OSError):
        pass


def _log(msg: str) -> None:
    _imprimir(msg, sys.stdout)


def _erro(msg: str) -> None:
    _imprimir(f"[ERRO] {msg}", sys.stderr)


def _sha256_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _escrever_atomico(caminho: Path, conteudo: str) -> None:
    """Grava em arquivo temporario, faz fsync e troca — nunca deixa arquivo pela metade."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    with open(temporario, "w", encoding="utf-8", newline="\n") as f:
        f.write(conteudo)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporario, caminho)


def _resolver_pasta(valor: str | None) -> Path:
    return Path(valor).resolve() if valor else Path.cwd().resolve()


def _carregar_manifesto(pasta: Path) -> dict:
    caminho = pasta / NOME_MANIFESTO
    if not caminho.is_file():
        raise FileNotFoundError(
            f"manifesto ausente: {caminho}. Rode 'livro.py init <pasta>' antes."
        )
    return json.loads(caminho.read_text(encoding="utf-8"))


def _salvar_manifesto(pasta: Path, manifesto: dict) -> None:
    _escrever_atomico(pasta / NOME_MANIFESTO, json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n")


def _template(manifesto: dict, pasta: Path) -> Path:
    declarado = manifesto.get("template")
    if declarado:
        caminho = (pasta / declarado).resolve() if not Path(declarado).is_absolute() else Path(declarado)
        if caminho.is_file():
            return caminho
    return TEMPLATE_PADRAO


def _achar_pandoc() -> str | None:
    """Caminho do pandoc: primeiro o do sistema, depois o embutido em pypandoc-binary."""
    do_sistema = shutil.which("pandoc")
    if do_sistema:
        return do_sistema
    try:
        import pypandoc  # dependencia opcional: so existe se instalada via pip
    except ImportError:
        return None
    embutido = Path(pypandoc.__file__).parent / "files" / ("pandoc.exe" if os.name == "nt" else "pandoc")
    if embutido.is_file():
        return str(embutido)
    try:
        return pypandoc.get_pandoc_path()
    except Exception:
        return None


def _typst_cli_usavel() -> tuple[str | None, str]:
    """Caminho do typst do PATH — so se ele servir de fato. Retorna (caminho, motivo).

    Tres armadilhas reais, todas ja observadas em maquina de trabalho:
      1. `shutil.which` acha o nome mas o programa nao executa;
      2. acha um atalho .CMD/.BAT (instalacao via npm, shim de gerenciador de versao)
         que o pandoc nao consegue invocar como motor de PDF;
      3. acha uma versao antiga demais para o template (que usa `context`, de 0.11+).
    Achar o nome no PATH nao prova nenhuma das tres — por isso aqui ele e exercitado.
    """
    caminho = shutil.which("typst")
    if caminho is None:
        return None, "ausente no PATH"

    if os.name == "nt" and not caminho.lower().endswith(".exe"):
        return None, f"{caminho} nao e executavel nativo (.exe) — o pandoc nao o invoca"

    try:
        res = subprocess.run([caminho, "--version"], capture_output=True, text=True, timeout=20)
    except Exception as exc:
        return None, f"{caminho} nao executou ({exc.__class__.__name__})"
    if res.returncode != 0 or not res.stdout.strip():
        return None, f"{caminho} respondeu com erro a --version"

    achado = re.search(r"(\d+)\.(\d+)\.(\d+)", res.stdout)
    if not achado:
        return None, f"{caminho} nao reportou versao reconhecivel"
    versao = tuple(int(g) for g in achado.groups())
    if versao < VERSAO_TYPST_MINIMA:
        legivel = ".".join(str(v) for v in versao)
        minima = ".".join(str(v) for v in VERSAO_TYPST_MINIMA)
        return None, f"{caminho} e typst {legivel}, abaixo do minimo {minima} exigido pelo template"

    return caminho, ".".join(str(v) for v in versao)


def _resolver_motor() -> dict:
    """Descobre como compilar nesta maquina.

    Duas vias, nesta ordem de preferencia:
      1. binarios no PATH  -> pandoc chama o typst direto (--pdf-engine=typst).
      2. pacotes pip       -> pandoc gera .typ e a API do pacote 'typst' gera o PDF.
         O pacote pip 'typst' NAO instala executavel, so a funcao Python — por isso
         --pdf-engine=typst nao serve nesta via.
    """
    typst_cli, motivo_cli = _typst_cli_usavel()
    typst_api = False
    if typst_cli is None:
        try:
            import typst  # noqa: F401
            typst_api = True
        except ImportError:
            pass
    return {"pandoc": _achar_pandoc(), "typst_cli": typst_cli,
            "typst_api": typst_api, "motivo_cli": motivo_cli}


def _compilar_pdf(markdown: Path, template: Path, pdf: Path, motor: dict) -> tuple[int, str]:
    """Gera o PDF pela via disponivel. Retorna (exit code, mensagem de erro)."""
    base = _pandoc_base(markdown, template, motor["pandoc"])

    if motor["typst_cli"]:
        res = subprocess.run(base + ["--pdf-engine", "typst", "-o", str(pdf)],
                             capture_output=True, text=True)
        return res.returncode, res.stderr

    if motor["typst_api"]:
        import typst
        typ = pdf.with_suffix(".typ")
        res = subprocess.run(base + ["-t", "typst", "-s", "-o", str(typ)],
                             capture_output=True, text=True)
        if res.returncode != 0:
            return res.returncode, res.stderr
        try:
            typst.compile(str(typ), output=str(pdf))
        except Exception as exc:
            return 1, f"typst (via pacote Python) falhou: {exc}"
        finally:
            typ.unlink(missing_ok=True)
        return 0, ""

    return 1, "typst indisponivel (nem no PATH nem como pacote Python) — rode 'livro.py doctor'"


def _partes_ordenadas(pasta: Path, manifesto: dict) -> list[Path]:
    dir_partes = pasta / manifesto.get("pasta_partes", NOME_PARTES)
    nomes = manifesto.get("partes") or sorted(p.name for p in dir_partes.glob("*.md"))
    caminhos = []
    for nome in nomes:
        caminho = dir_partes / nome
        if not caminho.is_file():
            raise FileNotFoundError(f"parte declarada no manifesto e ausente em disco: {caminho}")
        caminhos.append(caminho)
    return caminhos


# ---------------------------------------------------------------------------
# doctor — pre-voo do ambiente
# ---------------------------------------------------------------------------

def cmd_doctor(_args: argparse.Namespace) -> int:
    motor = _resolver_motor()
    falhou = False

    if motor["pandoc"]:
        try:
            versao = subprocess.run([motor["pandoc"], "--version"], capture_output=True,
                                    text=True, timeout=20).stdout.splitlines()[0]
        except Exception:
            versao = "(versao nao reportada)"
        origem = "PATH" if shutil.which("pandoc") else "pacote pip pypandoc-binary"
        _log(f"[OK]    pandoc   {versao}  ({origem})")
    else:
        _erro("pandoc ausente — instale o programa (pandoc.org/installing.html) "
              "ou o pacote: pip install pypandoc-binary")
        falhou = True

    if motor["typst_cli"]:
        try:
            versao = subprocess.run([motor["typst_cli"], "--version"], capture_output=True,
                                    text=True, timeout=20).stdout.strip()
        except Exception:
            versao = "(versao nao reportada)"
        _log(f"[OK]    typst    {versao}  (PATH — via direta, pandoc chama o typst)")
    elif motor["typst_api"]:
        import typst
        versao = getattr(typst, "__version__", "(versao nao exposta)")
        _log(f"[OK]    typst    {versao}  (pacote pip — via em dois passos, sem executavel)")
        if motor["motivo_cli"] != "ausente no PATH":
            _log(f"[AVISO] typst do PATH descartado: {motor['motivo_cli']}")
    else:
        if motor["motivo_cli"] != "ausente no PATH":
            _erro(f"typst do PATH inutilizavel: {motor['motivo_cli']}")
        _erro("typst ausente — instale o programa (github.com/typst/typst) "
              "ou o pacote: pip install typst")
        falhou = True

    if not TEMPLATE_PADRAO.is_file():
        _erro(f"template ausente: {TEMPLATE_PADRAO}")
        falhou = True
    else:
        _log(f"[OK]    template {TEMPLATE_PADRAO}")

    instaladas: set[str] = set()
    if motor["typst_cli"]:
        try:
            saida = subprocess.run([motor["typst_cli"], "fonts"], capture_output=True,
                                   text=True, timeout=30).stdout
            instaladas = {linha.strip() for linha in saida.splitlines()}
        except Exception:
            pass
    elif motor["typst_api"]:
        try:
            import typst
            instaladas = {f.family for f in typst.Fonts().fonts()}
        except Exception:
            pass

    if instaladas:
        # O template declara cadeias de fallback; basta uma de cada familia existir.
        texto_ok = bool(instaladas & {"Inter", "Segoe UI", "Calibri", "Liberation Sans", "DejaVu Sans"})
        mono_ok = bool(instaladas & {"Consolas", "Courier New", "DejaVu Sans Mono", "Liberation Mono"})
        _log(f"[{'OK' if texto_ok else 'AVISO'}]    fonte de texto: "
             f"{'encontrada' if texto_ok else 'nenhuma da cadeia — typst usara substituta'}")
        _log(f"[{'OK' if mono_ok else 'AVISO'}]    fonte monoespacada: "
             f"{'encontrada' if mono_ok else 'nenhuma da cadeia — typst usara substituta'}")

    return 1 if falhou else 0


# ---------------------------------------------------------------------------
# init — esqueleto de uma obra nova
# ---------------------------------------------------------------------------

_PARTES_INICIAIS = ("00-frontmatter.md", "01-parte-um.md")

_MODELO_FRONTMATTER = """---
title: "{titulo}"
subtitle: "{subtitulo}"
author:
  - {autor}
date: "{data}"
lang: pt-BR
institute: "{instituicao}"
eyebrow: "{eyebrow}"
tagline: |
  {tagline}
toc: true
toc-depth: 2
abstract: |
  Descreva aqui, em três a cinco parágrafos, o escopo da obra: quais níveis de
  profundidade ela percorre, sob quais eixos fixos de análise, e o que ela
  deliberadamente deixa de fora.
---

# Como ler este livro

## A quem este livro se destina

Substitua este texto. Nomeie os leitores reais da obra e diga, para cada um,
por onde começar.

## A estrutura

Substitua este texto pela matriz da obra: o eixo vertical (níveis de
aproximação) e o eixo horizontal (as perguntas fixas feitas em cada nível).

## As convenções visuais

```{{=typst}}
#painel("Painel de contexto")[
  Caixas como esta trazem contexto, decisão histórica ou advertência. Quando o
  painel descreve algo incompleto ou pendente, o texto diz isso explicitamente.
]
```
"""

_MODELO_PARTE = """# PARTE I — TÍTULO DA PARTE

Parágrafo de abertura: o que esta parte responde e em que ordem.

# Capítulo 1 — Título do capítulo

```{=typst}
#ficha(
  ("Papel", "Uma linha sobre o que este objeto é"),
  ("Entrada", "O que ele consome"),
  ("Saída", "O que ele entrega"),
)
```

## 1.1 Primeira seção

Texto.

## 1.2 Rastreabilidade do capítulo

Liste aqui os arquivos ou fontes que sustentam cada afirmação do capítulo.
"""


def cmd_init(args: argparse.Namespace) -> int:
    pasta = _resolver_pasta(args.pasta)
    if (pasta / NOME_MANIFESTO).exists() and not args.force:
        _erro(f"ja existe {NOME_MANIFESTO} em {pasta}. Use --force para sobrescrever o manifesto.")
        return 1

    slug = args.slug or re.sub(r"[^a-z0-9]+", "-", args.titulo.lower()).strip("-")[:60] or "livro"
    nome_base = f"{date.today().strftime('%d-%m-%Y')}_{slug.upper()}"

    manifesto = {
        "versao_manifesto": "1.0",
        "titulo": args.titulo,
        "nome_base": nome_base,
        "pasta_partes": NOME_PARTES,
        "template": str(Path("ativos") / "livro.typst") if args.copiar_template else None,
        "partes": list(_PARTES_INICIAIS),
        "revisoes": [],
    }

    dir_partes = pasta / NOME_PARTES
    dir_partes.mkdir(parents=True, exist_ok=True)

    frontmatter = _MODELO_FRONTMATTER.format(
        titulo=args.titulo,
        subtitulo=args.subtitulo or "",
        autor=args.autor or "Autor nao informado",
        data=args.data or date.today().strftime("%d/%m/%Y"),
        instituicao=args.instituicao or args.titulo,
        eyebrow=args.eyebrow or "DOCUMENTO TECNICO",
        tagline=args.tagline or "Uma linha de posicionamento da obra, exibida na capa.",
    )
    if not (dir_partes / _PARTES_INICIAIS[0]).exists() or args.force:
        _escrever_atomico(dir_partes / _PARTES_INICIAIS[0], frontmatter)
    if not (dir_partes / _PARTES_INICIAIS[1]).exists() or args.force:
        _escrever_atomico(dir_partes / _PARTES_INICIAIS[1], _MODELO_PARTE)

    if args.copiar_template:
        destino = pasta / "ativos" / "livro.typst"
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TEMPLATE_PADRAO, destino)
        _log(f"[OK] template copiado para {destino} (edite-o para personalizar a identidade visual)")

    _salvar_manifesto(pasta, manifesto)
    _log(f"[OK] obra inicializada em {pasta}")
    _log(f"     partes:    {pasta / NOME_PARTES}")
    _log(f"     manifesto: {pasta / NOME_MANIFESTO}")
    _log(f"     proximo:   escreva as partes e rode 'livro.py check' e 'livro.py build'")
    return 0


def cmd_add_parte(args: argparse.Namespace) -> int:
    pasta = _resolver_pasta(args.pasta)
    manifesto = _carregar_manifesto(pasta)
    dir_partes = pasta / manifesto.get("pasta_partes", NOME_PARTES)

    nome = args.nome if args.nome.endswith(".md") else f"{args.nome}.md"
    caminho = dir_partes / nome
    if caminho.exists():
        _erro(f"parte ja existe: {caminho}")
        return 1

    _escrever_atomico(caminho, f"# {args.titulo or nome[:-3]}\n\nTexto.\n")

    partes = manifesto.get("partes") or []
    if args.depois_de and args.depois_de in partes:
        partes.insert(partes.index(args.depois_de) + 1, nome)
    else:
        partes.append(nome)
    manifesto["partes"] = partes
    _salvar_manifesto(pasta, manifesto)
    _log(f"[OK] parte criada e registrada: {caminho}")
    return 0


# ---------------------------------------------------------------------------
# check — auditoria deterministica do fonte
# ---------------------------------------------------------------------------

def _auditar_texto(caminho: Path, texto: str) -> list[str]:
    achados: list[str] = []
    linhas = texto.split("\n")

    # 1. Cercas de codigo balanceadas (causa classica de PDF truncado).
    abertas = 0
    for i, linha in enumerate(linhas, 1):
        if linha.lstrip().startswith("```"):
            abertas += 1
    if abertas % 2 != 0:
        achados.append(f"{caminho.name}: numero impar de cercas ``` ({abertas}) — bloco de codigo nao fechado")

    # 2. Blocos typst crus com parenteses/colchetes desbalanceados: o typst
    #    falha a compilacao inteira por um unico parentese faltando.
    dentro = False
    inicio = 0
    bloco: list[str] = []
    for i, linha in enumerate(linhas, 1):
        if not dentro and linha.strip().startswith("```{=typst}"):
            dentro, inicio, bloco = True, i, []
            continue
        if dentro and linha.strip().startswith("```"):
            dentro = False
            corpo = "\n".join(bloco)
            for abre, fecha, nome in (("(", ")", "parenteses"), ("[", "]", "colchetes")):
                if corpo.count(abre) != corpo.count(fecha):
                    achados.append(
                        f"{caminho.name}:{inicio}: bloco typst com {nome} desbalanceados "
                        f"({corpo.count(abre)} x {corpo.count(fecha)})"
                    )
            continue
        if dentro:
            bloco.append(linha)
    if dentro:
        achados.append(f"{caminho.name}:{inicio}: bloco typst aberto e nunca fechado")

    # 3. Tabelas: coluna estreita demais para o conteudo que carrega.
    for i, linha in enumerate(linhas):
        s = linha.strip()
        if not (s.startswith("|") and set(s) <= set("|:- ")):
            continue
        colunas = s.strip("|").split("|")
        larguras = [len(c) for c in colunas]
        total = sum(larguras) or 1
        maiores = [0] * len(colunas)
        for j in range(i + 1, min(i + 60, len(linhas))):
            lj = linhas[j].strip()
            if not lj.startswith("|"):
                break
            celulas = [c.strip() for c in lj.strip("|").split("|")]
            for k in range(min(len(celulas), len(colunas))):
                palavra = max((len(x) for x in celulas[k].split()), default=0)
                maiores[k] = max(maiores[k], palavra)
        for k, (largura, maior) in enumerate(zip(larguras, maiores)):
            disponivel = LARGURA_CORPO_CHARS * largura / total
            if maior > disponivel:
                achados.append(
                    f"{caminho.name}:{i + 1}: coluna {k + 1} da tabela e estreita demais "
                    f"({100 * largura / total:.0f}% da largura) para o conteudo (palavra de {maior} chars) "
                    f"— alargue o separador dessa coluna"
                )

    # 4. Tabela estreita demais no fonte: o writer typst so emite larguras
    #    relativas quando a linha passa de --columns; abaixo disso a tabela
    #    encolhe e desalinha.
    for i, linha in enumerate(linhas):
        s = linha.strip()
        if s.startswith("|") and set(s) <= set("|:- ") and len(s) <= COLUNAS_PANDOC:
            achados.append(
                f"{caminho.name}:{i + 1}: separador de tabela com {len(s)} chars "
                f"(<= {COLUNAS_PANDOC}) — a tabela nao ocupara a largura do corpo"
            )

    # 5. Acentuacao: PT-BR sem diacritico e erro de revisao, nao estilo.
    suspeitas = ("nao ", "nao.", "sao ", "codigo", "documentacao", "execucao", "portao",
                 "voce", "tambem", "alem ", "possivel", "necessario", "usuario", "criacao")
    for i, linha in enumerate(linhas, 1):
        if linha.lstrip().startswith(("```", "|", "    ")) or "`" in linha:
            continue
        baixa = linha.lower()
        for termo in suspeitas:
            if termo in baixa:
                achados.append(f"{caminho.name}:{i}: possivel falta de acentuacao PT-BR perto de '{termo.strip()}'")
                break

    return achados


def _auditar_rastreabilidade(pasta: Path, texto: str, raiz_evidencia: Path | None) -> list[str]:
    """Confere se caminhos de arquivo citados em codigo inline existem de fato.

    So audita quando --raiz-evidencia e informada: sem raiz declarada, um caminho
    citado nao e verificavel e o silencio seria mais honesto que um falso OK.
    """
    if raiz_evidencia is None:
        return []
    achados = []
    candidatos = set(re.findall(r"`([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:py|json|md|yaml|yml|typst|toml|ini|cfg))`", texto))
    for rel in sorted(candidatos):
        if rel.startswith(("http", "<")) or "*" in rel:
            continue
        if not (raiz_evidencia / rel).exists():
            achados.append(f"rastreabilidade: arquivo citado nao existe em {raiz_evidencia}: {rel}")
    return achados


def cmd_check(args: argparse.Namespace) -> int:
    pasta = _resolver_pasta(args.pasta)
    manifesto = _carregar_manifesto(pasta)
    partes = _partes_ordenadas(pasta, manifesto)

    raiz = Path(args.raiz_evidencia).resolve() if args.raiz_evidencia else None
    achados: list[str] = []
    palavras = 0

    for caminho in partes:
        texto = caminho.read_text(encoding="utf-8")
        palavras += len(texto.split())
        achados.extend(_auditar_texto(caminho, texto))
        achados.extend(_auditar_rastreabilidade(pasta, texto, raiz))

    primeiro = partes[0].read_text(encoding="utf-8") if partes else ""
    if not primeiro.startswith("---"):
        achados.append(f"{partes[0].name}: a primeira parte precisa abrir com o bloco YAML de metadados")

    _log(f"partes: {len(partes)} | palavras: {palavras}")
    if not achados:
        _log("[OK] nenhuma inconsistencia deterministica encontrada")
        return 0

    for a in achados:
        _log(f"[ACHADO] {a}")
    _log(f"[FALHA] {len(achados)} achado(s)")
    return 1


# ---------------------------------------------------------------------------
# build / preview / status / update
# ---------------------------------------------------------------------------

def _montar_markdown(pasta: Path, manifesto: dict) -> tuple[Path, str]:
    partes = _partes_ordenadas(pasta, manifesto)
    corpo = "\n\n".join(p.read_text(encoding="utf-8").rstrip() for p in partes) + "\n"
    destino = pasta / f"{manifesto['nome_base']}.md"
    _escrever_atomico(destino, corpo)
    return destino, corpo


def _pandoc_base(markdown: Path, template: Path, pandoc: str | None = None) -> list[str]:
    return [
        pandoc or "pandoc", str(markdown),
        "--from", "markdown+raw_attribute+pipe_tables+yaml_metadata_block",
        "--template", str(template),
        "--columns", str(COLUNAS_PANDOC),
    ]


def cmd_build(args: argparse.Namespace) -> int:
    pasta = _resolver_pasta(args.pasta)
    manifesto = _carregar_manifesto(pasta)
    template = _template(manifesto, pasta)

    motor = _resolver_motor()
    if not motor["pandoc"] or not (motor["typst_cli"] or motor["typst_api"]):
        _erro("pandoc e/ou typst indisponiveis — rode 'livro.py doctor'")
        return 1

    markdown, corpo = _montar_markdown(pasta, manifesto)
    pdf = pasta / f"{manifesto['nome_base']}.pdf"

    codigo, erro = _compilar_pdf(markdown, template, pdf, motor)
    if codigo != 0:
        _erro("compilacao falhou:")
        print(erro[-4000:], file=sys.stderr)
        return codigo

    manifesto["hash_fonte"] = _sha256_texto(corpo)
    manifesto["ultima_compilacao"] = date.today().isoformat()
    _salvar_manifesto(pasta, manifesto)

    _log(f"[OK] markdown: {markdown.name} ({len(corpo.splitlines())} linhas, {len(corpo.split())} palavras)")
    _log(f"[OK] pdf:      {pdf.name} ({pdf.stat().st_size / 1024:.1f} KB)")
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    pasta = _resolver_pasta(args.pasta)
    manifesto = _carregar_manifesto(pasta)
    template = _template(manifesto, pasta)

    motor = _resolver_motor()
    if not motor["pandoc"] or not (motor["typst_cli"] or motor["typst_api"]):
        _erro("pandoc e/ou typst indisponiveis — rode 'livro.py doctor'")
        return 1

    markdown, _ = _montar_markdown(pasta, manifesto)
    typ = pasta / f"{manifesto['nome_base']}.typ"

    res = subprocess.run(_pandoc_base(markdown, template, motor["pandoc"])
                         + ["-t", "typst", "-s", "-o", str(typ)], capture_output=True, text=True)
    if res.returncode != 0:
        _erro(res.stderr[-3000:])
        return res.returncode

    saida = pasta / (args.saida or "preview")
    if saida.exists():
        shutil.rmtree(saida)   # resto de execucao anterior faz inspecionar pagina velha
    saida.mkdir(parents=True, exist_ok=True)
    molde = str(saida / "pagina{n}.png")

    if motor["typst_cli"]:
        res = subprocess.run([motor["typst_cli"], "compile", "--format", "png",
                              "--ppi", str(args.ppi), str(typ), molde],
                             capture_output=True, text=True)
        typ.unlink(missing_ok=True)
        if res.returncode != 0:
            _erro(res.stderr[-3000:])
            return res.returncode
    else:
        import typst as motor_typst
        try:
            motor_typst.compile(str(typ), output=molde, format="png", ppi=float(args.ppi))
        except Exception as exc:
            _erro(f"typst (via pacote Python) falhou: {exc}")
            return 1
        finally:
            typ.unlink(missing_ok=True)

    paginas = sorted(saida.glob("pagina*.png"))
    _log(f"[OK] {len(paginas)} pagina(s) em {saida}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    pasta = _resolver_pasta(args.pasta)
    manifesto = _carregar_manifesto(pasta)
    partes = _partes_ordenadas(pasta, manifesto)

    corpo = "\n\n".join(p.read_text(encoding="utf-8").rstrip() for p in partes) + "\n"
    hash_atual = _sha256_texto(corpo)
    hash_compilado = manifesto.get("hash_fonte")
    pdf = pasta / f"{manifesto['nome_base']}.pdf"

    _log(f"obra:      {manifesto.get('titulo')}")
    _log(f"partes:    {len(partes)}")
    _log(f"palavras:  {len(corpo.split())}")
    _log(f"pdf:       {'existe' if pdf.is_file() else 'AUSENTE'}"
         + (f" ({pdf.stat().st_size / 1024:.1f} KB)" if pdf.is_file() else ""))
    _log(f"compilado: {manifesto.get('ultima_compilacao') or 'nunca'}")
    _log(f"revisoes:  {len(manifesto.get('revisoes', []))}")

    if hash_compilado is None or not pdf.is_file():
        _log("[PENDENTE] o PDF ainda nao foi gerado a partir deste fonte")
        return 1
    if hash_atual != hash_compilado:
        _log("[DESATUALIZADO] o fonte mudou desde a ultima compilacao — rode 'livro.py update'")
        return 1
    _log("[OK] PDF em dia com o fonte")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    """Recompila somente quando o fonte mudou e registra a revisao no manifesto."""
    pasta = _resolver_pasta(args.pasta)
    manifesto = _carregar_manifesto(pasta)
    partes = _partes_ordenadas(pasta, manifesto)

    corpo = "\n\n".join(p.read_text(encoding="utf-8").rstrip() for p in partes) + "\n"
    hash_atual = _sha256_texto(corpo)
    pdf = pasta / f"{manifesto['nome_base']}.pdf"

    if hash_atual == manifesto.get("hash_fonte") and pdf.is_file() and not args.force:
        _log("[OK] fonte inalterado e PDF presente — nada a recompilar (use --force para recompilar assim mesmo)")
        return 0

    if not args.pular_check:
        codigo = cmd_check(argparse.Namespace(pasta=str(pasta), raiz_evidencia=args.raiz_evidencia))
        if codigo != 0:
            _erro("check reprovou — corrija os achados ou rode com --pular-check assumindo o risco")
            return codigo

    codigo = cmd_build(argparse.Namespace(pasta=str(pasta)))
    if codigo != 0:
        return codigo

    manifesto = _carregar_manifesto(pasta)
    revisoes = manifesto.get("revisoes", [])
    revisoes.append({
        "data": date.today().isoformat(),
        "hash_fonte": hash_atual,
        "palavras": len(corpo.split()),
        "nota": args.nota or "",
    })
    manifesto["revisoes"] = revisoes
    _salvar_manifesto(pasta, manifesto)
    _log(f"[OK] revisao {len(revisoes)} registrada no manifesto")
    return 0


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="livro.py", description="Motor deterministico de livro-texto (pandoc + typst)")
    sub = p.add_subparsers(dest="comando", required=True)

    sub.add_parser("doctor", help="Verifica pandoc, typst e fontes")

    pi = sub.add_parser("init", help="Cria o esqueleto de uma obra nova")
    pi.add_argument("pasta", nargs="?", default=None)
    pi.add_argument("--titulo", required=True)
    pi.add_argument("--subtitulo", default=None)
    pi.add_argument("--autor", default=None)
    pi.add_argument("--data", default=None)
    pi.add_argument("--instituicao", default=None)
    pi.add_argument("--eyebrow", default=None, help="Etiqueta pequena acima do titulo na capa")
    pi.add_argument("--tagline", default=None, help="Paragrafo curto de posicionamento na capa")
    pi.add_argument("--slug", default=None)
    pi.add_argument("--copiar-template", action="store_true",
                    help="Copia o template para <pasta>/ativos/ e passa a usa-lo (permite personalizar)")
    pi.add_argument("--force", action="store_true")

    pa = sub.add_parser("add-parte", help="Cria uma parte nova e registra no manifesto")
    pa.add_argument("pasta", nargs="?", default=None)
    pa.add_argument("--nome", required=True)
    pa.add_argument("--titulo", default=None)
    pa.add_argument("--depois-de", default=None, help="Nome da parte apos a qual inserir")

    pc = sub.add_parser("check", help="Auditoria deterministica do fonte")
    pc.add_argument("pasta", nargs="?", default=None)
    pc.add_argument("--raiz-evidencia", default=None,
                    help="Raiz para conferir se os arquivos citados na rastreabilidade existem")

    pb = sub.add_parser("build", help="Concatena as partes e compila o PDF")
    pb.add_argument("pasta", nargs="?", default=None)

    pp = sub.add_parser("preview", help="Renderiza paginas em PNG")
    pp.add_argument("pasta", nargs="?", default=None)
    pp.add_argument("--ppi", type=int, default=90)
    pp.add_argument("--saida", default=None)

    ps = sub.add_parser("status", help="Estado da obra e se o PDF esta em dia")
    ps.add_argument("pasta", nargs="?", default=None)

    pu = sub.add_parser("update", help="Recompila se o fonte mudou e registra a revisao")
    pu.add_argument("pasta", nargs="?", default=None)
    pu.add_argument("--nota", default=None, help="O que mudou nesta revisao")
    pu.add_argument("--raiz-evidencia", default=None)
    pu.add_argument("--pular-check", action="store_true")
    pu.add_argument("--force", action="store_true")

    return p


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)
    despacho = {
        "doctor": cmd_doctor,
        "init": cmd_init,
        "add-parte": cmd_add_parte,
        "check": cmd_check,
        "build": cmd_build,
        "preview": cmd_preview,
        "status": cmd_status,
        "update": cmd_update,
    }
    try:
        return despacho[args.comando](args)
    except (FileNotFoundError, ValueError) as exc:
        _erro(str(exc))
        return 1


if __name__ == "__main__":
    codigo = main()
    # A regra de uso do ecossistema manda canalizar saida verbosa (`| tail -n 20`).
    # Quando o filtro fecha o cano antes do fim, o flush final do interpretador
    # emite "Exception ignored" e troca o exit code por 120 — apagando o resultado
    # real do comando. Drenar stdout para o descarte preserva o codigo verdadeiro.
    try:
        sys.stdout.flush()
    except (BrokenPipeError, OSError):
        try:
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        except Exception:
            pass
    sys.exit(codigo)
