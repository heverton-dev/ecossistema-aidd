# Auditoria de Etapa: Instalação de Dependências (v4, após correção dos Tickets 1, 2 e 3)

### [RECURSO]: Histórico v1 a v3 (verify, bootstrap, diagnóstico do impeccable, Tickets 1 e 2)
- **Ordem de Execução:** ETAPA_02, após o clone da ETAPA_01 (HEAD `89b4facc`).
- **Ação Executada:** resumo do que as versões anteriores fizeram. O detalhe está em `ETAPA_02-instalacao-de-dependencias.md` (v1), `_v2.md` e `_v3.md`.
  - v1: `verify` (exit 1, 42 pendências) e `bootstrap` (exit 1, hash do `impeccable`).
  - v2: causa comprovada (o instalador baixa o conteúdo atual de um servidor remoto; o hash fixado era da 4.3.1). Ticket 1: `sha256` atualizado.
  - v3: Ticket 2 (TDD): o `verify` distingue deriva de versão de adulteração, via `versao_esperada`.
- **Entrega / Artefato Gerado:** ambiente de dependências íntegro; `verify` com exit 0.
  - *Caminho Exato (100% concluído):* `FLUXO-PURE\scripts\gestor_dependencias.py`, `FLUXO-PURE\scripts\test_gestor_dependencias.py`, `FLUXO-PURE\modulos\04-nucleo-compartilhado\contracts\dependencias_externas.json`
- **Status & Diagnóstico:**
  - *Sucesso:* Sim.
  - *Falhas / Anomalias:*
    - *Ocorrência:* nenhuma pendente dos Tickets 1 e 2.
    - *Localização Exata do Erro:* N/A
  - *Ação Corretiva Cirúrgica:* Tickets 1 e 2, já resolvidos.

### [RECURSO]: Correção do Ticket 3 (TDD Red-Green em scripts/gestor_dependencias.py)
- **Ordem de Execução:** após a v3 e após a decisão de resolver os tickets abertos antes da ETAPA_03.
- **Ação Executada:**
  1. **Red:** 3 testes novos (`TestAddSkillVersaoEsperada`) em `scripts/test_gestor_dependencias.py`. `pytest -k AddSkillVersao` → exit 1; falharam 2 (parâmetro `versao_esperada` inexistente; flag `--versao-esperada` não reconhecida). O 3º, "omite o campo quando não informada", passou desde o início e serve de guarda de regressão. Log: `C:\Users\trcnologia\aidd-logs-red-t3.txt`.
  2. **Implementação** em `scripts/gestor_dependencias.py`:
     - `adicionar_skill(..., versao_esperada=None)`: grava `versao_esperada` na entrada só quando informada, para não alterar manifestos existentes.
     - `_cmd_add_skill` repassa `args_ns.versao_esperada`.
     - Parser: flag `--versao-esperada` (dest `versao_esperada`); linha de uso do cabeçalho atualizada.
  3. **Green:** `pytest scripts/test_gestor_dependencias.py` → exit 0, 31 passed. Log: `aidd-logs-green-t3.txt`.
- **Entrega / Artefato Gerado:** o `add-skill` não perde mais a verificação de deriva ao regravar uma skill.
  - *Caminho Exato (100% concluído):* `FLUXO-PURE\scripts\gestor_dependencias.py`, `FLUXO-PURE\scripts\test_gestor_dependencias.py`
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. Red falhou (exit 1) e Green passou (exit 0); os 28 testes anteriores continuam verdes.
  - *Falhas / Anomalias:*
    - *Ocorrência:* o primeiro Green falhou (1 failed, 30 passed). Causa: erro no meu stub de teste. O `bootstrap_skills` falso devolvia `{}`, e `_cmd_add_skill` lê `resultado["bootstrap"]["ja_instaladas"]`, gerando `KeyError`. O código de produção estava certo.
    - *Localização Exata do Erro:* `scripts/test_gestor_dependencias.py`, método `_preparar` da classe `TestAddSkillVersaoEsperada`.
  - *Ação Corretiva Cirúrgica:* o stub passou a devolver `{"ja_instaladas": [], "instaladas": [], "falhas": []}`.
  - *Limitação:* a flag foi verificada por teste unitário e pelo `--help` do CLI. Não rodei `add-skill` real contra o manifesto, porque o comando regrava a entrada e dispara o bootstrap.

### [RECURSO]: Refazer ETAPA_02 com o mecanismo real
- **Ordem de Execução:** após o Green do Ticket 3.
- **Ação Executada:** `python ecossistema.py dependencia verify` no clone → exit 0, "[SUCESSO] … 66 dependências" (log `aidd-logs-verify6.txt`). Mesmo `verify` no motor original, na branch `fix/pure-etapa-02-hash-impeccable`, com a skill local atualizada para 4.5.2 → exit 0.
- **Entrega / Artefato Gerado:** ETAPA_02 verde no clone e no original (branch de correção).
  - *Caminho Exato (100% concluído):* logs em `C:\Users\trcnologia\aidd-logs-*.txt`
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. Exit codes reais, capturados na mesma linha, sem pipe.
  - *Falhas / Anomalias:*
    - *Ocorrência:* o `verify` no original só passa na branch `fix/…`. Na `main` e na `docs/prompt-teste-real-fluxos` continua reprovando, até o merge. Isso é esperado pelo padrão de merge no fim do fluxo.
    - *Localização Exata do Erro:* N/A
  - *Ação Corretiva Cirúrgica:* nenhuma.

### [RECURSO]: Espelhamento no motor original (padrão de branches)
- **Ordem de Execução:** após o Green no clone.
- **Ação Executada:** os 2 arquivos do Ticket 3 foram copiados para o original, na branch `fix/pure-etapa-02-hash-impeccable` (diff +42/−3). `pytest` exit 0 (31 passed); `add-skill --help` exit 0 e mostra `--versao-esperada`; `verify` exit 0. Audit completo (gates, `python -X utf8 ecossistema.py audit`, com TEMP seguro) concluído: exit real 0 (`audit3_exit=0` em `aidd-logs-orig-audit3-exit.txt`), 65 gates aprovados em 10m03s (log `aidd-logs-orig-audit3.txt`). Commit `ab710ec0` na branch `fix/pure-etapa-02-hash-impeccable`, após aprovação do usuário; sem merge e sem push.
- **Entrega / Artefato Gerado:** Ticket 3 na branch de correção do original, sem commit.
  - *Caminho Exato (100% concluído):* `ecossistema-aidd\scripts\gestor_dependencias.py`, `ecossistema-aidd\scripts\test_gestor_dependencias.py`
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. `pytest` exit 0 (31 passed), `verify` exit 0 e audit completo exit 0 (65 gates). O commit foi feito com aprovação do usuário.
  - *Falhas / Anomalias:*
    - *Ocorrência:* nenhuma até o momento.
    - *Localização Exata do Erro:* N/A
  - *Ação Corretiva Cirúrgica:* N/A

## TICKETS
### Ticket 1: Hash do impeccable defasado — RESOLVIDO (v2)
- **Falha:** o manifesto fixava o hash do `SKILL.md` 4.3.1, e o instalador entrega o 4.5.2.
- **Artefato de Handoff:** `modulos/04-nucleo-compartilhado/contracts/dependencias_externas.json`
- **Requisito TDD (Red):** `verify` após `bootstrap` retornava exit 1 "hash SHA-256 divergente".
- **Implementação Técnica:**
  - `sha256` atualizado para `35c88304…d234c`.
- **Verificação (Green):** `bootstrap` e `verify` com exit 0.
- **Construtor Prompt (EN):**
  - Update the `sha256` of skill `impeccable` to the hash of the installed SKILL.md and run `python ecossistema.py dependencia verify`, asserting exit 0.

### Ticket 2: Deriva de versão x adulteração — RESOLVIDO (v3)
- **Falha:** qualquer atualização do upstream gerava "artefato pode ter sido adulterado".
- **Artefato de Handoff:** `scripts/gestor_dependencias.py`
- **Requisito TDD (Red):** `pytest -k Deriva` com exit 1 (6 failed).
- **Implementação Técnica:**
  - Helpers `_extrair_versao_frontmatter` e `_e_deriva_de_versao`; campo `versao_esperada`; mensagem diferenciada.
- **Verificação (Green):** `pytest scripts/test_gestor_dependencias.py` com exit 0.
- **Construtor Prompt (EN):**
  - Assert that `verificar()` reports "nova versao do upstream" when `versao_esperada` differs and the hash diverges, and "adulterado" otherwise; run pytest and assert exit 0.

### Ticket 3: `add-skill` perde `versao_esperada` ao regravar a skill (Refere-se a consistência do manifesto) — RESOLVIDO
- **Falha:** `adicionar_skill` recriava a entrada sem `versao_esperada`, desligando a distinção de deriva.
- **Artefato de Handoff:** `scripts/gestor_dependencias.py`
- **Requisito TDD (Red):** `pytest scripts/test_gestor_dependencias.py -k AddSkillVersao` → exit 1 (2 failed).
- **Implementação Técnica:**
  - Parâmetro opcional `versao_esperada` em `adicionar_skill`, repassado por `_cmd_add_skill`.
  - Flag `--versao-esperada` no parser de `add-skill`.
- **Verificação (Green):** `pytest scripts/test_gestor_dependencias.py` → exit 0 (31 passed); `add-skill --help` exit 0 mostrando a flag.
- **Construtor Prompt (EN):**
  - Add the optional `versao_esperada` parameter to `adicionar_skill` and the `--versao-esperada` CLI flag, writing the field only when provided.
  - Run `python -m pytest scripts/test_gestor_dependencias.py -q` and assert exit 0.
