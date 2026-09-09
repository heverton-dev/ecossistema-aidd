# AUDITORIA: SEGURANÇA EM PROFUNDIDADE, ZERO-TRUST E SUPPLY CHAIN

> **Data:** 2026-09-09
> **Status:** ✅ PLANO FORMALIZADO — `docs/planos/a-fazer/05-seguranca-zero-trust-e-supply-chain/`
> **Tags:** #plano-gerado #seguranca #zero-trust #supply-chain #appsec #mcp
> **Escopo:** Análise profunda de superfície de ataque, integridade de supply chain, sandbox de execução LLM, RCE e conformidade Zero-Trust no Ecossistema AIDD.
> **Método:** leitura direta de `security.py`, `mcp_server.py`, `sincronizador_harness.py`, `subagent_engine.py`, `08_implementador.py`, `G_SEGURANCA.py`, `G_CYBERSECURITY_OWASP.py`, manifests de dependência; varredura por padrões de execução/env/sandbox.

──────

## 1. Threat Model & Attack Surface Map (STRIDE)

| Fronteira | Ameaça dominante | Vetor concreto | Estado atual |
|:--|:--|:--|:--|
| **Web (Fase 1) → LLM → código gerado → execução na máquina do dev** | **E (Elevation/Repudiation→RCE)** | Referência maliciosa envenena a análise; Fase 8 gera código; gate I4 **executa** `main.py` do projeto gerado; pytest importa e roda o código — **sem sandbox algum** | 🔴 crítico: execução nativa com env completo do host |
| **Delegado/headless LLM → harness com credenciais** | S/E | `utils_delegacao` herda `os.environ` integral (`{**os.environ}` no env do pytest) — chaves de API visíveis a código gerado | 🔴 alto |
| **MCP tools → banco da suíte** | I/E | `sistema_executar_consulta` executa SELECT em tabela com ident sanitizado — bem feito; mas `register_injected_tools` carrega **código arbitrário de `src/core/mcp/*.py` sem verificação de integridade** | 🟡 médio-alto |
| **Componentes injetados (enterprise)** | T (Tampering) | Hashes SHA-256 gravados **no mesmo arquivo** (CAPABILITIES.json) que descreve os arquivos — atacante com write access re-hash e sobrescreve | 🟡 médio (integridade ≠ autenticidade) |
| **JWT/RBAC do runtime gerado** | S (Spoofing) | Segredo default hardcoded para dev; alg fixo HS256 (bom — sem confusão de alg), mas sem `aud`/`iss` e sem rotação | 🟡 médio |
| **RLS app-layer (SQLite) / PG policy** | I (Info disclosure) | `SET app.current_tenant_id = '{tenant_id}'` interpolação direta no PostgreSQL (`database.py:390`) | 🔴 alto no fluxo PG |
| **Supply chain pip/npm** | T (Tampering) | `>=` sem pin exato, sem `--require-hashes`, sem lockfile; skills instaladas via `npx` sem checksum | 🔴 alto |
| **Gates de segurança como controle** | Repudiation/confiança falsa | Regex-scan + probes comportamentais bons, mas cegos para vetores inteiros (ver §5) | 🟡 médio |

**Superfície mais quente:** o pipeline do generator é um **compilador de confiança** — entrada da web não confiável vira código que roda com os privilégios do usuário. Todo o resto é secundário frente a isso.

## 2. Detailed Vulnerability Findings

### 2.1 Execução de código LLM sem sandbox (Fase 8 / generator)

- **[SEC-1] 🔴 CRÍTICO — Sem isolamento de processo em nenhum nível.** `_rodar_pytest` (`08_implementador.py:1491`) e `_gate_i4_cli_executa` (`:512`) executam código gerado por LLM com `subprocess.run([sys.executable, ...])` herdando **`{**os.environ}` explicitamente** (`:1488`), cwd no projeto, sem container/jail/seccomp/Job Object/prlimit/`resource` — confirmado por busca: nenhum mecanismo de isolamento em `scripts/phases/`. Cenário: referência da Fase 1 (GitHub/HF/Replit — fontes não confiáveis) envenena a análise → Fase 8 emite `main.py` com `os.system(curl … | sh)` → gate I4 executa `--help`... que já rodou o payload no import. **O `--help` do Python executa o código de nível de módulo** — o "smoke-test inofensivo" é, na verdade, execução plena.
- **[SEC-2] 🔴 Credenciais do host expostas ao código gerado:** env integral herdado inclui `LLM_MODEL` keys, `JWT_SECRET_KEY`, `SSH_KEY_PATH`, tokens do `.env` carregado por `utils_delegacao.py:88-95` (dotenv da tool inteira). Nenhuma lista de permissão/deny-list de env vars.
- **[SEC-3] 🟡 Prompt-injection sem defesa em profundidade:** gates R1-R4 (Fase 1) e E3/I1-I5 validam **estrutura**, não intenção. Um design que instrui "apague arquivos em cleanup" passa por todos os gates. Não há análise de chamadas perigosas no código gerado (nem o `G_CYBERSECURITY_OWASP` roda sobre o output da Fase 8 — ele roda no repositório do ecossistema, não no projeto gerado).

### 2.2 Supply chain & integridade de dependências

- **[SEC-4] 🔴 Nenhum pin exato nem hash em pip:** `requirements.txt` (raiz) e de todas as tools usam `>=` solto (`pytest>=7.4.0`, `litellm>=1.20.0`, `mcp>=1.0`...). Sem `--require-hashes`, sem lockfile (`uv.lock`/`pip-tools`). Resolver de pip pode puxar versão nova comprometida a qualquer build. `requirements-dev.txt` herda (`-r requirements.txt`).
- **[SEC-5] 🟡 npm com versão exata mas sem integrity registry:** `.mimocode/package.json` fixa `@mimo-ai/plugin 0.1.14` (sem lockfile commitado? `package-lock.json` existe no diretório) e skills instaladas via `npx impeccable install` **sem checksum** — o install baixa código da registry a cada bootstrap. `gates/dependencias_externas.json` registra o *comando* de install e o caminho de verificação, mas não hash do artefato.
- **[SEC-6] 🟡 Dependency confusion:** nomes de pacotes internos não reservados em registry público; scripts de install confiam no nome (`pacote: "impeccable"`). Typosquatting em `npx` skills segue o mesmo padrão — nenhuma lista de permissão assinada.
- **[SEC-7] 🟢 Ponto positivo:** `G_HADOLINT`/`G_INFRA_COMPOSE` (Checkov) auditam imagens/compose — única parte da supply chain com scanner real.

### 2.3 Zero-Trust no AIDD Enterprise — realidade da verificação

- **[SEC-8] 🔴 SHA-256 não é tamper-proof: hash e dado no mesmo lugar.** `sincronizador_harness.py:40-77` grava `arquivos_hashes` em `CAPABILITIES.json` — o mesmo arquivo JSON que um atacante (ou um agente comprometido) pode reescrever junto com o conteúdo: recomputa sha256 dos arquivos alterados e cola no registry. `verificar_sincronizacao` (`:90-115`) compara contra **o próprio registry mutável**. Isso é **detecção de drift acidental** (corrupção, sync esquecido — valor real), **não** resistência a adulteração deliberada. Sem assinatura digital, sem chave externa, sem log de somente-anexo. O rótulo "Zero-Trust com validação SHA-256" (AGENTS.md §1) supera o que o mecanismo entrega — violação direta da Regra de Ouro #9.
- **[SEC-9] 🟡 `register_injected_tools` executa código de `src/core/mcp/*.py` sem verificação:** `mcp_server.py:81-120` faz `importlib` de todo `.py` no diretório e registra `TOOL_DEF`/`handler`. O materializador escreve lá (`materializador.py` gera `mcp` em `src/core/mcp/`) — o elo "hash verifica o componente" **não é consultado** no load: a verificação existe (CAPABILITIES) mas não está ligada ao caminho de execução.
- **[SEC-10] 🔴 Interpolação SQL na policy PG:** `database.py:390` — `SET app.current_tenant_id = '{tenant_id}'` com f-string. `tenant_id` vem do contexto de aplicação; se qualquer caminho de código propagar input do usuário até `set_tenant`, é injeção SQL/quebra de isolamento no Postgres (caminho SQLite usa thread-local — seguro). Correção: `SET app.current_tenant_id = %s` via parametrização ou validação UUID estrita antes.
- **[SEC-11] 🟡 JWT: base boa com dois furos:** `security.py` — alg fixo HS256 e `compare_digest` (não vulnerável a confusão de alg/timing — bom). Furos: (1) **segredo default hardcoded** `DEV_ONLY_INSECURE_SECRET_CHANGE_BEFORE_DEPLOY` (`:12-13`) usado se env ausente — em produção esquecida, é forjável; (2) sem validação `iss`/`aud`, sem `nbf`, sem revogação (existe `token_revocation.py`, mas não está ligado ao decode — verificar ligação no deploy real). (3) `exp` checado apenas se presente — token sem `exp` vive para sempre.
- **[SEC-12] 🟢 Webhooks HMAC correto:** `webhooks.py:62,103-114` assina com `hmac.compare_digest` e headers duplos (`X-Webhook-Signature`/`X-Hub-Signature-256`).
- **[SEC-13] 🟡 RLS app-layer (SQLite):** `RLSConnection` reescreve queries por AST — sólido como conceito, mas: `executescript` passa **sem rewrite** (`database.py:372-373`) — DDL/scripts criados por módulo não são filtrados (risco baixo: DDL raramente por tenant, mas é buraco formal); e o registry `RLS_TABLE_REGISTRY` é global-mutável em runtime — qualquer módulo esquecido de `enable_rls_tenant` fica sem proteção **silenciosamente** (fail-open).

### 2.4 MCP Server — fronteira de privilégio

- **[SEC-14] 🟡 Sanitização de ident existe e é boa:** `_sanitize_ident` (`mcp_server.py:20-26`) permite `[a-zA-Z0-9_]` — mata traversal/SQLi por nome de tabela em `sistema_executar_consulta` (`:223-238`, SELECT com placeholder no LIMIT — correto). **Sem exposição de caminho de arquivo em tools** — a preocupação de `../../etc/passwd` não se materializa nas tools atuais (nada recebe path).
- **[SEC-15] 🟡 Mas `limite` sem cap:** `int(args.get("limite", 50))` sem teto — `limite=10^9` = DoS de memória no host da suíte. Baixo custo de correção.
- **[SEC-16] 🔴 Herança de env nos subprocessos do engine:** `subagent_engine.spawn` (`subagent_engine.py:479-487`) roda worker com env do pai completo (incluindo secrets do `.env`); `ecossistema.py` roteia tools com env herdado + `PYTHONPATH`. Padrão do repo: nenhum subprocesso sanitiza env — combinado com SEC-1/2, qualquer código executado pelo pipeline vê tudo.

## 3. Zero-Trust Hardening Blueprint (especificações canônicas)

### 3.1 Sandbox hermético para execução de código gerado
```
Nível 1 (cross-platform, já viável hoje):
  subprocess com env mínimo: {PATH, PYTHONPATH=projeto/src, PYTHONUTF8, TMPDIR=tempdir próprio}
  + cwd = tempdir do projeto; sem rede: bloqueio por wrapper (socket patch via sitecustomize
    no subprocess) OU --isolate flag; timeout duro (já existe) + memory cap (resource.setrlimit /
    Job Object no Windows — o repo roda em Windows: prioridade).
Nível 2 (Linux/CI): container efêmero (docker run --network none --read-only --cap-drop ALL
    --memory 512m --pids-limit 64 -v projeto:/w:ro), imagem slim pré-pullada.
Nível 3 (produção máxima): gVisor/Kata ou VM efêmera.
Gate novo G_SANDBOX: AST recusa subprocess.run sem env= explícito em scripts do engine.
```
- Pré-requisito: **classificar outputs por confiança** — código da Fase 8 nunca roda no nível de confiança do próprio engine.

### 3.2 Manifest de componentes ASSINADO (fechar SEC-8/9)
```
1. Par de chaves Ed25519 do ecossistema; chave pública versionada NO REPO (fonte separada do dado).
2. No materializar: manifest.json assinado (sig sobre o JSON canônico: arquivos+hashes+timestamp).
3. No register_injected_tools (SEC-9): só carrega .py de src/core/mcp/ se a assinatura do manifest
   vigente bate (ed25519.verify) — verificação ligada ao caminho de execução, não paralela a ele.
4. Registry atualiza-se apenas via operação assinada; gate falha se hash ≠ assinatura vigente.
5. Migração: manter drift-detection atual como camada 1; assinatura como camada 2.
```

### 3.3 Wrapper defensivo de MCP
- Cap em `limite` (ex.: 500) + validação int positiva.
- Env de MCP servers lançados pelo harness: deny-list de segredos (`JWT_SECRET_KEY`, `*_API_KEY`, `SSH_KEY_PATH`) no launcher (o `.mcp.json` já existe como ponto de injeção — incluir `env` mínimo lá).
- `executescript` do RLS: ou bloquear em conexão RLS (fail-closed), ou exigir regeneração de registry após script (fechar [SEC-13]).
- `set_tenant` PG: parametrizar ou validar UUID com regex estrita (fechar [SEC-10]).

### 3.4 Supply chain pinned
- `requirements.txt` → versões exatas `==` geradas por `pip-compile` (ou `uv lock`), com hashes (`--generate-hashes`) e install por `--require-hashes` no CI/pre-commit.
- Skills/MCPs externos: registrar sha256 do artefato instalado em `dependencias_externas.json` e verificar no `dependencia verify` (o comando já existe — falta o hash no contrato).

## 4. Security Gate Reality Check (anti-marketing)

- **`G_SEGURANCA` (master/enterprise, 502 linhas) — melhor que regex puro, com buracos reais:** tem camadas comportamentais de verdade (XSS com payload `<script>` contra HTML gerado `:107-128`, SQL injection com payload contra o motor real `:213+`, JWT forjado testado `:135-140`, anti-backdoor `:169`). Blind spots: (a) regex de SQLi só pega padrões de concatenação em `execute(f"...")` — não pega SQL montado em variável intermediária nem `_rewrite_*` do RLS quebrado; (b) **não roda contra o código gerado pela Fase 8** (roda no repo do ecossistema); (c) é o gate cujo rótulo "blindagem militar" já está rastreado como violação da Regra #9 (pendência `07-corrigir-gate-de-seguranca...`).
- **`G_CYBERSECURITY_OWASP` (forge, 111 linhas) — regex-scan honesto sobre o que é:** docstring declara exatamente o que é ("varredura estática… padrões de alto risco") com severidades alta/média e `EXCLUDED_DIRS` auto-excluindo `gates/` (o próprio gate se declararia). Buracos estruturais do regex-scan (herdados de qualquer abordagem assim): sem dataflow (não distingue `eval` de config interna vs input externo), sem análise de `getattr`/`importlib` dinâmico (que o ecossistema **usa** em 3 pontos: mcp_server, pipeline de fases, subagent worker), não pega command injection via `subprocess.run(list)` com elementos montados de input.
- **[SEC-17] Falha de cobertura declarada:** nenhum gate de segurança roda sobre `output/` do generator — o produto final (código entregue ao usuário) é o único artefato sem varredura. O `verificar_gates.py` do generator existe mas não inclui os gates de segurança do ecossistema.

## 5. Actionable Roadmap (priorizado)

| # | Pri | Ação | Fecha | Critério de pronto |
|:--|:--:|:--|:--|:--|
| 1 | **P0** | Sandbox Nível 1: env mínimo (allowlist) + cwd tempdir + cap de memória/Job Object no Windows em TODOS os subprocessos que executam código gerado (Fase 8 pytest, I4, subagent_engine) | [SEC-1/2/16] | Teste: código gerado com `os.environ` dumping não vê `JWT_SECRET_KEY`/API keys; gate AST proíbe subprocess sem env= explícito |
| 2 | **P0** | `G_CYBERSECURITY_OWASP` (ou subconjunto ALTA) rodando sobre o output da Fase 8 antes do gate I4 | [SEC-3/17] | Pipeline com payload `os.system` no código gerado é bloqueado na Fase 8, com o achado no index da fase |
| 3 | **P0** | Corrigir interpolação em `set_tenant` PG (parametrizada ou UUID regex estrito) | [SEC-10] | Teste com `tenant_id = "x'; DROP TABLE"` rejeitado; policy PG criada só com UUID válido |
| 4 | **P1** | Pin exato + hashes: migrar requirements para lockfile com `--generate-hashes` (pip-compile/uv), install com `--require-hashes` | [SEC-4] | CI instala só por lockfile; gate falha com requirements sem pin |
| 5 | **P1** | Manifest assinado Ed25519 para componentes + verificação ligada ao `register_injected_tools` | [SEC-8/9] | Componente alterado sem re-assinatura não carrega; chave pública versionada no repo separada do registry |
| 6 | **P1** | JWT: proibir segredo default em modo não-dev (fail-fast), exigir `exp`, ligar revogação ao decode | [SEC-11] | Boot sem JWT_SECRET_KEY em modo prod falha com erro claro; token sem exp rejeitado |
| 7 | **P1** | Hash de artefatos de skills/MCPs externos em `dependencias_externas.json` + verificação no `dependencia verify` | [SEC-5/6] | Modificação do artefato pós-install é detectada pelo verify |
| 8 | **P2** | MCP: cap no `limite`; env deny-list de segredos no launcher de MCP; `executescript` fail-closed em conexão RLS | [SEC-13/15] | Testes por item |
| 9 | **P2** | RLS fail-closed: módulo sem `enable_rls_tenant` explicitamente registrado gera warning estruturado no boot (lista esperada por config) | [SEC-13] | Boot reporta tabelas não-protegidas; gate compara contra lista esperada |
| 10 | **P3** | Sandbox Nível 2 (container `--network none`) como modo opcional do pipeline (--isolate), imagem pré-pullada | [SEC-1] | Execução em container validada em Linux/CI; fallback Nível 1 documentado |

**Sequência:** 1-3 são executáveis nesta semana e fecham os vetores de RCE/injeção reais; 4-5 fecham a supply chain e dão ao "Zero-Trust" um mecanismo à altura do rótulo; 6-9 endurecem o runtime gerado; 10 é profundidade extra.
