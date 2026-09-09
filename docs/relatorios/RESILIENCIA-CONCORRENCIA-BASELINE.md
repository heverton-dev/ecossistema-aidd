# AUDITORIA: RESILIÊNCIA, CONCORRÊNCIA E INTEGRIDADE TRANSACIONAL

> **Data:** 2026-09-09
> **Status:** ✅ PLANO FORMALIZADO — `docs/planos/a-fazer/04-resiliencia-concorrencia-e-integridade/`
> **Tags:** #plano-gerado #resiliencia #concorrencia #integridade
> **Escopo:** Análise técnica profunda de confiabilidade de runtime, SQLite WAL, atomicidade de arquivos e recuperação de falhas no Ecossistema AIDD.
> **Método:** leitura direta do código com referências arquivo:linha; `cmp` byte-a-byte entre master/enterprise; varredura por padrões (`os.replace`, `fsync`, `BEGIN`, `busy_timeout`, staging). Escopo de código-limpo/deduplicação **excluído** (coberto por agentes ativos em `docs/planos/fazendo/`).

──────

## 1. Executive Risk Scorecard (Criticidade × Probabilidade de corrupção de estado / perda de dados)

| Tool | Corrupção de estado | Perda de dados | Encontro crítico dominante |
|:---|:---|:---|:---|
| **aidd-master** (runtime gerado) | 🔴 **ALTA** (Crítico × Média) | 🟡 MÉDIA | Outbox at-least-once **de fato at-most-once** (perda silenciosa de eventos); WAL correto mas sem controle de transação explícito |
| **aidd-enterprise** (runtime gerado) | 🔴 **ALTA** (Crítico × Média) | 🟡 MÉDIA | Idêntico ao master (arquivos byte-idênticos confirmados por `cmp` para `database.py`/`outbox_worker.py`) |
| **aidd-generator** (pipeline 8 fases) | 🟡 MÉDIA (Alto × Média) | 🟡 MÉDIA (custo de tokens) | Cache sem schema, sem atomicidade, sem resume — crash = re-executar tudo + estados mistos no cache |
| **aidd-ops** (pipeline deploy) | 🟢 BAIXA-MÉDIA | 🟢 BAIXA | `_gravar_plano` não atômico; deploy sem checkpoint de retomada |
| **Orquestração** (`ecossistema.py`) | 🟢 BAIXA | 🟢 BAIXA | Sem estado próprio; herda os riscos das tools que roteia |
| **aidd-forge** (injection) | 🟡 MÉDIA | 🟢 BAIXA | `shutil.copy2` direto no destino (sem staging); `--force` pode truncar arquivo se kill no meio da cópia |

**Matriz resumida:** 2 ferramentas em risco crítico (os runtimes gerados, que também são o produto entregue ao usuário final), 1 em risco médio-alto com custo financeiro direto (generator — tokens queimados), resto controlado.

---

## 2. Detailed Technical Findings

### 2.1 SQLite Concurrency & WAL Integrity (`src/core/database.py`)

**O que está correto (base sólida):**
- WAL + PRAGMAs aplicados por event listener do SQLAlchemy em toda conexão nova: `journal_mode=WAL`, `synchronous=NORMAL`, `busy_timeout=5000`, `foreign_keys=ON` (`database.py:90-104`). Padrão correto para SQLite concorrente.
- Pool gerenciado pelo SQLAlchemy (NIH #8), `timeout=10.0` no connect — SQLITE_BUSY tem um caminho de retry no driver antes de propagar.
- Context manager transacional correto na fachada: `__exit__` faz `rollback()` em exceção, `commit()` em sucesso (`database.py:117-124`, idem `PostgresConnectionProxy`, idem `RLSConnection`).
- `busy_timeout` também aplicado no fluxo async (`database.py:460-470`).

**Violações:**

- **[SQL-1] Worktree paralelas sobre o MESMO `app.db` = contenção real.** O runtime gerado usa `DATABASE_URL` default `sqlite:///app.db` (`database.py:645`). Duas sessões/worktrees de desenvolvimento apontando para o mesmo arquivo criam writers concorrentes. WAL mitiga (1 writer + N readers), mas: `busy_timeout=5000` é pouco sob migrations longas (CREATE TABLE + seed dentro de `init_schema` de cada módulo, executadas no boot de `Database.__init__` via `init_system_tables`); e **não há circuito de degradação** — ao estourar `SQLITE_BUSY`, a exceção sobe crua para o route handler, que a traduz em `{"sucesso": False, "erro": str(e)}` genérico (ex.: `modulo1/routes.py:95-97`). Sem retry com backoff, sem código de erro estruturado.
- **[SQL-2] Nenhuma transação explícita em código gerado — confiança total no `__exit__` implícito.** `services.py` dos módulos gerados executa N statements (`SELECT` de leitura para diff + `UPDATE` + audit + outbox) e nunca chama `BEGIN`/`commit()`/`rollback()` explicitamente; a atomicidade depende 100% do `with self.db.get_connection() as conn` do `EngineFacadeConnection.__exit__`. Isso **funciona** (python sqlite3 não abre transação implícita para SELECT; commit no exit cobre o bloco), mas é um contrato invisível: qualquer código gerado que use `conn.execute` **fora** do `with` (ou aninhe conexões) comita em instantes diferentes. `record_migration` (`database.py:652-663`) é o único que chama `conn.commit()` explícito dentro do with — redundante mas inofensivo.
- **[SQL-3] `ReadModelCache.get_or_revalidate` dispara thread daemon que usa conexões do pool sem coordenação** (`cqrs.py:30-38`): a revalidação em background roda `fetcher()` (que abre conexão do pool) numa thread qualquer, com `check_same_thread=False` tornando isso *possível* mas não *coordenado*. Com pool SQLAlchemy default (5 conexões + overflow 10), picos de revalidação concorrente podem exaurir o pool e o erro aparece na thread daemon (engolido silenciosamente — ninguém lê o resultado). Risco de stale eterno sem sinal.
- **[SQL-4] `check_same_thread=False` global** (`database.py:90`): necessário para o worker daemon, mas remove a única guarda do sqlite3 contra uso multi-thread acidental de uma mesma conexão. Com o facade devolvendo conexões ao pool no `close()` (`database.py:110-112`), uma conexão "fechada" pode estar em uso por outra thread — o padrão OutboxWorker (abaixo) usa conexões curtas por operação, o que evita o pior caso, mas nada impede que código gerado retenha uma conexão entre requests.

### 2.2 Atomic Operations & File System Idempotency

- **[FS-1] ✅ Padrão-ouro existe e é testado — mas só no aidd-generator.** `scripts/core/injector/materializador.py:1-100`: staging em `.aidd/cache/_injector_staging/<uuid>/` → valida destinos → escreve tudo em staging → publica com `os.replace` (atômico por arquivo) → rollback do que foi publicado em falha. Testado inclusive com injeção de falha no meio do `os.replace` (`scripts/gates/G_INJECT.py:123-131` via mock de `os.replace`).
- **[FS-2] 🔴 O mesmo conceito em `aidd-master/enterprise/materializador.py` é snapshot-rollback, não atômico.** `materializar()` faz `open(destino, "w")` **direto no destino final** (`materializador.py:515-520`) com snapshot em memória para rollback (`_executar_rollback`, `materializador.py:409-428`). Duas janelas de corrupção: (a) kill (SIGINT/power) durante a escrita = arquivo truncado em disco, snapshot perdido junto com o processo — rollback nunca roda; (b) o rollback em si pode falhar silenciosamente (`except OSError: pass` em cada passo, `materializador.py:412-428`), deixando estado parcial *sem sinal*. Espelhos multi-harness são escritos no mesmo padrão não-atômico (`materializador.py:515-525`), e os destinos canônicos são escritos com "melhor esforço, não falha a operação" (`materializador.py:530-546` — comentário explícito) — podem ficar dessincronizados dos espelhos principais.
- **[FS-3] 🔴 `scaffold_infra.py` (enterprise, entregue ao usuário) escreve 7 arquivos Terraform/Helm sequencialmente, sem staging nem rollback** (`scaffold_infra.py:394-398` — `open(path, "w")` + write, loop). Kill no meio = half-generated `infra/` sem nenhum marcador de incompletude. `scripts/add_module.py` e `compose_suite.py` usam `tempfile.TemporaryDirectory` para **renderizar** mas depois copiam direto para o destino final (mesmo padrão copy-then-hope).
- **[FS-4] 🟡 `aidd-forge/core/injector.py`: `shutil.copy2(src, dst)` direto** (`injector.py:63`). Copy de arquivo de template grande pode ser interrompido → destino truncado. Como o forge trabalha com arquivos pequenos e `skipped` se existe, a janela é estreita mas existe; o overwrite com `--force` usa o mesmo caminho.
- **[FS-5] 🟡 Registry updates (CAPABILITIES.json, mcp.json) são read-modify-write sem lock nem rename atômico** (`materializador.py:295-303` escreve CAPABILITIES direto; `materializador.py:460-465` idem mcp.json — este último com rollback manual de conteúdo, que sofre da mesma janela kill-window do [FS-2]). Duas injeções concorrentes podem perder updates do registry (lost update).
- **[FS-6] 🟢 `remover_componente` tem ordem segura** (remove arquivos antes de reescrever registry — `materializador.py:311-336`): uma falha no meio deixa arquivos órfãos (recuperável por re-sync) em vez de registry apontando para nada.

### 2.3 Pipeline Failure Recovery & State Machines (aidd-generator 8 fases)

**Realidade atual: "resume" por acidente, não por design:**

- **[PIPE-1] 🔴 Não existe máquina de estados do pipeline.** `executar_pipeline` (`pipeline_completo.py:151-260`) é uma função linear: fases 1→2→3→4→5→(8)→6→7 com `if idx is None: return _falhar(...)`. Não há leitura de `_phase_0N_index.json` pré-existente para pular fase completa, não há `--resume-from`, não há persistência do estado de progresso do pipeline (o que existe são os índices por fase, escritos como *efeito colateral*). Falha na fase 7 = re-executar fases 1-6 (com custo real de LLM nas fases 2-5/8).
- **[PIPE-2] 🔴 Fases gravam cache diretamente no destino final, sem staging/atomicidade.** Todas as 8 fases usam `write_text`/`json.dump` direto (`01_pesquisador.py:676-680, 733-747`; padrão idêntico nas demais — `02_analisador.py:266-269`, `03_designer.py:352-355`, `04_decisor.py:173-176`, `05_criador.py:378-381`). Kill durante `json.dump` = JSON truncado no cache. O pipeline seguinte não detecta: a fase anterior não valida o que lê.
- **[PIPE-3] 🔴 Leitura de cache sem validação de schema e sem tolerância a truncamento.** `pipeline_completo.py:199,211,222,233`: `json.loads(insights_path.read_text())` — um JSON truncado do [PIPE-2] vira `JSONDecodeError` não tratada, crashando o pipeline com traceback cru (não o `_falhar` estruturado). Pior: `analise = json.loads((data_dir / 'analise_phase2.json').read_text())` **sem checar `.exists()`** (`pipeline_completo.py:211`) — se a fase 2 falhou parcialmente, o crash é `FileNotFoundError`. A única checagem de existência é opcional (`if insights_path.exists() else {}` — `pipeline_completo.py:199`), o que **mascara** cache ausente como `{}` e propaga lixo para a fase 2.
- **[PIPE-4] 🟡 Os "gates de schema" existem mas não guardam a persistência.** `ValidadorGates.executar_todos` (fase 1, R1-R4) e `_gate_e3_sqlite_schema` (fase 5) validam conteúdo **antes** de escrever, mas nenhum schema JSON formal valida os arquivos `.aidd/cache/data/*.json` **na leitura** pela fase seguinte (nenhum uso de `jsonschema`/verificação de chaves obrigatórias nas fases 2-8). O diretório `scripts/phases/schemas/` existe — não é consumido na fronteira de leitura.
- **[PIPE-5] 🟡 Fase 5 escreve no projeto-alvo com o mesmo padrão não-atômico** (mkdir + write direto em `scripts/schemas/`, `05_criador.py:399-402`): falha no meio da fase 5 deixa projeto-alvo parcialmente criado, sem journal para saber o que ficou faltando. O gate E3 valida apenas o schema SQLite, não a completude do projeto.
- **[PIPE-6] 🟢 Ponto positivo:** cada fase persiste `_phase_0N_index.json` com `status`/`tokens`/tempo — a **matéria-prima** para um resume por design já existe; falta o orquestrador consumi-la.

### 2.4 aidd-ops: deployment pipeline

- **[OPS-1] 🟡 `_gravar_plano` não atômico** (`pipeline_ops.py:60-64`): mesmo padrão [PIPE-2]. O plano é o contrato de entrada do `scaffold_infra` (item 12) — truncamento aqui quebra a integração ops→enterprise silenciosamente (`_carregar_sizing_ops` lê sem schema).
- **[OPS-2] 🟡 Deploy (`pipeline_ops_deploy.py` + `ssh_runner.py`) não tem checkpoint de retomada:** hardening Ansible é idempotente por natureza (bom — re-run seguro), mas o pipeline como um todo não registra que etapa completou; falha em `swap` re-roda `atualizar_pacotes`+`docker`. Sem `Result` persistido por etapa. Não é corrupção (Ansible idempotente), é custo/tempo.
- **[OPS-3] 🟢 Pontos positivos:** `Result` monádico em toda a fronteira (`pipeline_ops.py:103-165`); erros estruturados propagados sem máscara; pre-voo de conectividade antes do deploy (`ssh_runner.py:96-120`); tags de bootstrap em lista fechada (`TAGS_PERMITIDAS`).

### 2.5 Transactional Outbox & Event Publishing

**A atomicidade da gravação está correta; a entrega tem dois defeitos de semântica:**

- **[OUT-1] ✅ Inserção na mesma transação da mutação: CORRETO.** `enqueue_outbox_event` recebe a **conexão da mutação** e faz INSERT na `_outbox_events` dentro do mesmo `with` (`database.py:668-681`; uso real em `modulo1/services.py:63-66`: INSERT de negócio + audit WORM + outbox + `conn.commit()` no mesmo bloco). Kill entre mutation e emit = evento continua `pendente` e é repescado. Isso é Outbox feito certo.
- **[OUT-2] 🔴 "At-least-once" prometido, "at-most-once" entregue na prática.** `outbox_worker.py:41-72`: lê pendentes, faz `event_bus.emit(...)` (dispatch em memória) e **só depois** marca como processado em **outra conexão/transação** (`_marcar_processado`, `outbox_worker.py:74-78`). Vazamento inverso: se o processo cair **após** o emit mas **antes** do UPDATE de status, o evento é reprocessado no boot (correto, at-least-once). MAS: se o `emit()` lança (listener com bug), o evento **nunca é marcado como processado e nunca mais é tentado com sucesso** — não há retry counter, dead-letter, nem backoff; o evento fica `pendente` para sempre, re-falhando a cada ciclo de 2s e imprimindo `[OUTBOX_ERROR]` no stdout (`outbox_worker.py:38-40,66-67`), infinitamente. Com listeners não-idempotentes (o comum em código gerado), o reprocesso pós-crash também duplica efeitos colaterais.
- **[OUT-3] 🔴 Nenhuma garantia de exclusividade entre workers concorrentes.** `process_pending` faz `SELECT ... WHERE status='pendente' LIMIT ?` sem `FOR UPDATE`/claim atômico (`outbox_worker.py:47-57`). Dois processos do servidor (ex.: `uvicorn --workers 2`, ou server + script de manutenção ambos com OutboxWorker) processam **o mesmo evento duas vezes** — a janela entre o SELECT e o UPDATE de status é toda a execução do handler. Para entregar at-least-once com N workers, falta claim atômico (`UPDATE ... WHERE status='pendente' RETURNING` ou coluna `claimed_by/claimed_at`).
- **[OUT-4] 🟡 Sem idempotency-key para o consumidor.** O `event_id` existe (uuid4 no enqueue) mas não é passado como contrato para o handler; nenhum dos lados oferece tabela de deduplicação. At-least-once **sem idempotência do consumidor** = efeitos duplicados garantidos em qualquer crash-replay.
- **[OUT-5] 🟡 Ordenação não garantida:** `ORDER BY criado_em ASC` (resolução ISO-8601 com microssegundos — eventos no mesmo microssegundo podem reordenar; e emit concorrente entre workers quebra ordem de qualquer forma). Para eventos de domínio com semântica de estado (criado→atualizado→deletado), reordenação = estado inconsistente no consumidor.

---

## 3. Target Hardening Architecture (receitas)

### 3.1 `Escritor Atômico` (filesystem) — resolver [FS-2/3/4/5], [PIPE-2/5], [OPS-1]
Promover a receita já provada no generator (`staging → os.replace → rollback`) para utilitário compartilhado:
```
escritor_atomico.escrever(destino, conteudo):
    1. tmp = destino.parent / f".{nome}.{uuid}.tmp"     # mesmo filesystem do destino (rename atômico garantido)
    2. open(tmp,"w") → write → f.flush() → os.fsync(f.fileno())
    3. os.replace(tmp, destino)                          # atômico; kill antes daqui = destino intacto
    4. fsync do diretório (durability do rename)         # opcional-nível-produção
```
- Multi-arquivo transacional: reusar staging dir + ordem de publicação com journal (`_journal.json` no staging: lista ordenada de publishes pendentes) para **recuperar** (não só reverter) após crash: no boot, qualquer `_journal.json` órfão é concluído ou descartado.
- Aplicar em: `materializador.py` (master+enterprise), `scaffold_infra.py`, `add_module.py`, `compose_suite.py`, todas as 8 fases do generator, `_gravar_plano` (ops), registry writers (CAPABILITIES/mcp.json).
- Fonte única em `componentes/compartilhado/` (o "almoxarifado" já decidido no Item 1 do plano de código-limpo) — um único place de teste e auditoria.

### 3.2 `Gerenciador de Conexão WAL` (SQLite) — resolver [SQL-1/3/4]
- **Retry com backoff para SQLITE_BUSY:** wrap `conn.execute` no `EngineFacadeConnection` com retry exponencial (50ms→2s, 5 tentativas) apenas em `sqlite3.OperationalError: database is locked` — busy_timeout cobre a contenção curta; o retry cobre a longa (migrations).
- **Pool explícito:** `pool_size=10, max_overflow=5, pool_pre_ping=True` no `create_engine`; `pool_timeout` mapeado para erro estruturado (não exceção crua).
- **Thread-safety coordenada:** revalidação do `ReadModelCache` passa a consumir de uma fila própria com 1 worker (não thread por miss), limitando conexões concorrentes do cache a 1.
- **Erros estruturados:** `SQLITE_BUSY` traduzido para `Result.fail(codigo="DB_LOCKED")` na fronteira do route handler (integra com o `Result` já padrão no ops).

### 3.3 `Outbox Idempotente` — resolver [OUT-2/3/4/5]
```
tabela _outbox_events + colunas: tentativas INT DEFAULT 0, claimed_at TEXT, claimed_by TEXT
claim atômico:   UPDATE _outbox_events SET claimed_at=?, claimed_by=? WHERE status='pendente' AND claimed_at IS NULL
                 → (sqlite3.Cursor.rowcount > 0) ganha o lote (ou row-level via UPDATE...RETURNING)
entrega:         emit() com try/except → sucesso: status='processado'
                                              → falha: tentativas+=1, claimed_at=NULL
                 → tentativas >= N (ex. 10): status='dead_letter' (parar de re-falhar; inspecionável)
idempotência:    tabela _eventos_processados(event_id PRIMARY KEY, processado_em) consultada
                 pelo consumidor antes de aplicar efeito (dedupe padrão at-least-once)
ordenação:       coluna seq INTEGER (AUTOINCREMENT no insert) e ORDER BY seq — não timestamp
```
Permanece at-least-once **com dedupe explícito no consumidor** — semântica honesta (alinhada à Regra de Ouro #9).

### 3.4 `Máquina de Estados do Pipeline` (generator) — resolver [PIPE-1/3/4]
```
.aidd/cache/_pipeline_state.json   ← estado explícito, versionado, escrito atomicamente (3.1)
{ "pipeline_id": uuid, "fase_atual": 5, "fases": {"1": "COMPLETO", ..., "4": "COMPLETO"} }
```
- `executar_pipeline` lê o estado no boot: fase `COMPLETO` com index válido é **pulada** (critério de completude = `_phase_0N_index.json` parse ok + `status=COMPLETO` + validação de schema da fase → fecha [PIPE-4]).
- Flag `--resume` (default: resume se estado existe, `--fresh` para recomeçar). Falha de parse de cache → `_falhar` estruturado, nunca traceback cru nem `{}` silencioso.
- Schemas JSON das fases (`scripts/phases/schemas/`) validados com `jsonschema` na **leitura** de cada artefato inter-fase.

---

## 4. Actionable Roadmap (priorizado, pronto para planos-auditoria-runner)

| # | Prioridade | Ação | Resolve | Ferramenta | Critério de pronto (gate/teste) |
|:--|:--:|:--|:--|:--|:--|
| 1 | **P0** | Outbox: claim atômico + retry counter + dead-letter + `seq` monotônico; tabela de dedupe consumida pelo handler | [OUT-2/3/4/5] | master+enterprise (fonte única) | Teste: 2 workers `process_pending` paralelos → cada evento despachado exatamente 1×; teste: listener falhando 3× → evento vai a dead-letter, sem loop infinito |
| 2 | **P0** | `Escritor Atômico` compartilhado + migrar os 8 pontos de escrita crítica (materializador ×2, scaffold_infra, add_module, compose_suite, fases 1-8, _gravar_plano) | [FS-2/3/4/5], [PIPE-2/5], [OPS-1] | todas | Gate AST: proibir `open(destino,"w")` direto nos módulos listados; teste de kill-inject no meio da escrita (mock de `os.replace`) — já existe modelo no `G_INJECT.py` |
| 3 | **P1** | Máquina de estados do pipeline + resume por fase + validação `jsonschema` na leitura inter-fases | [PIPE-1/3/4] | generator | Teste: falhar fase 5 → `--resume` executa apenas fase 5 em diante (fases 1-4 lidas do cache validado); JSON truncado injetado → `_falhar` estruturado |
| 4 | **P1** | Retry/backoff SQLITE_BUSY + pool explícito + erros estruturados `DB_LOCKED` na fronteira HTTP | [SQL-1/2] | master+enterprise | Teste: lock externo no db (2ª conexão BEGIN EXCLUSIVE) durante request → request recebe `Result.fail(DB_LOCKED)` com retry transparente, não exceção |
| 5 | **P1** | Fila única p/ revalidação do ReadModelCache (1 worker) + telemetria de stale | [SQL-3] | master+enterprise | Teste: pico de 100 misses concorrentes → ≤ pool estável, sem thread explosion; métrica de idade máxima de stale |
| 6 | **P2** | Registry writers (CAPABILITIES.json / mcp.json) com lock de arquivo + rename atômico | [FS-5] | master+enterprise | Teste: 2 `materializar()` concorrentes → ambos os updates do registry presentes |
| 7 | **P2** | Ops deploy: persistir `Result` por etapa de bootstrap (checkpoint) para re-run incremental | [OPS-2] | ops | Re-run pós-falha executa apenas etapas pendentes (verificável por log de etapas) |
| 8 | **P2** | Journal de recuperação pós-crash para multi-arquivo (concluir/descartar staging órfão no boot) | [FS-2] | master/enterprise + generator | Teste: staging com journal simulado é concluído no próximo boot; sem journal parcial sem dono |

**Sequência recomendada:** 1 e 2 primeiro (corrigem perda real de eventos e corrupção real de arquivos — os únicos achados críticos × prováveis). 3 depende de 2 (estado do pipeline usa o escritor atômico). 4-8 independentes entre si.

**Nota de honestidade de rótulo (Regra #9):** o docstring do `outbox_worker.py` afirma "Entrega Garantida At-Least-Once" e o de `materializador.py` (master) afirma "Motor de Materialização Transacional"; ambos descrevem garantias **mais fortes** que as implementadas (at-most-once na prática; snapshot-rollback sem atômica). Os dois rótulos entram na lista de termos a corrigir junto com o roadmap acima.
