# Feature `add-artifact` — Injetor de Capacidades no AIDD Master

> **Status:** Aprovado (aguardando implementação)
> **Data:** 03/09/2026
> **Contexto:** AIDD Master Enterprise v5.1
> **Idioma:** PT-BR

---

## 1. Objetivo

Adicionar uma nova feature ao projeto AIDD Master que permita **injetar novas capacidades** de forma **totalmente integrada ao fluxo da ferramenta**, em sua camada adequada, sem intervenção manual além do comando de gatilho.

O mecanismo é **genérico e unificado**: o mesmo processo se aplica a **qualquer tipo de package**, tratado de forma idêntica.

## 2. Escopo de Tipos Suportados

O injetor cobre (mas não se limita a) os seguintes tipos de artifacts. Cada um é tratado como **um package** com o mesmo fluxo:

| Tipo | Descrição | Camada de destino (configurável) |
| :--- | :--- | :--- |
| `skill` | Capacidade/instrução de agente (SKILL.md) | `.claude/skills/`, `.mimocode/skills/`, ... |
| `mcp` | Servidor/ferramenta Model Context Protocol | `src/core/mcp/`, `templates/`, ... |
| `rule` | Regra de governança / camada | `templates/rules/`, `.claude/`, ... |
| `spec` | Especificação técnica | `docs/specs/`, `templates/`, ... |
| `config` | Configuração / settings | raiz, `templates/`, ... |
| `agent` | Subagente especializado | `templates/agents/`, ... |

> **Decisão:** a injeção é **configurável por tipo** — cada tipo possui um **mapa de camadas** (ver Fase 1) indicando os destinos de injeção.

## 3. Funcionamento do Mecanismo (Fluxo Único)

Para **qualquer** artifact (skill, mcp, rule, spec, config, agent), o framework executa automaticamente:

1. **Detectar a camada adequada** — identifica em qual tipo/camada o artifact se encaixa (não requer o usuário informar).
2. **Criar o pacote** nos lugares corretos da estrutura (**injeção física** do pacote).
3. **Integrar ao projeto como um todo** — registro global, indexação, publicação (**integração estrutural**).
4. **Atualizar** o catálogo/registro de novas capacidades.

## 4. Gatilhos de Disparo (Ambos)

A feature pode ser acionada de duas formas:

### 4.1 Comando CLI dedicado
```bash
python scripts/aidd.py add-artifact <nome> [--tipo auto|skill|mcp|rule|spec|config|agent] [--dir <destino>]
```

### 4.2 Linguagem Natural
```bash
python scripts/aidd.py "adicione uma skill de análise de cibersegurança"
```
O sistema infere **tipo** e **nome** automaticamente a partir do prompt.

---

## 5. Fases de Implementação

### Fase 1 — Core Registry (Catálogo de Camadas)
- Criar `src/core/artifact_catalog.py`.
- Define o **mapa configurável** de tipos → camadas de injeção.
- Cada tipo declara: `tipo`, `detector` (regex/keywords), `pastas_destino` (configurável), `padrao_arquivo`, `registro_index`.

```json
{
  "skill": {"dirs": [".claude/skills", ".mimocode/skills", "templates/"], "index": "CAPABILITIES.json"},
  "mcp":   {"dirs": ["src/core/mcp/", "templates/"], "index": "MCP-REGISTRY.json"},
  "rule":  {"dirs": ["templates/rules/", ".claude/"], "index": "RULES-INDEX.json"},
  "spec":  {"dirs": ["docs/specs/", "templates/"], "index": "SPECS-INDEX.json"}
}
```

### Fase 2 — Layer Detector (Detecção Automática de Camada)
- Criar `src/core/artifact_detector.py`.
- Dado o texto/prompt, detecta **tipo** e **nome** via keywords + análise do conteúdo.

### Fase 3 — Injetor Físico (Package Injection)
- Criar `src/core/artifact_injector.py`.
- Gera o scaffold do pacote (SKILL.md, mcp.json, rule.md, spec.md...) e injeta nos destinos do mapa de camadas.
- Responsável pela **injeção física** e replicação nos mirrors.

### Fase 4 — Integração Estrutural Global (REGISTRY)
- Cria/atualiza **índice global de capacidades** (`CAPABILITIES.json`, `MCP-REGISTRY.json`, etc.).
- Integra ao `status` e ao `audit` para que a nova capacidade apareça no ecossistema.

### Fase 5 — Comandos CLI + Linguagem Natural
- Adicionar `add-artifact` em `scripts/aidd.py` (subparser + rota natural no `main()`).
- Adicionar à tabela de roteamento de intenções do `AGENTS.md`.

### Fase 6 — Validação
- Rodar `python -m pytest tests/`.
- Rodar `python scripts/run_all.py` (10 Quality Gates).
- Teste manual: `add-artifact` de uma skill de cibersegurança e verificar injeção + registro.

---

## 6. Arquivos Novos Propostos

| Arquivo | Responsabilidade |
| :--- | :--- |
| `src/core/artifact_catalog.py` | Mapa configurável de tipos → camadas |
| `src/core/artifact_detector.py` | Detecção de tipo/nome a partir do prompt |
| `src/core/artifact_injector.py` | Injeção física do pacote + mirrors |
| `src/core/artifact_registry.py` | Índice global de capacidades |
| `scripts/artifact_cli.py` (opcional) | Helpers de CLI reutilizáveis |

## 7. Qualidade / Aderência

- Respeita os Quality Gates (Result Monad, parametrização SQL, soft-delete, zero stubs).
- Padrões de comunicação via Shared Kernel (`core.*`), sem acoplamento de bounded context.
- Observabilidade via `@trace_span` nas funções críticas.
- Follows convention de pastas `src/core/` e `scripts/`.

---

## 8. Ponto de Checkpoint

Classificado como **planejado/aguardando implementação**. Antes de codificar, validar com o usuário a **lista de camadas por tipo** no mapa configurável (Fase 1).
