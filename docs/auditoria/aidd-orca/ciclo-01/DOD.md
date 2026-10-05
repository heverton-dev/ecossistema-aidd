# Definition of Done: aidd-orca (Auditoria 15-D)

## Metas e Critérios Binários de Aceitação

1. **D1 (Contratos e Regras):**
   A ferramenta `aidd-orca` deve proibir terminantemente o avanço de frentes não auditadas, a remoção arbitrária de `.orca/.orca_state.json` e a auto-aprovação de gates pelo mesmo harness da frente executora.

2. **D3 & D10 (Isolamento e Topologia):**
   A orquestração deve operar exclusivamente através de Git Worktrees efêmeras e branches dedicados, sem subagentes concorrentes em segundo plano no fluxo nativo.

3. **D11 & D13 (Circuit Breaker e Quality Gates):**
   Limites do circuit breaker (`max_execution_time_seconds: 1800`, `idle_heartbeat_seconds: 300`) devem ser preservados e cada frente deve passar por auditoria rigorosa de gates (`exit 0`) antes do merge.
