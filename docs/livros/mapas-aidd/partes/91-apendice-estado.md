# Apêndice B — Estado honesto

Tabela consolidada de todos os achados dos mapas, gerada de `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`. Em aberto por gravidade: 0 alta, 1 média, 4 baixa. Cada achado em aberto traz no arquivo o texto pronto para abrir o fluxo de melhoria (`pedido_melhoria`).

## Em aberto (5)

| Achado | Gravidade · mapa |
| :-------------------------------------- | :-------------------------------------------- |
| 1 guardas com o mesmo nome e código diferente (`CAT-gates-versoes`) | Média · guardas |
| Ciclo de auditoria sem todos os documentos: aidd-master/ciclo-01 (`CAT-ciclo-aidd-master-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-open/ciclo-01 (`CAT-ciclo-aidd-open-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-ops/ciclo-01 (`CAT-ciclo-aidd-ops-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: fronteiras-ferramentas/ciclo-01 (`CAT-ciclo-fronteiras-ferramentas-ciclo-01`) | Baixa · oficina |

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
