# Pacote 5 — MCPs de Borda: Cloudflare (DNS) e Docker (Gap 2 da proposta)

> **Status:** ⏳ Bloqueado pelo Pacote 4 + **aprovação pontual do usuário antes do primeiro registro DNS real criado**.
> **Gap original coberto:** Gap 2 (§8.2 da proposta) — "Conectividade de Borda via MCPs (Cloudflare & Docker)".

---

## Diagnóstico (correção ao diagnóstico da proposta original)

A proposta descreve este gap como "o catálogo de componentes atual não possui conectores oficiais para provedores de infraestrutura" — impreciso. Verificado no repositório: a **convenção física de MCP já existe e está em uso real**:
- `componentes/aidd-enterprise/mcps/` — pasta viva no padrão de componentes, hoje vazia.
- `componentes/aidd-generator/mcps/mcp-verificador-cve/server.py` — MCP funcional já em produção no repo (verificador de CVE), prova de que o padrão de implementação de MCP já é conhecido e replicável.

O gap real, mais estreito do que a proposta descreve: **não existe nenhum MCP de infraestrutura (Cloudflare, Docker) ainda** — mas a convenção para criar um já está pronta, reduzindo o esforço deste pacote a "seguir um padrão existente com um domínio novo", não "inventar a convenção".

**Correção aplicada após auditoria real (verificação independente, com execução real de comando):**
- **Achado crítico, comprovado empiricamente:** `python scripts/gestor_componentes.py verify --tipo mcp --ferramenta aidd-ops`, rodado hoje no estado real do repositório, retorna `Componentes verificados: 0` / `[SUCESSO]` — porque o escopo `"aidd-ops"` ainda não existe em `gates/manifesto_harnesses.json["escopos"]` (trabalho do Pacote 2). O filtro por `--ferramenta` que não bate com nenhum escopo produz lista vazia, e tanto `sync` quanto `verify` processam **zero componentes** retornando sucesso — um falso positivo real, não hipotético. Corrigido abaixo: o critério de saída agora exige conferir a CONTAGEM de componentes verificados (`Componentes verificados: 2`), nunca só o exit code.
- **Item 4 corrigido:** `01-decisao-escopo-e-mvp.md` **não** decide nenhum domínio/zona DNS — a única decisão real do Pacote 1 sobre ambiente de teste é a VPS descartável (Pacote 4). O domínio/subdomínio de teste do Cloudflare **ainda não foi decidido** e precisa ser pedido no mesmo momento da aprovação pontual, não presumido como já resolvido.
- **Item 5 corrigido:** não existe no manifesto real nenhum mecanismo de "registrar um MCP individual" — componentes são descobertos automaticamente a partir do conteúdo físico de `componentes/<escopo>/mcps/`. O que precisa existir é o **escopo** `aidd-ops` (com `"mcp"` em `tipos_aplicaveis`), que é responsabilidade do Pacote 2, não deste pacote — este pacote só depende disso, não o cria.

---

## Definição de Pronto

0. **Pré-condição a confirmar antes de qualquer outra coisa:** `gates/manifesto_harnesses.json["escopos"]["aidd-ops"]` já existe (saída do Pacote 2), com `root: "tools/aidd-ops"` e `"mcp"` em `tipos_aplicaveis`. Se não existir, PARE — registrar esse escopo não é trabalho deste pacote.
1. `componentes/aidd-ops/mcps/cloudflare-mcp/` criado seguindo exatamente a estrutura de `componentes/aidd-generator/mcps/mcp-verificador-cve/` (mesmo padrão de `server.py`, mesmo estilo de exposição de tools MCP, mesma escolha de biblioteca padrão apenas — sem `requests`, usar `urllib.request` para as chamadas HTTP reais à API da Cloudflare).
2. `cloudflare-mcp` expõe no mínimo: criação de registro A, criação de registro CNAME, consulta de status de propagação — autenticado via token de API do Cloudflare lido de variável de ambiente (nunca hardcoded; auditado por `gates/G_SEGREDOS.py`).
3. `componentes/aidd-ops/mcps/docker-mcp/` criado no mesmo padrão, expondo no mínimo: `docker compose config` (validação sintática, sem subir nada), status de contêineres, logs — **escopo deste pacote é só leitura/validação**. Operações destrutivas (`down`, `rm`) **não são implementadas neste pacote** — ficam como nota explícita para um pacote futuro que decidir implementá-las, com exigência de confirmação explícita por parâmetro nunca padrão implícito, e teste real (`confirm=False` → erro; `confirm=True` → executa) como parte do critério de saída daquele pacote futuro.
4. Modo de teste: `cloudflare-mcp` validado primeiro contra uma **zona de teste isolada** (subdomínio descartável de um domínio controlado pelo usuário) — o domínio/subdomínio de teste ainda **não foi decidido em nenhum pacote anterior** e precisa ser pedido explicitamente no momento da aprovação pontual (mesmo tratamento dado ao IP da VPS no Pacote 4) — nunca contra um domínio de produção em uso.
5. Ambos os MCPs sincronizados via `python ecossistema.py components sync --tipo mcp --ferramenta aidd-ops`, dependendo do escopo `aidd-ops` já registrado no manifesto pelo Pacote 2 (item 0) — este pacote não registra o escopo, só depende dele.

---

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai criar dois MCPs de borda para tools/aidd-ops/, cobrindo o Gap 2
identificado em "docs/features/PLANO ARQUITETURAL NOVA FEATURE AIDD-OPS.md
§8.2": cloudflare-mcp (gestão de DNS) e docker-mcp (controle de
contêineres). O padrão de MCP JÁ EXISTE no repositório — leia
componentes/aidd-generator/mcps/mcp-verificador-cve/server.py primeiro e
replique o mesmo estilo de implementação, não invente uma convenção nova.

Pré-requisito: Pacote 4 aplicado (SSH Runner já existe).

CONTEXTO JÁ INVESTIGADO (confirme antes de agir): rodei
`python scripts/gestor_componentes.py verify --tipo mcp --ferramenta aidd-ops`
no estado real do repositório e obtive `Componentes verificados: 0` /
`[SUCESSO]` — porque o escopo "aidd-ops" ainda não existe no manifesto.
Isso significa que `components verify` retorna sucesso mesmo com ZERO
componentes processados quando o escopo não bate — não confie em exit 0
sozinho, sempre confira a contagem.

DEFINIÇÃO DE PRONTO:

0. Confirme que gates/manifesto_harnesses.json["escopos"]["aidd-ops"] já
   existe (saída do Pacote 2), com root "tools/aidd-ops" e "mcp" em
   tipos_aplicaveis. Se não existir, PARE e reporte — registrar esse
   escopo é trabalho do Pacote 2, não deste.

1. Crie componentes/aidd-ops/mcps/cloudflare-mcp/server.py expondo tools
   MCP para: criar registro A, criar registro CNAME, consultar status de
   propagação DNS. Use `urllib.request` (biblioteca padrão, mesma
   convenção do MCP de referência) para as chamadas HTTP reais à API da
   Cloudflare — não adicione `requests` como dependência nova. Token de
   API do Cloudflare lido de variável de ambiente (ex: CLOUDFLARE_API_TOKEN)
   — nunca hardcoded. Rode `python gates/G_SEGREDOS.py` ao final e
   confirme exit 0.

2. Crie componentes/aidd-ops/mcps/docker-mcp/server.py expondo tools MCP
   SÓ de leitura/validação: `docker compose config` (validação sintática
   read-only), status de contêineres, logs. NÃO implemente `down`/`rm`
   neste pacote — deixe como nota explícita para um pacote futuro.

3. NÃO rode nenhuma operação de escrita do cloudflare-mcp (criar registro
   real) contra nenhuma zona/domínio real ainda. Escreva testes com
   mocks da API do Cloudflare para validar o parsing de request/response.
   O domínio/subdomínio de teste AINDA NÃO FOI DECIDIDO em nenhum pacote
   anterior — não presuma um. Pare e reporte que o MCP está pronto para
   validação com uma zona de teste real, aguardando o domínio/subdomínio
   autorizado (a ser pedido explicitamente, mesmo tratamento do IP da
   VPS no Pacote 4).

4. Rode `python ecossistema.py components sync --tipo mcp --ferramenta aidd-ops`
   seguido de `components verify --tipo mcp --ferramenta aidd-ops` — NÃO
   é suficiente confirmar exit 0: confira explicitamente que a saída
   mostra "Componentes verificados: 2" (os dois MCPs novos). Se mostrar
   0, algo está errado com o escopo (item 0) — não declare sucesso.

REGRAS DE ESCOPO — NÃO FAÇA: não crie nenhum registro DNS real sem receber
explicitamente o domínio/subdomínio de teste autorizado nesta conversa;
não implemente `down`/`rm` no docker-mcp neste pacote; não hardcode
token de API; não adicione `requests` como dependência nova; não faça
git commit/push sem aprovação.

ENTREGÁVEL: código dos dois MCPs, testes com mock da API Cloudflare,
resultado de gates/G_SEGREDOS.py, saída completa de `components verify`
(com a contagem "2" explícita, não só o exit code), e confirmação
explícita de que nenhum registro DNS real foi criado nesta etapa.
```

---

## Critério de validação

`gates/G_SEGREDOS.py` exit 0; `python ecossistema.py components verify --tipo mcp --ferramenta aidd-ops` exit 0 **E** relatando "Componentes verificados: 2" explicitamente (exit 0 sozinho não é suficiente — pode ocorrer com 0 componentes processados se o escopo `aidd-ops` não estiver registrado); testes com mock cobrindo criação de registro A/CNAME e validação de compose (`pytest <caminho real>` com exit 0 explícito); `git status` limpo além dos arquivos esperados; primeiro registro DNS real (se e quando aprovado) criado só em zona de teste isolada, nunca em produção.

---

## Veredito

*(Preencher após execução — registrar se houve ou não criação de registro DNS real, contra qual zona, sob qual aprovação.)*

## Prompt de Execução — English version

```
You are going to create two edge MCPs for tools/aidd-ops/, covering Gap
2 identified in "docs/features/PLANO ARQUITETURAL NOVA FEATURE
AIDD-OPS.md §8.2": cloudflare-mcp (DNS management) and docker-mcp
(container control). The MCP convention ALREADY EXISTS in the repo —
read componentes/aidd-generator/mcps/mcp-verificador-cve/server.py
first and replicate the same implementation style, do not invent a new
convention.

Prerequisite: Package 4 applied (SSH Runner already exists).

ALREADY-INVESTIGATED CONTEXT (confirm before acting): running
`python scripts/gestor_componentes.py verify --tipo mcp --ferramenta aidd-ops`
against the real current repo state returns `Componentes verificados: 0`
/ `[SUCESSO]` — because the "aidd-ops" scope does not exist yet in the
manifest. This means `components verify` returns success even with ZERO
components processed when the scope does not match — never trust exit 0
alone, always check the count.

DEFINITION OF DONE:

0. Confirm that gates/manifesto_harnesses.json["escopos"]["aidd-ops"]
   already exists (output of Package 2), with root "tools/aidd-ops" and
   "mcp" in tipos_aplicaveis. If it does not exist, STOP and report —
   registering that scope is Package 2's job, not this one's.

1. Create componentes/aidd-ops/mcps/cloudflare-mcp/server.py exposing
   MCP tools for: creating an A record, creating a CNAME record,
   querying DNS propagation status. Use `urllib.request` (standard
   library, same convention as the reference MCP) for the real HTTP
   calls to the Cloudflare API — do not add `requests` as a new
   dependency. Cloudflare API token read from an environment variable
   (e.g. CLOUDFLARE_API_TOKEN) — never hardcoded. Run
   `python gates/G_SEGREDOS.py` at the end and confirm exit 0.

2. Create componentes/aidd-ops/mcps/docker-mcp/server.py exposing
   READ-ONLY MCP tools: `docker compose config` (read-only syntax
   validation), container status, logs. Do NOT implement `down`/`rm` in
   this package — leave it as an explicit note for a future package.

3. Do NOT run any write operation of cloudflare-mcp (creating a real
   record) against any real zone/domain yet. Write tests with mocks of
   the Cloudflare API to validate request/response parsing. The test
   domain/subdomain has NOT been decided in any prior package — do not
   assume one. Stop and report that the MCP is ready for validation
   against a real test zone, pending the authorized domain/subdomain
   (to be explicitly requested, same treatment as the VPS IP in
   Package 4).

4. Run `python ecossistema.py components sync --tipo mcp --ferramenta aidd-ops`
   followed by `components verify --tipo mcp --ferramenta aidd-ops` —
   exit 0 alone is NOT sufficient: explicitly confirm the output shows
   "Componentes verificados: 2" (the two new MCPs). If it shows 0,
   something is wrong with the scope (item 0) — do not declare success.

SCOPE RULES — DO NOT: create any real DNS record without an explicitly
given test domain/subdomain authorized in this conversation; implement
`down`/`rm` in docker-mcp in this package; hardcode any API token; add
`requests` as a new dependency; `git commit`/`git push` without
approval.

DELIVERABLE: code of both MCPs, tests with a mocked Cloudflare API, the
result of gates/G_SEGREDOS.py, the full output of `components verify`
(with the "2" count explicit, not just the exit code), and explicit
confirmation that no real DNS record was created at this stage.
```
