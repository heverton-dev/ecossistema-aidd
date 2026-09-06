# PROCESSO E DECISÕES — Integração da Feature AIDD-Ops

> **Origem:** `docs/features/PLANO ARQUITETURAL NOVA FEATURE AIDD-OPS.md` (proposta original) e `docs/planos/integracao-aidd-ops/PLANO-INTEGRACAO-AIDD-OPS.md` (parecer técnico e visão geral dos 9 pacotes).
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
- `01-decisao-escopo-e-mvp.md` — bloco de decisão do usuário (§4 do plano-mestre); nenhum outro pacote começa antes deste.
- `02-fundamentos-governanca-gates.md`
- `03-mvp-tools-aidd-ops-fases-1-3.md`
- `04-ssh-runner-execucao-remota.md`
- `05-mcps-borda-cloudflare-docker.md`
- `06-gate-infra-compose.md`
- `07-gate-preflight-e2e.md`
- `08-templates-canonicos-e-generator-flag.md`
- `09-validacao-e2e-piloto-real.md`

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
- **Suporte multi-harness da nova ferramenta:** seguindo a Regra de Ouro #6 do `AGENTS.md` (Supremacia Agnóstica), qualquer skill/comando/gate novo criado para `tools/aidd-ops/` precisa passar por `python ecossistema.py components verify` como qualquer outro componente — isso é herdado do protocolo já existente (`docs/protocolos/PROTOCOLO-AGNOSTICIDADE-COMPONENTES.md`), não reinventado aqui.

---

## 6. Registro de progresso

| Pacote | Status | Documento |
|---|---|---|
| 1. Decisão de escopo e MVP | ✅ Concluído em 06/09/2026 — 5ª ferramenta oficial (implementação restrita a Fases 1-3 no Pacote 3), MVP primeiro, VPS descartável já disponível (detalhes só no Pacote 4), piloto = Clínicas | `01-decisao-escopo-e-mvp.md` |
| 2. Fundamentos de governança | ⏳ Diagnóstico + Definição de Pronto + Prompt de Execução prontos, aguardando execução. 2 achados reais da verificação: (1) só `G_ECOSSISTEMA_INTEGRIDADE.py` precisa mudar agora — `G_CLI_HELP_CONSISTENCIA` e `G_DRIFT_NUCLEO_COMPARTILHADO` NÃO; (2) rascunho inicial mandava criar `skills/aidd-ops-runner/SKILL.md` e os slash commands direto no destino — CORRIGIDO para criar a fonte canônica em `componentes/compartilhado/` + `components sync`, conforme processo já homologado | `02-fundamentos-governanca-gates.md` |
| 3. MVP `tools/aidd-ops/` (Fases 1-3) | ⏳ Diagnóstico + Definição de Pronto + Prompt de Execução prontos, aguardando execução do Pacote 2 primeiro. Desenhado como 100% determinístico (zero LLM), ver `VEREDITO-TECNICO-VIABILIDADE.md` §6 | `03-mvp-tools-aidd-ops-fases-1-3.md` |
| 4. SSH Runner | ⏳ Escrito por agente paralelo, **verificado e corrigido** por auditoria independente: faltava amarrar ao Result monad/gate próprio do Pacote 3, faltava `requirements.txt` com paramiko, faltava gate estrutural para a garantia "lista fechada de operações", critério de saída era mais fraco que o padrão — as 4 correções foram aplicadas ao documento | `04-ssh-runner-execucao-remota.md` |
| 5. MCPs de borda (Cloudflare/Docker) | ⏳ Escrito por agente paralelo, **verificado e corrigido**: achado crítico comprovado por execução real — `components verify --tipo mcp` retorna exit 0 com 0 componentes se o escopo `aidd-ops` não estiver registrado (falso positivo real); também corrigido: dependência inexistente do domínio de teste "decidido no Pacote 1" (não existe), ambiguidade sobre `down`/`rm` do docker-mcp (removida do escopo deste pacote), biblioteca HTTP não especificada (fixado `urllib.request`) | `05-mcps-borda-cloudflare-docker.md` |
| 6. Gate `G_INFRA_COMPOSE` | ⏳ Escrito por agente paralelo, **verificado e corrigido**: dependência de Docker não tratada com honestidade (adicionado `shutil.which("docker")` + falha estruturada, não traceback cru); referência quebrada ao artefato do Pacote 3 (nome errado `plano-infra-*.json` → corrigido para `PLANO-INFRAESTRUTURA.json`, estático e por-nicho); caminho de templates corrigido para bater com o Pacote 8 | `06-gate-infra-compose.md` |
| 7. Comando `ops preflight` (Pre-Flight E2E) | ⏳ Escrito por agente paralelo, **verificado e ajustado**: barreira de aprovação pontual confirmada correta, sem violação; método de teste local era vago demais (só "mocks") — corrigido para exigir servidor HTTP/TLS local real + certificado self-signed + resolver DNS injetável, mesmo rigor de `test_oidc_sso.py`; nomenclatura corrigida (não é um arquivo `gates/G_*.py`, é subcomando `ops preflight`) | `07-gate-preflight-e2e.md` |
| 8. Templates canônicos de infraestrutura | ⏳ Escrito por agente paralelo, **verificado e corrigido**: erro factual nos tipos do manifesto corrigido, caminho de exemplo corrigido (`tools/aidd-ops/templates/infra/`, não `componentes/templates/`). **Decisão do usuário (06/09/2026): a Parte B original (flag `--type=infra-stack` acoplando aidd-generator a aidd-ops) foi REJEITADA** — contradizia "cada ferramenta é standalone" (Rodada 2) — removida do pacote, não será implementada | `08-templates-canonicos-e-generator-flag.md` |
| 9. Validação E2E com piloto real | ⏳ Escrito por agente paralelo, **verificado e corrigido**: achado crítico — o comando `ops deploy <ambiente>` era invocado mas nenhum pacote (2-8) se comprometia a construí-lo; corrigido adicionando essa responsabilidade como Fase 0 deste pacote. Também corrigido: rollback sem opção de decomissionar a VPS inteira nem revogar credenciais; confirmação pontual sem pedir "quais credenciais"; sem reforço do teto LGPD/jurídico dentro do próprio documento autocontido | `09-validacao-e2e-piloto-real.md` |

Esta tabela é atualizada ao final de cada pacote — nunca antes da validação real daquele pacote. Todos os 9 pacotes (mais o veredito técnico) são, até agora, só PLANO — nenhuma linha de código de `tools/aidd-ops/` foi escrita ainda; nenhum pacote foi de fato executado.

---

## 7. O que nunca muda neste processo, mesmo sob pressão de terminar rápido

- Nenhum pacote de risco (4, 5, 7, 9) executa contra sistema real sem o pedido explícito e pontual descrito em §4.
- Nenhuma nota/status sobe neste registro sem o comando de validação correspondente ter sido rodado de verdade.
- Onde existir um teto estrutural (custo de infraestrutura, escopo jurídico — §5), isso fica documentado honestamente, nunca escondido para parecer que o pacote está "mais pronto" do que está.
