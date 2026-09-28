# Plano de Evolução (Fase 2) - mapa-pecas (Ciclo 04)

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F para o subsistema `mapa-pecas` (Ciclo 04), com o objetivo de sanear os 4 achados de catálogo através do framework Lens 15-D.

## Estratégia de Execução

Todos os tickets abaixo seguem ciclo TDD estrito e conferência determinística.

### Ticket 1: Padronização Canônica do Portão G_SEGREDOS (Refere-se a D9 / DoD 6)
- **Falha 15-D:** `D9. Segurança e Permissões`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-04/ENTREGA-TICKET-01.json`
- **Requisito TDD (Red):** `CAT-gates-versoes` acusa divergência de código no portão `G_SEGREDOS`.
- **Implementação Técnica:**
  - Sincronizar o conteúdo de `gates/G_SEGREDOS.py` (motor canônico `detect-secrets` OSS com baseline) para os scripts e templates de `tools/aidd-enterprise/` e `tools/aidd-master/`.
  - Eliminar o código legado de entropia Shannon caseira duplicado.
  - Verificar que o portão aprova em todas as pastas com exit code 0.
- **Verificação (Green):** Execução do catálogo registra `gates_mesmo_nome_codigo_diferente` zerado.
- **Construtor Prompt (EN):**
  - Standardize G_SEGREDOS.py across tools/aidd-enterprise/ and tools/aidd-master/ to match the canonical gates/G_SEGREDOS.py.
  - Remove legacy custom Shannon entropy implementations and point to the OSS detect-secrets engine.
  - Run python scripts/catalogo_pecas.py and verify gates_mesmo_nome_codigo_diferente is 0.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-04/ENTREGA-TICKET-01.json.

### Ticket 2: Registro do Portão G_aidd_forge no Pre-commit (Refere-se a D13 / DoD 6)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-04/ENTREGA-TICKET-02.json`
- **Requisito TDD (Red):** `CAT-declarados-fora-do-commit` acusa que `G_aidd_forge` está declarado na Lei #9 mas ausente dos ganchos de commit.
- **Implementação Técnica:**
  - Adicionar a execução de `gates/G_aidd_forge.py` no pre-commit hook ou mapeamento canônico de gates ativos no commit.
  - Assegurar que `G_aidd_forge.py` executa de forma rápida e hermética (< 2s).
- **Verificação (Green):** `CAT-declarados-fora-do-commit` zerado no catálogo.
- **Construtor Prompt (EN):**
  - Register gates/G_aidd_forge.py in the pre-commit hook scripts and governance gate mapping.
  - Ensure fast hermetic execution under 2 seconds.
  - Verify that CAT-declarados-fora-do-commit is eliminated in achados_ciclo.py.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-04/ENTREGA-TICKET-02.json.

### Ticket 3: Resolução e Fechamento das 7 Dimensões 15-D de aidd-forge (Refere-se a D3 / DoD 8)
- **Falha 15-D:** `D3. Dependências e Hermeticidade`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-04/ENTREGA-TICKET-03.json`
- **Requisito TDD (Red):** `CAT-15d-aidd-forge` acusa 7 dimensões 15-D reprovadas no laudo revisado de `aidd-forge`.
- **Implementação Técnica:**
  - Auditar os requisitos das dimensões D3, D10, D11, D12, D13, D14, D15 de `aidd-forge`.
  - Atualizar o laudo revisado com a conformidade comprovada das ferramentas de bootstrap e shielding.
- **Verificação (Green):** `CAT-15d-aidd-forge` zerado no catálogo.
- **Construtor Prompt (EN):**
  - Review open 15-D dimensions in docs/auditoria/aidd-forge/ciclo-01/LAUDO-15D-REVISADO.md.
  - Validate and mark compliant dimensions D3, D10, D11, D12, D13, D14, D15.
  - Verify CAT-15d-aidd-forge is eliminated in achados_ciclo.py.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-04/ENTREGA-TICKET-03.json.

### Ticket 4: Conclusão do Laudo Revisado de skills-ddd/ciclo-01 (Refere-se a D14 / DoD 8)
- **Falha 15-D:** `D14. Higiene e Ciclo de Vida`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-04/ENTREGA-TICKET-04.json`
- **Requisito TDD (Red):** `CAT-ciclo-skills-ddd-ciclo-01` acusa ausência de `LAUDO-15D-REVISADO.md` no ciclo de auditoria.
- **Implementação Técnica:**
  - Gerar o artefato formal `LAUDO-15D-REVISADO.md` em `docs/auditoria/skills-ddd/ciclo-01/` consolidando a conformidade das skills DDD.
  - Verificar a integridade documental de todos os ciclos da oficina de auditoria.
- **Verificação (Green):** `CAT-ciclo-skills-ddd-ciclo-01` zerado e catálogo com `totais.aberto == 0`.
- **Construtor Prompt (EN):**
  - Create docs/auditoria/skills-ddd/ciclo-01/LAUDO-15D-REVISADO.md consolidating DDD skills audit results.
  - Verify documentation completeness across all audit office cycles.
  - Verify CAT-ciclo-skills-ddd-ciclo-01 is resolved in achados_ciclo.py.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-04/ENTREGA-TICKET-04.json.
