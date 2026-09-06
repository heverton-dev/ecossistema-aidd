# Pacote 1 — Decisão de Escopo e Estratégia de MVP

> **Status:** ✅ CONCLUÍDO em 06/09/2026 — as 4 decisões foram feitas pelo usuário via pergunta explícita, depois que o parecer técnico (`docs/planos/integracao-aidd-ops/PLANO-INTEGRACAO-AIDD-OPS.md`) foi verificado de verdade (não só lido) contra o código real do repositório.
> **Não toca infraestrutura real.** Só decisão + registro.

---

## Verificação real do parecer técnico (antes de pedir qualquer decisão)

As afirmações centrais de `PLANO-INTEGRACAO-AIDD-OPS.md §2.2` foram checadas contra o código, não aceitas por leitura:

| Afirmação | Verificado | Evidência |
|---|:---:|---|
| Ecossistema hoje é hardcoded para "4 ferramentas" | ✅ Confirmado | `AGENTS.md:11` ("unifica 4 ferramentas complementares"); `gates/G_ECOSSISTEMA_INTEGRIDADE.py:25-28` tem a lista literal das 4 ferramentas hardcoded (mais 4 skills, linhas 32-35) |
| `G_CLI_HELP_CONSISTENCIA` documentado como cobrindo "19 arquivos" das 4 ferramentas | ✅ Confirmado | `AGENTS.md:77` e `gates/G_CLI_HELP_CONSISTENCIA.py:17` |
| `G_DRIFT_NUCLEO_COMPARTILHADO` compara especificamente aidd-master vs aidd-enterprise (não genérico) | ✅ Confirmado | `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py:42-43` (`DIR_A`/`DIR_B` hardcoded para essas 2 ferramentas) |
| Convenção de MCP já existe, mas catálogo de infra está vazio | ✅ Confirmado | `componentes/aidd-enterprise/mcps/` existe e está vazia; `componentes/aidd-generator/mcps/mcp-verificador-cve/` é um MCP real, funcional, em produção |
| Não existe nenhuma pasta `templates/` em `componentes/` hoje | ✅ Confirmado | Busca recursiva por diretório `templates` dentro de `componentes/` não encontrou nenhum resultado |

**Conclusão da verificação:** o parecer técnico é factualmente correto. As 4 decisões abaixo partem de um diagnóstico real, não de uma leitura superficial da proposta original.

---

## Decisão real do usuário (06/09/2026, via pergunta explícita)

### 1. Status da AIDD-Ops no ecossistema

**Decisão: 5ª ferramenta oficial desde já.** `AGENTS.md` e os 3 gates que hoje fixam "4 ferramentas" (`G_ECOSSISTEMA_INTEGRIDADE`, `G_CLI_HELP_CONSISTENCIA`, `G_DRIFT_NUCLEO_COMPARTILHADO` — este último só se `aidd-ops` também ganhar um núcleo compartilhado, o que não é garantido) serão atualizados para reconhecer 5 ferramentas — isso é trabalho do **Pacote 2**.

Recomendação aplicada (registrada para o caso de precisar reverter): formalizar a governança agora, mas **restringir a implementação real do Pacote 3 só às Fases 1-3 do pipeline** (Intake, Curadoria, Sizing — zero SSH/DNS/deploy reais). Isso evita rodar 2 narrativas paralelas (ferramenta "oficial" que na prática ainda não faz nada de arriscado) e evita uma futura migração cara de "experimental" para "oficial" depois que já existir código e usuários dependendo do formato experimental.

### 2. Estratégia de MVP

**Decisão: MVP primeiro.** O Pacote 3 entrega só as Fases 1-3 (Intake & Diagnóstico de Negócio → Curadoria e Seleção da Stack → Sizing e Síntese Dinâmica da Camada de Dados) — nenhuma delas toca VPS, SSH ou DNS reais. As Fases 4-10 (Bootstrapping via SSH, DNS via Cloudflare, geração de artefatos/segredos, build do Gateway/Frontend, deploy Docker, testes pré-voo, backup/entrega) só são implementadas a partir do Pacote 4 em diante, cada uma com seu próprio ciclo diagnóstico → Definição de Pronto → aprovação pontual → implementação → validação real.

### 3. Ambiente de teste para os Pacotes 4, 5, 7 e 9

**Decisão: já existe uma VPS descartável disponível.** Os detalhes de acesso (IP, usuário, chave SSH, provedor) serão pedidos **só quando chegarmos ao Pacote 4** — não há necessidade de coletar isso agora, e não é seguro deixar esse dado registrado num documento de planejamento antes de ser efetivamente necessário.

### 4. Nicho piloto para validação end-to-end (Pacote 9)

**Decisão: Clínicas & Odontologia.** Stack: Typebot (triagem) + Twenty CRM (prontuário/pipeline) + Chatwoot/Evolution API (WhatsApp) + Cal.com (agendamento) — menor superfície de integração entre as 5 opções da proposta original, conforme recomendação do parecer técnico.

---

## Efeito imediato desta decisão

- **Pacote 2 (Fundamentos de governança) está desbloqueado** — vai atualizar `AGENTS.md §1`, `ecossistema.py` (dispatch + `cmd_status`) e os gates que assumem "4 ferramentas" para reconhecerem `aidd-ops` como a 5ª ferramenta, sem ainda existir código funcional dentro de `tools/aidd-ops/` (isso é o Pacote 3).
- **Pacotes 4, 5, 7, 9 continuam bloqueados** por aprovação pontual (SSH real, DNS real, deploy real) — a decisão de escopo aqui autoriza o diagnóstico e a implementação de código desses pacotes quando chegar a vez deles, não a execução contra a VPS/DNS reais. Isso será pedido de novo, no momento, com o alvo explícito.
- **Registro atualizado em `00-PROCESSO-E-DECISOES.md` §6** (tabela de progresso).
