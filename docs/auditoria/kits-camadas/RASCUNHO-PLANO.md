# Kits por camada — rascunho de plano

> **Status:** RASCUNHO, proposto em 02/10/2026 e aprovado pelo usuário só como registro. Começa depois do Bloco 5 do `fronteiras-ferramentas` ciclo-01. Nada foi criado além deste arquivo. Quando o ciclo abrir, `python scripts/scaffold_auditoria.py kits-camadas` gera a estrutura `ciclo-01/` e este rascunho vira o `PLANO-EVOLUCAO.md` (padrão 4F).

## A ideia

Toda aplicação, venha do `aidd-pure`, do `aidd-open` ou do `aidd-freedom`, entrega as mesmas 9 camadas de `docs/padroes/PADRAO-OURO-ARQUITETURA-CAMADAS-MERCADO.md`. Cada camada ganha um **kit** completo, guardado no almoxarifado (`componentes/compartilhado/`) e entregue ao projeto pelo forge, para as 3 ferramentas usarem a mesma versão:

| Parte do kit | O que é | Regra |
|---|---|---|
| Molde | O estado da arte da camada, pronto para o projeto | Guarda a **fonte e a data** da referência |
| Guarda | Gate hiper-especializado na camada | Prova que morde (Lei #13) |
| Script determinístico | Só onde a regra é matemática | Sem LLM (Lei #1) |
| Testes TDD | Vermelho primeiro, depois verde | Zero stubs |
| Campainha (hook) | Só onde o erro é difícil de desfazer | No máximo 2 no ecossistema inteiro |
| Referência da skill | Uma seção por camada numa skill única | Não criar 9 skills novas |

## Quantas peças

9 camadas × 6 partes dariam 54, mas nem toda camada precisa de tudo. A estimativa é de **cerca de 41**: 32 peças novas e 9 referências da skill.

| Parte | Quantas | Por quê |
|---|---|---|
| Molde | 9 | um por camada |
| Guarda | 9 | uma por camada; nas camadas 6 e 8 o gate atual já cobre parte e pode ser aproveitado |
| Testes TDD | 9 | um conjunto por camada |
| Script determinístico | cerca de 4 | só onde a regra é matemática: contraste OKLCH (1), assinatura HMAC (4), migração (7), cobertura do Quarteto (8) |
| Hook | 1 novo | migração destrutiva; o de segredo já existe (`G_SEGREDOS`) |
| Skill | 1 skill com 9 referências | uma skill, não nove |

O número exato sai da fase de medição real, que mostra quais gates atuais servem de guarda.

## Decisões já tomadas

1. **Uma skill só, com 9 referências**, em vez de 9 skills: a renomeação de 26/09 reduziu de 75 para 37 skills, e 9 novas desfariam o ganho.
2. **Hooks só onde o erro é caro**: migração de banco destrutiva (camada 7) e segredo em código (já existe o `G_SEGREDOS`). Hook em toda camada deixa o commit lento de novo (o ciclo `agilidade-gates` levou o commit de 20 min para 2–3 min).
3. **Molde com validade**: cada molde registra fonte e data; uma guarda avisa quando passar de 90 dias sem revisão. Sem isso, "o mais atualizado" envelhece sem ninguém ver.
4. **Piloto na camada 4** (offline-first + HMAC): tem a parte mais matemática e hoje a guarda só confere se o módulo existe. Se o kit funcionar nela, replicar nas outras 8.

## Medição inicial do que já existe

> Feita por nome e descrição dos gates e do catálogo em 02/10/2026. **Não substitui reprodução real**: a primeira fase do ciclo roda cada gate contra um projeto que quebra a camada e registra se ele reprova de verdade.

| # | Camada | Gates que já cobrem | Peças no catálogo | Lacuna provável |
|---|---|---|---|---|
| 1 | Visual (OKLCH, Tailwind, microinterações) | `G_NOVE_CAMADAS_MERCADO` (procura tokens `oklch` e Tailwind), `G_QUALIDADE` (linter básico de UI) | `mcps/mobbin_mcp` (MCP Mobbin registrado); pipeline Impeccable real nos harnesses | molde de tokens; script de contraste em OKLCH; integração Mobbin + Impeccable real |
| 2 | Rotas e cascas (TanStack Router/Start) | `G_STACK_PADRAO_OURO`, `G_FRONTEND_LAYERS`, `G_TEMPLATE_TANSTACK_OFFLINE` | nenhuma | molde no catálogo (o template vive fora dele) |
| 3 | PWA (Vite PWA + Workbox) | `G_NOVE_CAMADAS_MERCADO` (detecta a configuração), `G_TEMPLATE_TANSTACK_OFFLINE` | nenhuma | guarda do manifesto e do service worker |
| 4 | Offline-first + HMAC | `G_NOVE_CAMADAS_MERCADO` (procura a fila e a palavra HMAC), `G_TEMPLATE_TANSTACK_OFFLINE` | nenhuma | **piloto**: script que assina e confere a fila de verdade |
| 5 | Estado e contratos (TanStack Query + Zod) | `G_NOVE_CAMADAS_MERCADO`, `G_CONTRACT_ROT` | `specs/` (11) | guarda de esquema Zod contra o OpenAPI |
| 6 | Backend modular (VSA + OpenAPI 3.1) | `G_DISPATCH_PIPELINE_VSA`, `G_ARQUITETURA_DELIVERABLE`, `G_CONTRACT_ROT` | `src-core/` (40) | o mais coberto; revisar só a guarda de fatias |
| 7 | Banco (PostgreSQL / SQLite WAL) | `G_MIGRATION_ROT`, `G_TRANSACTION_LOG_LRU`, `G_ESCRITOR_ATOMICO`, `G_NOVE_CAMADAS_MERCADO` | nenhuma | molde de migração; hook de migração destrutiva |
| 8 | Quarteto (`/api`, `/webhook`, `/mcp`, `/docs`) | `G_QUARTETO_SINE_QUA_NON`, `G_CONTRACT_ROT` | `moldes/quarteto` (18) | script de cobertura do Quarteto sobre os módulos |
| 9 | Observabilidade e testes reais | `G_TESTES_REAIS`, `G_PORTAO_PROVA_QUE_MORDE`, `G_ZERO_HEADLESS` | nenhuma | molde de observabilidade (logs, métricas) |

## Ordem proposta

1. **Fase de medição real**: um projeto quebrado por camada; registrar quais gates reprovam e quais deixam passar.
2. **Piloto camada 4**: molde, guarda, script, testes e referência da skill.
3. **Revisão do piloto com o usuário** antes de replicar.
4. **Camadas 1, 7 e 8** (onde há regra matemática ou erro caro).
5. **Camadas 2, 3, 5, 6 e 9**.
6. **Prova final**: os 3 fluxos com um harness de verdade respondendo os pedidos de IA, e o `G_NOVE_CAMADAS_MERCADO` rodando no app gerado por cada fluxo.

## Dependências

- Bloco 2 do `fronteiras-ferramentas` (almoxarifado e `forge fornecer`): **feito**.
- Bloco 4 (remoção das cópias): os kits entram no catálogo depois que as cópias saírem, para não nascerem duplicados.
- Regra do usuário: o ecossistema nunca tem LLM ou API key configurada; o modelo é sempre o do harness (protocolo delegado). Nenhum script do kit chama API.
