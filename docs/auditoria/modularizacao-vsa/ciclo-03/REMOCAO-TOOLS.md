# Remoção de tools/ — ciclo-03, Ticket 5 (Lei #7)

> Lista do que sai e para onde foi o conteúdo, medida em 06/10/2026 antes do `git rm`.
> Rede de segurança: tag `pre-vsa-ciclo-03` (232cac4) e todo o histórico do git.

| Ferramenta | Arquivos que saem de tools/ | Pasta canônica (fica) | Idênticos | Divergentes decididos (RECONCILIACAO.md) | Só em tools/ |
|---|---|---|---|---|---|
| aidd-forge | 182 | `modulos/01-governanca-e-qualidade/core/aidd-forge` | 177 | 5 | 0 |
| aidd-planner | 26 | `modulos/01-governanca-e-qualidade/core/aidd-planner` | 16 | 10 | 0 |
| aidd-pure | 200 | `modulos/02-triade-motores/fluxo-01-pure/core/aidd-pure` | 182 | 18 | 0 |
| aidd-open | 60 | `modulos/02-triade-motores/fluxo-02-open/core/aidd-open` | 45 | 15 | 0 |
| aidd-freedom | 27 | `modulos/02-triade-motores/fluxo-03-freedom/core/aidd-freedom` | 26 | 1 | 0 |
| aidd-master | 306 | `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master` | 289 | 17 | 0 |
| aidd-enterprise | 963 | `modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise` | 950 | 13 | 0 |
| aidd-ops | 96 | `modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops` | 68 | 28 | 0 |

Total: 1860 arquivos versionados saem de `tools/`; fica só `tools/LEIA-ME.md` (sai no próximo ciclo).

Não foram para `modulos/` de propósito (cache e gerados, nunca versionados ou ignorados): `__pycache__/`, `.pytest_cache/`, `node_modules/`, `*.pyc`, `*.db-wal`, `*.db-shm`.

## Prova de zero perda

- `python scripts/reconciliar_copias_vsa.py --exigir-zero` antes do `git rm`: exit 0 (0 divergente sem decisão, 0 só em tools/, 107 divergências decididas pelo lado de modulos/).
- `python scripts/inventario_capacidades.py comparar docs/auditoria/fronteiras-ferramentas/ciclo-01/INVENTARIO-ANTES.json --aceitos docs/auditoria/modularizacao-vsa/ciclo-03/ORFAOS-ACEITOS.json` depois do `git rm`: exit 0.
  - Nenhuma função, classe ou teste ficou órfão no ciclo-03 (comparação item a item contra a tag `pre-vsa-ciclo-03`).
  - 373 órfãos já existiam na tag (dívida da foto de 04/10, anterior ao ciclo); 206 são linhas de caminho do layout `tools/` reescritas nos Tickets 3 e 4.
  - Sem `--aceitos` o comando sai com 1 (579 órfãos), igual ao estado da tag (373): por isso a lista com motivo.
- Bateria completa depois do `git rm`: total de testes passando >= 3463 (linha de base do Ticket 1).
