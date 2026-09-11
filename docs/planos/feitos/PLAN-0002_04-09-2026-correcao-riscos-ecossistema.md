# PLANO DE CORREÇÃO E MITIGAÇÃO DE RISCOS — ECOSSISTEMA AIDD UNIFICADO

> **Repositório:** `https://github.com/heverton-dev/ecossistema-aidd`
> **Diretório Local:** `C:\Users\trcnologia\Desktop\ecossistema-aidd`
> **Data da Auditoria:** 04/09/2026
> **Status:** CONCLUÍDO — todos os 8 riscos corrigidos e validados em 04/09/2026
> **Commits:** e551ec1 (R1+R2), 3ddb6a2 (R5), 21e7b85 (R4), b99ecd7 (R3), 992db8b (R6), 47278ea (R7), 0db2d32 (R8)
> **Validação final:** 1278 testes passando / 0 falhas nas 4 ferramentas, 4 gates da raiz aprovados (`python ecossistema.py audit`)
> **Referência:** Este documento complementa `docs/planos/PLANO-EXECUCAO-ECOSSISTEMA-AIDD.md`, corrigindo desvios entre o que foi planejado/declarado e o estado real verificado por comando.

---

## 1. OBJETIVO

Corrigir 8 riscos **verificados por execução real** (não especulação) que contradizem as Regras de Ouro do `AGENTS.md`:
Determinismo Primeiro, Qualidade Binária (Gates), Persistência Estruturada e Transparência Total, Economia de Tokens, Zero Stubs/Mocks, e Supremacia Agnóstica.

Todo achado abaixo foi reproduzido com o comando exato que o comprova. Nenhuma correção deste plano deve ser marcada como `CONCLUIDO` sem o comando de verificação da Fase correspondente retornando exit code 0.

---

## 2. SUMÁRIO EXECUTIVO DOS RISCOS (ordenados por severidade)

| # | Risco | Severidade | Arquivo(s) | Regra de Ouro violada | Status |
|---|---|---|---|---|---|
| R1 | Suite de testes de `aidd-master` não coleta (`ModuleNotFoundError: database`) | **CRÍTICA** | `tools/aidd-master/templates/v2/` (vazio) | #2 Qualidade Binária | ✅ RESOLVIDO |
| R2 | `pytest.ini` da raiz quebrado por BOM UTF-8 | **CRÍTICA** | `pytest.ini` | #2 Qualidade Binária | ✅ RESOLVIDO |
| R3 | Duplicação byte-a-byte de núcleo entre `aidd-master` e `aidd-master-enterprise` (22 de 24 arquivos, não só os 3 originalmente achados) | Alta | `tools/*/src/core/*.py` | #3 Fonte Única / Desacoplamento | ✅ RESOLVIDO (gate de drift por hash, sem acoplamento) |
| R4 | Mecanismo de symlink AGENTS.md→harness falha silenciosamente no Windows | Alta | `05_criador.py` (aidd-generator) | #3 Transparência Total | ✅ RESOLVIDO (manifest + gate de drift auto-contido no projeto gerado) |
| R5 | 2 testes falhando em `aidd-generator` | Alta | `tests/test_phase_05.py`, `tests/test_preflight_llm.py` | #2 Qualidade Binária | ✅ RESOLVIDO (causa raiz: testes não-herméticos, não bug de produto) |
| R6 | Gates `G_HARNESS_COMPAT.py` / `G_SEGREDOS.py` prometidos mas ausentes na raiz | Média | `gates/` (raiz) | #6 Supremacia Agnóstica | ✅ RESOLVIDO |
| R7 | Nenhum CI na raiz do ecossistema | Média | `.github/workflows` (ausente) | #2 Qualidade Binária | ✅ RESOLVIDO |
| R8 | Estado JSON declarado como "vivo" é snapshot estático com número incorreto | Baixa | `PLANO-EXECUCAO-ESTRUTURADO.json` | #3 Persistência Estruturada | ✅ RESOLVIDO (`ecossistema.py status --testes`) |

---

## 3. PLANO DE CORREÇÃO EM 5 FASES SEQUENCIAIS

### FASE 1 — Hotfix Bloqueante (R1 + R2)
**Por quê primeiro:** sem isso, nenhum gate determinístico do ecossistema consegue rodar de ponta a ponta. É a pré-condição para validar qualquer outra fase.

1.1. **Corrigir `pytest.ini` da raiz (R2):**
   - Recriar o arquivo sem BOM (`utf-8` puro, sem `utf-8-sig`).
   - Corrigir `testpaths` para apontar só para o que existe (`gates`), ou criar `tests/` na raiz com um teste-sentinela que invoca os 4 subprojetos.
   - Verificação: `python -m pytest --collect-only -q` deve rodar sem `ERROR: unexpected line`.

1.2. **Restaurar o módulo ausente em `aidd-master` (R1):**
   - Investigar em `proj_aidd` (fonte original citada no plano de importação) se `templates/v2/database.py` existe e foi esquecido na cópia não-destrutiva; se existir, copiar.
   - Se não existir em lugar nenhum (pior caso: funcionalidade nunca terminada), decidir entre:
     (a) implementar `Database`, `PostgresConnectionProxy`, `PostgresCursorProxy`, `_translate_ddl_for_postgres` conforme o contrato que `tests/unit/test_database_adapter.py` espera, ou
     (b) remover o teste órfão e abrir débito técnico rastreado (nunca deletar silenciosamente — documentar o porquê).
   - Fazer o mesmo diagnóstico para `tests/unit/test_cqrs_local_first.py` (mesma causa-raiz provável).
   - Verificação: `cd tools/aidd-master && python -m pytest -q` sem erros de coleta.

**Critério de saída da Fase 1:** `python -m pytest --collect-only -q` na raiz E `python -m pytest -q` em `tools/aidd-master` retornam exit 0.

---

### FASE 2 — Correção dos Testes Vermelhos e do Mecanismo de Symlink (R4 + R5)
**Por quê nesta ordem:** R5 e R4 são a mesma causa-raiz — o `aidd-generator` tenta criar symlinks (`.claude/CLAUDE.md → AGENTS.md`, `.agent/AGENT.md → AGENTS.md`, etc.) e falha silenciosamente em Windows sem privilégio elevado/modo desenvolvedor, caindo para cópia de conteúdo — o que quebra a promessa de "fonte única de verdade".

2.1. **Decidir a estratégia de symlink no Windows** (ver Seção 4 — decisão do usuário necessária):
   - Opção A: manter cópia de conteúdo como fallback, mas com um **hash de sincronismo** (ex: gate que compara hash de `AGENTS.md` com o hash-fonte registrado no topo de cada cópia) para detectar drift.
   - Opção B: exigir/instruir ativação do "Developer Mode" do Windows ou rodar com privilégio para symlink real funcionar.
   - Opção C: adotar Junctions do NTFS (`mklink /J`) em vez de symlinks simbólicos — não exigem privilégio elevado no Windows.

2.2. Corrigir `test_phase_05.py::test_criar_arquivos_configuracao_sem_env_e_honesto` para refletir a estratégia escolhida (o teste deve validar o comportamento real e documentado, não um ideal que falha silenciosamente).

2.3. Corrigir `test_preflight_llm.py::test_sem_llm_model_falha` — investigar por que o preflight não está bloqueando corretamente a ausência de `LLM_MODEL` (risco funcional: pipeline pode rodar sem modelo configurado e falhar tarde, gastando tokens à toa — contradiz "Zero Token Fallacy").

2.4. Aplicar a mesma verificação em `.claude/CLAUDE.md`, `.agent/AGENT.md`, `.cursor/rules/aidd.md` da **raiz do ecossistema-aidd** — hoje são cópias manuais paralelas ao `AGENTS.md`, não symlinks nem gerados por um único script. Escolher e aplicar o mesmo mecanismo da Fase 2.1.

**Critério de saída da Fase 2:** `cd tools/aidd-generator && python -m pytest -q` → `0 failed`. Todos os arquivos de harness na raiz (`.claude/CLAUDE.md`, `.agent/AGENT.md`, `.cursor/rules/aidd.md`) têm procedência rastreável e documentada a partir de `AGENTS.md`.

---

### FASE 3 — Eliminar Duplicação Estrutural (R3)
**Por quê depois da Fase 1/2:** só faz sentido refatorar núcleo compartilhado depois que os testes de ambas ferramentas estão verdes (senão não há como validar que a extração não quebrou nada).

3.1. Criar um pacote compartilhado (ex: `tools/_shared_core/` ou publicar `aidd-master` como dependência local de `aidd-master-enterprise` via `pip install -e`) contendo:
   - `caveman_protocol.py` (729 linhas)
   - `subagent_engine.py` (645 linhas)
   - `nextjs_exporter.py`

3.2. Atualizar os imports de `aidd-master-enterprise/src/core/` para consumir o pacote compartilhado em vez da cópia local.

3.3. Adicionar ao `gates/G_ECOSSISTEMA_INTEGRIDADE.py` uma checagem nova: **detecção de duplicação de arquivo idêntico entre `tools/*/src/core/`** (hash SHA-256 comparado entre ferramentas) — isso fecha a lacuna que permitiu o drift silencioso passar despercebido por todos os gates existentes.

3.4. Rodar as suítes de teste de `aidd-master` E `aidd-master-enterprise` após a extração.

**Critério de saída da Fase 3:** `diff` entre os 3 arquivos e o pacote compartilhado não existe mais (fonte única); `python gates/G_ECOSSISTEMA_INTEGRIDADE.py` detecta e reprova qualquer duplicação futura.

---

### FASE 4 — Fechar as Lacunas de Governança (R6 + R7 + R8)

4.1. **Materializar os gates prometidos na raiz (R6):**
   - Adaptar `G_HARNESS_COMPAT.py` (hoje só existe como template a ser injetado em projetos *gerados*) para uma versão que audita o **próprio ecossistema-aidd**: verifica se `.claude/`, `.agent/`, `.cursor/` da raiz estão sincronizados com `AGENTS.md` (usa o mecanismo escolhido na Fase 2.1).
   - Adaptar `G_SEGREDOS.py` para escanear todo o `git ls-files` da raiz em busca de padrões de credenciais (reaproveitar os padrões usados nos testes de `test_gate_cybersecurity_owasp.py`).
   - Registrar os dois no `ecossistema.py audit` (função `cmd_audit`), rodando em sequência após `G_ECOSSISTEMA_INTEGRIDADE.py`.

4.2. **Criar CI mínimo na raiz (R7):**
   - `.github/workflows/audit.yml`: em todo push/PR, roda `python ecossistema.py audit` + `pytest -q` em cada um dos 4 `tools/*` + o novo `pytest` da raiz (Fase 1.1).
   - Gate de merge: falha se qualquer um desses passos retornar exit ≠ 0.

4.3. **Corrigir o estado declarado (R8):**
   - Reescrever `PLANO-EXECUCAO-ESTRUTURADO.json` com a contagem real e agregada de testes por ferramenta (gerada por script, não digitada manualmente — reforça Regra #1, Determinismo Primeiro):
     ```json
     "testes": {
       "aidd-forge": {"passed": 191, "skipped": 1},
       "aidd-generator": {"passed": 751, "failed": 0},
       "aidd-master": {"passed": "<preencher pós Fase 1>", "failed": 0},
       "aidd-master-enterprise": {"passed": 168, "skipped": 4}
     }
     ```
   - Adicionar um comando `python ecossistema.py status --testes` que regenera esse bloco automaticamente rodando pytest em cada ferramenta — transforma o JSON de "snapshot manual" em "estado derivado e reproduzível", cumprindo de fato a Regra #3.

**Critério de saída da Fase 4:** `python ecossistema.py audit` cobre estrutura + harmonia de harness + segredos. CI verde em um push de teste. JSON de estado gerado por script, não editado à mão.

---

### FASE 5 — Validação Final e Re-Auditoria Completa

5.1. Re-executar, em sequência, e documentar o resultado de cada um:
   ```
   python -m pytest --collect-only -q                     # raiz
   python ecossistema.py audit                             # gates completos
   cd tools/aidd-forge && python -m pytest -q
   cd tools/aidd-generator && python -m pytest -q
   cd tools/aidd-master && python -m pytest -q
   cd tools/aidd-master-enterprise && python -m pytest -q
   ```
2. Confirmar que nenhum dos 3 arquivos de núcleo (R3) diverge mais entre ferramentas.
5.3. Atualizar `docs/planos/PLANO-EXECUCAO-ECOSSISTEMA-AIDD.md` com uma nota de rodapé referenciando este plano de correção como concluído, e atualizar `PLANO-EXECUCAO-ESTRUTURADO.json` (Fase 4.3) com os números finais reais.
5.4. Só então declarar publicamente (README, commit) o status "100% homologado" — nunca antes desse fechamento.

**Critério de saída da Fase 5 (Definition of Done do plano inteiro):** todos os 8 riscos da Seção 2 com status `RESOLVIDO`, todos os comandos acima com exit 0, e nenhuma alegação em documentação que não seja verificável por comando.

---

## 4. DECISÕES QUE PRECISAM DO USUÁRIO ANTES DE EXECUTAR

1. **Estratégia de symlink (Fase 2.1):** cópia com hash de sincronismo vs. exigir Developer Mode vs. Junctions NTFS. Isso afeta como `aidd-forge`/`aidd-generator` escrevem `.claude/`, `.agent/`, `.cursor/` em **todo projeto gerado** pelo ecossistema, não só neste repositório — decisão de escopo amplo.
2. **`templates/v2/database.py` ausente (Fase 1.2):** confirmar se existe uma cópia recuperável em `proj_aidd` (mencionado no plano original como fonte homologada) antes de decidir entre reimplementar ou remover o teste órfão.
3. **Local do pacote compartilhado (Fase 3.1):** novo diretório `tools/_shared_core/` vs. `aidd-master-enterprise` depender de `aidd-master` via import direto (acopla as duas ferramentas, o que o `AGENTS.md` hoje trata como desacopladas).

---

## 5. RISCOS RESIDUAIS (fora do escopo deste plano)

- Não foi feita auditoria de profundidade em `aidd-master-enterprise/materiais-extras/examples/` (604 arquivos de projetos de exemplo) — pode conter os mesmos padrões de risco (duplicação, gates ausentes) em escala menor.
- Não foi verificada a paridade de conteúdo entre `.cursor/rules/aidd.md` e `AGENTS.md` além de checagem de existência.
- Este plano não cobre auditoria de qualidade do código gerado pelo pipeline do `aidd-generator` em si (apenas a integridade do próprio ecossistema orquestrador).
