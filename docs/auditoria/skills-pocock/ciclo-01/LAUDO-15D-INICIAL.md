# Template de Auditoria de Ferramenta (Lens 15-D) - skills-pocock

Este documento descreve a auditoria inicial do ciclo `skills-pocock` (skills derivadas de `mattpocock/skills`), dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `skills-pocock`
- **Descrição Breve:** Conjunto de skills procedurais e de engenharia agêntica adaptadas do repositório Matt Pocock para o ecossistema AIDD (`aidd-diagnose`, `aidd-tickets`, `aidd-grill`, `aidd-tdd`, `aidd-retro`, `aidd-escrita-agentes`, `aidd-entrega`, `aidd-wizard`).
- **Comando de Gatilho:** Comandos slash correspondentes (`/aidd-diagnose`, `/aidd-tickets`, etc.) e `python ecossistema.py components sync`.

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** Contratos e formatos das skills padronizados em `docs/protocolos/CONVENCAO-AUTORIA-SKILLS.md`. No estado inicial, faltavam glossário unificado e amarração estrita aos princípios de engenharia canônica.
- **D2. Input e Gatilhos:** Gatilhos acionados via slash commands e invocação agêntica natural. No estado inicial, aidd-grill não operava em rodadas sequenciais estritas.
- **D3. Raio de Impacto e Isolamento:** Skills operam no escopo de arquivos acordados em cada comando, com delimitação clara.
- **D4. Componentes e Fractalidade:** Fonte canônica única centralizada em `componentes/compartilhado/skills/` distribuída para todos os harnesses suportados via `gestor_componentes.py`.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** Elevar o rigor de engenharia de software agêntica, erradicando vibe coding e forçando TDD Red-Green e fatias verticais.
- **[Estágio 1 - Diagnóstico e Triage] D6. O que o Estágio Faz:** Isolamento sistemático de falhas em 5 fases.
- **[Estágio 1 - Diagnóstico e Triage] D7. O que o Estágio Recebe:** Sintoma ou falha de teste com comando de reprodução mínimo.
- **[Estágio 1 - Diagnóstico e Triage] D8. O que o Estágio Processa:** Fases de hipóteses isoladas com teste vermelho antes de qualquer alteração de código.
- **[Estágio 1 - Diagnóstico e Triage] D9. O que o Estágio Entrega:** Causa raiz comprovada e teste de regressão aprovado.
- **D10. Orquestração e Topologia:** Quebra de tarefas complexas em fatias verticais com tracer bullets e dependências "Bloqueado por".

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** Falhas em comandos humanos encapsuladas em scripts interativos com fallback transparente via `aidd-wizard`.
- **D12. Observabilidade e Frugalidade:** Sessões registradas com retrospectiva pós-execução (`aidd-retro`) convertendo falhas de agente em portões mecânicos determinísticos.

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** Portão canônico `gates/G_PROVA_SKILLS_POCOCK.py` e validação de formato `gates/G_SKILL_FORMATO.py`.
- **D14. Critério de Rejeição (Rollback):** Rejeição determinística por portões `G_SKILL_ROT.py` e `G_SKILL_FORMATO.py`.
- **D15. Output Consolidado e Handoff:** Fechamento e handoff das entregas com modelo padronizado via `aidd-entrega`.

---

## 3. Matriz de Avaliação da Execução
- [x] A ferramenta isolou seu raio de impacto corretamente?
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas?
- [x] O output final passou em todos os Quality Gates e emitiu o Handoff?

**Nota Inicial: 8.5 / 10**
