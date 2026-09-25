# Laudo 15-D Revisado — `aidd-diagnose` (Fase 4 / Retorno, ciclo-01)

> Auditoria de 2026-09-25 na branch `audit/evolucao-aidd-diagnose-ciclo-01` (`6e7a9f8`). Todo achado tem reprodução real.
> Scripts de prova: `prova_diag.py` (scratchpad da sessão) e teste-sentinela em `docs/diagnosticos/`.
> Base de comparação: `LAUDO-15D-INICIAL.md` (nota 4/10).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-diagnose`
- **Descrição Breve:** Protocolo de 5 fases para achar a causa de uma falha, agora com CLI, checagem de cobertura do grafo, fallback sem MCP, gate próprio e módulos de isolamento/observabilidade/rollback/handoff.
- **Comando de Gatilho:** `/aidd-diagnose` e `python ecossistema.py diagnose {iniciar,fase}` (novo; `iniciar --sintoma "x"` → exit 0).

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** `SKILL.md` idêntico nas 5 cópias (hash `81F7AF4E`). **Achado:** o `SKILL.md` só cita `cobertura_grafo.py` e `fallback.py`. Não cita `cli.py`, `isolamento.py`, `observabilidade.py`, `rollback.py`, `handoff.py` nem `G_aidd_diagnose.py` (grep → 0 ocorrências). O agente que segue a skill nunca é mandado usar 5 dos 7 entregáveis.
- **D2. Input e Gatilhos:** Implementado. `iniciar` exige `--sintoma` (sem ele → exit 2 do argparse); `fase --numero N` bloqueia pular fase. **Defeito reproduzido:** `obter_ultima_sessao()` ordena pelo nome da pasta (`<data>_<slug>`), não pela data de criação. Duas sessões no mesmo dia: criei "zebra antiga" e depois "abelha nova" → devolveu `20260925_zebra-antiga`. O `fase` avança a sessão errada.
- **D3. Raio de Impacto e Isolamento:** `isolamento.py` existe (`DiagnoseWorktreeManager`, `validar_caminho_escrita`) e tem testes, mas não tem entrypoint (`--help` não imprime nada) e ninguém o importa fora dos testes. **Parcial: mecanismo existe, não está ligado.**
- **D4. Componentes e Fractalidade:** MCP `code-review-graph` + `cobertura_grafo.py` + `fallback.py` (ambos com CLI funcional: `verificar/medir`, `analisar`). Comando `diagnose` registrado em `ecossistema.py`.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** Sem mudança: método científico, uma hipótese ativa por vez, fim num teste de regressão permanente.
  - **[Estágio 1 — Reprodução] D6. O que o Estágio Faz:** Isola a falha num comando mínimo. **D7. O que o Estágio Recebe:** sintoma (`iniciar --sintoma`). **D8. O que o Estágio Processa:** LLM; a CLI só grava `sessao.json`. **D9. O que o Estágio Entrega:** `docs/diagnosticos/<data>_<slug>/sessao.json`.
  - **[Estágio 2 — Raio de impacto] D6. O que o Estágio Faz:** Checa cobertura do grafo e consulta impacto. **D7. O que o Estágio Recebe:** arquivos suspeitos. **D8. O que o Estágio Processa:** `cobertura_grafo.py verificar` (corrige o falso "0 impacto" do laudo inicial) e `fallback.py analisar` quando o MCP cai. **D9. O que o Estágio Entrega:** `fase2.modo` = `grafo` ou `fallback` no `sessao.json`.
  - **[Estágio 3 — Hipótese] D6/D7/D8/D9:** LLM formula a hipótese; entrega o bloco `HIPOTESES ATIVAS:` no relatório, conferido pelo gate.
  - **[Estágio 4 — Prova] D6/D7/D8/D9:** Instrumentação temporária. `isolamento.py` deveria confinar isso numa worktree, mas não é chamado (ver D3).
  - **[Estágio 5 — Correção] D6/D7/D8/D9:** Fix + teste de regressão; o gate exige `falhou_antes`/`passou_depois`.
- **D10. Orquestração e Topologia:** Linear 1→5 com `sessao.json` persistido entre fases (antes: só a conversa). `fase` marca a fase como concluída ao **entrar** nela; nada confere que o trabalho da fase anterior foi feito.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** Implementado: `fallback.py` com retry + backoff e análise estática por AST sem LLM. Coberto por `tests/test_fallback_diagnose.py`.
- **D12. Observabilidade e Frugalidade:** `observabilidade.py` existe com testes, sem entrypoint e sem chamador. **Parcial: não está ligado.**

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** `gates/G_aidd_diagnose.py` existe, registrado em `AGENTS.md` e no catálogo (48→49). **Limitação reproduzida:** o gate confia em campos auto-declarados. Um `relatorio_causa_raiz.json` 100% inventado (`"comando_reproducao": "echo inventado"`, `falhou_antes: true`, `passou_depois: true`) → **exit 0**. Ele confere o formato do relatório, não executa a reprodução.
- **D14. Critério de Rejeição (Rollback):** `rollback.py` (`executar_com_rollback`) existe com testes, sem entrypoint e sem chamador. **Parcial: não está ligado.**
- **D15. Output Consolidado e Handoff:** `handoff.py {emitir,transicionar}` com CLI funcional. Não é citado no `SKILL.md`.

## Defeitos que bloqueiam o merge

1. **GRAVE: um teste apaga dados reais do repositório.** `.agents/skills/aidd-diagnose/scripts/test_cli.py::test_fase_rejeita_sem_sessao_anterior` roda `shutil.rmtree(ROOT/"docs"/"diagnosticos")` no repo real. Prova: criei `docs/diagnosticos/20990101_sentinela/dado-real.txt`, rodei só esse teste (exit 0) → o arquivo sumiu, e sumiu também o `sessao.json` versionado. O teste existe em 4 cópias (uma por harness).
2. **O mesmo `test_cli.py` escreve no repo real e depende da ordem dos testes.** Os outros testes criam sessões em `docs/diagnosticos/` de verdade (é a origem do `20260924_test-sequence/sessao.json` que entrou na branch). Rodando a suíte com essa sobra no disco: `test_iniciar_com_sintoma_cria_sessao_json` **falha** (`'Test sequence' == 'Teste de diagnose'`): 1 falha, 55 aprovados.
3. **`obter_ultima_sessao()` escolhe a sessão errada** (D2 acima).
4. **5 entregáveis sem ligação com a skill** (D1/D3/D12/D14): isolamento, observabilidade e rollback só rodam nos próprios testes.

## Arquivos fora do escopo da ferramenta
- Manter: `AGENTS.md`, `ecossistema.py`, 3 arquivos em `docs/auditoria/historico_auditorias/` (registro do gate).
- Commit separado: `tests/test_properties.py` (ajuste de hypothesis sem relação com o diagnose).
- Remover: `docs/diagnosticos/20260924_test-sequence/sessao.json` (sobra de teste, ver defeito 2), `projetos/app-loja/README-USUARIO.md`, `projetos/lovable-app/README-USUARIO.md`.

---

## 3. Matriz de Avaliação da Execução
- [ ] A ferramenta isolou seu raio de impacto corretamente? — **Não.** O isolamento existe em código mas não é chamado, e os testes da própria CLI escrevem e apagam no repo real.
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas? — **Sim, em boa parte.** Cobertura do grafo e fallback agora são motores determinísticos com teste.
- [ ] O output final passou em todos os Quality Gates e emitiu o Handoff? — **Não.** A suíte da ferramenta tem 1 falha dependente de ordem; o gate aprova relatório inventado; o handoff não é citado na skill.

**Nota revisada: 6/10** (era 4/10). O mecanismo foi construído; falta ligá-lo à skill e tirar os testes do repo real. **Veredito: NÃO mergear antes de corrigir os defeitos 1 a 3.**

---

## 4. Correções aplicadas (2026-09-25, mesma branch)

| Achado | Correção | Prova |
|---|---|---|
| Defeito 1: teste com `rmtree` no repo real | `scripts/test_cli.py` apagado das 7 cópias. A regra que ele cobria (fase sem sessão → exit 1) foi para `tests/test_diagnose_cli.py`, rodando em `tmp_path` | `test_repositorio_real_intocado`: reprova com a CLI antiga (exit 1), passa com a nova |
| Defeito 2: testes gravando no repo real | `cli.py` aceita `AIDD_DIAGNOSE_RAIZ`; todos os testes da CLI usam `tmp_path`. `scripts/test_observabilidade.py` foi para `tests/test_diagnose_observabilidade.py`, com carga isolada. O caso `test_observabilidade_sem_relatorio_retorna_1` foi apagado: era tautológico (`sys.exit(1)` fixo) e gravava arquivo e pasta dentro da skill | Bateria de 64 testes → exit 0, sem nenhum arquivo novo em `docs/diagnosticos/` nem na pasta da skill |
| Defeito 3: sessão errada | `localizar_ultima_sessao()` em `cli.py` ordena por `data_inicio` do `sessao.json` (mtime como desempate); `handoff.py` reusa a mesma função | Teste zebra/abelha: reprova na CLI antiga, passa na nova; `prova_diag.py` → `abelha-nova` |
| Defeito 4: módulos soltos | `cli.py` virou a entrada única: `registrar`/`relatorio` (observabilidade), `worktree` (isolamento, nova `criar_worktree_fase4`), `limpar` (rollback). `SKILL.md` ganhou a tabela da CLI e os comandos em cada fase | Repo git temporário: `worktree` criou a worktree e a branch `diagnose/*`; `limpar` removeu as duas (exit 0) |
| Gate aceitava relatório inventado | `G_aidd_diagnose` exige que o arquivo do teste de regressão exista e roda o pytest nele. `falhou_antes` continua declarado, e isso está escrito na skill | Relatório inventado → exit 1; 2 testes novos que mordem (teste inexistente, teste vermelho) |
| Fora de escopo | Removidos `docs/diagnosticos/20260924_test-sequence/sessao.json` e os 2 `projetos/*/README-USUARIO.md` | `git rm` |

`tests/test_properties.py` continua no commit do Ticket 1: separar exigiria reescrever o histórico da branch.

**Nota pós-correção: 8/10.** Falta só a prova de `falhou_antes`, que continua auto-declarado.
