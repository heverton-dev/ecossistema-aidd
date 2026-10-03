# Plano de Evolução (Fase 2) - aidd-skills

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de readequar a convenção de skills e o ferramental de governança agêntica de acordo com o Laudo 15-D, a Definição de Pronto (DoD) e os aprendizados do documento de referência `O que é uma Skill em AIDD.md`.

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor). Para cada requisito funcional, testes determinísticos (exit 0 / exit 1) devem assegurar a integridade sem degradação das 44 skills canônicas existentes.

### Ticket 1: Padronização de Negative Guardrails e Stopping Checklist (Refere-se a D1 / DoD 1)
- **Falha 15-D:** `D1. Contratos e Regras`
- **Artefato de Handoff:** `docs/protocolos/CONVENCAO-AUTORIA-SKILLS.md`
- **Gate do Ticket:** `python gates/G_SKILL_FORMATO.py`
- **Requisito TDD (Red):** Validar se o protocolo define explicitamente os blocos obrigatórios de anti-patterns da LLM (`Negative Guardrails`) e critérios binários de parada (`Stopping Checklist / Completion Criteria`).
- **Implementação Técnica:**
  - Atualizar a convenção `docs/protocolos/CONVENCAO-AUTORIA-SKILLS.md` formalizando a seção recomendada de `Negative Guardrails` (o que NUNCA fazer, bloqueando vícios estocásticos) e `Stopping Checklist` (critérios binários para o agente encerrar a execução).
  - Preservar o teto estrito de 450 linhas por SKILL.md e a exigência de idioma inglês para instruções à máquina (Lei #4).
- **Verificação (Green):** Documentação consolidada sem inconsistências lexicais com o gate `G_SKILL_FORMATO.py`.
- **Construtor Prompt (EN):**
  - Update docs/protocolos/CONVENCAO-AUTORIA-SKILLS.md.
  - Add explicit sections for Negative Guardrails (anti-patterns) and Stopping Checklist (binary completion criteria).
  - Keep hard ceiling of 450 lines per SKILL.md and English body for machine readability (Law #4).
  - Verify with markdown linter and gate consistency.

### Ticket 2: Auditoria de Falhas e Resiliência Operacional nos SKILL.md (Refere-se a D11 / DoD 2)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-skills/SKILL.md`
- **Gate do Ticket:** `python gates/G_SKILL_FORMATO.py && python gates/G_SKILL_ROT.py`
- **Requisito TDD (Red):** Checar se o SKILL.md de aidd-skills instrui o agente sobre como agir em modos de falha (Failure Modes / Fallbacks).
- **Implementação Técnica:**
  - Adicionar ao `componentes/compartilhado/skills/aidd-skills/SKILL.md` a seção com diretrizes claras de recuperação de erro quando gates falham ou quando há duplicação no catálogo.
  - Rodar o sync de componentes para propagar a alteração para os harnesses.
- **Verificação (Green):** `python gates/G_SKILL_FORMATO.py` e `python gates/G_SKILL_ROT.py` retornam exit 0.
- **Construtor Prompt (EN):**
  - Edit componentes/compartilhado/skills/aidd-skills/SKILL.md.
  - Add Failure Modes & Fallback section to guide agent on handling catalog conflicts and gate failures.
  - Run python ecossistema.py components sync --tipo skill --ferramenta compartilhado.
  - Run python gates/G_SKILL_FORMATO.py and python gates/G_SKILL_ROT.py. Assert exit 0.

### Ticket 3: Fortalecimento do Quality Gate G_SKILL_FORMATO (Refere-se a D13 / DoD 3)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/G_SKILL_FORMATO.py`
- **Gate do Ticket:** `python gates/G_SKILL_FORMATO.py`
- **Requisito TDD (Red):** Adicionar verificação opcional (--rigoroso) ou advertência no gate para skills sem seção de guardrails ou critérios de conclusão.
- **Implementação Técnica:**
  - Atualizar `gates/G_SKILL_FORMATO.py` permitindo modo estrito `--rigoroso` para auditoria profunda de novas skills sem quebrar retrocompatibilidade com o legado das 44 skills.
  - Garantir que o gate continue determinístico, rápido (< 1s) e baseado em análise estática.
- **Verificação (Green):** Testes unitários do gate passando e `python gates/G_SKILL_FORMATO.py` padrão mantendo exit 0.
- **Construtor Prompt (EN):**
  - Update gates/G_SKILL_FORMATO.py to support deep structural inspection without breaking existing 44 canonical skills.
  - Ensure zero LLM dependencies and sub-second execution time.
  - Run python gates/G_SKILL_FORMATO.py across all skills. Assert exit 0.
