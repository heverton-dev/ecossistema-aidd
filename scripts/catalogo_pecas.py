#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Catálogo de peças do Ecossistema AIDD (mapa-pecas ciclo-01, passo 1).

Varre o repositório e grava um inventário único de todas as peças que montam
os fluxos (ferramentas, comandos de CLI, skills, comandos slash, MCPs, hooks,
gates, contratos de handoff e as etapas da Tríade Canônica), junto com os
achados de repetição e de encaixe quebrado.

Tudo é extraído do código (AST, regex sobre decoradores de CLI, hashes). A
única parte dinâmica é a checagem de encaixe: cada chamada `ecossistema.py
<ferramenta> ...` feita pelo orquestrador da tríade é conferida contra o
`--help` real da ferramenta (subcomando existe? flags existem?).

Somente leitura no repositório: escreve apenas o arquivo de saída.

Uso:
  python scripts/catalogo_pecas.py [--saida ARQ] [--sem-encaixe] [--check]
    --saida        destino do JSON (padrão: docs/auditoria/mapa-pecas/catalogo-pecas.json)
    --sem-encaixe  pula a checagem dinâmica via --help (mais rápido, só estático)
    --check        não grava; exit 1 se o arquivo existente estiver desatualizado
Exit 0: catálogo gravado (ou atualizado, no --check). Exit 1: --check divergente.
"""
import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA_PADRAO = RAIZ / "docs" / "auditoria" / "mapa-pecas" / "catalogo-pecas.json"
COMPARTILHADO = RAIZ / "componentes" / "compartilhado"
ORQUESTRADOR = RAIZ / "scripts" / "orquestrador_sincrono.py"
DEPENDENCIAS = RAIZ / "gates" / "dependencias_externas.json"

# Pastas que são exemplos/sandboxes copiados, não peças vivas.
IGNORAR = ("materiais-extras", "sandbox-forge-teste", ".venv", "node_modules", "__pycache__")

# Ponto de entrada de cada ferramenta (espelha os cmd_* de ecossistema.py).
ENTRADAS = {
    "aidd-forge": ("forge", "aidd_forge/cli.py"),
    "aidd-planner": ("planner", "aidd_planner/cli.py"),
    "aidd-generator": ("generate", "scripts/pipeline_completo.py"),
    "aidd-factory": ("factory", "scripts/pipeline_factory.py"),
    "aidd-bridge": ("bridge", "aidd_bridge/cli.py"),
    "aidd-master": ("master", "scripts/aidd.py"),
    "aidd-enterprise": ("enterprise", "scripts/aidd.py"),
    "aidd-ops": ("ops", "scripts/pipeline_ops.py"),
}

# Tarefas que deveriam ter uma dona só: regex sobre o nome do arquivo.
TAREFAS = {
    "barrar-segredos": r"segredo|secret",
    "compat-harness": r"harness",
    "injetar-componentes": r"inject",
    "detectar-stack-camada": r"detector",
    "auditar-conformidade": r"(^|_)audit",
    "docker-compose": r"compose",
    "gerar-frontend": r"frontend",
    "ponte-orca": r"orca",
    "escrita-atomica": r"escritor_atomico",
    "resultado-monad": r"^result\.py$",
}

# `@click.command(...)` é comando único (sem subcomandos); só grupos contam.
RE_CLICK = re.compile(r"@(?!click\.)[\w.]+\.command\(\s*[\"']([\w-]+)[\"']")
RE_ARGPARSE = re.compile(r"add_parser\(\s*[\"']([\w-]+)[\"']")
RE_FLAG = re.compile(r"--[a-z][\w-]*")


def _rel(p: Path) -> str:
    return p.relative_to(RAIZ).as_posix()


def _ignorado(p: Path) -> bool:
    # Pastas-ponto na raiz (.claude, .agents...) são destinos gerados por `components sync`.
    return any(parte in IGNORAR for parte in p.parts) or p.parts[0].startswith(".")


def _ler(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def _hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def _frontmatter(texto: str, campo: str) -> str:
    m = re.search(rf"^{campo}:\s*(.+)$", texto, re.MULTILINE)
    return m.group(1).strip().strip("\"'") if m else ""


def _descricao_readme(pasta: Path) -> str:
    readme = pasta / "README.md"
    if not readme.is_file():
        return ""
    for linha in _ler(readme).splitlines():
        if linha.startswith(">"):
            return linha.lstrip("> ").replace("**", "").strip()
    return ""


def _py_vivos(base: Path):
    return sorted(p for p in base.rglob("*.py") if not _ignorado(p.relative_to(RAIZ)))


# ── Peças ────────────────────────────────────────────────────────────────

def coletar_ferramentas() -> list[dict]:
    ferramentas = []
    for pasta in sorted((RAIZ / "tools").iterdir()):
        if not pasta.is_dir() or pasta.name not in ENTRADAS:
            continue
        atalho, entrada = ENTRADAS[pasta.name]
        cli = pasta / entrada
        texto = _ler(cli) if cli.is_file() else ""
        comandos = sorted(set(RE_CLICK.findall(texto)) | set(RE_ARGPARSE.findall(texto)))
        gates = sorted(_rel(p) for p in _py_vivos(pasta) if p.name.startswith("G_"))
        mcps = sorted(_rel(p) for p in pasta.glob("mcps/*/server.py"))
        ferramentas.append({
            "id": pasta.name,
            "descricao": _descricao_readme(pasta),
            "chamada": f"python ecossistema.py {atalho}",
            "entrada_cli": _rel(cli) if cli.is_file() else None,
            "comandos": comandos,
            "gates_proprios": gates,
            "mcps_proprios": mcps,
            "arquivos_py": len([p for p in _py_vivos(pasta) if "test" not in p.name]),
        })
    return ferramentas


def coletar_skills_terceiros() -> list[str]:
    """Skills de terceiros registradas em gates/dependencias_externas.json (instaladas
    pelo instalador do fornecedor, nunca copiadas para a fonte unica)."""
    sys.path.insert(0, str(RAIZ / "scripts"))
    import gestor_dependencias
    return sorted(gestor_dependencias.skills_de_terceiros(str(DEPENDENCIAS)))


def coletar_skills(terceiros: list[str] = ()) -> list[dict]:
    skills = []
    for skill_md in sorted((COMPARTILHADO / "skills").glob("*/SKILL.md")):
        texto = _ler(skill_md)
        skills.append({
            "id": skill_md.parent.name,
            "descricao": _frontmatter(texto, "description"),
            "linhas": texto.count("\n") + 1,
            "terceiro": skill_md.parent.name in terceiros,
        })
    return skills


RE_SKILL_DO_COMANDO = re.compile(r"skill `(?:skills/)?([a-z0-9]+(?:-[a-z0-9]+)*)`")


def _descricao_comando(texto: str) -> str:
    descricao = _frontmatter(texto, "description")
    if descricao:
        return descricao
    corpo = re.sub(r"^---\n.*?\n---\n", "", texto, flags=re.DOTALL)
    for linha in corpo.splitlines():
        linha = linha.strip()
        if linha and not linha.startswith(("#", ">", "-", "`", "|")):
            return linha
    return ""


def coletar_comandos_slash() -> list[dict]:
    """Cada comando e a skill que ele chama (frase 'Executa a skill `x`'), e se ela existe."""
    comandos = []
    for p in sorted((COMPARTILHADO / "comandos").glob("*.md")):
        texto = _ler(p)
        m = RE_SKILL_DO_COMANDO.search(texto)
        skill = m.group(1) if m else ""
        comandos.append({
            "id": p.stem, "caminho": _rel(p), "descricao": _descricao_comando(texto),
            "skill": skill, "skill_existe": bool(skill) and (COMPARTILHADO / "skills" / skill / "SKILL.md").is_file(),
        })
    return comandos


def coletar_mcps(ferramentas: list[dict]) -> dict:
    registrados = []
    mcp_json = RAIZ / ".mcp.json"
    if mcp_json.is_file():
        registrados = sorted(json.loads(_ler(mcp_json)).get("mcpServers", {}))
    configs = " ".join(_ler(RAIZ / n) for n in (".mcp.json", "opencode.jsonc", "mimocode.jsonc")
                       if (RAIZ / n).is_file())
    internos = []
    for f in ferramentas:
        for caminho in f["mcps_proprios"]:
            nome = Path(caminho).parent.name
            internos.append({
                "id": nome, "ferramenta": f["id"], "caminho": caminho,
                "registrado_em_config": nome in configs or caminho in configs,
            })
    return {"registrados_mcp_json": registrados, "internos_das_ferramentas": internos}


def coletar_hooks() -> list[dict]:
    settings = RAIZ / ".claude" / "settings.json"
    if not settings.is_file():
        return []
    hooks = []
    for evento, grupos in json.loads(_ler(settings)).get("hooks", {}).items():
        for grupo in grupos:
            for h in grupo.get("hooks", []):
                comando = h.get("command", "")
                script = re.search(r"[\w./-]+\.(py|sh|cmd)", comando)
                hooks.append({
                    "evento": evento,
                    "matcher": grupo.get("matcher", ""),
                    "script": script.group(0) if script else comando[:80],
                })
    return hooks


def _gates_no_pre_commit() -> set[str]:
    cfg = RAIZ / ".pre-commit-config.yaml"
    return set(re.findall(r"gates/(G_\w+)\.py", _ler(cfg))) if cfg.is_file() else set()


def _papel_gate(p: Path) -> str:
    """Onde o guarda trabalha: ecossistema (raiz), ferramenta, entrega (vai no app) ou componente."""
    partes = p.relative_to(RAIZ).parts
    if partes[0] == "gates":
        return "ecossistema"
    if "templates" in partes:
        return "entrega"
    return "ferramenta" if partes[0] == "tools" else "componente"


def _descricao_gate(p: Path) -> str:
    try:
        doc = ast.get_docstring(ast.parse(_ler(p).lstrip("﻿"))) or ""
    except SyntaxError:
        return ""
    # Pula o banner (====, "ECOSSISTEMA AIDD — QUALITY GATE: X", "G_X.py — Quality Gate…");
    # de "GATE: G_X — texto" fica só o texto. Junta o primeiro parágrafo e, se ele
    # termina em ":", o primeiro item que o segue.
    prefixo_nome = re.compile(rf"^(?:(?:quality\s+)?gate:\s*)?{re.escape(p.stem)}(?:\.py)?\s*[—–:-]?\s*",
                              re.IGNORECASE)
    partes = []
    for linha in doc.splitlines():
        linha = re.sub(r"^quality gate:\s*", "", linha.strip(), flags=re.IGNORECASE)
        sem_nome = prefixo_nome.sub("", linha, count=1)
        banner = (set(linha) <= set("=-") or linha.upper().startswith("ECOSSISTEMA AIDD")
                  or (sem_nome != linha and (not sem_nome or sem_nome.lower().startswith("quality gate"))))
        linha = sem_nome
        if linha and set(linha) <= set("=-"):
            partes = []  # régua depois de um título: o que veio antes era cabeçalho
            continue
        if not partes and (not linha or banner):
            continue
        if not linha:
            if partes[-1].endswith(":"):
                continue
            break
        partes.append(linha.lstrip("-*0123456789. "))
        if len(partes) > 1 and partes[-2].endswith(":"):
            break
    texto = " ".join(partes)
    return texto if len(texto) <= 200 else texto[:200].rsplit(" ", 1)[0] + "…"


def _meta_gates():
    """Reaproveita os parsers dos próprios meta-guardas (fonte única da regra)."""
    sys.path.insert(0, str(RAIZ / "gates"))
    try:
        import G_LEI_DECLARA_PORTAO as leis
        import G_PORTAO_PROVA_QUE_MORDE as morde
    finally:
        sys.path.pop(0)
    return leis, morde


RE_DECLARACAO_TOLERANTE = re.compile(r"^\s*-\s+(?:\*\*)?Port[ãa]o(?:\*\*)?:.*?(G_\w+)\.py")


def _leis_por_gate(leis_mod, agents_md: str) -> tuple[dict[str, list[int]], list[str]]:
    """Mapeia guarda -> leis que o declaram e devolve as declarações que o meta-guarda não enxerga.

    Leitura tolerante: aceita comentário depois de `(provado)`. O regex estrito do
    G_LEI_DECLARA_PORTAO pula essas linhas; elas voltam como achado, não somem.
    """
    bloco = leis_mod.extrair_bloco_leis(agents_md)
    mapa, invisiveis, numero = defaultdict(list), [], None
    for linha in bloco.splitlines():
        cabecalho = leis_mod.RE_LAW_HEADER.match(linha.strip())
        if cabecalho:
            numero = int(cabecalho.group(1))
            continue
        m = RE_DECLARACAO_TOLERANTE.match(linha)
        if m and numero is not None:
            if numero not in mapa[m.group(1)]:
                mapa[m.group(1)].append(numero)
            if not leis_mod.RE_GATE_DECLARATION.match(linha):
                invisiveis.append(f"Lei #{numero}: {m.group(1)}")
    return mapa, invisiveis


RE_FORCA = re.compile(r"\((provado|nao-provado|sem-gate)")
RE_DECLARACAO_QUALQUER = re.compile(r"^\s*-\s+(?:\*\*)?Port[ãa]o(?:\*\*)?:\s*(.+)$")


def coletar_leis() -> list[dict]:
    """Cada lei do AGENTS.md e as declarações de portão embaixo dela, lidas de forma
    tolerante; 'visivel' diz se o G_LEI_DECLARA_PORTAO (regex estrito) enxerga a linha."""
    leis_mod, _ = _meta_gates()
    bloco = leis_mod.extrair_bloco_leis(_ler(RAIZ / "AGENTS.md"))
    leis, atual = [], None
    for linha in bloco.splitlines():
        cabecalho = leis_mod.RE_LAW_HEADER.match(linha.strip())
        if cabecalho:
            atual = {"numero": int(cabecalho.group(1)), "titulo": cabecalho.group(2).strip().rstrip(":"),
                     "portoes": [], "sem_gate": False}
            leis.append(atual)
            continue
        if atual is None:
            continue
        m = RE_DECLARACAO_TOLERANTE.match(linha)
        if m:
            forca = RE_FORCA.search(linha)
            atual["portoes"].append({
                "gate": m.group(1),
                "forca": forca.group(1) if forca else "",
                "visivel": bool(leis_mod.RE_GATE_DECLARATION.match(linha)),
            })
        else:
            decl = RE_DECLARACAO_QUALQUER.match(linha)
            alvo = re.sub(r"\s*[\(\[][\w\-]+[\)\]].*$", "", decl.group(1)) if decl else ""
            if alvo and leis_mod.normalizar_literal_sem_gate(alvo):
                atual["sem_gate"] = True
    return leis


def coletar_harnesses() -> dict:
    """Cada harness do manifesto: pasta, tipos de peça que recebe, destino de cada tipo,
    skills presentes em disco e arquivo de config de MCP. Mais as pastas legadas versionadas."""
    manifesto = json.loads(_ler(RAIZ / "gates" / "manifesto_harnesses.json"))
    sys.path.insert(0, str(RAIZ / "scripts"))
    import gestor_dependencias
    tipos = manifesto["tipos_componente"]
    nossas = {p.parent.name for p in (COMPARTILHADO / "skills").glob("*/SKILL.md")}
    lista = []
    for nome, info in manifesto["harnesses_suportados"].items():
        prefixo = info.get("prefixo_pasta", "")
        recebe = [t for t, v in tipos.items() if nome in (v.get("harnesses_aplicaveis") or [])]
        destinos = {t: ((tipos[t].get("dest_harness_template_overrides") or {}).get(nome)
                        or tipos[t].get("dest_harness_template") or "").replace("{prefixo_pasta}", prefixo)
                    for t in recebe}
        base = RAIZ / prefixo
        if nome == "gemini-cli":
            skills = list(base.glob("extensions/*/skills/*/SKILL.md"))
        else:
            skills = list(base.glob("skills/*/SKILL.md"))
        mcp = gestor_dependencias.DESTINOS_MCP.get(nome, {}).get("caminho")
        nomes_em_disco = {s.parent.name for s in skills}
        lista.append({"id": nome, "prefixo": prefixo, "confirmado": bool(info.get("confirmado")), "recebe": recebe,
                      "destinos": destinos, "skills_em_disco": len(skills),
                      "nossas_faltando": sorted(nossas - nomes_em_disco),
                      "terceiros_em_disco": len(nomes_em_disco - nossas),
                      "config_mcp": _rel(Path(mcp)) if mcp else ""})
    legadas = []
    for pasta in (".gemini/skills", ".agent/skills"):
        r = subprocess.run(["git", "ls-files", pasta], cwd=RAIZ, capture_output=True, text=True)
        n = len([linha for linha in r.stdout.splitlines() if linha.strip()])
        if n:
            legadas.append({"pasta": pasta, "arquivos_versionados": n})
    return {"harnesses": lista, "pastas_legadas": legadas}

def coletar_moldes_entrega() -> list[dict]:
    """Cada molde de entrega (tools/<f>/templates/<molde>/): o que vai junto com o app gerado."""
    moldes = []
    pastas = list(RAIZ.glob("tools/*/templates")) + list(RAIZ.glob("tools/*/aidd_*/templates"))
    for tpl in sorted(pastas):
        for sub in sorted(p for p in tpl.iterdir() if p.is_dir() and p.name not in IGNORAR):
            arquivos = [f for f in sub.rglob("*") if f.is_file() and not any(x in IGNORAR for x in f.parts)]
            dona = tpl.relative_to(RAIZ / "tools").parts[0]
            moldes.append({"ferramenta": dona, "molde": sub.name, "caminho": _rel(sub),
                           "arquivos": len(arquivos)})
    return moldes

def coletar_scripts() -> list[dict]:
    """Cada script de scripts/: o que faz (docstring) e quem o chama (painel, commit, guardas, outros scripts, testes)."""
    fontes = {"painel": [RAIZ / "ecossistema.py"],
              "commit": [RAIZ / ".pre-commit-config.yaml", RAIZ / ".githooks" / "pre-commit"],
              "guardas": sorted((RAIZ / "gates").glob("G_*.py")),
              "scripts": sorted((RAIZ / "scripts").glob("*.py")),
              "testes": sorted((RAIZ / "tests").rglob("test_*.py")) + sorted((RAIZ / "scripts").glob("test_*.py"))
              + sorted((RAIZ / "gates").glob("test_*.py"))}
    textos = {grupo: [(p, _ler(p)) for p in arquivos if p.is_file()] for grupo, arquivos in fontes.items()}
    lista = []
    for p in sorted((RAIZ / "scripts").glob("*.py")):
        if p.name.startswith("test_") or p.name == "__init__.py":
            continue
        try:
            doc = ast.get_docstring(ast.parse(_ler(p).lstrip("\ufeff"))) or ""
        except SyntaxError:
            doc = ""
        linha = next((x.strip() for x in doc.splitlines() if x.strip() and not set(x.strip()) <= set("=-─")), "")
        chamado_por = sorted(grupo for grupo, itens in textos.items()
                             if any(p.stem in texto for arq, texto in itens if arq != p))
        lista.append({"id": p.stem, "descricao": linha, "chamado_por": chamado_por})
    return lista

RE_NOTA_LAUDO = re.compile(r"[Nn]ota[^:\n]*:\s*\**\s*(\d+(?:[.,]\d+)?)\s*/\s*10")
# Documentos que toda rodada 4F produz; a fase 3 (Construtor) entrega código, não documento fixo.
FASES_CICLO = (("laudo_inicial", "LAUDO-15D-INICIAL.md"), ("plano_evolucao", "PLANO-EVOLUCAO.md"),
               ("laudo_revisado", "LAUDO-15D-REVISADO.md"), ("dod", "DOD.md"))


def coletar_oficina() -> dict:
    """Planos em docs/planos/ (rascunho, a-fazer, fazendo, feitos) e ciclos de auditoria em
    docs/auditoria/<alvo>/ciclo-NN/, com as fases presentes e a última nota do laudo."""
    base = RAIZ / "docs" / "planos"
    planos = []
    for estado, pasta in (("rascunho", base), ("a-fazer", base / "a-fazer"), ("fazendo", base / "fazendo"),
                          ("feitos", base / "feitos")):
        for p in sorted(pasta.glob("PLAN-*")):
            itens = len([f for f in p.glob("[0-9][0-9]-*.md") if not f.name.startswith("00-")]) if p.is_dir() else 0
            planos.append({"id": p.name.removesuffix(".md"), "estado": estado, "itens": itens})
    ciclos = []
    for d in sorted((RAIZ / "docs" / "auditoria").glob("*/ciclo-*")):
        nomes = {f.name for f in d.iterdir()}
        nota = ""
        for arquivo in ("LAUDO-15D-REVISADO.md", "LAUDO-15D-INICIAL.md"):
            if arquivo in nomes:
                notas = RE_NOTA_LAUDO.findall(_ler(d / arquivo))
                if notas:
                    nota = notas[-1].replace(",", ".")
                    break
        ciclos.append({"alvo": d.parent.name, "ciclo": d.name, "caminho": _rel(d),
                       "fases": {chave: arquivo in nomes for chave, arquivo in FASES_CICLO}, "nota": nota})
    melhorias = len(list((RAIZ / "docs" / "melhorias").glob("*.json")))
    return {"planos": planos, "ciclos": ciclos, "relatorios_melhoria": melhorias}

RE_DIMENSAO_MOLDE = re.compile(r"\*\*(?:\[[^\]]*\]\s*)?D(\d+)\.\s*([^:*]+):\*\*")
RE_DIMENSAO_LAUDO = re.compile(r"D(\d+)\.\s*[^:*]+:\*\*")


def classificar_dimensao(texto: str) -> str:
    """Classificação por palavra-chave do texto do laudo (aproximação honesta, não julgamento)."""
    baixo = texto.lower()
    if "failed" in baixo or "not implemented" in baixo:
        return "falha"
    if "parcial" in baixo:
        return "parcial"
    if "implementado" in baixo:
        return "ok"
    return "descrito"


def coletar_lente_15d() -> dict:
    """As 15 dimensões do molde de auditoria e, para cada ciclo com laudo, a classificação de
    cada dimensão no laudo mais recente (revisado, senão inicial)."""
    molde = _ler(RAIZ / "docs" / "auditoria" / "TEMPLATE-AUDITORIA-FERRAMENTA.md")
    dimensoes = {}
    for n, titulo in RE_DIMENSAO_MOLDE.findall(molde):
        dimensoes.setdefault(int(n), titulo.strip())
    laudos = []
    for d in sorted((RAIZ / "docs" / "auditoria").glob("*/ciclo-*")):
        for arquivo in ("LAUDO-15D-REVISADO.md", "LAUDO-15D-INICIAL.md"):
            if (d / arquivo).is_file():
                classes = {}
                for linha in _ler(d / arquivo).splitlines():
                    achados = list(RE_DIMENSAO_LAUDO.finditer(linha))
                    for i, m in enumerate(achados):
                        fim = achados[i + 1].start() if i + 1 < len(achados) else len(linha)
                        classes.setdefault(str(int(m.group(1))), classificar_dimensao(linha[m.end():fim]))
                laudos.append({"alvo": d.parent.name, "ciclo": d.name, "laudo": _rel(d / arquivo), "dimensoes": classes})
                break
    return {"dimensoes": [{"numero": n, "titulo": t} for n, t in sorted(dimensoes.items())], "laudos": laudos}

def _prova_que_morde(morde_mod, nome: str) -> bool:
    teste = morde_mod.encontrar_arquivo_teste(f"{nome}.py", str(RAIZ / "gates"))
    return bool(teste) and morde_mod.auditar_teste_de_falha(teste, executar=False)[0]


def coletar_gates() -> tuple[list[dict], list[str]]:
    no_pre_commit = _gates_no_pre_commit()
    leis_mod, morde_mod = _meta_gates()
    leis, invisiveis = _leis_por_gate(leis_mod, _ler(RAIZ / "AGENTS.md"))
    por_nome = defaultdict(list)
    for base in (RAIZ / "gates", RAIZ / "tools", RAIZ / "componentes"):
        for p in _py_vivos(base):
            if p.name.startswith("G_") and p.suffix == ".py":
                por_nome[p.stem].append(p)
    gates = []
    for nome in sorted(por_nome):
        copias = sorted(por_nome[nome])
        na_raiz = RAIZ / "gates" / f"{nome}.py"
        principal = na_raiz if na_raiz.is_file() else copias[0]
        versoes = {}
        for p in copias:
            versoes.setdefault(_hash(p), chr(ord("A") + len(versoes)))
        gates.append({
            "id": nome,
            "descricao": _descricao_gate(principal),
            # Versão = letra por conteúdo (A, B, C…): cópias com a mesma letra são idênticas.
            # Não grava o hash em si: sequência hex longa vira falso positivo no G_SEGREDOS.
            "copias": [{"caminho": _rel(p), "versao": versoes[_hash(p)], "papel": _papel_gate(p)} for p in copias],
            "versoes_distintas": len(versoes),
            "no_pre_commit": nome in no_pre_commit and na_raiz.is_file(),
            # Só medido para a raiz: é lá que a Lei #13 exige gates/test_g_<nome>.py.
            "prova_que_morde": _prova_que_morde(morde_mod, nome) if na_raiz.is_file() else None,
            "leis": sorted(leis.get(nome, [])),
        })
    return gates, invisiveis


def coletar_contratos() -> list[dict]:
    fontes = [p for p in _py_vivos(RAIZ) if "test" not in p.name]
    textos = {p: _ler(p) for p in fontes}
    contratos = []
    for schema in sorted((COMPARTILHADO / "specs").glob("*.schema.json")):
        dados = json.loads(_ler(schema))
        contratos.append({
            "id": schema.name.replace(".schema.json", ""),
            "titulo": dados.get("title", ""),
            "usado_por": sorted(_rel(p) for p, t in textos.items() if schema.name in t),
        })
    return contratos


# ── Receita da tríade (orquestrador_sincrono.py) ─────────────────────────

def _lista_de_chamada(no: ast.List) -> list[str] | None:
    """Devolve os tokens após 'ecossistema.py' numa lista literal de comando."""
    itens = [e.value if isinstance(e, ast.Constant) and isinstance(e.value, str) else "<var>"
             for e in no.elts]
    if "ecossistema.py" not in itens:
        return None
    return itens[itens.index("ecossistema.py") + 1:]


def _caminho_interno(no: ast.BinOp) -> str | None:
    """Detecta ROOT_DIR / "tools" / ... (atalho que pula a CLI da ferramenta)."""
    partes = []
    while isinstance(no, ast.BinOp) and isinstance(no.op, ast.Div):
        if isinstance(no.right, ast.Constant):
            partes.append(str(no.right.value))
        no = no.left
    partes.reverse()
    return "/".join(partes) if partes and partes[0] == "tools" else None


def _compara_fluxo(teste) -> bool:
    """True para `self.fluxo == <n>`."""
    return (isinstance(teste, ast.Compare) and isinstance(teste.left, ast.Attribute)
            and teste.left.attr == "fluxo" and isinstance(teste.comparators[0], ast.Constant))


def _chamadas_do_no(no: ast.AST) -> tuple[list[list[str]], list[str]]:
    chamadas, internos = [], []
    for sub in ast.walk(no):
        if isinstance(sub, ast.List):
            tokens = _lista_de_chamada(sub)
            if tokens:
                chamadas.append(tokens)
        elif isinstance(sub, ast.BinOp):
            caminho = _caminho_interno(sub)
            if caminho:
                internos.append(caminho)
    # ast.walk visita cada pedaço de `a / b / c`; fica só o caminho completo.
    internos = sorted({c for c in internos if not any(o.startswith(c + "/") for o in internos)})
    return chamadas, internos


def coletar_receita() -> dict:
    arvore = ast.parse(_ler(ORQUESTRADOR))
    metodos = {n.name: n for n in ast.walk(arvore) if isinstance(n, ast.FunctionDef)}
    fluxos = {1: "pure", 2: "open", 3: "freedom"}
    etapas = []
    for nome in sorted(n for n in metodos if n.startswith("etapa_")):
        metodo = metodos[nome]
        por_fluxo = {}
        for no in metodo.body:
            teste = getattr(no, "test", None)
            while isinstance(no, ast.If) and _compara_fluxo(teste):
                n_fluxo = teste.comparators[0].value
                por_fluxo[fluxos.get(n_fluxo, str(n_fluxo))] = _chamadas_do_no(ast.Module(no.body, []))
                no = no.orelse[0] if no.orelse else None
                teste = getattr(no, "test", None)
        chamadas, internos = _chamadas_do_no(metodo)
        etapas.append({
            "etapa": nome,
            "descricao": (ast.get_docstring(metodo) or "").splitlines()[0],
            "chamadas_cli": chamadas,
            "chamadas_por_fluxo": {k: v[0] for k, v in sorted(por_fluxo.items())},
            "atalhos_internos": internos,
            "chama_alguma_ferramenta": bool(chamadas),
        })
    return {"arquivo": _rel(ORQUESTRADOR), "etapas": etapas}


# ── Encaixe dinâmico (via --help real) ───────────────────────────────────

def _help(tokens: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "ecossistema.py", *tokens, "--help"],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=120,
    )
    return proc.returncode, proc.stdout + proc.stderr


def _aceita_posicional(texto_help: str) -> bool:
    """Lê a linha `Usage:` do Click: `Usage: x [OPTIONS] IDEIA` aceita, `Usage: x [OPTIONS]` não."""
    for linha in texto_help.splitlines():
        if linha.lower().startswith("usage:"):
            resto = linha.split(None, 2)[2] if len(linha.split(None, 2)) > 2 else ""
            return bool(resto.replace("[OPTIONS]", "").strip())
    return True


def verificar_encaixes(receita: dict, ferramentas: list[dict]) -> list[dict]:
    comandos_por_atalho = {f["chamada"].split()[-1]: set(f["comandos"]) for f in ferramentas}
    resultados, vistos = [], set()
    for etapa in receita["etapas"]:
        for tokens in etapa["chamadas_cli"]:
            chave = tuple(tokens)
            if chave in vistos or not tokens:
                continue
            vistos.add(chave)
            atalho, resto = tokens[0], tokens[1:]
            sub = resto[0] if resto and not resto[0].startswith("-") else None
            comandos = comandos_por_atalho.get(atalho, set())
            alvo = [atalho, sub] if sub and sub in comandos else [atalho]
            rc, texto = _help(alvo)
            flags = [t for t in resto if t.startswith("--")]
            faltando = [f for f in flags if f not in set(RE_FLAG.findall(texto))]
            problemas = []
            if rc != 0:
                problemas.append(f"--help saiu com exit {rc}")
            if sub and comandos and sub not in comandos:
                problemas.append(f"subcomando '{sub}' não existe (a ferramenta tem: {', '.join(sorted(comandos))})")
            if sub and not comandos and not _aceita_posicional(texto):
                problemas.append(f"'{sub}' passado como argumento, mas a ferramenta não aceita argumento posicional")
            if faltando:
                problemas.append(f"flags inexistentes: {', '.join(faltando)}")
            resultados.append({
                "etapa": etapa["etapa"],
                "chamada": "ecossistema.py " + " ".join(tokens),
                "encaixa": not problemas,
                "problemas": problemas,
            })
    return resultados


# ── Achados ──────────────────────────────────────────────────────────────

def _dona(caminho: str) -> str:
    partes = caminho.split("/")
    return partes[1] if partes[0] == "tools" else partes[0]


def achar_repeticoes(ferramentas, skills, gates, receita) -> dict:
    # 1. Arquivos byte-idênticos entre ferramentas diferentes.
    por_hash = defaultdict(list)
    for base in (RAIZ / "tools", RAIZ / "componentes", RAIZ / "gates", RAIZ / "core"):
        for p in _py_vivos(base):
            if p.name != "__init__.py" and p.stat().st_size and "test" not in p.name:
                por_hash[_hash(p)].append(_rel(p))
    pares = defaultdict(int)
    for caminhos in por_hash.values():
        donas = tuple(sorted({_dona(c) for c in caminhos}))
        if len(donas) > 1:
            pares[" + ".join(donas)] += 1
    identicos = [{"donas": k, "arquivos": v} for k, v in sorted(pares.items(), key=lambda x: -x[1])]

    # 2. Mesmo verbo de CLI exposto por mais de uma ferramenta.
    verbo_donas = defaultdict(list)
    for f in ferramentas:
        for c in f["comandos"]:
            verbo_donas[c].append(f["id"])
    verbos = {v: d for v, d in sorted(verbo_donas.items()) if len(d) > 1}

    # 3. Tarefa com mais de uma dona (por nome de arquivo).
    todos = [p for p in _py_vivos(RAIZ) if "test" not in p.name and not p.name.startswith("__")]
    tarefas = {}
    for tarefa, padrao in TAREFAS.items():
        rx = re.compile(padrao, re.IGNORECASE)
        achados = sorted(_rel(p) for p in todos if rx.search(p.name) and not _rel(p).startswith("docs/"))
        donas = sorted({_dona(c) for c in achados})
        if len(donas) > 1:
            tarefas[tarefa] = {"donas": donas, "arquivos": achados}

    # 4. Skills com a mesma descrição (aliases).
    por_desc = defaultdict(list)
    for s in skills:
        if s["descricao"]:
            por_desc[s["descricao"][:60].lower()].append(s["id"])
    skills_alias = sorted(v for v in por_desc.values() if len(v) > 1)

    return {
        "arquivos_identicos_entre_donas": identicos,
        "verbos_cli_repetidos": verbos,
        "tarefas_com_varias_donas": tarefas,
        "gates_mesmo_nome_codigo_diferente": sorted(g["id"] for g in gates if g["versoes_distintas"] > 1),
        "skills_mesma_descricao": skills_alias,
        "etapas_sem_ferramenta": [e["etapa"] for e in receita["etapas"] if not e["chama_alguma_ferramenta"]],
        "etapas_com_atalho_interno": {e["etapa"]: e["atalhos_internos"]
                                      for e in receita["etapas"] if e["atalhos_internos"]},
    }


def gerar(com_encaixe: bool = True) -> dict:
    ferramentas = coletar_ferramentas()
    skills_terceiros = coletar_skills_terceiros()
    skills = coletar_skills(skills_terceiros)
    gates, declaracoes_invisiveis = coletar_gates()
    receita = coletar_receita()
    catalogo = {
        "versao": 1,
        "gerado_por": "scripts/catalogo_pecas.py",
        "totais": {},
        "ferramentas": ferramentas,
        "skills": skills,
        "skills_terceiros": skills_terceiros,
        "leis": coletar_leis(),
        "lente_15d": coletar_lente_15d(),
        "oficina": coletar_oficina(),
        "scripts": coletar_scripts(),
        "moldes_entrega": coletar_moldes_entrega(),
        "harnesses": coletar_harnesses(),
        "comandos_slash": coletar_comandos_slash(),
        "mcps": coletar_mcps(ferramentas),
        "hooks": coletar_hooks(),
        "gates": gates,
        "contratos": coletar_contratos(),
        "receita_triade": receita,
        "encaixes": verificar_encaixes(receita, ferramentas) if com_encaixe else None,
    }
    catalogo["achados"] = achar_repeticoes(ferramentas, skills, gates, receita)
    catalogo["achados"]["declaracoes_de_lei_invisiveis_ao_meta_gate"] = declaracoes_invisiveis
    catalogo["totais"] = {
        "ferramentas": len(ferramentas),
        "comandos_cli": sum(len(f["comandos"]) for f in ferramentas),
        "skills": len(skills),
        "leis": len(catalogo["leis"]),
        "lente_15d": len(catalogo["lente_15d"]["dimensoes"]),
        "oficina": len(catalogo["oficina"]["planos"]),
        "scripts": len(catalogo["scripts"]),
        "moldes_entrega": len(catalogo["moldes_entrega"]),
        "harnesses": len(catalogo["harnesses"]["harnesses"]),
        "skills_nossas": sum(1 for s in skills if not s["terceiro"]),
        "skills_terceiros_copiadas": sum(1 for s in skills if s["terceiro"]),
        "skills_terceiros_registradas": len(skills_terceiros),
        "comandos_slash": len(catalogo["comandos_slash"]),
        "mcps_registrados": len(catalogo["mcps"]["registrados_mcp_json"]),
        "mcps_internos": len(catalogo["mcps"]["internos_das_ferramentas"]),
        "hooks": len(catalogo["hooks"]),
        "gates_nomes": len(gates),
        "gates_arquivos": sum(len(g["copias"]) for g in gates),
        "contratos": len(catalogo["contratos"]),
        "etapas_receita": len(receita["etapas"]),
        "encaixes_quebrados": None if not com_encaixe
        else sum(1 for e in catalogo["encaixes"] if not e["encaixa"]),
    }
    return catalogo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gera o catálogo de peças do Ecossistema AIDD.")
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    parser.add_argument("--sem-encaixe", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    texto = json.dumps(gerar(com_encaixe=not args.sem_encaixe), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        atual = args.saida.read_text(encoding="utf-8") if args.saida.is_file() else ""
        if atual != texto:
            print(f"[DESATUALIZADO] {args.saida} difere do código. Rode: python scripts/catalogo_pecas.py")
            return 1
        print(f"[OK] {args.saida} em dia com o código.")
        return 0
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(texto, encoding="utf-8")
    print(f"[OK] Catálogo gravado em {args.saida}")
    return 0


if __name__ == "__main__":
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")
    sys.exit(main())
