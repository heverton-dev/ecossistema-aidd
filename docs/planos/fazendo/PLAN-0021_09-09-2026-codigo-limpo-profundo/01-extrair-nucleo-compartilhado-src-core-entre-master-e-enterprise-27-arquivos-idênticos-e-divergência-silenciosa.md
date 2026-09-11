# Item 1 — Extrair nucleo compartilhado src-core entre master e enterprise (27 arquivos idênticos e divergência silenciosa)

> **Escopo:** Unificar `tools/aidd-master/src/core/` e `tools/aidd-enterprise/src/core/` (27 arquivos hoje byte-idênticos, 8.781 linhas) numa fonte única, com sincronização mecânica determinística para os dois destinos. Resolver as 3 divergências silenciosas já em curso entre as "gêmeas" antes de sincronizar, para não apagar por acidente uma diferença que seja intencional. Não entra: `templates/` (Item 2) nem `scripts/gates`/`templates/gates` (Item 3) — mesmo tipo de duplicação, mas tratados em itens separados por volume e por serem áreas de risco distintas.
> **Status:** [CONCLUÍDO — 2026-09-09]

---

## Contexto ja investigado

Fonte: `docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html` (achados #1 e #8, medidos por hash MD5 e diff real, não estimados).

- Hash MD5 arquivo-a-arquivo (comando reproduzível na §1.3 do relatório) encontrou **27 arquivos byte-idênticos** entre `tools/aidd-master/src/core/` e `tools/aidd-enterprise/src/core/`, somando **8.781 linhas redundantes**. Maiores: `database.py` (4.086 linhas somadas entre as cópias), `openapi.py` (1.764), `jobs.py` (1.668), `security.py` (1.536).
- Único mecanismo de proteção hoje: `G_DRIFT_NUCLEO_COMPARTILHADO` — **detecta** divergência, não **previne** nem sincroniza automaticamente.
- Prova de custo real e recente: o Item 16 do plano `docs/planos/fazendo/01-correcao-pos-auditoria-sem-maquiagem/` (XSS armazenado em `get_studio_html`), concluído em 2026-09-09, precisou ser corrigido **manualmente em 6 cópias físicas** do mesmo arquivo (3 diretórios × 2 ferramentas) porque não existe fonte única nem sincronização automática.
- 3 divergências silenciosas já em curso entre master e enterprise, verificadas por diff real (não é apenas leitura cruzada):
  - `src/core/mcp_server.py`: `register_injected_tools()` (~40 linhas) existe só no master — o enterprise não carrega ferramentas MCP injetadas.
  - `src/core/intent_router.py`: reconhece os termos "hook"/"gancho" só no enterprise — o master não.
  - `src/core/materializador.py`: trata "hook" como script `hook.sh` (bash) no master e como JSON no enterprise — mesmo conceito, dois formatos incompatíveis.
- Padrão de referência já existente no próprio repositório para resolver esse tipo de problema: o mecanismo de sincronização de componentes (skills/MCPs) do `aidd-forge` — fonte única + sincronização mecânica para os destinos, em vez de edição manual em cada cópia (citado no relatório, §8.2, como modelo a seguir).

## Decisao Registrada (confirmada com o usuario em 2026-09-09)

- **Estrategia:** criar um "almoxarifado" compartilhado novo (pacote/diretorio fora de master e enterprise, consumido pelos dois) — nenhuma das duas ferramentas vira "fonte" as custas da outra.
- **Divergencia 1 (register_injected_tools):** migrada para o almoxarifado; as duas ferramentas passam a ter essa capacidade.
- **Divergencia 2 (reconhecimento de "hook"/"gancho" no intent_router):** migrada para o almoxarifado; as duas ferramentas passam a reconhecer.
- **Divergencia 3 (formato de hook no materializador — bash no master, JSON no enterprise):** unificar para **JSON** — mais seguro (nao executa shell arbitrario) e mais portavel entre ambientes (Windows incluso) que um script `hook.sh`.

## Definicao de Pronto

1. Existe uma decisão registrada (humana, não fabricada pela execução deste item) sobre qual será a fonte única dos 27 arquivos: master vira fonte com sync mecânico pro enterprise, ou os dois passam a consumir de um pacote/diretório compartilhado novo.
2. As 3 divergências documentadas acima são resolvidas por decisão explícita registrada neste arquivo antes da sincronização — unificar o comportamento OU documentar formalmente por que devem permanecer diferentes. Nunca apagadas silenciosamente pela sincronização.
3. Rodando novamente o script de hash MD5 (§1.3 do relatório) sobre os dois diretórios `src/core/`, o resultado mostra 0 arquivos com divergência não documentada.
4. `G_DRIFT_NUCLEO_COMPARTILHADO` (ou gate substituto) continua rodando nos Quality Gates e passa verde após a mudança.
5. Suíte de testes real (pytest, sem stub/mock de comportamento) de master e enterprise passa com exit 0 após a unificação.

## Criterio de saida

- Fonte única implementada, com sincronização mecânica documentada (comando determinístico — não copy-paste manual).
- As 3 divergências do achado #8 fechadas com decisão explícita registrada (unificação ou justificativa documentada).
- Testes reais passando nas duas ferramentas, gate de drift verde.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 1: extrair um nucleo compartilhado para os 27 arquivos hoje
byte-identicos entre tools/aidd-master/src/core/ e tools/aidd-enterprise/src/core/
(8.781 linhas redundantes, medidas por MD5 - ver docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html
achados #1 e #8 para evidencia completa).

Fatos que voce precisa saber antes de comecar:
- Arquivos maiores duplicados: database.py, openapi.py, jobs.py, security.py.
- Ja existe um gate G_DRIFT_NUCLEO_COMPARTILHADO que so detecta divergencia, nao sincroniza.
- 3 divergencias silenciosas ja existem entre as duas copias:
  1. src/core/mcp_server.py: register_injected_tools() so existe no master.
  2. src/core/intent_router.py: reconhece "hook"/"gancho" so no enterprise.
  3. src/core/materializador.py: trata hook como hook.sh (bash) no master, JSON no enterprise.
- O aidd-forge ja tem um mecanismo de sincronizacao mecanica de componentes (skills/MCPs)
  que pode servir de modelo de arquitetura para este item.

Regras obrigatorias:
1. A decisao arquitetural JA FOI TOMADA e esta registrada na secao "Decisao Registrada"
   acima - siga-a exatamente (almoxarifado compartilhado novo, as 3 divergencias resolvidas
   por uniao de capacidades, formato de hook unificado para JSON). Nao a questione nem
   invente uma alternativa.
2. Siga rigorosamente a Definicao de Pronto acima.
3. Nao invente aprovacoes. Nao marque este item como concluido sem reproducao real dos
   criterios de saida (rodar o hash MD5 de novo, rodar os testes reais, rodar o gate).
4. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 1: extract a shared core for the 27 files that are today
byte-identical between tools/aidd-master/src/core/ and tools/aidd-enterprise/src/core/
(8,781 redundant lines, measured by MD5 - see docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html
findings #1 and #8 for full evidence).

Facts you need before starting:
- Largest duplicated files: database.py, openapi.py, jobs.py, security.py.
- A gate named G_DRIFT_NUCLEO_COMPARTILHADO already exists but only detects drift, it does
  not sync.
- 3 silent divergences already exist between the two copies:
  1. src/core/mcp_server.py: register_injected_tools() exists only in master.
  2. src/core/intent_router.py: recognizes "hook"/"gancho" only in enterprise.
  3. src/core/materializador.py: treats hook as hook.sh (bash) in master, JSON in enterprise.
- aidd-forge already has a mechanical sync mechanism for components (skills/MCPs) that can
  serve as an architectural model for this item.

Mandatory rules:
1. The architectural decision has ALREADY BEEN MADE and is recorded in the "Decisao
   Registrada" section above - follow it exactly (new shared package, the 3 divergences
   resolved by merging capabilities into both tools, hook format unified to JSON). Do not
   question it or invent an alternative.
2. Strictly follow the Definition of Done above.
3. Do not fabricate approvals. Do not mark this item done without real reproduction of the
   exit criteria (re-run the MD5 hash, re-run the real tests, re-run the gate).
4. Maintain monorepo governance rules (AGENTS.md).
```
