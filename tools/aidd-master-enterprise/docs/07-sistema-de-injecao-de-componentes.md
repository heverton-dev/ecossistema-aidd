# 07 — Sistema de Injeção Automática de Componentes

> **Projeto:** AIDD Master Enterprise
> **Status:** PLANEJADO (Aguardando Aprovação)
> **Data:** 03/09/2026

---

## 1. Objetivo

Adicionar uma nova feature ao framework que permite **adicionar novos componentes ao projeto** de forma totalmente integrada ao fluxo da ferramenta, na camada adequada.

O sistema detecta a camada onde o componente adicionado se encaixa, cria o componente nos locais apropriados dentro da estrutura, integra-o ao projeto como um todo e atualiza todos os pontos de referência globais.

**Não se limita a skills:** o mesmo processo se aplica a **MCPs, Rules, Specs, Agents, Configs e outros tipos de componentes**.

---

## 2. Confirmação do Escopo

| Tipo de Componente | Exemplo | Aplica-se o Fluxo Completo |
| :--- | :--- | :---: |
| **Skill** | Análise de cibersegurança | ✅ |
| **MCP** | Novo servidor/ferramenta MCP | ✅ |
| **Rule** | Regra Zero Trust | ✅ |
| **Spec** | Especificação de novo domínio | ✅ |
| **Agent** | Agente Security Analyst | ✅ |
| **Config** | Configuração de harness | ✅ |

Todos os 6 tipos seguem exatamente o mesmo pipeline:

1. **Detecção** → identificar o tipo do componente e a camada alvo
2. **Criação física** → gerar os arquivos nos diretórios corretos
3. **Integração global** → registrar no projeto como um todo
4. **Atualização** → sincronizar todos os pontos de referência

---

## 3. Mapeamento da Estrutura Atual (por tipo)

### 3.1 Skill

| Aspecto | Localização |
| :--- | :--- |
| **Diretórios físicos** | `.skills/<nome>/SKILL.md`<br>`.claude/skills/<nome>/SKILL.md`<br>`.agent/skills/<nome>/SKILL.md` |
| **Integração global** | `AGENTS.md`<br>`templates/core/CLAUDE.md`<br>`templates/core/AGENTS.md`<br>`templates/core/GEMINI.md` |
| **Padrão de arquivo** | Frontmatter `name` + `description` + `commands`, corpo em PT-BR |

### 3.2 MCP

| Aspecto | Localização |
| :--- | :--- |
| **Diretórios físicos** | `src/core/mcp_server.py` (registro de tools)<br>`templates/core/mcp_server.py` (template) |
| **Integração global** | `AGENTS.md`<br>`PLANO-EXECUCAO-ESTRUTURADO.json` (flag `mcp_enabled`) |
| **Contrato** | JSON-RPC 2.0, ferramentas nomeadas |

### 3.3 Rule

| Aspecto | Localização |
| :--- | :--- |
| **Diretórios físicos** | `templates/rules/<nome>.md` |
| **Integração global** | `AGENTS.md` (seção Quality Gates)<br>`templates/core/CLAUDE.md`<br>`templates/core/AGENTS.md`<br>`templates/core/GEMINI.md` |

### 3.4 Agent

| Aspecto | Localização |
| :--- | :--- |
| **Diretórios físicos** | `templates/agents/<nome>.md` |
| **Integração global** | `AGENTS.md` (seção Roteamento)<br>`templates/core/AGENTS.md`<br>`src/core/intent_router.py` (se tiver trigger) |

### 3.5 Spec

| Aspecto | Localização |
| :--- | :--- |
| **Diretórios físicos** | `templates/` ou `src/modules/<dominio>/` |
| **Integração global** | `PLANO-EXECUCAO-ESTRUTURADO.json`<br>`SPEC-ARQUITETURA.md` |

### 3.6 Config

| Aspecto | Localização |
| :--- | :--- |
| **Diretórios físicos** | `templates/core/`<br>`src/core/`<br>raiz do projeto |
| **Integração global** | `AGENTS.md`<br>arquivos de configuração dos harnesses |

---

## 4. Plano de Ação — 5 Fases

### Fase 1: Motor de Detecção de Camada

**Arquivo:** `src/core/component_registry.py`

- Criar registry com mapeamento `tipo → diretório → arquivos de integração`
- Função `detect_layer(component_type, component_name)` que resolve onde criar e onde atualizar
- Schema de metadados para cada componente (`name`, `type`, `description`, `layer`, `dependencies`)

### Fase 2: Scripts de Criação Física (6 builders)

| Script | Criação |
| :--- | :--- |
| `scripts/inject_skill.py` | `.skills/`, `.claude/skills/`, `.agent/skills/` com `SKILL.md` |
| `scripts/inject_mcp.py` | registra tool no `mcp_server.py` + template |
| `scripts/inject_rule.py` | `templates/rules/<nome>.md` |
| `scripts/inject_agent.py` | `templates/agents/<nome>.md` |
| `scripts/inject_spec.py` | spec + atualização do plano |
| `scripts/inject_config.py` | config e propagação |

### Fase 3: Integrador Global

**Arquivo:** `src/core/global_integrator.py`

Função `integrate_component(component_type, component_data)` que:

- Injeta referência no `AGENTS.md` (seção apropriada)
- Injeta referência no `templates/core/CLAUDE.md`
- Injeta referência no `templates/core/AGENTS.md`
- Injeta referência no `templates/core/GEMINI.md`
- Atualiza `intent_router.py` (se for rule/agent com trigger)
- Atualiza `PLANO-EXECUCAO-ESTRUTURADO.json` (se existir)

### Fase 4: Comando CLI `aidd inject`

Novo subcomando no `scripts/aidd.py`:

```
python scripts/aidd.py inject <tipo> <nome> [--desc "descrição"] [--layer auto|core|module|template] [--content "conteúdo ou caminho"]
```

**Exemplos:**

```
python scripts/aidd.py inject skill ciberseguranca --desc "Análise de vulnerabilidades"
python scripts/aidd.py inject mcp audit-orchestrator --desc "Orquestrador de auditoria"
python scripts/aidd.py inject rule zero-trust --desc "Regra de segurança zero trust"
python scripts/aidd.py inject agent security-analyst --desc "Agente de análise de segurança"
```

### Fase 5: Intent Router Expansão + Validação

- Adicionar padrões no `intent_router.py`:
  - "adicionar skill de X" → `inject skill X`
  - "criar mcp para Y" → `inject mcp Y`
  - "adicionar regra de Z" → `inject rule Z`
- Gate de validação `G_INJECT.py` que verifica se a injeção foi completa (arquivos criados + integrados)

---

## 5. Comandos Resumidos

| Intenção | Comando CLI |
| :--- | :--- |
| Adicionar skill | `python scripts/aidd.py inject skill <nome>` |
| Adicionar MCP | `python scripts/aidd.py inject mcp <nome>` |
| Adicionar regra | `python scripts/aidd.py inject rule <nome>` |
| Adicionar agente | `python scripts/aidd.py inject agent <nome>` |
| Adicionar spec | `python scripts/aidd.py inject spec <nome>` |
| Adicionar config | `python scripts/aidd.py inject config <nome>` |
| Validar injeção | `python scripts/run_all.py` (novo gate `G_INJECT`) |

---

## 6. Critérios de Aceite (Quality Gates)

A entrega só é considerada completa quando:

1. **Detecção correta**: o tipo do componente e a camada alvo são identificados automaticamente.
2. **Criação física completa**: todos os arquivos são gerados nos locais corretos.
3. **Integração global**: referências injetadas em todos os arquivos de governança do projeto.
4. **Consistência multi-harness**: `AGENTS.md`, `CLAUDE.md` e `GEMINI.md` sincronizados.
5. **Zero stubs**: nenhuma função vazia com `pass` ou `TODO`.
6. **Gate `G_INJECT`**: validação determinística retorna exit 0.
