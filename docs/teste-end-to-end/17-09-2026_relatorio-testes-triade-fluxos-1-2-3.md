# Relatório de Execução e Homologação End-to-End da Tríade Canônica (Fluxos 1, 2 e 3)

> **Data de Abertura:** 17/09/2026  
> **Objetivo:** Validação end-to-end dos 3 Fluxos Canônicos de Criação do Ecossistema AIDD, testados individualmente por sessão para garantia de contexto limpo, rastreabilidade factual e economia severa de tokens.  
> **Arquitetura Base:** Universal Convergence Funnel (Quarteto *Sine Qua Non*: `/swagger`, `/webhooks`, `/mcp`, `/docs`)  

---

## 1. Topologia da Tríade Canônica de Criação

Cada fluxo representa um caminho industrial especializado alimentado pelo **`aidd-planner`** e convergindo obrigatoriamente para o funil de robustez corporativa:

```
                                  ┌───────────────────┐
                                  │    aidd-forge     │
                                  └─────────┬─────────┘
                                            ▼
                                  ┌───────────────────┐
                                  │   aidd-planner    │
                                  └─────────┬─────────┘
                                            │
               ┌────────────────────────────┼────────────────────────────┐
               ▼                            ▼                            ▼
        ┌──────────────┐             ┌──────────────┐             ┌──────────────┐
        │   FLUXO 01   │             │   FLUXO 02   │             │   FLUXO 03   │
        │ Do Zero Puro │             │ Open-Source  │             │   Low-Code   │
        │aidd-generator│             │ aidd-factory │             │ aidd-bridge  │
        └──────┬───────┘             └──────┬───────┘             └──────┬───────┘
               │                            │                            │
               └────────────────────────────┼────────────────────────────┘
                                            ▼
                                  ┌───────────────────┐
                                  │    aidd-master    │ (Monólito Modular VSA)
                                  └─────────┬─────────┘
                                            ▼
                                  ┌───────────────────┐
                                  │  aidd-enterprise  │ (SHA-256 & Missão Crítica)
                                  └─────────┬─────────┘
                                            ▼
                                  ┌───────────────────┐
                                  │     aidd-ops      │ (Infraestrutura, Docker & VPS)
                                  └───────────────────┘
```

---

## 2. FLUXO 01: Do Zero Puro (Custom MVP)

- **Esteira:** `FORGE` → `PLANNER` → `GENERATOR` → `MASTER` → `ENTERPRISE` → `OPS`
- **Motor Primário:** `aidd-generator` (Pipeline de 8 fases, TDD Red-Green estrito)
- **Diretório Alvo do Teste:** `testes/fluxo-01-pure/`
- **Status do Fluxo:** **Etapas 1-4 CONCLUÍDAS; Etapas 5-7 pendentes**

### Checklist de Execução por Ferramenta:
- [x] **Etapa 1 (`aidd-forge`):** Injeção de governança, Git, pre-commit hooks e regras de isolamento.
- [x] **Etapa 2 (`aidd-planner`):** Intake BDD/SDD, geração e auditoria do `PLANNER.json` (Fluxo 1).
- [x] **Etapa 3 (`aidd-generator`):** Execução do pipeline TDD de 8 fases (Spec -> Arquitetura -> Testes Red -> Implementação Green -> Quarteto). 4 bugs reais achados e corrigidos, score final 88/100.
- [x] **Etapa 4 (`aidd-master`):** Harmonização em Monólito Modular (`init` + `add-module`). 2 bugs reais achados e corrigidos, auditoria final APROVADA (7/7 gates).
- [ ] **Etapa 5 (`aidd-enterprise`):** Injeção de componentes resilientes e validação de hashes SHA-256.
- [ ] **Etapa 6 (`aidd-ops`):** Provisionamento do docker-compose unificado e envs de produção.
- [ ] **Etapa 7 (Auditoria Final):** Aprovação com exit code 0 em todos os Quality Gates.

### Registro de Inconsistências e Auto-Correções (Fluxo 01)

**Etapa 1 (`aidd-forge`) — CONCLUÍDA:**
- Comando real executado: `python ecossistema.py forge init testes/fluxo-01-pure` (mecanismo real, sem proxy).
- 1ª execução: 38 arquivos criados, mas hook `pre-commit` **não instalado** — mensagem `'.git' nao encontrado (nao e um repositorio git)`.
- **Causa raiz (verificada em código, `tools/aidd-forge/aidd_forge/core/git_hooks.py`):** comportamento by-design — `forge init` não executa `git init` sozinho; ele apenas instala o hook se `.git` já existir. Não é bug, é uma pré-condição não documentada no checklist do Fluxo 01.
- **Auto-correção:** executado `git init` em `testes/fluxo-01-pure/`, seguido de `forge init --force`. Hook `pre-commit` instalado com sucesso em `.git/hooks/pre-commit`.
- `forge audit testes/fluxo-01-pure`: **CONFORME, 100% (15/15 PASS)**, todos os gates G01–G15.
- **Recomendação para o checklist:** documentar que `git init` no diretório alvo é pré-requisito do `aidd-forge init` para que o pre-commit hook seja instalado na primeira passada.

**Etapa 2 (`aidd-planner`) — CONCLUÍDA:**
- Caso de teste escolhido: MVP "Gestão de Tarefas" (domínio produtividade; criação, conclusão e listagem de tarefas) — simples e suficiente para exercitar o pipeline de 8 fases sem complexidade acidental.
- `python ecossistema.py planner init --fluxo 1 --nome "Gestao de Tarefas" --slug gestao-tarefas --dominio produtividade --pasta testes/fluxo-01-pure`: `PLANNER.json` gerado, 100% conforme (Schema + Quarteto Sine Qua Non + SDD/BDD).
- `planner validate`: PASS (100% conforme).
- `planner audit`: `G_PLANNER_SCHEMA`, `G_PLANNER_SINE_QUA_NON`, `G_PLANNER_COERENCIA_FLUXO` — todos **[Passed]**. Nenhuma inconsistência encontrada.
- **Achado de integração (não bloqueante):** `aidd-generator` não lê o `PLANNER.json` gerado pelo `aidd-planner` — recebe a ideia como texto livre via argumento posicional (`generate "<ideia>"`). Não há handoff programático entre as duas ferramentas no Fluxo 01; a "convergência" do diagrama é apenas conceitual/manual nesta etapa.

**Etapa 3 (`aidd-generator`) — 2 achados reais, 1 corrigido, 1 CRÍTICO em aberto:**

Comando real: `python ecossistema.py generate "<ideia>" --pasta testes/fluxo-01-pure --implementar-codigo` (resolve para `run_generator_delegated.py`, não `pipeline_completo.py` diretamente — ver achado crítico abaixo).

**1) BUG corrigido — path duplicado no gate E5 da Fase 5 (Criador):**
- 1ª execução: pipeline falhou na Fase 5/8 com `E5_sincronizacao_harness` reprovado: `can't open file '...\testes\fluxo-01-pure\testes\fluxo-01-pure\scripts\gates\G_SYNC_HARNESS.py'` (pasta alvo duplicada no caminho).
- **Causa raiz:** `tools/aidd-generator/scripts/phases/05_criador.py:243-255`, método `_gate_e5_sincronizacao_harness`. `gate_path = pasta / 'scripts/gates/G_SYNC_HARNESS.py'` fica relativo quando `pasta` é relativa (caso real de uso via CLI: `--pasta testes/fluxo-01-pure`). O `subprocess.run` chamava com `[sys.executable, str(gate_path)]` **e** `cwd=str(pasta)` — o SO resolve o argv relativo contra o cwd do subprocesso (já dentro de `pasta`), duplicando o segmento.
- **Por que os testes não pegaram:** `tools/aidd-generator/tests/test_phase_05.py` sempre usa `tmp_path` do pytest, que é absoluto — o bug só se manifesta com pasta relativa, exatamente o padrão real de uso da CLI. Zero cobertura para esse caso.
- **Correção aplicada:** `str(gate_path.resolve())` em vez de `str(gate_path)` (linha 254). Teste de regressão novo adicionado: `test_gate_e5_funciona_com_pasta_relativa` (usa `monkeypatch.chdir` + pasta relativa, reproduzindo o cenário real).
- **Validação real:** `python -m pytest tests/test_phase_05.py -q` → **28 passed** (exit code 0). Pipeline reexecutado do zero: Fase 5 passou (`E5_sincronizacao_harness: [OK] 5 copia(s) sincronizada(s)`).

**2) ACHADO CRÍTICO EM ABERTO — protocolo delegado substituído por mock hardcoded, sem aviso:**
- `ecossistema.py generate` (função `cmd_generate`) prioriza `run_generator_delegated.py` sobre `pipeline_completo.py` quando o primeiro existe — **é o caminho real e default da CLI**, não um modo opcional.
- `run_generator_delegated.py` sobe automaticamente uma thread daemon rodando `aidd_delegado_mediator.py::loop_mediador`, que fica varrendo `.aidd/cache/` a cada 50ms e responde **qualquer** `_llm_request_*.json` — de qualquer projeto, qualquer ideia — com conteúdo **hardcoded fixo** sobre "Sistema Operacional Logístico CTT Portugal... gestão de frotas, encomendas express, roteirização VRP" (ver `aidd_delegado_mediator.py:38-143`). Todo `tokens_consumidos` retornado é sempre exatamente `420`, para qualquer prompt.
- **Isso não é o Protocolo Delegado real** descrito em `docs/PRINCIPIO-UNIVERSALIDADE.md` (onde a ADE ativa — Claude Code, neste caso — deveria ler o prompt de verdade e responder com conteúdo genuíno). É um mock que finge ser o protocolo, e responde tão rápido (50ms) que nunca dá chance de uma resposta genuína chegar primeiro.
- **Evidência da contaminação:** com a ideia real "Sistema de gestão de tarefas pessoais", a Fase 3 (Designer) recebeu de volta scripts `gestor_frotas.py` e `roteirizador_vroom.py` — nomes hardcoded do mock, sem nenhuma relação com o domínio pedido. A Fase 8 falhou tentando implementar `gestor_frotas.py` porque a resposta mock de fallback não contém as chaves `codigo`/`teste` esperadas.
- **Origem:** commit `b79c162` (16/09/2026 22:26, mensagem "feat(generator): add native delegated mediator and e2e validation (exit 0)") — de sessão anterior a esta, possivelmente concorrente (ver alerta de memória sobre duas sessões na mesma pasta). O "exit 0" relatado nesse commit e a "validação e2e" da memória de 04/09 (10/10 testes, servidor real) foram alcançados **com este mock respondendo sempre sobre logística CTT**, não com conteúdo real gerado pela ideia testada naquela sessão.
- **Impacto:** qualquer execução de `aidd-generator --implementar-codigo` (ou mesmo sem essa flag, fases 2/3 também são afetadas) produz artefatos de design/código contaminados com o domínio fixo "CTT/frotas", mascarados como se fossem resposta real da ADE ativa. Viola diretamente a Lei Fundamental de Transparência e o princípio de Zero Alucinação do próprio `AGENTS.md` do aidd-generator.
- **Decisão do usuário:** remover o mock e usar o protocolo delegado real. Aplicado: `ecossistema.py::cmd_generate` revertido para chamar `pipeline_completo.py` diretamente; `aidd_delegado_mediator.py` e `run_generator_delegated.py` deletados. Suite completa (1016 testes) segue passando.

**3) BUG corrigido — sandbox da Fase 8 quebra sempre no Windows (`SandboxNivel1`):**
- Ao responder de verdade ao protocolo delegado (via um script "watcher" que entrega minhas respostas pré-compostas e já validadas, contornando o timeout de 30-60s — ver nota metodológica abaixo), a Fase 8 passou a rodar de fato, mas os gates `I2_testes_coletam`/`I3_testes_passam`/`I5_teste_integracao` reprovavam sempre com "0/0 testes", mesmo com código 100% correto (validado isoladamente: 8/8 pytest, exit 0).
- **Causa raiz:** `tools/aidd-generator/scripts/phases/sandbox_nivel_1.py`. `ENV_EXECUCAO_ALLOWLIST` só continha `PATH, PYTHONPATH, PYTHONUTF8, TMPDIR`. No Windows, sem `SYSTEMROOT`, o carregador de DLL do Winsock não inicializa — qualquer import transitivo que toque `asyncio`/rede (ex.: o plugin `anyio`, dependência comum de FastAPI/Starlette, autocarregado pelo pytest se instalado no ambiente) quebra com `OSError [WinError 10106]`. Reproduzido isolando o subprocess exatamente como a Fase 8 o invoca.
- **Correção aplicada:** `montar_env_minimo()` agora inclui `SYSTEMROOT` quando `os.name == 'nt'` (Windows-only, não afeta outros SOs). Teste de regressão novo: `test_sandbox_pytest_com_plugin_asyncio_nao_quebra_sem_systemroot` (roda pytest real, sem mock, e falha se `WinError 10106` aparecer na saída).
- **Validação real:** `python -m pytest tests/test_sandbox_nivel_1.py -q` → 19 passed.

**4) BUG corrigido — path relativo duplicado também na Fase 8 (`_rodar_pytest`), mesma classe do bug #1:**
- Mesmo corrigindo o SYSTEMROOT, a Fase 8 continuou reprovando com "0/0" e "Directory not found. Check your '--rootdir' option."
- **Causa raiz:** `08_implementador.py::_rodar_pytest` (e `_gate_i4_cli_executa`) montavam `alvo_absoluto = str(self.pasta_projeto / alvo)` sem `.resolve()` — quando `self.pasta_projeto` é relativo (caso real da CLI: `--pasta testes/fluxo-01-pure`), o argumento do arquivo de teste e `--rootdir` continuavam relativos, e o subprocess roda com `cwd` no tempdir isolado do sandbox (diferente do cwd do processo pai) — o SO resolve o caminho relativo contra o cwd errado. Nome da variável (`alvo_absoluto`) era enganoso: nunca era de fato absoluto.
- **Correção aplicada:** `self.pasta_projeto.resolve()` antes de montar o argumento do pytest e o `--rootdir`, em `_rodar_pytest` e em `_gate_i4_cli_executa`.
- **Por que os testes não pegaram:** de novo, `tests/test_phase_08.py` só usava `tmp_path` (absoluto) ou mockava `subprocess.run` inteiro (ignorando os argumentos reais). Teste de regressão novo, sem mock: `test_rodar_pytest_funciona_com_pasta_relativa` (pytest real, sandbox real, pasta relativa real — falha reproduzindo "Directory not found" sem o fix, passa com ele).
- **Validação real:** `python -m pytest tests/test_phase_08.py -q` → 58 passed. Suite completa do aidd-generator após os 3 fixes: `python -m pytest -q` → **1019 passed, 5 skipped**.

**Nota metodológica — como respondi de verdade ao protocolo delegado sem estourar o timeout:** o protocolo espera resposta em 30-60s; ida-e-volta de chamadas de ferramenta é lento demais. Solução: compus o conteúdo (análise da ideia, design AIDD, código+testes do `gestor_tarefas.py`, schema SQL) com antecipação, validei cada peça isoladamente (pytest real, exit 0) e usei um script auxiliar local (`watcher_fluxo01.py`, só nesta sessão, nunca commitado) que entrega essas respostas já prontas assim que os arquivos `_llm_request_*.json` aparecem — resolvendo apenas o problema de latência, não fabricando conteúdo de outro domínio como fazia o mock removido.

**RESULTADO FINAL DA ETAPA 3 (pipeline completo, 8 fases, do zero, com os 4 fixes acima):**
- `python ecossistema.py generate "<ideia>" --pasta testes/fluxo-01-pure --implementar-codigo` → **PIPELINE COMPLETO — score final: 88/100** (Profissional).
- Fase 8: 1 script implementado (`src/infrastructure/gestor_tarefas.py`, CRUD real sobre SQLite), 8 testes passando, 1 teste de integração passando, 0 violações de Clean Architecture.
- Fase 7 (auto-crítica): Completude Pipeline 85/100, Qualidade Gates 100/100, Determinismo 66/100, Validações 100/100, Documentação 100/100, Rastreabilidade 100/100.
- Ponto a melhorar identificado pela própria auto-crítica da ferramenta: determinismo (67% de fases determinísticas vs. mínimo recomendado).

**5) BUG corrigido — achado durante o commit, fora do escopo do `aidd-generator`: o pre-commit trava o repositório inteiro por causa do `aidd-master`:**
- Ao commitar as correções acima, o gate `G_TESTES_REAIS` do pre-commit (roda pytest real de cada ferramenta em `tools/`) ficou preso por quase 1 hora sem terminar, bloqueando qualquer commit no monorepo.
- **Causa raiz:** `tools/aidd-master/scripts/gates/G_SEGURANCA.py`, Camada 8 (CVE Dependency Audit). O gate roda `pip-audit -r requirements.txt`, que cria um venv temporário e executa `pip install --upgrade pip wheel setuptools` — **acesso real à rede (PyPI)** dentro de um gate que deveria ser 100% determinístico/local. Havia um `timeout=120` no `subprocess.run(...)`, mas isso só mata o processo direto (`pip-audit`); no Windows, o processo-neto (`pip install`, que é quem realmente acessa a rede) fica **órfão e continua rodando indefinidamente**, travando o pre-commit sempre que a rede estiver lenta ou instável.
- **Correção aplicada:** nova função `_run_matando_arvore_em_timeout()` em `G_SEGURANCA.py` — usa `subprocess.Popen` + `taskkill /F /T /PID` no Windows (mata a árvore inteira de processos) em vez de `subprocess.run(timeout=...)`. Teste de regressão novo, sem rede real e sem mock: `test_run_matando_arvore_em_timeout_mata_processo_neto` (simula um processo pai que gera um filho de longa duração, confirma que o filho morre junto quando o timeout do pai dispara).
- **Validação real:** teste de regressão comprovadamente pega a regressão (travou de propósito ao simular a versão antiga, sem kill de árvore). Suite completa do `aidd-master`: `python -m pytest -q` → **352 passed, 3 skipped** (164s, sem travamentos).
- **Nota:** este bug é anterior a esta sessão e afeta qualquer commit no monorepo, não só os do Fluxo 01. Corrigido durante esta sessão porque bloqueava o commit das correções do `aidd-generator`.

**Etapa 4 (`aidd-master`) — 2 bugs achados e corrigidos, auditoria final APROVADA:**

Mecanismo real: `python ecossistema.py master init <nome> --pasta <dest>` (cria o monólito com um módulo "principal" padrão) seguido de `python ecossistema.py master add-module <modulo> --pasta <dest>` (adiciona a fatia vertical "tarefas"). Não há handoff automático do código gerado pelo `aidd-generator` na Etapa 3 — mesma lacuna de integração observada entre `aidd-planner` e `aidd-generator`; `add-module` gera um scaffold CRUD genérico (Clean Architecture completa: domain/application/infrastructure/interfaces) parametrizado pelo nome do módulo, não importa a lógica de negócio já escrita.

**1) BUG corrigido — `master init` nunca gera `src/server.py`:**
- `master audit` reprovava sempre com `G_ESTRUTURA FAIL`: "Servidor Monolítico Modular 'src/server.py' ➔ Servidor ausente ou vazio".
- **Causa raiz:** `scripts/provision_project.py::provision()` (implementação real de `master init`) cria o módulo "principal" via `add_module.criar_modulo()`, mas essa função só RE-liga/regenera `src/server.py` quando ele **já existe** (comportamento documentado no próprio código: a primeira geração é responsabilidade de quem chama `criar_modulo()` a primeira vez). Como era a primeira vez, o arquivo nunca nascia. `compose_suite.py` (usado por outro fluxo) já fazia isso certo, gerando o server.py antes de criar o primeiro módulo.
- **Por que nenhum teste pegou:** `provision_project.py` não tinha nenhum teste — nenhum teste jamais chamava `provision()` e verificava os arquivos gerados (mesma classe de lacuna documentada em `test_compose_suite.py` para outro bug anterior).
- **Correção aplicada:** `provision()` agora chama `generate_modular_server_code()` (a mesma função que `compose_suite.py` usa) e escreve `src/server.py` logo após criar o módulo inicial.

**2) BUG corrigido — `src/static/index.html` copiado de um template desatualizado, sem CSS/modal exigidos por `G_CONTRACTS`:**
- `master audit` reprovava com `G_CONTRACTS FAIL`: "Super-App 'index.html' sem CSS offline-first embutido" e "sem estrutura modal com display encapsulado".
- **Causa raiz:** `provision()` copiava estaticamente `templates/core/index.html` — um arquivo desatualizado, sem a variável CSS `--bg-base` nem `modal-overlay`/`modal-generic`, que o próprio gate `G_CONTRACTS` exige. O template real e atualizado (`templates/cookiecutter-scaffold/.../index.html.j2`, usado por `compose_suite.py` via `generate_superapp_index_html()`) já tinha essas partes.
- **Correção aplicada:** `provision()` não copia mais `index.html` estaticamente — gera via `generate_superapp_index_html()`, igual a `compose_suite.py`.
- **Novo arquivo de teste:** `tests/unit/test_provision_project.py` (4 testes, nenhum existia antes) — cobre os 2 bugs acima com reprodução real (chama `provision()` de verdade, roda os gates `G_ESTRUTURA`/`G_CONTRACTS` reais contra o projeto gerado, sem mock). Confirmado que cada teste detecta a regressão correspondente ao reverter o fix.
- **Validação real:** `python -m pytest tests/unit/test_provision_project.py -v` → 4 passed. Suite completa do `aidd-master`: `python -m pytest -q` → **356 passed, 3 skipped**.

**RESULTADO FINAL DA ETAPA 4 (projeto recriado do zero com os 2 fixes):**
- `master init` + `master add-module tarefas` → estrutura completa gerada (2 módulos: `principal` + `tarefas`).
- `master test`: 4/4 testes unitários passando.
- `master audit --report`: **APROVADO — 7/7 gates PASS** (`G_ESTRUTURA`, `G_QUALIDADE`, `G_TESTES`, `G_CONTRACTS`, `G_SEGREDOS`, `G_HARNESS_COMPAT`, `G_SEGURANCA`).

---

## 3. FLUXO 02: Motores Open-Source & Stacks Integradas

- **Esteira:** `FORGE` → `PLANNER` → `FACTORY` → `MASTER` → `ENTERPRISE` → `OPS`
- **Motor Primário:** `aidd-factory` (Curadoria Open-Source, Gateway VSA FastAPI, Compose)
- **Diretório Alvo do Teste:** `testes/fluxo-02-factory/`
- **Status do Fluxo:** **PROGRAMADO (Após conclusão do Fluxo 01)**

### Checklist de Execução por Ferramenta:
- [ ] **Etapa 1 (`aidd-forge`):** Bootstrap e regras no projeto alvo.
- [ ] **Etapa 2 (`aidd-planner`):** Geração do `PLANNER.json` (Fluxo 2) e exportação para o formato Factory.
- [ ] **Etapa 3 (`aidd-factory`):** Execução do pipeline de 9 fases e geração de VSA + Gateway + Compose.
- [ ] **Etapa 4 (`aidd-master`):** Integração das fatias de proxy no Monólito Modular.
- [ ] **Etapa 5 (`aidd-enterprise`):** Blindagem SHA-256 de componentes de gateway.
- [ ] **Etapa 6 (`aidd-ops`):** Validação de portas e deploy VPS.
- [ ] **Etapa 7 (Auditoria Final):** Quality Gates 100% PASS.

### Registro de Inconsistências e Auto-Correções (Fluxo 02)
*(A ser preenchido iterativamente durante a execução da sessão)*

---

## 4. FLUXO 03: Desacoplamento Low-Code (Lovable / v0 / Bolt)

- **Esteira:** `FORGE` → `PLANNER` → `BRIDGE` → `MASTER` → `ENTERPRISE` → `OPS`
- **Motor Primário:** `aidd-bridge` (Anti-lockin, Migração de Banco para PostgreSQL, Nginx SPA)
- **Diretório Alvo do Teste:** `testes/fluxo-03-bridge/`
- **Status do Fluxo:** **PROGRAMADO (Após conclusão do Fluxo 02)**

### Checklist de Execução por Ferramenta:
- [ ] **Etapa 1 (`aidd-forge`):** Fundação de governança agêntica.
- [ ] **Etapa 2 (`aidd-planner`):** Mapeamento do frontend exportado e esquema de banco.
- [ ] **Etapa 3 (`aidd-bridge`):** Scan anti-lockin, conversão de banco para PostgreSQL e empacotamento.
- [ ] **Etapa 4 (`aidd-master`):** Conexão do frontend ao backend VSA modular.
- [ ] **Etapa 5 (`aidd-enterprise`):** Auditoria SHA-256.
- [ ] **Etapa 6 (`aidd-ops`):** Conteinerização e deploy na VPS.
- [ ] **Etapa 7 (Auditoria Final):** Quality Gates 100% PASS.

### Registro de Inconsistências e Auto-Correções (Fluxo 03)
*(A ser preenchido iterativamente durante a execução da sessão)*

---

## 5. Painel Consolidado de Quality Gates e Métricas

| Fluxo | Quality Gates Específicos | Testes Unitários Reais | Status Final |
|---|---|---|---|
| **Fluxo 01 (Zero Puro)** | `G_PLANNER_*`, `G_TESTES_REAIS`, `G_MASTER_*`, `G_ENTERPRISE_*`, `G_INFRA_*` | A medir | Aguardando |
| **Fluxo 02 (Open-Source)** | `G_PLANNER_*`, `G_FACTORY_*` (6 gates), `G_MASTER_*`, `G_ENTERPRISE_*`, `G_INFRA_*` | A medir | Aguardando |
| **Fluxo 03 (Low-Code)** | `G_PLANNER_*`, `G_BRIDGE_*`, `G_MASTER_*`, `G_ENTERPRISE_*`, `G_INFRA_*` | A medir | Aguardando |
| **Meta-Gate Global** | `python ecossistema.py audit` (11 Quality Gates) | A medir | Aguardando |
