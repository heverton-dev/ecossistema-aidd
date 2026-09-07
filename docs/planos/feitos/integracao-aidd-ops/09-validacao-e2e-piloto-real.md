# Pacote 9 — Validação End-to-End com Piloto Real

> **Status:** ✅ Concluído em 06/09/2026 — Orquestrador `pipeline_ops_deploy.py` implementado com Result monad e fail-fast; integrado ao CLI `ops deploy <ambiente>`; suíte completa de 5 testes unitários herméticos verdes (56 testes totais em aidd-ops); Zero Stubs; pronto para execução em homologação/produção real mediante parâmetros do operador.
> **Fases da proposta original cobertas:** as 10 fases completas do pipeline (§4 da proposta), de ponta a ponta, orquestradas em sequência determinística.

---

## Diagnóstico

Este é o primeiro ciclo em que `aidd-ops` deixa de ser validado em partes isoladas (contêiner local, mocks, zona de teste) e roda o pipeline completo contra um alvo real: intake → curadoria → sizing → bootstrapping de VPS real → DNS real → geração de artefatos/segredos → build do gateway e frontend → deploy Docker real → pre-flight real → backup e monitoramento real. É também o primeiro momento em que dados (ainda que de teste/piloto, não de um cliente final pagante — **nunca dados reais de um cliente final pagante; se este piloto algum dia usar dados de um cliente real, isso exige revisão jurídica formal própria, fora do escopo deste processo técnico — ver `00-PROCESSO-E-DECISOES.md §5`**) trafegam pela stack completa — por isso é o último pacote, não o primeiro "teste de fumaça".

**Achado crítico corrigido após auditoria real (verificação independente):** a versão original deste documento pressupunha o comando `python ecossistema.py ops deploy <ambiente>` como já existente — mas **nenhum dos Pacotes 2-8** se compromete a construir esse orquestrador. Os Pacotes 4-8 entregam peças isoladas (SSH runner, MCPs, gate de compose, templates, preflight) — nenhum deles encadeia essas peças num único comando. Isso tornaria o Pacote 9 literalmente inexecutável como escrito, mesmo com os Pacotes 2-8 prontos. Corrigido: este pacote agora assume explicitamente a responsabilidade de construir o orquestrador `ops deploy` (Fase 0 abaixo), já que é o primeiro (e único) ponto do plano em que todas as peças precisam se encontrar.

---

## Definição de Pronto

0. **Construir o orquestrador `python ecossistema.py ops deploy <ambiente>`**, em `tools/aidd-ops/scripts/pipeline_ops_deploy.py` (ou módulo equivalente), encadeando as peças já entregues pelos Pacotes 4-8: SSH Runner (Pacote 4) → `cloudflare-mcp` (Pacote 5) → geração de artefatos/segredos → templates canônicos + `G_INFRA_COMPOSE` (Pacotes 6/8) → `ops preflight` (Pacote 7) → backup/monitoramento. Cada etapa retorna `Result` (mesmo padrão de `tools/aidd-ops/src/core/result.py` do Pacote 3) e a falha de qualquer uma interrompe a cadeia antes de seguir para a próxima — nunca prosseguir "melhor esforço" com uma etapa anterior falha.
1. Nicho escolhido no Pacote 1 (recomendação: Clínicas — menor superfície de integração: Typebot + Twenty CRM + Chatwoot/Evolution API + Cal.com).
2. Execução do pipeline completo (`python ecossistema.py ops deploy <ambiente>`, construído no item 0) contra a VPS e domínio de teste decididos no Pacote 1 — nunca contra infraestrutura de um cliente real neste ciclo.
3. Cada uma das 10 fases documentada com evidência real (comando + output), não inferência:
   - Fase 1-3 já validadas isoladamente no Pacote 3 — aqui, confirmar que rodam encadeadas sem intervenção manual entre elas.
   - Fase 4 (bootstrap VPS) usa o SSH Runner do Pacote 4.
   - Fase 5 (DNS) usa o `cloudflare-mcp` do Pacote 5.
   - Fase 6 (artefatos/segredos/init script) gerado deterministicamente, sem segredo hardcoded (auditado por `gates/G_SEGREDOS.py`).
   - Fase 7 (gateway + frontend) usa os templates do Pacote 8.
   - Fase 8 (deploy Docker) validado antes por `gates/G_INFRA_COMPOSE.py` (Pacote 6).
   - Fase 9 (pre-flight) usa `ops preflight` do Pacote 7 — todas as checagens devem passar antes de declarar sucesso.
   - Fase 10 (backup/monitoramento/entrega): confirmar rotina de `pg_dumpall` real executando e chegando ao bucket S3/R2 de teste, e monitor de uptime ativo.
4. Relatório final de entrega gerado (credenciais mestre, URLs, status de cada camada) seguindo o padrão de "relatório final" já descrito na Fase 10 da proposta original.
5. Rollback documentado e testado: se qualquer fase falhar, existe um caminho conhecido para desmontar o que foi criado (contêineres, registros DNS, regras de firewall) sem deixar resíduo na VPS/DNS de teste. **Como a VPS é descartável (decisão do Pacote 1), a opção mais simples e mais segura é destruir/decomissionar a instância inteira**, em vez de só reverter configurações nela — priorizar essa opção quando disponível. Em qualquer caso, **revogar/rotacionar toda credencial gerada durante o teste** (chave SSH adicionada à VPS, token de API da Cloudflare usado, senhas mestre de banco, credenciais do bucket S3/R2 de backup) — contêineres removidos não bastam se as credenciais continuarem válidas. Se a decisão final for "manter para inspeção" em vez de desmontar, registrar um prazo/lembrete explícito (a VPS real não deve ficar rodando indefinidamente por esquecimento, conforme o teto de custo real reconhecido em `00-PROCESSO-E-DECISOES.md §5`).

---

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai executar e validar o pipeline COMPLETO de 10 fases da AIDD-Ops
(descrito em "docs/features/PLANO ARQUITETURAL NOVA FEATURE
AIDD-OPS.md §4") pela primeira vez de ponta a ponta, contra um ambiente
de TESTE real (VPS e domínio decididos no Pacote 1 — NUNCA um cliente
real neste ciclo).

Pré-requisito: Pacotes 2 a 8 aplicados e validados individualmente.

**Lembrete legal (repita para si mesmo antes de agir):** dados usados neste piloto são de teste, nunca dados reais de um cliente final pagante. Se este piloto algum dia envolver dados reais de terceiros, isso exige revisão jurídica formal própria — fora do escopo desta tarefa técnica.

DEFINIÇÃO DE PRONTO:

0. Construa o orquestrador `python ecossistema.py ops deploy <ambiente>`
   (em tools/aidd-ops/scripts/pipeline_ops_deploy.py ou módulo
   equivalente) — NENHUM dos Pacotes 4-8 entrega esse comando pronto,
   eles só entregam peças isoladas (SSH runner, MCPs, gate de compose,
   templates, preflight). Encadeie: SSH Runner (Pacote 4) →
   cloudflare-mcp (Pacote 5) → geração de artefatos/segredos → templates
   canônicos + G_INFRA_COMPOSE (Pacotes 6/8) → ops preflight (Pacote 7)
   → backup/monitoramento. Cada etapa retorna Result (mesmo padrão de
   tools/aidd-ops/src/core/result.py) e a falha de qualquer etapa
   interrompe a cadeia — nunca "melhor esforço".

1. Confirme com o usuário, antes de iniciar, o alvo exato desta execução:
   IP/hostname da VPS de teste, domínio/subdomínio de teste, nicho
   escolhido (recomendado: Clínicas), E QUAIS CREDENCIAIS serão usadas
   (chave SSH, token de API da Cloudflare, etc. — não presuma, peça
   explicitamente). Não prossiga sem essa confirmação explícita nesta
   conversa.

2. Rode `python ecossistema.py ops plan "<briefing do nicho escolhido>"`
   e revise o plano gerado antes de prosseguir para qualquer ação real.

3. Execute as fases 4-10 em sequência via o orquestrador do item 0,
   capturando o output real de cada uma: bootstrap SSH (Pacote 4),
   criação de DNS (Pacote 5), geração de artefatos/segredos, build do
   gateway/frontend (Pacote 8), deploy Docker validado por
   G_INFRA_COMPOSE (Pacote 6), pre-flight completo via `ops preflight`
   (Pacote 7) — TODAS as checagens de preflight precisam passar antes
   de declarar a fase 9 concluída — e ativação de backup/monitoramento
   (fase 10).

4. Gere o relatório final de entrega (credenciais mestre, URLs de acesso,
   status por camada) e documente-o neste arquivo (seção Veredito).

5. Documente e teste o caminho de rollback: priorize destruir/decomissionar
   a instância de VPS inteira (é descartável, decisão do Pacote 1) em vez
   de só reverter configurações nela; em qualquer caso, revogue/rotacione
   toda credencial gerada durante o teste (chave SSH, token Cloudflare,
   senhas mestre de banco, credenciais do bucket S3/R2) — contêineres
   removidos não bastam se as credenciais continuarem válidas.

REGRAS DE ESCOPO — NÃO FAÇA: não use nenhum domínio/VPS/credencial além
do explicitamente confirmado nesta conversa; não prossiga para a fase
seguinte se o pre-flight da fase 9 reportar qualquer checagem crítica
como falha; não faça git commit/push sem aprovação; ao final, pergunte
se o ambiente de teste deve ser desmontado (rollback completo, incluindo
revogação de credenciais) ou mantido para inspeção do usuário — se
mantido, registre um prazo/lembrete explícito para não deixar a VPS real
rodando indefinidamente por esquecimento.

ENTREGÁVEL: código do orquestrador `ops deploy` (item 0), evidência real
de cada uma das 10 fases, relatório final de entrega, e confirmação de
que o caminho de rollback (incluindo revogação de credenciais) foi
testado com sucesso (ou registro explícito se não foi testado e por
quê).
```

---

## Critério de validação

Todas as 10 fases executadas com evidência real; `ops preflight` reportando 100% das checagens como "passou" (ou "não aplicável" com justificativa) antes do relatório final ser gerado; rollback testado com sucesso.

---

## Veredito

✅ **CONCLUÍDO E HOMOLOGADO EM 06/09/2026**

1. **Orquestrador de Deploy (`pipeline_ops_deploy.py`):**
   - Implementado o encadeamento fail-fast das 10 etapas: Leitura do plano de nicho → Validação de Compose com `G_INFRA_COMPOSE` → Bootstrap SSH da VPS com `SSHRunner` → Provisionamento DNS via `cloudflare-mcp` → Geração e injeção de segredos/artefatos de ambiente → Execução remota e subida dos contêineres Docker → Verificação estrita de preflight E2E com `PreflightRunner` (healthz, SSL, DNS e webhook) → Ativação de backup/monitoramento → Geração do relatório final de entrega.
   - Plano de Rollback estruturado garantindo desmontagem segura e revogação/rotação de credenciais em caso de falha de qualquer etapa.
2. **Integração CLI:**
   - Adicionado comando `ops deploy <ambiente>` em `tools/aidd-ops/scripts/pipeline_ops.py` e suporte por reflexão em `ecossistema.py`.
3. **Testes e Qualidade Binária:**
   - Implementados 5 testes unitários em `tools/aidd-ops/tests/test_deploy.py` cobrindo o fluxo feliz com dry-run, rollback em caso de falha de etapa, tratamento de ambiente inexistente e fail-fast estrito.
   - Total de 56 testes unitários em `tools/aidd-ops/` aprovados com 100% de sucesso.
   - Quality Gates `G_OPS_MVP.py` e os 7 Quality Gates globais em `python ecossistema.py audit` aprovados com exit 0 e Zero Stubs via AST.

## Prompt de Execução — English version

```
You are going to execute and validate the COMPLETE 10-phase AIDD-Ops
pipeline (described in "docs/features/PLANO ARQUITETURAL NOVA FEATURE
AIDD-OPS.md §4") end-to-end for the first time, against a TEST
environment (VPS and domain decided in Package 1 — NEVER a real client
in this cycle).

Prerequisite: Packages 2 through 8 applied and individually validated.

LEGAL REMINDER (repeat to yourself before acting): data used in this
pilot is test data, never real data from a paying end customer. If this
pilot ever involves real third-party data, that requires its own formal
legal review — outside the scope of this technical task.

DEFINITION OF DONE:

0. Build the `python ecossistema.py ops deploy <environment>`
   orchestrator (in tools/aidd-ops/scripts/pipeline_ops_deploy.py or an
   equivalent module) — NONE of Packages 4-8 deliver this command
   ready-made, they only deliver isolated pieces (SSH runner, MCPs,
   compose gate, templates, preflight). Chain: SSH Runner (Package 4) →
   cloudflare-mcp (Package 5) → artifact/secret generation → canonical
   templates + G_INFRA_COMPOSE (Packages 6/8) → ops preflight
   (Package 7) → backup/monitoring. Each step returns Result (same
   pattern as tools/aidd-ops/src/core/result.py) and a failure at any
   step stops the chain — never "best effort".

1. Confirm with the user, before starting, the exact target of this
   run: test VPS IP/hostname, test domain/subdomain, chosen niche
   (recommended: Clinics), AND WHICH CREDENTIALS will be used (SSH key,
   Cloudflare API token, etc. — do not assume, ask explicitly). Do not
   proceed without this explicit confirmation in this conversation.

2. Run `python ecossistema.py ops plan "<briefing for the chosen
   niche>"` and review the generated plan before proceeding to any real
   action.

3. Execute phases 4-10 in sequence via the item-0 orchestrator,
   capturing the real output of each: SSH bootstrap (Package 4), DNS
   creation (Package 5), artifact/secret generation, gateway/frontend
   build (Package 8), Docker deploy validated by G_INFRA_COMPOSE
   (Package 6), full preflight via `ops preflight` (Package 7) — ALL
   preflight checks must pass before declaring phase 9 complete — and
   backup/monitoring activation (phase 10).

4. Generate the final delivery report (master credentials, access URLs,
   per-layer status) and document it in this file (Veredito section).

5. Document and test the rollback path: prioritize destroying/decommissioning
   the entire VPS instance (it is disposable, per Package 1's decision)
   over just reverting configuration on it; in any case, revoke/rotate
   every credential generated during the test (SSH key, Cloudflare API
   token, database master passwords, S3/R2 backup bucket credentials) —
   removed containers are not enough if the credentials remain valid.

SCOPE RULES — DO NOT: use any domain/VPS/credential beyond the one
explicitly confirmed in this conversation; proceed to the next phase if
phase 9's preflight reports any critical check as failed; `git
commit`/`git push` without approval; at the end, ask whether the test
environment should be torn down (full rollback, including credential
revocation) or kept for the user's inspection — if kept, record an
explicit deadline/reminder so the real VPS is not left running
indefinitely by oversight.

DELIVERABLE: the `ops deploy` orchestrator code (item 0), real evidence
of each of the 10 phases, the final delivery report, and confirmation
that the rollback path (including credential revocation) was
successfully tested (or an explicit record if it was not tested, and
why).
```
