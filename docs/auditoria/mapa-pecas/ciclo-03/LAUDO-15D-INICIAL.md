# Template de Auditoria de Ferramenta (Lens 15-D) - INICIAL (Fase 1: Inspetor)

Este documento descreve a auditoria arquitetural inicial da ferramenta `mapa-pecas` no Ciclo 03, dissecando sua anatomia com o framework Lens 15-D (The Agentic Anatomical Matrix) com estrita observância à Lei #8 (Honestidade de Rótulo).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `mapa-pecas`
- **Descrição Breve:** Catálogo factual de peças, dependências, encaixes e mapas visuais do ecossistema AIDD.
- **Comando de Gatilho:** `python scripts/catalogo_pecas.py` e `python scripts/mapa_visual.py <tipo>`

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** Contratos e esquemas de catálogo estruturados. No início do Ciclo 03, foram identificadas duplicidades reportadas entre scaffolds certificados e donas de tarefas/verbos/moldes sem formalização unificada.
- **D2. Input e Gatilhos:** CLI e scripts de mapas aceitam argumentos determinísticos e validam existência de catálogo.
- **D3. Raio de Impacto e Isolamento:** I/O contido em `docs/mapas-visuais/`, `docs/livros/mapas-aidd/` e `docs/auditoria/mapa-pecas/`.
- **D4. Componentes e Fractalidade:** Moldes de entrega agora associados a donas canônicas de entrega e governança.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** Mapeamento integral e visual das peças do ecossistema.
- **D6. O que o Estágio Faz:** Coleta AST, inspeciona rotas, mede encaixes e gera relatórios HTML.
- **D7. O que o Estágio Recebe:** Arquivos-fonte do repositório em disco sob git.
- **D8. O que o Estágio Processa:** Parser determinístico via módulo `ast` do Python sem heurística livre de LLM.
- **D9. O que o Estágio Entrega:** Catálogo consolidado `catalogo-pecas.json` e 13 mapas visuais navegáveis.
- **D10. Orquestração e Topologia:** Fluxo unificado sem atalhos internos e com titularidade canônica estabelecida.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** Tratamento estruturado de falhas com mensagens claras e exit codes determinísticos.
- **D12. Observabilidade e Frugalidade:** Arquivos idênticos governados e sincronizados via portão `G_DRIFT_NUCLEO_COMPARTILHADO.py`.

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** Portão `gates/G_mapa_pecas.py` provado com bateria unitária de exit 0 e exit 1.
- **D14. Critério de Rejeição (Rollback):** Flag `--check` determinística em todos os geradores retornando exit 1 se houver drift.
- **D15. Output Consolidado e Handoff:** Manifestos e handoffs estruturados emitidos a cada ciclo de evolução.

---

## 3. Matriz de Avaliação da Execução
- [x] D1 (Contratos e Regras): gaps de titularidade identificados para resolução.
- [x] D4 (Componentes e Fractalidade): donas de moldes e tarefas mapeadas.
- [x] D12 (Observabilidade e Frugalidade): sincronismo do núcleo compartilhado certificado.
- [x] D13 (Quality Gate G_mapa_pecas.py): portão aprovado e morde sob corrupção.
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas? Sim, 100% dos achados derivados de análise factual.
- [x] O output final passou em todos os Quality Gates e emitiu o Handoff? Sim.
