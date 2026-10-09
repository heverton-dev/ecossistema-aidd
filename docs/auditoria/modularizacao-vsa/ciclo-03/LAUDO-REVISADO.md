# Laudo revisado — modularizacao-vsa ciclo-03

> Ticket 22 (Bloco 8), 09/10/2026. Cada achado do `DIAGNOSTICO.md` (06/10/2026) com o comando de prova rodado de novo e o exit code real.
> Base medida: branch `aidd/vsa-c03-bloco-8` (T21 `887a1b66`, T20 `024c9cdb`, DoD 1 `6d6cd441` e `3ffad397`) sobre a `main` `1f7a6c24`, que já traz o Ticket 23 do Bloco 9 (`d9f81a43`). Comandos rodados na raiz da worktree, salvo indicação, com `TEMP`, `TMP` e `TMPDIR` fora de `AppData\Local\Temp`.
> Decisões do usuário que guiaram o ciclo (ver `DIAGNOSTICO.md`): A — `modulos/` é a cópia canônica; B — gate só sai com 0 ou 1; C — cada gate na fatia dona.

## Resumo

| Achado (06/10) | Estado em 09/10 | Tickets |
| :-- | :-- | :-- |
| 1. Migração VSA foi cópia | Resolvido; o comparador de capacidades, vermelho desde o T6, voltou a exit 0 no Bloco 8 | T1–T5, DoD 1 (Bloco 8) |
| 2. Gates duplicados e fora do commit | Resolvido | T7–T9 |
| 3. Gates de fronteira cegos | Resolvido; o esqueleto repetido entre enterprise e master saiu no T23 | T10–T12, T20, T23 |
| 4. Stubs e scripts órfãos | Resolvido | T13, T14 |
| 5. Exit codes | Resolvido (decisão B) | T15 |
| 6. Micro-gates | Resolvido | T16 |
| 7. Contexto | Resolvido | T17–T19 |
| 8. Lixo versionado | Resolvido | T6, T12 |
| 9. Fronteiras-ferramentas ciclo-01 (parciais) | Resolvido | T16, T20, T21 |
| 10. Bateria | Resolvido | T9, correção pós-audit de 08/10 |

## Achados

### 1. Migração VSA foi cópia, não mudança
- Antes: `tools/` com ~1.860 arquivos versionados e a segunda cópia em `modulos/`; 1.450 pares duplicados; 83 arquivos `.py` fora das duas pastas apontando para `tools/`.
- Provas:
  - `git ls-files tools` → exit 0; só `tools/LEIA-ME.md`.
  - `python scripts/reconciliar_copias_vsa.py --exigir-zero` → exit 0; 0 divergentes, 0 só em `tools/`, 1.124 só em `modulos/`.
  - `python -m pytest -q -p no:cacheprovider tests/test_tools_extinto.py tests/test_sem_referencia_tools.py tests/test_reconciliar_copias_vsa.py` → exit 0 (12 passed).
  - `python scripts/inventario_capacidades.py comparar docs/auditoria/fronteiras-ferramentas/ciclo-01/INVENTARIO-ANTES.json --aceitos docs/auditoria/modularizacao-vsa/ciclo-03/ORFAOS-ACEITOS.json` → exit 0; zero órfão fora da lista: 724 itens aceitos, cada um com motivo e commit, e 14.664 itens de 2 pastas apagadas no T6 (`materiais-extras/` do `aidd-enterprise`, arquivada fora do repositório com o OK do usuário, e o cache de execução `output-clinica/.aidd/cache`). Antes do commit `6d6cd441` saía com 1 (14.807 órfãos): as 2 pastas e 143 linhas reescritas no T6 (2), no T8 (43) e no T10 (98). Depois do rebase sobre o T23 saiu com 1 de novo: 2 órfãos, a linha do `scripts/aidd.py` que o T23 reescreveu ao renomear `application` para `application_enterprise`, aceitos no commit `3ffad397`. Nenhuma função, classe ou teste órfão fora de `materiais-extras/`.
- Estado: resolvido pelos Tickets 1 a 5. O T5 provou o comparador com exit 0 depois do `git rm` de `tools/`; ninguém o rodou de novo depois do T6, e ele não roda em nenhuma bateria. No Bloco 8, com o OK do usuário, o commit `6d6cd441` fez o comparador aceitar pasta apagada inteira (com motivo e só se ela não existir em layout nenhum) e registrou as 143 linhas com o commit de cada uma. O `3ffad397` registrou as 2 linhas reescritas pelo T23 e tirou da docstring nova uma citação à pasta `tools/` que reprovava o `test_sem_referencia_tools.py` (erro do `6d6cd441`). Ver pendência 1.

### 2. Gates duplicados e nunca executados nas fatias
- Antes: 69 gates de `modulos/*/gates` idênticos aos de `gates/`; `.pre-commit-config.yaml` sem nenhuma referência a `modulos/`.
- Provas:
  - `python modulos/04-nucleo-compartilhado/gates/G_COPIA_UNICA_VSA.py` → exit 0; modo bloqueio, 0 violações.
  - `python scripts/mapa_gates.py verificar` → exit 0; 0 divergências entre o `.pre-commit-config.yaml` e o `MAPA-GATES.json`.
  - `python -m pytest -q -p no:cacheprovider tests/test_mapa_gates.py tests/test_gates_raiz_extinta.py` → exit 0 (14 passed).
- Estado: resolvido. 72 portões no `MAPA-GATES.json`, cada um na pasta `gates/` da fatia dona; a pasta `gates/` da raiz deixou de existir (Tickets 7 e 8).

### 3. Gates de fronteira cegos (salvaguarda 4, DoD 4)
- Antes: `G_AST_BOUNDED_CONTEXT` e `G_modularizacao_vsa` só procuravam `import tools.`/`modulos.`; nenhum `interface.py`; o `G_MODULO_FRONTEIRA` do padrão não existia; colisão real do pacote `core` entre open e pure.
- Provas:
  - `python modulos/04-nucleo-compartilhado/gates/G_MODULO_FRONTEIRA.py` → exit 0; modo bloqueio por padrão (Ticket 20), 0 acoplamento novo, 49 perdoados com data e motivo, 0 entrada morta.
  - `python -m pytest -q -p no:cacheprovider modulos/04-nucleo-compartilhado/gates/test_g_modulo_fronteira.py tests/test_interfaces_fatias.py` → exit 0 (30 passed); `interface.py` com `__all__` nas 7 fatias e pacotes `core` renomeados (Ticket 10).
  - `python -m pytest -q -p no:cacheprovider tests/test_almoxarifado.py`, de dentro de `modulos/01-governanca-e-qualidade/core/aidd-forge` → exit 0 (7 passed); `obter_peca` recusa destino em `modulos/` (Ticket 12).
  - `python -m pytest -q -p no:cacheprovider tests/test_esqueleto_unico_enterprise_master.py` → exit 0 (4 passed); o esqueleto de app só no `aidd-master` e o `allowlist_pacotes_repetidos.json` só com o `core` (Ticket 23).
- Estado: resolvido. O Ticket 23 (Bloco 9, `d9f81a43`) deixou o app de demonstração só no `aidd-master`: saíram 40 arquivos e 2 testes do `aidd-enterprise`, o pacote `application` dele virou `application_enterprise` e o `allowlist_pacotes_repetidos.json` ficou só com o `core` (núcleo vendorizado, exceção do usuário).

### 4. Stubs e scripts órfãos (ciclo-01)
- Antes: `modularizacao-vsa inspect|verify|status` com texto fixo e exit 0; seis scripts `*_vsa.py` sem consumidor.
- Provas:
  - `python ecossistema.py modularizacao-vsa verify` → exit 0; mede as fatias de verdade desde o Ticket 13.
  - `python -m pytest -q -p no:cacheprovider tests/test_vsa_cli_real.py tests/test_sem_orfaos_vsa.py` → exit 0 (5 passed).
- Estado: resolvido (Tickets 13 e 14; `ERRATA.md` no ciclo-01).

### 5. Exit codes (salvaguarda 1)
- Antes: 0 de 71 gates usavam `scripts/exit_codes.py`, e a convenção 0–5 contradizia o `G_SAIDA_BINARIA`.
- Provas:
  - `python modulos/04-nucleo-compartilhado/gates/G_SAIDA_BINARIA.py` → exit 0; os portões do `MAPA-GATES.json` saem só com 0 ou 1.
  - `python -m pytest -q -p no:cacheprovider tests/test_convencao_exit_escopo.py` → exit 0 (3 passed); a escala 0–5 vale só para scripts e CLIs.
- Estado: resolvido pela decisão B (Ticket 15).

### 6. Micro-gates (salvaguarda 3)
- Antes: os 3 comandos `pytest modulos/0N-... --maxfail=1` saíam com exit 1 já na coleta.
- Provas:
  - `python -m pytest -q -p no:cacheprovider tests/test_micro_gates_fatias_verdes.py` → exit 0 (7 passed).
  - `git commit` do Ticket 20 (13 arquivos, só a fatia forge tocada; commit original, antes do rebase sobre o T23) → exit 0 em 168 s; pre-commit com 65 aprovados e o micro-gate rodando só a suíte do forge (a mesma suíte, rodada à mão da pasta do forge: 316 passed, 1 skipped).
- Estado: resolvido (Ticket 16). Tempos medidos no `DOD.md`, item 6.

### 7. Contexto (salvaguardas 6 e 7, padrão §4)
- Antes: `AGENTS.md` local em 1 de 7 fatias; `components sync` não lia as skills das fatias; 9 subgrafos com nomes fora do padrão e ~15 grafos órfãos.
- Provas:
  - `python -m pytest -q -p no:cacheprovider tests/test_agents_por_fatia.py tests/test_skills_fatias_sync.py tests/test_subgrafos_nomes_padrao.py` → exit 0 (58 passed).
  - `python ecossistema.py components verify` → exit 0; 78 componentes sincronizados com a fonte canônica.
- Estado: resolvido (Tickets 17 a 19; codebase-memory de 39 para 8 projetos, `REMOCAO-SUBGRAFOS.md`).

### 8. Lixo versionado e fronteira do almoxarifado
- Antes: `sandbox-forge-teste`, `secoes/` e `_destino_teste_almoxarifado` dentro de `modulos/`; `materiais-extras` copiada para `modulos/`.
- Provas:
  - `python -m pytest -q -p no:cacheprovider tests/test_modulos_sem_lixo.py` → exit 0 (3 passed).
- Estado: resolvido (Ticket 6; a guarda do almoxarifado é o Ticket 12, achado 3).

### 9. Fronteiras-ferramentas ciclo-01 (itens parciais)
- Antes: T9/T10 (testes do forge só rodavam de dentro da pasta), T19 (só olhava `tools/`), T20 (100 violações perdoadas) e T21 (comparação E2E anterior à VSA) parciais.
- Provas:
  - `python modulos/04-nucleo-compartilhado/gates/G_FRONTEIRA_FERRAMENTAS.py --modo bloqueio` → exit 0; lê `git ls-files modulos`, 32 violações conhecidas, todas perdoadas com data e motivo (eram 100 em 06/10).
  - `python -m pytest -q -p no:cacheprovider tests/test_fiscais_vsa_bloqueio.py` → exit 0 (58 passed); nenhuma entrada morta, motivo revisado em cada uma (Ticket 20).
  - `python scripts/e2e_foto.py comparar --base ciclo-01 --novo ultimo` → exit 0; foto `ciclo-26`, tirada depois da VSA, sem métrica pior que a base (Ticket 21, `COMPARACAO-E2E.md`).
  - `python -m pytest -q -p no:cacheprovider tests/test_foto_e2e_pos_vsa.py tests/test_e2e_foto.py` → exit 0 (16 passed).
- Estado: resolvido. T9/T10 virou o desenho: cada suíte roda da pasta da ferramenta com `--rootdir=.` (Ticket 16).

### 10. Bateria
- Antes: `python ecossistema.py audit` com exit 1 (62 aprovados, 1 reprovado: `G_SEGREDOS` regravava o `.secrets.baseline`), 1.360 s.
- Provas:
  - `python ecossistema.py audit` sobre a `main` `ee9e15f1` (08/10, 17:48–18:20) → exit 0; 66 aprovados, 0 reprovados; `G_TESTES_REAIS` com 3.689 testes passando, 0 falhas.
- Estado: resolvido (`G_SEGREDOS` idempotente no Ticket 9). O `gate_final` do Bloco 8 fica registrado no `PROMPT-CONTINUACAO.md`.

## Critérios de aceite (DOD.md)

| DoD | Estado | Prova |
| :-- | :-- | :-- |
| 1. Uma cópia só | Cumprido | Achado 1: `tools/` extinto, reconciliação e comparador de capacidades com exit 0 (o comparador voltou a 0 nos commits `6d6cd441` e `3ffad397`) |
| 2. Sem lixo e sem casca | Cumprido | Achado 8 |
| 3. Gates no dono | Cumprido | Achado 2 |
| 4. Fronteira que morde | Cumprido | Achado 3; o esqueleto enterprise × master saiu no T23 (`d9f81a43`) |
| 5. Sem stubs | Cumprido | Achados 4 e 5 |
| 6. Micro-gates verdes | Cumprido | Achado 6 |
| 7. Contexto enxuto | Cumprido | Achado 7 |
| 8. Fechamento honesto | Cumprido | Fiscais em bloqueio e allowlists revisadas (T20), foto E2E (T21), este laudo e o padrão de arquitetura marcado como implementado (T22) |

## Desvios do plano

- Ticket 21: a base `ciclo-01` não precisou ser restaurada do histórico; a pasta das fotos foi movida para `Desktop/01_projetos_apps/testes-e2e-ecossistema-aidd` em 05/10 e o `e2e_foto.py` passou a procurá-la lá.
- Ticket 22: o nome do arquivo segue o plano (`LAUDO-REVISADO.md`); o catálogo de peças só reconhece `LAUDO-15D-REVISADO.md`, por isso o achado `CAT-ciclo-modularizacao-vsa-ciclo-03` continua aberto.
- DoD 1: o `ORFAOS-ACEITOS.json` dizia que a lista só podia diminuir; no Bloco 8 ela cresceu de 579 para 724 entradas (722 no Bloco 8 e 2 do T23) e ganhou 2 pastas removidas, com o OK do usuário (09/10). A descrição do arquivo agora exige motivo e commit citado.
- Padrão de arquitetura: os desvios de implementação (sem proxies em `tools/`, gates só 0/1, cascas `quarteto-studios/` e `04/cli` removidas) estão na seção 8 de `docs/padroes/ARQUITETURA-MODULARIZACAO-VSA-ECOSSISTEMA.md`.

## Pendências e achados novos

1. **Comparador de capacidades vermelho do T6 ao Bloco 8 (DoD 1): resolvido.** Os 14.807 órfãos eram o arquivamento aprovado de `materiais-extras/`, o cache apagado e linhas reescritas pelos reapontamentos; nenhuma função, classe ou teste se perdeu fora de `materiais-extras/`. Com o OK do usuário (09/10), os commits `6d6cd441` e `3ffad397` (este depois do rebase sobre o T23) levaram o comparador a exit 0. Ele continua fora das baterias: pôr numa bateria obrigaria a registrar cada linha reescrita de arquivo antigo; fica como prova de fechamento de ciclo.
2. **Portões de ferramenta sem chamador** (achado do T20): `G_FACTORY_ANALYSIS`, `G_FACTORY_COMPOSE`, `G_FACTORY_ENV`, `G_FACTORY_INIT_DB` e `G_FACTORY_INTEGRATION` no `aidd-open` e `G_INTEGRACAO_CROSS_SCRIPT` no `aidd-pure`. Ligar ou apagar é decisão pendente.
3. **Hook `g-testes-reais` com `files: ^tools/`** (achado do Bloco 3): no commit quase nunca dispara; as suítes do commit rodam pelo `g-micro-gates-diff`, e o `audit` roda o `G_TESTES_REAIS` inteiro.
4. **Suíte do forge rodada da raiz de uma worktree** (achado do T20): importa o `aidd_forge` editável da `main`; de dentro da pasta da ferramenta, como rodam o micro-gate e o `G_TESTES_REAIS`, está correta.
5. **Esqueleto enterprise × master: resolvido no Ticket 23** (Bloco 9, `d9f81a43`; a auditoria do Bloco 9 saiu com exit 0, 66 aprovados, em 34min31s). As 29 entradas de `aidd-enterprise/` e `aidd-master/` nas allowlists de fronteira ficaram como o T23 deixou.
