# Phase 08 — Implementador (Micro-Ambiente) v3.0

## Escopo
Geração de código funcional real com verificação via pytest + loop de correção + auto-cura.

## Restrições
- LLM via subagente efêmero (Context-Purge Engine) — descarte imediato de contexto
- Schema SQLite compartilhado derivado ANTES de implementar scripts isolados
- Validação AST mecânica (_validar_contrato_ast) antes de pytest real
- Loop de correção: traceback real do pytest reenviado ao LLM (até 3 tentativas)
- UTF-8 explícito na escrita de arquivos gerados
- CRUD 100% Completo: rotas e repositories de entidades centrais DEVEM implementar Create, Read, Update (PUT/PATCH com edição total) e Delete.
- Impeccable Design: frontend sem 'AI Slop' (paleta Zinc neutra profunda, tipografia tabular, microinterações 150ms). PROIBIDO usar `alert()`, `confirm()` ou `prompt()` do navegador — usar `static/share/ui_dialogs.js`.
- Swagger Dark Mode: FastAPI docs com tema escuro nativo.
- Studio MCP: disponibilizar endpoint JSON-RPC 2.0 (/mcp/rpc) com listagem e execução de tools para agentes de IA.
- Studio Webhooks: engine assíncrona de eventos com HMAC SHA-256 (header X-AIDD-Signature) e histórico de entregas.

## Result Monad (Sprint 06)
- Toda operação de implementação DEVE usar o padrão Result Monad:
  - `Result.ok(valor)` para sucesso — contém o artefato gerado
  - `Result.fail(erro)` para falha — contém mensagem + traceback
- Funções NUNCA levantam exceções para controle de fluxo — retornam Result
- O pipeline encadeia Results: se qualquer etapa retorna Err, o pipeline para
- Result é inspecionável: `result.is_ok()`, `result.is_err()`, `result.unwrap()`
- `_chamar_llm_result()` é o ponto único de chamada LLM com Result

## Micro-Tasks AST (Sprint 06)
- Script é decomposto em MicroTasks via AST parsing estático (Zero Token)
- Cada MicroTask = 1 função/método = 1 unidade de teste
- `decompor_script_em_microtasks()` extrai funções do código gerado
- `decompor_e_implementar_microtasks()` verifica/testa cada micro-task
- Se teste passa, micro-tasks são apenas para granularidade de auditoria

## Post-Mortem 5-Porquês (Sprint 06)
- Quando pytest falha, `PostMortemAnalyzer.analisar_falha()` executa:
  1. Isola o traceback relevante
  2. Extrai causa raiz (último erro)
  3. Classifica o tipo de falha (assertion, import, type, etc.)
  4. Identifica o padrão/causa comum
  5. Sugere correção específica
- Auto-Cura: regenera APENAS a função afetada (não o script inteiro)
- Máximo 3 tentativas de auto-cura (`MAX_TENTATIVAS_MICROTASK`)

## pytest
- Testes DEVE ser executados via `subprocess.run([sys.executable, '-m', 'pytest', ...])`
- Traceback real capturado e reenviado ao LLM para correção
- 100% dos testes DEVE passar — nunca estimado, sempre medido
- Testes gerados incluem: unitários por script + integração cross-script

## Gates
- I1: Todos os scripts do design implementados em disco
- I2: pytest coleta sem erro de import
- I3: 100% dos testes passando (nunca estimado)
- I4: CLI smoke-test (--help exit code 0)
- I5: Teste de integração cross-script gerado e passando
- I6: Clean Architecture/DDD — deliverables em conformidade com G_ARQUITETURA_DELIVERABLE

## Clean Architecture + DDD (Item 9)
- Prompt inclui regras de organização em camadas quando script requer persistência/API.
- Feature 'arquitetura' derivada de sqlite|crud|api — ativa BLOCO_REGRA_ARQUITETURA no prompt.
- Auditoria por arquivo (G_ARQUITETURA_DELIVERABLE) roda após microtasks OK.
- Violações alimentam o loop de correção via PROMPT_CORRIGIR_ARQUITETURA (fase phase_08_fix_arquitetura).
- Se violações persistem em 3 tentativas, script é marcado como falho.
- Reutilização existente (cache) também verifica arquitetura antes de reaproveitar.

## Saída
- `_phase_08_index.json` em `.aidd/cache/data/`
- `src/` com scripts implementados
- `tests/` com testes gerados

## Tokens
- Consumo: variável (chamadas reais de LLM, incluindo correções)
- Determinismo: 0% (pura LLM com verificação mecânica)
