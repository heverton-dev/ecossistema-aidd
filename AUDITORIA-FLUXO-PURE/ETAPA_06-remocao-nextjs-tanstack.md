# Auditoria de Etapa: Remoção do Next.js e geração em TanStack Router + Vite (passos 1 a 4)

Decisões do usuário: excluir tudo de Next.js; padrão = **TanStack Router + Vite como SPA** (build estático servido por nginx, offline-first); documentos históricos datados ficam como estão; manuais e protocolos vivos são atualizados; livros e catálogo são regenerados pelas ferramentas. **Todo o trabalho abaixo está no clone `FLUXO-PURE`, sem commit. O espelhamento no motor original ainda NÃO foi feito** (Ticket R10).

### [RECURSO]: Mapeamento do Next.js (passo 0, somente leitura)
- **Ordem de Execução:** após a decisão do usuário de abolir o Next.js.
- **Ação Executada:** `git grep` por Next.js em todo o repositório rastreado; leitura do `nextjs_exporter.py`, do `tanstack_exporter.py` antigo, dos 11 testes do exportador e dos chamadores.
- **Entrega / Artefato Gerado:** diagnóstico.
  - *Caminho Exato (100% concluído):* `C:\Users\trcnologia\aidd-tmp\next_files.txt` (lista dos 203 arquivos).
- **Status & Diagnóstico:**
  - *Sucesso:* Sim.
  - *Falhas / Anomalias:*
    - *Ocorrência:* 203 arquivos rastreados citam Next.js (~120 históricos, 19 espelhos de harness, ~60 vivos). O gerador real ainda era `NextJSExporter` (782 linhas, **3 cópias** idênticas em `componentes/`, `aidd-master/src/core` e `aidd-enterprise/src/core`), usado por `compose_suite`, `add_module` (master e enterprise), `provision_project` e `export_frontend`. O `tanstack_exporter.py` (76 linhas, com "Abolição formal e definitiva do Next.js" no cabeçalho) só copiava um template de 10 arquivos **sem** `vite.config`, `index.html`, `tsconfig` nem rotas, e só o `aidd-open` o usava. Havia ainda um **segundo** gerador (`export-frontend` em `openapi_to_ts.py`, 2 cópias) e um **terceiro** (`aidd-open/frontend_generator.py`, sem nenhum chamador). `provision_project` com `frontend_stack='tanstack'` já era o padrão, mas apenas copiava o template estático `templates/v2/frontend`, e o `add_module` nunca regenerava páginas para projetos TanStack. Contradições: `AGENTS.md:131` e skill `aidd-pure:38` dizem Next.js; o docstring de `G_STACK_PADRAO_OURO` lista Next.js como stack obrigatória. O teste de build do Next ficava **pulado** nesta máquina (Node 26 fora da faixa 18-22).
    - *Localização Exata do Erro:* `componentes/compartilhado/src-core/nextjs_exporter.py`; `aidd-master/scripts/{compose_suite,add_module,provision_project,openapi_to_ts,aidd}.py`; `aidd-enterprise/scripts/...`; `aidd-open/src/core_open/{frontend_generator,vsa_generator}.py`.
  - *Ação Corretiva Cirúrgica:* passos 1 a 4 abaixo.

### [RECURSO]: Passo 1-2, novo `TanStackRouterExporter` (TDD Red-Green)
- **Ordem de Execução:** após o mapeamento.
- **Ação Executada:** (Red) `aidd-master/tests/unit/test_tanstack_exporter.py` com 13 testes portados dos 11 do Next mais "nenhum arquivo gerado menciona Next.js" e "libs offline-first incluídas"; falhou (exit 1, o exportador antigo não devolvia `modules`). (Green) reescrita de `componentes/compartilhado/src-core/tanstack_exporter.py` (828 linhas): os componentes React neutros (Modal, ConfirmDialog, FormField, ícones, página de módulo) foram reaproveitados do exportador Next por script; foram reescritos `package.json`, `vite.config.ts`, `tsconfig.json`, `tailwind.config.ts`, `postcss.config.js`, `index.html` (script anti-flash de tema), `src/main.tsx`, `src/router.tsx` (rotas em código, sem plugin), `Navbar` (TanStack `Link`), `api-client` (`VITE_API_URL`), `Dockerfile` (build + nginx na porta 3000), `nginx.conf` (`try_files $uri /index.html`). Copia as libs offline-first do template padrão-ouro (`pwa`, `seguranca`, `banco`, `sync-queue`, `use-mobile`).
- **Entrega / Artefato Gerado:** exportador novo e teste.
  - *Caminho Exato (100% concluído):* `componentes/compartilhado/src-core/tanstack_exporter.py` e `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/tests/unit/test_tanstack_exporter.py`.
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. Os testes do exportador passam (14, contando o do healthcheck do Passo 4), incluindo `npm install`, `tsc --noEmit` e `vite build` reais.
  - *Falhas / Anomalias:*
    - *Ocorrência:* a busca do template quebraria dentro de projeto gerado (sem o repositório); resolvido com busca em dois locais (`componentes/.../frontend-tanstack` ou `templates/frontend-tanstack` ao lado de `scripts/`).
    - *Localização Exata do Erro:* `tanstack_exporter.py::_copiar_libs_offline`.
  - *Ação Corretiva Cirúrgica:* busca em candidatos; `compose_suite` copia o template para o projeto gerado.

### [RECURSO]: Passo 3a/3b, chamadores no master e no enterprise
- **Ordem de Execução:** após o exportador.
- **Ação Executada:** `tanstack_exporter.py` incluído em `src-core/MANIFEST.json` e copiado byte a byte para master e enterprise por `components`/`src-core/sync.py`; troca em `compose_suite` (default `frontend_stack="tanstack"`), `add_module` (master e enterprise), `provision_project` (usa o exportador; antes copiava template estático), `aidd.py`, `export_frontend.py` e `openapi_to_ts.py` (o `export-frontend` agora chama o exportador e grava os tipos OpenAPI em `src/types.ts`); `ValueError` explícito para `frontend_stack` fora de `tanstack|python-html` (teste Red falhou antes; Green passou). Testes antigos que codificavam o contrato Next foram atualizados nos dois módulos. `CATALOGO.json`: selo do `MANIFEST.json` atualizado e `tanstack_exporter.py` catalogado; baseline do drift atualizado (o `openapi_to_ts` passou de "divergente" para "idêntico" nas duas cópias).
- **Entrega / Artefato Gerado:** chamadores trocados.
  - *Caminho Exato (100% concluído):* `aidd-master/scripts/*.py`, `aidd-enterprise/scripts/*.py`, `componentes/compartilhado/CATALOGO.json`, `modulos/04-nucleo-compartilhado/contracts/baseline_nucleo_compartilhado.json`.
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. Suíte completa do master **466 passed, 4 skipped** (exit 0); suíte completa do enterprise exit 0; `G_DRIFT_NUCLEO_COMPARTILHADO` exit 0.
  - *Falhas / Anomalias:*
    - *Ocorrência:* `test_cmd_setup_diagnostico_completo_com_pip_isolado` falha **só** quando roda em uma combinação específica de 4 arquivos; falha também no motor original sem nenhuma mudança minha, e passa sozinho e na suíte inteira. É defeito antigo de isolamento entre testes (Ticket R6). Os dois módulos têm `tests/conftest.py` de mesmo nome e não rodam na mesma sessão do pytest (executados separadamente).
    - *Localização Exata do Erro:* `aidd-master/tests/unit/test_cli_commands.py::test_cmd_setup_diagnostico_completo_com_pip_isolado`.
  - *Ação Corretiva Cirúrgica:* nenhuma de código (não é da troca de stack).

### [RECURSO]: Passo 3c, `aidd-open`
- **Ordem de Execução:** após master e enterprise.
- **Ação Executada:** removidos `frontend_generator.py` e os 4 templates `.j2` de Next (`gerar_frontend` não tinha nenhum chamador); `vsa_generator`: default `"tanstack"`, rejeição de stack inválida (`FRONTEND_STACK_INVALIDA`), `tecnologia` do contrato C3 sempre `tanstack_router`; fase 09 e `G_FACTORY_INTEGRATION`: `next` nas dependências reprova como "abolido" e frontend TanStack exige `vite.config.ts`, `tsconfig.json`, `index.html`, `src/main.tsx`, `src/router.tsx`. `tests/test_frontend_stack_tanstack.py` (7 testes; Red com 5 falhas).
- **Entrega / Artefato Gerado:** `aidd-open` sem Next.js.
  - *Caminho Exato (100% concluído):* `modulos/02-triade-motores/fluxo-02-open/core/aidd-open/`.
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. **28 passed** (exit 0).
  - *Falhas / Anomalias:*
    - *Ocorrência:* nenhuma.
    - *Localização Exata do Erro:* N/A.
  - *Ação Corretiva Cirúrgica:* N/A.

### [RECURSO]: Passo 4, infraestrutura e prova com Docker
- **Ordem de Execução:** após o `aidd-open`.
- **Ação Executada:** molde `docker-compose.yml` (serviço `web` com build arg `VITE_API_URL`, healthcheck com `wget`), comentários do `nginx.conf` do molde, comentário do dimensionamento do `aidd-ops`; selos do `CATALOGO.json` atualizados. **Prova real:** o `compose_suite` gerou o frontend de um projeto com 2 módulos; `docker build` exit 0; container na porta 3000; `/`, `/pedidos`, `/clientes` e uma rota inexistente devolveram **200** (fallback de SPA), ativo `/assets/*.js` 200 com cache de 1 ano.
- **Entrega / Artefato Gerado:** infra para build estático.
  - *Caminho Exato (100% concluído):* `componentes/compartilhado/moldes/infra/docker-compose.yml`, `nginx/nginx.conf`; `tanstack_exporter.py` (Dockerfile).
- **Status & Diagnóstico:**
  - *Sucesso:* Sim, após correção.
  - *Falhas / Anomalias:*
    - *Ocorrência:* na primeira prova o container ficou `unhealthy`: o `wget http://localhost:3000` do healthcheck resolve `localhost` para IPv6 (`::1`) e o nginx só escuta em IPv4 (`Connection refused`). Só o teste com container mostrou isso.
    - *Localização Exata do Erro:* `Dockerfile` gerado por `tanstack_exporter.py` (linha do `HEALTHCHECK`) e `moldes/infra/docker-compose.yml:35`.
  - *Ação Corretiva Cirúrgica:* Red (`test_healthcheck_usa_ipv4_explicito` falhou) e Green (`127.0.0.1` no Dockerfile e no molde; selos do catálogo atualizados; `sync.py` reaplicado). Segunda prova: container **healthy**, 0 falhas; container, imagem e pasta temporária removidos.
  - *Não verificado:* `nginx -t` isolado e o compose completo (backend Python + nginx de borda + frontend juntos).

## TICKETS

### Ticket R1: `NextJSExporter` como gerador real, TanStack raso (Refere-se a Lei #11) — RESOLVIDO NO CLONE
- **Falha:** a abolição estava declarada mas o gerador de master/enterprise ainda produzia Next.js.
- **Artefato de Handoff:** `componentes/compartilhado/src-core/tanstack_exporter.py`
- **Requisito TDD (Red):** `pytest test_tanstack_exporter.py` exit 1.
- **Implementação Técnica:**
  - Novo `TanStackRouterExporter` (rotas em código, nginx, offline-first, `VITE_API_URL`).
- **Verificação (Green):** testes do exportador exit 0, incluindo build real.
- **Construtor Prompt (EN):**
  - Implement a TanStack Router + Vite exporter that reproduces the old Next exporter contract, with code-defined routes and a static nginx Dockerfile; run `python -m pytest .../test_tanstack_exporter.py` and assert exit 0.

### Ticket R2: Chamadores presos ao Next (Refere-se a `compose_suite`, `add_module`, `provision`, `export-frontend`) — RESOLVIDO NO CLONE
- **Falha:** quatro caminhos geravam Next ou template estático.
- **Artefato de Handoff:** `aidd-master/scripts/*.py`, `aidd-enterprise/scripts/*.py`
- **Requisito TDD (Red):** `test_provision_rejeita_frontend_stack_nextjs_abolida` falhou (1 failed).
- **Implementação Técnica:**
  - Troca de import/default/condições, validação de stack, `export-frontend` com tipos OpenAPI.
- **Verificação (Green):** master 466 passed e enterprise exit 0.
- **Construtor Prompt (EN):**
  - Switch all callers to `TanStackRouterExporter`, reject unsupported `frontend_stack` with `ValueError`, keep OpenAPI types in `src/types.ts`; run both suites and assert exit 0.

### Ticket R3: Terceiro gerador e verificadores de Next no `aidd-open` — RESOLVIDO NO CLONE
- **Falha:** `frontend_generator.py` morto, default `nextjs`, gates aceitando `next`.
- **Artefato de Handoff:** `aidd-open/src/core_open/`, `scripts/phases_open/09_integracao.py`, `gates/G_FACTORY_INTEGRATION.py`
- **Requisito TDD (Red):** `test_frontend_stack_tanstack.py`, 5 falhas.
- **Implementação Técnica:**
  - Remoção do código morto, validação, gates que exigem TanStack completo.
- **Verificação (Green):** 28 passed.
- **Construtor Prompt (EN):**
  - Remove the dead Next generator, default to `tanstack`, make the gates reject Next and require a complete TanStack frontend; run the aidd-open tests and assert exit 0.

### Ticket R4: Healthcheck IPv6 no container do frontend (Refere-se a prova com Docker) — RESOLVIDO NO CLONE
- **Falha:** container `unhealthy` por `localhost` → `::1`.
- **Artefato de Handoff:** `tanstack_exporter.py` e `moldes/infra/docker-compose.yml`
- **Requisito TDD (Red):** `test_healthcheck_usa_ipv4_explicito` exit 1.
- **Implementação Técnica:**
  - `127.0.0.1` nos dois pontos.
- **Verificação (Green):** teste exit 0 e container `healthy` na prova real.
- **Construtor Prompt (EN):**
  - Use `127.0.0.1` in every wget healthcheck of the generated frontend and the compose mold; verify with a real container reaching `healthy`.

### Ticket R5: Resíduos de Next.js ainda vivos (Refere-se a "excluir tudo") — ABERTO (passos 5 e 6)
- **Falha:** ainda citam Next.js: `handoff-*.schema.json` (enum `nextjs_app_router`), `G_STACK_PADRAO_OURO` (docstring e verificações), `G_CONTRACTS`, `G_NOVE_CAMADAS_MERCADO`, 3 skills (`aidd-pure`, `aidd-open`, `aidd-frontend-forms`), `README.md`, `AGENTS.md:131`, `CATALOGO`, testes da raiz (`test_forge_templates_padrao_ouro`, `test_skill_frontend_forms`, `test_livro_projeto`, `test_orquestrador_sincrono`), as 3 cópias de `nextjs_exporter.py` e o `test_nextjs_exporter.py`, `templates/v2/frontend` do master.
- **Artefato de Handoff:** os arquivos acima.
- **Requisito TDD (Red):** um gate/teste que varre arquivos vivos (fora de documentos históricos) e reprova qualquer rastro de Next.js.
- **Implementação Técnica:**
  - Atualizar, remover e regenerar catálogo, mapas e livros pelas ferramentas.
- **Verificação (Green):** o gate novo com exit 0 e o `audit` completo com exit 0.
- **Construtor Prompt (EN):**
  - Add a guard that fails on any Next.js trace in live files, then remove the remaining references and the three `nextjs_exporter.py` copies and regenerate catalog and maps; finish with a full audit at exit 0.

### Ticket R6: Teste de isolamento do master (Refere-se a confiabilidade da suíte) — ABERTO
- **Falha:** `test_cmd_setup_diagnostico_completo_com_pip_isolado` falha numa combinação de 4 arquivos (também no original sem mudanças).
- **Artefato de Handoff:** `aidd-master/tests/unit/test_cli_commands.py`
- **Requisito TDD (Red):** `pytest test_provision_project.py test_compose_suite.py test_cli_commands.py test_attach_vsa.py` → exit 1.
- **Implementação Técnica:**
  - Isolar o estado compartilhado (módulos importados/`monkeypatch`).
- **Verificação (Green):** a combinação com exit 0.
- **Construtor Prompt (EN):**
  - Reproduce the failure with the four-file pytest combination, find the shared state it depends on, isolate it, and rerun the combination asserting exit 0.

### Ticket R7: Deleção sem explicação de 2 arquivos rastreados (Refere-se a integridade do repositório) — ABERTO, NÃO REPRODUZIDO
- **Falha:** `projetos/app-loja/README-USUARIO.md` e `projetos/lovable-app/README-USUARIO.md` apareceram como apagados no clone; restaurados com `git checkout`.
- **Artefato de Handoff:** a determinar (nenhum teste, `components sync --dry-run`, `sync.py` nem `pure --dry-run` reproduziu em 5 tentativas).
- **Requisito TDD (Red):** a definir quando houver reprodução.
- **Implementação Técnica:** conferir `git status | grep '^ D'` após cada comando grande.
- **Verificação (Green):** a definir.
- **Construtor Prompt (EN):**
  - If the deletion reappears, bisect by running each recent command and checking `git status`; add a test that fails when a command touches tracked files under `projetos/`.

### Ticket R8: Baseline de RAM do dimensionamento (Refere-se a `aidd-ops`) — ABERTO (observação)
- **Falha:** o baseline de 1,5 GB foi calculado com frontend Node; com nginx estático pode ser menor. Não alterado sem medição.
- **Artefato de Handoff:** `aidd-ops/scripts/phases_ops/03_sizing.py`
- **Requisito TDD (Red):** a definir após medir o consumo do container estático.
- **Implementação Técnica:** medir e ajustar.
- **Verificação (Green):** testes de dimensionamento com exit 0.
- **Construtor Prompt (EN):**
  - Measure the static frontend container's memory, then adjust the sizing baseline and its tests accordingly.

### Ticket R9: Compose completo não provado (Refere-se a verificação de ponta a ponta) — ABERTO
- **Falha:** só o container do frontend foi provado; falta backend + nginx de borda + frontend juntos e `nginx -t`.
- **Artefato de Handoff:** `moldes/infra/`
- **Requisito TDD (Red):** a definir.
- **Implementação Técnica:** subir o compose completo de um projeto gerado e testar as rotas por prefixo.
- **Verificação (Green):** respostas 200 em `/`, `/api/...`, `/docs`, `/openapi.json` e containers `healthy`.
- **Construtor Prompt (EN):**
  - Bring up the full generated compose and assert the edge nginx routes `/` to the frontend and `/api`, `/docs`, `/openapi.json` to the backend, all healthy.

### Ticket R10: Trabalho só no clone, sem espelhamento no original (Refere-se ao padrão de branches) — ABERTO
- **Falha:** nada dos passos 1 a 4 está em branch do motor original.
- **Artefato de Handoff:** o diff do clone (exportador, MANIFEST, CATALOGO, baseline, master, enterprise, aidd-open, moldes, testes).
- **Requisito TDD (Red):** `diff` entre clone e original nesses arquivos mostra divergência.
- **Implementação Técnica:** criar `fix/pure-etapa-06-nextjs-para-tanstack` a partir da `main`, aplicar o diff, rodar pytest dos 3 módulos, os gates e o `audit` completo; atenção ao catálogo de peças e aos mapas visuais (um teste que importa peças pode reprovar 3 gates de mapa).
- **Verificação (Green):** `audit` completo com exit 0 e commit só com aprovação do usuário.
- **Construtor Prompt (EN):**
  - Create the branch from a clean `main`, apply the clone diff, run the three module suites, the drift gate and the full audit; commit only after user approval.
