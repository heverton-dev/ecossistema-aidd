# Plano de Evolução (Fase 2) - mapa-pecas (Ciclo 03)

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F para o subsistema `mapa-pecas` (Ciclo 03), com o objetivo de sanear os 5 achados remanescentes de `ACHADOS.json` através do framework Lens 15-D.

## Estratégia de Execução
Todos os tickets abaixo seguem ciclo TDD estrito e conferência determinística. Cada ticket aborda um agrupamento funcional dos achados de catálogo com evidência verificável e handoff estruturado.

### Ticket 1: Titularidade Canônica de Tarefas e Verbos CLI (Refere-se a D4 / DoD 1)
- **Falha 15-D:** `D4. Componentes e Fractalidade`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-03/ENTREGA-TICKET-01.json`
- **Requisito TDD (Red):** Catálogo deve acusar tarefas com donas conflitantes e verbos de CLI sem dona canônica formal.
- **Implementação Técnica:**
  - Declarar tabela `DONAS_TAREFAS` com a ferramenta dona canônica de cada uma das 10 tarefas mapeadas no ecossistema.
  - Declarar tabela `DONAS_VERBOS` atribuindo cada verbo CLI duplicado à sua ferramenta primária de referência.
  - Atualizar `achar_repeticoes` em `scripts/catalogo_pecas.py` para respeitar as donas canônicas declaradas.
- **Verificação (Green):** Execução do catálogo de peças registra `tarefas_com_varias_donas` e `verbos_cli_repetidos` zerados.
- **Construtor Prompt (EN):**
  - Define canonical task ownership in DONAS_TAREFAS table in scripts/catalogo_pecas.py.
  - Define canonical CLI verb ownership in DONAS_VERBOS table in scripts/catalogo_pecas.py.
  - Filter declared canonical tasks and verbs in achar_repeticoes.
  - Verify that catalog repetition check reports zero task and verb conflicts.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-03/ENTREGA-TICKET-01.json.

### Ticket 2: Governança e Titularidade de Moldes de Entrega (Refere-se a D4 / DoD 2)
- **Falha 15-D:** `D4. Componentes e Fractalidade`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-03/ENTREGA-TICKET-02.json`
- **Requisito TDD (Red):** Diagnóstico de achados acusa moldes repetidos entre ferramentas sem dona primária formal.
- **Implementação Técnica:**
  - Mapear titularidade em `DONAS_MOLDES` para os scaffolds de entrega compartilhados (`agents`, `core`, `v2`, `gates`, `rules`, etc.).
  - Adicionar o metadado `dona_canonica` em cada molde coletado por `coletar_moldes_entrega`.
  - Atualizar `scripts/achados_ciclo.py` para ignorar moldes que possuem dona formal em `DONAS_MOLDES`.
- **Verificação (Green):** `achados_ciclo.py` não reporta mais o achado `CAT-moldes-repetidos`.
- **Construtor Prompt (EN):**
  - Add dona_canonica to coletar_moldes_entrega in scripts/catalogo_pecas.py using DONAS_MOLDES.
  - Update scripts/achados_ciclo.py to filter delivery templates governed by DONAS_MOLDES.
  - Run achados_ciclo.py and assert CAT-moldes-repetidos is eliminated.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-03/ENTREGA-TICKET-02.json.

### Ticket 3: Certificação de Cópias do Núcleo Compartilhado (Refere-se a D12 / DoD 5)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-03/ENTREGA-TICKET-03.json`
- **Requisito TDD (Red):** `CAT-arquivos-identicos` acusa falsos positivos em arquivos governados pelo portão de drift do núcleo compartilhado.
- **Implementação Técnica:**
  - Implementar `_eh_copia_governada` em `scripts/catalogo_pecas.py` reconhecendo o cluster de sincronismo governado (`aidd-master`, `aidd-enterprise`, `componentes`, `gates`, `templates`).
  - Filtrar réplicas intencionais de arquitetura mantidas sem acoplamento de runtime per Lei #1 e Lei #6.
  - Assegurar que qualquer arquivo duplicado fora da governança de drift continue sendo barrado.
- **Verificação (Green):** `CAT-arquivos-identicos` zerado em `ACHADOS.json`.
- **Construtor Prompt (EN):**
  - Implement _eh_copia_governada in scripts/catalogo_pecas.py to validate synchronized architectural clusters.
  - Filter governed baseline files from accidental duplicate findings in achar_repeticoes.
  - Verify G_DRIFT_NUCLEO_COMPARTILHADO.py passes with exit 0.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-03/ENTREGA-TICKET-03.json.

### Ticket 4: Conclusão do Ciclo 4F e Recompilação de Artefatos (Refere-se a D13 / DoD 6)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-03/ENTREGA-TICKET-04.json`
- **Requisito TDD (Red):** Auditoria acusa falta de documentos do ciclo-03 e mapas visuais HTML desatualizados.
- **Implementação Técnica:**
  - Gerar todos os documentos do Ciclo 03 (`LAUDO-15D-INICIAL.md`, `RELATORIO-CONSTRUTOR.md`, `LAUDO-15D-REVISADO.md`, `RESUMO-USUARIO.md`, `RELATORIO-TECNICO.md`).
  - Recompilar catálogo `catalogo-pecas.json` e todos os 13 mapas visuais HTML e o manual de montagem.
  - Executar verificação com `--check` em todos os geradores e rodar a suíte do `G_mapa_pecas.py`.
- **Verificação (Green):** Todos os 14 mapas passam no `--check` e `pytest gates/test_g_mapa_pecas.py` passa 100%.
- **Construtor Prompt (EN):**
  - Generate complete 4F audit cycle documents in docs/auditoria/mapa-pecas/ciclo-03/.
  - Recompile catalogo-pecas.json and all 13 HTML maps plus assembly manual.
  - Verify all maps with --check flag and run quality gate G_mapa_pecas.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-03/ENTREGA-TICKET-04.json.
