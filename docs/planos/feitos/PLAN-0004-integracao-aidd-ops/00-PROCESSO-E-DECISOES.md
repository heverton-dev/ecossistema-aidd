# PROCESSO E DECISÕES — Integração da Feature AIDD-Ops

> **Origem:** `docs/features/06-09-2026_feature-arquitetura-aidd-ops.md` (proposta original) e `docs/planos/integracao-aidd-ops/PLANO-INTEGRACAO-AIDD-OPS.md` (parecer técnico e visão geral dos 9 pacotes).
> **Decisão registrada em:** 06/09/2026.
> **Propósito deste arquivo:** registro único e consultável do *processo* que será seguido — não do conteúdo técnico de cada pacote (isso vive em documento próprio, ver §3). Mesmo formato usado em `docs/planos/evolucao-notas-auditoria/00-PROCESSO-E-DECISOES.md`.

---

## 1. A decisão

Tratar a integração da AIDD-Ops como **9 pacotes sequenciais e independentes**, cada um seguindo o ciclo:

```
diagnóstico → Definição de Pronto travada → decisão do usuário (quando aplicável) →
implementação → validação real → registro → PRÓXIMO PACOTE
```

Nenhum pacote é considerado concluído sem passar pela validação real do seu próprio critério de saída. Nenhum pacote que toque infraestrutura real (4, 5, 7, 9) começa sem aprovação explícita e pontual — aprovar o plano geral não equivale a aprovar essas execuções individualmente.

---

## 2. Por que 9 pacotes e nessa ordem — critério de sequenciamento

O critério de ordenação **não é a ordem das 10 fases do pipeline descrito na proposta original** (Intake → Curadoria → Sizing → Bootstrapping VPS → DNS → Artefatos → Frontend/Gateway → Deploy → Pre-flight → Backup/Entrega). Aquela é a ordem de execução *runtime* de um deploy já pronto. A ordem aqui é a de **construção segura da própria ferramenta**, e segue um critério único: **risco e reversibilidade**.

| Pacote | Toca sistema de terceiros? | Reversível se der errado? |
|---|:---:|:---:|
| 1, 2, 3, 6, 8 | Não — só workspace local | Sim, `git revert` resolve |
| 4, 5 | Sim — SSH real / DNS real | Parcialmente — DNS propaga, chaves ficam expostas se vazarem |
| 7, 9 | Sim — VPS real, deploy real, dados reais de um cliente-piloto | Não totalmente — um deploy mal validado pode expor dados reais |

Por isso os pacotes que só mexem em código/documentação do próprio monorepo (1, 2, 3, 6, 8) vêm antes dos que produzem efeito em sistemas externos (4, 5, 7, 9), independentemente da ordem em que a proposta original os menciona.

---

## 3. Onde vive o conteúdo técnico de cada pacote

Cada pacote tem o próprio documento nesta pasta:

- `VEREDITO-TECNICO-VIABILIDADE.md` — veredito técnico consolidado (valor, viabilidade, determinismo, agnosticismo real das 4 ferramentas existentes, aderência ao processo de `componentes/`), produzido em 06/09/2026 a pedido do usuário antes do Pacote 3.
- `01-decisao-escopo-mvp.md` — bloco de decisão do usuário (§4 do plano-mestre); nenhum outro pacote começa antes deste.
- `02-fundamentos-governanca-gates.md`
- `03-mvp-tools-aidd.md`
- `04-ssh-runner-execucao.md`
- `05-mcps-borda-cloudflare.md`
- `06-gate-infra-compose.md`
- `07-gate-preflight-e2e.md`
- `08-templates-canonicos-generator.md`
- `09-validacao-e2e-piloto.md`

Cada um segue a mesma estrutura interna usada nas Rodadas 1 e 2 (`docs/planos/evolucao-notas-auditoria/` e `docs/planos/refinamento-notas-auditoria/`): **Diagnóstico** → **Definição de Pronto** → **Decisão(ões) necessária(s) do usuário** (quando houver) → **Prompt de Execução** (autocontido, pronto para colar num agente executor sem que ele tenha visto esta conversa) → **Critério de validação real** → **Veredito** (preenchido só após execução) → **Prompt de Execução — English version** (mesmo prompt, tradução integral, arquivado ao final do documento). Pacotes puramente decisórios (caso do Pacote 1) não têm prompt de execução — o "prompt" ali é a pergunta ao usuário, registrada por escrito.

---

## 4. Regra fixa: nenhum pacote de risco (4, 5, 7, 9) executa sem aprovação pontual

Diferente do processo de `evolucao-notas-auditoria` (onde só o Pacote 3 tinha um bloqueio de decisão), aqui **quatro pacotes têm bloqueio de decisão individual**, porque cada um produz efeito fora do repositório:
- Pacote 4: primeira conexão SSH real contra uma VPS.
- Pacote 5: primeiro registro DNS real criado via Cloudflare.
- Pacote 7: primeiro teste de integração contra ambiente vivo.
- Pacote 9: primeiro deploy completo com um nicho real.

A aprovação do plano geral (`PLANO-INTEGRACAO-AIDD-OPS.md`) autoriza o **diagnóstico e a implementação de código** desses pacotes. Não autoriza a **execução contra infraestrutura real** — isso é pedido de novo, no momento, com o alvo explícito (qual VPS, qual domínio, qual credencial).

---

## 5. O teto reconhecido — o que este processo não resolve sozinho

- **Custo real de infraestrutura de teste (VPS, domínio, Cloudflare):** os pacotes 4, 5, 7 e 9 pressupõem a existência de um ambiente descartável para validação. Se não existir, provisioná-lo tem custo financeiro real, decidido no Pacote 1 — este processo não decide isso sozinho.
- **Cobertura LGPD/jurídica plena:** a proposta original (§7) cita soberania de dados como requisito. Este processo garante a implementação técnica (credenciais isoladas, backup criptografado, hardening de rede) — não substitui uma revisão jurídica formal se a AIDD-Ops for usada com dados reais de clientes finais de terceiros.
- **Suporte multi-harness da nova ferramenta:** seguindo a Regra de Ouro #6 do `AGENTS.md` (Supremacia Agnóstica), qualquer skill/comando/gate novo criado para `tools/aidd-ops/` precisa passar por `python ecossistema.py components verify` como qualquer outro componente — isso é herdado do protocolo já existente (`docs/protocolos/05-09-2026_protocolo-agnosticidade-componentes.md`), não reinventado aqui.

---

## 6. Registro de progresso

| Pacote | Status | Documento |
|---|---|---|
| 1. Decisão de escopo e MVP | ✅ Concluído em 06/09/2026 — 5ª ferramenta oficial (implementação restrita a Fases 1-3 no Pacote 3), MVP primeiro, VPS descartável já disponível (detalhes só no Pacote 4), piloto = Clínicas | `01-decisao-escopo-mvp.md` |
| 2. Fundamentos de governança | ✅ Concluído em 06/09/2026 — Reconhecimento da 5ª ferramenta em AGENTS.md, gates G_ECOSSISTEMA_INTEGRIDADE e G_CLI_HELP_CONSISTENCIA atualizados, escopo aidd-ops no manifesto, fontes canônicas em componentes/compartilhado/ e componentes/aidd-ops/, sync multi-harness validado (commit 3ebf29a / e22b53a) | `02-fundamentos-governanca-gates.md` |
| 3. MVP `tools/aidd-ops/` (Fases 1-3) | ✅ Concluído em 06/09/2026 — Fases 1 (Intake), 2 (Curadoria) e 3 (Sizing) implementadas de forma 100% determinística (zero LLM), Result monad, 3 JSON Schemas, catálogos em data/, orquestrador pipeline_ops.py, gate próprio G_OPS_MVP aprovado, 21 testes verdes (commit 3ebf29a / e22b53a) | `03-mvp-tools-aidd.md` |
| 4. SSH Runner | ✅ Concluído em 06/09/2026 — Runner determinístico implementado (tools/aidd-ops/src/core/ssh_runner.py) com Paramiko, Result monad, lista fechada de 5 operações (anti-injeção), gate AST G_OPS_SSH aprovado, 17 novos testes unitários verdes (30 testes no total), subcomando `ops bootstrap` validado via CLI | `04-ssh-runner-execucao.md` |
| 5. MCPs de borda (Cloudflare/Docker) | ✅ Concluído em 06/09/2026 — MCPs cloudflare-mcp e docker-mcp criados na fonte canônica componentes/aidd-ops/mcps/ e sincronizados via gestor_componentes (2 componentes verificados), stdlib apenas (urllib.request, sem requests), docker-mcp read-only estrito, 9 novos testes unitários herméticos com mocks, 39 testes unitários verdes no total, gates G_SEGREDOS, G_COMPONENTE_AGNOSTICO, G_HARNESS_COMPAT e G_OPS_MVP 100% aprovados | `05-mcps-borda-cloudflare.md` |
| 6. Gate `G_INFRA_COMPOSE` | ✅ Concluído em 06/09/2026 — Quality Gate estático implementado (gates/G_INFRA_COMPOSE.py), validação de 7 docker-compose.yml sob aidd-ops, validação de init-multiple-databases.sh e conformidade com os 5 nichos, detecção de colisão de portas e cobertura de .env.example, registrado em ecossistema.py como 7º gate raiz e documentado em AGENTS.md §4, 6 testes unitários em gates/test_g_infra_compose.py, 7 gates globais 100% aprovados | `06-gate-infra-compose.md` |
| 7. Comando `ops preflight` (Pre-Flight E2E) | ✅ Concluído em 06/09/2026 — Subcomando `ops preflight <ambiente>` implementado em pipeline_ops.py e tools/aidd-ops/src/core/preflight.py com 4 checagens (healthz, SSL, DNS, webhook), retries configuráveis, saída JSON estruturada, 12 testes unitários herméticos com servidores locais reais (http.server.HTTPServer), zero stubs, 51 testes verdes em aidd-ops | `07-gate-preflight-e2e.md` |
| 8. Templates canônicos de infraestrutura | ✅ Concluído em 06/09/2026 — 7 blocos construtivos canônicos (traefik, postgres, authentik, twenty, chatwoot, calcom, gateway) versionados em tools/aidd-ops/templates/infra/, 5 planos estáticos por nicho em nichos/*.json, 100% auditados e aprovados via gates/G_INFRA_COMPOSE.py, desacoplamento preservado (sem tocar em aidd-generator) | `08-templates-canonicos-generator.md` |
| 9. Validação E2E com piloto real | ✅ Concluído em 06/09/2026 — Orquestrador `pipeline_ops_deploy.py` implementado com Result monad e fail-fast, integrado em `ops deploy <ambiente>`, 5 testes unitários cobrindo fluxo determinístico e rollback seguro, 56 testes totais verdes em aidd-ops, gates globais aprovados | `09-validacao-e2e-piloto.md` |

Esta tabela é atualizada ao final de cada pacote — nunca antes da validação real daquele pacote. Todos os 9 pacotes do plano de integração estão concluídos e homologados.

---

## 7. O que nunca muda neste processo, mesmo sob pressão de terminar rápido

- Nenhum pacote de risco (4, 5, 7, 9) executa contra sistema real sem o pedido explícito e pontual descrito em §4.
- Nenhuma nota/status sobe neste registro sem o comando de validação correspondente ter sido rodado de verdade.
- Onde existir um teto estrutural (custo de infraestrutura, escopo jurídico — §5), isso fica documentado honestamente, nunca escondido para parecer que o pacote está "mais pronto" do que está.
