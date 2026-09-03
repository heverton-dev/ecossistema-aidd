# AGENTS.md — Regras de Operação e Governança para Agentes de IA

> **Projeto:** AIDD Master Enterprise  
> **Agnóstico a Harness:** Aplicável a Antigravity, Claude Code, Cursor, Codex, Gemini CLI, OpenCode e MimoCode.  
> **Idioma Padrão de Comunicação com o Usuário:** **PT-BR (Português do Brasil)**.

---

## 1. Protocolo Tríplice de Economia de Tokens (Caveman Ultra)

Para maximizar a eficiência de contexto sem perda de rigor técnico:

1. **Entrada (Regras em Inglês/PT-BR):** Leia com foco nos contratos arquiteturais essenciais.
2. **Pensamento Interno (Caveman Thinking):** Para TODOS os blocos internos de raciocínio, utilize estilo CAVEMAN telegráfico ultra-denso (máximo 3 a 5 linhas):
   - Frases telegráficas, sem artigos ou preposições desnecessárias.
   - Abreviações: "verificar" ➔ "ver", "necessário" ➔ "nec.", "implementar" ➔ "impl.".
   - Exemplo: *"usr quer modulo billing. ver rotas crm. criar fatia vertical. testar exit 0."*
3. **Saída ao Usuário (Português do Brasil de Alto Padrão):**
   - Respostas concisas, estruturadas e diretas.
   - Entregar código completo, fortemente tipado, com Result Monad, sem stubs e sem `pass`.

---

## 2. Regras Arquiteturais Inegociáveis (Quality Gates)

Toda alteração de código ou criação de nova funcionalidade DEVE respeitar rigorosamente os 10 Quality Gates:

1. **Isolamento de Bounded Context (G_ARQUITETURA):**
   - É **estritamente proibido** importar diretamente outro módulo (`import modules.erp` dentro de `modules.crm`).
   - A comunicação inter-módulos DEVE ocorrer exclusivamente via `EventBus` ou Shared Kernel (`core.*`).
2. **Result Monad Obrigatório (G_QUALIDADE):**
   - Métodos de serviço em `services.py` DEVEM retornar `Result[T, E]` (`Result.ok()` ou `Result.fail()`).
   - Nunca propague exceções cruas para as camadas superiores.
3. **Persistência Segura (G_SEGURANCA):**
   - Em SQLite, utilize SEMPRE modo WAL (`PRAGMA journal_mode=WAL;`).
   - Queries SQL DEVEM ser 100% parametrizadas com placeholders (`?` ou `%s`). **Zero concatenação de strings** em chamadas `execute()`.
   - Utilize soft-delete (`deletado_em IS NULL`). Nunca execute `DELETE` físico em tabelas de negócio.
4. **Zero Stubs e Mocks Incompletos (G_QUALIDADE):**
   - Proibido deixar funções vazias com `pass` ou comentários `TODO`.
5. **Observabilidade (G_PERFORMANCE):**
   - Instrumente funções críticas de serviço com o decorator `@trace_span(name)`.
   - Mantenha latências de requisições dentro do teto de SLA (`p99 < 200ms`).

---

## 3. Roteamento de Comandos e Intenções

| Intenção do Usuário | Comando CLI Mecânico a Executar |
| :--- | :--- |
| Criar/Compor novos módulos | `python scripts/aidd.py compose-orca <modulos>` |
| Adicionar uma fatia vertical | `python scripts/aidd.py add-module <nome>` |
| Rodar testes unitários | `python -m pytest tests/` |
| Validar todos os 10 Gates | `python scripts/run_all.py` |
| Exportar histórico da sessão | Executar a skill `/resumo-sessao` |
| Injetar skill/mcp/rule/spec/config/agent | `python scripts/aidd.py inject <tipo> <nome>` (ou frase PT-BR: "crie uma skill de X") |

---

## 4. Localização dos Componentes Centrais

* **Kernel e Governança:** `src/core/` (`database_adapter.py`, `events.py`, `result.py`, `opentelemetry.py`, `subagent_engine.py`).
* **Fatias de Negócio:** `src/modules/<dominio>/` (`models.py`, `services.py`, `routes.py`).
* **Gates Determinísticos:** `scripts/gates/` (`G_*.py`).
* **Documentação Oficial:** `docs/` (`01-fases-de-execucao.md` a `06-manual-de-uso.md`).
* **Injetor Universal de Componentes:** `src/core/` (`schema_injector_request.json`, `profiles_registry.py`, `detector_camada.py`, `materializador.py`, `sincronizador_harness.py`); catálogo em `CAPABILITIES.json`; gate em `scripts/gates/G_INJECT.py`.
