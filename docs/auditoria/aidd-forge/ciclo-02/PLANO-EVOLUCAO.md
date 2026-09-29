# Plano de Evolução (Fase 2) - aidd-forge (Ciclo 02)

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de consolidar a governança da ferramenta `aidd-forge` em conformidade com o Laudo 15-D e a Definição de Pronto (DoD).

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor) e isolamento em Git Worktree efêmera. Para cada requisito funcional, testes automatizados (exit 0 / exit 1) devem ser criados antes da implementação real.

### Ticket 1: Blindagem de Templates TanStack Padrão-Ouro e Quality Gates (Refere-se a D13 / DoD 6)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `docs/auditoria/aidd-forge/ciclo-02/ENTREGA-TICKET-01.json`
- **Requisito TDD (Red):** Executar verificação determinística que falhe (exit 1) caso `gates/G_aidd_forge.py` ou os templates de governança TanStack contenham referências obsoletas ou stubs.
- **Implementação Técnica:**
  - Validar a conformidade bidirecional do gate `gates/G_aidd_forge.py` e execução de `gates/test_g_aidd_forge.py`.
  - Garantir integridade dos templates de governança em `tools/aidd-forge/templates/` com o Padrão-Ouro (Lei #11).
  - Executar a suíte de testes unitários da ferramenta em `tests/test_forge_*.py`.
- **Verificação (Green):** Bateria de testes e verificação de gates executam com sucesso (exit 0).
- **Construtor Prompt (EN):**
  - Run pytest on gates/test_g_aidd_forge.py to verify bidirectional bite.
  - Run pytest on all forge tests under tests/test_forge_*.py.
  - Verify that templates in tools/aidd-forge/templates/ adhere to TanStack gold standard.
  - Ensure zero stubs in forge scripts and assert exit 0.
  - Write handoff json to docs/auditoria/aidd-forge/ciclo-02/ENTREGA-TICKET-01.json.

### Ticket 2: Handoff Estruturado SHA-256 e Fechamento do Ciclo 02 (Refere-se a D15 / DoD 8)
- **Falha 15-D:** `D15. Output Consolidado e Handoff`
- **Artefato de Handoff:** `docs/auditoria/aidd-forge/ciclo-02/ENTREGA-TICKET-02.json`
- **Requisito TDD (Red):** Validar barreira determinística que reprove (exit 1) se o manifesto de handoff do ciclo 02 ou hashes dos módulos estiverem ausentes.
- **Implementação Técnica:**
  - Gerar e validar a assinatura estruturada de handoff da ferramenta `aidd-forge` com hashes SHA-256 de todos os 7 módulos em `scripts/` e do quality gate.
  - Emitir `docs/auditoria/aidd-forge/ciclo-02/ENTREGA-TICKET-02.json` registrando o inventário de entrega, conformidade com os 8 critérios de DoD e encerramento da Fase 3.
- **Verificação (Green):** Manifesto emitido e validado com sucesso (exit 0).
- **Construtor Prompt (EN):**
  - Run python ecossistema.py forge handoff emit to compute SHA-256 digests.
  - Verify that all seven modules in scripts directory have valid hashes.
  - Verify compliance against all eight DoD criteria in docs/auditoria/aidd-forge/ciclo-02/DOD.md.
  - Assert zero unverified claims and ensure exit 0.
  - Write handoff json to docs/auditoria/aidd-forge/ciclo-02/ENTREGA-TICKET-02.json.
