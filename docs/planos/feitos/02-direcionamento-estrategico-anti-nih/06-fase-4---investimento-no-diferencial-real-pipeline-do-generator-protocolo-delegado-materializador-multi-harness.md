# Item 6 — Fase 4 - Investimento no diferencial real (pipeline do generator, protocolo delegado, materializador multi-harness)

> **Escopo:** Definir e priorizar melhorias concretas para os diferenciais do ecossistema sem equivalente de mercado: (1) Protocolo Delegado do Generator e (2) Materializador Multi-Harness (`componentes/` + fleet discovery).
> **Status:** [TODOS OS 6 SUB-ITENS CONCLUÍDOS EM 2026-09-08 — 6.1/6.3/6.4/6.5/6.6 via §1.1; 6.2 aprovado e implementado separadamente na mesma data]
> **Modelo sugerido:** Claude Opus · Antigravity Gemini 3.8 · MiMo mimo-v2.5-pro

---

## 1. Decisão de Alinhamento (2026-09-07)

- **Decisão do usuário (via `orca orchestration ask`):** Antecipar a definição, detalhamento e priorização dos itens de melhoria no planejamento, mantendo a **execução técnica travada** até que a reauditoria final da Fase 3 (Item 5) esteja concluída e publicada com prova antes/depois.
- **Motivo de governança:** Investir código novo sobre uma base em migração repete o erro original de construir features sobre fundações não verificadas. O mapeamento prévio reduz incerteza e permite execução imediata assim que a base pós-Fase 2 for atestada na Fase 3.

## 1.1 Registro de Aprovação de Execução (2026-09-08)

- **Contexto:** Fase 3 foi concluída e publicada em 2026-09-08 (`docs/relatorios/relatorio-reauditoria-fase3-antes-depois.html`), satisfazendo a precondição 2 da Seção 5. Uma auditoria (nesta mesma sessão, com Claude Code, sem subagentes, usando reprodução real de testes/gates) encontrou código de 6.1, 6.3, 6.4, 6.5 e 6.6 já escrito no working tree **sem** aprovação formal por sub-item registrada em documento algum — violando a precondição 3 da Seção 5.
- **Aprovação do usuário:** Nesta conversa, em 2026-09-08, após receber o relatório completo da auditoria (achados 1 a 6), o usuário instruiu explicitamente: *"I want you to make all the corrections, okay? All of them. From 1 to 6, everything. In fact, everything you found here, I want you to correct, please."* — cobrindo a regularização retroativa da execução de 6.1, 6.3, 6.4, 6.5 e 6.6 (código já correto e reproduzido, faltava só o registro de aprovação) e a correção da documentação. Esta é a aprovação formal por sub-item exigida pela precondição 3, registrada aqui com a citação exata para não fabricar aprovação nenhuma além do que foi realmente dito.
- **Não coberto por esta aprovação:** Item 6.2 (extensions nativas do Gemini CLI) — nenhum código foi escrito para ele, e ele não fazia parte dos achados da auditoria. Continua exigindo aprovação explícita própria antes de iniciar.

---

## 2. Diferenciais Reais Identificados (Sem Equivalente OSS)

Conforme a Seção 5 de `docs/features/oportunidades-reaproveitamento-oss-nih.md`:
1. **Protocolo Delegado do Generator:** Mecanismo autônomo em que o pipeline solicita e consome raciocínio do assistente/ADE ativo na sessão via arquivos JSON no disco, sem exigir chave de API externa nem dependência de SDK de terceiros.
2. **Materializador Multi-Harness:** Sincronizador determinístico com fonte física única (`componentes/`) que projeta skills, comandos, specs e regras nos formatos e árvores nativas de 7 harnesses (Claude Code, Antigravity, OpenCode, MimoCode, Gemini CLI, Cursor, Hermes).
3. **Fleet Discovery (Mecanismo Auxiliar):** Detecção estática e dinâmica de binários de agentes de IA instalados no host (`tools/aidd-generator/scripts/phases/utils_fleet_discovery.py`).

---

## 3. Matriz de Melhorias Concretas e Priorização

A ordem foi definida priorizando confiabilidade de comunicação entre processos (P1), conformidade de contratos multi-harness (P2) e observabilidade/performance (P3):

| Prioridade | ID | Diferencial | Melhoria Concreta | Complexidade |
|---|---|---|---|---|
| **P1** | **6.1** | Protocolo Delegado | Contrato formal com JSON Schema e validação estrita de payload | Média |
| **P1** | **6.2** | Materializador | Suporte nativo a extensions no Gemini CLI (`gemini-extension.json`) | Baixa |
| **P2** | **6.3** | Protocolo Delegado | Polling adaptativo orientável a eventos (file watcher / backoff) | Média |
| **P2** | **6.4** | Materializador | Detector de Drift Bidirecional (alertar edição manual fora de `componentes/`) | Baixa |
| **P3** | **6.5** | Fleet Discovery | Expansão de frota (Kiro CLI, Cursor subagents) e validação de paths no PATH | Baixa |
| **P3** | **6.6** | Protocolo Delegado | Estimativa local de tokens via tokenizer offline como telemetria auxiliar | Média |

---

## 4. Itens de Execução com Definição de Pronto (DpP)

### Item 6.1 — Contrato formal com JSON Schema no Protocolo Delegado (P1) [CONCLUÍDO]
- **Objetivo:** Substituir a validação implícita de campos (`"conteudo" in dados`) em `tools/aidd-generator/scripts/phases/utils_delegacao.py` por validação formal via JSON Schema (`jsonschema`).
- **Definição de Pronto (DpP):**
  1. [x] Esquema JSON formal para `_llm_request_*.json` e `_llm_response_*.json` definido e versionado em `schemas/` (`tools/aidd-generator/scripts/phases/schemas/llm_request_v1.json`, `llm_response_v1.json`, `registry.py`).
  2. [x] `utils_delegacao.py` valida requisições antes da escrita e respostas antes do consumo via `schemas.registry` (`SchemaValidationError`), rejeitando payloads truncados ou malformados com erro legível.
  3. [x] Preservação mandatória do campo `origem_medicao: "autodeclarado"` para respostas delegadas.
  4. [x] Testes unitários com casos de payload válido, incompleto e inválido passando com 100% de sucesso.
  - **Evidência de validação (reproduzida em 2026-09-08):** `pytest tools/aidd-generator/tests/test_schemas_delegacao.py` → **29/29 passed**.

### Item 6.3 — Polling adaptativo e event-driven no Protocolo Delegado (P2) [CONCLUÍDO]
- **Objetivo:** Eliminar o busy wait com sleep rígido de 1s/5s em `aguardar_resposta()`, adotando backoff adaptativo e verificação assíncrona/watcher de sistema de arquivos quando disponível.
- **Definição de Pronto (DpP):**
  1. [x] Timeout configurável por fase (`aguardar_resposta(..., timeout=timeout_efetivo, fase=fase)`).
  2. [x] Polling escalonado: 100ms inicial (`INTERVALO_POLLING_INICIAL`), escalando por fator 1.5 (`FATOR_BACKOFF_POLLING`) até teto de 1s (`INTERVALO_POLLING_MAX`).
  3. [x] File watcher event-driven via `watchdog` (`Observer`/`FileSystemEventHandler`) quando a biblioteca está disponível, com fallback determinístico para o polling escalonado quando não está.
  4. [x] Suíte de testes do generator passando sem atrasos artificiais.
  - **Evidência de validação (reproduzida em 2026-09-08):** `pytest tools/aidd-generator/tests/test_utils_delegacao.py` → **42/42 passed em 0.91s** (sem sleeps artificiais na suíte). Nota: a DpP original citava `tests/test_delegacao.py`; o arquivo real é `test_utils_delegacao.py` — corrigido aqui para não deixar referência a um caminho que não existe.

### Item 6.2 — Conformidade de Extensions Nativas no Gemini CLI (P1) [CONCLUÍDO]
- **Objetivo:** Migrar o suporte ao Gemini CLI no manifesto (`gates/manifesto_harnesses.json`) do diretório não documentado `.gemini/skills/` para o padrão oficial de extensions (`.gemini/extensions/<nome>/gemini-extension.json` e comandos `.toml`).
- **Aprovação registrada (2026-09-08):** usuário aprovou explicitamente este item nesta sessão, após confirmar que o formato já estava mapeado (schema real obtido de `geminicli.com/docs/extensions/writing-extensions/` via WebFetch nesta mesma sessão) e que era só implementação, sem pesquisa em aberto.
- **Definição de Pronto (DpP):**
  1. [x] Template de extension implementado no gerador de componentes (`scripts/gestor_componentes.py`): novo campo genérico `dest_harness_template_overrides` (destino aninhado `extensions/<nome>/skills/<nome>/` só para este harness, sem afetar os outros 6) e `manifestos_extra_por_harness` (gera `gemini-extension.json` deterministicamente a partir do nome do componente, sem fonte 1:1 em `componentes/`). Comando `.toml`: **não aplicável agora** — `command` já excluía `gemini-cli` antes desta correção (formato incompatível, `.toml` vs `.md`) e nenhum comando deste manifesto está migrado para lá; nada usa esse destino hoje, então não há o que testar sem fabricar um comando só pra isso.
  2. [x] Manifesto `gates/manifesto_harnesses.json` atualizado com `confirmado: true` para o Gemini CLI.
  3. [x] `python ecossistema.py components sync --tipo todos` materializa a estrutura de extensions (48/48 componentes) sem alterar os outros 6 harnesses (conferido: `.claude/skills/<nome>/` continua no formato antigo, inalterado).
  4. [x] Testes de regressão em `gates/G_HARNESS_COMPAT.py` e `gates/G_COMPONENTE_AGNOSTICO.py` aprovados (exit 0).
  - **Evidência de validação (reproduzida em 2026-09-08):** os 2 gates acima + `gates/G_SEGREDOS.py` aprovados; `gates/test_gestor_componentes_drift.py` com 2 testes novos cobrindo geração e drift do `gemini-extension.json` — **5/5 passed**; teste negativo manual (corromper `gemini-extension.json` de propósito → `components verify` detectou → `components sync --force` restaurou o conteúdo correto).

### Item 6.3 — Polling adaptativo e event-driven no Protocolo Delegado (P2)
- **Objetivo:** Eliminar o busy wait com sleep rígido de 1s/5s em `aguardar_resposta()`, adotando backoff adaptativo e verificação assíncrona/watcher de sistema de arquivos quando disponível.
- **Definição de Pronto (DpP):**
  1. Timeout configurável por fase (fases de implementação suportam timeouts maiores sem travar threads).
  2. Polling escalonado (100ms inicial para respostas instantâneas, subindo progressivamente para reduzir I/O de disco).
  3. Fallback limpo e determinístico para headless quando timeout expirar (sem crash nem perda de contexto).
  4. Suíte de testes do generator (`pytest tests/test_delegacao.py`) passando sem atrasos artificiais.

### Item 6.4 — Detector de Drift Bidirecional no Materializador Multi-Harness (P2) [CONCLUÍDO]
- **Objetivo:** Adicionar checagem determinística em `ecossistema.py components verify` para alertar se arquivos em destinos gerados (`.claude/`, `.agents/`, `.cursor/`, etc.) foram modificados diretamente sem reflexo em `componentes/`.
- **Definição de Pronto (DpP):**
  1. [x] Algoritmo de hash/checksum SHA-256 comparando destinos gerados contra os fontes canônicos em `componentes/`.
  2. [x] Comando `python ecossistema.py components verify` reporta arquivo modificado, arquivo órfão e arquivo divergente.
  3. [x] Opção de force-sync para restaurar a integridade a partir de `componentes/`.
  4. [x] Gate `gates/G_HARNESS_COMPAT.py` integrado à verificação de drift bidirecional.
  - **Evidência de validação:** Suíte determinística em `gates/test_gestor_componentes_drift.py` passando (3/3 testes), `gates/G_HARNESS_COMPAT.py` aprovado (100% OK), e `python ecossistema.py components verify --tipo todos` validando os 48 componentes.

### Item 6.5 — Expansão e Robustecimento do Fleet Discovery (P3) [CONCLUÍDO]
- **Objetivo:** Atualizar `utils_fleet_discovery.py` para mapear novos runtimes emergentes (Kiro CLI, Cursor subagents, hermes) e sanitizar resolução de binários em Windows/POSIX.
- **Definição de Pronto (DpP):**
  1. [x] Registro de Kiro CLI e Hermes Agent nos dicionários de agentes conhecidos (`AGENTES_CONHECIDOS`/`KNOWN_AGENTS`) com flags de detecção, nos 3 pontos de fleet discovery (`aidd-generator`, `aidd-enterprise`, `aidd-master`). Binário `hermes` confirmado como real e já documentado no ecossistema (`utils_modelo.py`, `AGENTS.md:140`, `HARNESS-COMPAT.json`), não inventado.
     - **Correção de escopo (2026-09-08):** "Cursor subagents" **não** foi adicionado como alvo de detecção binária separado. Investigação real (`gates/manifesto_harnesses.json:38`, citando a documentação oficial `cursor.com/docs/subagents`) confirma que subagents do Cursor são arquivos (`.cursor/agents/<nome>.md`) consumidos pelo mesmo binário `cursor` já registrado — não existe um executável distinto para descobrir no host. Tratá-lo como novo "binário" seria uma alegação fabricada (viola a Lei de Zero Alucinação do próprio ecossistema, `AGENTS.md`). A distribuição do formato `.cursor/agents/` já é responsabilidade do materializador multi-harness (`gates/manifesto_harnesses.json` + `gates/G_HARNESS_COMPAT.py`), não do fleet discovery.
  2. [x] Tratamento estrito de extensões (`.cmd`, `.ps1`, `.bat`, binários nativos) em ambientes Windows — `_encontrar_executavel_windows`/`_resolve_executable`.
  3. [x] Testes unitários em `tests/test_fleet_discovery.py` (3 arquivos) atualizados e cobrindo os novos alvos sem mocks fantasiosos.
  - **Evidência de validação (reproduzida em 2026-09-08):** `pytest` real por ferramenta — `aidd-enterprise`: 36/36 passed; `aidd-master`: 36/36 passed; `aidd-generator`: 34/34 passed (105 testes reais no total). `fleet_discovery.py` de `aidd-enterprise`/`aidd-master` continua byte-idêntico entre si — **já monitorado** por `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` (baseline `esperado_identico: true`, gate verde após esta correção), não é débito em aberto (ver `00-PROCESSO-E-DECISOES.md`).

### Item 6.6 — Telemetria Auxiliar Offline de Tokens (P3) [CONCLUÍDO]
- **Objetivo:** Fornecer contagem auxiliar e determinística de tokens locais via biblioteca offline (ex: `tiktoken`), mantendo estritamente o rótulo de transparência.
- **Definição de Pronto (DpP):**
  1. [x] Cálculo de tokens do payload de entrada e saída via `tiktoken` adicionado no retorno com o campo explícito `tokens_estimativa_local` (`entrada`, `saida`, `total`, `tokenizer`, `metodo`).
  2. [x] Mantido rigorosamente o campo `origem_medicao: "autodeclarado"` para a resposta do agente remoto, evitando qualquer alegação enganosa de "medição de billing real".
  3. [x] Documentação atualizada em `docs/PRINCIPIO-UNIVERSALIDADE.md`.
  - **Evidência de validação:** 35 testes em `tools/aidd-generator/tests/test_utils_delegacao.py` e 4 testes em `test_transparencia_tokens.py` passando (100% verde).

---

## 5. Regra de Governança para Início da Implementação

Nenhum dos sub-itens acima (6.1 a 6.6) pode ter seu código implementado antes de:
1. Conclusão das migrações da Fase 2 (Troca de motor).
2. Publicação e homologação do relatório final da Fase 3 (Item 5 — Reauditoria sem maquiagem pós-troca de motor com heatmap comparativo antes → depois).
3. Aprovação formal do usuário para o início do sub-item específico.

---

## 6. Criterio de Saida deste Item 6

- [x] Consulta e aprovação formal do usuário via `orca orchestration ask` realizada.
- [x] Lista de melhorias concretas dos 2 diferenciais reais definida e detalhada.
- [x] Priorização sequenciada (P1, P2, P3) travada.
- [x] Cada sub-item possui Definição de Pronto (DpP) atômica e checável.
- [x] Trava de dependência da Fase 3 registrada sem ambiguidades.
- [x] Registro de progresso em `00-PROCESSO-E-DECISOES.md` atualizado.

