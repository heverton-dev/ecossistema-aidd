# Auditoria de Etapa: Configuração de Ambiente (v4, versão final com os Tickets 1, 2 e 3 resolvidos e commitados)

### [RECURSO]: Histórico v1 a v3 (cópia do .env, Tickets 1 e 2, primeira versão do Ticket 3)
- **Ordem de Execução:** após a ETAPA_02 (v4).
- **Ação Executada:** resumo; o detalhe está em `ETAPA_03-configuracao-de-ambiente.md` (v1), `_v2.md` e `_v3.md`.
  - v1: `.env` copiado do original (30 variáveis: 27 preenchidas, 3 vazias; valores não registrados). Anomalia: `.env` não ignorado no clone.
  - v2: Ticket 1 resolvido (`.env`, `.env.*` e `!.env.example` no `.gitignore`, com teste hermético). Ticket 2 resolvido por diagnóstico. Ticket 3 aberto (dry-run criava `projetos/<slug>/`).
  - v3: Ticket 3 resolvido no clone com `if not self.dry_run` em `orquestrador_sincrono.py:230`, mas com um teste que importava o orquestrador (corrigido nesta v4).
- **Entrega / Artefato Gerado:** ambiente configurado e protegido.
  - *Caminho Exato (100% concluído):* `FLUXO-PURE\.env`, `FLUXO-PURE\.gitignore`, `FLUXO-PURE\scripts\test_gitignore_env.py`, `FLUXO-PURE\scripts\orquestrador_sincrono.py`
- **Status & Diagnóstico:**
  - *Sucesso:* Sim.
  - *Falhas / Anomalias:*
    - *Ocorrência:* nenhuma pendente.
    - *Localização Exata do Erro:* N/A
  - *Ação Corretiva Cirúrgica:* Tickets 1, 2 e 3.

### [RECURSO]: Falha do audit do original com o teste da v3 (gates de mapa)
- **Ordem de Execução:** ao espelhar o Ticket 3 no original (`fix/pure-etapa-03-dryrun-sem-mkdir`).
- **Ação Executada:** `python -X utf8 ecossistema.py audit` (TEMP seguro) com o teste da v3, que importava `orquestrador_sincrono`.
- **Entrega / Artefato Gerado:** diagnóstico da falha.
  - *Caminho Exato (100% concluído):* `C:\Users\trcnologia\aidd-logs-orig-audit5.txt` e `aidd-logs-orig-audit6.txt`
- **Status & Diagnóstico:**
  - *Sucesso:* Não. O audit 5 e o audit 6 deram exit real 1 (62 gates aprovados, 3 reprovados), embora a notificação da tarefa dissesse "exit 0".
  - *Falhas / Anomalias:*
    - *Ocorrência:* `G_mapa_pecas`, `G_aidd_visual_maps` e `G_PORTAO_PROVA_QUE_MORDE` reprovaram. Meu teste novo em `scripts/` importava o orquestrador, e o catálogo factual (`catalogo-pecas.json`) registrou isso como `"scripts"` em `chamado_por`; o catálogo, os mapas `indice` e `scripts` e o `MANIFESTO-MAPAS.json` (hashes) ficaram desatualizados.
    - *Localização Exata do Erro:* `docs/auditoria/mapa-pecas/catalogo-pecas.json` (linha ~3029, lista `chamado_por`); `docs/mapas-visuais/mapa-00-indice.html` e `mapa-10-scripts.html` (e as versões `nao-tecnicos/`); `docs/mapas-visuais/MANIFESTO-MAPAS.json`.
  - *Ação Corretiva Cirúrgica:*
    - Primeira tentativa (audit 6): regenerei o catálogo (`catalogo_pecas.py`) e os mapas `indice` e `scripts`. Não bastou, pois o manifesto de hashes também exigiria `visual-maps gerar` (compila o livro com pandoc e typst).
    - Segunda tentativa (definitiva): desfiz a regeneração (`git checkout` dos arquivos de catálogo e mapas) e reescrevi o teste, descrito no recurso seguinte.

### [RECURSO]: Correção final do Ticket 3 (teste pelo mecanismo real)
- **Ordem de Execução:** após o diagnóstico acima.
- **Ação Executada:**
  1. Teste reescrito: `scripts/test_orquestrador_sincrono_dryrun.py` roda `python ecossistema.py pure --nome "Teste Dry" --slug teste-dry --dominio gestao --pasta <tmp>/projetos/teste-dry --dry-run` por subprocess e afirma `returncode == 0` e pasta inexistente. Não importa o orquestrador, então o catálogo não muda.
  2. **Red:** com o `mkdir` original restaurado, `pytest` → exit 1; o assert falhou por `pasta.exists()` verdadeiro (log `aidd-logs-red-e3t3b.txt`).
  3. **Green:** com `if not self.dry_run:` aplicado, `pytest` → exit 0 (log `aidd-logs-green-e3t3b.txt`).
  4. No original: `catalogo_pecas.py --check` em dia; `G_mapa_pecas` exit 0; `G_aidd_visual_maps` exit 0; `pytest` exit 0.
  5. Audit completo (audit 7): exit real 0 (`audit7_exit=0`), 65 gates aprovados em 6m50s.
  6. Commit `925bac15` na branch `fix/pure-etapa-03-dryrun-sem-mkdir` (hooks passaram, `core.bare` false, worktree limpo), com aprovação do usuário. Sem merge e sem push.
- **Entrega / Artefato Gerado:** dry-run sem efeito no disco, testado pelo comando real.
  - *Caminho Exato (100% concluído):* `ecossistema-aidd\scripts\orquestrador_sincrono.py`, `ecossistema-aidd\scripts\test_orquestrador_sincrono_dryrun.py`
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. Red (exit 1), Green (exit 0), gates de mapa (exit 0) e audit completo (exit 0).
  - *Falhas / Anomalias:*
    - *Ocorrência:* Nenhuma.
    - *Localização Exata do Erro:* N/A
  - *Ação Corretiva Cirúrgica:* N/A
  - *Observação:* o teste Green no clone foi o mesmo arquivo copiado ao original; o clone ainda não está commitado.

### [RECURSO]: Prompt vivo (docs/prompts)
- **Ordem de Execução:** após o audit 7.
- **Ação Executada:** na branch `docs/prompt-teste-real-fluxos` incluí a seção 3.3 ("Resolver no ato" e "teste pelo mecanismo real, para não alterar o catálogo") e a linha do registro de alterações. A mudança está no working tree, sem commit.
- **Entrega / Artefato Gerado:** regra nova no prompt.
  - *Caminho Exato (100% concluído):* `ecossistema-aidd\docs\prompts\13-10-2026_prompt-teste-real-fluxos-aidd.md`
- **Status & Diagnóstico:**
  - *Sucesso:* Sim, até o commit, que aguarda aprovação.
  - *Falhas / Anomalias:*
    - *Ocorrência:* Nenhuma.
    - *Localização Exata do Erro:* N/A
  - *Ação Corretiva Cirúrgica:* N/A

## TICKETS
### Ticket 1: `.env` sem regra no .gitignore versionado — RESOLVIDO (commit `61377f1c`, branch `fix/pure-etapa-03-gitignore-env`)
- **Falha:** o `.gitignore` não ignorava `.env`.
- **Artefato de Handoff:** `.gitignore`
- **Requisito TDD (Red):** `pytest scripts/test_gitignore_env.py` → exit 1 (2 failed).
- **Implementação Técnica:**
  - Linhas `.env`, `.env.*` e `!.env.example`; teste hermético.
- **Verificação (Green):** `pytest scripts/test_gitignore_env.py` → exit 0 (3 passed); audit completo exit 0 (65 gates).
- **Construtor Prompt (EN):**
  - Add `.env`, `.env.*` and `!.env.example` to the root `.gitignore` and run `python -m pytest scripts/test_gitignore_env.py -q`, asserting exit 0.

### Ticket 2: Variáveis exigidas pelo PURE — RESOLVIDO (sem mudança de código)
- **Falha:** não se sabia se faltava variável para o PURE.
- **Artefato de Handoff:** `.env.example`
- **Requisito TDD (Red):** não aplicável (dry-run exit 0, sem falha reproduzível).
- **Implementação Técnica:**
  - Nenhuma; diagnóstico por dry-run e varredura de `os.environ`.
- **Verificação (Green):** `python ecossistema.py pure "Teste Dry" gestao --dry-run` → exit 0.
- **Construtor Prompt (EN):**
  - If a real PURE run fails on a missing environment variable, add a failing check for it and document it in `.env.example`.

### Ticket 3: Dry-run cria `projetos/<slug>/` vazio — RESOLVIDO (commit `925bac15`, branch `fix/pure-etapa-03-dryrun-sem-mkdir`)
- **Falha:** `pure --dry-run` criava a pasta do projeto (`scripts/orquestrador_sincrono.py:230`).
- **Artefato de Handoff:** `scripts/orquestrador_sincrono.py`
- **Requisito TDD (Red):** `pytest scripts/test_orquestrador_sincrono_dryrun.py` → exit 1 (pasta existe após o dry-run).
- **Implementação Técnica:**
  - `mkdir` protegido por `if not self.dry_run`.
  - Teste via subprocess do comando real, sem importar o orquestrador.
- **Verificação (Green):** o teste → exit 0; `G_mapa_pecas` e `G_aidd_visual_maps` → exit 0; audit completo exit 0 (65 gates).
- **Construtor Prompt (EN):**
  - Guard the `mkdir` in `etapa_01_forge` with `if not self.dry_run`.
  - Test it by running the real `pure ... --dry-run` command via subprocess, never by importing the orchestrator, then run `python -m pytest scripts/test_orquestrador_sincrono_dryrun.py -q` asserting exit 0.

---

## EMENDA (13/10/2026, ETAPA_09, Ticket 7 da ETAPA_05; executada em modo autônomo)

**Correção de diagnóstico:** o Ticket 2 deste relatório ("Variáveis exigidas pelo PURE — RESOLVIDO (sem mudança de código)") afirmou, com base no dry-run e numa varredura de `os.environ`, que o PURE não lia variável do `.env`. Isso estava **errado**: o `aidd-planner` lê `MOBBIN_API_KEY` e `MOBBIN_API_URL` (`mobbin_client.py`) e, desde a ETAPA_08, também as variáveis de deploy (`VPS_HOST`, `VPS_USER`, `SSH_KEY_PATH` ou `VPS_PASSWORD`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ZONE_ID`, `DEFAULT_ROOT_DOMAIN`). A varredura não incluiu o diretório do planner e o `--dry-run` não executa o planner, por isso não mostrou nada.

**Causa:** varredura incompleta (o planner ficou fora) e prova insuficiente (o dry-run não exercita a etapa 2).
**Regra daqui em diante:** a varredura de `os.environ`/`getenv` cobre todos os módulos `modulos/**` e o `.env.example` deve listar tudo o que ela achar; o dry-run não vale como prova de que uma variável não é lida.
**Estado atual:** o planner bloqueia por variável de deploy ausente (ETAPA_08) e o `.env.example` avisa disso (ETAPA_09).
