# Definition of Done: aidd-handoff (Readequação Arquitetural)

## Metas e Critérios Binários de Aceitação

1. **D3 (Isolamento de Raio de Impacto e Worktree):**
   A ferramenta `aidd-handoff` deve conter `HandoffWorktreeManager` em `scripts/isolamento.py` bloqueando escrita fora de `docs/secoes/` ou de Git Worktree efêmera.

2. **D4 (Componentes, Fractalidade e CLI Fallback):**
   A ferramenta deve expor interface determinística local via `scripts/cli.py` e poder ser acionada via terminal `python ecossistema.py handoff {gerar,validar,emitir}` sem depender exclusivamente de chat.

3. **D8 (Motor Determinístico de Serialização):**
   Implementar `scripts/motor.py` para extrair dados git (`git log`, `git diff --stat`), validar presença das 5 seções canônicas e verificar ausência de código-fonte colado via AST/regex mecânico.

4. **D11 (Tratamento de Exceções e Fallback Operacional):**
   Implementar `scripts/fallback.py` com resolução de colisões de nome (`-2`), recuperação em contexto pesado e tolerância a encoding sem falha catastrófica.

5. **D12 (Observabilidade e Frugalidade):**
   Implementar `scripts/observabilidade.py` (`RastreadorHandoff`) medindo contagem de seções, linhas totais, estimativa de tokens e persistindo métricas.

6. **D13 (Quality Gate Spec):**
   Deverá ser criado `gates/G_aidd_handoff.py` que valide deterministicamente a conformidade das 5 seções, ausência de código colado e integridade de formatação, retornando exit 0 ou exit 1.

7. **D14 (Critério de Rejeição e Rollback):**
   Implementar `scripts/rollback.py` que reverta arquivos gerados parcialmente em caso de falha de validação ou erro de I/O.

8. **D15 (Output Consolidado e Handoff Assinado):**
   Implementar `scripts/handoff.py` emitindo manifesto de handoff assinado com HMAC-SHA256 validando integridade do artefato.
