# Auditoria de Etapa: Planner, passo 1 — bloco Ambiente (Ticket 1 da ETAPA_05)

Primeiro passo da jornada **Ambiente → entrevista (grill) → spec → Mobbin → planner**. Correção feita no clone; o espelho no motor original vem em branch própria (`fix/pure-etapa-08-planner-ambiente`), sem commit antes da aprovação.

### [RECURSO]: Decisões do usuário que moldaram o passo
- **Ordem de Execução:** antes de escrever o teste.
- **Ação Executada:** registro das decisões.
- **Status & Diagnóstico:**
  - *Decisões:* (1) caminhos do Mobbin, **nesta ordem**: 1 = MCP oficial (harness), 2 = chave no `.env`, 3 = nenhum; (2) o deploy exige `VPS_HOST`, `VPS_USER`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ZONE_ID`, `DEFAULT_ROOT_DOMAIN` e `SSH_KEY_PATH` ou `VPS_PASSWORD` (a resposta "AMBAS" foi interpretada como aceitar as duas formas de autenticação; **a confirmar**); (3) o planner lê `CLOUDFLARE_ZONE_ID` e `DEFAULT_ROOT_DOMAIN` do `.env`; (4) o **Coolify é abolido**: deploy só `compose-nativo`, para todos os fluxos (iniciativa própria, abaixo em Tickets); (5) o fato de o deploy real do `compose-nativo` devolver `REAL_NAO_IMPLEMENTADO` foi aceito como ticket.
  - *Falhas / Anomalias:* nenhuma.

### [RECURSO]: Investigação do deploy (antes de fixar a lista de variáveis)
- **Ação Executada:** leitura de `aidd-ops/scripts/pipeline_ops.py` (`DeployOrchestrator`), `core_ops/coolify.py` e da etapa 6 do orquestrador.
- **Status & Diagnóstico:**
  - *Sucesso:* Sim.
  - *Achados:* (a) o `aidd-ops` tem 2 motores: `coolify` (stack pronta de terceiros: Twenty, Chatwoot, Cal.com, Postgres, Uptime Kuma, via API; exige `COOLIFY_BASE_URL` e `COOLIFY_API_TOKEN`) e `compose-nativo` (o `docker-compose.yml` gerado pelo master, via SSH); (b) o `compose-nativo` em modo real **não implementa o deploy**: só testa o SSH e devolve `REAL_NAO_IMPLEMENTADO`, mandando copiar a pasta e rodar `./deploy.sh` à mão; (c) a etapa 6 do orquestrador só roda `ops plan` (planeja, não implanta); (d) o ops só lê do ambiente `CLOUDFLARE_API_TOKEN` e `SSH_KEY_PATH`; host, usuário e domínio chegam por parâmetro.
  - *Falhas / Anomalias:* as variáveis `CLOUDFLARE_ZONE_ID` e `DEFAULT_ROOT_DOMAIN` não são lidas pelo ops; por decisão do usuário passam a ser lidas pelo planner.

### [RECURSO]: Bloco Ambiente (TDD Red-Green)
- **Ordem de Execução:** primeiro o teste (Red), depois o módulo (Green), depois o orquestrador (Red-Green) e a regressão.
- **Ação Executada:**
  1. `tests/test_ambiente.py` (22 testes): detecção de harness, passo a passo só do harness detectado, variáveis de deploy (lista exata do que falta, branco = ausente, SSH por chave ou senha, sem Coolify), `init` sem ambiente reprova listando os 3 caminhos na ordem, gravação sem segredos, nenhum valor de variável na saída, Mobbin que nunca bloqueia (chave ausente, recusada, rede fora do ar), validação por chamada real mínima (1 tela, `standard`), `ambiente.json` corrompido bloqueia o `init`.
  2. Novo `src/core_planner/ambiente.py` (+ re-exportação em `aidd_planner/core/ambiente.py`); `src/cli.py` ganha o subcomando `planner ambiente --pasta P --mobbin 1|2|3` e o `init` passa a verificar o ambiente antes de qualquer outra coisa.
  3. `scripts/test_orquestrador_ambiente.py` (3 testes, em subprocesso para não alterar o catálogo): a etapa 2 do `/pure` para e lista os 3 caminhos se não há ambiente registrado; com `--mobbin` registra o ambiente **antes** do `init`; com ambiente já registrado dispensa a escolha. `scripts/orquestrador_sincrono.py` ganha `--mobbin`.
  4. Regressão: `tests/conftest.py` do planner recebe uma fixture que parte do ambiente já satisfeito para os testes de **outros** assuntos (o bloqueio de verdade está só em `test_ambiente.py`); `tests/test_orquestrador_contratos_reais.py` passa `mobbin="3"`, injeta as variáveis de deploy por `monkeypatch` (o teste não depende do `.env` de quem roda) e registra o ambiente antes do `init` real.
- **Entrega / Artefato Gerado:** `.aidd/ambiente.json` por projeto, sem segredo (harness, caminho do Mobbin, se foi validado, motor `compose-nativo` e a lista de variáveis exigidas).
  - *Caminho Exato (100% concluído):* `modulos/01-governanca-e-qualidade/core/aidd-planner/src/core_planner/ambiente.py`, `src/cli.py`, `tests/test_ambiente.py`, `tests/conftest.py`; `scripts/orquestrador_sincrono.py`, `scripts/test_orquestrador_ambiente.py`; `tests/test_orquestrador_contratos_reais.py`.
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. Red: `test_ambiente.py` exit 2 (módulo inexistente) e os 3 do orquestrador exit 1; depois da regressão natural, 24 testes antigos do planner reprovaram (exit 1) e 11 do orquestrador, o que provou o bloqueio; Green: `test_ambiente.py` **22 passed**; planner completo **70 passed**; orquestrador (`contratos_reais` + `sincrono`) **29 passed**; `scripts/test_orquestrador_ambiente.py` e `test_orquestrador_sincrono_dryrun.py` **4 passed**; guarda do Next e `test_gitignore_env` passam (8 passed no conjunto).
  - *Prova real (sem mocks, com o `.env` do clone):* `planner ambiente --mobbin 1` → exit 0, imprime o passo a passo do Claude Code (`claude mcp add --transport http mobbin https://api.mobbin.com/mcp` e `/mcp`); `--mobbin 2` → exit 0, **chave aceita pelo Mobbin** (chamada real) e `validado: true`; `--mobbin 3` → exit 0; sem escolha → exit 1 com os 3 caminhos na ordem; `planner init` com ambiente → exit 0 (Design System gerado), sem ambiente → exit 1; `pure ... --dry-run` → exit 0. Varredura de vazamento: nenhuma ocorrência da chave do Mobbin nem do token da Cloudflare nas saídas e nos arquivos gerados.
  - *Falhas / Anomalias:*
    - *Ocorrência:* o harness do passo a passo para OpenCode, MiMoCode e Antigravity foi escrito pela documentação de cada um e está marcado **não verificado** no próprio texto; só o Claude Code foi exercitado.
    - *Ocorrência:* ao rodar o `init` real, o clone mostrou `.mcp.json`, `.agents/mcp_config.json` e `mimocode.jsonc` modificados (apenas o `cwd` dos MCPs, de um worktree antigo para o clone), com data de **antes** desta etapa; não vêm deste passo e não são espelhados no original.
    - *Correção minha:* escrevi no rascunho que a suíte "passou de 2 s para 45 s" por causa da fixture; é falso. Os 2 s eram da rodada em que 24 testes reprovaram logo no início do `init`; a suíte completa com os 70 testes leva ~45 s por si (teste de `init` com `git`/gates). Sem relação com este passo.

### [RECURSO]: Espelho no motor original (Ticket 8-E)
- **Ordem de Execução:** após a prova no clone.
- **Ação Executada:** branch `fix/pure-etapa-08-planner-ambiente` a partir da `main` (alterações locais alheias guardadas no `git stash`); patch gerado no clone com `git diff` e aplicado com `git apply`; suítes; regeneração (catálogo, `derivados regenerar`, mapas/livro/PDF/manifesto, baseline de segredos); gates individuais; seção 17 no relatório E2E (Lei #9); commit com hooks ligados; push com `pre-push`.
- **Entrega / Artefato Gerado:** commit `72907cf1` (`feat(planner): bloco Ambiente abre o planner...`), no GitHub em `origin/fix/pure-etapa-08-planner-ambiente`; `main` remota intacta em `89b4facc`.
- **Status & Diagnóstico:**
  - *Sucesso:* Sim, na segunda tentativa. No original: planner **70 passed**, orquestrador **32 passed**; `G_mapa_pecas`, `G_aidd_visual_maps`, `G_DRIFT_NUCLEO_COMPARTILHADO`, `G_HANDOFF_MELHORIA`, `G_DISCIPLINA_TESTE_FERRAMENTA` e `G_SEGREDOS` com exit 0; commit com todos os gates do pre-commit (exit 0); push com `pre-push` (exit 0).
  - *Falhas / Anomalias:*
    - *Ocorrência (erro meu):* a primeira tentativa de commit reprovou (exit 1), e a notificação de "exit 0" da tarefa em segundo plano era só do último comando do script; li o exit real do arquivo. Dois motivos: (1) `G_SEGREDOS` acusou 3 valores falsos de teste em `test_ambiente.py` (`cf-token-secreto-123`, `mbn_chave_secreta_...`, `"senha"`), resolvidos com `# pragma: allowlist secret` (no clone e no original); (2) `G_HARNESS_COMPAT`, `G_COMPONENTE_AGNOSTICO` e `G_PORTAO_PROVA_QUE_MORDE` reprovaram porque os espelhos locais `.codebuddy/skills/` (ignorados pelo git) das skills `aidd-frontend-forms`, `aidd-open` e `aidd-pure` estavam com a versão da branch da etapa 06 (sem Next.js), enquanto esta branch parte da `main` (fonte com Next.js).
    - *Localização Exata do Erro:* `tests/test_ambiente.py:28,32,86`; `.codebuddy/skills/{aidd-frontend-forms,aidd-open,aidd-pure}/SKILL.md` (locais, não versionados).
  - *Ação Corretiva Cirúrgica:* pragmas nos 3 valores; os 3 espelhos restaurados com `git show HEAD:componentes/compartilhado/skills/<skill>/SKILL.md`.
  - *Consequência a lembrar:* os espelhos `.codebuddy/` acompanham a branch em que a pasta está. **Ao voltar para a etapa 06, ou depois do merge na `main`, copiar de novo a fonte da branch ativa para esses 3 arquivos**, ou `G_HARNESS_COMPAT` reprova.
  - *Alterações locais alheias:* `PLANO-EXECUCAO-ESTRUTURADO.json` e `docs/testes/status_testes_ferramentas.json` reaparecem modificados depois dos testes e da regeneração; foram deixados de fora do commit.

## TICKETS

### Ticket 8-A: Abolir o Coolify e fechar o deploy `compose-nativo` — ABERTO (decisão do usuário)
- **Falha:** o `aidd-ops` mantém o motor `coolify` (`core_ops/coolify.py`, `pipeline_ops.py`, intake web, testes, docs, `.env.example` com `COOLIFY_*`) e o deploy real do `compose-nativo` devolve `REAL_NAO_IMPLEMENTADO`.
- **Artefato de Handoff:** `modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops/` (`scripts/pipeline_ops.py`, `src/core_ops/coolify.py`, `apps/intake/`, `GUIA.md`), `.env.example`, docs vivas e skills.
- **Requisito TDD (Red):** guarda `tests/test_sem_coolify_vivo.py` (mesmo desenho do `test_sem_nextjs_vivo.py`) reprova os rastros; teste que roda `deploy --motor compose-nativo` real contra um SSH simulado e afirma cópia dos arquivos e `docker compose up -d --build` remoto (hoje: `REAL_NAO_IMPLEMENTADO`).
- **Implementação Técnica:**
  - Remover o motor Coolify e tudo que o cita; `compose-nativo` vira o único motor, com deploy real (copiar o projeto, `docker compose up -d --build` pelo `SSHRunner`) e o preflight já existente.
  - Etapa 6 do orquestrador passar de `ops plan` para plano + deploy (a decidir com o usuário, pois deploy real mexe na VPS).
- **Verificação (Green):** guarda e testes do ops com exit 0; audit do original sem gate vermelho.
- **Construtor Prompt (EN):**
  - Remove the Coolify deploy engine and every live reference, make compose-native the only engine with a real SSH deploy (copy project, remote `docker compose up -d --build`), write a guard test like the Next.js one, and run the ops suite asserting exit 0.

### Ticket 8-B: Confirmar "AMBAS" e o limite do `SSH_KEY_PATH ou VPS_PASSWORD` — ABERTO
- **Falha:** a resposta do usuário foi lida como "aceita chave ou senha"; se a intenção era exigir as duas, a regra muda.
- **Artefato de Handoff:** `ambiente.py` (`VARIAVEIS_DEPLOY_OBRIGATORIAS`) e `tests/test_ambiente.py`.
- **Requisito TDD (Red):** a definir após a confirmação.
- **Implementação Técnica:** confirmar com o usuário; ajustar a lista e os testes se preciso.
- **Verificação (Green):** `pytest tests/test_ambiente.py` com exit 0.
- **Construtor Prompt (EN):**
  - Ask the user whether SSH auth requires the key, the password, or either; adapt the required-variable list and its tests accordingly.

### Ticket 8-C: Documentar o bloco Ambiente (parte do Ticket 6 da ETAPA_05) — ABERTO
- **Falha:** a skill `aidd-planner`, o comando `planner.md`, o `GUIA.md` e o `AGENTS.md` do planner não citam `planner ambiente`, `--mobbin` nem os 3 caminhos; o `.env.example` não diz que as 6 variáveis de deploy bloqueiam o planner.
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-planner/SKILL.md`, `componentes/compartilhado/comandos/planner.md`, `.env.example`, docs do planner, `docs/teste-end-to-end/relatorio-teste-end-to-end.md` (Lei #9).
- **Requisito TDD (Red):** teste de documentação que exige a menção a `planner ambiente` e à ordem 1/2/3 na skill.
- **Implementação Técnica:** documentar; regenerar espelhos e catálogo no original.
- **Verificação (Green):** teste e gates de skill/harness com exit 0.
- **Construtor Prompt (EN):**
  - Document `planner ambiente`, `--mobbin 1|2|3` (MCP, key, none) and the deploy variables in the planner skill, command, guide and `.env.example`, then regenerate mirrors and run the skill gates asserting exit 0.

### Ticket 8-D: Passo a passo por harness — ABERTO
- **Falha:** OpenCode, MiMoCode e Antigravity têm passo a passo escrito pela documentação, sem teste em máquina; o Gemini CLI não é detectado (foi substituído pelo Antigravity CLI em 18/06/2026; ver Ticket 8 da ETAPA_05).
- **Artefato de Handoff:** `ambiente.py` (`_PASSOS_MCP`, `_MARCADORES_HARNESS`), `manifesto_harnesses.json`.
- **Requisito TDD (Red):** a definir após decidir se o `gemini-cli` permanece.
- **Implementação Técnica:** testar cada harness quando houver acesso; atualizar a lista.
- **Verificação (Green):** gates de harness com exit 0.
- **Construtor Prompt (EN):**
  - Verify the Mobbin MCP setup steps for OpenCode, MiMoCode and Antigravity on a real install, remove the "unverified" marks, and align the harness detection list with the manifest.

### Ticket 8-E: Espelhar no motor original — RESOLVIDO (commit `72907cf1`, branch `fix/pure-etapa-08-planner-ambiente`)
- **Falha:** a correção existe só no clone.
- **Artefato de Handoff:** os arquivos listados acima.
- **Requisito TDD (Red):** `pytest` do planner e do orquestrador no original com a fixture ausente reprova o `init`.
- **Implementação Técnica:** branch `fix/pure-etapa-08-planner-ambiente` a partir da `main`, aplicar o patch, regenerar catálogo, mapas, livro e baseline, rodar os gates e o audit; **commit e push só com a aprovação**.
- **Verificação (Green):** gates e audit com exit 0.
- **Construtor Prompt (EN):**
  - Branch from main, apply the planner/orchestrator patch, regenerate the catalog, maps, book and secrets baseline, run the gates and the audit, and only then ask for approval to commit and push.
