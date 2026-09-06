# Pacote 7 — Comando `ops preflight` / Pre-Flight E2E (Gap 4 da proposta)

> **Status:** ⏳ Bloqueado pelos Pacotes 4, 5 e 6 + **aprovação pontual do usuário antes de qualquer execução contra ambiente vivo**.
> **Gap original coberto:** Gap 4 (§8.2 da proposta) — "Bateria de Testes Pré-Produção (Pre-Flight E2E Tests)".
> **Natureza:** diferente dos outros 6 gates — este é um teste de **integração contra infraestrutura viva** (VPS real, DNS real), não estático/offline. Precisa de tratamento e expectativa diferentes dos demais.
> **Nota de nomenclatura (corrigida após auditoria):** este NÃO é um arquivo `gates/G_*.py` (ao contrário do que o nome "G_PRE_FLIGHT_E2E" no título antigo sugeria, e do que o `G_INFRA_COMPOSE.py` do Pacote 6 realmente é) — é um subcomando `ops preflight <ambiente>`, sob demanda, fora da bateria de `cmd_audit`. O nome de arquivo `G_PRE_FLIGHT_E2E` era usado só como codinome interno, o que já causou confusão numa auditoria independente — evite criar por engano um arquivo `gates/G_PRE_FLIGHT_E2E.py`.

---

## Diagnóstico

Os 6 gates atuais e o `G_INFRA_COMPOSE` (Pacote 6) rodam em segundos, sem custo e sem efeito colateral, porque validam só o repositório local. Este comando, como descrito na proposta (curl real em `/healthz`, validação de certificado SSL emitido pelo Traefik, simulação de webhook ponta-a-ponta), **depende de um deploy real já no ar** — não pode rodar como parte do `python ecossistema.py audit` síncrono de todo commit, sob risco de tornar a auditoria lenta, cara (tempo de VPS) e instável (flakiness de rede/DNS).

**Decisão de desenho necessária:** este NÃO deve ser um 8º gate incondicional de `audit` — deve ser um comando separado (`python ecossistema.py ops preflight <ambiente>`), rodado sob demanda após um deploy real, nunca automaticamente a cada commit.

**Correção aplicada após auditoria real (verificação independente):** a barreira de aprovação pontual foi confirmada correta e sem violação — em nenhum ponto o documento autoriza um executor a rodar contra rede externa sem aprovação explícita. O achado real foi outro: o método de teste local proposto (item 4, "mocks de resposta HTTP/DNS/SSL") era vago demais e mais fraco do que o padrão já estabelecido no próprio repositório. Existem 2 precedentes reais e mais rigorosos: `tools/aidd-enterprise/tests/unit/test_oidc_sso.py` (duplicado em `aidd-master`), que sobe um **servidor HTTP local real** (`http.server.HTTPServer` em `127.0.0.1:0`) simulando um provedor OIDC para provar o fluxo de ponta a ponta sem rede externa; e o próprio Pacote 4 (SSH Runner), que exige um **contêiner Docker local real** com servidor SSH, não apenas mocks. Corrigido abaixo para exigir o mesmo nível de rigor.

---

## Definição de Pronto

1. `python ecossistema.py ops preflight <ambiente>` implementado como comando dedicado (não incorporado ao `audit` incondicional), recebendo o alvo real (domínio/IP) já implantado.
2. Validações mínimas:
   - Requisição HTTP real a cada endpoint `/healthz` esperado (por serviço da stack), status 200 obrigatório.
   - Validação do certificado SSL emitido (emissor, validade, cadeia) no domínio de borda.
   - Simulação de 1 webhook de ponta-a-ponta (dispara evento sintético contra o gateway, confirma propagação até o serviço de destino).
   - Resolução DNS confirmada para cada subdomínio esperado do plano de infraestrutura.
3. Timeout e retry explícitos e configuráveis (propagação de DNS/SSL pode levar minutos) — o comando nunca trava indefinidamente nem falha por uma corrida de tempo não documentada.
4. Relatório de saída estruturado (JSON), distinguindo claramente checagem "passou", "falhou" e "não aplicável" (ex.: serviço que não expõe `/healthz`) — nunca um `exit 1` genérico sem indicar qual checagem específica falhou.
5. **Primeira execução real só contra o ambiente de teste decidido no Pacote 1**, nunca direto contra um deploy de cliente real, e só com aprovação pontual do usuário informando o alvo.

---

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai implementar o comando `python ecossistema.py ops preflight
<ambiente>`, cobrindo o Gap 4 identificado em
"docs/features/PLANO ARQUITETURAL NOVA FEATURE AIDD-OPS.md §8.2": bateria
de testes pré-produção contra um deploy JÁ REALIZADO (não é um gate
estático — depende de infraestrutura viva).

Pré-requisito: Pacotes 4, 5 e 6 aplicados.

DEFINIÇÃO DE PRONTO:

1. Implemente como subcomando dedicado (`ops preflight <ambiente>`), NÃO
   como gate incondicional dentro de `cmd_audit` — este teste tem custo
   e depende de rede real, não deve rodar em todo commit.

2. Implemente as 4 checagens: HTTP real em /healthz de cada serviço
   esperado (status 200), validação de certificado SSL (emissor,
   validade), simulação de 1 webhook ponta-a-ponta contra o gateway, e
   resolução DNS de cada subdomínio esperado. Use timeouts e retries
   explícitos e configuráveis via parâmetro (propagação de DNS/SSL pode
   levar minutos — documente isso no --help).

3. Saída em JSON estruturado, com status por checagem (passou/falhou/não
   aplicável) e mensagem específica de causa em caso de falha — nunca um
   exit code sem detalhamento de qual checagem falhou.

4. Escreva testes reais (não mocks superficiais) usando servidores locais
   de verdade, mesmo padrão de rigor já usado em
   tools/aidd-enterprise/tests/unit/test_oidc_sso.py: (a) suba um
   servidor HTTP local real (`http.server.HTTPServer` em `127.0.0.1:0`
   ou equivalente) simulando `/healthz` para os 3 estados (200 OK, erro,
   endpoint ausente/"não aplicável"); (b) suba um servidor TLS local com
   certificado self-signed gerado no próprio teste (via `cryptography`
   ou `openssl` chamado como subprocess) para exercitar de verdade a
   lógica de validação de emissor/validade/cadeia — não simule a
   resposta, valide um certificado real; (c) torne a função de resolução
   DNS testável com um resolver injetável (parâmetro/dependency
   injection), permitindo testar os 3 estados sem rede externa. O texto
   "aguardando o ambiente de teste autorizado" do item 5 não é desculpa
   para testar só com mocks superficiais — o CÓDIGO do comando precisa
   ser provado real antes da aprovação pontual chegar.

5. NÃO rode este comando contra nenhum ambiente real de rede externa
   nesta etapa. O domínio/IP de teste AINDA NÃO FOI DECIDIDO em nenhum
   pacote anterior (o Pacote 1 só decidiu a VPS descartável, não domínio
   nenhum) — não presuma um. Pare e reporte que o comando está pronto,
   aguardando o ambiente de teste autorizado (a ser pedido explicitamente
   no momento da aprovação pontual) para a primeira validação real.

REGRAS DE ESCOPO — NÃO FAÇA: não registre este comando dentro de
cmd_audit (deve permanecer subcomando separado, sob demanda); não execute
contra nenhum domínio/IP real sem esse alvo ter sido explicitamente
autorizado nesta conversa; não faça git commit/push sem aprovação.

ENTREGÁVEL: código do comando, testes com mock, e confirmação explícita
de que nenhuma execução tocou ambiente real de rede externa nesta etapa.
```

---

## Critério de validação

Testes reais (servidor HTTP local, servidor TLS local com certificado self-signed, resolver DNS injetável) 100% passando, cobrindo os 3 estados de cada checagem — não apenas mocks superficiais; primeira execução real (quando aprovada, com domínio/IP explicitamente pedido nesse momento) contra o ambiente de teste retorna relatório JSON coerente, distinguindo cada checagem.

---

## Veredito

*(Preencher após execução — registrar explicitamente se houve execução contra ambiente real, qual ambiente, e o relatório obtido.)*

## Prompt de Execução — English version

```
You are going to implement the `python ecossistema.py ops preflight
<environment>` command, covering Gap 4 identified in
"docs/features/PLANO ARQUITETURAL NOVA FEATURE AIDD-OPS.md §8.2": a
pre-production test battery against an ALREADY-DEPLOYED environment
(this is not a static gate — it depends on live infrastructure).

Prerequisite: Packages 4, 5 and 6 applied.

DEFINITION OF DONE:

1. Implement it as a dedicated subcommand (`ops preflight
   <environment>`), NOT as an unconditional gate inside `cmd_audit` —
   this test has a real cost and depends on live network, it must not
   run on every commit.

2. Implement the 4 checks: real HTTP request to /healthz for each
   expected service (status 200), SSL certificate validation (issuer,
   validity), simulation of 1 end-to-end webhook against the gateway,
   and DNS resolution of each expected subdomain. Use explicit,
   configurable timeouts and retries (DNS/SSL propagation can take
   minutes — document this in --help).

3. Structured JSON output, with a status per check (passed/failed/not
   applicable) and a specific failure-cause message — never an exit
   code with no detail on which check failed.

4. Write real tests (not shallow mocks) using real local servers, same
   rigor already used in
   tools/aidd-enterprise/tests/unit/test_oidc_sso.py: (a) spin up a
   real local HTTP server (`http.server.HTTPServer` on `127.0.0.1:0` or
   equivalent) simulating `/healthz` for the 3 states (200 OK, error,
   missing endpoint/"not applicable"); (b) spin up a local TLS server
   with a self-signed certificate generated in the test itself (via
   `cryptography` or `openssl` called as a subprocess) to really
   exercise the issuer/validity/chain validation logic — do not mock
   the response, validate a real certificate; (c) make the DNS
   resolution function testable with an injectable resolver (parameter/
   dependency injection), allowing the 3 states to be tested without
   external network. Item 5's "pending the authorized test environment"
   is not an excuse to test with shallow mocks only — the command's
   CODE needs to be proven real before the point-in-time approval
   arrives.

5. Do NOT run this command against any real external-network
   environment at this stage. The test domain/IP has NOT been decided
   in any prior package (Package 1 only decided the disposable VPS, no
   domain) — do not assume one. Stop and report that the command is
   ready, pending the authorized test environment (to be explicitly
   requested at the point-in-time approval moment) for the first real
   validation.

SCOPE RULES — DO NOT: register this command inside cmd_audit (it must
remain a separate, on-demand subcommand); execute against any real
domain/IP that has not been explicitly authorized in this conversation;
`git commit`/`git push` without approval.

DELIVERABLE: command code, tests with mocks, and explicit confirmation
that no execution touched a real external-network environment at this
stage.
```
