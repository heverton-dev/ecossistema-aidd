# PLANO DE INTEGRAÇÃO — Feature AIDD-Ops no Ecossistema AIDD

> **Origem:** `docs/features/06-09-2026_feature-arquitetura-aidd-ops.md` (proposta v2.1, Setembro/2026) — Meta-Orquestrador Agêntico de Infraestrutura e Stacks Open Source (alternativa white-label ao GoHighLevel).
> **Status:** PARECER TÉCNICO CONCLUÍDO — Pacote 1 (decisão de escopo/MVP) já decidido pelo usuário em 06/09/2026 (ver `integracao-aidd-ops/01-decisao-escopo-e-mvp.md`). Pacotes 2-9 seguem bloqueados por dependência sequencial e, nos casos 4/5/7/9, por aprovação pontual adicional antes de tocar infraestrutura real (ver `integracao-aidd-ops/00-PROCESSO-E-DECISOES.md §4`).
> **Documentos-irmãos:** `integracao-aidd-ops/00-PROCESSO-E-DECISOES.md` (processo) + `integracao-aidd-ops/01..09-*.md` (pacotes técnicos individuais).

---

## 1. Objetivo deste documento

Responder, com evidência real coletada no repositório (não impressão), duas perguntas:

1. **A proposta AIDD-Ops agrega valor real ao ecossistema-aidd?**
2. **Se sim, qual é o caminho de integração que não repete o próprio erro que a proposta identifica em outros contextos** (§5.1 da proposta: "clonar e fundir tudo de uma vez é inviável — a abordagem correta é modular e incremental")?

Este plano não implementa nada. Ele organiza a decisão e, uma vez aprovada, entrega o roteiro pacote-a-pacote em `integracao-aidd-ops/`.

---

## 2. Parecer técnico — a proposta agrega valor?

**Veredito: sim, mas não do jeito e no tamanho em que foi proposta.**

A proposta descreve corretamente uma solução tecnicamente sólida para orquestrar infraestrutura self-hosted (Traefik + Authentik + Next.js + microsserviços Docker + PostgreSQL centralizado com bancos lógicos isolados). As decisões de engenharia da Seção 5 dela (Cenário A de banco vs. anti-padrão de tabela compartilhada; Gateway próprio vs. n8n; imagens oficiais vs. Dockerfile) estão corretas e bem justificadas. O gap de mercado que ela mira (alternativa soberana ao GoHighLevel, sem contadores de contato/sobretaxa, self-hosted) é real.

O problema não é a arquitetura da feature — é o enquadramento de como ela se encaixa no ecossistema-aidd **hoje**:

### 2.1 O que a proposta acerta sobre o ecossistema
- Reconhece explicitamente (§8.1) que o ecossistema-aidd atual é "Desenvolvimento e Governança de Código de Software Local" — não confunde o produto com o que ele não é.
- Os 4 "Ajustes" propostos (§8.3: nova ferramenta em `tools/`, gates novos, templates canônicos, flag no generator) usam exatamente o vocabulário e os diretórios reais do repositório (`tools/`, `gates/`, `componentes/`) — não é uma proposta genérica colada por cima.

### 2.2 O que a proposta subestima ou erra (verificado no código, não em documentação)
| Afirmação da proposta | Realidade verificada | Impacto |
|---|---|---|
| "Criação da 5ª Ferramenta" (§8.3, Ajuste 1) | `AGENTS.md §1` define o ecossistema como "**4 ferramentas complementares**" — e esse número está **hardcoded**, não é só prosa: `ecossistema.py:115-120` (`cmd_status`) lista as 4 por nome; `ecossistema.py:168-179` (`dispatch`) mapeia exatamente 4 comandos; `gates/G_ECOSSISTEMA_INTEGRIDADE.py`, `gates/G_CLI_HELP_CONSISTENCIA.py` (documentado como cobrindo "19 arquivos `argparse` das 4 ferramentas") e `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` (compara especificamente `aidd-master` vs `aidd-enterprise`) foram escritos assumindo essa cardinalidade fixa. | Adicionar uma 5ª ferramenta não é "criar uma pasta em `tools/`" — é uma mudança sistêmica na camada de governança que toca no mínimo 3 dos 6 gates e o CLI raiz. A proposta não menciona isso. |
| "Gap 2: catálogo de componentes atual não possui conectores oficiais para provedores de infraestrutura" (§8.2) | Impreciso: a convenção de MCPs **já existe** — `componentes/aidd-enterprise/mcps/` (pasta viva, hoje vazia) e `componentes/aidd-generator/mcps/mcp-verificador-cve/server.py` (MCP real, funcional, já em produção no repo). | O gap real não é "criar a convenção de MCP" (já existe) — é "não existe nenhum MCP de infraestrutura ainda". Diferença pequena mas relevante: o trabalho de Ajuste 2 é mais barato do que a proposta descreve. |
| "Ajuste 3: Catálogo de Templates Canônicos de Infraestrutura" | Confirmado: **não existe** nenhuma pasta `templates/` em `componentes/` hoje, de nenhum tipo. Este seria o primeiro precedente de "template" no repo — não um padrão existente sendo estendido. | Corretamente identificado pela proposta, mas sem precedente para copiar o estilo — este pacote exige desenho de convenção nova, não replicação. |
| Nenhuma menção a custo/natureza dos testes dos gates novos propostos (`G_INFRA_COMPOSE`, `G_PRE_FLIGHT_E2E`) | Os 6 gates atuais são **100% estáticos e offline** (AST, regex, diff de arquivo, JSON) — rodam em segundos, sem custo, sem efeito colateral em sistemas de terceiros. `G_PRE_FLIGHT_E2E`, como descrito (curl real em `/healthz`, validação de SSL emitido, webhook simulado ponta-a-ponta), é um teste de integração contra **infraestrutura viva** (VPS real, DNS real do Cloudflare) — categoria de teste que o ecossistema nunca precisou rodar em `python ecossistema.py audit`. | Isso não invalida a ideia, mas ela não pode entrar na mesma bateria síncrona/determinística/gratuita dos outros 6 gates sem redesenho (ambiente de teste isolado, custo de VPS de CI, tratamento de flakiness de rede). |
| Blast radius | As 4 ferramentas atuais leem/escrevem exclusivamente no workspace local do desenvolvedor. AIDD-Ops, por desenho, ganha SSH em servidor real, criação de registros DNS públicos e geração de credenciais mestre para bancos com dados reais de clientes finais (implicação LGPD explícita, citada na própria proposta §7). | Categoria de risco nova e maior que qualquer coisa hoje governada pelo ecossistema. Nenhum gate atual foi desenhado para impedir uma ação irreversível contra um ambiente de produção real de terceiros. |

### 2.3 Conclusão do parecer
A feature **deve avançar**, porque preenche uma lacuna real e a arquitetura técnica proposta é consistente com os princípios do próprio `AGENTS.md` (determinismo, especialização de subagentes, gates binários). Mas ela precisa ser tratada como o que realmente é: **uma mudança de categoria de produto** (de "governança de geração de código local" para "operador de infraestrutura remota multi-tenant"), não como "mais uma ferramenta igual às outras 4". Isso muda a ordem de execução: antes de escrever uma linha de `tools/aidd-ops/`, a camada de governança (AGENTS.md, `ecossistema.py`, gates que assumem "4 ferramentas") precisa reconhecer explicitamente a 5ª peça — e a primeira execução contra infraestrutura real precisa de um portão de aprovação humana que hoje não existe em nenhum gate do repositório.

---

## 3. Estrutura dos pacotes de integração

Seguindo o mesmo método já usado em `docs/planos/evolucao-notas-auditoria/` (ciclo fechado por pacote: diagnóstico → Definição de Pronto → implementação → validação real → registro), a integração da AIDD-Ops foi quebrada em **9 pacotes**, deliberadamente sequenciados por risco crescente (do puramente estático/offline ao que toca infraestrutura real de terceiros):

| # | Pacote | Toca infra real? | Documento |
|---|---|:---:|---|
| 1 | Decisão de escopo e estratégia de MVP | Não | `01-decisao-escopo-e-mvp.md` |
| 2 | Fundamentos de governança (AGENTS.md, `ecossistema.py`, gates que assumem "4 ferramentas") | Não | `02-fundamentos-governanca-gates.md` |
| 3 | MVP do `tools/aidd-ops/` — só Fases 1-3 do pipeline (Intake, Curadoria, Sizing) | Não | `03-mvp-tools-aidd-ops-fases-1-3.md` |
| 4 | SSH Runner determinístico (Gap 1 da proposta) | Sim (primeira vez) | `04-ssh-runner-execucao-remota.md` |
| 5 | MCPs de borda — Cloudflare DNS + Docker (Gap 2) | Sim | `05-mcps-borda-cloudflare-docker.md` |
| 6 | Gate `G_INFRA_COMPOSE` (Gap 3) | Não (estático) | `06-gate-infra-compose.md` |
| 7 | Gate `G_PRE_FLIGHT_E2E` (Gap 4) | Sim | `07-gate-preflight-e2e.md` |
| 8 | Templates canônicos de infra (ver nota) | Não | `08-templates-canonicos-e-generator-flag.md` |
| 9 | Validação end-to-end com 1 nicho piloto real (ex.: Clínicas) | Sim | `09-validacao-e2e-piloto-real.md` |

> **Nota (06/09/2026):** o Pacote 8 originalmente também incluía uma flag `--type=infra-stack` no `aidd-generator`, acoplando-o ao `aidd-ops` via subprocess. Auditoria independente identificou que isso contradizia a decisão de "cada ferramenta é standalone" (Rodada 2) sem reconciliar essa tensão — o usuário decidiu **rejeitar** esse acoplamento. O Pacote 8 cobre hoje só os templates canônicos.

**Regra de sequenciamento:** pacotes 1-3 e 6, 8 não têm nenhum efeito colateral fora do workspace local — podem ser executados e validados sem custo e sem risco a terceiros. Pacotes 4, 5, 7 e 9 tocam sistemas reais (SSH, DNS, VPS) e **exigem aprovação explícita e pontual do usuário antes de cada execução**, não apenas aprovação do plano como um todo.

---

## 4. Decisões do usuário — Pacote 1 (registradas em 06/09/2026)

Detalhadas em `integracao-aidd-ops/01-decisao-escopo-e-mvp.md`. Resumo:

1. **Estatuto da ferramenta:** AIDD-Ops entra desde já como 5ª ferramenta oficial do ecossistema — `AGENTS.md §1` e os gates que hoje fixam "4 ferramentas" serão atualizados (Pacote 2), mas a implementação real do Pacote 3 fica restrita às Fases 1-3 (sem SSH/DNS/deploy reais), para não abrir uma ferramenta "oficial" que ainda não faz nada de arriscado.
2. **MVP primeiro:** confirmado. Pacote 3 entrega só Fases 1-3 (Intake, Curadoria, Sizing); Fases 4-10 só avançam a partir do Pacote 4, cada uma com seu próprio ciclo de aprovação pontual.
3. **Ambiente de teste (pacotes 4, 5, 7, 9):** já existe uma VPS descartável disponível — detalhes de acesso (IP, chave) serão coletados só quando o Pacote 4 começar, não antes.
4. **Nicho piloto (pacote 9):** Clínicas & Odontologia (Typebot + Twenty CRM + Chatwoot/Evolution API + Cal.com) — menor superfície de integração entre as 5 opções da proposta original.

O Pacote 2 está desbloqueado. Pacotes 4, 5, 7 e 9 continuam exigindo aprovação pontual separada antes de tocar infraestrutura real, independentemente desta decisão de escopo (ver `integracao-aidd-ops/00-PROCESSO-E-DECISOES.md §4`).
