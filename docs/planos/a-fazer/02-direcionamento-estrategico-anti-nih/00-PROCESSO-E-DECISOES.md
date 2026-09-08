# PROCESSO E DECISOES — direcionamento-estrategico-anti-nih

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

- **Origem:** conversa estratégica de 2026-09-07, depois da auditoria "sem maquiagem" e do levantamento NIH (`docs/features/oportunidades-reaproveitamento-oss-nih.md`), respondendo a 3 perguntas do usuário: (1) o trabalho já feito foi perdido? (2) qual era o direcionamento correto desde o início? (3) qual o plano profundo, sensato e coeso pra frente?
- **Objetivo Principal:** Registrar essas 3 respostas como decisão formal e sequenciar a execução — não é o plano tático de correção de bugs (esse já existe em `docs/planos/correcao-pos-auditoria-sem-maquiagem/`), é a camada estratégica **acima** dele: definir o norte do produto, trocar o motor de infraestrutura reinventada por OSS maduro sem perder a modelagem de domínio já construída, e só depois investir esforço no que é diferencial real.
- **Relação com o plano tático:** o plano tático (`correcao-pos-auditoria-sem-maquiagem/`) é a Fase 0 implícita desta iniciativa — corrige bugs e rótulos enganosos que existem HOJE. Esta iniciativa não duplica aqueles 14 itens; ela define o que vem depois.
- **Regra inegociável:** nenhuma migração de motor pode ser declarada concluída sem reprodução real (rodar a suíte de testes + subir o app gerado de novo) — "trocamos pra Cookiecutter" só é fato depois de reproduzido, não quando o código foi escrito.
- **Limites de Escopo:** Não inclui decisões não aprovadas por humano; não inclui reescrever nenhuma ferramenta do zero — é redirecionamento e substituição de peças, não relançamento do produto.

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | Inventario do que fica vs o que troca por ferramenta (o trabalho que continua de pe) | `01-inventario-do-que-fica-vs-o-que-troca-por-ferramenta-o-trabalho-que-continua-de-pe.md` |
| 2 | Registro do direcionamento correto e 2 novas Regras de Ouro (checklist anti-NIH, zero linguagem de marketing) | `02-registro-do-direcionamento-correto-e-2-novas-regras-de-ouro-checklist-anti-nih-zero-linguagem-de-marketing.md` |
| 3 | Fase 1 - Travar o norte: reescrever abertura do AGENTS.md com o north star de uma frase | `03-fase-1---travar-o-norte-reescrever-abertura-do-agentsmd-com-o-north-star-de-uma-frase.md` |
| 4 | Fase 2 - Troca de motor sequenciada por risco (seguranca, scaffolding, infra do ops) | `04-fase-2---troca-de-motor-sequenciada-por-risco-seguranca-scaffolding-infra-do-ops.md` |
| 5 | Fase 3 - Reauditoria sem maquiagem pos-troca de motor, prova antes e depois | `05-fase-3---reauditoria-sem-maquiagem-pos-troca-de-motor-prova-antes-e-depois.md` |
| 6 | Fase 4 - Investimento no diferencial real (pipeline do generator, protocolo delegado, materializador multi-harness) | `06-fase-4---investimento-no-diferencial-real-pipeline-do-generator-protocolo-delegado-materializador-multi-harness.md` |
| 7 | Bootstrap de dependências do produto gerado, por ferramenta (forge não é chamado por nenhuma das outras 4) | `07-bootstrap-de-dependencias-do-produto-gerado-por-ferramenta-forge-nao-eh-chamado-por-nenhuma-das-outras-4.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Documento |
|---|---|---|---|
| 1 | Inventario do que fica vs o que troca por ferramenta (o trabalho que continua de pe) | ⏳ Rascunho gerado, aguardando aprovacao | `01-inventario-do-que-fica-vs-o-que-troca-por-ferramenta-o-trabalho-que-continua-de-pe.md` |
| 2 | Registro do direcionamento correto e 2 novas Regras de Ouro (checklist anti-NIH, zero linguagem de marketing) | ✅ Concluído (2026-09-07) — AGENTS.md §2 com Regras #8/#9, gate `gates/G_HONESTIDADE_ROTULO.py` criado e reproduzido (5 testes reais em `gates/test_g_honestidade_rotulo.py` + execução direta contra o repo, que reprovou de verdade contra a violação já conhecida em `tools/aidd-master` e `tools/aidd-enterprise` `scripts/gates/`) | `02-registro-do-direcionamento-correto-e-2-novas-regras-de-ouro-checklist-anti-nih-zero-linguagem-de-marketing.md` |
| 3 | Fase 1 - Travar o norte: reescrever abertura do AGENTS.md com o north star de uma frase | ✅ Concluído (2026-09-07) — north star "Transformar uma ideia em software testado, e distribuir a mesma governança pra qualquer harness de IA" aprovado explicitamente pelo usuário via `orca orchestration ask`; AGENTS.md §1 e README.md (abertura) citam a frase; removida alegação solta não rastreável ("garantindo que a IA nunca alucine, nunca invente código pela metade e nunca quebre o projeto") | `03-fase-1---travar-o-norte-reescrever-abertura-do-agentsmd-com-o-north-star-de-uma-frase.md` |
| 4 | Fase 2 - Troca de motor sequenciada por risco (seguranca, scaffolding, infra do ops) | ✅ Ordem aprovada (2026-09-07) — 5 fases travadas, #11/#12 fora de escopo, decisao Coolify/CapRover/Dokku travada como 1º passo da Fase 3; execucao de cada sub-troca vira item futuro proprio quando chegar a vez | `04-fase-2---troca-de-motor-sequenciada-por-risco-seguranca-scaffolding-infra-do-ops.md` |
| 5 | Fase 3 - Reauditoria sem maquiagem pos-troca de motor, prova antes e depois | 🔄 Baseline "antes" gerado (2026-09-08), aguardando Fase 2 para comparativo | `05-fase-3---reauditoria-sem-maquiagem-pos-troca-de-motor-prova-antes-e-depois.md` |
| 6 | Fase 4 - Investimento no diferencial real (pipeline do generator, protocolo delegado, materializador multi-harness) | ✅ Definição concluída e priorizada (2026-09-07) — itens 6.1 a 6.6 estruturados com DpP, execução travada para pós-Fase 3 conforme aprovado via `orca orchestration ask` | `06-fase-4---investimento-no-diferencial-real-pipeline-do-generator-protocolo-delegado-materializador-multi-harness.md` |
| 7 | Bootstrap de dependências do produto gerado, por ferramenta (forge não é chamado por nenhuma das outras 4) | 🔄 Decisão (a) registrada + protótipo real feito em aidd-master (`compose_suite.py`), aguardando aprovação humana antes de generalizar às outras 3 ferramentas | `07-bootstrap-de-dependencias-do-produto-gerado-por-ferramenta-forge-nao-eh-chamado-por-nenhuma-das-outras-4.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
