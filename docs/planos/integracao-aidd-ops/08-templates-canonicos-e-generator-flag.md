# Pacote 8 — Templates Canônicos de Infraestrutura

> **Status:** ⏳ Bloqueado pelo Pacote 3 (pode rodar em paralelo aos Pacotes 4-7).
> **Ajuste original coberto:** Ajuste 3 (Catálogo de Templates Canônicos) — §8.3 da proposta.
> **Decisão do usuário (06/09/2026):** a proposta original também incluía uma "Parte B" (flag `--type=infra-stack` no `aidd-generator`, acoplando-o ao `aidd-ops` via subprocess). O usuário **rejeitou esse acoplamento** explicitamente — contradizia a decisão já registrada de que cada ferramenta do ecossistema é standalone (Rodada 2). A Parte B **não faz parte deste pacote nem de nenhum outro** — quem quiser um plano de infraestrutura usa `ecossistema.py ops plan` diretamente. Este documento cobre só os templates canônicos (a parte que tinha valor real e não tinha problema de acoplamento).

---

## Diagnóstico

Confirmado: **não existe hoje nenhuma pasta `templates/` em `componentes/`**, de nenhum tipo — este pacote não estende um padrão existente, cria o primeiro precedente. Isso muda a natureza do trabalho: além de escrever os templates em si (Traefik com TLS, Authentik SSO, Twenty CRM, Chatwoot, Cal.com, Gateway FastAPI, PostgreSQL centralizado), é preciso decidir a convenção de onde/como um "template de infraestrutura" vive.

**Correções aplicadas após auditoria real (verificação independente):**
- **Erro factual corrigido:** a versão original deste diagnóstico afirmava que `gates/manifesto_harnesses.json` cobre os tipos `skill, mcp, rule, spec, roteiro, config`. Carregando o JSON real (`tipos_componente.keys()`), o conjunto correto é **`skill, command, mcp, spec, config, hook, sub-agent, script`** — não existe `rule` nem `roteiro` no manifesto (provável confusão com a chave `"rule"` de `CANONICAL_TEMPLATES` do injetor, que é outra coisa). A conclusão prática não muda (`templates` não é um tipo reconhecido hoje), mas a evidência estava errada.
- **Analogia real confirmada (ponto forte do pacote, mantido):** `tools/aidd-master/templates/core/` e `tools/aidd-master/templates/v2/` existem de verdade e são consumidos internamente por `tools/aidd-master/scripts/provision_project.py` via cópia direta de arquivo (`shutil.copyfile`), **nunca** pelo mecanismo de `gestor_componentes.py`/`components sync`. Essa é a analogia real e correta que justifica a recomendação abaixo.
- **Inconsistência de caminho corrigida:** a versão original recomendava "templates ficam internos a `tools/aidd-ops/`, sem sync" mas usava `componentes/templates/infra/<bloco>/` como caminho de exemplo — isso contradiz a própria recomendação e quebraria a convenção real `componentes/<ferramenta>/<tipo>/` (confirmada em disco: toda pasta de 1º nível de `componentes/` é nomeada por ferramenta ou `compartilhado`, nunca por tipo solto). **Caminho corrigido para `tools/aidd-ops/templates/infra/<bloco>/`**, coerente com o precedente real de `tools/aidd-master/templates/`.
- **Parte B removida (decisão do usuário):** a proposta de flag `--type=infra-stack` no `aidd-generator` faria seu pipeline de 8 fases invocar `ecossistema.py ops plan` via subprocess — a primeira vez que uma ferramenta do ecossistema dependeria, em tempo de execução, de outra. Isso contradizia, sem citar nem reconciliar, a decisão já registrada na Rodada 2 (`docs/planos/refinamento-notas-auditoria/04-unificacao-injetor-aidd-enterprise.md`, linha 86: cada ferramenta é standalone). O usuário decidiu **rejeitar** esse acoplamento — a Parte B foi removida deste pacote e não será implementada em nenhum outro, a menos que uma decisão futura explícita reabra essa discussão.

---

## Definição de Pronto

1. Convenção decidida: templates de infraestrutura ficam como conteúdo estático interno de `tools/aidd-ops/templates/infra/<bloco>/` — **sem** passar pelo mecanismo de sincronização multi-harness (`components sync`), pelo mesmo motivo e mesmo padrão real que `tools/aidd-master/templates/` já usa (consumidos pela própria ferramenta, não por um harness de IA).
2. Blocos construtivos mínimos versionados (cada um com `docker-compose.yml` + `.env.example` + `README.md` de uso): Traefik com TLS Let's Encrypt; Authentik SSO com PostgreSQL próprio; Twenty CRM; Chatwoot; Cal.com; Gateway FastAPI mínimo; PostgreSQL centralizado com `init-multiple-databases.sh` parametrizável.
3. Todo `docker-compose.yml` novo criado neste pacote passa por `gates/G_INFRA_COMPOSE.py` (Pacote 6) antes de ser considerado pronto, se o Pacote 6 já estiver aplicado — senão, `docker compose config` manual, documentando a validação formal como pendente.
4. Para cada um dos 5 nichos do catálogo (`tools/aidd-ops/data/catalogo_nichos.json`, Pacote 3), criar um `PLANO-INFRAESTRUTURA.json` **estático e versionado** dentro do próprio bloco de template correspondente — este é o artefato estático que o `gates/G_INFRA_COMPOSE.py` (Pacote 6) usa para conferir que todo banco lógico citado tem entrada correspondente no script `init-multiple-databases.sh`.

## Critério de saída

- Os 7 blocos construtivos criados em `tools/aidd-ops/templates/infra/<bloco>/`, cada um com `docker-compose.yml` + `.env.example` (sem valor sensível hardcoded) + `README.md`.
- `docker compose config` (ou `gates/G_INFRA_COMPOSE.py`, se o Pacote 6 já estiver aplicado) → exit 0 para todo `docker-compose.yml` novo.
- Um `PLANO-INFRAESTRUTURA.json` estático por nicho do catálogo, coerente com os bancos lógicos de cada bloco.
- `git status` limpo além dos arquivos esperados.

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai criar o catálogo de templates canônicos de infraestrutura para
tools/aidd-ops/, cobrindo o Ajuste 3 de "docs/features/PLANO
ARQUITETURAL NOVA FEATURE AIDD-OPS.md §8.3". NÃO EXISTE hoje nenhuma
pasta templates/ em componentes/ — você está criando o primeiro
precedente, não estendendo um padrão existente.

DECISÃO JÁ TOMADA (não reabra): templates de infraestrutura ficam como
conteúdo estático interno de tools/aidd-ops/templates/infra/<bloco>/ —
SEM passar por components sync (mesmo padrão real de
tools/aidd-master/templates/core|v2, consumidos internamente por
provision_project.py via shutil.copyfile, nunca por
gestor_componentes.py). NÃO existe nenhuma flag nova no aidd-generator
neste pacote nem em nenhum outro — essa extensão foi avaliada e
REJEITADA pelo usuário por acoplar duas ferramentas que devem
permanecer standalone. Não implemente nada em tools/aidd-generator/.

Pré-requisito: Pacote 3 aplicado (tools/aidd-ops/ existe com `ops plan`
e o catálogo de nichos em tools/aidd-ops/data/catalogo_nichos.json).
Recomendado (mas não bloqueante): Pacote 6 aplicado (G_INFRA_COMPOSE já
existe para validar os composes que você vai criar).

DEFINIÇÃO DE PRONTO:

1. Crie os 7 blocos construtivos em
   tools/aidd-ops/templates/infra/<bloco>/, cada um com
   docker-compose.yml + .env.example (sem valor sensível hardcoded,
   só nomes de variável) + README.md curto de uso: Traefik com TLS
   Let's Encrypt; Authentik SSO com PostgreSQL próprio; Twenty CRM;
   Chatwoot; Cal.com; Gateway FastAPI mínimo; PostgreSQL centralizado
   com init-multiple-databases.sh parametrizável. Priorize imagens
   Docker oficiais (Docker Hub/GHCR) — só gere Dockerfile próprio se
   não houver imagem oficial, documentando o motivo.

2. Se o Pacote 6 já estiver aplicado, rode gates/G_INFRA_COMPOSE.py
   contra todo docker-compose.yml novo e corrija até passar. Se ainda
   não estiver aplicado, rode ao menos `docker compose config`
   manualmente em cada um e documente que a validação formal via gate
   fica pendente.

3. Para cada um dos 5 nichos reais em
   tools/aidd-ops/data/catalogo_nichos.json (Pacote 3), crie um
   PLANO-INFRAESTRUTURA.json estático e versionado dentro do bloco de
   template correspondente (ou num diretório próprio por nicho que
   referencie os blocos usados) — listando os bancos lógicos e blocos
   que aquele nicho usa. Este é o artefato ESTÁTICO que
   gates/G_INFRA_COMPOSE.py (Pacote 6) precisa para conferir
   init-multiple-databases.sh contra um plano real, não contra uma
   execução de teste efêmera do usuário.

REGRAS DE ESCOPO — NÃO FAÇA: não hardcode segredo em nenhum
.env.example (só nomes de variável, sem valor); não toque em
tools/aidd-generator/ de forma alguma (a flag --type=infra-stack foi
rejeitada pelo usuário, não implemente); não crie nada em
componentes/templates/ (caminho errado, use
tools/aidd-ops/templates/infra/); não faça git commit/push sem
aprovação.

ENTREGÁVEL: estrutura completa de tools/aidd-ops/templates/infra/, os 5
PLANO-INFRAESTRUTURA.json estáticos por nicho, e evidência real
(output) de docker compose config ou G_INFRA_COMPOSE.py passando para
todo compose novo.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent. Self-contained.

```
You are going to create the canonical infrastructure template catalog
for tools/aidd-ops/, covering Adjustment 3 of "docs/features/PLANO
ARQUITETURAL NOVA FEATURE AIDD-OPS.md §8.3". There is currently NO
templates/ folder in componentes/ — you are creating the first
precedent, not extending an existing pattern.

ALREADY-MADE DECISION (do not reopen): infrastructure templates stay as
static content internal to tools/aidd-ops/templates/infra/<block>/ —
WITHOUT going through components sync (same real pattern as
tools/aidd-master/templates/core|v2, consumed internally by
provision_project.py via shutil.copyfile, never by
gestor_componentes.py). There is NO new flag in aidd-generator in this
package nor in any other — that extension was evaluated and REJECTED
by the user for coupling two tools that must remain standalone. Do not
implement anything in tools/aidd-generator/.

Prerequisite: Package 3 applied (tools/aidd-ops/ exists with `ops plan`
and the niche catalog at tools/aidd-ops/data/catalogo_nichos.json).
Recommended (not blocking): Package 6 applied (G_INFRA_COMPOSE already
exists to validate the composes you will create).

DEFINITION OF DONE:

1. Create the 7 building blocks under
   tools/aidd-ops/templates/infra/<block>/, each with a
   docker-compose.yml + .env.example (no hardcoded sensitive value,
   variable names only) + a short usage README.md: Traefik with TLS
   Let's Encrypt; Authentik SSO with its own PostgreSQL; Twenty CRM;
   Chatwoot; Cal.com; minimal FastAPI Gateway; centralized PostgreSQL
   with a parametrizable init-multiple-databases.sh. Prioritize
   official Docker images (Docker Hub/GHCR) — only generate a custom
   Dockerfile if no official image exists, documenting why.

2. If Package 6 is already applied, run gates/G_INFRA_COMPOSE.py
   against every new docker-compose.yml and fix until it passes. If
   not yet applied, at least run `docker compose config` manually on
   each and document that formal gate validation is pending.

3. For each of the 5 real niches in
   tools/aidd-ops/data/catalogo_nichos.json (Package 3), create a
   static, versioned PLANO-INFRAESTRUTURA.json inside the corresponding
   template block (or its own per-niche directory referencing the
   blocks used) — listing the logical databases and blocks that niche
   uses. This is the STATIC artifact that gates/G_INFRA_COMPOSE.py
   (Package 6) needs to check init-multiple-databases.sh against a real
   plan, not against an ephemeral user test run.

SCOPE RULES — DO NOT: hardcode any secret in any .env.example (variable
names only, no values); touch tools/aidd-generator/ in any way (the
--type=infra-stack flag was rejected by the user, do not implement it);
create anything under componentes/templates/ (wrong path, use
tools/aidd-ops/templates/infra/); `git commit`/`git push` without
approval.

DELIVERABLE: complete tools/aidd-ops/templates/infra/ structure, the 5
per-niche static PLANO-INFRAESTRUTURA.json files, and real evidence
(output) of docker compose config or G_INFRA_COMPOSE.py passing for
every new compose.
```
