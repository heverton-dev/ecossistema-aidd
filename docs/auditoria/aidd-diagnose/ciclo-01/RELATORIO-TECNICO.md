# Relatório Técnico de Engenharia — Pipeline 4F (aidd-diagnose)

## 1. Metadados do Pipeline
- **Pipeline ID:** `auditoria-aidd-diagnose` (auditoria) / `evolucao-aidd-diagnose` (evolução)
- **Ferramenta Alvo:** `aidd-diagnose` (fonte: `componentes/compartilhado/skills/aidd-diagnose/SKILL.md`; 8 cópias por harness, hash `85f544a7`)
- **Harnesses (de `CONFIG-EXECUCAO-USUARIO.json`):** claude (inspetor), agy (arquiteto), mimo (construtor), opencode (retorno); rodízio de evolução claude → agy → mimo → opencode
- **Execução real das Fases 1-2 desta rodada:** Claude Code (Opus 5.5), em sessão interativa
- **Branch Alvo:** `main`

## 2. Evidências Reproduzidas (Fase 1)
- `python ecossistema.py dependencia verify` → EXIT 0 (39 dependências)
- Handshake MCP real em `code-review-graph serve`: `initialize` em 11,3 s; `tools/list` = 30 ferramentas, incluindo `query_graph_tool`, `detect_changes_tool`, `get_impact_radius_tool`
- Sonda SQLite em `.code-review-graph/graph.db`: 158 de 1734 `.py` versionados (>200 B) sem nó; `get_impact_radius_tool(["scripts/scaffold_auditoria.py"])` → `status: ok`, 0 impactados (falso negativo)
- Mutação em `.claude/skills/aidd-diagnose/SKILL.md` → `G_HARNESS_COMPAT` EXIT 1; restaurado → EXIT 0. `G_UNIVERSAL_HARNESS`, `G_ECOSSISTEMA_INTEGRIDADE`, `G_DRIFT_ANALYZER` e `G_DRIFT_NUCLEO_COMPARTILHADO` não pegam essa divergência (EXIT 0)
- `python ecossistema.py diagnose --help` → EXIT 1 ("comando desconhecido")

## 3. Correções Estruturais no Gerador (feitas nesta rodada)
- `scripts/scaffold_auditoria.py`: lê só `pipeline_auditoria_4f`; papel ou campo ausente → `ValueError`/EXIT 1, sem valor padrão inventado; `MANIFESTO-4F.json` regerado a cada execução; gera `PROMPT-FASE-2-ARQUITETO.txt` e `PROMPT-FASE-3-CONSTRUTOR.txt` fechados e em inglês; template em `docs/auditoria/TEMPLATE-AUDITORIA-FERRAMENTA.md`; nunca escreve no config.
- `scripts/compilador_plano_evolucao.py`: harness/model/comando só de `pipeline_evolucao_rotativo`, sem padrão inventado; handoff vem de `**Artefato de Handoff:**` (o mapa fixo do aidd-melhoria foi removido); prompt do ticket vem de `**Construtor Prompt (EN):**`, e não-ASCII ou palavra PT reprovam; valida antes de escrever, então falha não deixa arquivo parcial.
- `ecossistema.py evolucao`: erro de compilação vira EXIT 1 limpo.
- Testes: `tests/test_scaffold_auditoria.py` (8) + `tests/test_compilador_plano_evolucao.py` (10) → 18 passed. RED provado antes (12 falhas com o código anterior).

## 4. Estrutura Canônica de Arquivos da Auditoria (`docs/auditoria/aidd-diagnose/ciclo-01/`)
- `DOD.md`: Definition of Done.
- `MANIFESTO-4F.json`: manifesto das 4 fases, derivado do config.
- `PROMPT-FASE-1-INSPETOR.txt`, `PROMPT-FASE-2-ARQUITETO.txt`, `PROMPT-FASE-3-CONSTRUTOR.txt`, `PROMPT-FASE-4-RETORNO.txt`: prompts fechados de cada fase.
- `../G_auditoria_15D.py` (raiz da ferramenta, compartilhado entre ciclos): gate das 15 dimensões; sem argumento valida o ciclo vigente.
- `LAUDO-15D-INICIAL.md`: laudo da Fase 1 (nota 4/10).
- `PLANO-EVOLUCAO.md` / `PLANO-EVOLUCAO.json`: 8 tickets (D2, D3, D8, D11, D12, D13, D14, D15).
- `prompts_tickets/PROMPT-TICKET-01..08.txt`: prompts do Construtor em inglês telegráfico imperativo.
- `RESUMO-USUARIO.md` / `RELATORIO-TECNICO.md`: este par de fechamento parcial.

## 5. Quality Gates e Atestado Binário
- `python docs/auditoria/aidd-diagnose/G_auditoria_15D.py docs/auditoria/aidd-diagnose/ciclo-01/LAUDO-15D-INICIAL.md` → **EXIT 0**
- `python scripts/compilador_plano_evolucao.py --plano docs/auditoria/aidd-diagnose/ciclo-01/PLANO-EVOLUCAO.md` → **EXIT 0** (8 fases, 8/8 iguais ao config, 8/8 prompts ASCII)
- `pytest tests/test_scaffold_auditoria.py tests/test_compilador_plano_evolucao.py` → **18 passed**

## 6. Pendências Conhecidas
- Nenhuma no gerador. O `docs/auditoria/aidd-melhoria/ciclo-01/PLANO-EVOLUCAO.md` ganhou os 8 blocos `**Construtor Prompt (EN):**` e foi recompilado (EXIT 0). Os prompts dele agora estão em inglês, os handoffs e nomes das fases ficaram iguais, e harness/model/comando_terminal seguem o rodízio do config.

## 7. Migração para Ciclos (2026-09-24)
- Os artefatos desta rodada foram movidos da raiz para `ciclo-01/`, e os caminhos internos foram reescritos. A Fase 3 agora entrega `ciclo-01/RELATORIO-CONSTRUTOR.md`, e não mais um diretório de código, para que o cache do orquestrador valha por ciclo.
- Uma nova rodada (`python scripts/scaffold_auditoria.py aidd-diagnose`) retoma este ciclo enquanto não existir `LAUDO-15D-REVISADO.md`. Depois disso, abre `ciclo-02/`.
