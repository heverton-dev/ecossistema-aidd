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
HARNESSES = [h for h in (".agents", ".claude", ".gemini", ".cursor", ".opencode", ".mimocode", ".codebuddy", ".windsurf")
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
  e Na Casa para fornecer o rigor técnico, os caminhos absolutos dos arquivos no disco e as 11 dimensões
  milimetricamente auditadas). Cobre com precisão cirúrgica as 8 Ferramentas Macro, as {N_SKILLS} Micro-Ferramentas (Skills),
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

### Na Casa (A Foto Técnica Rigorosa e as 11 Dimensões)
- **Caminho Físico no Disco:** [`{m['caminho']}`](file:///{Path(ROOT_DIR / m['caminho']).resolve().as_posix()})
- **Arquivo Canônico de Regras:** [`{m['caminho']}/AGENTS.md`](file:///{Path(ROOT_DIR / m['caminho'] / 'AGENTS.md').resolve().as_posix()})

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
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/{s_id}`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* `G_SKILL_ROT.py` confere se todo caminho, script e comando citado no `SKILL.md` existe de verdade.
  6. *Scripts 0 LLM:* {s_scripts}
  7. *Hooks:* {HOOK_SKILL_ROT} Distribuição aos harnesses via `python ecossistema.py components sync --tipo todos`.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.
""")

# Parte III: os quality gates globais
partes.append(f"""
# PARTE III: OS {N_GATES} GUARDIÕES INCORRUPTÍVEIS (QUALITY GATES)

## Na Festa
Imagine {N_GATES} cães de guarda robóticos sentados na saída da fábrica. Cada um tem um sensor diferente. Um cheira se tem segredo vazando, outro mede a espessura da parede, outro confere se tem botão quebrado e outro morde o pneu para ver se está furado. Se um único guarda latir (der exit 1), o portão de saída se tranca imediatamente e ninguém sai até consertar!

## Na Casa (A Matriz dos {N_GATES} Quality Gates Canônicos)
Localização canônica: `gates/G_*.py`
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
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* {('Argumentos CLI: ' + ', '.join('`' + f + '`' for f in g['flags'])) if g['flags'] else 'Sem argumentos de CLI (roda sobre o repositório inteiro).'}
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* {g['hook']}
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Nenhum — o portão não depende de servidor MCP para rodar.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).
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
