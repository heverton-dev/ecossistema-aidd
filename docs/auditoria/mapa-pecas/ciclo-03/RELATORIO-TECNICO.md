# Relatório Técnico (Ciclo 03 - mapa-pecas)

## 1. Contexto e Motivação
O Ciclo 03 do subsistema `mapa-pecas` foi executado para sanear os 5 achados remanescentes de `ACHADOS.json`, assegurando que o catálogo de peças e os mapas visuais representem com precisão absoluta as decisões de arquitetura e titularidade do monorepo AIDD.

## 2. Mudanças Implementadas
1. **`scripts/catalogo_pecas.py`:**
   - Adicionada tabela canônica `DONAS_TAREFAS` com a titularidade das 10 tarefas mapeadas.
   - Adicionada tabela canônica `DONAS_VERBOS` mapeando os 20 verbos expostos em CLI para suas ferramentas primárias.
   - Adicionado campo `dona_canonica` em `coletar_moldes_entrega()`.
   - Implementada função `_eh_copia_governada()` para desconsiderar réplicas intencionais de arquitetura sob baseline de drift.
   - Atualizada a função `achar_repeticoes()` para expor apenas divergências reais não governadas.
2. **`scripts/achados_ciclo.py`:**
   - Adicionado filtro de moldes governados baseando-se em `DONAS_MOLDES`.
3. **`docs/auditoria/mapa-pecas/ciclo-03/`:**
   - Scaffold e preenchimento de todos os artefatos do pipeline 4F (`DOD.md`, `LAUDO-15D-INICIAL.md`, `PLANO-EVOLUCAO.md`, `PLANO-EVOLUCAO.json`, `RELATORIO-CONSTRUTOR.md`, `LAUDO-15D-REVISADO.md`, manifestos de entrega).

## 3. Verificação Factual
- Execução de `python scripts/catalogo_pecas.py`: saída `[OK] Catálogo gravado`.
- Execução de `python scripts/achados_ciclo.py --saida docs/auditoria/mapa-pecas/ciclo-03/ACHADOS.json`: `totais.aberto == 0`.
- Execução de `python gates/G_mapa_pecas.py`: exit code 0.
- Execução de `pytest gates/test_g_mapa_pecas.py`: 7 passed, exit code 0.
