# Remoção de subgrafos do codebase-memory (ciclo-03, Ticket 19)

Lista mostrada ao usuário em 08/10/2026 e apagada só depois do OK dele ("sim para as duas"). Este registro foi escrito logo após a remoção. Comando de prova: `list_projects` do codebase-memory-mcp (39 projetos antes, 8 depois).

## Órfãos: pasta raiz não existe mais (24, ~11 GB)

Caminhos relativos a `C:/Users/trcnologia/Desktop/`.

- `aidd-wt/push-main`
- `aidd-wt/vsa-c03-bloco-1`
- `aidd-wt/vsa-c03-bloco-2`
- `aidd-wt/vsa-c03-bloco-3`
- `aidd-wt/vsa-c03-bloco-4`
- `aidd-wt/vsa-c03-bloco-5`
- `aidd-wt/vsa-c03-bloco-6`
- `ecossistema-aidd/.claude/worktrees/bloco-5-ticket-20`
- `ecossistema-aidd/wt_ticket_2`
- `worktrees_auditoria-modularizacao-vsa-ciclo-01/Fase_1_Inspetor`
- `worktrees_auditoria-modularizacao-vsa-ciclo-01/Fase_2_Arquiteto`
- `worktrees_auditoria-modularizacao-vsa-ciclo-01/Fase_3_Construtor`
- `worktrees_auditoria-modularizacao-vsa-ciclo-01/Fase_4_Inspetor_Retorno`
- `worktrees_auditoria-modularizacao-vsa-ciclo-01/_gate_final`
- `worktrees_evolucao-aidd-skills-ciclo-02/_gate_final`
- `worktrees_evolucao-fronteiras-ferramentas-ciclo-01/Fase_1_Ticket_1_Gate_pr_prio_por_ticket_e_um_manifesto_por_bloco`
- `worktrees_evolucao-fronteiras-ferramentas-ciclo-01-bloco-1/Fase_4_Ticket_4_Padronizar_os_nomes_dos_construtores_pelo_nome_do_fluxo`
- `worktrees_evolucao-fronteiras-ferramentas-ciclo-01-bloco-2/Fase_9_Ticket_9_Consumo_sob_demanda___o_forge_entrega_a_pe_a`
- `worktrees_evolucao-fronteiras-ferramentas-ciclo-01-bloco-2/_gate_final`
- `worktrees_evolucao-fronteiras-ferramentas-ciclo-01-bloco-3/_gate_final`
- `wt_bloco4_open`
- `wt_impeccable_mobbin`
- `wt_test_audit`
- `cache/wt_cbm_eval (fora do Desktop)`

## Substituídos pelos nomes do padrão §7.5 (7)

- `vsa-01-governanca` → `vsa-modulo-governanca`
- `vsa-04-nucleo` → `vsa-aidd-nucleo`
- `vsa-blindagem-enterprise`, `vsa-fatiamento-master`, `vsa-operacoes-ops` → `vsa-modulo-plataforma-ops`
- `vsa-core-cli` (`scripts/`) → fica só no grafo do repositório inteiro
- `C-Users-trcnologia-Desktop-ecossistema-aidd-tools-aidd-master`: `tools/` não tem mais código versionado (só `tools/LEIA-ME.md` e restos não versionados de harness)

`vsa-triade-fluxo-pure`, `vsa-triade-fluxo-open` e `vsa-triade-fluxo-freedom` mantêm o nome: foram reindexados (sobrescritos), não apagados.

## Ficaram (8)

- `C-Users-trcnologia-Desktop-ecossistema-aidd` (grafo do repositório inteiro)
- `C-Users-trcnologia-Desktop-worktrees_auditoria-aidd-visual-maps-ciclo-01-Fase_3_Construtor` (outra sessão, ativa)
- os 6 subgrafos do padrão: `vsa-aidd-nucleo`, `vsa-modulo-governanca`, `vsa-triade-fluxo-pure`, `vsa-triade-fluxo-open`, `vsa-triade-fluxo-freedom`, `vsa-modulo-plataforma-ops` (reindexados a partir da main depois do merge do Bloco 7)
