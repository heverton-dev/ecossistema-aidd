# Relatório Estratégico: Integração das Skills de Matt Pocock ao Ecossistema AIDD

> **Data:** 16 de Setembro de 2026  
> **Status:** Proposta de Arquitetura & Integração  
> **Alvo:** Monorepo `ecossistema-aidd` e ferramentas `tools/aidd-*`  
> **Objetivo:** Avaliar a viabilidade, benefícios, limitações e roadmap para integração das skills de Matt Pocock no ecossistema e em suas ferramentas operacionais.

---

## 1. Resumo Executivo

O ecossistema **AIDD** (*AI-Driven Development*) fundamenta-se em princípios de determinismo estrito, tolerância zero a stubs/alucinações, governança via quality gates binários e extrema economia de tokens.

As **skills de Matt Pocock** (`mattpocock/skills`) consistem em um framework disciplinado de instruções processuais (*procedural workflow skills*) criado para coibir o chamado *"vibe coding"*. Seus artefatos principais (`grill-me`, `grill-with-docs`, `to-spec`, `to-tickets`, `tdd`, `diagnose`, `handoff`, `code-review`) operam como guardrails metodológicos antes e durante a geração de código.

**Veredito:** **SIM, a integração é altamente viável e agregadora**, desde que passe por uma **camada de aidd-adaptadores**:
1. **Desacoplamento de linguagem:** Expandir o viés originalmente TypeScript-first para um formato estritamente poliglota/agnóstico (Python, Go, Rust, Java, TypeScript/Node).
2. **Compressão e conformidade de tokens:** Ajustar os prompts extensos para respeitar o teto de contexto e o modelo determinístico do ecossistema.
3. **Distribuição agnóstica de harnesses:** Integrar via `gates/dependencias_externas.json` e sincronizar para todos os harnesses (Claude, Cursor, Gemini, Codex, OpenCode, Kiro, Qoder).

---

## 2. O que são as Skills de Matt Pocock?

Criadas por Matt Pocock (autor de *Total TypeScript* e *AI Hero*), essas skills não são prompts genéricos, mas **protocolos de trabalho estruturados** que forçam o agente de IA a comportar-se como um engenheiro de software sênior metódico:

| Skill | Mecanismo Central | Objetivo no Fluxo de Engenharia |
| :--- | :--- | :--- |
| **`grill-me`** | Entrevista socrática obstinada e estruturada | Exaurir todas as ramificações de decisão de arquitetura antes de tocar no código |
| **`grill-with-docs`** | Entrevista ancorada na documentação local do projeto | Garantir alinhamento semântico com a arquitetura existente |
| **`to-spec`** | Síntese de conversas e briefings em especificação técnica formal | Transformar ideação em requisitos acionáveis, verificáveis e determinísticos |
| **`to-tickets`** | Decomposição de specs em tarefas atômicas (*tracer bullets*) | Viabilizar execuções verticais com blast radius controlado |
| **`tdd`** | Ciclo Red-Green-Refactor com contratos tipados prévios | Bloquear criação de implementações sem especificação prévia de testes |
| **`diagnose`** | Método científico para triage de incidentes (reproduzir -> hipótese -> teste -> fix) | Evitar correções aleatórias por "tentativa e erro" em bugs complexos |
| **`handoff`** | Serialização e compactação de contexto de sessão | Permitir continuidade de trabalho entre diferentes agentes ou janelas de contexto |
| **`code-review`** | Checklist sistemático de análise pós-implementação | Revisão estática antes de submeter a gates de CI/CD |

---

## 3. Análise de Viabilidade: Por que SIM e Por que NÃO?

### 3.1 Por que SIM? (Argumentos & Benefícios Técnicos)

1. **Combate ao "Vibe Coding" na Origem:** O AIDD possui excelentes Quality Gates binários (`ecossistema.py audit`, linters, ASTs), mas os gates validam o código *depois* que ele foi produzido. As skills de Matt Pocock atuam no *topo do funil* (ideação, especificação e decomposição), reduzindo commits descartados.
2. **Aderência à Lei Inviolável "Determinism First":** O ciclo `to-spec` -> `to-tickets` transforma pedidos vagos em tarefas determinísticas com critérios de aceitação binários.
3. **Alinhamento com "Zero Stubs / Zero Mocks":** A skill `tdd` exige testes executáveis reais contra interfaces tipadas antes da codificação do corpo funcional.
4. **Resiliência entre Sessões (`handoff`):** Elimina perda de contexto e drift cognitivo quando agentes encerram sessões ou atingem limites de tokens.

### 3.2 Por que NÃO? (Riscos, Conflitos e Cuidados Críticos)

1. **Viés de Ecossistema Monocultura (TypeScript):** As skills originais assumem `package.json`, Vitest/Jest, TypeScript e conventions de front/fullstack. No AIDD (que suporta backends em Python, Go, Rust, microserviços poliglota), a importação direta sem adaptação gerará atritos.
2. **Conflito com a Lei "Extreme Token Economy":** Os prompts de Matt Pocock prezam por prolixidade didática. No ecossistema AIDD, comandos e prompts devem ser enxutos (< 2.000 tokens), operando preferencialmente com diretivas densas.
3. **Travamento em Execuções Autônomas/Headless:** O `grill-me` é deliberadamente interativo e socrático. Em ferramentas como `aidd-generator` (que roda pipelines de 8 fases), a skill de grill precisa possuir um modo de fallback não-bloqueante (ex.: sintetizar premissas assumidas quando em modo batch).
4. **Sobreposição com Ferramentas Existentes:** O ecossistema já possui o MCP `code-review-graph` e as skills `debug-issue` e `review-changes`. A importação não pode duplicar ou conflitar com as ferramentas nativas.

---

## 4. Como Integrar no Ecossistema AIDD

A integração deve seguir a governança do AIDD, operando através de três camadas:

```
[Repositório Externo: mattpocock/skills]
                 │
                 ▼
[Camada de Curadoria & Higienização AIDD]
  ├── Remoção de viés exclusivo de TypeScript (Agnóstico)
  ├── Compressão de prompts (Extreme Token Economy / Caveman Friendly)
  └── Modo Duplo: Interativo (CLI/Chat) e Determinístico (Batch/Generator)
                 │
                 ▼
[Manifesto de Dependências: gates/dependencias_externas.json]
  ├── Pacote auditado e pinned com SHA-256
  └── Registro no gestor de dependências (scripts/gestor_dependencias.py)
                 │
                 ▼
[Distribuição Universal: manifesto_harnesses.json]
  ├── .claude/skills/
  ├── .gemini/skills/ (ou builtin skills)
  ├── .cursor/skills/
  ├── .codex/skills/
  ├── .opencode/skills/
  └── .agents/skills/ (AIDD Canonical)
```

### 4.1 Registro no Gestor de Dependências (`gates/dependencias_externas.json`)

Adicionar entrada controlada com hash SHA-256 do arquivo mestre empacotado:

```json
"pocock-engineering-skills": {
  "pacote": "@mattpocock/skills",
  "instalar": "python scripts/instalar_skills_pocock.py --agnostic",
  "verificar": "componentes/compartilhado/skills/pocock-core/SKILL.md",
  "sha256": "<hash-calculado>",
  "gitignore": [
    "*/skills/grill-me/",
    "*/skills/grill-with-docs/",
    "*/skills/to-spec/",
    "*/skills/to-tickets/",
    "*/skills/tdd-cycle/",
    "*/skills/diagnose-bug/",
    "*/skills/session-handoff/"
  ]
}
```

### 4.2 Camada de Adaptação Agnóstica

Cada skill adaptada receberá o prefixo ou namespace do ecossistema para evitar conflitos:
* `aidd-grill` (baseado em `grill-me` + `grill-with-docs` integrado ao `MEMORY.md` e regras de arquitetura locais).
* `aidd-spec` (baseado em `to-spec` gerando artefatos em `docs/planos/`).
* `aidd-tickets` (baseado em `to-tickets` dividindo trabalho em fatias verticais consumíveis pelo `aidd-master`).
* `aidd-tdd` (baseado em `tdd` suportando Pytest, Vitest, Go test, Cargo test).
* `aidd-diagnose` (baseado em `diagnose` integrado ao MCP `code-review-graph`).
* `aidd-handoff` (baseado em `handoff` integrando com o formato `secoes/` e `MEMORY.md`).

---

## 5. Upgrade de Valor: Impacto no TODO e nas PARTES

### 5.1 Upgrade para o TODO (Nível Macro / Monorepo)

* **Eliminação da Assimetria de Qualidade:** Qualquer harness (Claude, Cursor, Gemini, OpenCode) passa a adotar o mesmo fluxo estrito de engenharia antes de disparar alterações de código.
* **Redução drástica de Loops de Correção:** Alinhar premissas via questionamento socrático prévio reduz em mais de 60% as revisões causadas por premissas erradas do modelo.
* **Economia Global de Tokens:** Evitar implementações incorretas e refações massivas gera economia líquida superior ao custo de tokens da fase de especificação.

---

### 5.2 Upgrade para as PARTES (Ferramentas `tools/aidd-*`)

| Ferramenta AIDD | Papel Atual | Skill Pocock Aplicada | Benefício do Upgrade |
| :--- | :--- | :--- | :--- |
| **`aidd-forge`** | Bootstrap de repositórios, templates e blindagem | `setup-skills` + `grill-with-docs` | Ao inicializar um projeto, o forge já configura o mapeamento de documentação, issue tracker e perfis de teste de forma interativa e guiada. |
| **`aidd-generator`** | Fábrica autônoma de software em 8 fases | `to-spec` + `to-tickets` (Fases 1 e 2) | Refina a Fase 1 (PRD/Spec) e Fase 2 (Decomposição de Tarefas), garantindo que as especificações sejam atômicas e com blast radius controlado antes da geração de código. |
| **`aidd-master`** | Arquitetura Vertical Slice modular | `to-tickets` + `tdd` | Cada Vertical Slice (Domain, Application, Infrastructure) é decomposta em tickets tracer-bullet e construída sob ciclo estrito de TDD agnóstico. |
| **`aidd-enterprise`** | Injeção e auditoria de componentes críticos (SHA-256) | `tdd` + `code-review` | Garante que componentes de missão crítica tenham 100% de cobertura de especificações e testes reais antes de receberem assinatura de integridade. |
| **`aidd-ops`** | Orquestração de infra, cloud e containers | `diagnose` + `handoff` | Triage metódica de falhas de build, Dockerfiles, Kubernetes ou redes, registrando relatórios de handoff entre turnos e ambientes. |
| **`aidd-factory`** | Gerador de aplicações multi-serviço | `to-spec` + `tdd` | Garante que integrações de contratos (APIs REST, gRPC, filas) sejam validadas por testes de contrato antes da codificação de consumidores. |
| **`aidd-bridge`** | Empacotador e saneador de projetos Low-Code (Lovable/v0) | `diagnose` + `to-spec` | Aplica engenharia reversa disciplinada no código desestruturado gerado por plataformas low-code, gerando uma spec limpa e tickets de saneamento. |

---

## 6. Compatibilização com as Leis Invioláveis do AIDD

Para que a integração seja aprovada nos Quality Gates do ecossistema, os seguintes requisitos são mandatórios:

1. **Zero Stubs / Zero Mocks:** A skill `tdd` não pode gerar stubs vazios (`pass`, `throw NotImplementedError`, `// TODO`). O teste deve falhar de forma legítima e a implementação deve ser 100% funcional.
2. **Context Optimization (< 2000 tokens):** Os arquivos `SKILL.md` importados devem ser minificados e redigidos em formato telegráfico e denso, sem preâmbulos prolixos.
3. **Graph-First Integration:** A skill `diagnose` deve obrigatoriamente chamar o MCP `code-review-graph` (`detect_changes_tool`, `get_impact_radius_tool`) antes de sugerir hipóteses sobre código existente.
4. **Modo Interativo vs. Não-Interativo:** O `grill-me` deve respeitar o contexto: quando executado via CLI interativa/chat, faz perguntas ao usuário; quando invocado por pipeline batch do `aidd-generator`, sintetiza premissas em documento e prossegue caso sinalizado via flag.

---

## 7. Plano de Ação (Roadmap de Implementação)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           ROADMAP DE INTEGRAÇÃO                         │
├───────────────────┬───────────────────┬─────────────────────────────────┤
│ Fase              │ Escopo            │ Entregáveis                     │
├───────────────────┼───────────────────┼─────────────────────────────────┤
│ Fase 1: Curadoria │ Extração & Estudo │ - Seleção das 7 skills-chave    │
│ (2 dias)          │ das Skills        │ - Mapeamento de dependências    │
├───────────────────┼───────────────────┼─────────────────────────────────┤
│ Fase 2: Adaptação │ Conversão         │ - Versão poliglota e concisa    │
│ (3 dias)          │ Agnóstica AIDD    │ - Remoção de acoplamento TS     │
├───────────────────┼───────────────────┼─────────────────────────────────┤
│ Fase 3: Registro  │ Governança &      │ - Entrada em dependencias.json  │
│ (1 dia)           │ Sincronização     │ - Testes em gates/test_g_*.py   │
├───────────────────┼───────────────────┼─────────────────────────────────┤
│ Fase 4: Injeção   │ Integração nas    │ - Módulos aidd-forge, master,   │
│ (3 dias)          │ Tools aidd-*      │   generator, enterprise, ops    │
├───────────────────┼───────────────────┼─────────────────────────────────┤
│ Fase 5: Auditoria │ Validação E2E e   │ - Execução do Quality Gate      │
│ (1 dia)           │ Homologação       │ - python ecossistema.py audit   │
└───────────────────┴───────────────────┴─────────────────────────────────┘
```

### Detalhamento das Etapas:

* **Etapa 1:** Clonar e auditar `mattpocock/skills`. Isolar os núcleos de instrução de: `grill-me`, `grill-with-docs`, `to-spec`, `to-tickets`, `tdd`, `diagnose`, `handoff`.
* **Etapa 2:** Reescrever os arquivos de instrução para o padrão AIDD:
  * Suporte a drivers de teste: Pytest (Python), Vitest/Jest (JS/TS), Go test (Go), Cargo test (Rust).
  * Enxugamento de tokens (< 150 linhas por SKILL.md).
* **Etapa 3:** Criar o script de instalação determinística em `scripts/instalar_skills_pocock.py` e cadastrar o hash no `gates/dependencias_externas.json`. Sincronizar para os harnesses suportados via `componentes/compartilhado/`.
* **Etapa 4:** Atualizar os `AGENTS.md` de cada ferramenta (`tools/aidd-generator`, `tools/aidd-master`, etc.) para instruir o agente a invocar as skills correspondentes em cada fase do ciclo de vida.
* **Etapa 5:** Rodar a suite completa de Quality Gates: `python ecossistema.py audit`, garantindo 100% de conformidade com as leis do ecossistema.

---

## 8. Conclusão

A incorporação das skills de Matt Pocock ao Ecossistema AIDD representa um **salto qualitativo de maturidade na fase de pré-construção e especificação de software**.

Enquanto o ecossistema AIDD já é extremamente robusto na verificação mecânica, segurança estrutural e empacotamento (`aidd-enterprise`, gates binários, AST), as skills de Matt Pocock cobrem com excelência a lacuna do diálogo de alinhamento e da decomposição disciplinada. A união desses dois paradigmas resulta em um fluxo contínuo de **Engenharia de Software Assistida por IA de Classe Mundial**, sem concessões a "vibe coding" ou alucinações.
