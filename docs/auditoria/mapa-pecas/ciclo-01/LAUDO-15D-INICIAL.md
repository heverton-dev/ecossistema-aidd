# Template de Auditoria de Ferramenta (Lens 15-D) - mapa-pecas

Este documento descreve a estrutura canônica para auditar a ferramenta e subsistema `mapa-pecas` (mapas visuais e catálogo de peças) do ecossistema AIDD, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix) com base nos 34 achados críticos levantados no catálogo e mapas visuais.

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `mapa-pecas`
- **Descrição Breve:** Subsistema de catálogo factual, extração de encaixes e mapas visuais do ecossistema AIDD (`docs/mapas-visuais/`, `scripts/catalogo_pecas.py`, `scripts/achados_ciclo.py`).
- **Comando de Gatilho:** `python scripts/catalogo_pecas.py` / `python scripts/achados_ciclo.py` / `/aidd-visual-maps`

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** FAILED: Not implemented. 10 declarações de lei no `AGENTS.md` não são reconhecidas pelo meta-guarda por comentários após `(provado)` (CAT-declaracoes-invisiveis); 22 guardas da raiz não possuem lei correspondente associada (CAT-guardas-sem-lei); e a validação de contrato em `G_CONTRACT_ROT` aprova falsamente quando não consegue inspecionar o contrato (VER-001).
- **D2. Input e Gatilhos:** Recebe como gatilho comandos de script e comandos de auditoria (`python scripts/catalogo_pecas.py` e `python scripts/achados_ciclo.py`). Porém, comandos slash `/aidd-livro-texto` e `/planner` apontam para referências inexistentes ou mal formatadas (VER-014), gerando inconsistência de gatilho no ecossistema.
- **D3. Raio de Impacto e Isolamento:** FAILED: Not implemented. O comando `--dry-run` do orquestrador altera o disco gravando `README-USUARIO.md` (VER-004), violando o isolamento de simulação; o `detect-secrets` vaza o caminho absoluto da máquina local dentro de `.secrets.baseline` (VER-011).
- **D4. Componentes e Fractalidade:** FAILED: Not implemented. O sync de componentes puxava skills modificadas dos harnesses de volta para a fonte `componentes/` (VER-013); há skills repetidas, nomes misturados e cópias de terceiros na fonte única (VER-012); pasta legada `.gemini/skills` ainda versionada (CAT-pasta-legada-gemini-skills); e 3 MCPs internos órfãos não consumidos por nenhum agente (CAT-mcps-internos).

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** A visão pretendida é mapear 100% da anatomia do ecossistema em 12 mapas visuais navegáveis, integrando catálogo factual de peças, leis, guardas e encaixes.
- **[Estágio 1 - Catálogo de Peças] D6. O que o Estágio Faz:** Varre o repositório e gera `docs/auditoria/mapa-pecas/catalogo-pecas.json`.
- **[Estágio 1 - Catálogo de Peças] D7. O que o Estágio Recebe:** Arquivos-fonte do repositório (`tools/`, `gates/`, `componentes/`, `scripts/`, `AGENTS.md`).
- **[Estágio 1 - Catálogo de Peças] D8. O que o Estágio Processa:** FAILED: Not implemented. A análise de encaixes revelou que etapas do orquestrador usam atalhos internos mexendo por dentro de ferramentas (`etapa_02_planner` e `etapa_03_engine`, CAT-atalho-interno) e 10 tarefas são duplicadas por mais de uma ferramenta (CAT-tarefas-varias-donas).
- **[Estágio 1 - Catálogo de Peças] D9. O que o Estágio Entrega:** Arquivo `catalogo-pecas.json` contendo a lista consolidada de peças e métricas.
- **D10. Orquestração e Topologia:** FAILED: Not implemented. Chamadas de encaixe da receita falham (`ecossistema.py bridge scan --dir <var>` e `ecossistema.py factory curate --dominio <var> --output <var>`, CAT-encaixe); etapas 6 e 7 do orquestrador não chamam ferramentas reais (CAT-etapa-sem-ferramenta); etapa 3 do Fluxo 02 chama factory sem `PLANO-INFRAESTRUTURA.json` (VER-003); e a etapa 7 grava `CONFORME_100_POR_CENTO` sem rodar nenhum guarda (VER-002).

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** FAILED: Not implemented. O hook `.githooks/pre-commit` silencia falhas terminando sem mensagem explicativa clara (VER-009); há condição de corrida entre testes concorrentes no `G_PORTAO_PROVA_QUE_MORDE` (VER-005).
- **D12. Observabilidade e Frugalidade:** FAILED: Not implemented. 100 arquivos idênticos duplicados entre ferramentas em `tools/` gerando desperdício e risco de divergência (CAT-arquivos-identicos); 7 moldes de entrega replicados (CAT-moldes-repetidos); 20 verbos repetidos na CLI (CAT-verbos-repetidos); e 3 scripts órfãos sem chamador (CAT-scripts-sem-chamador).

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** FAILED: Not implemented. 7 guardas declarados em lei não rodam no pre-commit (CAT-declarados-fora-do-commit); 10 guardas homônimos possuem código divergente entre raiz e ferramentas (CAT-gates-versoes); `G_HANDOFF_MELHORIA` reprova com o manifesto versionado (VER-008); 6 testes unitários quebrando em `tools/aidd-orca` (VER-006); 2 testes quebrando em `tools/aidd-improvement` (VER-007); e `aidd-melhoria` falha em 7 dimensões 15-D (CAT-15d-aidd-melhoria).
- **D14. Critério de Rejeição (Rollback):** FAILED: Not implemented. Não há guarda determinístico unitário `gates/G_mapa_pecas.py` que prove rejeição com exit 1 quando o catálogo divergir da realidade do repositório.
- **D15. Output Consolidado e Handoff:** FAILED: Not implemented. Ciclos de auditoria `mapa-pecas/ciclo-01` e `skills-pocock/ciclo-01` estavam incompletos sem todos os documentos canônicos do protocolo 4F (CAT-ciclo-mapa-pecas-ciclo-01 e CAT-ciclo-skills-pocock-ciclo-01).

---

## 3. Matriz de Avaliação da Execução
- [ ] A ferramenta isolou seu raio de impacto corretamente?
- [ ] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas?
- [ ] O output final passou em todos os Quality Gates e emitiu o Handoff?
