# Definition of Done: aidd-plan (Readequação Arquitetural)

## Metas e Critérios Binários de Aceitação

1. **D1 (Contratos e Regras):**
   A ferramenta `aidd-plan` deve conter `scripts/contrato.py` validando asserções programáticas do ciclo de vida de planos (status canônicos DRAFT/APPROVED/EM EXECUCAO, estrutura de diretório e proibição de aprovação sem aval).

2. **D3 (Isolamento de Raio de Impacto e Sandbox):**
   A ferramenta deve conter `PlanWorktreeManager` e `validar_caminho_escrita` em `scripts/isolamento.py`, confinando I/O estritamente a `docs/planos/` ou a diretório temporário/worktree efêmera (`SandboxViolationError`).

3. **D4 (Componentes e Fractalidade):**
   A ferramenta deve ser modularizada e empacotada dentro de `componentes/compartilhado/skills/aidd-plan/scripts/` com CLI desacoplada em `scripts/cli.py` delegando para o ecossistema.

4. **D11 (Tratamento de Exceções e Fallback Operacional):**
   Implementar `scripts/fallback.py` com resolução de colisões de nome, verificação e correção automática de cercas corrompidas e recuperação resiliente.

5. **D12 (Observabilidade e Frugalidade):**
   Implementar `scripts/observabilidade.py` (`RastreadorPlano`) medindo contagem de itens, estimativa de tokens, validação de notas e persistência de telemetria.

6. **D13 (Quality Gate de Repositório):**
   Deverá ser criado `gates/G_aidd_plan.py` que valide deterministicamente a conformidade das pastas em `docs/planos/`, checagem de cercas e ausência de notas sem evidência, retornando exit 0 ou exit 1.

7. **D14 (Critério de Rejeição e Rollback):**
   Implementar `scripts/rollback.py` (`executar_com_rollback`) revertendo alterações e arquivos parciais em caso de falha de validação ou exceção de execução.

8. **D15 (Output Consolidado e Handoff Assinado):**
   Implementar `scripts/handoff.py` emitindo manifesto de integridade com hash SHA-256 e assinatura HMAC-SHA256 para cada plano gerado ou transicionado.
