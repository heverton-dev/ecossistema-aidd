# Proposta: nomes padronizados das skills (mapa-pecas ciclo-01)

> **Status:** APROVADA pelo usuário em 26/09/2026, com ordem de execução em sessão dedicada (branch próprio a partir de `aidd/mapa-pecas-ciclo-01`).
> **Regra aplicada:** `docs/protocolos/CONVENCAO-AUTORIA-SKILLS.md`, seção 5.3 (decisões do usuário de 26/09/2026).
> **Medido em:** `main` `f033773`, 75 skills em `componentes/compartilhado/skills/`.

## Resultado

| | Hoje | Depois |
|---|---|---|
| Skills nossas | 56 | **37** |
| Skills de terceiros dentro da fonte única | 19 | **0** (passam para `gates/dependencias_externas.json`) |
| Pares com a mesma descrição | 13 | **0** |
| Sufixo `-runner`, número ou nome sem `aidd-` | 29 | **0** |
| Nome com palavra em português | 18 | **0** (o comando slash em PT-BR continua) |

Os comandos slash que as pessoas digitam (`/pure`, `/open`, `/freedom`, `/melhoria`, `/plan`, `/orchestrate`…) **não mudam**: eles passam a chamar a skill `aidd-*` correspondente.

## Tabela de-para

Ação: **manter** (nome já certo) · **renomear** · **fundir** (várias viram uma; o conteúdo maior e mais recente prevalece, o resto vai para `references/`) · **sai** (o conteúdo foi fundido; vira comando slash, se necessário).

### Fluxos da Tríade (11 → 3)

| Hoje | Depois | Ação |
|---|---|---|
| `aidd-pure`, `pure`, `fluxo-01-runner` | `aidd-pure` | fundir |
| `aidd-open`, `open`, `fluxo-02-runner` | `aidd-open` | fundir |
| `aidd-freedom`, `freedom`, `fluxo-03-runner`, `aidd-bridge` (parte "dispara o Fluxo 03") | `aidd-freedom` | fundir |
| `aidd-orchestrator-runner` (roda qualquer fluxo) | cada skill de fluxo chama `run-fluxo` | sai |

### Ferramentas (8 → 8, uma por ferramenta)

| Hoje | Depois | Ação |
|---|---|---|
| `aidd-forge-runner` | `aidd-forge` | renomear |
| `aidd-planner-runner` | `aidd-planner` | renomear |
| `aidd-generator-runner` | `aidd-generator` | renomear |
| `aidd-factory-runner` | `aidd-factory` | renomear |
| `aidd-bridge-runner` | `aidd-bridge` | renomear (o nome deixa de significar "Fluxo 03") |
| `aidd-master-runner` | `aidd-master` | renomear |
| `aidd-enterprise-runner` | `aidd-enterprise` | renomear |
| `aidd-ops-runner` | `aidd-ops` | renomear |

### Oficina (19 → 12)

| Hoje | Depois | Ação |
|---|---|---|
| `aidd-melhoria`, `melhoria` | `aidd-improvement` | fundir (conteúdo real em `melhoria`, 146 linhas) |
| `aidd-plan`, `plan`, `aidd-planos`, `planos-auditoria-runner` | `aidd-plan` | fundir (moldes de plano vão para `references/`) |
| `aidd-orchestrate`, `orchestrate` | `aidd-orchestrate` | fundir (conteúdo real em `orchestrate`, 186 linhas) |
| `aidd-orca`, `orca-plan-orchestrator` | `aidd-orca` | fundir (scripts e testes vêm de `orca-plan-orchestrator`) |
| `aidd-dispatch-runner` | `aidd-dispatch` | renomear |
| `aidd-pipeline-runner` | `aidd-pipeline` | renomear |
| `aidd-auditor-4f-runner` | `aidd-audit-4f` | renomear |
| `aidd-evolucao-runner` | `aidd-evolution` | renomear |
| `aidd-sessao`, `sessao` | `aidd-session` | fundir |
| `aidd-livro-texto` | `aidd-textbook` | renomear |
| `aidd-diagnose` | `aidd-diagnose` | manter |
| `aidd-retro` | `aidd-retro` | manter |

### Peças do ecossistema (8 → 4)

| Hoje | Depois | Ação |
|---|---|---|
| `aidd-componentes`, `componentes-runner` | `aidd-components` | fundir |
| `aidd-dependencias`, `dependencia-runner` | `aidd-dependencies` | fundir (conteúdo real em `dependencia-runner`, 91 linhas) |
| `aidd-mcp`, `mcp-creator-runner` | `aidd-mcp` | fundir |
| `aidd-skills`, `skill-creator-runner` | `aidd-skills` | fundir |

### Escrita e processo (10 → 10)

| Hoje | Depois | Ação |
|---|---|---|
| `aidd-escrita-agentes` | `aidd-agent-writing` | renomear |
| `aidd-entrega` | `aidd-delivery` | renomear |
| `aidd-reexplica` | `aidd-reexplain` | renomear |
| `aidd-grill`, `aidd-grill-docs`, `aidd-handoff`, `aidd-spec`, `aidd-tdd`, `aidd-tickets`, `aidd-wizard` | iguais | manter |

### Terceiros (19 → saem da fonte única)

| Fornecedor | Skills | Ação |
|---|---|---|
| Cloudflare | `agents-sdk`, `cloudflare`, `cloudflare-email-service`, `cloudflare-one`, `cloudflare-one-migrations`, `durable-objects`, `nextjs-on-cloudflare`, `sandbox-migrate-to-next`, `sandbox-next`, `sandbox-stable`, `turnstile-spin`, `web-perf`, `workers-best-practices`, `wrangler` | registrar em `dependencias_externas.json` com o instalador oficial; tirar de `componentes/` |
| impeccable | `impeccable` | já registrada; tirar a cópia de `componentes/` |
| code-review-graph | `debug-issue`, `explore-codebase`, `refactor-safely`, `review-changes` | já registradas; tirar as cópias de `componentes/` |

## Além dos nomes

- **Idioma do conteúdo:** cerca de 33 skills nossas têm o corpo em português (medido por heurística de palavras, então é uma estimativa). Elas passam para inglês na mesma etapa da fusão ou renomeação, para não mexer duas vezes no mesmo arquivo.
- **Guarda novo `G_SKILL_FORMATO`:** confere a seção 5.1 e a 5.3 (padrão do nome, nome igual à pasta, descrição com "Use when", sem `-runner`, corpo de no máximo 450 linhas).
- **`G_IDIOMA_LEI_4`:** ampliar o escopo para `componentes/*/skills/`.

## Onde a mudança encosta

Cada renomeação precisa atualizar, no mesmo commit:
- as referências no `AGENTS.md` (ex.: §3 lista `aidd-pure`, `fluxo-01-runner`, `aidd-bridge-runner`) e nos comandos em `componentes/compartilhado/comandos/`;
- os caminhos citados em `docs/protocolos/`, que o `G_DOCS_ROT` e o `G_SKILL_ROT` conferem;
- as cópias nos harnesses: `components sync` cria as novas, mas as antigas precisam ser apagadas, senão o `G_SKILL_ROT` acusa skill órfã;
- os testes que citam nome de skill (ex.: `tests/fixtures/skills_pocock/`, que só usa nomes mantidos).

## Ordem sugerida de execução (cada etapa com commit próprio e todos os guardas verdes)

1. **Terceiros para fora** (19). É a que menos arrisca: nada nosso depende do nome deles.
2. **Guarda `G_SKILL_FORMATO` em modo aviso**, para medir antes e depois.
3. **Ferramentas** (8 renomeações simples).
4. **Fusões de fluxos e oficina** (as que exigem ler e juntar conteúdo).
5. **Peças e escrita.**
6. **`G_SKILL_FORMATO` e `G_IDIOMA_LEI_4` passam a reprovar**, e o mapa das skills é gerado.

> **Atenção:** existe outra sessão trabalhando na mesma pasta (branch `fix/csp-nonce-script-src`). A execução deve rodar num branch próprio a partir da `main` e só começar quando a outra sessão tiver commitado, porque o `components sync` reescreve as pastas dos harnesses inteiras.
