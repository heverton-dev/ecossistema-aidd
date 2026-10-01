# Definição de Pronto (Definition of Done - DoD) — agilidade-gates

> Alvo: o processo de mudança do ecossistema (gates do commit, gate_final, `--aprovar`, ciclos pesados).
> Objetivo: commit do dia a dia rápido, sem perder a segurança — a main só recebe o que passou na bateria completa.
> Origem: relatório `docs/melhorias/30-09-2026_melhoria-agilidade-gates-commit.html`.

## Critérios Obrigatórios de Aceite

1. **DoD 1: Medição real antes/depois (D12)**
   - `scripts/medir_gates.py` grava o tempo real de cada gate em JSON (`segundos`, `exit_code`, `modo`).
   - O relatório do ciclo mostra o "antes" (bateria completa) e o "depois" (commit rápido) com números medidos, nunca estimados.

2. **DoD 2: G_TESTES_REAIS testa só a ferramenta tocada no commit (D3)**
   - No commit, só roda o pytest das ferramentas de `tools/<nome>/` que estão no stage.
   - Mudança fora de uma ferramenta específica (ex.: `tools/` compartilhado, o próprio gate, `allowlist_skipped_testes.json`) roda **todas**.
   - Em modo completo (`AIDD_GATES_MODO=completo`) roda sempre todas.

3. **DoD 3: G_SEGREDOS varre só os arquivos do commit (D3)**
   - No commit, a varredura cobre só os arquivos do stage, contra o `.secrets.baseline`.
   - Em modo completo, varre todo o `git ls-files` (comportamento atual).
   - Um segredo novo plantado num arquivo do stage reprova com exit 1 no modo rápido.

4. **DoD 4: gate_final é sempre completo (D13)**
   - O `gate_final` do orquestrador roda com `AIDD_GATES_MODO=completo` de forma explícita.
   - Teste prova que morde: pedir modo rápido dentro do gate_final não reduz a bateria.

5. **DoD 5: Arquivos derivados se regeneram num só comando (D15)**
   - `python ecossistema.py derivados regenerar` refaz `handoff-melhoria.json` (hash do blob em LF), `.secrets.baseline`, `PLANO-EXECUCAO-ESTRUTURADO.json`, livro e `ACHADOS.json`.
   - Rodar duas vezes seguidas não gera diff (idempotente).

6. **DoD 6: `--aprovar` resolve sozinho conflito só em arquivo derivado (D14)**
   - Conflito **somente** em arquivos da lista de derivados: resolve, regenera, conclui o merge.
   - Conflito em qualquer outro arquivo: aborta o merge, sem deixar lixo (`git status` limpo), como hoje.

7. **DoD 7: Um ciclo pesado por vez + aviso ao terminar (D11)**
   - Segundo ciclo pesado espera na fila (trava em arquivo) em vez de rodar em paralelo; trava órfã (processo morto) é liberada.
   - Fim do ciclo (aprovado ou reprovado) dispara aviso local e grava o resultado.
   - `AGENTS.md` ganha a regra: tarefa longa roda em segundo plano, o agente volta sozinho ao terminar — nunca "me chame em 30 minutos".

8. **DoD 8: Push com código exige bateria completa verde (D13)**
   - `pre-push`: se o push leva mudança fora de `secoes/`, `docs/` e `*.md`, exige bateria completa verde para aquele commit (reaproveita resultado já gravado para o mesmo SHA).
   - Push só de `secoes/`/`docs/`/`*.md` passa sem bateria completa.

## Fora deste ciclo (registrado para o próximo)
- Cache de resultado por ferramenta no gate_final (pular testes de ferramenta idêntica à última execução verde).
