# Definition of Done: aidd-planner-runner (Readequação Arquitetural)

## Metas e Critérios Binários de Aceitação

1. **D3 (Isolamento de Raio de Impacto e Sandbox):**
   A ferramenta deve conter `PlannerWorktreeManager` e `validar_caminho_escrita` em `componentes/compartilhado/skills/aidd-planner/scripts/isolamento.py`, confinando I/O a diretórios autorizados ou Git Worktree efêmera (`SandboxViolationError`).

2. **D11 (Tratamento de Exceções e Fallback Operacional):**
   Implementar `componentes/compartilhado/skills/aidd-planner/scripts/fallback.py` com resolução de colisões de projeto e recuperação resiliente.

3. **D12 (Observabilidade e Frugalidade):**
   Implementar `componentes/compartilhado/skills/aidd-planner/scripts/observabilidade.py` (`RastreadorPlanner`) medindo métricas do blueprint (bounded contexts, entidades, endpoints, tokens estimados).

4. **D13 (Quality Gate de Repositório):**
   Deverá ser criado `gates/G_aidd_planner_runner.py` que valide deterministicamente a conformidade de projetos gerados pelo planner sob a Lei #13.

5. **D14 (Critério de Rejeição e Rollback):**
   Implementar `componentes/compartilhado/skills/aidd-planner/scripts/rollback.py` (`executar_com_rollback`) revertendo scaffolds e arquivos parciais em caso de falha de validação ou exceção.

6. **D15 (Output Consolidado e Handoff Assinado):**
   Implementar `componentes/compartilhado/skills/aidd-planner/scripts/handoff.py` emitindo manifesto de handoff assinado com HMAC-SHA256 validando integridade do `PLANNER.json` e arquivos associados.
