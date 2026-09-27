# Apêndice B — Estado honesto

Tabela consolidada de todos os achados dos mapas, gerada de `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`. Em aberto por gravidade: 9 alta, 13 média, 9 baixa. Cada achado em aberto traz no arquivo o texto pronto para abrir o fluxo de melhoria (`pedido_melhoria`).

## Em aberto (30)

| Achado | Gravidade · mapa |
| :-------------------------------------- | :-------------------------------------------- |
| 100 arquivos idênticos copiados entre ferramentas (`CAT-arquivos-identicos`) | Alta · ferramentas |
| Chamada da receita não encaixa: ecossistema.py bridge scan \-\-dir <var> (`CAT-encaixe-ecossistema-py-bridge-scan-dir-var`) | Alta · encaixes |
| Chamada da receita não encaixa: ecossistema.py factory curate \-\-dominio <var> \-\-output <var> (`CAT-encaixe-ecossistema-py-factory-curate-dominio-var-output-var`) | Alta · encaixes |
| Etapa da receita não chama ferramenta: etapa_06_ops (`CAT-etapa-sem-ferramenta-etapa-06-ops`) | Alta · encaixes |
| Etapa da receita não chama ferramenta: etapa_07_auditoria (`CAT-etapa-sem-ferramenta-etapa-07-auditoria`) | Alta · encaixes |
| A validação de contrato aprova quando não consegue conferir (`VER-001`) | Alta · encaixes |
| Etapa 7 grava CONFORME_100_POR_CENTO sem rodar guarda nenhum (`VER-002`) | Alta · encaixes |
| Etapa 3 do Fluxo 02 chama o factory sem o PLANO-INFRAESTRUTURA.json que ele exige (`VER-003`) | Alta · encaixes |
| Corrida entre testes no G_PORTAO_PROVA_QUE_MORDE (`VER-005`) | Alta · guardas |
| 7 dimensões 15-D com falha no laudo de aidd-melhoria (`CAT-15d-aidd-melhoria`) | Média · lente15d |
| Etapa mexe por dentro de uma ferramenta: etapa_02_planner (`CAT-atalho-interno-etapa-02-planner`) | Média · encaixes |
| Etapa mexe por dentro de uma ferramenta: etapa_03_engine (`CAT-atalho-interno-etapa-03-engine`) | Média · encaixes |
| 10 declarações de lei que o meta-guarda não lê (`CAT-declaracoes-invisiveis`) | Média · leis |
| 7 guardas declarados em lei que não rodam no commit (`CAT-declarados-fora-do-commit`) | Média · leis |
| 10 guardas com o mesmo nome e código diferente (`CAT-gates-versoes`) | Média · guardas |
| 7 moldes de entrega com o mesmo nome em várias ferramentas (`CAT-moldes-repetidos`) | Média · moldes |
| Pasta legada ainda versionada: .gemini/skills (`CAT-pasta-legada-gemini-skills`) | Média · harnesses |
| 10 tarefas feitas por mais de uma ferramenta (`CAT-tarefas-varias-donas`) | Média · ferramentas |
| O \-\-dry-run do orquestrador grava README-USUARIO.md no disco (`VER-004`) | Média · encaixes |
| 6 testes falhando na aidd-orca, fora do pre-commit (`VER-006`) | Média · skills |
| G_HANDOFF_MELHORIA reprova com o handoff-melhoria.json versionado (`VER-008`) | Média · leis |
| Ciclo de auditoria sem todos os documentos: mapa-pecas/ciclo-01 (`CAT-ciclo-mapa-pecas-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: skills-pocock/ciclo-01 (`CAT-ciclo-skills-pocock-ciclo-01`) | Baixa · oficina |
| 22 guardas da raiz que nenhuma lei declara (`CAT-guardas-sem-lei`) | Baixa · leis |
| 3 MCPs das ferramentas que nenhum agente deste repositório usa (`CAT-mcps-internos`) | Baixa · conexoes |
| 3 scripts que nenhum código chama (`CAT-scripts-sem-chamador`) | Baixa · scripts |
| 20 verbos de CLI em mais de uma ferramenta (`CAT-verbos-repetidos`) | Baixa · ferramentas |
| 2 testes falhando na aidd-improvement, fora do pre-commit (`VER-007`) | Baixa · skills |
| forge audit: AGENTS.md genérico (G04) e forge init ainda cria .agent/ (`VER-010`) | Baixa · ferramentas |
| O detect-secrets grava o caminho absoluto da máquina no .secrets.baseline (`VER-011`) | Baixa · guardas |

## Sob suspeita (1)

| Achado | Gravidade · mapa |
| :-------------------------------------- | :-------------------------------------------- |
| O .githooks/pre-commit pode falhar sem mensagem (`VER-009`) | Média · scripts |

## Resolvidos (3)

| Achado | Gravidade · mapa |
| :-------------------------------------- | :-------------------------------------------- |
| O sync de componentes puxava skills dos harnesses de volta para a fonte (`VER-013`) | Alta · harnesses |
| Skills repetidas, nomes misturados e terceiros copiados na fonte única (`VER-012`) | Média · skills |
| Comandos /aidd-livro-texto e /planner sem skill válida (`VER-014`) | Média · comandos |
