# Relatório Técnico do Arquiteto — skills-ddd (Ciclo 01)

> **Ciclo:** `docs/auditoria/skills-ddd/ciclo-01`  
> **Papel:** Arquiteto do Ecossistema AIDD  
> **Decisão:** Extração Seletiva e Transformação Canônica de Manuais e Skills  

---

## 1. Diagnóstico Arquitetural e Triagem de Ativos

O repositório `skills-ddd-clean` concentra duas camadas de naturezas distintas:
1. **Camada de Mecanismos de Infraestrutura e Framework:** Fortemente acoplada a NestJS, Prisma, TurboRepo e `@mentoria-360/shared`. Esta camada é incompatível com o núcleo do ecossistema AIDD.
2. **Camada de Engenharia de Software e Modelagem de Domínio:** Princípios agnósticos de Domain-Driven Design (DDD), Clean Architecture, segregação de comandos e leituras (CQRS), invariantes em entidades e objetos de valor, validação funcional com `Result` e contratos de UI frontend em Next.js.

### Matriz de Decisão Arquitetural

| Ativo Original | Natureza | Ação Arquitetural | Destino Canônico no Ecossistema |
| :--- | :--- | :--- | :--- |
| `module-entity`, `module-value-object`, `module-domain-service`, `module-use-case`, `module-aggregate`, `module-repository` (`references/*.md`) | Padrões de Domínio e Invariantes | **Conversão para Manual Canônico** | `docs/protocolos/PADRAO-DDD-CLEAN-VSA.md` |
| `module-query-cqrs` (`query-cqrs-pattern.md`) | Arquitetura de Leitura de Alto Desempenho | **Conversão para Manual Canônico** | `docs/protocolos/PADRAO-CONSULTAS-LEITURA-CQRS.md` |
| `skills-standards.md` | Convenções de Nomenclatura e Tipos de Arquivos | **Incorporação em Protocolo Existente** | `docs/protocolos/PADRAO-OURO-STACK-TECNOLOGICA.md` |
| `frontend-form-schema` + `form-schema-pattern.md` | Criação de Formulários Zod/React Hook Form | **Criação de Skill Canônica** | `componentes/compartilhado/skills/aidd-frontend-forms/` |
| `backend-controller`, `backend-nest-config`, `backend-prisma-data`, `config-prisma` | Infraestrutura NestJS / Prisma | **Descarte Técnico** | Incompatível com Lei #11 (Backend Python puro + SQLite WAL). |
| `config-project`, `config-new-module`, `config-shared-*` | Monorepo TurboRepo | **Descarte Técnico** | Incompatível com a topologia de Monólito Modular VSA do `aidd-master`. |
| `config-auth-*` | Autenticação vinculada a `@mentoria-360/shared` | **Descarte Técnico** | Violação da Lei #6 (Agnostic Supremacy / Dependência fechada). |
| `openspec-*` | Workflow baseado em CLI terceira | **Descarte Técnico** | Substituído nativamente por `aidd-spec`, `aidd-tickets` e `aidd-pipeline`. |

---

## 2. Diretrizes Técnicas de Implementação

### 2.1 Manual `PADRAO-DDD-CLEAN-VSA.md`
* **Objetivo:** Estabelecer como regras de negócio ricas devem ser modeladas nas fatias verticais VSA do AIDD.
* **Preservar:** Conceito de Entidades com identidade clara, `tryCreate` estático que valida antes de instanciar, imutabilidade com `cloneWith`, Value Objects autocontidos e consolidação de erros funcionais com `Result`.
* **Ajustar:** Demonstrar implementações em **Python moderno** (dataclasses com Pydantic V2 / custom validations) para o backend, e em **TypeScript** puro para o frontend. Eliminar qualquer menção a `@mentoria-360/shared`.

### 2.2 Manual `PADRAO-CONSULTAS-LEITURA-CQRS.md`
* **Objetivo:** Garantir que rotas GET de leitura e relatórios não incorram no overhead de carregar agregados completos de escrita.
* **Diretriz:** Leitura direta em SQL otimizado sobre SQLite WAL (ou Postgres em apps legadas migradas pelo Bridge), projetando diretamente em DTOs/schemas de resposta.

### 2.3 Skill Canônica `aidd-frontend-forms`
* **Localização:** `componentes/compartilhado/skills/aidd-frontend-forms/SKILL.md`.
* **Stack:** Next.js (App Router), TypeScript, Tailwind CSS, Zod e React Hook Form (aderência 100% à Lei #11).
* **Conformidade:** Seguir a convenção de autoria de skills (`docs/protocolos/CONVENCAO-AUTORIA-SKILLS.md`), com frontmatter padronizado e corpo em inglês conciso.

---

## 3. Estratégia de Testes e Quality Gates

1. Todo manual e skill terá um teste automatizado em `tests/` comprovando a existência de seções obrigatórias, conformidade com a Lei #4 (sem jargões sem tradução e documentação rigorosa) e aderência ao padrão-ouro.
2. Nenhuma alteração manual será feita em pastas de harnesses (.claude, .gemini, etc.); a propagação será feita estritamente pelo comando determinístico `python ecossistema.py components sync --tipo todos`.
3. O ciclo será encerrado com a execução completa do Quality Gate binário (`python ecossistema.py audit`), garantindo exit code 0.
