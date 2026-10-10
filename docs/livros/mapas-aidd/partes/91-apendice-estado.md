# Apêndice B — Estado honesto

Tabela consolidada de todos os achados dos mapas, gerada de `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`. Em aberto por gravidade: 0 alta, 3 média, 28 baixa. Cada achado em aberto traz no arquivo o texto pronto para abrir o fluxo de melhoria (`pedido_melhoria`).

## Em aberto (31)

| Achado | Gravidade · mapa |
| :-------------------------------------- | :-------------------------------------------- |
| 1 dimensões 15-D com falha no laudo de aidd-orca (`CAT-15d-aidd-orca`) | Média · lente15d |
| 5 guardas declarados em lei que não rodam no commit (`CAT-declarados-fora-do-commit`) | Média · leis |
| 10 guardas com o mesmo nome e código diferente (`CAT-gates-versoes`) | Média · guardas |
| Ciclo de auditoria sem todos os documentos: aidd-componentes/ciclo-01 (`CAT-ciclo-aidd-componentes-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-dependencias/ciclo-01 (`CAT-ciclo-aidd-dependencias-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-dispatch-runner/ciclo-01 (`CAT-ciclo-aidd-dispatch-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-enterprise-runner/ciclo-01 (`CAT-ciclo-aidd-enterprise-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-forge-runner/ciclo-01 (`CAT-ciclo-aidd-forge-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-freedom-runner/ciclo-01 (`CAT-ciclo-aidd-freedom-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-livro-texto/ciclo-01 (`CAT-ciclo-aidd-livro-texto-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-master/ciclo-01 (`CAT-ciclo-aidd-master-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-master/ciclo-02 (`CAT-ciclo-aidd-master-ciclo-02`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-master-runner/ciclo-01 (`CAT-ciclo-aidd-master-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-mcp/ciclo-01 (`CAT-ciclo-aidd-mcp-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-open-runner/ciclo-01 (`CAT-ciclo-aidd-open-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-ops-runner/ciclo-01 (`CAT-ciclo-aidd-ops-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-orca/ciclo-01 (`CAT-ciclo-aidd-orca-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-orchestrator-runner/ciclo-01 (`CAT-ciclo-aidd-orchestrator-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-pipeline-runner/ciclo-01 (`CAT-ciclo-aidd-pipeline-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-pure-runner/ciclo-01 (`CAT-ciclo-aidd-pure-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-session/ciclo-01 (`CAT-ciclo-aidd-session-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-skills/ciclo-02 (`CAT-ciclo-aidd-skills-ciclo-02`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: calibracao-pipeline/ciclo-01 (`CAT-ciclo-calibracao-pipeline-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: code-review-graph/ciclo-01 (`CAT-ciclo-code-review-graph-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: fluxo-01-runner/ciclo-01 (`CAT-ciclo-fluxo-01-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: fluxo-02-runner/ciclo-01 (`CAT-ciclo-fluxo-02-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: fluxo-03-runner/ciclo-01 (`CAT-ciclo-fluxo-03-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: fronteiras-ferramentas/ciclo-01 (`CAT-ciclo-fronteiras-ferramentas-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: quadro-kanban-pipelines/ciclo-01 (`CAT-ciclo-quadro-kanban-pipelines-ciclo-01`) | Baixa · oficina |
| 1 guardas da raiz que nenhuma lei declara (`CAT-guardas-sem-lei`) | Baixa · leis |
| 5 scripts que nenhum código chama (`CAT-scripts-sem-chamador`) | Baixa · scripts |

## Resolvidos (14)

| Achado | Gravidade · mapa |
| :-------------------------------------- | :-------------------------------------------- |
| A validação de contrato aprova quando não consegue conferir (`VER-001`) | Alta · encaixes |
| Etapa 7 grava CONFORME_100_POR_CENTO sem rodar guarda nenhum (`VER-002`) | Alta · encaixes |
| Etapa 3 do Fluxo 02 chama o factory sem o PLANO-INFRAESTRUTURA.json que ele exige (`VER-003`) | Alta · encaixes |
| Corrida entre testes no G_PORTAO_PROVA_QUE_MORDE (`VER-005`) | Alta · guardas |
| O sync de componentes puxava skills dos harnesses de volta para a fonte (`VER-013`) | Alta · harnesses |
| O \-\-dry-run do orquestrador grava README-USUARIO.md no disco (`VER-004`) | Média · encaixes |
| 6 testes falhando na aidd-orca, fora do pre-commit (`VER-006`) | Média · skills |
| G_HANDOFF_MELHORIA reprova com o handoff-melhoria.json versionado (`VER-008`) | Média · leis |
| O .githooks/pre-commit pode falhar sem mensagem (`VER-009`) | Média · scripts |
| Skills repetidas, nomes misturados e terceiros copiados na fonte única (`VER-012`) | Média · skills |
| Comandos /aidd-livro-texto e /planner sem skill válida (`VER-014`) | Média · comandos |
| 2 testes falhando na aidd-improvement, fora do pre-commit (`VER-007`) | Baixa · skills |
| forge audit: AGENTS.md genérico (G04) e forge init ainda cria .agent/ (`VER-010`) | Baixa · ferramentas |
| O detect-secrets grava o caminho absoluto da máquina no .secrets.baseline (`VER-011`) | Baixa · guardas |
