# Item 6 — Fase 4 - Investimento no diferencial real (pipeline do generator, protocolo delegado, materializador multi-harness)

> **Escopo:** Definir e priorizar melhorias concretas para os diferenciais do ecossistema sem equivalente de mercado: (1) Protocolo Delegado do Generator e (2) Materializador Multi-Harness (`componentes/` + fleet discovery).
> **Status:** [DEFINIÇÃO CONCLUÍDA / APROVADA EM 2026-09-07 — Execução travada para pós-Fase 3 (Item 5)]
> **Modelo sugerido:** Claude Opus · Antigravity Gemini 3.8 · MiMo mimo-v2.5-pro

---

## 1. Decisão de Alinhamento (2026-09-07)

- **Decisão do usuário (via `orca orchestration ask`):** Antecipar a definição, detalhamento e priorização dos itens de melhoria no planejamento, mantendo a **execução técnica travada** até que a reauditoria final da Fase 3 (Item 5) esteja concluída e publicada com prova antes/depois.
- **Motivo de governança:** Investir código novo sobre uma base em migração repete o erro original de construir features sobre fundações não verificadas. O mapeamento prévio reduz incerteza e permite execução imediata assim que a base pós-Fase 2 for atestada na Fase 3.

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

### Item 6.1 — Contrato formal com JSON Schema no Protocolo Delegado (P1)
- **Objetivo:** Substituir a validação implícita de campos (`"conteudo" in dados`) em `tools/aidd-generator/scripts/phases/utils_delegacao.py` por validação formal via JSON Schema (`jsonschema`).
- **Definição de Pronto (DpP):**
  1. Esquema JSON formal para `_llm_request_*.json` e `_llm_response_*.json` definido e versionado em `schemas/`.
  2. `utils_delegacao.py` valida requisições antes da escrita e respostas antes do consumo, rejeitando payloads truncados ou malformados com erro legível.
  3. Preservação mandatória do campo `origem_medicao: "autodeclarado"` para respostas delegadas.
  4. Testes unitários com casos de payload válido, incompleto e inválido passando com 100% de sucesso.

### Item 6.2 — Conformidade de Extensions Nativas no Gemini CLI (P1)
- **Objetivo:** Migrar o suporte ao Gemini CLI no manifesto (`gates/manifesto_harnesses.json`) do diretório não documentado `.gemini/skills/` para o padrão oficial de extensions (`.gemini/extensions/<nome>/gemini-extension.json` e comandos `.toml`).
- **Definição de Pronto (DpP):**
  1. Template de extension e comando TOML implementado no gerador de componentes (`scripts/gestor_componentes.py`).
  2. Manifesto `gates/manifesto_harnesses.json` atualizado com `confirmado: true` para o Gemini CLI.
  3. `python ecossistema.py components sync` materializa a estrutura de extensions sem quebrar os outros 6 harnesses.
  4. Testes de regressão em `gates/G_HARNESS_COMPAT.py` e `gates/G_COMPONENTE_AGNOSTICO.py` aprovados (exit 0).

### Item 6.3 — Polling adaptativo e event-driven no Protocolo Delegado (P2)
- **Objetivo:** Eliminar o busy wait com sleep rígido de 1s/5s em `aguardar_resposta()`, adotando backoff adaptativo e verificação assíncrona/watcher de sistema de arquivos quando disponível.
- **Definição de Pronto (DpP):**
  1. Timeout configurável por fase (fases de implementação suportam timeouts maiores sem travar threads).
  2. Polling escalonado (100ms inicial para respostas instantâneas, subindo progressivamente para reduzir I/O de disco).
  3. Fallback limpo e determinístico para headless quando timeout expirar (sem crash nem perda de contexto).
  4. Suíte de testes do generator (`pytest tests/test_delegacao.py`) passando sem atrasos artificiais.

### Item 6.4 — Detector de Drift Bidirecional no Materializador Multi-Harness (P2)
- **Objetivo:** Adicionar checagem determinística em `ecossistema.py components verify` para alertar se arquivos em destinos gerados (`.claude/`, `.agents/`, `.cursor/`, etc.) foram modificados diretamente sem reflexo em `componentes/`.
- **Definição de Pronto (DpP):**
  1. Algoritmo de hash/checksum SHA-256 comparando destinos gerados contra os fontes canônicos em `componentes/`.
  2. Comando `python ecossistema.py components verify` reporta arquivo modificado, arquivo órfão e arquivo divergente.
  3. Opção de force-sync para restaurar a integridade a partir de `componentes/`.
  4. Gate `gates/G_HARNESS_COMPAT.py` integrado à verificação de drift bidirecional.

### Item 6.5 — Expansão e Robustecimento do Fleet Discovery (P3)
- **Objetivo:** Atualizar `utils_fleet_discovery.py` para mapear novos runtimes emergentes (Kiro CLI, Cursor subagents, hermes) e sanitizar resolução de binários em Windows/POSIX.
- **Definição de Pronto (DpP):**
  1. Registro de Kiro CLI e Cursor nos dicionários de agentes conhecidos com flags de detecção.
  2. Tratamento estrito de extensões (`.cmd`, `.ps1`, `.bat`, binários nativos) em ambientes Windows.
  3. Testes unitários em `tests/test_fleet_discovery.py` atualizados e cobrindo os novos alvos sem mocks fantasiosos.

### Item 6.6 — Telemetria Auxiliar Offline de Tokens (P3)
- **Objetivo:** Fornecer contagem auxiliar e determinística de tokens locais via biblioteca offline (ex: `tiktoken`), mantendo estritamente o rótulo de transparência.
- **Definição de Pronto (DpP):**
  1. Cálculo de tokens do payload de entrada e saída via `tiktoken` adicionado no retorno com o campo explícito `tokens_estimativa_local`.
  2. Mantido rigorosamente o campo `origem_medicao: "autodeclarado"` para a resposta do agente remoto, evitando qualquer alegação enganosa de "medição de billing real".
  3. Documentação atualizada em `docs/PRINCIPIO-UNIVERSALIDADE.md`.

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

