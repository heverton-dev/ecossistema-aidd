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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mapa_gates  # noqa: E402  (dono e caminho de cada gate)
from escopo_escrita_mapas import ForaDoEscopo, garantir_escopo  # noqa: E402
from gravacao_atomica_mapas import gravar_lote  # noqa: E402
from resiliencia_mapas import ler_texto, relatar_falha  # noqa: E402  (retry de I/O e falha em JSON)
from telemetria_mapas import Medicao, medir  # noqa: E402  (uma linha JSON por execução)
from pastas_ferramentas import ferramenta_do_caminho, pastas  # noqa: E402  (ciclo-03 VSA)

RAIZ = Path(__file__).resolve().parent.parent
SAIDA_PADRAO = RAIZ / "docs" / "auditoria" / "mapa-pecas" / "catalogo-pecas.json"
COMPARTILHADO = RAIZ / "componentes" / "compartilhado"
ORQUESTRADOR = RAIZ / "scripts" / "orquestrador_sincrono.py"
DEPENDENCIAS = RAIZ / "modulos" / "04-nucleo-compartilhado" / "contracts" / "dependencias_externas.json"

# Pastas que são exemplos/sandboxes copiados, não peças vivas.
IGNORAR = ("materiais-extras", "sandbox-forge-teste", ".venv", "node_modules", "__pycache__", "dist", "build", ".codebuddy", "package-lock.json")

# Ponto de entrada de cada ferramenta (espelha os cmd_* de ecossistema.py).
ENTRADAS = {
    "aidd-forge": ("forge", "aidd_forge/cli.py"),
    "aidd-planner": ("planner", "src/cli.py"),
    "aidd-pure": ("pure-motor", "scripts/pipeline_completo.py"),
    "aidd-open": ("open-motor", "scripts/pipeline_factory.py"),
    "aidd-freedom": ("freedom-motor", "aidd_freedom/cli.py"),
    "aidd-master": ("master", "scripts/aidd.py"),
    "aidd-enterprise": ("enterprise", "scripts/aidd.py"),
    "aidd-ops": ("ops", "scripts/pipeline_ops.py"),
}

# Tarefas com sua respectiva dona canônica e padrão de arquivo
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

DONAS_TAREFAS = {
    "barrar-segredos": "gates",
    "compat-harness": "componentes",
    "injetar-componentes": "aidd-enterprise",
    "detectar-stack-camada": "aidd-forge",
    "auditar-conformidade": "gates",
    "docker-compose": "aidd-ops",
    "gerar-frontend": "aidd-pure",
    "ponte-orca": "componentes",
    "escrita-atomica": "gates",
    "resultado-monad": "aidd-master",
}

DONAS_MOLDES = {
    "agents": "aidd-master",
    "cookiecutter-scaffold": "aidd-master",
    "core": "aidd-master",
    "gates": "aidd-forge",
    "rules": "aidd-forge",
    "static": "aidd-master",
    "v2": "aidd-master",
}

DONAS_VERBOS = {
    "add-module": "aidd-master",
    "apply": "aidd-master",
    "audit": "gates",
    "bench": "aidd-master",
    "compose": "aidd-master",
    "compose-orca": "aidd-master",
    "deploy": "aidd-ops",
    "export": "aidd-planner",
    "export-frontend": "aidd-master",
    "heal": "aidd-master",
    "init": "aidd-forge",
    "inject": "aidd-enterprise",
    "plan": "aidd-planner",
    "prompt": "aidd-master",
    "refine-module": "aidd-master",
    "scaffold-infra": "aidd-ops",
    "setup": "aidd-master",
    "status": "ecossistema",
    "test": "aidd-master",
    "verificar-drift": "aidd-enterprise",
}

# Gates com implementações especializadas por ferramenta local documentadas
GATES_ESPECIALIZADOS = {"G_INJECT", "G_HARNESS_COMPAT"}

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
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except (FileNotFoundError, OSError):
        return ""


def _hash(p: Path) -> str:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:12]
    except (FileNotFoundError, OSError):
        return ""


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
    for nome, rel in sorted(pastas().items()):
        pasta = RAIZ / rel
        if not pasta.is_dir() or nome not in ENTRADAS:
            continue
        atalho, entrada = ENTRADAS[nome]
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
    """Skills de terceiros registradas em modulos/04-nucleo-compartilhado/contracts/dependencias_externas.json (instaladas
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


def _nome_mcp(nome: str) -> str:
    """mobbin_mcp e mobbin-mcp são o mesmo servidor: compara sem caixa e com '_' = '-'."""
    return nome.lower().replace("_", "-")


def coletar_mcps(ferramentas: list[dict]) -> dict:
    """MCPs registrados no .mcp.json e MCPs de código próprio, unidos sem duplicar.

    Código próprio = os `mcps/*/server.py` de cada ferramenta, as pastas
    componentes/compartilhado/mcps/*/server.py e os servidores do .mcp.json cujo
    argumento é um .py do repositório. Duplicata = mesmo caminho ou mesmo nome.
    """
    servidores = {}
    mcp_json = RAIZ / ".mcp.json"
    if mcp_json.is_file():
        servidores = json.loads(_ler(mcp_json)).get("mcpServers", {})
    registrados = sorted(servidores)
    configs = " ".join(_ler(RAIZ / n) for n in (".mcp.json", "opencode.jsonc", "mimocode.jsonc")
                       if (RAIZ / n).is_file())
    candidatos = [(Path(c).parent.name, f["id"], c) for f in ferramentas for c in f["mcps_proprios"]]
    candidatos += [(p.parent.name, "componentes", _rel(p)) for p in sorted((COMPARTILHADO / "mcps").glob("*/server.py"))]
    for nome, dados in sorted(servidores.items()):
        for arg in dados.get("args") or []:
            if str(arg).endswith(".py") and (RAIZ / str(arg)).is_file():
                caminho = Path(str(arg)).as_posix()
                candidatos.append((nome, ferramenta_do_caminho(caminho) or caminho.split("/")[0], caminho))
    internos, vistos = [], set()
    for nome, dona, caminho in candidatos:
        if caminho in vistos or _nome_mcp(nome) in vistos:
            continue
        vistos |= {caminho, _nome_mcp(nome)}
        internos.append({"id": nome, "ferramenta": dona, "caminho": caminho,
                         "registrado_em_config": nome in configs or caminho in configs})
    return {"registrados_mcp_json": registrados, "internos_das_ferramentas": internos}


def coletar_hooks() -> list[dict]:
    """Gatilhos do .claude/settings.json e todo .claude/hooks/*.py que nenhum gatilho chama.

    Nunca lê o .claude/settings.local.json: ele não é versionado (não existe nas
    worktrees nem nas outras máquinas), então o catálogo mudaria de máquina para
    máquina e o --check de frescor (catalogo_em_dia) quebraria.
    """
    hooks = []
    settings = RAIZ / ".claude" / "settings.json"
    if settings.is_file():
        for evento, grupos in json.loads(_ler(settings)).get("hooks", {}).items():
            for grupo in grupos:
                for h in grupo.get("hooks", []):
                    comando = h.get("command", "")
                    script = re.search(r"[\w./-]+\.(py|sh|cmd)", comando)
                    hooks.append({
                        "evento": evento,
                        "matcher": grupo.get("matcher", ""),
                        "script": script.group(0) if script else comando[:80],
                        "status": "ligado no settings.json",
                    })
    ligados = {Path(h["script"]).name for h in hooks}
    for p in sorted((RAIZ / ".claude" / "hooks").glob("*.py")):
        if p.name not in ligados:
            hooks.append({"evento": "sem gatilho", "matcher": "", "script": _rel(p),
                          "status": "sem gatilho no settings.json"})
    return hooks


def _gates_no_pre_commit() -> set[str]:
    cfg = RAIZ / ".pre-commit-config.yaml"
    return set(re.findall(r"gates/(G_\w+)\.py", _ler(cfg))) if cfg.is_file() else set()


# Pastas de gates do ecossistema (cada gate na fatia dona, MAPA-GATES.json).
PASTAS_DE_GATES_DO_ECOSSISTEMA = {
    "modulos/01-governanca-e-qualidade/gates",
    "modulos/02-triade-motores/fluxo-01-pure/gates",
    "modulos/02-triade-motores/fluxo-02-open/gates",
    "modulos/02-triade-motores/fluxo-03-freedom/gates",
    "modulos/03-plataforma-e-entrega/gates",
    "modulos/04-nucleo-compartilhado/gates",
}


def _papel_gate(p: Path) -> str:
    """Onde o guarda trabalha: ecossistema (raiz), ferramenta, entrega (vai no app) ou componente."""
    partes = p.relative_to(RAIZ).parts
    if partes[0] == "gates" or (partes[0] == "modulos" and partes[-2] == "gates"
                                and "/".join(partes[:-1]) in PASTAS_DE_GATES_DO_ECOSSISTEMA):
        return "ecossistema"
    if "templates" in partes:
        return "entrega"
    return "ferramenta" if ferramenta_do_caminho("/".join(partes)) else "componente"


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
    sys.path.insert(0, str(RAIZ / "modulos" / "01-governanca-e-qualidade" / "gates"))  # meta-guardas moram na fatia 01 (MAPA-GATES.json)
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
    manifesto = json.loads(_ler(RAIZ / "modulos" / "04-nucleo-compartilhado" / "contracts" / "manifesto_harnesses.json"))
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
    """Cada molde de entrega (<pasta da ferramenta>/templates/<molde>/): o que vai junto com o app gerado."""
    moldes = []
    templates = [t for rel in pastas().values()
                 for t in [RAIZ / rel / "templates", *(RAIZ / rel).glob("aidd_*/templates")] if t.is_dir()]
    for tpl in sorted(templates):
        for sub in sorted(p for p in tpl.iterdir() if p.is_dir() and p.name not in IGNORAR):
            arquivos = [f for f in sub.rglob("*") if f.is_file() and not any(x in IGNORAR for x in f.parts)]
            dona = ferramenta_do_caminho(_rel(tpl))
            moldes.append({
                "ferramenta": dona,
                "molde": sub.name,
                "caminho": _rel(sub),
                "arquivos": len(arquivos),
                "dona_canonica": DONAS_MOLDES.get(sub.name, dona),
            })
    return moldes

GERADORES_DE_DOC = {"catalogo_pecas", "mapa_visual", "livro_mapas", "achados_ciclo"}


def coletar_scripts() -> list[dict]:
    """Cada script de scripts/: o que faz (docstring) e quem o chama (painel, commit, guardas, outros scripts, testes)."""
    fontes = {"painel": [RAIZ / "ecossistema.py"],
              "commit": [RAIZ / ".pre-commit-config.yaml", RAIZ / ".githooks" / "pre-commit"],
              "guardas": _caminhos_dos_gates(),
              "scripts": sorted((RAIZ / "scripts").glob("*.py")),
              "testes": sorted((RAIZ / "tests").rglob("test_*.py")) + sorted((RAIZ / "scripts").glob("test_*.py"))
              + sorted(t for p in {g.parent for g in _caminhos_dos_gates()} for t in p.glob("test_*.py"))}
    # Geradores de documentação citam scripts como dado (texto do mapa/livro), não os chamam.
    textos = {grupo: [(p, _ler(p)) for p in arquivos if p.is_file() and p.stem not in GERADORES_DE_DOC]
              for grupo, arquivos in fontes.items()}
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
FASES_CICLO = (("laudo_inicial", ("LAUDO-15D-INICIAL.md", "DIAGNOSTICO.md", "LAUDO-INICIAL.md")),
               ("plano_evolucao", ("PLANO-EVOLUCAO.md",)),
               ("laudo_revisado", ("LAUDO-15D-REVISADO.md", "LAUDO-REVISADO.md")),
               ("dod", ("DOD.md",)))


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
        for arquivo in ("LAUDO-15D-REVISADO.md", "LAUDO-REVISADO.md", "LAUDO-15D-INICIAL.md", "LAUDO-INICIAL.md", "DIAGNOSTICO.md"):
            if arquivo in nomes:
                notas = RE_NOTA_LAUDO.findall(_ler(d / arquivo))
                if notas:
                    nota = notas[-1].replace(",", ".")
                    break
        ciclos.append({"alvo": d.parent.name, "ciclo": d.name, "caminho": _rel(d),
                       "fases": {chave: any(a in nomes for a in (arqs if isinstance(arqs, tuple) else (arqs,)))
                                 for chave, arqs in FASES_CICLO}, "nota": nota})
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
    trecho_inicial = texto.strip()[:30].lower()
    if "implementado" in trecho_inicial or "aprovado" in trecho_inicial:
        return "ok"
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
        for arquivo in ("LAUDO-15D-REVISADO.md", "LAUDO-REVISADO.md", "LAUDO-15D-INICIAL.md", "LAUDO-INICIAL.md", "DIAGNOSTICO.md"):
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

def _caminhos_dos_gates() -> list[Path]:
    """Todos os gates do MAPA-GATES.json (vazio numa árvore sem mapa)."""
    try:
        return sorted(mapa_gates.caminhos(RAIZ))
    except (KeyError, OSError, ValueError):
        return []


def _caminho_do_gate(nome: str) -> Path:
    """Caminho do gate na fatia dona (MAPA-GATES.json); fora do mapa, um caminho inexistente."""
    try:
        return mapa_gates.caminho(nome, RAIZ)
    except (KeyError, OSError, ValueError):
        return RAIZ / "gates" / f"{nome}.py"


def _prova_que_morde(morde_mod, nome: str) -> bool:
    teste = morde_mod.encontrar_arquivo_teste(f"{nome}.py", str(_caminho_do_gate(nome).parent))
    return bool(teste) and morde_mod.auditar_teste_de_falha(teste, executar=False)[0]


def coletar_gates() -> tuple[list[dict], list[str]]:
    no_pre_commit = _gates_no_pre_commit()
    leis_mod, morde_mod = _meta_gates()
    leis, invisiveis = _leis_por_gate(leis_mod, _ler(RAIZ / "AGENTS.md"))
    por_nome = defaultdict(list)
    for base in (RAIZ / "modulos", RAIZ / "componentes"):
        for p in _py_vivos(base):
            if p.name.startswith("G_") and p.suffix == ".py":
                por_nome[p.stem].append(p)
    gates = []
    for nome in sorted(por_nome):
        copias = sorted(por_nome[nome])
        no_dono = _caminho_do_gate(nome)
        principal = no_dono if no_dono.is_file() else copias[0]
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
            "no_pre_commit": nome in no_pre_commit and no_dono.is_file(),
            # Só medido para a raiz: é lá que a Lei #13 exige gates/test_g_<nome>.py.
            "prova_que_morde": _prova_que_morde(morde_mod, nome) if no_dono.is_file() else None,
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
    """Detecta ROOT_DIR / "modulos" / ... (atalho que pula a CLI da ferramenta)."""
    partes = []
    while isinstance(no, ast.BinOp) and isinstance(no.op, ast.Div):
        if isinstance(no.right, ast.Constant):
            partes.append(str(no.right.value))
        no = no.left
    partes.reverse()
    return "/".join(partes) if partes and partes[0] == "modulos" else None


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


# Número do fluxo (self.fluxo no orquestrador) -> nome do fluxo da Tríade.
FLUXOS_TRIADE = {1: "pure", 2: "open", 3: "freedom"}


def coletar_receita() -> dict:
    arvore = ast.parse(_ler(ORQUESTRADOR))
    metodos = {n.name: n for n in ast.walk(arvore) if isinstance(n, ast.FunctionDef)}
    fluxos = FLUXOS_TRIADE
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


# ── Pipelines, módulos VSA e agentes ─────────────────────────────────────

RE_PASSO_DE_FLUXO = re.compile(r"Step (\d+) of the (.+?) flow", re.IGNORECASE)
RE_SKILL_PIPELINE = re.compile(r"\bruns the\b[^.]*\bpipeline\b", re.IGNORECASE)
RE_FASE = re.compile(r"^###\s+Phase\s+\d+:\s*(.+)$", re.MULTILINE)
RE_SECAO_DE_ETAPAS = re.compile(r"^##\s+(?:Execution|Steps|Workflow|Protocol)\b.*$", re.MULTILINE)
RE_ITEM_NUMERADO = re.compile(r"^\d+\.\s+(.+)$")


def _etapas_da_skill(texto: str) -> list[str]:
    """Etapas declaradas no SKILL.md: os títulos '### Phase N: x' ou, sem eles, os itens
    numerados de primeiro nível da primeira seção Execution/Steps/Workflow/Protocol."""
    fases = [f.strip() for f in RE_FASE.findall(texto)]
    if fases:
        return fases
    secao = RE_SECAO_DE_ETAPAS.search(texto)
    if not secao:
        return []
    etapas = []
    for linha in texto[secao.end():].splitlines():
        if linha.startswith("## "):
            break
        item = RE_ITEM_NUMERADO.match(linha)
        if item:
            frase = re.split(r"(?<=[\w`)\]])(?:\.\s+(?=[A-Z])|:\s)", item.group(1).replace("**", ""), maxsplit=1)[0]
            etapas.append(frase.strip().rstrip(".:")[:90])
    return etapas


def coletar_pipelines(receita: dict | None = None) -> list[dict]:
    """Lê os pipelines diretamente do contrato único e vivo PIPELINES.json (D0)."""
    caminho = RAIZ / "modulos" / "04-nucleo-compartilhado" / "contracts" / "PIPELINES.json"
    if not caminho.exists():
        return []
    dados = json.loads(_ler(caminho))
    pipelines = []
    for pipe in dados.get("pipelines", []):
        etapas = []
        for et in pipe.get("etapas", []):
            etapas.append({
                "id": et.get("id", ""),
                "peca": et.get("peca", et.get("id", "")),
                "titulo": et.get("titulo", ""),
                "chamada": et.get("chamada", "")
            })
        item = dict(pipe)
        item["origem"] = pipe.get("origem", pipe.get("comando", "modulos/04-nucleo-compartilhado/contracts/PIPELINES.json"))
        item["etapas"] = etapas
        pipelines.append(item)
    return pipelines


def verificar_contrato_vivo_pipelines(pipelines_extras: list[str] | None = None) -> list[str]:
    """Detector do contrato vivo (D0): compara pipelines conhecidos contra PIPELINES.json."""
    caminho = RAIZ / "modulos" / "04-nucleo-compartilhado" / "contracts" / "PIPELINES.json"
    if not caminho.exists():
        return ["Contrato PIPELINES.json nao encontrado"]
    dados = json.loads(_ler(caminho))
    declarados = {pipe.get("id") for pipe in dados.get("pipelines", [])}
    conhecidos = {
        "pure", "open", "freedom",
        "auditoria-4f", "evolucao", "melhoria-plan-orchestrate",
        "aidd-ingest", "aidd-ops", "aidd-pipeline",
        "bateria-gates", "despacho-vsa", "run-plan"
    }
    if pipelines_extras:
        conhecidos.update(pipelines_extras)
    divergencias = []
    for pipe in sorted(conhecidos):
        if pipe not in declarados:
            divergencias.append(f"Pipeline '{pipe}' detectado no codigo mas nao declarado em PIPELINES.json")
    return divergencias


def _primeira_frase_readme(pasta: Path) -> str:
    readme = pasta / "README.md"
    if not readme.is_file():
        return ""
    return next((x.strip() for x in _ler(readme).splitlines() if x.strip() and not x.startswith(("#", ">"))), "")


def coletar_modulos() -> list[dict]:
    """Cada área de modulos/ (fatia vertical do VSA) e as subpastas dela: ferramentas que
    moram ali (MAPA-DONOS-FERRAMENTAS.json), guardas e arquivos .py."""
    donas = pastas()
    areas = []
    for area in sorted(p for p in (RAIZ / "modulos").iterdir() if p.is_dir() and not p.name.startswith(("_", "."))):
        fatias = []
        for fatia in sorted(p for p in area.iterdir() if p.is_dir() and p.name not in IGNORAR
                            and not p.name.startswith(("_", "."))):
            rel = _rel(fatia)
            py = _py_vivos(fatia)
            fatias.append({
                "id": fatia.name,
                "caminho": rel,
                "ferramentas": sorted(n for n, pasta in donas.items() if pasta == rel or pasta.startswith(rel + "/")),
                "guardas": len([p for p in py if p.name.startswith("G_")]),
                "arquivos_py": len([p for p in py if "test" not in p.name]),
            })
        areas.append({"id": area.name, "caminho": _rel(area), "descricao": _primeira_frase_readme(area),
                      "fatias": fatias})
    return areas


def coletar_agentes() -> list[dict]:
    """Templates de agentes (templates/agents/*.md) da área de plataforma e entrega, agrupados
    por nome; versão por conteúdo (A, B…), como nos guardas: mesma letra = cópia idêntica."""
    base = RAIZ / "modulos" / "03-plataforma-e-entrega"
    por_nome = defaultdict(list)
    for pasta in sorted(base.rglob("templates/agents")):
        if pasta.is_dir() and not _ignorado(pasta.relative_to(RAIZ)):
            for arq in sorted(pasta.glob("*.md")):
                por_nome[arq.stem].append(arq)
    agentes = []
    for nome, arquivos in sorted(por_nome.items()):
        versoes = {}
        for arq in arquivos:
            versoes.setdefault(_hash(arq), chr(ord("A") + len(versoes)))
        titulo = next((x.lstrip("# ").strip() for x in _ler(arquivos[0]).splitlines() if x.startswith("#")), "")
        agentes.append({
            "id": nome,
            "papel": titulo,
            "copias": [{"caminho": _rel(a), "ferramenta": ferramenta_do_caminho(_rel(a)) or "", "versao": versoes[_hash(a)]}
                       for a in arquivos],
            "versoes_distintas": len(versoes),
        })
    return agentes


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
    return ferramenta_do_caminho(caminho) or caminho.split("/")[0]


def _eh_copia_governada(caminhos: list[str]) -> bool:
    """Verifica se os arquivos idênticos pertencem ao cluster de sincronismo governado
    (baseline do núcleo compartilhado, templates de entrega e gates certificados)."""
    cluster = {"aidd-master", "aidd-enterprise", "aidd-open", "aidd-forge", "aidd-pure", "componentes", "gates"}
    donas = {_dona(c) for c in caminhos}
    return donas.issubset(cluster)


def achar_repeticoes(ferramentas, skills, gates, receita) -> dict:
    # 1. Arquivos byte-idênticos entre ferramentas diferentes (não governados).
    por_hash = defaultdict(list)
    for base in (RAIZ / "modulos", RAIZ / "componentes", RAIZ / "gates", RAIZ / "core"):
        for p in _py_vivos(base):
            if p.name != "__init__.py" and p.stat().st_size and "test" not in p.name:
                por_hash[_hash(p)].append(_rel(p))
    pares = defaultdict(int)
    for caminhos in por_hash.values():
        donas = tuple(sorted({_dona(c) for c in caminhos}))
        if len(donas) > 1 and not _eh_copia_governada(caminhos):
            pares[" + ".join(donas)] += 1
    identicos = [{"donas": k, "arquivos": v} for k, v in sorted(pares.items(), key=lambda x: -x[1])]

    # 2. Mesmo verbo de CLI exposto por mais de uma ferramenta (sem dona canônica declarada).
    verbo_donas = defaultdict(list)
    for f in ferramentas:
        for c in f["comandos"]:
            verbo_donas[c].append(f["id"])
    verbos = {v: d for v, d in sorted(verbo_donas.items()) if len(d) > 1 and v not in DONAS_VERBOS}

    # 3. Tarefa com mais de uma dona (sem dona canônica declarada).
    todos = [p for p in _py_vivos(RAIZ) if "test" not in p.name and not p.name.startswith("__")]
    tarefas = {}
    for tarefa, padrao in TAREFAS.items():
        if tarefa in DONAS_TAREFAS:
            continue
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
        "gates_mesmo_nome_codigo_diferente": sorted(
            g["id"] for g in gates
            if len({c["versao"] for c in g["copias"] if c["papel"] != "entrega"}) > 1
            and g["id"] not in GATES_ESPECIALIZADOS
        ),
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
        "pipelines": coletar_pipelines(receita),
        "modulos": coletar_modulos(),
        "agentes": coletar_agentes(),
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
        "pipelines": len(catalogo["pipelines"]),
        "modulos": len(catalogo["modulos"]),
        "agentes": len(catalogo["agentes"]),
        "encaixes_quebrados": None if not com_encaixe
        else sum(1 for e in catalogo["encaixes"] if not e["encaixa"]),
    }
    return catalogo


def _texto(catalogo: dict) -> str:
    return json.dumps(catalogo, ensure_ascii=False, indent=2) + "\n"


# Uma varredura por processo para o mesmo arquivo em disco (chave: caminho, mtime, tamanho):
# o índice pergunta o frescor uma vez por mapa, e cada varredura custa segundos.
_FRESCOR: dict[tuple, tuple[bool, list[str]]] = {}


def catalogo_em_dia(raiz: Path = RAIZ, caminho: Path | None = None) -> tuple[bool, list[str]]:
    """Gera o catálogo em memória e compara com o JSON em disco.

    Devolve (em_dia, chaves de primeiro nível que divergem). A varredura é sempre do
    checkout deste script, então `raiz` tem de ser RAIZ (num repositório de teste, roda
    o script da própria cópia). Catálogo gravado com --sem-encaixe (encaixes = null) é
    comparado com uma geração também sem encaixes.
    """
    if Path(raiz).resolve() != RAIZ:
        raise ValueError(f"catalogo_em_dia varre {RAIZ}; para {raiz}, rode o scripts/catalogo_pecas.py de lá")
    caminho = Path(caminho or SAIDA_PADRAO)
    if not caminho.is_file():
        return False, ["<arquivo ausente>"]
    estado = caminho.stat()
    chave = (str(caminho.resolve()), estado.st_mtime_ns, estado.st_size)
    if chave not in _FRESCOR:
        atual = ler_texto(caminho)
        try:
            disco = json.loads(atual)
        except ValueError:
            disco = {}
        memoria = gerar(com_encaixe=not isinstance(disco, dict) or disco.get("encaixes") is not None)
        texto = _texto(memoria)
        if atual == texto:
            _FRESCOR[chave] = (True, [])
        else:
            disco = disco if isinstance(disco, dict) else {}
            memoria = json.loads(texto)  # mesma forma do disco (tuplas viram listas)
            divergentes = sorted(k for k in set(disco) | set(memoria) if disco.get(k) != memoria.get(k))
            _FRESCOR[chave] = (False, divergentes or ["<formatação>"])
    return _FRESCOR[chave]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gera o catálogo de peças do Ecossistema AIDD.")
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    parser.add_argument("--sem-encaixe", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    with medir("catalogo", "catalogo", args.saida) as medicao:
        medicao.exit_code = _gerar_ou_conferir(args, medicao)
    return medicao.exit_code


def _gerar_ou_conferir(args: argparse.Namespace, medicao: Medicao) -> int:
    if not args.check:
        try:
            garantir_escopo(args.saida)
        except ForaDoEscopo as erro:
            print(f"[ERRO] {erro}")
            return 1
    texto = _texto(gerar(com_encaixe=not args.sem_encaixe))
    if args.check:
        atual = ler_texto(args.saida) if args.saida.is_file() else ""
        if atual != texto:
            print(f"[DESATUALIZADO] {args.saida} difere do código. Rode: python scripts/catalogo_pecas.py")
            return 1
        print(f"[OK] {args.saida} em dia com o código.")
        return 0
    try:
        gravar_lote({args.saida: texto})
        medicao.arquivos_gravados = 1
    except (OSError, ValueError) as erro:
        return relatar_falha(erro, "catalogo", "catalogo", args.saida)
    print(f"[OK] Catálogo gravado em {args.saida}")
    return 0


if __name__ == "__main__":
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")
    sys.exit(main())
