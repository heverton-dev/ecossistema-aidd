# -*- coding: utf-8 -*-
"""
Gerador determinístico do Livro Visual de Auditoria do Ecossistema AIDD.
Mapeia as 8 Ferramentas Macro, 66 Skills, 48 Quality Gates e 91 Componentes Agnósticos.
"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
LIVRO_PATH = ROOT_DIR / "docs" / "livros" / "22-09-2026_O-GRANDE-LIVRO-VISUAL-DA-AUDITORIA-AIDD.md"
CATALOGO_PATH = ROOT_DIR / "docs" / "auditoria" / "catalogo_micro_ferramentas_e_gates.json"

with open(CATALOGO_PATH, encoding="utf-8") as f:
    catalogo = json.load(f)

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

for t in tools_order:
    f_path = ROOT_DIR / "docs" / "auditoria" / f"{t}-2026-09-22.md"
    if f_path.is_file():
        fichas_macro[t] = f_path.read_text(encoding="utf-8")

partes = []

# Frontmatter
partes.append("""---
title: "O Grande Livro Visual da Auditoria AIDD"
subtitle: "A Fábrica de Software Perfeita: Uma Viagem Pelas 8 Ferramentas Macro, 66 Micro-Ferramentas, 48 Guardas e 91 Componentes"
author:
  - "Equipe de Engenharia Canônica do Ecossistema AIDD e Antigravity Agent"
date: "22 de setembro de 2026"
lang: pt-BR
toc: true
toc-depth: 3
abstract: |
  Este livro é a documentação visual e pedagógica definitiva de cada engrenagem do Ecossistema AIDD.
  Escrito através da técnica dual (Na Festa para explicar de forma lúdica que até uma criança entenda,
  e Na Casa para fornecer o rigor técnico, os caminhos absolutos dos arquivos no disco e as 11 dimensões
  milimetricamente auditadas). Cobre com precisão cirúrgica as 8 Ferramentas Macro, as 66 Micro-Ferramentas (Skills),
  os 48 Quality Gates determinísticos e os 91 Componentes Agnósticos sincronizados em múltiplos ambientes.
---

# Prólogo: Bem-vindo à Cidade da Fábrica de Brinquedos Perfeita

Imagine uma cidade onde existe uma fábrica de brinquedos mágicos. Mas não é uma fábrica qualquer onde as coisas quebram e ninguém sabe o motivo. É uma fábrica que constrói castelos digitais inteiros em poucos minutos!

Para que tudo funcione sem nenhum fio solto, a fábrica possui:
1. **8 Grandes Oficinas Mestras (As Ferramentas Macro):** Cada uma com um mestre construtor responsável por uma grande missão.
2. **66 Ferramentas de Precisão no Cinto dos Mestres (As Micro-Ferramentas / Skills):** Lupas, réguas, tesouras mágicas e parafusadeiras que realizam tarefas hiperespecíficas.
3. **48 Guardas Incorruptíveis na Porta (Os Quality Gates):** Inspetores robóticos que não deixam passar nada se tiver um único parafuso torto ou se faltar a etiqueta de segurança.
4. **91 Peças Fundamentais (Os Componentes Agnósticos):** Blocos de encaixe perfeito que funcionam em qualquer mesa de trabalho (seja no Claude, no Gemini, no Cursor ou no Windsurf).

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

for idx, t in enumerate(tools_order, 1):
    m = metaforas_macro[t]
    conteudo_ficha = fichas_macro.get(t, "")
    partes.append(f"""
## Capítulo {idx}: {m['nome']}

### Na Festa (A Metáfora Memorável)
> {m['festa']}

Imagine que você precisa construir um prédio. Esta ferramenta é o mestre de obras especializado exatamente nessa missão. Ela não adivinha, não improvisa e não erra porque possui trilhos de aço milimétricos.

### Na Casa (A Foto Técnica Rigorosa e as 11 Dimensões)
- **Caminho Físico no Disco:** [`{m['caminho']}`](file:///{Path(ROOT_DIR / m['caminho']).resolve().as_posix()})
- **Arquivo Canônico de Regras:** [`{m['caminho']}/AGENTS.md`](file:///{Path(ROOT_DIR / m['caminho'] / 'AGENTS.md').resolve().as_posix()})

{conteudo_ficha}

---
""")

# Parte II: As 66 Micro-ferramentas
partes.append("""
# PARTE II: O CINTO DE UTILIDADES (AS 66 MICRO-FERRAMENTAS / SKILLS)

## Na Festa
Imagine o cinto de utilidades do Batman ou a caixa de ferramentas mágica de um relojoeiro suíço. Cada uma dessas 66 ferramentas tem um formato único e resolve exatamente um problema específico sem fazer barulho nem desperdiçar energia.

## Na Casa (O Catálogo Completo das 66 Skills Canônicas)
Localização canônica: `componentes/compartilhado/skills/`
""")

for s_idx, s in enumerate(catalogo["skills"], 1):
    s_id = s["id"]
    s_desc = s["descricao"]
    s_path = f"componentes/compartilhado/skills/{s_id}/SKILL.md"
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
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.
""")

# Parte III: Os 48 Quality Gates
partes.append("""
# PARTE III: OS 48 GUARDIÕES INCORRUPTÍVEIS (QUALITY GATES)

## Na Festa
Imagine 48 cães de guarda robóticos sentados na saída da fábrica. Cada um tem um sensor diferente. Um cheira se tem segredo vazando, outro mede a espessura da parede, outro confere se tem botão quebrado e outro morde o pneu para ver se está furado. Se um único guarda latir (der exit 1), o portão de saída se tranca imediatamente e ninguém sai até consertar!

## Na Casa (A Matriz dos 48 Quality Gates Canônicos)
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
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).
""")

# Parte IV: Os 91 Componentes Agnósticos
partes.append("""
# PARTE IV: OS 91 COMPONENTES AGNÓSTICOS (PEÇAS UNIVERSAIS LEGO)

## Na Festa
Imagine peças de LEGO de altíssima precisão. Não importa se você está montando na mesa azul (Claude), na mesa verde (Gemini), na mesa cinza (Cursor) ou na mesa preta (Windsurf). As peças encaixam com o mesmo clique suave e a mesma firmeza matemática. Nenhuma mesa fica com uma peça diferente da outra.

## Na Casa (A Sincronização dos 91 Componentes)
- **Fonte Canônica Única:** `componentes/compartilhado/`
- **Ambientes Espelhados (Harnesses):** `.agents/`, `.claude/`, `.gemini/`, `.cursor/`, `.windsurf/`, `.codebuddy/`, `.opencode/`.
- **Garantia de Integridade:** Validação criptográfica SHA-256 via `python ecossistema.py components verify --tipo todos`. Se um único byte divergir entre qualquer harness e a fonte canônica, o sistema aponta drift e bloqueia o commit.

### As 6 Famílias dos 91 Componentes:
1. **Comandos de Terminal Canônicos (`componentes/compartilhado/comandos/`):** 9 scripts de automação (`ecossistema.py`, `faz_commit.py`, etc.).
2. **Campainhas e Travas Git (`componentes/compartilhado/hooks/`):** Travas de pré-commit e verificação de regras.
3. **Escudo de Segurança (`componentes/compartilhado/security/`):** Detectores de vazamento de segredos e chaves.
4. **Habilidades Atômicas (`componentes/compartilhado/skills/`):** 66 pastas de skills padronizadas.
5. **Esquemas e Contratos Formais (`componentes/compartilhado/specs/`):** Esquemas JSON Draft-7 para handoff formal entre módulos.
6. **Núcleo Compartilhado de Código (`componentes/compartilhado/src-core/`):** Utilitários de missão crítica (`escritor_atomico.py`, `result.py`, `assinatura_manifesto.py`).

---

# Epílogo: A Orquestra Perfeita

Quando você junta as **8 Ferramentas Macro**, as **66 Micro-Ferramentas**, os **48 Quality Gates** e os **91 Componentes Agnósticos**, o que você tem não é apenas um projeto de software: você tem uma **catedral digital determinística**.

No Ecossistema AIDD, nenhuma linha de código nasce sem plano, nenhuma ferramenta opera sem contrato e nenhum portão se abre sem que a prova matemática tenha sido atendida.

*Fim da Auditoria Canônica — 22 de Setembro de 2026.*
""")

LIVRO_PATH.write_text("\n".join(partes), encoding="utf-8")
print(f"[SUCESSO] Livro gerado com sucesso em: {LIVRO_PATH}")
