# Plano de Evolução (Fase 2) — skills-ddd (Ciclo 01)

Este plano materializa a integração seletiva de Manuais Canônicos e da Skill de Formulários derivadas de `skills-ddd-clean`, conforme o `RELATORIO-TECNICO.md` e o `DOD.md` deste ciclo.

**Status:** RASCUNHO — pronto para execução pelo pipeline de evolução.

## Estratégia de Execução
- Todo ticket segue TDD estrito (Red → Green). O teste de validação é escrito e executado antes, comprovando que falha (exit 1) na ausência do artefato.
- Fonte canônica dos manuais: `docs/protocolos/`.
- Fonte canônica da skill: `componentes/compartilhado/skills/aidd-frontend-forms/`. Nunca editar cópias de harnesses manualmente.
- A distribuição universal ocorre no Ticket 5 via `python ecossistema.py components sync --tipo todos`.
- O fechamento do ciclo ocorre no Ticket 6 com a auditoria geral do ecossistema (`python ecossistema.py audit` exit 0).

---

### Ticket 1: Manual Canônico de DDD Tático & Invariantes no Monólito VSA (Refere-se a D1 / DoD 1)
- **Falha 15-D:** `D1. Contratos e Regras`
- **Artefato de Handoff:** `docs/protocolos/PADRAO-DDD-CLEAN-VSA.md`
- **Requisito TDD (Red):** `tests/test_manual_ddd_clean_vsa.py` falha (exit 1) se o arquivo não existir ou não contiver: regras de Entidade imutável com `try_create` / `create`, Value Objects autocontidos, consolidação de erros com `Result`, Domain Services e desacoplamento de `@mentoria-360/shared`.
- **Implementação Técnica:**
  - Redigir `docs/protocolos/PADRAO-DDD-CLEAN-VSA.md` em PT-BR claro e estruturado.
  - Explicar como aplicar DDD tático dentro de fatias verticais VSA (`features/<nome>/`).
  - Fornecer código de referência funcional em Python puro (usando Dataclasses e Pydantic) e TypeScript puro para frontend.
  - Documentar armadilhas comuns: mutabilidade descontrolada, vazamento de regras de domínio para controllers e acoplamento a ORMs.
- **Verificação (Green):** `pytest tests/test_manual_ddd_clean_vsa.py` retorna exit 0 e `python gates/G_DOCS_ROT.py` retorna exit 0.
- **Construtor Prompt (EN):**
  - Write `tests/test_manual_ddd_clean_vsa.py` first. Assert exit 1 when `docs/protocolos/PADRAO-DDD-CLEAN-VSA.md` is missing or lacks core DDD sections (Entity with try_create, Value Object, Result pattern, VSA integration, zero external vendor lock-in).
  - Create `docs/protocolos/PADRAO-DDD-CLEAN-VSA.md` with complete, typed Python and TypeScript examples.
  - Run `pytest tests/test_manual_ddd_clean_vsa.py` to ensure exit 0.

---

### Ticket 2: Manual Canônico de Leitura Otimizada e CQRS para Fatias Verticais (Refere-se a D8 / DoD 2)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `docs/protocolos/PADRAO-CONSULTAS-LEITURA-CQRS.md`
- **Requisito TDD (Red):** `tests/test_manual_cqrs_leitura.py` falha (exit 1) se o arquivo não existir ou não contiver: segregação explícita entre Comandos (escrita com validação de invariantes) e Consultas (leitura direta SQL projetando em DTOs), diretrizes para SQLite WAL e proibição de carregar agregados em rotas GET.
- **Implementação Técnica:**
  - Redigir `docs/protocolos/PADRAO-CONSULTAS-LEITURA-CQRS.md` em PT-BR claro.
  - Detalhar a arquitetura de leitura leve: controllers/rotas chamam diretamente adaptadores de query SQL sem instanciar entidades de negócio.
  - Apresentar exemplos comparativos de latência e consumo de memória entre leitura orientada a modelo vs leitura projetada em DTO.
- **Verificação (Green):** `pytest tests/test_manual_cqrs_leitura.py` retorna exit 0 e `python gates/G_DOCS_ROT.py` retorna exit 0.
- **Construtor Prompt (EN):**
  - Write `tests/test_manual_cqrs_leitura.py` first. Assert exit 1 if `docs/protocolos/PADRAO-CONSULTAS-LEITURA-CQRS.md` does not exist or lacks CQRS command vs query rules, SQL projection, and SQLite WAL guidelines.
  - Create `docs/protocolos/PADRAO-CONSULTAS-LEITURA-CQRS.md`.
  - Run `pytest tests/test_manual_cqrs_leitura.py` to assert exit 0.

---

### Ticket 3: Incorporação de Nomenclatura Frontend na Stack Ouro (Refere-se a D1 / DoD 3)
- **Falha 15-D:** `D1. Contratos e Regras`
- **Artefato de Handoff:** `docs/protocolos/PADRAO-OURO-STACK-TECNOLOGICA.md`
- **Requisito TDD (Red):** `tests/test_convencao_nomenclatura_frontend.py` falha (exit 1) se `PADRAO-OURO-STACK-TECNOLOGICA.md` não contiver a seção de convenção de sufixos de arquivo para o frontend Next.js (`.component.tsx`, `.page.tsx`, `.context.tsx`, `.hook.ts`, `.schema.ts`).
- **Implementação Técnica:**
  - Adicionar seção em `docs/protocolos/PADRAO-OURO-STACK-TECNOLOGICA.md` padronizando a organização de arquivos no ecossistema Next.js.
  - Estabelecer a regra de kebab-case e sufixos explícitos para facilitar a inspeção automatizada pelos Quality Gates.
- **Verificação (Green):** `pytest tests/test_convencao_nomenclatura_frontend.py` retorna exit 0.
- **Construtor Prompt (EN):**
  - Write `tests/test_convencao_nomenclatura_frontend.py` first. Assert exit 1 while `PADRAO-OURO-STACK-TECNOLOGICA.md` lacks standard frontend suffix naming conventions.
  - Edit `docs/protocolos/PADRAO-OURO-STACK-TECNOLOGICA.md` to add the naming section.
  - Run test to assert exit 0.

---

### Ticket 4: Nova Skill Canônica `aidd-frontend-forms` (Refere-se a D2 / DoD 4)
- **Falha 15-D:** `D2. Input e Gatilhos`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-frontend-forms/SKILL.md`
- **Requisito TDD (Red):** `tests/test_skill_frontend_forms.py` falha (exit 1) se a pasta ou o `SKILL.md` não existir, não tiver o frontmatter `Use when...`, exceder o limite de linhas ou não cobrir Next.js + Zod + React Hook Form.
- **Implementação Técnica:**
  - Criar `componentes/compartilhado/skills/aidd-frontend-forms/SKILL.md` seguindo rigorosamente a `CONVENCAO-AUTORIA-SKILLS.md`.
  - Corpo conciso em inglês, instruções práticas de schema Zod, inferência de tipos TypeScript e binding com React Hook Form.
  - Testar conformidade com os gates `G_SKILL_FORMATO.py` e `G_SKILL_ROT.py`.
- **Verificação (Green):** `pytest tests/test_skill_frontend_forms.py` passa e gates de skill passam com exit 0.
- **Construtor Prompt (EN):**
  - Write `tests/test_skill_frontend_forms.py` first. Assert exit 1 while `componentes/compartilhado/skills/aidd-frontend-forms/SKILL.md` is absent.
  - Create `componentes/compartilhado/skills/aidd-frontend-forms/SKILL.md` strictly following `CONVENCAO-AUTORIA-SKILLS.md`.
  - Validate with `python gates/G_SKILL_FORMATO.py` and `python gates/G_SKILL_ROT.py`. Assert exit 0.

---

### Ticket 5: Sincronização Universal Multi-Harness (Refere-se a D15 / DoD 5)
- **Falha 15-D:** `D15. Integração com o Ecossistema`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-frontend-forms/SKILL.md`
- **Requisito TDD (Red):** `python ecossistema.py components verify` acusa divergência se a nova skill não estiver replicada.
- **Implementação Técnica:**
  - Executar deterministicamente `python ecossistema.py components sync --tipo todos`.
  - Validar que a skill `aidd-frontend-forms` foi instalada com sucesso em todos os ambientes configurados.
- **Verificação (Green):** `python ecossistema.py components verify` retorna exit 0.
- **Construtor Prompt (EN):**
  - Run `python ecossistema.py components sync --tipo todos`.
  - Run `python ecossistema.py components verify`. Assert exit 0.

---

### Ticket 6: Quality Gate Final do Ecossistema (Refere-se a DoD 6)
- **Falha 15-D:** `D15. Output Consolidado e Handoff`
- **Artefato de Handoff:** `docs/auditoria/skills-ddd/ciclo-01/RELATORIO-CONSTRUTOR.md`
- **Requisito TDD (Red):** Não aplicável (estágio de convergência).
- **Implementação Técnica:**
  - Executar a bateria de testes geral: `pytest tests/`.
  - Executar a auditoria oficial de governança: `python ecossistema.py audit`.
  - Registrar evidências de saída no `RELATORIO-CONSTRUTOR.md`.
- **Verificação (Green):** `python ecossistema.py audit` retorna exit 0 com 100% dos portões de qualidade aprovados.
- **Construtor Prompt (EN):**
  - Run full test suite: `pytest tests/`. Assert exit 0.
  - Run ecosystem audit: `python ecossistema.py audit`. Assert exit 0.
  - Document all outputs and results in `docs/auditoria/skills-ddd/ciclo-01/RELATORIO-CONSTRUTOR.md`.
