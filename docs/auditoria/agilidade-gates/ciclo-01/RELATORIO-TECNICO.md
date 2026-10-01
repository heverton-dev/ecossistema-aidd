# Relatório Técnico — agilidade-gates ciclo-01

- **Origem:** `docs/melhorias/30-09-2026_melhoria-agilidade-gates-commit.html` (nota atual 3/10).
- **Critérios:** `DOD.md` (8 itens). **Plano:** `PLANO-EVOLUCAO.md` / `.json` (8 tickets).
- **Resultado:** merge `c85eab2` na main; árvore idêntica à aprovada no gate_final (54/54 gates, `AIDD_GATES_MODO=completo`).

## Tickets

| # | Entrega | Commit | Quem fez | gate_fase |
|---|---|---|---|---|
| 1 | `scripts/medir_gates.py` (tempo real por gate) | `638c396` | agy | 769 passed |
| 2 | `gates/_escopo_commit.py` + G_TESTES_REAIS por ferramenta tocada | `93fc42d` | mimo | 779 passed |
| 3 | G_SEGREDOS só nos arquivos staged (completo = árvore inteira) | `663f926` | opencode | 780 passed |
| 4 | gate_final e `audit` forçam modo completo | `17916f5` | agy | 783 passed |
| 5 | `scripts/regenerar_derivados.py` + `ecossistema.py derivados` | `0eaaa09` | direto (mimo travou 1 h) | 790 passed |
| 6 | `--aprovar` resolve conflito só em derivado; aborta o resto | `c2cc3d2` | opencode | 810 passed |
| 7 | `scripts/fila_ciclos.py` (trava, órfã, aviso) + regra no AGENTS.md | `1b60aa9` | direto | 817 passed |
| 8 | `.githooks/pre-push` + registro verde por árvore | `5cbb5f4` | direto | 822 passed |

## Consertos que o ciclo exigiu

| Commit | O quê | Por quê |
|---|---|---|
| `56c52a2` | main verde: conftest isola módulos homônimos das skills, cmd `tdd`, `sys.exit` nos 3 gates novos, AGENTS.md, `.env.example`, timeouts do Checkov, PyJWT 2.15.1 (CVE-2026-101918) | o merge `139b672` entrou com 26 testes e 5 gates vermelhos |
| `c644183` | `preparar_worktree` em toda fase | gate_fase reprovava em worktree nova (`test_components_verify_exit_0`) |
| `d525b8e` | só `worker_done`/`escalation` encerram a fase | heartbeat reentregue virou "failed — alive" |
| `3e7db44` | chave AWS fictícia montada em runtime | gate_final achou o literal do ticket 3 |
| `9c45ba0` | linhas das chaves de teste no baseline | ticket 3 deslocou `gates/test_g_segredos.py` |

## Medições
- G_SEGREDOS completo: 903 s (antes do ciclo) · 520 s (gate_final).
- Commit com bateria inteira: 20–25 min · commit em modo rápido (tickets 5–8, fixes finais): 103–174 s.

## Riscos e limites conhecidos
- Commit de fase do orquestrador usa `--no-verify`: o que só o modo completo pega (literal de segredo, baseline deslocado) aparece no gate_final, como aconteceu duas vezes.
- `derivados regenerar` sem `--so` roda `status --testes --write` (pytest de todas as ferramentas): é lento.
- O shell em segundo plano do Claude Code é encerrado sob pouca memória; rode o gate_final numa aba do Orca.
