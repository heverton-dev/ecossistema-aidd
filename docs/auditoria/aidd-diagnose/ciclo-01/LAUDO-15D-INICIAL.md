# Laudo 15-D Inicial — `aidd-diagnose`

> Auditoria de 2026-09-23. Todo achado abaixo tem reprodução real (comando + exit code), não só leitura de código.
> Scripts de prova: `mcp_probe.py` / `mcp_call.py` (handshake MCP real) e sonda SQLite no `.code-review-graph/graph.db`.

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-diagnose`
- **Descrição Breve:** Protocolo de 5 fases para achar a causa de uma falha (reproduzir → raio de impacto no grafo → 1 hipótese → provar → corrigir + teste de regressão).
- **Comando de Gatilho:** `/aidd-diagnose` (só slash command; `python ecossistema.py diagnose` → exit 1, "comando desconhecido").

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** `componentes/compartilhado/skills/aidd-diagnose/SKILL.md` (fonte) + 7 cópias por harness, todas com o mesmo hash (`85f544a7`). Citada em `AGENTS.md:151`. Sem `scripts/`, sem testes: é uma skill só de instruções. OK.
- **D2. Input e Gatilhos:** Entrada implícita (falha, stacktrace, regressão). Nenhum formato de entrada definido. A ficha antiga (`historico_auditorias/micro-ferramentas-evolucao-2026-09-22.md:18`) promete o parâmetro `--fase <1-5>` — **FAILED: Not implemented** (não existe CLI nem script que aceite isso).
- **D3. Raio de Impacto e Isolamento:** A Fase 4 manda colocar "instrumentação temporária" direto no código e a Fase 5 manda removê-la antes do commit, sem worktree nem mecanismo de limpeza. **FAILED: Not implemented** (o isolamento depende só da disciplina do agente).
- **D4. Componentes e Fractalidade:** Recruta o MCP `code-review-graph` (declarado em `.mcp.json` e em `gates/dependencias_externas.json`; `dependencia verify` → exit 0). As 3 ferramentas citadas existem de fato: handshake real → `tools/list` com 30 ferramentas, incluindo `query_graph_tool`, `detect_changes_tool`, `get_impact_radius_tool`. O campo `depends: mcp:` do frontmatter não é lido por nenhum script/gate (é só decorativo).

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** Trocar tentativa-e-erro por método científico: uma hipótese por vez, cada uma provada ou descartada, terminando num teste de regressão permanente.
  - **[Estágio 1 — Reprodução] D6. O que o Estágio Faz:** Isola a falha num comando/teste mínimo determinístico.
  - **[Estágio 1] D7. O que o Estágio Recebe:** Sintoma da falha.
  - **[Estágio 1] D8. O que o Estágio Processa:** 100% LLM; nenhum motor verifica que a reprodução é determinística (ex.: rodar N vezes).
  - **[Estágio 1] D9. O que o Estágio Entrega:** Comando de reprodução (sem arquivo/formato definido).
  - **[Estágio 2 — Raio de impacto] D6. O que o Estágio Faz:** Consulta o grafo (callers/callees, mudanças, impacto).
  - **[Estágio 2] D7. O que o Estágio Recebe:** Arquivos/funções suspeitos.
  - **[Estágio 2] D8. O que o Estágio Processa:** MCP `code-review-graph`. **ACHADO GRAVE:** o grafo está desatualizado sem avisar — 158 de 1734 arquivos `.py` versionados não têm nenhum nó (ex.: `scripts/scaffold_auditoria.py`, `scripts/compilador_plano_evolucao.py`, `.agents/skills/aidd-melhoria/scripts/*.py`, todos adicionados em 2026-09-23). Prova real: `get_impact_radius_tool(changed_files=["scripts/scaffold_auditoria.py"])` → `status: ok`, "0 nodes impacted" — um falso "sem impacto". A skill não manda checar se o arquivo está no grafo nem cair para Grep.
  - **[Estágio 2] D9. O que o Estágio Entrega:** Lista de consumidores afetados (pode vir vazia de forma enganosa, ver acima).
  - **[Estágio 3 — Hipótese] D6/D7/D8/D9:** Formula UMA hipótese testável a partir do Estágio 2; puro LLM; entrega a frase-hipótese. Nenhum registro escrito exigido.
  - **[Estágio 4 — Prova] D6/D7/D8/D9:** Instrumentação/asserts temporários; recebe a hipótese; LLM + execução real; entrega "provada/descartada". Sem registro das hipóteses descartadas.
  - **[Estágio 5 — Correção] D6/D7/D8/D9:** Correção mínima + converter a reprodução em teste permanente; entrega fix + teste. Nada exige que o teste falhe **antes** do fix (a ficha antiga diz "Proibido... sem teste que falhe antes", mas o `SKILL.md` não diz).
- **D10. Orquestração e Topologia:** Linear 1→5 com laço 3↔4. Os dados passam só pela conversa; nenhum artefato em disco entre fases. **FAILED: Not implemented** (sem handoff persistido).

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** **FAILED: Not implemented.** Não há plano B se o MCP cair. Reproduzido nesta própria sessão: o harness reportou `code-review-graph (CONNECT_TIMEOUT) ... after 30000ms`, enquanto o servidor sozinho sobe em 11,3 s (sonda real). Com o MCP fora, a Fase 2 simplesmente não roda. Contraste: `componentes/compartilhado/comandos/melhoria.md` já tem "fallback universal para Grep/Glob/Read"; `debug-issue/SKILL.md` ao menos avisa "Se ausente, esta skill não funcional".
- **D12. Observabilidade e Frugalidade:** **FAILED: Not implemented.** Nenhum log, nenhum relatório de causa-raiz em arquivo, nada em `secoes/`.

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** Não existe `gates/G_aidd_diagnose.py`. A documentação (`matriz_exaustiva_66_skills_e_48_gates.md:21` e a ficha de 2026-09-22) liga a skill a `G_PORTAO_PROVA_QUE_MORDE`, mas esse gate é um meta-gate que verifica se cada `gates/G_*.py` tem teste de reprovação — não tem nada a ver com diagnóstico. **Rótulo desonesto na documentação.** O que existe e funciona: `G_HARNESS_COMPAT` pega cópia divergente da skill (teste de mutação: acrescentei 1 linha em `.claude/skills/aidd-diagnose/SKILL.md` → exit 1; restaurado → exit 0). `G_SKILL_ROT`, `G_UNIVERSAL_HARNESS`, `G_ECOSSISTEMA_INTEGRIDADE` → exit 0 (mas não pegam essa divergência).
- **D14. Critério de Rejeição (Rollback):** **FAILED: Not implemented.** Nada garante que a instrumentação temporária da Fase 4 foi removida, nem que o teste de regressão existe.
- **D15. Output Consolidado e Handoff:** **FAILED: Not implemented.** Nenhum relatório de causa-raiz, nenhum bastão para `aidd-tdd`/`aidd-handoff`.

## Achados colaterais (fora da skill, pegos durante a auditoria)
1. **CORRIGIDO no gerador:** `scripts/scaffold_auditoria.py` lia `papeis_pipeline_4f`/`padrao_geral`, mas `docs/auditoria/CONFIG-EXECUCAO-USUARIO.json` usa `pipeline_auditoria_4f`; o `MANIFESTO-4F.json` saía com `agy` nas 4 fases. Agora lê a chave canônica (formato antigo como fallback). Teste: `tests/test_scaffold_auditoria.py`.
2. **CORRIGIDO no gerador:** os prompts do scaffold apontavam para `docs/protocolos/TEMPLATE-AUDITORIA-FERRAMENTA.md` (inexistente); agora `docs/auditoria/TEMPLATE-AUDITORIA-FERRAMENTA.md`.
3. **CORRIGIDO no gerador:** a Fase 2 recebia o prompt genérico `docs/protocolos/auditoria/input_fase_2_arquiteto.txt` (com placeholder `<ferramenta>-v<N>`); o scaffold agora gera `PROMPT-FASE-2-ARQUITETO.txt` fechado, com os caminhos reais e o formato de ticket.
4. **CORRIGIDO no gerador:** `scripts/compilador_plano_evolucao.py` tinha um mapa fixo de handoffs do `aidd-melhoria` aplicado a qualquer ferramenta (o Ticket 1 do diagnose sairia com `.agents/skills/aidd-melhoria/scripts/isolamento.py`). Agora o handoff vem da linha `**Artefato de Handoff:**` do ticket; ticket sem ela reprova (exit 1). Teste: `tests/test_compilador_plano_evolucao.py` (inclui prova de que o JSON publicado do aidd-melhoria continua idêntico).
5. O `DOD.md` genérico exige `python ecossistema.py diagnose`, que não existe (coberto pelo Ticket 1 do `PLANO-EVOLUCAO.md`).
6. Sobreposição: `debug-issue` cobre o mesmo terreno (debug via grafo), sem referência cruzada entre as duas.

---

## 3. Matriz de Avaliação da Execução
- [ ] A ferramenta isolou seu raio de impacto corretamente? — **Não.** Instrumentação vai direto no código real, sem worktree nem limpeza verificada.
- [ ] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas? — **Parcial.** As 3 ferramentas MCP existem e respondem, mas o grafo desatualizado devolve "0 impacto" com `status: ok`, e a skill não manda desconfiar.
- [ ] O output final passou em todos os Quality Gates e emitiu o Handoff? — **Não.** Não há gate próprio nem handoff; o gate citado na documentação é o errado.

**Nota geral: 4/10.** Bom método no papel, zero mecanismo que garanta que ele foi seguido.
