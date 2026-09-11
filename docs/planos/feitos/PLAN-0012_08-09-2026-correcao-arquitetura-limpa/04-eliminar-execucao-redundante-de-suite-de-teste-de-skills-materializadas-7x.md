# Item 4 — Eliminar execucao redundante de suite de teste de skills materializadas 7x

> **Escopo:** Entra: parar de rodar a mesma suíte de teste de skill 7 vezes (uma por cópia de harness) quando as 7 cópias já são garantidamente idênticas por outro mecanismo. Não entra: remover as 7 cópias físicas em si (isso é o materializador, fora de escopo — ver item 3); não entra mudar o mecanismo de sync/drift já existente.

> **Status:** ✅ Concluído (achado não reproduzido — investigação real em 2026-09-08, ver "Investigação real" abaixo)

---

## Contexto já investigado

- Achado via `code-review-graph` (`get_surprising_connections`) em 2026-09-08: `.agents/skills/planos-auditoria-runner/tests/test_gerenciador_planos.py` (e as cópias idênticas em `.claude/`, `.cursor/`, `.gemini/`, `.mimocode/`, `.opencode/`, `skills/`) chamam de volta o mesmo `scripts/gerenciador_planos.py` — 2.819 conexões desse tipo encontradas no total, a maioria repetição do mesmo padrão para skills diferentes.
- Como as 7 cópias de cada skill já são garantidas idênticas por hash (via `python ecossistema.py components verify`, gate `G_HARNESS_COMPAT`), rodar a suíte de teste 7 vezes não aumenta a cobertura real — testa a mesma lógica repetidamente.
- Precisa de investigação antes de implementar (não assumida aqui): identificar exatamente onde/como a suíte completa de testes é hoje disparada (`python ecossistema.py audit`? `G_TESTES_REAIS.py`? outro comando?) para saber se ela já varre as 7 cópias ou só uma — a solução pode ser tão simples quanto configurar a coleta de teste (`pytest.ini`/`testpaths`) para ignorar as 6 cópias redundantes e rodar só a canônica.

## Investigação real (2026-09-08) — achado não reproduzido

Antes de implementar qualquer correção, foi feita a investigação exigida pela Definição de Pronto original. Resultado: **a execução redundante descrita não acontece hoje** — nem 7x, nem 1x, nem de nenhuma forma automática.

O que foi checado de verdade (comandos reais, não leitura de código):

1. **Nenhum mecanismo automatizado roda testes de skills.** `gates/G_TESTES_REAIS.py`, `ecossistema.py`, `.pre-commit-config.yaml`, `.githooks/pre-commit` e `.github/workflows/audit.yml` só rodam pytest dentro de `tools/<ferramenta>` (5 ferramentas). Nenhum toca `.agents/skills`, `.claude/skills`, `.cursor/skills`, `.gemini/*`, `.mimocode/skills`, `.opencode/skills`, `skills/` ou `componentes/compartilhado/skills`. Não existe script no repo que rode a suíte de teste de uma skill materializada.
2. **Tentativa real de reproduzir a duplicação:** rodar `pytest` apontando ao mesmo tempo para as 9 cópias físicas de `planos-auditoria-runner/tests` (não 7 — contagem real: `.agents`, `.claude`, `.cursor`, `.gemini/skills`, `.gemini/extensions/planos-auditoria-runner/skills/planos-auditoria-runner`, `.mimocode`, `.opencode`, `skills/`, `componentes/compartilhado`). No modo padrão do pytest isso **falha com erro de colisão de import** (8 erros, só 1 cópia é coletada) — não duplica silenciosamente. Só duplica de fato (27 = 9×3 testes) se alguém passar `--import-mode=importlib` explicitamente, o que nada no repo faz.
3. **Proteção adicional já existente:** as pastas de harness com ponto na frente (`.agents`, `.claude`, `.cursor`, `.gemini`, `.mimocode`, `.opencode`) são ignoradas por padrão pela varredura de diretórios do pytest (`norecursedirs` inclui `.*`). Um `pytest` genérico rodado na raiz nunca entra nelas sozinho.
4. **Inventário real de skills com teste de verdade** (de 31 skills na fonte canônica `componentes/compartilhado/skills/`): apenas 2 têm suíte pytest real — `orca-plan-orchestrator` (102 testes, ~10s, 6 falhas pré-existentes sem relação com este item) e `planos-auditoria-runner` (3 testes, 0.09s, todos passando). `turnstile-spin` tem uma pasta `tests/` mas só contém um `validation.md`, sem teste pytest.

**Conclusão:** o achado original veio do `code-review-graph` (`get_surprising_connections`), que aponta uma conexão estrutural (arquivo de teste → script) repetida uma vez por cópia física no grafo estático — isso é real (as cópias existem e são idênticas, cf. item 3), mas não corresponde a uma execução redundante que acontece ou pode acontecer por acidente hoje. Não há "antes" para medir nem redução de tempo/execuções a demonstrar, porque não há execução automática a eliminar.

**Decisão (aprovada pelo usuário em 2026-09-08):** fechar o item sem criar mecanismo novo de execução automática de testes de skills — isso seria escopo novo não solicitado, e o usuário considerou que testar skills automaticamente não é necessário neste momento. Nenhum código foi alterado por este item.

## Definição de Pronto (original, mantida para histórico — não se aplica após a investigação acima)

1. Investigação real (não suposição) de onde a redundância de fato acontece hoje: rodar a suíte completa e medir/contar quantas vezes cada teste de skill executa.
2. Mecanismo ajustado para rodar a suíte de cada skill com teste uma vez só (a partir da cópia canônica), preservando a garantia de que as 7 cópias continuam idênticas (via `G_HARNESS_COMPAT`/`G_COMPONENTE_AGNOSTICO`, que já cobrem isso).
3. Medição real de antes/depois: tempo total de execução da bateria de testes reduzido, sem perda de nenhum teste único (comparar lista de testes coletados antes/depois, não só o tempo).
4. Nenhuma skill sem teste passou a não ser testada por engano.

## Critério de saída

- Redução mensurável e reproduzida do tempo/quantidade de execuções redundantes.
- `python gates/G_TESTES_REAIS.py` (ou equivalente) continua aprovado, mesma cobertura real.
- Nenhum teste único foi perdido (lista de testes coletados comparada antes/depois).

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 4: Eliminar execucao redundante de suite de teste de skills materializadas 7x.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 4: Eliminar execucao redundante de suite de teste de skills materializadas 7x.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
