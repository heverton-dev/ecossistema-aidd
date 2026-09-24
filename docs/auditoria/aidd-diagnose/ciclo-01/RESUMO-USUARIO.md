# Resumo Executivo da Auditoria — aidd-diagnose

> **Pipeline:** Auditoria Linear 4 Fases (Inspetor -> Arquiteto -> Construtor -> Retorno)  
> **Status:** Fases 1 e 2 concluídas; Fases 3 e 4 aguardando execução  
> **Data:** 24/09/2026  

---

## Na Festa (O que foi entregue para quem usa)
A ferramenta `aidd-diagnose` (o "detetive" que acha por que algo quebrou) foi auditada nas 15 dimensões e tirou **nota 4/10**: o método de 5 passos é bom, mas nada garante que ele seja seguido. O achado mais grave: o "mapa" do código que ela consulta estava desatualizado (158 de 1734 arquivos Python sumidos) e respondia "nada afetado" sem avisar. Também não havia plano B quando esse mapa sai do ar. O conserto já está desenhado em 8 tickets, prontos para o Construtor.

Durante a auditoria, o próprio gerador de auditorias foi consertado: agora ele obedece ao `CONFIG-EXECUCAO-USUARIO.json` e gera os prompts dos tickets só em inglês.

---

## Painel das 4 Fases

| Fase | Agente / Harness (do config) | Função | Entrega | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Fase 1** | claude / haiku | Inspetor Inicial | Laudo 15-D Inicial (`LAUDO-15D-INICIAL.md`) | Aprovado (EXIT 0) |
| **Fase 2** | agy / haiku | Arquiteto de Software | Plano de Evolução (`PLANO-EVOLUCAO.md` + `.json`, 8 tickets) | Compilado (EXIT 0) |
| **Fase 3** | mimo / mimo-v2.6-flash | Construtor | Código dos 8 tickets | Aguardando |
| **Fase 4** | opencode / big-pickle | Inspetor de Retorno | Laudo 15-D Revisado (`LAUDO-15D-REVISADO.md`) | Aguardando |

> Honestidade de Rótulo (Lei #8): as Fases 1 e 2 desta rodada foram executadas nesta sessão pelo Claude, e não pelos harnesses do painel. O painel mostra o que o `MANIFESTO-4F.json` manda usar a partir de agora.

---

## O que está Ativo e o que Fica para Próximos Ciclos
- **Ativo agora:**
  - `MANIFESTO-4F.json` e `PLANO-EVOLUCAO.json` idênticos ao `CONFIG-EXECUCAO-USUARIO.json`, que continua intocado.
  - Prompts das Fases 2 e 3 e os 8 `prompts_tickets/` em inglês.
- **Próximo ciclo (Fase 3):** CLI `diagnose`, isolamento em worktree, detecção de mapa desatualizado, plano B sem MCP, relatório de causa-raiz, gate próprio, limpeza e handoff.

---

## Na Casa (Comandos Prontos para Copiar)

**Verificar conformidade do Laudo 15-D:**
```bash
python docs/auditoria/aidd-diagnose/G_auditoria_15D.py docs/auditoria/aidd-diagnose/ciclo-01/LAUDO-15D-INICIAL.md
```

**Recompilar o plano a partir do config atual:**
```bash
python scripts/compilador_plano_evolucao.py --plano docs/auditoria/aidd-diagnose/ciclo-01/PLANO-EVOLUCAO.md
```

**Executar a evolução (Fase 3):**
```bash
python ecossistema.py evolucao aidd-diagnose
```
