# Plano de Evolução (Fase 2) - skills-pocock

Este plano readequa as skills derivadas de `mattpocock/skills` (upstream `c55ee46`, MIT) conforme `RELATORIO-TECNICO.md` e `DOD.md` deste ciclo.

**Status:** RASCUNHO — aprovar este plano não autoriza a execução; o disparo do Construtor exige instrução separada do usuário.

## Estratégia de Execução
- Todo ticket segue TDD estrito (Red → Green). O teste é escrito antes e precisa falhar (exit 1) na versão atual.
- Fonte canônica: `componentes/compartilhado/skills/<skill>/`. Nunca editar as cópias dos harnesses à mão; a distribuição é o Ticket 12.
- **Rótulo honesto:** os testes dos Tickets 1–8 e 10 são **testes de contrato do texto**. Eles provam que a regra está escrita na skill, não que o agente a segue. A prova de comportamento é o **Ticket 13**: cada skill alterada roda num caso real e um gate confere o artefato gerado. O ciclo só fecha com o Ticket 13 em exit 0.
- Tickets com decisão humana (7 e 11) só geram rascunho/relatório; o Construtor nunca decide pelo usuário.
- Conflito conhecido: `docs/auditoria/aidd-diagnose/ciclo-01` (parado após a Fase 2) edita a **Fase 2** do mesmo `componentes/compartilhado/skills/aidd-diagnose/SKILL.md` (checagem de grafo desatualizado e bloco "Fallback (MCP indisponível)"). Regra: o Ticket 1 **não reescreve o arquivo inteiro**; altera só as Fases 1, 3, 4 e 6 e preserva a Fase 2 byte a byte. Qualquer ciclo que rodar depois parte do arquivo já alterado. As regras são compatíveis: lista de 3 a 5 hipóteses, uma **ativa** por vez (gate daquele ciclo).

### Ticket 1: Diagnóstico com loop vermelho e hipóteses em ordem (Refere-se a D8 / DoD 1)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-diagnose/SKILL.md`
- **Requisito TDD (Red):** `tests/test_skills_pocock_diagnose.py` reprova (exit 1) enquanto o `SKILL.md` contiver "exactly ONE hypothesis" ou não contiver: comando vermelho já executado como pré-requisito, etapa de minimização, lista de 3 a 5 hipóteses em ordem, prefixo `[DEBUG-`, e "sem ponto correto de teste = achado".
- **Implementação Técnica:**
  - Reescrever a Fase 1 como "construir loop": um comando rodado ao menos uma vez, que fica vermelho neste bug, determinístico e rápido. Sem ele, parar e pedir acesso/artefato ao usuário.
  - Adicionar minimização (cortar um elemento por vez até sobrar só o essencial).
  - Trocar "exactly ONE hypothesis" por "3 a 5 hipóteses falsificáveis em ordem, mostradas ao usuário; testar uma por vez".
  - Logs temporários com `[DEBUG-xxxx]` e limpeza por grep.
  - Não tocar na Fase 2 (grafo + fallback sem MCP): o teste compara o bloco da Fase 2 antes/depois e reprova se mudar.
  - **Pré-requisito:** a branch `audit/evolucao-aidd-diagnose-ciclo-01` (8 tickets prontos, sem merge em `main`) precisa estar mergeada antes deste ticket. Se não estiver, o Ticket 1 para com exit 1 e avisa o usuário.
  - **Compatível com `gates/G_aidd_diagnose.py`** (vem daquela branch): o gate lê o bloco `HIPOTESES ATIVAS:` até o próximo `##`/`HIPOTESES DESCARTADAS` e reprova se houver mais de uma. Por isso a lista de 3 a 5 fica num cabeçalho próprio `## Hipóteses candidatas`, **antes** de `HIPOTESES ATIVAS:`, que continua com uma só.
  - Manter abaixo de 150 linhas.
- **Verificação (Green):** o teste passa (exit 0) e `python gates/G_HARNESS_COMPAT.py` continua com exit 0.
- **Construtor Prompt (EN):**
  - Write tests/test_skills_pocock_diagnose.py first. Assert fail while SKILL.md says "exactly ONE hypothesis".
  - Also assert presence: red-capable command already run, minimise step, 3-5 ranked hypotheses, [DEBUG- prefix, no-seam finding.
  - Run test. Assert exit 1.
  - Edit componentes/compartilhado/skills/aidd-diagnose/SKILL.md. Phase 1 builds feedback loop: one command, already run, goes red on this bug, deterministic, fast.
  - No loop: stop, ask user for access or redacted artifact.
  - Add minimise step. Replace single hypothesis with 3-5 falsifiable ranked hypotheses, shown to user, tested one at a time.
  - Tag temp logs [DEBUG-xxxx]. Keep file under 150 lines.
  - Precondition: branch audit/evolucao-aidd-diagnose-ciclo-01 merged into main. Else stop, exit 1, tell user.
  - Never rewrite whole file. Edit phases 1, 3, 4, 6 only. Keep phase 2 byte for byte.
  - Put ranked list under own heading "## Hipoteses candidatas" placed before "HIPOTESES ATIVAS:". Keep exactly one active hypothesis. Run python gates/G_aidd_diagnose.py on a sample report. Assert exit 0.
  - Test asserts phase 2 block unchanged versus git HEAD.
  - Run test. Assert exit 0. Run python gates/G_HARNESS_COMPAT.py. Assert exit 0.

### Ticket 2: Tickets em fatias verticais com bloqueios (Refere-se a D10 / DoD 2)
- **Falha 15-D:** `D10. Orquestração e Topologia`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-tickets/SKILL.md`
- **Requisito TDD (Red):** `tests/test_skills_pocock_tickets.py` reprova enquanto existir a ordem fixa "Ticket 1: Types/Contracts and Failing Tests / Ticket 2: Minimal Functional Implementation" ou faltar: campo "Blocked by", regra de fatia vertical, sequência expand-migrate-contract, "Target Files" e "Validation Command".
- **Implementação Técnica:**
  - Remover a ordem testes → código → refatoração entre tickets.
  - Regra: cada ticket entrega um comportamento completo, verificável sozinho, cabe numa janela de contexto nova; pré-refatoração primeiro.
  - Campo "Blocked by" por ticket; ticket sem bloqueio pode começar já.
  - Refatoração ampla: adicionar o novo → migrar em lotes → remover o velho.
  - Manter "Target Files" e "Validation Command" (nossos) e a apresentação ao usuário antes de publicar.
- **Verificação (Green):** teste passa; o formato continua legível pelo `aidd-master` (conferir consumidores com grep por `TICKET-`).
- **Construtor Prompt (EN):**
  - Write tests/test_skills_pocock_tickets.py first. Assert fail while fixed order tests-then-code-then-refactor exists.
  - Assert presence: Blocked by field, vertical slice rule, expand-migrate-contract, Target Files, Validation Command.
  - Run test. Assert exit 1.
  - Edit componentes/compartilhado/skills/aidd-tickets/SKILL.md. Each ticket delivers one complete verifiable behavior.
  - Add Blocked by per ticket. Prefactor first. Wide refactor: expand, migrate in batches, contract.
  - Keep Target Files and Validation Command fields. Keep user review before publish.
  - Grep consumers for TICKET- format. Confirm aidd-master still parses tickets.
  - Run test. Assert exit 0.

### Ticket 3: Entrevista em rodadas com resposta recomendada (Refere-se a D2 / DoD 3)
- **Falha 15-D:** `D2. Input e Gatilhos`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-grill/SKILL.md`
- **Requisito TDD (Red):** `tests/test_skills_pocock_grill.py` reprova enquanto `aidd-grill` disser "One Question at a Time" ou faltar: rodadas numeradas, resposta recomendada por pergunta, "fatos são do agente / decisões são do usuário", modo "Consolidated Assumptions". Também reprova se `aidd-grill-docs` não citar `CONTEXT.md`.
- **Implementação Técnica:**
  - Trocar "uma pergunta por vez" por rodadas: todas as perguntas cujos pré-requisitos já foram decididos, numeradas, cada uma com resposta recomendada.
  - Fatos o agente busca sozinho; decisões vão para o usuário. Terminar só quando não houver pergunta pendente e o usuário confirmar.
  - Manter o modo não-interativo (Consolidated Assumptions) — é melhor que o original para pipelines.
  - Em `aidd-grill-docs`: ler `CONTEXT.md` e `docs/adr/` quando existirem e atualizar o glossário quando um termo for decidido.
- **Verificação (Green):** teste passa nas duas skills.
- **Construtor Prompt (EN):**
  - Write tests/test_skills_pocock_grill.py first. Assert fail while aidd-grill says One Question at a Time.
  - Assert presence: numbered rounds, recommended answer per question, facts are agent job, decisions are user job, Consolidated Assumptions.
  - Assert aidd-grill-docs mentions CONTEXT.md and docs/adr/.
  - Run test. Assert exit 1.
  - Edit componentes/compartilhado/skills/aidd-grill/SKILL.md. Ask whole frontier per round. Number questions. Give recommended answer.
  - Agent looks up facts. User makes decisions. Done when frontier empty and user confirms.
  - Keep headless Consolidated Assumptions mode.
  - Edit componentes/compartilhado/skills/aidd-grill-docs/SKILL.md. Read CONTEXT.md and docs/adr/ if present. Update glossary when term resolved.
  - Run test. Assert exit 0.

### Ticket 4: TDD com pontos de teste combinados e sem testes de fachada (Refere-se a D8 / DoD 4)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-tdd/SKILL.md`
- **Requisito TDD (Red):** `tests/test_skills_pocock_tdd.py` reprova enquanto "Refactor" for o passo 3 do ciclo ou faltar: "seams" combinados antes, anti-padrões (tautológico, acoplado à implementação, fatiado em camadas), "um teste → uma implementação por vez", Zero Stubs e a lista de runners.
- **Implementação Técnica:**
  - Ciclo vira Red → Green; refatoração passa para a revisão.
  - Antes do primeiro teste: listar os pontos públicos a testar e confirmar com o usuário.
  - Seção de anti-padrões com a regra "o valor esperado vem de fonte independente".
  - Manter Zero Stubs e runners Python/Node/Go/Rust.
- **Verificação (Green):** teste passa.
- **Construtor Prompt (EN):**
  - Write tests/test_skills_pocock_tdd.py first. Assert fail while Refactor is step 3 inside the loop.
  - Assert presence: seams agreed before tests, tautological test ban, implementation-coupled ban, horizontal slicing ban, one test then one implementation.
  - Assert Zero Stubs and runner list still present.
  - Run test. Assert exit 1.
  - Edit componentes/compartilhado/skills/aidd-tdd/SKILL.md. Loop is red then green. Move refactor to review stage.
  - Add anti-patterns section. Expected values come from independent source.
  - Run test. Assert exit 0.

### Ticket 5: Guia de escrita para agentes (Refere-se a D1 / DoD 6)
- **Falha 15-D:** `D1. Contratos e Regras`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-escrita-agentes/SKILL.md`
- **Requisito TDD (Red):** `tests/test_skills_pocock_escrita.py` reprova enquanto a skill não existir, não tiver frontmatter válido (`name`, `description`) ou não cobrir: ponteiro de contexto, regra que não muda nada (no-op), sedimento, ordem negativa, fonte única, critério de pronto por passo. Reprova também acima de 150 linhas.
- **Implementação Técnica:**
  - Adaptar `writing-for-agents` (upstream) em inglês telegráfico, citando o original e a licença MIT.
  - Descrição com gatilho: criar/editar skill, AGENTS.md, CLAUDE.md.
- **Verificação (Green):** teste passa.
- **Construtor Prompt (EN):**
  - Write tests/test_skills_pocock_escrita.py first. Assert fail while skill file missing.
  - Assert frontmatter name and description. Assert sections: context pointer, no-op, sediment, negation, single source of truth, completion criterion.
  - Assert file under 150 lines.
  - Run test. Assert exit 1.
  - Create componentes/compartilhado/skills/aidd-escrita-agentes/SKILL.md. Adapt upstream writing-for-agents. Telegraphic English.
  - Credit mattpocock/skills, MIT license. Trigger: create or edit skill, AGENTS.md, CLAUDE.md.
  - Run test. Assert exit 0.

### Ticket 6: Retrospectiva que transforma erro em gate (Refere-se a D12 / DoD 5)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-retro/SKILL.md`
- **Requisito TDD (Red):** `tests/test_skills_pocock_retro.py` reprova enquanto a skill não existir ou faltar: leitura do log da sessão, as 7 categorias (navegação, checagem automática, padrão de código, AGENTS.md, custo de ferramenta, no-op, acesso a informação), classificação mecânico → `gates/` e julgamento → regra de revisão, saída em ordem de gravidade, ponteiro para `aidd-escrita-agentes` e encaminhamento para `aidd-melhoria`.
- **Implementação Técnica:**
  - Adaptar `retro` (upstream, "in-progress"). Log padrão: sessão atual; opcional por caminho.
  - Proibido aplicar mudanças: só propor. Aplicação passa por `aidd-melhoria` com aprovação do usuário.
- **Verificação (Green):** teste passa.
- **Construtor Prompt (EN):**
  - Write tests/test_skills_pocock_retro.py first. Assert fail while skill file missing.
  - Assert: session log read, seven categories, mechanical maps to gates/, judgement maps to review rule, severity order, pointer to aidd-escrita-agentes, handoff to aidd-melhoria.
  - Run test. Assert exit 1.
  - Create componentes/compartilhado/skills/aidd-retro/SKILL.md. Adapt upstream retro. Propose only, never apply.
  - Credit mattpocock/skills, MIT license.
  - Run test. Assert exit 0.

### Ticket 7: Glossário CONTEXT.md, formato ADR e /aidd-reexplica (Refere-se a D1 / DoD 7)
- **Falha 15-D:** `D1. Contratos e Regras`
- **Artefato de Handoff:** `CONTEXT.md`
- **Requisito TDD (Red):** `tests/test_skills_pocock_contexto.py` reprova enquanto não existirem `CONTEXT.md` (seções "Linguagem", "Relações", "Ambiguidades sinalizadas"), `docs/adr/README.md` com o formato e `componentes/compartilhado/skills/aidd-reexplica/SKILL.md` apontando para `CONTEXT.md`.
- **Implementação Técnica:**
  - Rascunhar termos a partir de `AGENTS.md`, `docs/auditoria/` e `docs/planos/`: ciclo, fase, plano, sessão, ticket, gate, harness, 4F, 15-D, worktree.
  - Onde o termo tem mais de um sentido, **não escolher**: listar em "Ambiguidades sinalizadas" para o usuário decidir (HITL).
  - Adicionar uma linha-ponteiro para `CONTEXT.md` em `AGENTS.md`. Antes de editar `AGENTS.md`, checar se outra sessão está escrevendo nele (`git status` / horário de modificação).
  - `aidd-reexplica`: reexplica a última mensagem em PT-BR simples usando o glossário.
- **Verificação (Green):** teste passa e as ambiguidades ficam abertas para o usuário.
- **Construtor Prompt (EN):**
  - Write tests/test_skills_pocock_contexto.py first. Assert fail while CONTEXT.md, docs/adr/README.md, aidd-reexplica skill missing.
  - Run test. Assert exit 1.
  - Draft CONTEXT.md from AGENTS.md, docs/auditoria/, docs/planos/. Terms: ciclo, fase, plano, sessao, ticket, gate, harness, 4F, 15-D, worktree.
  - Term with two meanings: never pick one. List it under flagged ambiguities for user decision.
  - Create docs/adr/README.md with ADR format.
  - Before editing AGENTS.md check git status for concurrent writes. Add one pointer line to CONTEXT.md.
  - Create componentes/compartilhado/skills/aidd-reexplica/SKILL.md. Re-pitch last message in plain Portuguese using CONTEXT.md terms.
  - Run test. Assert exit 0.

### Ticket 8: Modelo de entrega com evidência (Refere-se a D15 / DoD 8)
- **Falha 15-D:** `D15. Output Consolidado e Handoff`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-entrega/SKILL.md`
- **Requisito TDD (Red):** `tests/test_skills_pocock_entrega.py` reprova enquanto a skill não existir ou faltar: seções "Resumo", "Evidência (antes/depois)", "Dá para desfazer?", "O que pode quebrar"; exigência de exit code real (redirecionado a arquivo, nunca por pipe); uso em commit longo, PR e fechamento de ticket.
- **Implementação Técnica:**
  - Adaptar `pr` (upstream, crédito original a humanlayer/show-me). Sem PR no fluxo atual (commit direto na main), aplicar ao corpo de commit e ao `RELATORIO-CONSTRUTOR.md`.
  - Proibir marcar item `[x]` sem evidência no mesmo documento.
- **Verificação (Green):** teste passa.
- **Construtor Prompt (EN):**
  - Write tests/test_skills_pocock_entrega.py first. Assert fail while skill file missing.
  - Assert sections: summary, evidence before and after, reversible door, blast radius. Assert real exit code rule, no pipes.
  - Run test. Assert exit 1.
  - Create componentes/compartilhado/skills/aidd-entrega/SKILL.md. Adapt upstream pr skill. Credit humanlayer show-me and mattpocock/skills.
  - Apply to commit body, PR body, RELATORIO-CONSTRUTOR.md. Checked box requires evidence in same document.
  - Run test. Assert exit 0.

### Ticket 9: Wizard para passos que só o humano faz (Refere-se a D11 / DoD 9)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-wizard/template.sh`
- **Requisito TDD (Red):** `tests/test_skills_pocock_wizard.py` reprova enquanto o template não existir. Com ele: `bash -n` passa; chamar `write_env` duas vezes com a mesma chave num `.env` temporário deixa **uma** linha; `ask_secret` não ecoa o valor. Teste de comportamento real (roda o bash), pula só se `bash` não existir no PATH, com skip registrado em `gates/allowlist_skipped_testes.json`.
- **Implementação Técnica:**
  - Copiar `wizard/template.sh` e `SKILL.md` do upstream, crédito MIT.
  - Garantir funcionamento no Git Bash do Windows (abertura de URL via `start`/`cmd.exe`).
  - SKILL.md: usar só quando o agente não pode fazer o passo sozinho; nunca rodar o wizard ponta a ponta.
- **Verificação (Green):** teste passa rodando bash de verdade.
- **Construtor Prompt (EN):**
  - Write tests/test_skills_pocock_wizard.py first. Assert fail while template.sh missing.
  - Test runs real bash: bash -n passes, write_env twice same key leaves one line in temp .env, ask_secret does not echo.
  - Run test. Assert exit 1.
  - Create componentes/compartilhado/skills/aidd-wizard/template.sh and SKILL.md. Adapt upstream wizard. Credit MIT.
  - Support Git Bash on Windows for URL opening.
  - Run test. Assert exit 0.

### Ticket 10: Seções de escopo no modelo de planos (Refere-se a D5 / DoD 2)
- **Falha 15-D:** `D5. Visão e Escopo`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-planos/SKILL.md`
- **Requisito TDD (Red):** `tests/test_skills_pocock_planos.py` reprova enquanto o modelo de plano gerado não tiver as seções "Ainda não especificado" e "Fora de escopo" com a regra: fora de escopo nunca volta para o plano atual.
- **Implementação Técnica:**
  - Localizar onde o `aidd-planos` monta o modelo (SKILL.md ou script chamado por ele) e acrescentar as duas seções.
  - Se o modelo vier de script, o teste roda o script e confere a saída (não o texto da skill).
- **Verificação (Green):** teste passa.
- **Construtor Prompt (EN):**
  - Locate where aidd-planos builds plan template. SKILL.md or script.
  - Write tests/test_skills_pocock_planos.py first. Assert fail while template lacks not-yet-specified section and out-of-scope section. Headings stay Portuguese as in plan text.
  - If template comes from script, test runs script and checks output.
  - Run test. Assert exit 1.
  - Add both sections. Rule: out of scope never returns to current plan.
  - Run test. Assert exit 0.

### Ticket 11: Relatório de skills globais duplicadas (Refere-se a D3 / DoD 10)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `scripts/relatorio_skills_duplicadas.py`
- **Requisito TDD (Red):** `tests/test_relatorio_skills_duplicadas.py` monta duas pastas temporárias (global e projeto) com skills de mesmo tema (`grilling` × `aidd-grill`) e reprova enquanto o script não listar o par. O script é **somente leitura**: o teste reprova se qualquer arquivo das pastas temporárias mudar.
- **Implementação Técnica:**
  - Mapa fixo de pares upstream × AIDD (grilling/grill-me/grill-with-docs × aidd-grill/aidd-grill-docs, tdd × aidd-tdd, diagnosing-bugs × aidd-diagnose, to-spec × aidd-spec, to-tickets × aidd-tickets, handoff × aidd-handoff, code-review × review-changes).
  - Saída: tabela em Markdown com caminho global, par AIDD e sugestão "remover/manter". Remoção é feita pelo usuário.
- **Verificação (Green):** teste passa; rodar contra `~/.agents/skills` real e anexar a saída ao `RELATORIO-CONSTRUTOR.md`.
- **Construtor Prompt (EN):**
  - Write tests/test_relatorio_skills_duplicadas.py first. Build temp global dir and temp project dir with overlapping skills.
  - Assert script lists pair grilling and aidd-grill. Assert no file changed in temp dirs.
  - Run test. Assert exit 1.
  - Create scripts/relatorio_skills_duplicadas.py. Read only. Fixed map upstream to AIDD pairs. Output markdown table.
  - Never delete. User removes global copies by hand.
  - Run test. Assert exit 0. Run against real global skills dir. Attach output to RELATORIO-CONSTRUTOR.md.

### Ticket 12: Distribuição multi-harness e gate final (Refere-se a D15 / DoD 10 / DoD 12)
- **Falha 15-D:** `D15. Output Consolidado e Handoff`
- **Artefato de Handoff:** `docs/auditoria/skills-pocock/ciclo-01/RELATORIO-CONSTRUTOR.md`
- **Requisito TDD (Red):** antes do sync, `python ecossistema.py components verify` reprova (exit 1) por divergência entre `componentes/compartilhado/skills/` e os harnesses.
- **Implementação Técnica:**
  - `python ecossistema.py components sync`; registrar skills novas onde o `gestor_componentes.py` exigir.
  - Atualizar a cópia do forge em `tools/aidd-forge/aidd_forge/templates/skills/` para as skills alteradas.
  - Atualizar a lista de skills em `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`.
  - `python ecossistema.py audit` com exit code real capturado em arquivo.
- **Verificação (Green):** `components verify` e `audit` com exit 0; `RELATORIO-CONSTRUTOR.md` com uma linha por ticket (arquivo entregue, comando de teste, exit antes, exit depois).
- **Construtor Prompt (EN):**
  - Run python ecossistema.py components verify. Redirect to file. Read real exit code. Assert exit 1 before sync.
  - Run python ecossistema.py components sync. Register new skills where gestor_componentes.py requires.
  - Update forge copies in tools/aidd-forge/aidd_forge/templates/skills/ for changed skills.
  - Update skill list in docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md.
  - Run components verify again. Assert exit 0. Run python ecossistema.py audit. Assert exit 0.
  - Write RELATORIO-CONSTRUTOR.md: one row per ticket with file, test command, exit before, exit after.

### Ticket 13: Prova de uso real das skills alteradas (Refere-se a D13 / DoD 11)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/G_PROVA_SKILLS_POCOCK.py`
- **Requisito TDD (Red):** `tests/test_g_prova_skills_pocock.py` usa artefatos salvos em `tests/fixtures/skills_pocock/` (um bom e um ruim por skill) e reprova enquanto o gate não existir. Com o gate: artefato ruim → exit 1, artefato bom → exit 0. Isso prova que o gate morde; o teste não chama modelo nenhum.
- **Implementação Técnica:**
  - Casos reais em `tests/fixtures/skills_pocock/`: (a) mini-projeto Python com um bug plantado; (b) uma spec curta de 3 comportamentos.
  - O gate roda cada skill em modo não-interativo (`claude -p --model haiku`) contra o caso e confere o artefato gerado:
    - `aidd-diagnose`: 3 ou mais hipóteses numeradas **e** um comando de reprodução que, executado de verdade no mini-projeto, sai com exit diferente de 0 antes do fix.
    - `aidd-tickets`: todo ticket tem "Blocked by" e nenhum ticket é só de testes ou só de código.
    - `aidd-grill` (modo não-interativo): bloco "Consolidated Assumptions" com recomendação por item.
    - `aidd-tdd`: seção de pontos de teste antes do primeiro teste.
  - Gate sob demanda (gasta tokens e depende de rede): fica **fora** do pre-commit, junto dos outros gates globais manuais, e é documentado assim.
- **Verificação (Green):** o teste do gate passa. O Construtor roda o gate de verdade uma vez e anexa a saída + exit code real ao `RELATORIO-CONSTRUTOR.md`. Sem essa execução, o ciclo não fecha.
- **Construtor Prompt (EN):**
  - Create tests/fixtures/skills_pocock/ with one good and one bad saved artifact per skill.
  - Add mini Python project with planted bug. Add short spec with three behaviors.
  - Write tests/test_g_prova_skills_pocock.py first. Bad artifact must give exit 1. Good artifact must give exit 0. No model call inside test.
  - Run test. Assert exit 1 while gate missing.
  - Create gates/G_PROVA_SKILLS_POCOCK.py. Run each changed skill headless with claude -p --model haiku against fixtures.
  - Check aidd-diagnose: 3 or more numbered hypotheses. Run repro command on planted bug project. Assert nonzero exit before fix.
  - Check aidd-tickets: every ticket has Blocked by. No ticket holds only tests or only code.
  - Check aidd-grill headless: Consolidated Assumptions block with recommendation per item.
  - Check aidd-tdd: seams section before first test.
  - Keep gate out of pre-commit. Document it as manual on-demand gate.
  - Run test. Assert exit 0. Run gate once for real. Redirect output to file. Read real exit code.
  - Attach gate output and exit code to RELATORIO-CONSTRUTOR.md.
  - Run python ecossistema.py audit again. Assert exit 0. This is final gate of cycle.
