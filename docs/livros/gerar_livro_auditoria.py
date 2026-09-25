# -*- coding: utf-8 -*-
"""
Gerador determinístico do Livro Visual de Auditoria do Ecossistema AIDD.

Tudo o que é contagem ou catálogo é lido do disco no momento da geração — skills em
componentes/compartilhado/skills/, portões em gates/, componentes nas 6 famílias de
componentes/compartilhado/ — para o livro nunca congelar números que mudam a cada
commit. As fichas das 8 ferramentas macro são o registro histórico da auditoria de
22/09/2026 (docs/auditoria/historico_auditorias/); erros factuais conhecidos nelas são
corrigidos na hora de embutir e listados na errata do livro.

Uso:  python docs/livros/gerar_livro_auditoria.py [DD-MM-AAAA]
"""

import ast
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DIR_HISTORICO = ROOT_DIR / "docs" / "auditoria" / "historico_auditorias"
DIR_SKILLS = ROOT_DIR / "componentes" / "compartilhado" / "skills"
DIR_COMPARTILHADO = ROOT_DIR / "componentes" / "compartilhado"
DATA_FICHAS = "2026-09-22"
MESES = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro")

DATA = sys.argv[1] if len(sys.argv) > 1 else date.today().strftime("%d-%m-%Y")
_d, _m, _a = DATA.split("-")
DATA_EXTENSO = f"{int(_d)} de {MESES[int(_m) - 1]} de {_a}"
LIVRO_PATH = ROOT_DIR / "docs" / "livros" / f"{DATA}_O-GRANDE-LIVRO-VISUAL-DA-AUDITORIA-AIDD.md"
PRE_COMMIT = (ROOT_DIR / ".pre-commit-config.yaml").read_text(encoding="utf-8")

# Nomes errados nas fichas históricas de 22/09 -> nome real no disco (errata do livro).
ERRATA_FICHAS = {
    "`G_BLOQUEAR_SEGREDO`": "`G_BLOQUEAR_SEGREDOS`",
    "`G_CYBERSECURITY`": "`G_CYBERSECURITY_OWASP`",
    "`G_FACTORY_INPUT` (validação estrita do schema do plano de infraestrutura), "
    "`G_FACTORY_OUTPUT` (verificação do manifesto de entrega), `G_FACTORY_DETERMINISTIC` "
    "(garantia de zero LLM nas fases 1, 4, 5 e 6).":
        "`G_FACTORY_ANALYSIS`, `G_FACTORY_COMPOSE`, `G_FACTORY_ENV`, `G_FACTORY_INIT_DB`, "
        "`G_FACTORY_INTEGRATION` e `G_FACTORY_MVP` (em `tools/aidd-factory/gates/`). "
        "`G_FACTORY_INPUT`, `G_FACTORY_OUTPUT` e `G_FACTORY_DETERMINISTIC` são rótulos de "
        "invariante no `AGENTS.md`, não arquivos de portão.",
    "catálogo de ferramentas (`data/catalogo_ferramentas.json`)":
        "requisitos de recursos (`data/requisitos_recursos.json`)",
}


def _frontmatter_descricao(skill_md: Path) -> str:
    """Lê o campo description do frontmatter YAML de um SKILL.md."""
    texto = skill_md.read_text(encoding="utf-8")
    m = re.search(r"^description:\s*(.+)$", texto, re.M)
    return m.group(1).strip().strip("\"'") if m else "(sem descrição no frontmatter)"


def _missao_do_portao(gate_py: Path) -> str:
    """Primeira linha útil da docstring do portão (pula cabeçalho e separadores)."""
    doc = ast.get_docstring(ast.parse(gate_py.read_text(encoding="utf-8-sig"))) or ""
    for linha in doc.splitlines():
        linha = linha.strip()
        if not linha or set(linha) <= set("=-") or linha.upper().startswith("ECOSSISTEMA AIDD"):
            continue
        if re.match(rf"^{re.escape(gate_py.stem)}(\.py)?\s*[—-]", linha):
            continue
        return linha
    return "(sem docstring)"


def _flags_do_portao(gate_py: Path) -> list:
    return sorted(set(re.findall(r"add_argument\(\s*[\"'](--[\w-]+)", gate_py.read_text(encoding="utf-8"))))


def _hook_do_portao(nome: str) -> str:
    # Cada hook local do pre-commit é um bloco que começa em "- id:".
    sem_comentarios = "\n".join(l for l in PRE_COMMIT.splitlines() if not l.lstrip().startswith("#"))
    bloco = next((b for b in re.split(r"\n\s*- id:", sem_comentarios) if f"gates/{nome}.py" in b), None)
    if bloco is None:
        return "Não está no `.pre-commit-config.yaml`: roda sob demanda (`python gates/" + nome + ".py`)."
    if re.search(r"stages:\s*\[?\s*manual", bloco):
        return "Registrado no `.pre-commit-config.yaml` com `stages: [manual]` (roda só quando chamado)."
    return "Roda automaticamente no commit via `.pre-commit-config.yaml`."


catalogo = {
    "skills": [
        {"id": d.name, "descricao": _frontmatter_descricao(d / "SKILL.md")}
        for d in sorted(DIR_SKILLS.iterdir(), key=lambda x: x.name.lower())
        if (d / "SKILL.md").is_file()
    ],
    "gates": [
        {"id": g.name, "descricao": _missao_do_portao(g), "flags": _flags_do_portao(g),
         "hook": _hook_do_portao(g.stem)}
        for g in sorted((ROOT_DIR / "gates").glob("G_*.py"), key=lambda x: x.name.lower())
    ],
}
FAMILIAS = ("comandos", "hooks", "security", "skills", "specs", "src-core")
contagem_familia = {
    f: sum(1 for x in (DIR_COMPARTILHADO / f).iterdir() if x.name != "__pycache__")
    for f in FAMILIAS
}
N_SKILLS = len(catalogo["skills"])
N_GATES = len(catalogo["gates"])
N_COMP = sum(contagem_familia.values())
HOOK_SKILL_ROT = _hook_do_portao("G_SKILL_ROT")
# ---------------------------------------------------------------------------
# Lente 15-D (docs/auditoria/TEMPLATE-AUDITORIA-FERRAMENTA.md): D1..D15.
# Cada dimensão é preenchida com evidência lida do disco. Em skill, a evidência é
# o que o SKILL.md DECLARA (texto), não prova de comportamento; o livro diz isso.
# ---------------------------------------------------------------------------
DIMENSOES_15D = (
    ("D1", "Contratos e Regras"), ("D2", "Input e Gatilhos"), ("D3", "Raio de Impacto e Isolamento"),
    ("D4", "Componentes e Fractalidade"), ("D5", "Visão e Escopo"), ("D6", "O que o Estágio Faz"),
    ("D7", "O que o Estágio Recebe"), ("D8", "O que o Estágio Processa"), ("D9", "O que o Estágio Entrega"),
    ("D10", "Orquestração e Topologia"), ("D11", "Tratamento de Exceções e Fallback"),
    ("D12", "Observabilidade e Frugalidade"), ("D13", "Quality Gates (Portões)"),
    ("D14", "Critério de Rejeição (Rollback)"), ("D15", "Output Consolidado e Handoff"),
)
CHAMADAS_ESCRITA = {"write_text", "write_bytes", "unlink", "rmtree", "rmdir", "mkdir", "makedirs",
                    "copyfile", "copy2", "copytree"}
# Nomes ambíguos (str.replace, list.remove, dict.copy) só contam quando chamados em os/shutil.
CHAMADAS_ESCRITA_OS = {"remove", "replace", "rename", "move", "copy"}
NOMES_LOCAIS = ({p.stem for p in (ROOT_DIR / "gates").glob("*.py")}
                | {p.stem for p in (ROOT_DIR / "scripts").glob("*.py")}
                | {p.stem for p in (DIR_COMPARTILHADO / "src-core").glob("*.py")})
COMANDOS_TEXTO = {c.stem: c.read_text(encoding="utf-8", errors="replace")
                  for c in (DIR_COMPARTILHADO / "comandos").glob("*.md")}


def _laudos_15d(nome: str) -> list:
    return sorted(p.relative_to(ROOT_DIR).as_posix()
                  for p in (ROOT_DIR / "docs" / "auditoria" / nome).glob("ciclo-*/LAUDO-15D-*.md"))


def _analise_portao(gate_py: Path) -> dict:
    arvore = ast.parse(gate_py.read_text(encoding="utf-8-sig"))
    escritas, imports, n_try, n_print, usa = set(), set(), 0, 0, set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Try):
            n_try += 1
        elif isinstance(no, (ast.Import, ast.ImportFrom)):
            nomes = [a.name for a in no.names] if isinstance(no, ast.Import) else [no.module or ""]
            for n in nomes:
                raiz = n.split(".")[0]
                usa.add(raiz)
                if raiz in NOMES_LOCAIS or n.split(".")[-1] in NOMES_LOCAIS:
                    imports.add(n.split(".")[-1])
        elif isinstance(no, ast.Call):
            f = no.func
            nome = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            if nome == "print":
                n_print += 1
            if nome in CHAMADAS_ESCRITA:
                escritas.add(nome)
            elif nome in CHAMADAS_ESCRITA_OS and isinstance(f, ast.Attribute) \
                    and isinstance(f.value, ast.Name) and f.value.id in ("os", "shutil"):
                escritas.add(f"{f.value.id}.{nome}")
            if nome == "open" and len(no.args) > 1 and isinstance(no.args[1], ast.Constant) \
                    and any(c in str(no.args[1].value) for c in "wax"):
                escritas.add("open(w)")
    tecnica = [t for t, mods in (("AST Python", {"ast"}), ("expressão regular", {"re"}),
                                 ("JSON Schema", {"jsonschema"}), ("subprocesso", {"subprocess"}),
                                 ("YAML", {"yaml"}), ("hash criptográfico", {"hashlib", "hmac"}))
               if usa & mods]
    teste = next((t.relative_to(ROOT_DIR).as_posix() for base in ("gates", "tests")
                  for t in (ROOT_DIR / base).glob(f"test_{gate_py.stem.lower()}*.py")), None)
    return {"escritas": sorted(escritas), "imports": sorted(imports), "try": n_try, "print": n_print,
            "tecnica": tecnica, "teste": teste}


def _cita(texto: str, grupo: str, termos: dict) -> str:
    """Fato conferível: quais termos o texto do SKILL.md cita (citar não é implementar)."""
    achados = [rotulo for rotulo, rx in termos.items() if re.search(rx, texto, re.I)]
    if achados:
        return f"o `SKILL.md` cita {', '.join(f'`{a}`' for a in achados)}."
    return f"o `SKILL.md` não cita {grupo}."


TERMOS_15D = {
    "D3": ("worktree nem isolamento", {"worktree": r"\bworktrees?\b", "isolamento": r"\bisola(mento|do|r)\b|\bisolat"}),
    "D11": ("fallback, retry nem indisponibilidade", {"fallback": r"\bfallback\b", "retry": r"\bretr(y|ies)\b",
                                                      "indisponível": r"indispon[ií]vel|\bunavailable\b"}),
    "D12": ("log, telemetria nem `secoes/`", {"log": r"\blog(s|ging)?\b", "telemetria": r"telemetr", "secoes/": r"secoes/"}),
    "D14": ("rollback nem limpeza", {"rollback": r"\brollback\b", "reverter": r"\brevert", "limpeza": r"\blimpeza\b|\bclean ?up\b"}),
    "D15": ("handoff", {"handoff": r"\bhandoff\b"}),
}


def _dimensoes_skill(s_id: str, s_desc: str, scripts: list) -> list:
    md = (DIR_SKILLS / s_id / "SKILL.md").read_text(encoding="utf-8", errors="replace")
    comandos = sorted(c for c, txt in COMANDOS_TEXTO.items() if c == s_id or s_id in txt)
    gate_proprio = sorted(g.name for g in (ROOT_DIR / "gates").glob("G_*.py")
                          if s_id.replace("-", "_").lower() in g.stem.lower())
    mcps = sorted(set(re.findall(r"code-review-graph|context7|graphify|chrome", md)))
    c = {d: _cita(md, g, t) for d, (g, t) in TERMOS_15D.items()}
    scripts_txt = (", ".join(f"`{x}`" for x in scripts) + " em `scripts/`") if scripts else "nenhum script próprio (roteiro em `SKILL.md`)"
    laudos = _laudos_15d(s_id)
    return [
        f"frontmatter `name`/`description` no `SKILL.md`; distribuída pela fonte única `componentes/compartilhado/skills/{s_id}/`.",
        ("gatilho pela `description` e pelos comandos " + ", ".join(f"`/{c}`" for c in comandos)) if comandos
        else "gatilho pela `description` do frontmatter (nenhum arquivo em `comandos/` aponta para ela).",
        c["D3"],
        f"scripts: {scripts_txt}; MCPs citados: {', '.join(f'`{m}`' for m in mcps) if mcps else 'nenhum'}.",
        s_desc,
        "executar o roteiro do `SKILL.md`" + (" e os scripts locais" if scripts else "") + ".",
        "o pedido do usuário ou do agente que a aciona.",
        "roteiro seguido pelo modelo" + (" + scripts determinísticos" if scripts else " (sem motor próprio)") + ".",
        "saída dos scripts locais e o que o roteiro orienta produzir (ver D5)." if scripts
        else "o que o roteiro do `SKILL.md` orienta produzir (ver D5); não há motor próprio que grave arquivo.",
        "espelhada nos harnesses por `python ecossistema.py components sync --tipo todos`.",
        c["D11"],
        c["D12"],
        f"`G_SKILL_ROT` confere caminhos e comandos citados. {HOOK_SKILL_ROT}"
        + (f" Portão próprio: {', '.join(f'`{g}`' for g in gate_proprio)}." if gate_proprio else " Sem portão próprio."),
        c["D14"],
        c["D15"]
        + (f" Laudo 15-D: {', '.join(f'`{l}`' for l in laudos)}." if laudos else " Ainda sem laudo 15-D próprio."),
    ]


def _dimensoes_portao(g: dict) -> list:
    a = _analise_portao(ROOT_DIR / "gates" / g["id"])
    flags = ("flags " + ", ".join(f"`{f}`" for f in g["flags"])) if g["flags"] else "sem flags (roda sobre o repositório inteiro)"
    escrita = ("grava ou remove arquivos (" + ", ".join(f"`{e}`" for e in a["escritas"]) + ")") if a["escritas"] \
        else "nenhuma chamada de escrita ou remoção de arquivo no próprio código"
    if "subprocesso" in a["tecnica"]:
        escrita += "; executa subprocessos, cujos efeitos não entram nesta contagem"
    no_commit = g["hook"].startswith("Roda automaticamente")
    return [
        "Lei #2 (saída binária) e Lei #13 (prova que morde).",
        f"{flags}. {g['hook']}",
        escrita + ".",
        ("importa módulos do repositório: " + ", ".join(f"`{m}`" for m in a["imports"])) if a["imports"]
        else "não importa módulos do repositório (autocontido).",
        g["descricao"].rstrip(":"),
        "auditar o que D5 descreve numa única passada (portão de estágio único).",
        "os arquivos passados por argumento ou, sem eles, o repositório." if g["flags"] else "o repositório inteiro.",
        ("técnica: " + ", ".join(a["tecnica"]) + ".") if a["tecnica"] else "técnica: leitura direta de arquivos.",
        "`exit 0` (aprovado) ou `exit 1` (bloqueado).",
        "acionado pelo pre-commit." if no_commit else "acionado só quando alguém o chama (não bloqueia o commit sozinho).",
        f"{a['try']} bloco(s) `try` no código." if a["try"] else "nenhum bloco `try`: erro inesperado derruba o portão (e o commit reprova).",
        f"{a['print']} saída(s) `print` para o terminal.",
        (f"teste próprio: `{a['teste']}`; " if a["teste"] else "sem teste com o nome do portão; ")
        + "o meta-portão `G_PORTAO_PROVA_QUE_MORDE` confere que ele reprova de verdade.",
        "`exit 1` bloqueia o commit." if no_commit else "`exit 1` só bloqueia quando o portão é chamado.",
        "o código de saída e as mensagens no terminal.",
    ]


def _lista_15d(valores: list) -> str:
    return "\n".join(f"  - **{d}. {n}:** {v}" for (d, n), v in zip(DIMENSOES_15D, valores))


HARNESSES = [h for h in (".agents", ".claude", ".codebuddy", ".codex", ".cursor", ".gemini", ".kiro",
                           ".mimocode", ".opencode", ".qoder", ".windsurf")
             if (ROOT_DIR / h).is_dir()]

# Ler fichas das 8 ferramentas macro
fichas_macro = {}
tools_order = [
    "aidd-forge",
    "aidd-planner",
    "aidd-generator",
    "aidd-factory",
    "aidd-bridge",
    "aidd-master",
    "aidd-enterprise",
    "aidd-ops"
]

errata_aplicada = []
for t in tools_order:
    f_path = DIR_HISTORICO / f"{t}-{DATA_FICHAS}.md"
    if not f_path.is_file():
        raise FileNotFoundError(f"Ficha histórica ausente: {f_path}")
    texto = f_path.read_text(encoding="utf-8")
    for errado, certo in ERRATA_FICHAS.items():
        if errado in texto:
            texto = texto.replace(errado, certo)
            errata_aplicada.append((t, errado, certo))
    fichas_macro[t] = texto

partes = []

# Frontmatter
partes.append(f"""---
title: "O Grande Livro Visual da Auditoria AIDD"
subtitle: "A Fábrica de Software Perfeita: Uma Viagem Pelas 8 Ferramentas Macro, {N_SKILLS} Micro-Ferramentas, {N_GATES} Guardas e {N_COMP} Componentes"
author:
  - "Equipe de Engenharia Canônica do Ecossistema AIDD e Antigravity Agent"
date: "{DATA_EXTENSO}"
lang: pt-BR
toc: true
toc-depth: 3
abstract: |
  Este livro é a documentação visual e pedagógica definitiva de cada engrenagem do Ecossistema AIDD.
  Escrito através da técnica dual (Na Festa para explicar de forma lúdica que até uma criança entenda,
  e Na Casa para fornecer o rigor técnico, os caminhos dos arquivos no disco e as 15 dimensões
  da Lente 15-D, preenchidas com evidência lida do repositório). Cobre com precisão cirúrgica as 8 Ferramentas Macro, as {N_SKILLS} Micro-Ferramentas (Skills),
  os {N_GATES} Quality Gates determinísticos e os {N_COMP} Componentes Agnósticos sincronizados em múltiplos ambientes.
---

# Prólogo: Bem-vindo à Cidade da Fábrica de Brinquedos Perfeita

Imagine uma cidade onde existe uma fábrica de brinquedos mágicos. Mas não é uma fábrica qualquer onde as coisas quebram e ninguém sabe o motivo. É uma fábrica que constrói castelos digitais inteiros em poucos minutos!

Para que tudo funcione sem nenhum fio solto, a fábrica possui:
1. **8 Grandes Oficinas Mestras (As Ferramentas Macro):** Cada uma com um mestre construtor responsável por uma grande missão.
2. **{N_SKILLS} Ferramentas de Precisão no Cinto dos Mestres (As Micro-Ferramentas / Skills):** Lupas, réguas, tesouras mágicas e parafusadeiras que realizam tarefas hiperespecíficas.
3. **{N_GATES} Guardas Incorruptíveis na Porta (Os Quality Gates):** Inspetores robóticos que não deixam passar nada se tiver um único parafuso torto ou se faltar a etiqueta de segurança.
4. **{N_COMP} Peças Fundamentais (Os Componentes Agnósticos):** Blocos de encaixe perfeito que funcionam em qualquer mesa de trabalho (seja no Claude, no Gemini, no Cursor, no OpenCode ou no Mimo).

Neste livro, nós vamos passear por cada canto dessa fábrica e tirar uma **FOTO** detalhada de cada peça!

---

# PARTE I: AS 8 FERRAMENTAS MACRO (AS GRANDES OFICINAS)

## Como ler as fichas desta parte: 11 dimensões antigas, 15 dimensões atuais

As fichas das 8 ferramentas são o registro da auditoria de {DATA_FICHAS}, feita antes de o ecossistema adotar a **Lente 15-D**. Elas usam uma matriz de **11 dimensões**. O padrão atual tem **15** (D1 a D15, lista completa na Parte V). A tabela mostra onde cada dimensão antiga cai na lente atual:

| Dimensão antiga (ficha de {DATA_FICHAS}) | Onde cai na Lente 15-D |
| :--------------------------------------- | :--------------------- |
| 1. Recebe (Input)                        | D2 Input e Gatilhos · D7 O que o Estágio Recebe |
| 2. Cria / Processa                       | D6 O que o Estágio Faz · D8 O que o Estágio Processa |
| 3. Entrega (Output)                      | D9 O que o Estágio Entrega · D15 Output Consolidado e Handoff |
| 4. Configurações                         | D2 Input e Gatilhos |
| 5. Guardas (Gates)                       | D13 Quality Gates |
| 6. Scripts determinísticos (0 LLM)       | D8 O que o Estágio Processa |
| 7. Hooks · 8. Agents · 9. Skills · 10. MCPs | D4 Componentes e Fractalidade |
| 11. Rules (`AGENTS.md`)                  | D1 Contratos e Regras |

**Seis dimensões da Lente 15-D não existiam na matriz antiga:** D3 Raio de Impacto e Isolamento, D5 Visão e Escopo, D10 Orquestração e Topologia, D11 Tratamento de Exceções e Fallback, D12 Observabilidade e Frugalidade e D14 Critério de Rejeição (Rollback). Nas 8 ferramentas elas continuam **sem avaliação** até cada uma passar pelo seu primeiro ciclo 15-D (`python ecossistema.py audit-4f --manifest <json>`).
""")

metaforas_macro = {
    "aidd-forge": {
        "nome": "AIDD Forge — O Altar da Fundação e os Guardiões das Leis",
        "festa": "O Mestre Ferreiro que prepara o chão da oficina, coloca a bigorna, estende as regras na parede e tranca a porta para ninguém entrar bagunçando.",
        "caminho": "tools/aidd-forge"
    },
    "aidd-planner": {
        "nome": "AIDD Planner — A Mesa do Arquiteto e o Livro de Receitas",
        "festa": "O Grande Arquiteto que escuta o sonho do cliente, desenha a planta baixa em papel milimetrado com todas as medidas, cores e quartos, e entrega uma receita que qualquer cozinheiro consegue seguir.",
        "caminho": "tools/aidd-planner"
    },
    "aidd-generator": {
        "nome": "AIDD Generator — O Trem Autônomo de 8 Vagões (Fluxo 01: Do Zero Puro)",
        "festa": "Um trem mágico com 8 vagões sequenciais. Ele recebe a ideia pura em uma ponta e, vagão por vagão (pesquisa, desenho, teste, programação), entrega uma cidade inteira de brinquedo montada e funcionando.",
        "caminho": "tools/aidd-generator"
    },
    "aidd-factory": {
        "nome": "AIDD Factory — A Linha de Montagem de Peças Prontas (Fluxo 02: Open-Source)",
        "festa": "O Mestre Montador que pega os melhores motores de brinquedo já inventados no mundo (motores abertos) e os conecta perfeitamente com cabos fortes para criar um veículo superpotente sem reinventar a roda.",
        "caminho": "tools/aidd-factory"
    },
    "aidd-bridge": {
        "nome": "AIDD Bridge — A Ponte da Libertação (Fluxo 03: Desacoplamento Low-Code)",
        "festa": "O Chaveiro Libertador que resgata os brinquedos que estavam presos em gaiolas com cadeados caros de empresas distantes (Lovable, Supabase), limpando-os para funcionarem livres no quintal da sua própria casa.",
        "caminho": "tools/aidd-bridge"
    },
    "aidd-master": {
        "nome": "AIDD Master — O Maestro da Harmonização Monolítica VSA",
        "festa": "O Maestro da Orquestra que garante que todos os instrumentos (fatias verticais) toquem em harmonia perfeita no mesmo salão, sem um bater no outro e com uma barreira invisível de segurança.",
        "caminho": "tools/aidd-master"
    },
    "aidd-enterprise": {
        "nome": "AIDD Enterprise — O Cofre de Alta Segurança e Selos Criptográficos",
        "festa": "O Inspetor do Cofre do Rei que confere o carimbo de ouro (assinatura digital SHA-256) em cada documento e garante que nenhum espião consiga alterar uma única linha de código.",
        "caminho": "tools/aidd-enterprise"
    },
    "aidd-ops": {
        "nome": "AIDD Ops — A Usina de Força e a Torre de Vigilância",
        "festa": "O Chefe dos Engenheiros que constrói a usina de energia (servidor VPS), liga os motores (Docker), tranca as portas com chaves fortes (SSH seguro) e coloca câmeras de vigilância 24 horas por dia (Uptime Kuma).",
        "caminho": "tools/aidd-ops"
    }
}

# Cada ferramenta tem um papel DIFERENTE na linha de produção — nunca resuma todas como
# "o mestre de obras que constrói", ou o leitor sai achando que forge/planner erguem
# parede, quando na verdade só generator/factory/bridge fazem isso. Esta frase-ponte
# amarra a metáfora da festa ao papel técnico real de cada uma, sem contradizer nenhuma.
pontes_tecnicas = {
    "aidd-forge": "Antes de qualquer parede ser erguida, é este ferreiro que crava as estacas no chão e escreve, na própria parede da oficina, as regras que toda construção futura vai ter que obedecer. Sem terreno preparado e sem regra escrita, não existe planta nem construção — é por isso que ele entra primeiro, e é por isso que ele mesmo não ergue tijolo nenhum.",
    "aidd-planner": "Com o terreno pronto e as regras na parede, é aqui que o sonho do cliente vira desenho técnico: cada cômodo, medida, porta e contrato descritos em detalhe antes de qualquer prego ser batido. O arquiteto entrega a planta — quem constrói é o próximo mestre da linha.",
    "aidd-generator": "Com a planta em mãos, este é o motor que efetivamente ergue a construção do zero: vagão por vagão, a ideia pura vira aplicação funcionando, sem depender de nenhum tijolo pré-fabricado de terceiros.",
    "aidd-factory": "Também constrói a partir da mesma planta, mas em vez de erguer tijolo por tijolo, monta a casa com módulos open-source já prontos, testados por milhares de outras obras e encaixados sob medida no projeto.",
    "aidd-bridge": "Aqui a casa já existe — só que presa a um dono que cobra aluguel para você nem abrir a porta. Este é o chaveiro que destranca as paredes de vendor lock-in e devolve as chaves de verdade para o dono real do código.",
    "aidd-master": "Com as construções de pé, é este maestro que garante que todas as alas do prédio funcionem como um único edifício coerente — nenhuma fatia vertical pisa no cano ou na fiação da vizinha.",
    "aidd-enterprise": "É o inspetor que sela cada ambiente com um lacre inviolável (assinatura criptográfica) antes de qualquer chave ser entregue para o mundo real — se o lacre estiver quebrado, a entrega não sai.",
    "aidd-ops": "É quem liga a energia do prédio já pronto, tranca as portas externas com fechaduras fortes e instala as câmeras de vigilância — para que a construção funcione 24 horas por dia sem ninguém arrombar a fechadura enquanto todos dormem.",
}

for idx, t in enumerate(tools_order, 1):
    m = metaforas_macro[t]
    ponte = pontes_tecnicas[t]
    conteudo_ficha = fichas_macro.get(t, "")
    partes.append(f"""
## Capítulo {idx}: {m['nome']}

### Na Festa (A Metáfora Memorável)
> {m['festa']}

{ponte}

### Na Casa (A Foto Técnica e a Ficha Histórica de 22/09/2026)
- **Caminho Físico no Disco:** [`{m['caminho']}`](file:///{Path(ROOT_DIR / m['caminho']).resolve().as_posix()})
- **Arquivo Canônico de Regras:** [`{m['caminho']}/AGENTS.md`](file:///{Path(ROOT_DIR / m['caminho'] / 'AGENTS.md').resolve().as_posix()})

> **Nota de leitura:** ficha histórica de {DATA_FICHAS}, na matriz antiga de **11 dimensões** (correspondência com a Lente 15-D no início desta parte); {('laudo 15-D: ' + ', '.join(_laudos_15d(Path(m['caminho']).name))) if _laudos_15d(Path(m['caminho']).name) else 'esta ferramenta ainda não passou por um ciclo 15-D.'}

{conteudo_ficha}

---
""")

# Parte II: as micro-ferramentas (skills)
partes.append(f"""
# PARTE II: O CINTO DE UTILIDADES (AS {N_SKILLS} MICRO-FERRAMENTAS / SKILLS)

## Na Festa
Imagine o cinto de utilidades do Batman ou a caixa de ferramentas mágica de um relojoeiro suíço. Cada uma dessas {N_SKILLS} ferramentas tem um formato único e resolve exatamente um problema específico sem fazer barulho nem desperdiçar energia.

## Na Casa (O Catálogo Completo das {N_SKILLS} Skills Canônicas)
Localização canônica: `componentes/compartilhado/skills/`

Cada skill abaixo é lida pela **Lente 15-D**, o padrão de auditoria do ecossistema (`docs/auditoria/TEMPLATE-AUDITORIA-FERRAMENTA.md`): D1 a D4 governança e blindagem, D5 a D10 o trabalho em si, D11 e D12 resiliência e economia, D13 a D15 validação e entrega. O gerador preenche cada dimensão lendo o disco. Em D3, D11, D12, D14 e D15 ele diz só se o texto do `SKILL.md` **cita** o assunto: citar não é implementar, e nas skills de domínio externo a citação costuma ser sobre o produto ensinado (o `retry` da `agents-sdk` é o do SDK da Cloudflare). A prova de comportamento só existe onde há laudo 15-D de um ciclo de auditoria (Parte V).
""")

for s_idx, s in enumerate(catalogo["skills"], 1):
    s_id = s["id"]
    s_desc = s["descricao"]
    s_path = f"componentes/compartilhado/skills/{s_id}/SKILL.md"
    dir_scripts = DIR_SKILLS / s_id / "scripts"
    scripts = sorted(x.name for x in dir_scripts.glob("*.py") if x.name != "__init__.py") if dir_scripts.is_dir() else []
    s_scripts = (", ".join(f"`{x}`" for x in scripts) + " em `scripts/`") if scripts else "Nenhum script próprio: a skill é um roteiro em `SKILL.md`."
    partes.append(f"""
### {s_idx}. Micro-Ferramenta: `{s_id}`
- **Foto / Identidade:** `{s_id}`
- **Caminho no Disco:** [`{s_path}`](file:///{Path(ROOT_DIR / s_path).resolve().as_posix()})
- **O que Faz (Missão Única):** {s_desc}
- **Lente 15-D desta Micro-Ferramenta:**
{_lista_15d(_dimensoes_skill(s_id, s_desc, scripts))}
""")

# Parte III: os quality gates globais
partes.append(f"""
# PARTE III: OS {N_GATES} GUARDIÕES INCORRUPTÍVEIS (QUALITY GATES)

## Na Festa
Imagine {N_GATES} cães de guarda robóticos sentados na saída da fábrica. Cada um tem um sensor diferente. Um cheira se tem segredo vazando, outro mede a espessura da parede, outro confere se tem botão quebrado e outro morde o pneu para ver se está furado. Se um único guarda latir (der exit 1), o portão de saída se tranca imediatamente e ninguém sai até consertar!

## Na Casa (A Matriz dos {N_GATES} Quality Gates Canônicos)
Localização canônica: `gates/G_*.py`

Cada guarda também é lido pela **Lente 15-D**. Aqui a evidência vem do próprio código Python, por AST: flags do `argparse`, chamadas que gravam ou apagam arquivos, módulos do repositório importados, blocos `try`, saídas `print` e se o `.pre-commit-config.yaml` o chama. Um portão é de estágio único, então D6 a D9 descrevem uma passada só.
""")

for g_idx, g in enumerate(catalogo["gates"], 1):
    g_id = g["id"]
    g_desc = g["descricao"]
    g_path = f"gates/{g_id}"
    partes.append(f"""
### {g_idx}. Guarda Incorruptível: `{g_id}`
- **Foto / Identidade:** `{g_id}`
- **Caminho no Disco:** [`{g_path}`](file:///{Path(ROOT_DIR / g_path).resolve().as_posix()})
- **Missão de Segurança:** {g_desc}
- **Lente 15-D deste Quality Gate:**
{_lista_15d(_dimensoes_portao(g))}
""")

# Parte IV: os componentes agnósticos
partes.append(f"""
# PARTE IV: OS {N_COMP} COMPONENTES AGNÓSTICOS (PEÇAS UNIVERSAIS LEGO)

## Na Festa
Imagine peças de LEGO de altíssima precisão. Não importa se você está montando na mesa azul (Claude), na mesa verde (Gemini), na mesa cinza (Cursor) ou na mesa preta (OpenCode). As peças encaixam com o mesmo clique suave e a mesma firmeza matemática. Nenhuma mesa fica com uma peça diferente da outra.

## Na Casa (A Sincronização dos {N_COMP} Componentes)
- **Fonte Canônica Única:** `componentes/compartilhado/`
- **Ambientes Espelhados (Harnesses):** {', '.join('`' + h + '/`' for h in HARNESSES)}.
- **Garantia de Integridade:** Validação criptográfica SHA-256 via `python ecossistema.py components verify --tipo todos`. Se um único byte divergir entre qualquer harness e a fonte canônica, o sistema aponta drift e bloqueia o commit.

### As 6 Famílias dos {N_COMP} Componentes:
1. **Slash Commands Canônicos (`componentes/compartilhado/comandos/`):** {contagem_familia['comandos']} especificações de comando em Markdown (`/pure`, `/forge`, `/melhoria`, etc.).
2. **Campainhas e Travas Git (`componentes/compartilhado/hooks/`):** {contagem_familia['hooks']} itens — travas de pré-commit e verificação de regras.
3. **Escudo de Segurança (`componentes/compartilhado/security/`):** {contagem_familia['security']} itens — detectores de vazamento de segredos e chaves.
4. **Habilidades Atômicas (`componentes/compartilhado/skills/`):** {contagem_familia['skills']} pastas de skills padronizadas.
5. **Esquemas e Contratos Formais (`componentes/compartilhado/specs/`):** {contagem_familia['specs']} esquemas JSON Draft-7 para handoff formal entre módulos.
6. **Núcleo Compartilhado de Código (`componentes/compartilhado/src-core/`):** {contagem_familia['src-core']} itens — utilitários de missão crítica (`escritor_atomico.py`, `result.py`, `assinatura_manifesto.py`).

---
""")

# Parte V: os ciclos de auditoria 4F, lidos do disco e do git (nunca do texto)
def _git(*args):
    r = subprocess.run(["git", *args], cwd=ROOT_DIR, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


linhas_ciclos = []
for ciclo in sorted((ROOT_DIR / "docs" / "auditoria").glob("*/ciclo-*")):
    ferramenta, nome = ciclo.parent.name, ciclo.name
    branch = f"audit/evolucao-{ferramenta}-{nome}"
    commits_fora = _git("rev-list", "--count", f"main..{branch}") if _git("rev-parse", "--verify", "-q", branch) else ""
    aprovado = bool(_git("rev-parse", "--verify", "-q", f"refs/aidd/aprovavel/evolucao-{ferramenta}-{nome}"))
    # Layout antigo (antes dos ciclos): uma branch por ticket, audit/evolucao-<ferramenta>/Fase_N_...
    legado = [b for b in _git("branch", "--format=%(refname:short)", "--list",
                              f"audit/evolucao-{ferramenta}/*").splitlines() if b]
    legado_fora = [b for b in legado if _git("rev-list", "--count", f"main..{b}") not in ("", "0")]
    revisado = (ciclo / "LAUDO-15D-REVISADO.md").exists()
    fora = bool(commits_fora and commits_fora != "0")
    construido = (ciclo / "RELATORIO-CONSTRUTOR.md").exists() or fora or bool(legado) or revisado
    fases = [
        ("1 Inspetor", (ciclo / "LAUDO-15D-INICIAL.md").exists()),
        ("2 Arquiteto", (ciclo / "PLANO-EVOLUCAO.md").exists()),
        ("3 Construtor", construido),
        ("4 Retorno", revisado),
    ]
    marcas = " · ".join(f"{f} {'feito' if ok else 'pendente'}" for f, ok in fases)
    if fora:
        onde = f"branch `{branch}` com {commits_fora} commit(s) fora da `main`"
    elif legado_fora:
        onde = f"{len(legado_fora)} branch(es) de ticket fora da `main`"
    elif legado:
        onde = f"na `main` ({len(legado)} branches de ticket, formato antigo, todas mescladas)"
    elif construido:
        onde = "na `main`"
    else:
        onde = "ainda não construído"
    linhas_ciclos.append(
        f"| `{ferramenta}/{nome}` | {marcas} | {onde} | {'sim' if aprovado else 'não'} |")

if linhas_ciclos:
    tabela_ciclos = "\n".join(linhas_ciclos)
    partes.append(f"""
# PARTE V: AS AUDITORIAS EM ANDAMENTO (OS CICLOS 4F)

## Na Festa
A fábrica não só fabrica brinquedos: de tempos em tempos ela para uma oficina inteira para revisão. Um inspetor anota os defeitos, o chefe escreve a ordem de serviço, um mecânico conserta e o inspetor volta para conferir. Enquanto o dono não assina a liberação, a oficina consertada fica numa garagem ao lado, sem voltar para a linha de produção.

## Na Casa (o estado real em {DATA_EXTENSO})
Cada rodada de auditoria de uma ferramenta é um ciclo em `docs/auditoria/<ferramenta>/ciclo-NN/`. A tabela abaixo foi montada pelo gerador olhando os arquivos de cada ciclo e o git, não copiada de relatório: a Fase 3 conta como feita quando existe `RELATORIO-CONSTRUTOR.md` ou commits na branch de evolução, e "aprovado" quer dizer que existe `refs/aidd/aprovavel/...` (o `gate_final` passou). Ciclos no formato antigo são anteriores a esse registro e aparecem como "não" mesmo já mesclados.

| Ciclo | Fases | Onde está o trabalho | `gate_final` aprovado |
| :---- | :---- | :------------------- | :-------------------: |
{tabela_ciclos}

As 15 dimensões da Lente 15-D, na ordem em que o Inspetor as preenche:

{chr(10).join(f'{i}. **{d}. {n}**' for i, (d, n) in enumerate(DIMENSOES_15D, 1))}

Nada disso entra na `main` sem aprovação humana: `python scripts/orquestrador_4f.py --manifest <json> --aprovar`.

---
""")

if errata_aplicada:
    linhas = "\n".join(f"- **{ferr}:** {errado} → {certo}" for ferr, errado, certo in errata_aplicada)
    partes.append(f"""
# Errata das Fichas de {DATA_FICHAS}

As fichas da Parte I são o registro histórico da auditoria de {DATA_FICHAS}. Estes nomes
estavam errados nelas e foram corrigidos ao gerar este livro (o arquivo histórico não foi
alterado):

{linhas}

---
""")

partes.append(f"""
# Epílogo: A Orquestra Perfeita

Quando você junta as **8 Ferramentas Macro**, as **{N_SKILLS} Micro-Ferramentas**, os **{N_GATES} Quality Gates** e os **{N_COMP} Componentes Agnósticos**, o que você tem não é apenas um projeto de software: você tem uma **catedral digital determinística**.

No Ecossistema AIDD, nenhuma linha de código nasce sem plano, nenhuma ferramenta opera sem contrato e nenhum portão se abre sem que a prova matemática tenha sido atendida.

*Fim da Auditoria Canônica — {DATA_EXTENSO}.*
""")

LIVRO_PATH.write_text("\n".join(partes), encoding="utf-8")
print(f"[SUCESSO] Livro gerado com sucesso em: {LIVRO_PATH}")
