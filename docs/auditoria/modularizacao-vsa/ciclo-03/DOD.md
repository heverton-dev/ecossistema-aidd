# Definição de Pronto (DoD) — modularizacao-vsa ciclo-03

> Alvo: `modulos/`, `tools/`, gates, CLI `ecossistema.py`, contexto dos harnesses.
> Origem: `DIAGNOSTICO.md` (06/10/2026) · Plano: `PLANO-EVOLUCAO.md` · Decisões A, B e C do usuário.

## Critérios Obrigatórios de Aceite

1. **DoD 1: Uma cópia só (decisão A)** — `git ls-files tools` só com `tools/LEIA-ME.md`; `reconciliar_copias_vsa.py --exigir-zero` exit 0; `inventario_capacidades.py comparar` com zero órfão; nenhuma referência viva a `tools/aidd-`; total de testes passando ≥ linha de base do Ticket 1.
2. **DoD 2: Sem lixo e sem casca** — `modulos/` sem sandbox, `secoes/`, `materiais-extras/`, `_destino_teste*`, `*.egg-info`, `*.db-wal/shm`; nenhuma pasta só com `__init__.py`; `materiais-extras/examples` arquivado fora do repo.
3. **DoD 3: Gates no dono (decisão C)** — cada gate em um único lugar, conforme `MAPA-GATES.json`; `gates/` da raiz sem `G_*.py`; `audit` com o mesmo número de gates; `G_SEGREDOS` idempotente.
4. **DoD 4: Fronteira que morde** — `interface.py` com `__all__` nas 7 fatias; sem pacote com nome repetido entre fatias; `G_MODULO_FRONTEIRA` prova que morde (sys.path, caminho literal, `tools/`); almoxarifado recusa destino dentro de `modulos/`.
5. **DoD 5: Sem stubs (decisão B)** — `modularizacao-vsa verify` reprova fatia quebrada; nenhum `scripts/*_vsa.py` órfão; ERRATA no ciclo-01; convenção de exit codes limitada a scripts e CLIs, gates só 0/1.
6. **DoD 6: Micro-gates verdes** — todo comando por fatia de `micro_gates.py` com exit 0. Tempo medido (08/10, Ticket 16): bateria completa dos 9 comandos = 693 s (antes 753 s); suítes de um commit só no pure = 32 s (antes 147 s: pure + open + freedom); commit real numa fatia = 387 s (a61b4eb1, só no master, cuja suíte leva ~240 s; antes do T16 o mesmo commit rodaria enterprise + master + ops ≈ 498 s só de suítes); commit do T16 tocando 5 subfatias = 322 s. Mudança (08/10, correção pós-audit): `test_comando_da_fatia_sai_com_zero`, que rodava os 9 comandos dentro da bateria `tests/`, saiu porque estourou o teto de 900 s do G_TESTES_REAIS; a prova de exit 0 por fatia passa a ser o pre-commit (micro-gates das fatias tocadas) e as suítes por ferramenta no G_TESTES_REAIS. Bateria `tests/` sozinha (`python -m pytest tests -q -p no:cacheprovider`, sem AIDD_GATES_MODO, mesma máquina): 1384 s antes, 794 s depois.
7. **DoD 7: Contexto enxuto** — `AGENTS.md` (< 400 tokens) e `README.md` (< 500) em cada fatia e subfatia; skills com dono único e sync lendo as fatias; subgrafos com os nomes do padrão e sem grafos órfãos.
8. **DoD 8: Fechamento honesto** — `G_COPIA_UNICA_VSA` e `G_MODULO_FRONTEIRA` em bloqueio; allowlists só com entradas justificadas; foto E2E pós-VSA sem piora; `python ecossistema.py audit` exit 0; `LAUDO-REVISADO.md` com o comando de prova de cada item.
