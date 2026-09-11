# PROCESSO E DECISOES — resiliencia-concorrencia-e-integridade

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

- **Origem:** Auditoria de Resiliência, Concorrência e Integridade Transacional registrada em `docs/relatorios/RESILIENCIA-CONCORRENCIA-BASELINE.md` (2026-09-09).
- **Objetivo Principal:** Eliminar vulnerabilidades críticas de concorrência e corrupção de estado: implementar claim atômico e dead-letter no Outbox pattern, criar utilitário compartilhado de gravação atômica (`staging -> os.replace -> rollback`) para os 8 pontos críticos de filesystem, introduzir máquina de estados e retomada inteligente (`--resume`) no pipeline do generator, e blindar o SQLite contra `SQLITE_BUSY` com retries exponenciais e pool explícito.
- **Limites de Escopo:**
  - Não inclui deduplicação genérica de código (já coberta pelos planos em `fazendo/`).
  - Foca estritamente na confiabilidade de runtime, isolamento transacional e recuperação pós-falha.
  - Toda mitigação deve ser comprovada por testes com injeção de falha simulada.

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | outbox-claim-atomico-retry-e-dead-letter | `01-outbox-claim-atomico-retry-e-dead-letter.md` |
| 2 | escritor-atomico-compartilhado-e-migracao-fs | `02-escritor-atomico-compartilhado-e-migracao-fs.md` |
| 3 | maquina-estados-pipeline-generator-e-resume | `03-maquina-estados-pipeline-generator-e-resume.md` |
| 4 | retry-backoff-sqlite-busy-e-pool-explicito | `04-retry-backoff-sqlite-busy-e-pool-explicito.md` |
| 5 | fila-unica-revalidacao-read-model-cache | `05-fila-unica-revalidacao-read-model-cache.md` |
| 6 | registry-writers-com-lock-e-rename-atomico | `06-registry-writers-com-lock-e-rename-atomico.md` |
| 7 | checkpoint-persistencia-result-ops-deploy | `07-checkpoint-persistencia-result-ops-deploy.md` |
| 8 | journal-recuperacao-pos-crash-multi-arquivo | `08-journal-recuperacao-pos-crash-multi-arquivo.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Documento |
|---|---|---|---|
| 1 | outbox-claim-atomico-retry-e-dead-letter | ⏳ Rascunho — parte ja implementada (ver auditoria) | `01-outbox-claim-atomico-retry-e-dead-letter.md` |
| 2 | escritor-atomico-compartilhado-e-migracao-fs | ⏳ Rascunho gerado, aguardando aprovacao | `02-escritor-atomico-compartilhado-e-migracao-fs.md` |
| 3 | maquina-estados-pipeline-generator-e-resume | ⏳ Rascunho — parte ja implementada (ver auditoria) | `03-maquina-estados-pipeline-generator-e-resume.md` |
| 4 | retry-backoff-sqlite-busy-e-pool-explicito | ⏳ Rascunho gerado, aguardando aprovacao | `04-retry-backoff-sqlite-busy-e-pool-explicito.md` |
| 5 | fila-unica-revalidacao-read-model-cache | ⏳ Rascunho gerado, aguardando aprovacao | `05-fila-unica-revalidacao-read-model-cache.md` |
| 6 | registry-writers-com-lock-e-rename-atomico | ⏳ Rascunho gerado, aguardando aprovacao | `06-registry-writers-com-lock-e-rename-atomico.md` |
| 7 | checkpoint-persistencia-result-ops-deploy | ⏳ Rascunho gerado, aguardando aprovacao | `07-checkpoint-persistencia-result-ops-deploy.md` |
| 8 | journal-recuperacao-pos-crash-multi-arquivo | ⏳ Rascunho gerado, aguardando aprovacao | `08-journal-recuperacao-pos-crash-multi-arquivo.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
