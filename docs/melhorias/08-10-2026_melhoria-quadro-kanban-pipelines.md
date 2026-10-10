# Quadro Kanban dos Pipelines — Plano de Implementação (v3)

> **Data:** 08-10-2026 / 10-10-2026  
> **Status:** CONCLUÍDO (10/10) — Todas as 6 fases implementadas, provadas e auditadas  
> **Nota final:** 10/10 — Zero stubs, 13 testes verdes, Quality Gate G_mapa_pecas exit 0  
> **Interface:** Craft Floor (Impeccable), Dark/Light Universal, Zero dependências externas  
> **Referência:** `zazencodes/zazencodes-season-3` → `src/software-factory-claude-code/factory/dashboard.html`

---

## 1. Em uma frase

Um dashboard local com **um Kanban para cada pipeline do ecossistema**: as colunas de cada quadro são as etapas daquele pipeline, cada execução é um cartão que anda de coluna em coluna, ao vivo, e tudo o que terminou fica num **Arquivo** consultável.

---

## 2. O que mudou entre as versões

| Ponto | v1 | v2 | v3 |
|---|---|---|---|
| Forma | um quadro só, 6 colunas iguais para tudo | um Kanban por pipeline, colunas = etapas do pipeline | igual à v2 |
| De onde vêm as etapas | cada leitor sabia as suas | contrato único de pipelines, lido por catálogo, mapa e quadro | contrato "vivo": pipeline novo não declarado barra o commit |
| Gaveta do cartão | linha do tempo e artefatos | igual à v1 | 5 blocos: linha do tempo, o que foi feito, por que parou, o que precisa de você, dados brutos |
| Passado | concluídos dos últimos 7 dias + limpeza | igual à v1 | aba Arquivo + arquivamento compactado (nada apagado sem OK) + backup mensal opcional no GitHub privado |
| Custo e ferramentas | não previsto | harness, LLM e tempo por etapa | + fase própria para skills, MCPs e tokens ("não medido" quando não houver dado) |
| Ordem | tela primeiro | contrato, registro, tela | igual à v2, mais arquivamento e custo no fim |

---

## 3. Inventário de hoje (medido em 08-10-2026, à noite)

Fonte: `docs/auditoria/mapa-pecas/catalogo-pecas.json`, chave `pipelines` (a mesma que desenha o mapa visual de pipelines).

| Pipeline | Etapas no catálogo hoje | Estado gravado hoje | O que falta para virar Kanban |
|---|---|---|---|
| Tríade pure | 7: fundação (forge), planejamento (planner), motor, despacho (master), blindagem (enterprise), infraestrutura (ops), auditoria do projeto | `<projeto>/.aidd/cache/_pipeline_state.json` | as 7 etapas já servem de colunas; falta o cartão saber a etapa atual |
| Tríade open | as mesmas 7 (motor = open) | nenhum | registrar a etapa atual |
| Tríade freedom | as mesmas 7 (motor = freedom) | nenhum | registrar a etapa atual |
| Auditoria 4F | 8, copiadas dos títulos da SKILL.md (3 delas são preparação, não fase) | manifesto, branch `audit/*`, refs aprováveis, worktrees, trava da fila | colunas reais: Fase 1 a Fase 4, gate final, aprovação |
| Evolução | 4 títulos genéricos ("For each ticket", "After the last ticket") | o mesmo do 4F | colunas por papel (decisão F) |
| melhoria → plan → orchestrate | 3 ("passo 1", "passo 2", "passo 3") | relatórios em `docs/melhorias/`, planos em `docs/planos/` | dar nome às etapas e registrar |
| aidd-ingest | 4 (triagem, auditoria 4F, plano, execução) | nenhum | registrar |
| aidd-ops | 0 | nenhum | declarar as etapas |
| aidd-pipeline | 0 | nenhum | declarar as etapas |

Rodam de verdade, mas não estão no catálogo: bateria de gates (`python ecossistema.py audit`), despacho VSA (`python ecossistema.py dispatch`) e run-plan (`orchestrator_pipeline.py`). Pela decisão A, os três entram.

**Conclusão:** hoje as "etapas" do catálogo são títulos copiados das SKILL.md, não colunas confiáveis. Antes de qualquer tela, cada pipeline declara suas etapas num lugar só.

### Fontes de estado por pipeline (levantadas na v1)

| Pipeline | Como roda | Estado que já existe | Como entra no quadro |
|---|---|---|---|
| Auditoria 4F | `python scripts/orquestrador_4f.py --manifest …` (dentro de `fila_ciclos.ciclo_pesado`) | manifesto; branch `audit/<id>`; worktrees `../worktrees_<id>/<fase>`; `refs/aidd/aprovavel/<id>`; merge `chore(audit): aprova <id>`; `.aidd/fila-ciclos.lock`; `secoes/medicoes/ultimo-ciclo.json` | leitura derivada; depois detalhe por etapa |
| Evolução | `python ecossistema.py evolucao …` compila o `PLANO-EVOLUCAO` e chama o mesmo `orquestrador_4f.py` | o mesmo do 4F | o mesmo do 4F |
| Bateria de gates | `python ecossistema.py audit` (pre-commit) | só o registro da última bateria verde por árvore (`secoes/medicoes/completo-<árvore>.json`) | registro no ponto de entrada |
| Despacho VSA | `python ecossistema.py dispatch` → `dispatch_pipeline.py` | só `dispatch_rollback_report.json`, e apenas em rollback | registro; depois etapa por fatia |
| Run-plan / pipeline | `ecossistema.py run-plan` / `pipeline` → `orchestrator_pipeline.py` | nenhum | registro; depois paralelo → barreira → sequencial |
| Tríade pure | `ecossistema.py pure` → aidd-pure | `<projeto>/.aidd/cache/_pipeline_state.json` (`PipelineStateManager`: `fases`, `fase_atual`, `status_global`) | registro; depois ponteiro para esse estado |
| Tríade open / freedom | `ecossistema.py open` / `freedom` | nenhum | registro |

Protótipo só-leitura da v1 (08-10-2026, sobre os 19 `MANIFESTO-4F.json`, 36 ms e 2 chamadas git): 15 concluídos, 3 com saídas parciais, 1 reprovado naquele dia e 6 branches `audit/*` abertas sem aprovação. Além deles, 39 `PLANO-EVOLUCAO*.json` no mesmo formato.

---

## 4. Como fica a tela

- **Página inicial "Pipelines":** um bloco por pipeline, com nome, quantas execuções estão em cada etapa (barrinhas), quantas estão paradas e quantas precisam de você.
- **Kanban do pipeline** (clique no bloco): colunas Fila → etapas declaradas → Concluído | Parado. Cada cartão é uma execução: título, etapa atual, tempo, harness, LLM, `motivo` (por que está ali) e o comando sugerido com botão "copiar".
- **"Precisa de você"** é selo vermelho no cartão, não coluna, e a contagem aparece no título da aba ("(1) Quadro AIDD").
- **Gaveta do cartão** (clique ou Enter; fecha com Esc), em 5 blocos:
  1. **Linha do tempo:** cada etapa com início, fim, duração, harness e LLM.
  2. **O que foi feito:** commits, arquivos gerados (abertos como texto) e o gate de cada etapa com o resultado.
  3. **Por que parou:** motivo, comando que falhou e as últimas linhas do log, com o caminho do log completo.
  4. **O que precisa de você:** a pergunta e o comando pronto para copiar.
  5. **Dados brutos:** o JSON da execução, recolhido.
- **Aba "Arquivo":** todas as execuções terminadas, com busca por pipeline, data e situação; cada uma abre a mesma gaveta. Inclui as já compactadas (seção 8, Fase 4).
- **Marcas por etapa** com ícone **e** texto: ✓ concluída, ● em curso, ○ pendente, ✕ falhou. A cor nunca é o único sinal, e `prefers-reduced-motion` desliga a animação de "em curso".
- **Concluído** no Kanban mostra os últimos 7 dias; o resto fica na aba Arquivo.

```text
┌ Quadro AIDD · [Pipelines] [Arquivo] ─────────────────── atualizado há 2 s ● ┐
│ Auditoria 4F   ▮▮▯▯▯▯  2 rodando · 1 precisa de você                         │
│ Evolução       ▮▯▯▯    1 rodando                                             │
│ Tríade pure    ▯▯▯▯▯▯▯ nada rodando                                          │
│ ...                                                                          │
├──────────────── Kanban: Auditoria 4F ───────────────────────────────────────┤
│ Fila │ Fase 1 │ Fase 2 │ Fase 3 │ Fase 4 │ Gate final │ Concluído │ Parado    │
│      │        │ grill  │        │        │            │    15     │   6       │
│      │        │ c-02 ● │        │        │            │           │           │
└──────┴────────┴────────┴────────┴────────┴────────────┴───────────┴───────────┘
```

---

## 5. Decisões fechadas (usuário, 08-10-2026)

| # | Pergunta | Decisão |
|---|---|---|
| A | Quais pipelines entram? | Os 12: os 9 do catálogo + bateria de gates, despacho VSA e run-plan. A lista é **viva**: pipeline novo ou etapa nova entra sozinho no quadro e ninguém esquece de declarar (D0). |
| B | O que é um cartão? | Uma execução. Tickets e fases ficam dentro da gaveta, que mostra tudo o que foi feito, por que parou e o que precisa de decisão (seção 4). |
| C | Colunas fixas além das etapas? | Fila + Concluído + Parado; "precisa de você" como selo. |
| D | Onde o dashboard mora? | Neste repositório (`python ecossistema.py quadro`). O Mission Control (localhost:8989) ganha só um link, por ser outro projeto. |
| E | Quem declara as etapas? | Contrato único `modulos/04-nucleo-compartilhado/contracts/PIPELINES.json`, com teste que reprova etapa registrada fora dele. |
| F | Colunas da evolução? | Por papel: construtor, gate do ticket, gate final, aprovação. A lista de tickets fica na gaveta. |
| G | O passado se perde? | Não. Aba Arquivo; execuções antigas são compactadas e continuam consultáveis; nada é apagado sem OK do usuário; backup mensal opcional num repositório privado no GitHub, só com dados resumidos e depois do detector de segredos. |
| H | Skills, MCPs, tokens, harness, LLM e tempo? | Harness, LLM e tempo desde a Fase 1 (o orquestrador já sabe). Skills, MCPs e tokens numa fase própria no fim (Fase 5), lidos do registro de conversa de cada harness depois que a execução termina; sem dado, o cartão mostra "não medido", nunca estimativa. |

---

## 6. Decisões de arquitetura

**D0 — Contrato único e vivo de pipelines.** `modulos/04-nucleo-compartilhado/contracts/PIPELINES.json` lista cada pipeline: `id`, `nome`, comando de entrada, etapas (`id` + título curto em português) e de onde vem o estado. O catálogo de peças, o mapa visual de pipelines e o quadro leem esse arquivo; o quadro relê a cada consulta. "Vivo" quer dizer três coisas:
1. pipeline ou etapa nova no contrato aparece no quadro sem reiniciar nada;
2. o catálogo compara o contrato com o código (comandos do `ecossistema.py`, SKILL.md de pipeline, manifestos): pipeline existente e não declarado deixa o catálogo desatualizado, e o `G_mapa_pecas` barra o commit;
3. o emissor recusa etapa fora do contrato, e o teste reprova.

**D1 — Três camadas, da mais barata para a mais cara.** Leitura derivada → registro no ponto de entrada → detalhe por etapa. Cada camada funciona sozinha; a de cima só enriquece o cartão.

**D2 — Estado explícito em `~/.aidd/execucoes/<run_id>/`** (sobrescrevível por `AIDD_HOME`). Fora do repositório (o orquestrador faz `git add -A` nas worktrees), vale para qualquer worktree e para os projetos-alvo da Tríade, e fica fora do `%TEMP%`, que o limpador da porta 8989 apaga. Arquivo compactado em `~/.aidd/arquivo/`.

**D3 — Um arquivo, um escritor.** `estado.json` só é escrito pelo processo que abriu a execução. Subprocesso que também registra abre a **própria** execução com `pai = <run_id>`.

**D4 — O quadro só observa.** Nenhum botão muda estado; ação humana aparece como comando pronto para copiar. Lei #7.

**D5 — Consulta a cada 2 s com ETag**, pausada com a aba oculta. Sem SSE nem WebSocket.

**D6 — Só biblioteca padrão do Python; página sem dependências** (HTML, CSS e JS próprios, sem CDN, sem build), com os tokens de cor de `docs/relatorios/DIRETRIZES-DESIGN-RELATORIOS.md`, tema claro e escuro. O quadro funciona sem internet; só o backup opcional usa rede.

**D7 — Código em `scripts/`.** Nada em `componentes/compartilhado/src-core` (núcleo de produto, vigiado pelo `G_DRIFT_NUCLEO_COMPARTILHADO`). Contrato de pipelines e schema de estado em `modulos/04-nucleo-compartilhado/contracts/`.

**D8 — Sem quality gate novo.** Comportamento coberto por testes em `tests/`, que somam menos de 3 s. O "vivo" (D0, item 2) usa o `G_mapa_pecas` que já existe.

**D9 — Leitura que não interfere.** O quadro nunca chama o Orca e nunca roda `git status`; só `for-each-ref`, `worktree list --porcelain`, `ls-tree`, `show` e `log`, com `GIT_OPTIONAL_LOCKS=0` e sem herdar `GIT_DIR`/`GIT_WORK_TREE`.

**D10 — Todo cartão diz por que está naquela coluna** (`motivo`). Nenhum rótulo sem evidência (Lei #8).

**D11 — Log e conversa não são copiados.** O estado guarda o caminho dos logs e o ID da sessão de cada agente; o arquivo nunca duplica logs nem registros de conversa (são eles que ocupam espaço).

---

## 7. Contrato de estado

- Arquivo: `${AIDD_HOME:-~/.aidd}/execucoes/<run_id>/estado.json`
- `run_id` = `<pipeline>-<chave>-<AAAAMMDDTHHMMSSZ>-<pid>` (só `[a-z0-9-]`, até 120 caracteres)
- Schema: `modulos/04-nucleo-compartilhado/contracts/estado-execucao.schema.json` (validado com `jsonschema` só nos testes)
- `pipeline` precisa existir no `PIPELINES.json`, e `etapa_atual` precisa ser uma das etapas declaradas para ele.
- A coluna do cartão é a `etapa_atual`; `fila`, `concluido`, `falhou`, `cancelado` e `interrompido` levam às colunas fixas.

```json
{
  "schema": "aidd.quadro.estado/2",
  "run_id": "auditoria-4f-auditoria-aidd-grill-ciclo-02-20261009t131500z-18244",
  "pipeline": "auditoria-4f",
  "chave": "auditoria-aidd-grill-ciclo-02",
  "titulo": "aidd-grill · ciclo-02",
  "comando": "python scripts/orquestrador_4f.py --manifest docs/auditoria/aidd-grill/ciclo-02/MANIFESTO-4F.json",
  "pai": null,
  "processo": {"pid": 18244, "inicio": "2026-10-09T13:15:00Z"},
  "status": "executando",
  "etapa_atual": "fase-2",
  "etapas": [
    {"id": "fase-1", "status": "concluida", "harness": "claude", "modelo": "haiku",
     "sessao": "<id da sessão do agente>", "inicio": "2026-10-09T13:15:40Z", "fim": "2026-10-09T13:31:02Z",
     "gate": {"comando": "python docs/auditoria/aidd-grill/G_auditoria_15D.py ...", "exit": 0},
     "feito": ["commit a1b2c3d: laudo inicial"], "artefatos": ["docs/auditoria/aidd-grill/ciclo-02/LAUDO-15D-INICIAL.md"],
     "log": "C:/Users/trcnologia/aidd-logs/...", "custo": "nao-medido"},
    {"id": "fase-2", "status": "agente", "harness": "agy", "modelo": "haiku", "inicio": "2026-10-09T13:31:10Z"},
    {"id": "fase-3", "status": "pendente"},
    {"id": "fase-4", "status": "pendente"},
    {"id": "gate-final", "status": "pendente"}
  ],
  "historico": [
    {"em": "2026-10-09T13:15:00Z", "etapa": null, "evento": "aberta"},
    {"em": "2026-10-09T13:31:02Z", "etapa": "fase-1", "evento": "gate", "mensagem": "exit 0"}
  ],
  "parada": null,
  "humano": null,
  "fim": null,
  "exit_code": null,
  "seq": 7,
  "atualizado_em": "2026-10-09T13:31:10Z"
}
```

Valores permitidos:

- `status` da execução: `fila`, `executando`, `concluido`, `falhou`, `cancelado`. O quadro deriva `interrompido` quando o status é `executando` e o pid já morreu.
- `status` da etapa: `pendente`, `agente`, `gate`, `concluida`, `falhou`, `pulada` (saída já existia).
- `parada`: `{"motivo": "...", "comando": "...", "log": "..."}` quando falhou, parou ou foi interrompida; `null` caso contrário.
- `humano`: `{"motivo": "...", "comando": "..."}` quando o pipeline espera alguém; `null` caso contrário.
- `custo` da etapa: `"nao-medido"` até a Fase 5; depois `{"tokens_entrada": n, "tokens_saida": n, "skills": [...], "mcps": [...], "fonte": "..."}`.

Regras do emissor (`scripts/estado_execucao.py`):

1. Só biblioteca padrão; grava com `escritor_atomico.escrever_json_atomico`.
2. Se `os.replace` der `PermissionError` (no Windows acontece quando o quadro está lendo o arquivo), tenta de novo até 5 vezes, com 50 ms de intervalo; depois desiste em silêncio, com um único aviso no stderr por execução.
3. Nunca levanta exceção para quem chamou: o registro nunca derruba um pipeline.
4. `AIDD_QUADRO=0` desliga tudo. Sob pytest (`PYTEST_CURRENT_TEST` presente) só grava se `AIDD_HOME` tiver sido definido de propósito.
5. Quem abre uma execução exporta `AIDD_EXECUCAO_PAI=<run_id>` para os filhos; o filho que registrar algo grava esse valor em `pai`.
6. Uso como gerenciador de contexto: exceção → `falhou` (com `parada`); `KeyboardInterrupt` → `cancelado`; `SystemExit(n)` → `concluido` se `n` for 0, `falhou` nos demais.
7. `pipeline` e etapas vêm do `PIPELINES.json`; etapa fora do contrato é recusada.
8. `historico` só cresce (um evento por mudança); o resto do arquivo é reescrito inteiro.

```python
with Execucao.abrir(pipeline="auditoria-4f", chave=pipeline_id, titulo=titulo) as ex:
    ex.etapa("fase-1", "agente", harness="claude", modelo="haiku", sessao=sessao, orca={"aba": aba})
    ex.etapa("fase-1", "gate", gate={"comando": gate_fase}, log=caminho_log)
    ex.etapa("fase-1", "concluida", gate={"comando": gate_fase, "exit": 0}, feito=["commit a1b2c3d"])
    ex.pedir_humano("aprovar o merge do ciclo",
                    f"python scripts/orquestrador_4f.py --manifest {manifesto} --aprovar")
```

---

## 8. Fases

Cada fase fecha sozinha. Cada ticket é um commit, com o DoD conferido por comando.

### Fase 0 — Contrato vivo e inventário (nenhuma tela) · ~1 sessão

- **T0.1** Criar `PIPELINES.json` com os 12 pipelines e as etapas de cada um (decisões A, E e F), mais teste de forma.
- **T0.2** `scripts/catalogo_pecas.py` (coletar_pipelines) passa a ler o contrato; catálogo, mapas e livro regenerados na pasta real (não com o `visual-maps gerar` sozinho).
- **T0.3** Declarar as etapas de aidd-ops e aidd-pipeline, que hoje têm zero.
- **T0.4** Detector do "vivo": o catálogo compara o contrato com o código (comandos do `ecossistema.py`, SKILL.md de pipeline, manifestos); pipeline não declarado deixa o catálogo desatualizado. Teste que planta um pipeline novo e prova que o `G_mapa_pecas` reprova.
- **DoD:** o mapa visual de pipelines mostra exatamente as etapas do contrato; `G_mapa_pecas` e `G_aidd_visual_maps` com exit 0; o teste do T0.4 morde.

### Fase 1 — Registro de estado · ~1 a 2 sessões

- **T1.1** Schema e emissor (seção 7): etapas, harness, LLM, ID da sessão, tempo, `feito`, `log`, `parada`, `humano`, `historico`.
- **T1.2** Registro no ponto de entrada de `ecossistema.py` para os pipelines do contrato que passam por ele (código de saída e saída de texto intactos).

### Fase 2 — Tela · ~2 sessões

- **T2.1** Leitor: execuções registradas + leitura derivada do 4F e da evolução.
- **T2.2** Servidor, página inicial "Pipelines", Kanban genérico que desenha qualquer pipeline do contrato, gaveta em 5 blocos e aba "Arquivo".
- **T2.3** Comando `python ecossistema.py quadro` (apelido `kanban`), documentação e link no Mission Control (no outro repositório, com OK do usuário).

### Fase 3 — Etapa ao vivo, um pipeline por vez · sob demanda

Auditoria 4F e evolução (orquestrador grava cada fase) → Tríades (`orquestrador_sincrono.py` e `PipelineStateManager`) → despacho VSA → run-plan → bateria de gates → ingest, melhoria → plan → orchestrate, ops e pipeline.

### Fase 4 — Alertas e arquivamento · ~1 sessão

- **T4.1** Alertas: execução com pid morto; pasta `../worktrees_*` sem execução viva; mesmo alvo em duas execuções vivas.
- **T4.2** Arquivamento (substitui a limpeza da v1): `python ecossistema.py quadro --arquivar --dias 30` só lista o que compactaria; com `--confirmar`, compacta em `~/.aidd/arquivo/<AAAA-MM>.zip` e remove os originais compactados; a aba Arquivo lê os `.zip`. Nunca toca execução viva; nada some sem `--confirmar`.
- **T4.3** Backup opcional: `--backup` envia o `.zip` do mês para um repositório privado no GitHub, pela API (sem clone local), só com dados resumidos e depois do detector de segredos.
- **DoD:** teste prova que a simulação não apaga nada; teste prova que uma execução arquivada abre na aba Arquivo; teste do backup com servidor falso, sem rede.

### Fase 5 — Custo e ferramentas por execução · sob demanda

- **T5.1** Coletor do Claude Code: ao fim de cada etapa, lê o registro de conversa da sessão (pelo ID gravado) e grava só totais: tokens de entrada e saída, skills e MCPs usados, com `fonte`.
- **T5.2** Outros harnesses (OpenCode, MiMo, Antigravity) e o 9Router, um por vez, só se o formato do registro permitir medir; senão continua "não medido".
- **DoD:** teste com amostra real de registro; cartão mostra "não medido" quando não há fonte.

---

## 9. Servidor e segurança

Rotas somente GET (outro método → 405):

| Rota | Resposta |
|---|---|
| `/`, `/quadro.css`, `/quadro.js` | arquivos de `scripts/quadro/` |
| `/api/pipelines` | página inicial (contagens por pipeline e etapa), com `ETag`; 304 se nada mudou |
| `/api/pipeline/<id>` | um Kanban |
| `/api/execucao/<run_id>` | `estado.json` completo de uma execução (viva ou arquivada) |
| `/api/arquivo?pipeline=&de=&ate=&status=&pagina=` | lista paginada do Arquivo |
| `/api/artefato?cartao=<id>&caminho=<rel>` | texto de um artefato **listado no cartão**, até 512 KB |

Só `127.0.0.1`; cabeçalho `Host` conferido (403 fora disso); artefato fora da lista ou fora do repositório → 404; `Content-Security-Policy: default-src 'self'`, `X-Content-Type-Options: nosniff`, `Cache-Control: no-store`; página montada com `textContent`/`createElement`, nunca `innerHTML` com conteúdo dinâmico (os artefatos são escritos por LLM, e o `G_CYBERSECURITY_OWASP` reprova esse padrão). Instantâneo com 1,5 s de cache; manifestos relidos só se o `mtime` mudar; no máximo 3 chamadas git por instantâneo, mais 1 por execução viva.

---

## 10. O que não fazer e riscos

| Não fazer | Por quê |
|---|---|
| Arrastar cartões, ou botões de aprovar, mesclar ou refazer | o quadro observa; a decisão fica no terminal (Lei #7) |
| SSE ou WebSocket | consulta a cada 2 s resolve, com menos código e sem reconexão |
| Tailwind, marked ou qualquer CDN | sem rede e sem build; a referência também não usa |
| SQLite, `transaction_log` ou `EventBus` | três destinos para o mesmo dado; SQLite com vários processos escrevendo trava no Windows |
| FastAPI ou Flask | dependência nova para poucas rotas GET |
| Código em `src-core` | é núcleo de produto, copiado e vigiado por drift |
| CPU/RAM por cartão | o monitor da porta 8989 já faz isso |
| Acesso remoto ou login | escuta só em 127.0.0.1 |
| Chamar `orca` ou `git status` no quadro | pode derrubar fase / trava o índice do git |
| Copiar logs ou registros de conversa para o arquivo | são o que ocupa espaço; o estado guarda só o caminho (D11) |
| Estimar tokens ou custo | sem medição real, o cartão diz "não medido" (Lei #8) |
| Skill ou slash command novo agora | cada skill custa sync em 6 harnesses e mais gates; o CLI basta |
| Planos de `docs/planos` no quadro | não são execuções; entram depois, se fizer falta |
| Gate novo | os testes e o `G_mapa_pecas` cobrem; a bateria já é longa (D8) |

| Risco | Mitigação |
|---|---|
| `os.replace` falha no Windows com o leitor aberto | 5 tentativas de 50 ms; o leitor lê rápido e, se o JSON vier ilegível, usa o último instantâneo bom |
| Convenções do 4F mudarem | funções importadas do orquestrador + teste com repositório git real |
| Registro derrubar um pipeline | todo erro é engolido e avisado uma vez; teste com emissor quebrado |
| Testes poluírem o quadro real | o emissor não grava sob pytest sem `AIDD_HOME` explícito |
| Cartão "fantasma" (pid morto) ou pid reaproveitado | status `interrompido` + "sem sinal há X min" |
| DNS rebinding / leitura indevida de arquivos | só 127.0.0.1, `Host` conferido, lista branca de artefatos, CSP |
| Contrato e pipelines divergirem | o emissor recusa etapa fora do contrato; o catálogo acusa pipeline não declarado (D0) |
| Doze Kanbans pesarem a página | a página inicial só mostra contagens; cada Kanban carrega só quando é aberto |
| Arquivo crescer | só dados resumidos (5 a 30 KB por execução; mil execuções ≈ 30 MB antes de compactar) |
| Arquivo existir só nesta máquina | backup mensal opcional no GitHub privado (T4.3) |
| Backup vazar segredo | só dados resumidos, detector de segredos antes do envio, repositório privado |
| Formato do registro de conversa mudar (Fase 5) | coletor por harness com teste de amostra real; falhou → "não medido" |
| Escopo inflar | cada fase fecha sozinha; reavaliar antes das Fases 3, 4 e 5 |

---

## 11. Regras de execução (lições deste repositório)

1. **Pré-requisito atendido:** a main está verde desde 08-10-2026 às 18:20 (10a41f82, `python ecossistema.py audit` com exit 0 e 66 aprovados), também no GitHub.
2. Um ticket, um commit; DoD conferido por comando, com o exit code gravado em arquivo (nunca `comando | tail`); o diff do commit é auditado.
3. Nunca `--no-verify`; merge e push só com OK humano.
4. Audit e push com `TEMP`, `TMP` e `TMPDIR` em `C:\Users\trcnologia\aidd-tmp`; logs e scripts de apoio em `C:\Users\trcnologia\aidd-logs` (o limpador da porta 8989 apaga o `%TEMP%`).
5. Ninguém roda `orca orchestration check` durante um ciclo 4F.
6. Antes de editar, conferir se outra sessão está escrevendo na mesma pasta.
7. Pesquisa de código pelo graph primeiro (Lei #14).
8. Os testes novos somam menos de 3 s: a pasta `tests/` leva ~790 s, com teto de 900 s no `G_TESTES_REAIS`.
9. Catálogo, mapas e livro se regeneram na pasta real (`python ecossistema.py derivados regenerar` depois deles); o `visual-maps gerar` sozinho deixa os gates de mapas vermelhos nesta máquina.
10. Este plano (os 3 arquivos em `docs/melhorias/`) entra no git no primeiro commit da Fase 0, junto com o catálogo regenerado: o `.json` dele é contado pelo catálogo.

---

## 12. Próximo passo

`/plan` só com a Fase 0 → execução numa sessão nova, depois dos Blocos 8 e 9 do ciclo-03 da modularização VSA.

---

## Anexo — comparação da v1 com os três planos anteriores

Os três arquivos foram removidos de `docs/melhorias/` em 08-10-2026 por decisão do usuário.

| Ponto | Plano 1 (`dashboard-kanban-pipelines`) | Plano 2 (`dashboard-kanban-tempo-real-pipelines`) | Plano 3 (`dashboard-visual-acompanhamento-pipelines`) | v1 deste plano |
|---|---|---|---|---|
| Primeira entrega útil | só depois de instrumentar os pipelines | idem | idem | quadro já útil sem mudar pipeline |
| Onde fica o estado | `.aidd/execucoes` dentro do repositório | `.aidd/telemetria` dentro do repositório | JSON + SQLite + EventBus | `~/.aidd/execucoes` |
| Onde fica o código | não definido | `src-core` (não existe) | `src-core` (núcleo de produto) | `scripts/` |
| Atualização | consulta a cada 2 s | SSE ou 1 s | SSE + 1 s | consulta a cada 2 s + ETag |
| Gate novo | `G_BOARD_ESTADO` | `G_KANBAN_TELEMETRIA` | `G_KANBAN_TELEMETRIA` | nenhum (testes) |
| Ações no quadro | — | arrastar + aprovar | — | só copiar o comando |
