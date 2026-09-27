# Relatório do Construtor — mapa-pecas (Ciclo 01)

> **Ciclo:** mapa-pecas/ciclo-01  
> **Data:** 27/09/2026  
> **Status:** CONCLUÍDO (6 de 6 tickets executados e aprovados)  

---

## 1. Resumo Executivo da Construção

Neste ciclo de evolução técnica do subsistema **mapa-pecas**, foram atacados os ~30 pontos críticos identificados no laudo anatômico 15-D inicial e no catálogo de peças, divididos em 6 tickets estruturados e verificados por testes reais.

---

## 2. Detalhamento por Ticket

### Ticket 1: Leis Invisíveis e Corrida no Meta-Guarda
- **Status:** CONCLUÍDO
- **Entregável:** `docs/auditoria/mapa-pecas/ciclo-01/ENTREGA-TICKET-01.json`
- **Ações:**
  - Ajustado regex em `gates/G_LEI_DECLARA_PORTAO.py` para aceitar anotações pós-`(provado)`, zerando todas as 10 leis tidas como invisíveis.
  - Corrigido `gates/test_g_determinismo_lei_1.py` para usar diretório temporário isolado via `tempfile.TemporaryDirectory()`, eliminando colisão de corrida concorrente com `G_PORTAO_PROVA_QUE_MORDE`.
- **Validação:** `pytest gates/test_g_determinismo_lei_1.py` (3/3 passed).

### Ticket 2: Encaixes de Pipeline e CLI no Orquestrador
- **Status:** CONCLUÍDO
- **Entregável:** `docs/auditoria/mapa-pecas/ciclo-01/ENTREGA-TICKET-02.json`
- **Ações:**
  - Corrigidos comandos do `scripts/orquestrador_sincrono.py`: `bridge scan` usa argumento posicional e `factory curate` gera o plano `--plano` obrigatório com a saída correta.
  - Conectadas as etapas 6 e 7 do orquestrador a comandos reais (`ops plan` e `ecossistema.py audit`).
  - Corrigido `_validar_schema` para reprovar deterministamente quando jsonschema ou schema estiver ausente (`VER-001`).
  - Corrigido `_fechar_entrega` garantindo que `--dry-run` não grave nenhum arquivo em disco (`VER-004`).
  - Removidos flags do Click em `tools/aidd-ops/scripts/pipeline_ops.py` que mascaravam os subcomandos no catálogo.
- **Validação:** Encaixes quebrados no catálogo zerados (0); `pytest tests/test_orquestrador_sincrono.py` (5/5 passed).

### Ticket 3: Resiliência de Testes, Hooks e Manifestos Críticos
- **Status:** CONCLUÍDO
- **Entregável:** `docs/auditoria/mapa-pecas/ciclo-01/ENTREGA-TICKET-03.json`
- **Ações:**
  - Corrigidos os 6 testes quebrando em `tools/aidd-orca` (`VER-006`): `test_agent_spawner.py`, `test_flight_plan.py` e `test_orchestrator_engine.py` adaptados para perfis canônicos modernos. 117/117 passando!
  - Corrigidos 2 testes de reanálise em `tools/aidd-improvement` (`VER-007`) para o padrão `PLAN-NNNN`. 6/6 passando!
  - Gerado `handoff-melhoria.json` canônico assinado e validado por `G_HANDOFF_MELHORIA.py` (`VER-008`).
  - Removido `2>/dev/null` de `.githooks/pre-commit` para evitar supressão cega de erros (`VER-009`).
  - Atualizado default de injeção do `aidd-forge` para `.agents/skills` canônico (`VER-010`).
- **Validação:** Testes unitários das ferramentas 100% verdes; `python gates/G_HANDOFF_MELHORIA.py` exit 0.

### Ticket 4: Sincronização de Componentes e Fechamento de Ciclos
- **Status:** CONCLUÍDO
- **Entregável:** `docs/auditoria/mapa-pecas/ciclo-01/ENTREGA-TICKET-04.json`
- **Ações:**
  - Emitidos os laudos canônicos `LAUDO-15D-INICIAL.md` e `LAUDO-15D-REVISADO.md` do ciclo `skills-pocock/ciclo-01`.
  - Confirmado mapeamento de 17/17 comandos slash para skills existentes.
- **Validação:** `CAT-ciclo-skills-pocock-ciclo-01` saneado no catálogo.

### Ticket 5: Deduplicação de Artefatos e Limpeza de Legados
- **Status:** CONCLUÍDO
- **Entregável:** `docs/auditoria/mapa-pecas/ciclo-01/ENTREGA-TICKET-05.json`
- **Ações:**
  - Pasta legada `.gemini/skills` removida do repositório (`CAT-pasta-legada-gemini-skills`).
  - Corrigido `gates/G_SEGREDOS.py` para sanitizar `filters_used` mantendo caminho relativo em `.secrets.baseline` e evitando vazamento de caminhos absolutos locais (`VER-011`).
  - Catalogados falsos-positivos de hashes sha256 no `.secrets.baseline`.
- **Validação:** `python gates/G_SEGREDOS.py` aprovado com exit 0 no repositório real.

### Ticket 6: Quality Gate e Rótulo Honesto do Mapa de Peças
- **Status:** CONCLUÍDO
- **Entregável:** `gates/G_mapa_pecas.py` e `docs/auditoria/mapa-pecas/ciclo-01/ENTREGA-TICKET-06.json`
- **Ações:**
  - Implementado o portão determinístico `gates/G_mapa_pecas.py`.
  - Criada a suíte de testes `tests/test_g_mapa_pecas.py` provando que morde (Lei #13) com exit 1 quando catálogo corrompido, achado crítico aberto, mapa visual ausente ou vazio, ou encaixes quebrados.
- **Validação:** `pytest tests/test_g_mapa_pecas.py` (7/7 passed em 1.01s).

---

## 3. Conclusão da Fase 3 (Construtor)
Todos os critérios do DoD foram plenamente atingidos. O sistema está pronto para a emissão do laudo revisado na Fase 4.
