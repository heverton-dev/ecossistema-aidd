# Auditoria de Etapa: Instalação de Dependências (v3, após correção dos Tickets 1 e 2)

### [RECURSO]: python ecossistema.py dependencia verify + bootstrap (histórico v1/v2)
- **Ordem de Execução:** 1º acionamento da ETAPA_02, após o clone da ETAPA_01 (HEAD `89b4facc`).
- **Ação Executada:** `verify` inicial (exit 1, 42 pendências) → `bootstrap` (14 skills e 27 registros de MCP; exit 1 por hash do `impeccable`). Detalhes em `ETAPA_02-instalacao-de-dependencias.md` (v1) e `_v2.md`.
- **Entrega / Artefato Gerado:** ambiente instalado; Ticket 1 resolvido na v2 (hash atualizado para o `SKILL.md` 4.5.2).
  - *Caminho Exato (100% concluído):* `FLUXO-PURE\.claude\skills\`, `FLUXO-PURE\.agents\mcp_config.json`, `FLUXO-PURE\.mcp.json`, `FLUXO-PURE\mimocode.jsonc`
- **Status & Diagnóstico:**
  - *Sucesso:* Sim (após o Ticket 1).
  - *Falhas / Anomalias:*
    - *Ocorrência:* hash do `impeccable` defasado (4.3.1 fixado, 4.5.2 entregue pelo instalador remoto).
    - *Localização Exata do Erro:* `modulos/04-nucleo-compartilhado/contracts/dependencias_externas.json:9`
  - *Ação Corretiva Cirúrgica:* Ticket 1 (v2).

### [RECURSO]: Correção do Ticket 2 (TDD Red-Green em scripts/gestor_dependencias.py)
- **Ordem de Execução:** após a v2, seguindo o Ticket 2 e a opção (a) já proposta (fixar também a `version:` esperada).
- **Ação Executada:**
  1. **Red:** 6 testes novos em `scripts/test_gestor_dependencias.py` (classe `TestDerivaDeVersaoVsAdulteracao`). `pytest -k Deriva` → exit 1, 6 failed (log: `C:\Users\trcnologia\aidd-logs-red.txt`).
  2. **Implementação** em `scripts/gestor_dependencias.py`:
     - `_extrair_versao_frontmatter(caminho)`: lê `version:` do frontmatter do `SKILL.md`.
     - `_e_deriva_de_versao(cfg)`: True se o manifesto declara `versao_esperada` e o arquivo traz outra versão.
     - `_checar_hash_skill`: na divergência, acrescenta "versao esperada X obtida Y" quando for deriva.
     - `verificar()`: mensagem "divergente por nova versao do upstream … atualize 'sha256' e 'versao_esperada'" em vez de "artefato pode ter sido adulterado" quando for deriva. Sem `versao_esperada` ou com a mesma versão, mantém a mensagem de adulteração.
  3. Manifesto: campo novo `"versao_esperada": "4.5.2"` no `impeccable` (linha 10).
  4. **Green:** `pytest scripts/test_gestor_dependencias.py` → exit 0, 28 passed (log: `aidd-logs-green2.txt`).
- **Entrega / Artefato Gerado:** verificação de integridade que separa deriva de versão de adulteração. O hash continua bloqueando nos dois casos.
  - *Caminho Exato (100% concluído):* `FLUXO-PURE\scripts\gestor_dependencias.py`, `FLUXO-PURE\scripts\test_gestor_dependencias.py`, `FLUXO-PURE\modulos\04-nucleo-compartilhado\contracts\dependencias_externas.json`
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. Teste Red falhou antes (exit 1) e passou depois (exit 0). Os 22 testes preexistentes continuam verdes.
  - *Falhas / Anomalias:*
    - *Ocorrência:* um erro meu no teste Red inicial: chamei `verificar_dependencias()`, que não existe; a função real é `verificar()` e devolve `(total, problemas)`. Corrigido antes da implementação.
    - *Localização Exata do Erro:* `scripts/test_gestor_dependencias.py`, método `test_verify_usa_mensagem_de_deriva_nao_de_adulteracao`.
  - *Ação Corretiva Cirúrgica:* teste corrigido para usar `verificar()`.
  - *Limitação conhecida:* `add-skill` regrava a entrada da skill sem `versao_esperada` (não há flag `--versao-esperada`). Não coberto neste ticket.

### [RECURSO]: Refazer ETAPA_02 com o mecanismo real (bootstrap, verify, simulação de deriva)
- **Ordem de Execução:** após o Green do Ticket 2.
- **Ação Executada:**
  1. `python ecossistema.py dependencia bootstrap` → exit 0 (log `aidd-logs-bootstrap3.txt`).
  2. `python ecossistema.py dependencia verify` → exit 0, "[SUCESSO] … 66 dependências" (log `aidd-logs-verify4.txt`).
  3. Simulação de deriva no manifesto real (backup em `aidd-tmp\manifesto.bak`): `versao_esperada` = `4.3.1` e `sha256` = hash antigo `3895765e…` → `verify` exit 1 com a mensagem "divergente por nova versao do upstream … versao esperada 4.3.1 obtida 4.5.2 … atualize 'sha256' e 'versao_esperada'" (log `aidd-logs-verify-deriva.txt`).
  4. Restauração do manifesto, confirmada por `cmp` (idêntico ao backup), e `verify` final → exit 0 (log `aidd-logs-verify5.txt`).
- **Entrega / Artefato Gerado:** ETAPA_02 verde de ponta a ponta; mensagem nova provada no `verify` real, não só em teste unitário.
  - *Caminho Exato (100% concluído):* logs em `C:\Users\trcnologia\aidd-logs-*.txt`
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. Exit 0 em `bootstrap` e no `verify` final; `pytest` exit 0 (28 passed). Exit codes capturados na mesma linha, sem pipe.
  - *Falhas / Anomalias:*
    - *Ocorrência:* minha primeira simulação de deriva estava errada: alterei só `versao_esperada` e o `verify` deu exit 0, porque o hash ainda batia e a deriva só vale quando o hash diverge. Refeita alterando também o `sha256`.
    - *Localização Exata do Erro:* N/A (erro do roteiro de teste, não do código).
  - *Ação Corretiva Cirúrgica:* simulação refeita; manifesto restaurado e comprovado idêntico.
  - *Pendência:* os gates globais (`G_SKILL_FORMATO` e outros) não foram rodados nesta etapa. As alterações em `scripts/` ficam sem commit no clone e precisam passar nos gates antes de qualquer commit.

## TICKETS
### Ticket 1: Hash do impeccable defasado — RESOLVIDO (ver v2)
- **Falha:** manifesto fixava o hash do `SKILL.md` 4.3.1; o instalador entrega o 4.5.2.
- **Artefato de Handoff:** `modulos/04-nucleo-compartilhado/contracts/dependencias_externas.json`
- **Requisito TDD (Red):** `verify` após `bootstrap` retornava exit 1 "hash SHA-256 divergente".
- **Implementação Técnica:**
  - `sha256` atualizado para `35c88304…d234c`.
- **Verificação (Green):** `bootstrap` e `verify` com exit 0.
- **Construtor Prompt (EN):**
  - Update the `sha256` of skill `impeccable` to the hash of the installed SKILL.md and run `python ecossistema.py dependencia verify`, asserting exit 0.

### Ticket 2: Hash fixo sem distinção entre deriva de versão e adulteração (Refere-se a Gate de integridade SHA-256) — RESOLVIDO
- **Falha:** qualquer atualização do upstream do `impeccable` gerava "artefato pode ter sido adulterado", sem indicar a versão esperada e a obtida.
- **Artefato de Handoff:** `scripts/gestor_dependencias.py`
- **Requisito TDD (Red):** `pytest scripts/test_gestor_dependencias.py -k Deriva` → exit 1 (6 failed).
- **Implementação Técnica:**
  - Helpers `_extrair_versao_frontmatter` e `_e_deriva_de_versao`; mensagem diferenciada em `_checar_hash_skill` e `verificar()`.
  - Campo `versao_esperada` no manifesto do `impeccable`.
- **Verificação (Green):** `pytest scripts/test_gestor_dependencias.py` → exit 0 (28 passed), e `verify` real com a mensagem de deriva provada.
- **Construtor Prompt (EN):**
  - In `scripts/test_gestor_dependencias.py` assert that `verificar()` reports "nova versao do upstream" when `versao_esperada` differs from the SKILL.md `version:` and the hash diverges, and "adulterado" otherwise.
  - Run `python -m pytest scripts/test_gestor_dependencias.py -q` and assert exit 0.

### Ticket 3: `add-skill` perde `versao_esperada` ao regravar a skill (Refere-se a consistência do manifesto) — ABERTO, NÃO EXECUTADO
- **Falha:** `adicionar_skill` recria a entrada sem `versao_esperada`; re-adicionar o `impeccable` desliga a distinção de deriva.
- **Artefato de Handoff:** `scripts/gestor_dependencias.py` (`adicionar_skill`, parser de `add-skill`)
- **Requisito TDD (Red):** teste que chama `adicionar_skill(..., versao_esperada="4.5.2")` e espera o campo gravado no manifesto; falha hoje com `TypeError`.
- **Implementação Técnica:**
  - Parâmetro opcional `versao_esperada` e flag `--versao-esperada`.
- **Verificação (Green):** `pytest scripts/test_gestor_dependencias.py` com exit 0.
- **Construtor Prompt (EN):**
  - Add a failing test for `adicionar_skill(versao_esperada=...)`, then add the optional parameter and the `--versao-esperada` CLI flag, writing it to the manifest entry when provided.
  - Run `python -m pytest scripts/test_gestor_dependencias.py -q` and assert exit 0.
