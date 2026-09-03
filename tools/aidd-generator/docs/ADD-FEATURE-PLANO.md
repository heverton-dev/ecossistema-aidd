# Plano de Feature — `aidd-add` : Injeção e Integração de Skills / MCPs / Rules / Specs

**Projeto:** aidd-generator
**Status:** ⏳ PLANEJADO (não implementado)
**Versão do documento:** 1.0
**Data:** 03/09/2026

---

## 1. Objetivo

Adicionar uma **nova feature** ao aidd-generator: um mecanismo **unificado** que permita
**adicionar novos artefatos** — **skills, MCPs, regras (rules), specs, hooks, configs** —
ao projeto, com:

1. **Detecção automática de camada (layer)** — o sistema identifica em que camada AIDD
   e em que parte da estrutura o item se encaixa.
2. **Criação física** nos lugares corretos da estrutura alvo.
3. **Integração ao fluxo global** — conecta o item ao pipeline/índice da ferramenta.
4. **Atualização de tudo** — reindexa, atualiza manifestos e verifica gates.

O mecanismo opera em **dois contextos**:
- **Projetos gerados** pelo aidd-generator (pós-geração).
- **No próprio motor** aidd-generator (meta, dentro de `scripts/`).

> O mesmo processo se aplica a **skill, MCP, rule, spec, hook e config** — um único fluxo,
> não implementações paralelas.

---

## 2. Conceito Central (Fluxo por item)

```
pedido do usuário ("adicionar skill de segurança cibernética")
   │
   ▼
[1] IntentRouter detecta o tipo (skill|mcp|rule|spec|hook|config) + escopo (projeto|motor)
   │
   ▼
[2] Detecção de CAMADA (HÍBRIDA)
   ├─ Heurística determinística primeiro
   │    tipo → (camada AIDD, pastas, arquivos, gates, índice)
   └─ Se ambíguo → LLM (protocolo delegado) decide a camada
   │
   ▼
[3] Materialização física (cria nos lugares certos)
   │
   ▼
[4] Integração ao fluxo global (registra no catálogo/índice/pipeline)
   │
   ▼
[5] Atualização de tudo (reindexa, atualiza manifestos, verifica gates)
   │
   ▼
Gate mecânico + pytest → sucesso (exit 0) ou erro (exit 1)
```

---

## 3. Decisões de Escopo (confirmadas com o usuário)

| # | Ponto | Decisão |
|---|-------|---------|
| 1 | **Onde opera** | **Ambos**: projetos gerados **e** o próprio motor aidd-generator, com detecção de camada em ambos. |
| 2 | **Detecção de camada** | **Híbrida**: heurística determinística primeiro; se ambíguo, delega ao LLM (protocolo delegado). |
| 3 | **Registro no plano** | **Sim**: registrar a feature como nova etapa no `PLANO-EXECUCAO-ESTRUTURADO.json`, seguindo o workflow AIDD (criterios_sucesso, gates, commits). |

---

## 4. Plano de Ação por Fases

| # | Fase | O quê | Critério de sucesso chave |
|---|------|-------|---------------------------|
| **1** | **Contrato de entrada (Schema)** | JSON Schema (Draft 2020-12) validando o pedido de adição: `tipo`, `nome`, `descricao`, `conteudo_opcional`, `escopo (projeto\|motor)`, `modo (heuristica\|llm\|hibrido)` | Schema válido; pedido mal-formado rejeitado por gate |
| **2** | **Rotas tipo → camada (heurística determinística)** | Mapeamento de cada tipo para sua camada AIDD + pastas/arquivos correspondentes (`skills/`, `mcps/`, `rules.md`, `specs/`, `hooks/`, `config`) no projeto **e** no motor | Cada tipo mapeia para ≥1 camada correta; testável sem LLM |
| **3** | **Detector híbrido de camada** (heurística + LLM) | Se o mapeamento for ambíguo, delega ao LLM via protocolo delegado (reutiliza `utils_delegacao.solicitar_llm`) e valida a resposta contra as rotas existentes | Fallback headless no timeout; resposta inválida reprova honestamente |
| **4** | **Motor de materialização** (`aidd_add` core) | Cria fisicamente o artefato nos lugares corretos da estrutura alvo (projeto **ou** motor) + opcionalmente symlink GLOBAL quando pertinente | Arquivo/estrutura realmente criada em disco; zero placeholder |
| **5** | **Integração ao fluxo global** | Registra o novo item no catálogo/índice do alvo (`_phase_XX_index.json` ou manifesto equivalente); conecta gates/hooks ao pipeline quando aplicável | Item aparece no índice real, não hardcoded |
| **6** | **Atualização & verificação** | Reindexa, atualiza manifestos, roda gates mecânicos e `pytest` | Gates passam; índice reflete o item; `pytest` verde |
| **7** | **Interface (CLI / IntentRouter)** | Novos comandos `/add-skill`, `/add-mcp`, `/add-rule`, `/add-spec` … ligados ao `SlashCommandHandler` + linguagem natural | Pedido em PT-BR dispara a injeção correta, sem decorar comando |
| **8** | **Uso-caso real (prova)** | Adicionar uma **skill de análise de segurança cibernética** num projeto gerado, além de um **MCP** e uma **rule** — validar integração ponta a ponta | Os 3 itens são detectados, materializados, integrados e indexados de verdade |

---

## 5. Detecção de Camada (Híbrida)

### 5.1 Manual de decisão (heurística determinística)

| Pedido do usuário | Camada AIDD | Pasta/estrutura alvo |
|---|---|---|
| skill (utilitário reutilizável) | Camada 5 (Bundles Modulares) | `skills/` no projeto; `~/.claude/skills` ou `scripts/` no motor |
| mcp (servidor de ferramentas) | Camada 1 (Contratos e Schemas) | `mcps/` + config de servidor |
| rule (regra/norma) | Camada 4 (Persistência Estruturada) | `rules.md` / `AGENTS.md` / `rules/` |
| spec (especificação/contrato) | Camada 1 (Contratos e Schemas) | `specs/`, `schemas/`, `docs/` |
| hook (ação automatizada) | Camada 3 (Gates Mecânicos) | `hooks/` / `.claude/hooks` |
| config (configuração) | Camada 5 / global | `config.*`, `.env.example`, `settings.json` |

> A tabela acima é a **heurística inicial**; será refinada na Fase 2 e — quando ambiguidade
> detectada — a Fase 3 delega ao LLM.

### 5.2 Verdade de verificação

- **Zero alucinação:** nenhum mapeamento inventado; cada camada/pasta é validada contra a
  estrutura real do alvo antes de materializar.
- **Determinismo primeiro:** se é Python puro, é o caminho correto; LLM **somente** para
  ambiguidade de camada (síntese), com fallback headless no timeout (padrão já provado em
  `utils_delegacao`).

---

## 6. Reutilização (Zero Duplicidade)

Tudo já existente que será reaproveitado:

| Componente existente | Reuso na feature |
|---|---|
| `IntentRouter` / `SlashCommandHandler` (`scripts/utils_intent_router.py`, `scripts/commands/slash_gen.py`) | Detecção de tipo/escopo a partir de linguagem natural |
| `utils_delegacao.solicitar_llm` + fallback headless | LLM do detector híbrido de camada (Fase 3) |
| Padrão `Gate` / `ValidadorGates` | Gates mecânicos de validação (Fases 1, 6) |
| `ITENS_GLOBAL_COMPARTILHAVEL` / symlinks (Fase 4/5) | Materialização GLOBAL vs LOCAL de skills/mcps/hooks |
| Padrão `_phase_NN_index.json` + `PLANO-EXECUCAO-ESTRUTURADO.json` | Rastreabilidade e persistência estruturada |
| Pipeline das Fases 1-8 (`pipeline_completo.py`) | Ponto de integração ao fluxo global do motor |

---

## 7. Rastreabilidade e Workflow (padrão AIDD)

Após conclusão de cada fase (conforme `AGENTS-WORKFLOW.md`):

1. ✅ Verificar todos `criterios_sucesso`
2. ✅ Testar (`pytest`, import, demo)
3. ✅ Commitar com referência ao `PLANO-EXECUCAO-ESTRUTURADO.json` e ao `id` da etapa
4. ✅ Atualizar o JSON (status → ✅, `commit` → hash real)
5. ✅ Commitar o JSON atualizado
6. ✅ Gerar prompt para a próxima sessão

---

## 8. Interfaces de Entrada (propostas para a Fase 7)

```
/add-skill <nome> [--escopo projeto|motor]
/add-mcp <nome> [--conteudo ...]
/add-rule <nome> [--conteudo ...]
/add-spec <nome> [--conteudo ...]
/add-hook <nome>
/add-config <nome>
```

**Linguagem natural** (IntentRouter):
- *"insira uma skill de análise de segurança cibernética"*
- *"adicione um MCP de ..."*
- *"nova regra de ..."*
- *"quero um spec para ..."*
- *"adicionar config de ..."*

---

## 9. Arquivos previstos (esboço)

```
scripts/
├── aidd_add/
│   ├── __init__.py
│   ├── schema_add_request.py      # Fase 1 — contrato JSON (Draft 2020-12)
│   ├── rotas_camada.py            # Fase 2 — heurística tipo → camada/pasta
│   ├── detector_camada.py         # Fase 3 — híbrido (heurística + LLM)
│   ├── materializador.py          # Fase 4 — criação física
│   ├── integrador.py              # Fase 5 — registro no índice/global
│   ├── atualizador.py             # Fase 6 — reindex + verificação
│   ├── cli.py                     # Fase 7 — interface
│   └── gates.py                   # Gates mecânicos da feature
├── commands/
│   └── slash_add.py               # Fase 7 — novos comandos slash
tests/
└── test_aidd_add.py               # Testes reais (0 skips)
docs/
└── ADD-FEATURE-PLANO.md           # Este documento
```

---

## 10. Próximos passos

1. (Opcional) Revisar/validar este plano com o usuário.
2. Registrar a feature como **nova etapa** no `PLANO-EXECUCAO-ESTRUTURADO.json`
   (decisão de escopo #3 confirmada).
3. Iniciar **Fase 1** (Contrato de entrada / schema).
4. Seguir o workflow AIDD de commits/gates/JSON para as Fases 2-8.

---

**Referências internas:**
- Workflow detalhado: `AGENTS-WORKFLOW.md`
- Plano/banco de verdade: `PLANO-EXECUCAO-ESTRUTURADO.json`
- Protocolo LLM universal: `docs/PRINCIPIO-UNIVERSALIDADE.md`
- Lei Fundamental: `.aidd/LEI-FUNDAMENTAL-TRANSPARENCIA.md`
