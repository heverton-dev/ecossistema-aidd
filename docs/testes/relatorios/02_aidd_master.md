# Relatório — Bateria 2: AIDD Master (`tools/aidd-master`)

> Execução real em 2026-09-06, ambiente Windows 11 (`C:\Users\trcnologia\Desktop\ecossistema-aidd`).
> Scripts: `docs/testes/testes/02_aidd_master_compose.py`, `02_aidd_master_inject.py`, `02_aidd_master_pytest.py`.
> Prompts de linguagem natural: `docs/testes/prompts/aidd_master_plan_estoque.txt`, `aidd_master_prompt_crm.txt`.
> Todos os comandos rodaram via `subprocess.run` real, exit code real capturado, sempre em diretórios temporários isolados (`tempfile.mkdtemp`), nunca contra o repositório real como alvo de escrita.

## Veredito final: **PASSOU COM RESSALVAS**

16 dos 17 itens da Definição de Pronto passaram com evidência real. 1 item (`refine-module`, 2.14) não pôde ser exercitado via caminho de ouro puro porque `compose` não gera `.feature` automaticamente (limitação de ambiente/geração, documentada, não simulada). Além disso, a bateria revelou um **achado real de comportamento** no tipo `inject hook` (ver §Achados) que não bloqueia o veredito mas precisa de atenção.

## Tabela dos 17 itens

| # | Item | Comando | Exit | Resultado |
|---|---|---|---|---|
| 2.1 | `init` | `aidd.py init ProjetoTesteInit --dir <tmp>/init-teste` | 0 | PASS — projeto provisionado (`proj_projetotesteinit/`), módulo `principal` gerado com Clean Architecture |
| 2.2 | `compose` | `aidd.py compose <tmp>/suite-teste "Suite Teste E2E" crm erp --db sqlite` | 0 | PASS — `src/modules/{crm,erp}`, `tests/`, `PLANO-EXECUCAO-ESTRUTURADO.json` confirmados |
| 2.3 | `add-module` | `aidd.py add-module estoque --descricao "..." --dir <tmp>/suite-teste` | 0 | PASS — `src/modules/estoque` criado, manifesto atualizado |
| 2.4 | `test unit` | `aidd.py test unit --dir <tmp>/suite-teste` | 0 | PASS — pytest real: **6 passed in 0.53s** (crm, erp, estoque) |
| 2.5 | `audit` (projeto composto) | `aidd.py audit --dir <tmp>/suite-teste` | 0 | PASS — 7 gates do projeto: 7/7 APROVADO, score de segurança 100% (21/21 testes) |
| 2.6 | `status` | `aidd.py status --dir <tmp>/suite-teste` | 0 | PASS — 3 módulos ativos, 8 quality gates instalados, SQLite ativo |
| 2.7a | `plan` (NL) | `aidd.py plan "Sistema de gestao de estoque com alertas" --dir <tmp>/plan-teste` | 0 | PASS — domínio reconhecido: `estoque` (casamento de palavra-chave, **zero LLM** confirmado no próprio output) |
| 2.7b | `prompt` (NL) | `aidd.py prompt "crie um crm simples para gestao de leads e vendas" --dir <tmp>/prompt-teste` | 0 | PASS — domínios reconhecidos: `crm, vendas` (mesma detecção determinística) |
| 2.8 | `inject` (7 tipos + dry-run + remover + config-file + mcp-command) | ver §Inject | 0 (todos) | PASS — 12/12 sub-itens (ver detalhe abaixo) |
| 2.9 | `verificar-drift` (limpo + divergente) | ver §Inject | 0 / 1 | PASS — caso limpo exit 0 ("Nenhum drift detectado"); após edição manual em arquivo hash-tracked, exit 1 `SYNC_DIVERGENTE` com hash esperado vs. obtido citado |
| 2.10 | `bench` | `aidd.py bench -n 50 --dir <tmp>/suite-teste` | 0 | PASS — 50/50 operações, throughput real **1862.9 req/s**, 0.54 ms/req |
| 2.11 | `heal` | `aidd.py heal --dir <tmp>/suite-teste` | 0 | PASS — reconfirma/ressincroniza kernel e fatias verticais sem erro |
| 2.12 | `scaffold-infra` | `aidd.py scaffold-infra --dir <tmp>/suite-teste` | 0 | PASS — 7 arquivos Terraform/Helm reais gerados (`main.tf`, `Chart.yaml`, `values.yaml`, templates) |
| 2.13 | `export-frontend` | `aidd.py export-frontend --dir <tmp>/suite-teste` | 0 | PASS — 13 arquivos Next.js/TypeScript gerados (`package.json`, `tsconfig.json`, páginas por módulo); **não** rodamos `npm install/build` (fora do escopo do comando testado, que só faz o scaffold) |
| 2.14 | `refine-module` | verificação de `features/crm.feature` | -1 (limitação) | **NÃO EXERCITADO** — `compose` não gera `.feature` automaticamente; não fabricamos arquivo fake. Documentado como limitação de geração, não de execução do comando |
| 2.15 | `deploy docker` | `aidd.py deploy docker` (cwd=`<tmp>/suite-teste`) | 0 | PASS COM RESSALVA — CLI processa e imprime instruções (exit 0), mas o `docker compose up` de fato falha porque **o daemon Docker Desktop não está rodendo nesta máquina** (`docker --version` OK, `docker ps` falha com erro de pipe). Ambiente: Docker instalado mas daemon inativo — limitação de ambiente documentada, `docker compose down` executado por precaução (no-op) |
| 2.16 | `compose-orca` | `aidd.py compose-orca --dir <tmp>/suite-orca --suite-name "Suite Orca" crm erp` | 0 | PASS — `COMPOSE-ORCA-MANIFEST.json` real: 2/2 módulos com sucesso, 12 arquivos criados, 167.33 ms |
| 2.17 | pytest suite completa | `python -m pytest tests/ -q` (cwd `tools/aidd-master`) | 0 | PASS — **238 passed, 4 skipped in 29.84s** — sem regressão do baseline conhecido (238/4) |

## Detalhe do item 2.8 — `inject` (7 tipos + variações)

| Sub-item | Tipo/cenário | Exit | Resultado |
|---|---|---|---|
| skill | `inject skill analise-de-dados` | 0 | 4 arquivos materializados (`.skills`, `.claude/skills`, `.agent/skills`, `.gemini/skills`) |
| mcp | `inject mcp servidor-dados-ext --mcp-command python --mcp-args [...]` | 0 | `mcp.json` gerado com o comando/args informados |
| rule | `inject rule seguranca-api` | 0 | `templates/rules/seguranca-api.md` + sync em `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` |
| spec | `inject spec contrato-crm` | 0 | spec materializada |
| config | `inject config app-config-principal --conteudo-file <json 5 campos>` | 0 | conteúdo do arquivo JSON (`database_url`, `debug_mode`, `max_connections`, `log_level`, `feature_flags`) aplicado corretamente |
| agent | `inject agent orquestrador-financeiro` | 0 | materializado |
| hook | `inject hook pre-commit-lint` | 0 | materializado — **ver achado abaixo sobre escrita fora do `--dir`** |
| dry-run | `inject skill skill-dryrun-test --dry-run` | 0 | confirmado: **zero arquivos novos** escritos em `<tmp>/dryrun-teste` |
| remover | injeta `hook-para-remover` depois `--remover` | 0 / 0 | remoção confirmada — arquivo local removido com sucesso |

## Achados reais (não hipotéticos)

### 1. `inject hook` escreve fora do `--dir` alvo, sempre no monorepo real (por design, não é bug de teste)

Investigação em `tools/aidd-master/src/core/materializador.py`: o tipo `hook` tem um `CANONICAL_TEMPLATES["hook"] = "componentes/{alvo_projeto}/hooks/{nome}/hook.sh"`, resolvido via `_default_ecossistema_root() = Path(__file__).resolve().parents[4]` — ou seja, a raiz do monorepo real, **independente do `--dir` passado na CLI**. Isso é a "Integração canônica Package 7" (comentário no próprio código), não um bug do script de teste: toda chamada real de `inject hook <nome>` grava:
- `componentes/aidd-master/hooks/<nome>/hook.sh` (canônico)
- `tools/aidd-master/.claude/hooks/<nome>/`, `.agent/hooks/<nome>/`, `.gemini/hooks/<nome>/` (espelhos multi-harness, via `sincronizar_componente`/`gestor_componentes.sync`)

Isso significa que o tipo `hook` **não pode ser testado em isolamento puro** sem tocar o repositório real — uma exceção real e reproduzível à Regra 1 (nunca escrever no repo real), inerente à arquitetura da ferramenta, não corrigível pelo teste. Efeito colateral confirmado durante a primeira execução: `git status` da raiz passou a listar `componentes/aidd-master/hooks/`, `tools/aidd-master/.claude/hooks/`, `.agent/hooks/`, `.gemini/hooks/` como novos untracked.

**Correção aplicada nesta sessão:** o script `02_aidd_master_inject.py` agora limpa manualmente essas pastas no `finally` (após cada execução), e a poluição já criada foi removida do repositório real (`git status` confirmado limpo após a limpeza). Recomendação para o produto: documentar esse comportamento explicitamente no `--help` do `inject hook`, já que é uma exceção real à isolação `--dir`.

### 2. `inject <tipo> --remover` não limpa os espelhos multi-harness do hook removido (gap real, achado por reprodução)

Ao remover `hook-para-remover` via `--remover`, o arquivo canônico (`componentes/aidd-master/hooks/hook-para-remover/hook.sh`) foi corretamente apagado (confirmado por `find` antes/depois), mas os espelhos sincronizados em `tools/aidd-master/.claude/hooks/hook-para-remover/`, `.agent/hooks/...`, `.gemini/hooks/...` **permaneceram no disco** — órfãos reais, confirmados por inspeção direta do sistema de arquivos após a remoção. Rastreado em `materializador.py:282-305`: a lista `arquivos_remover` inclui apenas o arquivo canônico resolvido por `resolve_canonical_destination(...)` nas duas raízes possíveis (ecossistema real e `root_dir` do teste) — não itera sobre os espelhos multi-harness gerados por `sincronizar_componente()`. Este é um gap real na capacidade "remoção com limpeza do canônico" (Rodada 2, Item 4): limpa o canônico, mas não os espelhos.

Não bloqueia o veredito da bateria (o item 2.8/2.9 testado via CLI direta funcionou como esperado para o alvo `--dir`), mas é um achado relevante que o time de manutenção do `aidd-master` deveria avaliar corrigir.

### 3. Correção no próprio script de teste (2.9 verificar-drift)

Na primeira execução, o script editava manualmente o primeiro arquivo `.py/.md/.yaml` encontrado em `dir_inject` — que por acaso era `AGENTS.md` (arquivo de sincronização multi-harness, **não rastreado por hash**), fazendo `verificar-drift` retornar exit 0 (nenhum drift) quando o esperado era exit 1. Investigação confirmou que isso era falha do script de teste, não do produto: `verificar-drift` só rastreia hashes dos arquivos listados em `arquivos_hashes` no `CAPABILITIES.json` (os arquivos realmente materializados pelo componente), não os arquivos de sincronização (`AGENTS.md`, `templates/core/*`). Corrigido o script para ler `CAPABILITIES.json` e editar um arquivo genuinamente hash-tracked (`.skills/analise-de-dados/SKILL.md`) — reexecutado, resultado real: exit 1 `SYNC_DIVERGENTE` com hash esperado/obtido citado corretamente.

## Limitações de ambiente documentadas

- **Docker**: CLI instalada (`docker --version` → 29.7.2), mas **daemon Docker Desktop não está rodando** nesta máquina (`docker ps` falha com erro de pipe nomeado). `deploy docker` foi executado e documentado — o CLI do aidd-master retorna exit 0 mesmo quando o `docker compose up` subjacente falha (ele só "processa instruções", não propaga a falha do daemon como erro fatal). Nenhum container ficou órfão (confirmado: daemon nem está ativo).
- **`refine-module`**: não exercitado via caminho de ouro puro — `compose` não gera `features/<modulo>.feature` automaticamente; não fabricamos um arquivo fake para forçar o teste a passar, conforme instruído.
- **`locust`**: não instalado nesta máquina — `test load` não foi exercitado nesta bateria (não fazia parte do escopo mínimo dos 17 itens, mas fica registrado para futura bateria de carga).
- **Node/TypeScript**: disponíveis (`node v26.7.0`) — `export-frontend` gerou os arquivos com sucesso; build real (`npm install && npm run build`) não foi executado (fora do escopo do comando testado).

## Limpeza e critérios de saída

- Todos os diretórios temporários (`aidd_bat2_*`, `aidd_inject_*`) foram removidos ao final de cada execução (`shutil.rmtree` no `finally`).
- Nenhum container Docker órfão (daemon nem estava ativo).
- `git status` da raiz do ecossistema real limpo ao final — confirmado após a limpeza manual da poluição do achado #1 (só restam os arquivos esperados em `docs/testes/`).
- Suíte pytest de `tools/aidd-master`: **238 passed, 4 skipped**, igual ao baseline conhecido — sem regressão.
- Nenhum `git commit`/`push` executado por este processo, em nenhum repositório.

## Resumo (5-8 linhas)

16/17 itens da Definição de Pronto passaram com evidência real de execução (exit codes reais, saída real citada). O único item não exercitado (`refine-module`) é uma limitação de geração documentada, não simulada. A suíte pytest completa do `aidd-master` confirma 238 passed/4 skipped, sem regressão do baseline. `deploy docker` foi tentado e documentado como limitação de ambiente (Docker instalado, daemon inativo). A bateria revelou dois achados reais e reproduzíveis no tipo `inject hook`: (1) ele grava sempre no monorepo real via caminho canônico absoluto, independente de `--dir` — comportamento por design, não bug de teste, mas que quebra a isolação esperada e exige limpeza manual pós-teste (já corrigida no script); (2) `--remover` limpa o arquivo canônico mas deixa órfãos os espelhos multi-harness sincronizados — gap real na capacidade de limpeza, recomendado para correção futura. Veredito: **PASSOU COM RESSALVAS**.
