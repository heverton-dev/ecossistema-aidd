# AUDITORIA: QUALIDADE DE TESTES, MUTAÇÃO E DETERMINISMO

> **Data:** 2026-09-09
> **Status:** ✅ PLANO FORMALIZADO — `docs/planos/a-fazer/03-qualidade-testes-e-mutacao/`
> **Tags:** #plano-gerado #qualidade-testes #teste-mutacao #anti-flakiness #gates
> **Escopo:** Análise profunda da eficácia real dos testes unitários e de integração, detecção de falsos positivos, asserções vazias e resiliência a mutações.
> **Método:** varredura por padrões em `tools/*/tests/` (102 ocorrências de asserts fracos, 20+ `time.sleep`, 42 arquivos com mock), leitura de suítes-chave (outbox, sizing, injector, CQRS), análise de `gates/G_TESTES_REAIS.py` e `pytest.ini` de cada tool.

──────

## 1. Test Quality Scorecard

| Tool | Confiabilidade | Resistência a mutação | Saúde de mocks | Síntese |
|:---|:---:|:---:|:---:|:---|
| aidd-master | 🟡 3/5 | 🔴 2/5 | 🟡 3/5 | Suíte ampla com side-effects bons (outbox/CRUD via HTTP), mas sleeps reais e cobertura fraca de regras financeiras/de segurança |
| aidd-enterprise | 🟡 3/5 | 🔴 2/5 | 🟡 3/5 | Espelho do master (por design); fan-out de hashes testado por contagem, não por conteúdo |
| aidd-generator | 🟡 3/5 | 🔴 1/5 | 🔴 2/5 | **O núcleo de valor (fases LLM) é o menos testável**: gates R/E/I testados, mas pipeline de fases sem teste de resumo; 65 refs de mock só no `test_utils_delegacao` |
| aidd-forge | 🟢 4/5 | 🟡 3/5 | 🟢 4/5 | Teste de integração full-pipeline real + injeção de falha em `os.replace` (G_INJECT) — melhor suíte do repo |
| aidd-ops | 🟢 4/5 | 🟡 3/5 | 🟢 4/5 | Contratos de Result testados, caso corrompido testado (`test_gate_saida_corrompida`), mas math de sizing só tem asserts de piso (`>= 2`), não de exatidão |
| gates/ (raiz) | 🟢 4/5 | 🟡 3/5 | 🟢 4/5 | Gates com testes próprios; G_TESTES_REAIS ignora `skipped > 0` (detalhe em 4.1) |

**Achado estrutural nº1:** a maioria dos pontos críticos de negócio do ecossistema (verificação SHA-256, sizing financeiro, WAL/PRAGMAs, outbox claim) têm **cobertura de linha razoável mas quase zero resistência a mutação** — os testes verificam que o código *roda*, não que as regras *estão certas*.

---

## 2. Detailed Test Smells Catalog

### 2.1 Asserções tautológicas / fracas (amostras concretas)

- **[TS-1] Asserts de não-nulo em cadeia:** 102 ocorrências de `assert X is not None` / `assert result` em `tools/*/tests`. Padrão dominante em `test_cli_commands.py` (master+enterprise) e `test_fuzzing.py`. Um assert de não-nulo aprova qualquer retorno, inclusive mensagens de erro — é teste de fumaça vestido de unitário.
- **[TS-2] Contagem no lugar de conteúdo (enterprise injector):** `test_aidd_core_injector.py:252` — `assert len(dados["skill"][0]["arquivos_hashes"]) == 5`. Testa que **5 hashes existem**, não que os hashes **correspondem ao conteúdo** escrito. Mutar a função de hash (ex.: sha256→sha1, ou hash do nome em vez do conteúdo) mantém o teste verde. Mutante de segurança crítico sobrevivente.
- **[TS-3] Asserts de piso onde a regra é exata (ops sizing):** `test_pipeline_ops.py:95-96` — `assert f3["vps"]["vcpu"] >= 2`, `ram_gb >= 4`. A regra de negócio é `math.ceil(soma dos requisitos)` (determinística, `03_sizing.py`); o teste aceita **qualquer** valor acima do piso. Mutante `ceil→floor+1` ou requisitos dobrados no JSON de catálogo sobrevivem. O arquivo correto de ouro (soma exata por nicho) não existe.
- **[TS-4] Gate de segurança textual (falso verde):** `tools/aidd-generator/tests/test_gate_cybersecurity_owasp.py` testa o gate que procura credenciais por regex em texto — mutantes que mudam o regex (ex.: só detectar `password` e não `senha`) sobrevivem porque o teste usa fixtures que o próprio regex-alvo reconhece. Nenhum teste com credencial real-forma que o regex mutado deve pegar e o falso-negativo deve falhar.
- **[TS-5] Asserção de dado mockado (oracle reinfectado):** em `test_utils_delegacao.py` (65 menções a mock/monkeypatch), vários testes afirmam o retorno do mock (`assert resultado == fake_resposta`) — testam a *colagem*, não a lógica. Ok para bordas de I/O; perigoso onde há transformação real no meio (ex.: `extrair_json_resposta`).

### 2.2 Mocking excessivo / caminhos reais não exercitados

- **[TS-6] `test_outbox_worker.py` (master) — falso contraste:** a suíte simula crash "antes do emit" (`test_process_pending_recovers_event_never_emitted_in_memory`) — bom — mas **nenhum teste simula o caso inverso real** (crash após emit, antes do mark → redespacho; nem listener que falha → hoje vira loop infinito de `pendente`, como documentado no relatório de resiliência). A suíte dá a impressão de que o Outbox está validado contra interrupção; o mutante "inverter ordem emit/mark" e o mutante "engolir exceção do listener" **sobrevivem**. Cobertura 100%, mutação 0%.
- **[TS-7] Fuzzing sem execução real:** `test_fuzzing.py:133-134` apenas afirma que o atributo `base_url` é o que foi passado. A classe `ContinuousAPIFuzzer` nunca fuzzinga nada nos testes — o nome da suíte promete comportamento que não é exercitado.
- **[TS-8] `test_database_adapter_poliglota.py:147-169`:** testes de factory PostgreSQL só validam a classe criada/erro lançado — nenhum contra um Postgres real (nem via testcontainers); mutante que quebra o DSN parsing sobrevive parcialmente (só o erro de `mysql://` é pegos).

### 2.3 Flakiness & dependências de tempo/ambiente

- **[TS-9] `time.sleep` como sincronização (20+ ocorrências):** `test_add_module_server_wiring.py:54` (master+enterprise, integração com servidor real), `test_compose_suite.py:164/193` (`sleep(0.5)` antes de `urlopen http://127.0.0.1:3000/...`), `test_cqrs_local_first.py:33/41` (`sleep(0.1/0.2)` para o stale-while-revalidate), `test_database_adapter.py:301` e `test_events_driver.py:125/137` (`sleep(1)`). Todos são corridas contra relógio: máquina lenta → falso vermelho; máquina rápida demais → corrida mascarada. Os de CQRS são os piores: validam timing de expiração de TTL **dormindo** em vez de injetar relógio.
- **[TS-10] Porta fixa 3000 em integração:** `test_add_module_server_wiring.py:100/103` e `test_compose_suite.py:159` sobem servidor real em `127.0.0.1:3000` — colide com qualquer serviço dev rodando na porta (CI e máquina do dev). O padrão correto já existe no próprio repo: `s.bind(("127.0.0.1", 0))` para porta efêmera (`test_database_adapter.py:269`, `test_oidc_sso.py:141`).
- **[TS-11] `RedisStreamsDriver("redis://localhost:6399/0")` (`test_events_driver.py:68`):** se o teste conectar de verdade quando algo escuta na 6399, fica verde por acaso; se não, depende de fallback implícito. Dependência ambiental não declarada.
- **[TS-12] Estado de SQLite entre testes:** bom em geral (`tmp_path` idiomático em `test_modulo1.py:36,167`), mas `test_cli_commands.py` referencia `sqlite:///app` — risco de criar/ler `app.db` no cwd se o monkeypatch de env falhar silenciosamente (state bleed entre suítes rodando no mesmo diretório).
- **[TS-13] Deprecation warnings silenciados globalmente:** `pytest.ini` da raiz tem `filterwarnings = ignore::DeprecationWarning` — mascara mudanças de API de dependências até que virem quebras reais. Sem `-W error` para categorias escolhidas.

### 2.4 Resumo dos mutantes críticos hipotéticos sobreviventes

| Mutante | Arquivo-alvo | Sobrevive porque |
|:--|:--|:--|
| sha256 → sha1 / hash do nome | injector enterprise (SHA-256 zero-trust) | [TS-2] contagem != conteúdo |
| `ceil` → `floor+1`, ou requisitos ×2 | `03_sizing.py` (ops) | [TS-3] só assert de piso |
| WAL/PRAGMA removidos do listener | `database.py:96-99` | nenhum teste afirma `PRAGMA journal_mode` da conexão resultante |
| ordem emit ↔ mark invertida | `outbox_worker.py` | [TS-6] caso de crash pós-emit não testado |
| tenant filter omitido no SELECT rewrite | `RLSConnection._rewrite_select` | filtros RLS não têm teste com 2 tenants e vazamento cruzado afirmado (verificação necessária — nenhum achado na varredura) |
| regex de credenciais enfraquecido | gates de segredos | [TS-4] fixtures cumplicientes |
| `math.ceil` de arredondamento p/ cima removido no vCPU | ops sizing | idem TS-3 |

---

## 3. Integration Gate Effectiveness (`G_TESTES_REAIS.py` + runners)

### 3.1 O que o gate faz bem
- Executa pytest **de verdade** por tool (não estrutura), timeout de 300s por suíte, falha binária exit 1 em `failed > 0` — alinhado à Qualidade Binária.
- Detecta suíte vazia explicitamente (`SEM TESTES (0 resultados)`) e `no tests ran`.
- TIMEOUT e ERRO de execução contam como falha (`G_TESTES_REAIS.py:96-103`) — não há como sumir com suíte quebrada sem sinal.

### 3.2 Buracos
- **[GE-1] `skipped > 0` não falha nem avisa:** o gate conta skipped e apenas o imprime (`G_TESTES_REAIS.py:108-112`). Uma suíte pode ter 200 skips sistemáticos (ex.: dependência de Redis/postgres ausente no CI) e o gate fica verde para sempre — "verde com asterisco". Para rótulo honesto (Regra #9): skip deveria ser orçado (limite N% ou lista nominal permitida) e excedido = falha.
- **[GE-2] Parsing por regex do output `-q`:** frágil a mudanças de formato do pytest (e de plugins que imprimem no stdout). O `--junitxml` num arquivo temporário daria contagens estruturadas (e permitiria rastrear skipped *por teste*).
- **[GE-3] Timeout global de 300s por tool sem testes marcados como lentos:** uma suíte que cresce (ex.: integração com servidor + sleeps) começa a tomar timeout esporádico em máquinas lentas — flaky de gate, não de teste. Marcadores `@pytest.mark.slow` + execução separada resolveriam com visibilidade.
- **[GE-4] Nenhum gate mede coisa além de passed/failed/skipped:** sem tracking de duração (regressão de velocidade invisível) e sem mutação (área 2 toda). O `G_TESTES_REAIS` é necessário mas não suficiente para "testes que provam regras".
- **[GE-5] `filterwarnings = ignore::DeprecationWarning` na raiz** (pytest.ini) — a política de warnings está em conflito com a detecção de falhas silenciosas: warnings viram ruído ignorado por padrão.

---

## 4. Target Testing Standards (padrões + testes de contrato)

### 4.1 Regras de asserção (para suítes internas e geradas)
1. **Proibido assert órfão de não-nulo como única asserção** de um comportamento — toda função testada precisa de ≥1 asserção de estado/efeito (retorno com valor esperado exato OU side-effect verificável em DB/arquivo).
2. **Regras exatas recebem asserts exatos:** sizing (soma+ceil), hash (conteúdo conhecido → hash conhecido), paginação (N+1). Fixtures de ouro com valores pré-computados.
3. **Hash testing:** teste de injector deve escrever conteúdo A, computar sha256(A) localmente e afirmar igualdade com o registro — invalida mutantes de algoritmo e de entrada.
4. **Mock policy:** mocks permitidos só nas bordas de I/O externo (rede, filesystem do host, relógio); lógica interna sempre real. Teste que afirma retorno de mock sem transformação real = smell [TS-5].
5. **Tempo:** proibido `time.sleep` para sincronização — ou polling com deadline (`assert_eventually(fn, timeout=5)` utilitário compartilhado) ou injeção de relógio (o `ReadModelCache` já aceitaria ttl fake — expor `now_fn`).
6. **Rede/portas:** obrigatório porta efêmera (`bind(("127.0.0.1", 0))` + `getsockname()`); padrão já existente no repo, só generalizar.

### 4.2 Testes de contrato entre ferramentas (novos)
- **Contrato sizing→Helm:** fixture `PLANO-INFRAESTRUTURA.json` com sizing conhecido → `_carregar_sizing_ops` + values.yaml gerado deve conter os recursos exatos (hoje o elo item-12 não tem teste de ponta).
- **Contrato outbox:** propriedade "nenhum evento é perdido nem duplicado sob crash entre emit/mark" — com worker real e kill injetado (o mock de falha do G_INJECT é o modelo).
- **Contrato RLS:** 2 tenants, INSERT/SELECT cruzados, afirmar zero vazamento em ambos os sentidos (fecha o mutante RLS da tabela 2.4).
- **Contrato WAL:** conexão nova obtida do `Database` deve reportar `PRAGMA journal_mode = wal` e `busy_timeout = 5000` (fecha o mutante de PRAGMAs).

### 4.3 Mutação como gate (fase final do roadmap)
- Adotar `mutmut` (anti-NIH: ferramenta OSS madura) **apenas nos módulos de regras exatas**: `03_sizing.py` (ops), injector SHA-256 (enterprise), `outbox_worker.py`, `RLSConnection` (master) — score de mutação mínimo (ex.: 70%) por módulo, gate `G_MUTACAO` com baseline versionado (mesma mecânica do `G_DRIFT_NUCLEO_COMPARTILHADO`).

---

## 5. Actionable Roadmap (priorizado, pronto para planos-auditoria-runner)

| # | Prioridade | Ação | Fecha | Critério de pronto |
|:--|:--:|:--|:--|:--|
| 1 | **P0** | Testes de conteúdo SHA-256 no injector (hash computado no teste vs registro) | [TS-2], mutante hash | Mutante sha1/entrada-trocada morre; teste afirma 5 arquivos com hashes de conteúdos distintos conhecidos |
| 2 | **P0** | Testes de exatidão do sizing (soma + ceil por fixture de nicho, valores de ouro) | [TS-3], mutante ceil | Mutantes `floor+1`/requisito×2 morrem; tabela de valores esperados por nicho no teste |
| 3 | **P1** | Teste de crash pós-emit no Outbox + teste de listener que falha (dead-letter após N) — alinhado ao roadmap P0 do relatório de resiliência | [TS-6] | Redespacho idempotente provado; loop infinito impossível (teste com listener sempre-falho termina) |
| 4 | **P1** | Eliminar `time.sleep` dos testes CQRS/events (injetar relógio) e das integrações (polling com deadline) | [TS-9] | 0 `time.sleep` em `tests/unit` (gate AST simples); CQRS TTL testado com now_fn fake |
| 5 | **P1** | Porta efêmera nas integrações de servidor (3000 → bind 0) | [TS-10] | Testes de integração passam com serviço já na 3000; padrão `getsockname()` nos 2 arquivos |
| 6 | **P1** | `G_TESTES_REAIS` v2: junitxml estruturado + orçamento de skipped (lista nominal) + duração por suíte no resumo | [GE-1/2/3] | Gate falha com skip não autorizado; contagens vindas de XML, não regex |
| 7 | **P2** | Testes de contrato RLS (vazamento cruzado) e WAL (PRAGMAs da conexão) | tabela 2.4 | Mutantes de filtro-tenant e PRAGMA removido morrem |
| 8 | **P2** | Contrato sizing→Helm (fixture PLANO-INFRAESTRUTURA → values.yaml exato) | elo item 12 | Teste de ponta ops→enterprise verde |
| 9 | **P3** | `G_MUTACAO` (mutmut) nos 4 módulos de regras exatas com baseline versionado | seção 4.3 | Score mínimo 70% por módulo; gate integrado ao pre-commit manual (como G_SEGREDOS) |
| 10 | **P3** | Política de warnings: remover `ignore::DeprecationWarning` global; escalar para erro por categoria selecionada | [TS-13]/[GE-5] | Suítes verdes sem filtro global; deprecações visíveis no resumo |

**Sequência:** 1-2 são os mutantes de segurança/finança (maior risco, menor custo). 3 depende da decisão de dead-letter do roadmap de resiliência (executar junto). 4-6 estabilizam o gate antes de 9 (mutação exige suíte rápida e determinística).
