# Taxonomia Canônica e Prevenção de Deterioração ("ROT") no Ecossistema AIDD

> **Status:** Auditado e Reconciliado (ISSUE-0018 — 6 categorias duplicadas absorvidas/rejeitadas como portões novos; 4 portões genuínos direcionados para ISSUE-0014..0017)
> **Data:** 19/09/2026 (Revisado em 20/09/2026)
> **Localização:** `docs/melhorias/19-09-2026_melhoria-taxonomia-prevencao-rot-ecossistema.md`
> **Origem:** Expansão pós-implementação do Quality Gate `G_DOCS_ROT` (Reconciliação anti-NIH via ISSUE-0018)

---

## 1. Visão Geral e Contexto

Após a implementação e homologação do portão determinístico de prevenção a **Docs Rot** (`gates/G_DOCS_ROT.py`), catalogou-se formalmente as manifestações de degradação ("ROT") que afetam o ecossistema. Na auditoria formal (ISSUE-0018), constatou-se que 6 das 10 propostas duplicavam mecanismos, planos ou portões já existentes. Per diretriz anti-NIH do ecossistema, o padrão **não** é criar portões redundantes, mas aprofundar os existentes ou direcionar para tickets abertos.

A tabela e as diretrizes a seguir compilam as 10 categorias essenciais de "ROT", seus mecanismos de mitigação e os Quality Gates determinísticos correspondentes.

---

## 2. Compilado Completo das Categorias "ROT"

### 1. Context Rot (Deterioração de Contexto Agêntico)
* **O que é:** Em sistemas agênticos e sessões longas de desenvolvimento, o acúmulo de histórico irrelevante, arquivos desatualizados no prompt, ferramentas com esquemas inflados e diretrizes redundantes degrada a precisão do LLM (efeito *lost in the middle*, alucinações, estouro da janela útil de tokens).
* **No AIDD:** O ecossistema combate via **Lei #4 (Extreme Token Economy)**, divisão modular do contexto (ISSUE-0005) e gate de idioma (ISSUE-0012). *(Nota de correção factual ISSUE-0018: A menção anterior ao combate via `sandeco-token-reduce` foi removida, pois a ISSUE-0008 comprovou que o compressor está inerte e seu check de disponibilidade sempre falha).*
* **Decisão de Reconciliação (ISSUE-0018):** ❌ **Rejeitado como novo portão isolado (`G_CONTEXT_ROT.py`).**
  - **Destino:** Dobrado nos tickets existentes **ISSUE-0005** (divisão de `AGENTS.md` em núcleo e seções sob demanda), **ISSUE-0012** (linter determinístico de inglês compacto da Lei #4) e **PLAN-0022 item 4** (Token budget enforcement).

---

### 2. Code Rot (ou Software Rot / Code Decay)
* **O que é:** Degradação gradual do código ao longo do tempo causada por mudanças no ambiente externo, bibliotecas de terceiros atualizadas, código morto (*dead code*), rotinas nunca invocadas e acúmulo silencioso de dívida técnica.
* **No AIDD:** O ecossistema exige determinismo e **Lei #5 (Zero Stubs / Zero Mocks)**.
* **Decisão de Reconciliação (ISSUE-0018):** ❌ **Rejeitado como novo portão isolado (`G_DEAD_CODE.py` / `G_CODE_ROT.py`).**
  - **Destino:** Dobrado na **ISSUE-0007** (resolução do `SagaOrchestrator`), **PLAN-0025 item 10** (inventário de código morto) e aprofundamento do orçamento estrito de testes skipped em `gates/G_TESTES_REAIS.py` + `gates/allowlist_skipped_testes.json`.

---

### 3. Architecture Rot (ou Architectural Drift / Erosion)
* **O que é:** Violação progressiva das fronteiras arquiteturais projetadas. No ecossistema AIDD, o padrão-ouro é o **Monólito Modular + VSA (Vertical Slice Architecture)**. A deterioração ocorre quando uma fatia vertical de domínio importa diretamente internos privados de outra fatia sem passar por contratos públicos ou pela camada horizontal compartilhada.
* **No AIDD:** Preserva as diretrizes de `aidd-master` e a integridade de deliverables e templates (Lei #1 Determinismo e Lei #11 Padrão-Ouro de Stack). *(Nota de correção factual ISSUE-0018: A referência anterior à Lei #6 era incorreta; a Lei #6 rege Agnostic Supremacy contra vendor lock-in de harness/SO/LLM, não fronteiras de fatias VSA).*
* **Decisão de Reconciliação (ISSUE-0018):** ❌ **Rejeitado como novo portão isolado (`G_ARCH_DRIFT.py`).**
  - **Destino:** Já coberto e aprofundado nos portões existentes **`gates/G_ARQUITETURA_DELIVERABLE.py`** (AST para regras Clean Architecture / isolamento de domínio), **`gates/G_FRONTEND_LAYERS.py`** (isolamento de UI dumb components), **`gates/G_DRIFT_ANALYZER.py`** / **`gates/G_DRIFT_NUCLEO_COMPARTILHADO.py`** e no ticket **ISSUE-0004** (zerar violações de arquitetura e religar trava).

---

### 4. Dependency Rot (ou Supply Chain / Tooling Rot)
* **O que é:** Versões fixadas de dependências que acumulam vulnerabilidades (CVEs), incompatibilidades silenciosas de runtimes (ex.: quebra entre Python 3.11 e 3.12, Node 18 e 22), ou scripts de setup que deixam de funcionar em máquinas limpas.
* **No AIDD:** Integrado à governança de `aidd-enterprise` e `dependencias_externas.json`.
* **Decisão de Reconciliação (ISSUE-0018):** ❌ **Rejeitado como novo portão isolado (`G_DEPENDENCY_ROT.py`).**
  - **Destino:** 100% coberto pelos portões existentes **`gates/G_DEPENDENCIAS_PIN_HASH.py`** (validação de pins exatos `==` e hashes sha256 em lockfiles) e **`gates/G_SUPPLY_CHAIN.py`** (varredura real de vulnerabilidades PyPA/OSV via `pip-audit`, typosquatting e URLs não autenticadas).

---

### 5. Test Rot (Deterioração de Bateria de Testes)
* **O que é:** Baterias de teste que testam apenas mocks artificiais, asserções vazias ou tautológicas (`assert True`), testes intermitentes (*flaky tests*), ou suítes que continuam passando enquanto a regra de negócio real de produção quebrou.
* **No AIDD:** Viola frontalmente a **Lei #5 (Zero Stubs)** e a **Lei #13 (Todo Portão Deve Provar que Morde)**.
* **Decisão de Reconciliação (ISSUE-0018):** ❌ **Rejeitado como novo portão isolado (`G_TEST_ROT.py`).**
  - **Destino:** Já coberto e aprofundado por **`gates/G_TESTES_REAIS.py`** (pytest real com allowlist de skips), meta-gate **`gates/G_PORTAO_PROVA_QUE_MORDE.py`** (**ISSUE-0011**) e **PLAN-0016 item 9** (portão de mutation testing já especificado).

---

### 6. Contract / Schema Rot (Deterioração de Contratos de API)
* **O que é:** Divergência silenciosa entre o schema contratual (OpenAPI 3.1, JSON Schema, Protobuf) e a implementação real das rotas e serviços. Ocorre quando uma rota altera status code, query param ou tipo de campo, mas o documento formal não acompanha.
* **No AIDD:** Quebra o *Quarteto Sine Qua Non* (`/docs`, `/webhooks`, `/mcp`, `/docs/guia`), induzindo agentes clientes a alucinações severas de chamada de ferramentas.
* **Decisão de Reconciliação (ISSUE-0018):** 🟢 **Aceito como portão genuinamente novo.**
  - **Destino:** Especificado e em fila de implementação na **ISSUE-0014** (`gates/G_CONTRACT_ROT.py`).

---

### 7. Config / Environment Rot (Deterioração de Ambiente e Infraestrutura)
* **O que é:** Quando arquivos de exemplo de variáveis de ambiente (`.env.example`), definições de conteinerização (`docker-compose.yml`) ou flags de CLI divergem das variáveis exigidas pelo código-fonte.
* **No AIDD:** Compromete a reprodutibilidade de deployment e a automação do `aidd-ops`. *(Nota de correção factual ISSUE-0018: A menção anterior a uma suposta "Lei #9 (Execução Limpa em Máquina Nova)" foi corrigida. A Lei #9 canônica em `AGENTS.md` é a Tool Testing Discipline; a prevenção de desvio de variáveis de ambiente resguarda a previsibilidade operacional e a portabilidade do ecossistema).*
* **Decisão de Reconciliação (ISSUE-0018):** 🟢 **Aceito como portão genuinamente novo.**
  - **Destino:** Especificado e em fila de implementação na **ISSUE-0015** (`gates/G_ENV_ROT.py`).

---

### 8. Skill & Tool Rot (Deterioração de Ferramental Agêntico)
* **O que é:** Ferramentas MCP ou Skills cujas instruções apontam para scripts CLI descontinuados, binários renomeados, parâmetros alterados ou caminhos de arquivos refatorados.
* **No AIDD:** Bloqueia a execução autônoma de fluxos da Tríade Canônica (`aidd-pure`, `aidd-open`, `aidd-bridge`). Teria evitado o caso de inércia silenciosa comprovado na ISSUE-0008.
* **Decisão de Reconciliação (ISSUE-0018):** 🟢 **Aceito como portão genuinamente novo.**
  - **Destino:** Especificado e em fila de implementação na **ISSUE-0016** (`gates/G_SKILL_ROT.py`).

---

### 9. Data / Migration Rot (Deterioração de Estado e Banco de Dados)
* **O que é:** Migrações SQL (`migrations/`) que perdem idempotência, scripts de rollback inexistentes ou esquemas de banco em produção que divergem do schema declarado pelas migrações (*schema drift*).
* **No AIDD:** Compromete a **Lei #3 (Structured Persistence)** em bancos SQLite WAL e PostgreSQL.
* **Decisão de Reconciliação (ISSUE-0018):** 🟢 **Aceito como portão genuinamente novo.**
  - **Destino:** Especificado e em fila de implementação na **ISSUE-0017** (`gates/G_MIGRATION_ROT.py`).

---

### 10. Prompt Rot (Deterioração de Prompts e Metadiretrizeis)
* **O que é:** System prompts contendo regras e truques de contorno legados para modelos já descontinuados, formatações abandonadas ou instruções em conflito direto com as convenções vivas do repositório.
* **No AIDD:** Incurre em desperdício de tokens de raciocínio e quebra da **Lei #12 (Anti-Docs Rot & Canonical Ingestion)**.
* **Decisão de Reconciliação (ISSUE-0018):** ❌ **Rejeitado como novo portão isolado (`G_PROMPT_ROT.py`).**
  - **Destino:** Já coberto e aprofundado via **`gates/G_DOCS_ROT.py`** (linter determinístico de links e caminhos canônicos vivos em docs/prompts), **`gates/G_LLM_PROMPT_SHIELD.py`** e pelo ticket **ISSUE-0012** (gate de inglês compacto e diretrizes vivas).

---

## 3. Matriz de Priorização e Reconciliação no AIDD

| Categoria "ROT" | Alvo Primário | Mecanismo Determinístico | Status Pós-Auditoria (ISSUE-0018) | Destino / Portão / Ticket |
| :--- | :--- | :--- | :--- | :--- |
| **Docs Rot** | `docs/`, `AGENTS.md`, links | Regex + Verificador de caminhos e HTTP | 🟢 **Homologado** | `gates/G_DOCS_ROT.py` (Ativo) |
| **Context Rot** | Prompts, schemas MCP, skills | Validador de token-budget e duplicações | 🟡 **Dobrado em Ticket** | ISSUE-0005, ISSUE-0012, PLAN-0022 #4 |
| **Architecture Rot** | Fronteiras de fatias VSA | AST Import / Boundary Checker | 🟡 **Aprofunda Existente** | `G_ARQUITETURA_DELIVERABLE.py`, ISSUE-0004 |
| **Contract Rot** | OpenAPI, Swagger, MCP Studio | Validador runtime vs spec estática | 🔵 **Novo Portão Aceito** | ISSUE-0014 (`G_CONTRACT_ROT.py`) |
| **Skill & Tool Rot** | Catálogo `componentes/.../skills` | Validador estático de paths e comandos | 🔵 **Novo Portão Aceito** | ISSUE-0016 (`G_SKILL_ROT.py`) |
| **Config & Env Rot** | `.env.example`, Docker | AST parser de `os.getenv` / `process.env` | 🔵 **Novo Portão Aceito** | ISSUE-0015 (`G_ENV_ROT.py`) |
| **Code Rot** | Código-fonte e dependências | AST scanner (`vulture`, dep-checker) | 🟡 **Dobrado em Ticket** | ISSUE-0007, PLAN-0025 #10, `G_TESTES_REAIS` |
| **Test Rot** | Bateria de testes em `tests/` | AST scanner de asserções e mutação | 🟡 **Aprofunda Existente** | `G_TESTES_REAIS.py`, Lei #13, PLAN-0016 #9 |
| **Data & Migration Rot**| Migrações SQL | Runner de migração em banco efêmero | 🔵 **Novo Portão Aceito** | ISSUE-0017 (`G_MIGRATION_ROT.py`) |
| **Prompt Rot** | System prompts e personas | Linter de diretrizes e termos deprecados | 🟡 **Aprofunda Existente** | `G_DOCS_ROT.py`, ISSUE-0012 |

---

## 4. Próximos Passos Consolidados

1. **Reconciliação Anti-NIH:** Zero portões novos criados para categorias já cobertas. Manter o princípio de que o padrão nunca é "novo portão solto".
2. **Execução dos 4 Portões Novos:** Implementar os portões genuínos sob a disciplina estrita da Lei #13 (`G_PORTAO_PROVA_QUE_MORDE.py` / ISSUE-0019):
   - **ISSUE-0014:** `G_CONTRACT_ROT.py`
   - **ISSUE-0015:** `G_ENV_ROT.py`
   - **ISSUE-0016:** `G_SKILL_ROT.py`
   - **ISSUE-0017:** `G_MIGRATION_ROT.py`
3. **Evolução dos Portões Existentes:** Fechar as pendências de arquitetura e contexto através das issues mapeadas (ISSUE-0004 para religar a trava de arquitetura; ISSUE-0005 e ISSUE-0012 para disciplina de contexto e idioma).
