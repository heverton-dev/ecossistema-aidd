# Taxonomia Canônica e Prevenção de Deterioração ("ROT") no Ecossistema AIDD

> **Status:** Proposta / Análise de Melhoria Arquitetural
> **Data:** 19/09/2026
> **Localização:** `docs/melhorias/19-09-2026_melhoria-taxonomia-prevencao-rot-ecossistema.md`
> **Origem:** Expansão pós-implementação do Quality Gate `G_DOCS_ROT`

---

## 1. Visão Geral e Contexto

Após a implementação e homologação do portão determinístico de prevenção a **Docs Rot** (`gates/G_DOCS_ROT.py`), identificou-se a necessidade de catalogar formalmente todas as manifestações de degradação ("ROT") que afetam o ciclo de vida do software, as arquiteturas modernas e a camada agêntica de IA (Agentic Context Engineering).

A tabela e as diretrizes a seguir compilam as 10 categorias essenciais de "ROT", seus mecanismos de mitigação e os Quality Gates determinísticos correspondentes.

---

## 2. Compilado Completo das Categorias "ROT"

### 1. Context Rot (Deterioração de Contexto Agêntico)
* **O que é:** Em sistemas agênticos e sessões longas de desenvolvimento, o acúmulo de histórico irrelevante, arquivos desatualizados no prompt, ferramentas com esquemas inflados e diretrizes redundantes degrada a precisão do LLM (efeito *lost in the middle*, alucinações, estouro da janela útil de tokens).
* **No AIDD:** O ecossistema combate via **Lei #4 (Extreme Token Economy)** e `sandeco-token-reduce`.
* **Portão Determinístico Proposto:** `G_CONTEXT_ROT.py`
  - Bloquear SKILLs ou prompts com tamanho superior a 2.000 tokens em arquivos de instrução primária.
  - Validar duplicação de regras entre `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` e skills (assegurando ponteiros únicos).
  - Auditar ferramentas MCP ociosas ou schemas não consumidos.

---

### 2. Code Rot (ou Software Rot / Code Decay)
* **O que é:** Degradação gradual do código ao longo do tempo causada por mudanças no ambiente externo, bibliotecas de terceiros atualizadas, código morto (*dead code*), rotinas nunca invocadas e acúmulo silencioso de dívida técnica.
* **No AIDD:** O ecossistema exige determinismo e **Lei #5 (Zero Stubs / Zero Mocks)**.
* **Portão Determinístico Proposto:** `G_DEAD_CODE.py` / `G_CODE_ROT.py`
  - Análise estática via AST (`vulture` em Python / ESLint/TS AST) para identificar funções, variáveis e imports mortos.
  - Varredura de dependências órfãs em `pyproject.toml`, `requirements.txt` ou `package.json` (pacotes instalados sem import real).
  - Bloqueio de testes marcados indefinidamente como `@pytest.mark.skip` sem vínculo ativo a issue/prazo.

---

### 3. Architecture Rot (ou Architectural Drift / Erosion)
* **O que é:** Violação progressiva das fronteiras arquiteturais projetadas. No ecossistema AIDD, o padrão-ouro é o **Monólito Modular + VSA (Vertical Slice Architecture)**. A deterioração ocorre quando uma fatia vertical de domínio importa diretamente internos privados de outra fatia sem passar por contratos públicos ou pela camada horizontal compartilhada.
* **No AIDD:** Preserva as diretrizes de `aidd-master` e a **Lei #6 (Agnostic Supremacy)**.
* **Portão Determinístico Proposto:** `G_ARCH_DRIFT.py` (ou `G_VSA_INTEGRITY.py`)
  - Analisador estático de imports AST: bloqueia importações cruzadas não autorizadas entre fatias (`slices/auth` não pode importar internals de `slices/billing`).
  - Garantir que módulos de domínio puro não importem diretamente drivers de infraestrutura ou harnesses específicos.

---

### 4. Dependency Rot (ou Supply Chain / Tooling Rot)
* **O que é:** Versões fixadas de dependências que acumulam vulnerabilidades (CVEs), incompatibilidades silenciosas de runtimes (ex.: quebra entre Python 3.11 e 3.12, Node 18 e 22), ou scripts de setup que deixam de funcionar em máquinas limpas.
* **No AIDD:** Integrado à governança de `aidd-enterprise` e `dependencias_externas.json`.
* **Portão Determinístico Proposto:** `G_DEPENDENCY_ROT.py`
  - Validação estrita de integridade via SHA-256 de binários e scripts terceiros.
  - Auditoria automatizada de vulnerabilidades conhecidas (`pip-audit` / `npm audit`).

---

### 5. Test Rot (Deterioração de Bateria de Testes)
* **O que é:** Baterias de teste que testam apenas mocks artificiais, asserções vazias ou tautológicas (`assert True`), testes intermitentes (*flaky tests*), ou suítes que continuam passando enquanto a regra de negócio real de produção quebrou.
* **No AIDD:** Viola frontalmente a **Lei #5 (Zero Stubs)** e a **Lei #13 (Todo Portão Deve Provar que Morde)**.
* **Portão Determinístico Proposto:** `G_TEST_ROT.py` (Mutation Testing & Anti-Stub Enforcement)
  - Varredura AST em arquivos `tests/` para banir asserções triviais ou mocks em testes que deveriam ser ponta a ponta.
  - Testes de mutação para garantir que a suite falhe obrigatoriamente sob injeção de defeito.

---

### 6. Contract / Schema Rot (Deterioração de Contratos de API)
* **O que é:** Divergência silenciosa entre o schema contratual (OpenAPI 3.1, JSON Schema, Protobuf) e a implementação real das rotas e serviços. Ocorre quando uma rota altera status code, query param ou tipo de campo, mas o documento formal não acompanha.
* **No AIDD:** Quebra o *Quarteto Sine Qua Non* (`/swagger`, `/webhooks`, `/mcp`, `/docs`), induzindo agentes clientes a alucinações severas de chamada de ferramentas.
* **Portão Determinístico Proposto:** `G_CONTRACT_ROT.py`
  - Comparador determinístico entre a árvore de rotas/respostas em runtime contra o `openapi.json` versionado.

---

### 7. Config / Environment Rot (Deterioração de Ambiente e Infraestrutura)
* **O que é:** Quando arquivos de exemplo de variáveis de ambiente (`.env.example`), definições de conteinerização (`docker-compose.yml`) ou flags de CLI divergem das variáveis exigidas pelo código-fonte.
* **No AIDD:** Quebra a **Lei #9 (Execução Limpa em Máquina Nova)** e as automações de deployment do `aidd-ops`.
* **Portão Determinístico Proposto:** `G_ENV_ROT.py`
  - Varredura via AST/Regex em chamadas como `os.getenv(...)`, `os.environ[...]` ou `process.env.*`, garantindo que toda chave exigida esteja espelhada em `.env.example`.

---

### 8. Skill & Tool Rot (Deterioração de Ferramental Agêntico)
* **O que é:** Ferramentas MCP ou Skills cujas instruções apontam para scripts CLI descontinuados, binários renomeados, parâmetros alterados ou caminhos de arquivos refatorados.
* **No AIDD:** Bloqueia a execução autônoma de fluxos da Tríade Canônica (`aidd-pure`, `aidd-open`, `aidd-bridge`).
* **Portão Determinístico Proposto:** `G_SKILL_ROT.py`
  - Validação estática de todos os caminhos relativos/absolutos, scripts e comandos referenciados dentro do corpo dos arquivos `SKILL.md`.

---

### 9. Data / Migration Rot (Deterioração de Estado e Banco de Dados)
* **O que é:** Migrações SQL (`migrations/`) que perdem idempotência, scripts de rollback inexistentes ou esquemas de banco em produção que divergem do schema declarado pelas migrações (*schema drift*).
* **No AIDD:** Compromete a **Lei #3 (Structured Persistence)** em bancos SQLite WAL e PostgreSQL.
* **Portão Determinístico Proposto:** `G_MIGRATION_ROT.py`
  - Aplicação sequencial de migrações (up e down) em banco efêmero isolado em memória a cada build, assegurando convergência ao schema final.

---

### 10. Prompt Rot (Deterioração de Prompts e Metadiretrizeis)
* **O que é:** System prompts contendo regras e truques de contorno legados para modelos já descontinuados, formatações abandonadas ou instruções em conflito direto com as convenções vivas do repositório.
* **No AIDD:** Incurre em desperdício de tokens de raciocínio e quebra da **Lei #12 (Anti-Docs Rot & Canonical Ingestion)**.
* **Portão Determinístico Proposto:** `G_PROMPT_ROT.py`
  - Linter determinístico que audita templates de prompt e arquivos de governança contra vocabulários descontinuados ou convenções revogadas.

---

## 3. Matriz de Priorização e Impacto no AIDD

| Categoria "ROT" | Alvo Primário | Mecanismo Determinístico | Impacto no AIDD |
| :--- | :--- | :--- | :--- |
| **Docs Rot** *(Resolvido)* | `docs/`, `AGENTS.md`, links | Regex + Verificador de caminhos e HTTP | 🟢 **Homologado** |
| **Context Rot** | Prompts, schemas MCP, skills | Validador de token-budget e duplicações | 🔴 **Crítico** |
| **Architecture Rot** | Fronteiras de fatias VSA | AST Import Checker cruzando regras de slice | 🔴 **Crítico** |
| **Contract Rot** | OpenAPI, Swagger, MCP Studio | Validador runtime vs spec estática | 🔴 **Crítico** |
| **Skill & Tool Rot** | Catálogo `componentes/.../skills` | Validador estático de paths e comandos | 🟡 **Alto** |
| **Config & Env Rot** | `.env.example`, Docker | AST parser de `os.getenv` / `process.env` | 🟡 **Alto** |
| **Code Rot** | Código-fonte e dependências | AST scanner (`vulture`, dep-checker) | 🟡 **Alto** |
| **Test Rot** | Bateria de testes em `tests/` | AST scanner de asserções e testes mutantes | 🟡 **Alto** |
| **Data & Migration Rot**| Migrações SQL | Runner de migração em banco efêmero | 🟡 **Alto** |
| **Prompt Rot** | System prompts e personas | Linter de diretrizes e termos deprecados | 🔵 **Médio** |

---

## 4. Próximos Passos Recomendados

1. **Prioridade 1:** Implementação do portão `G_CONTEXT_ROT.py` para reforçar a Lei #4 (Extreme Token Economy) com medição de tokens e anti-duplicação.
2. **Prioridade 2:** Implementação do portão `G_ARCH_DRIFT.py` para blindar o padrão Monólito Modular VSA.
3. Todo novo portão deverá obrigatoriamente respeitar a **Lei #13**, provando que morde via teste automatizado de falha deliberada (`exit 1`).
