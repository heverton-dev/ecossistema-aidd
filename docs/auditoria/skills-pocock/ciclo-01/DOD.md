# Definição de Pronto (Definition of Done - DoD) — skills-pocock

> Critérios de aceite da evolução das skills derivadas de `mattpocock/skills` (commit upstream `c55ee46`, licença MIT).
> Fonte canônica das skills: `componentes/compartilhado/skills/<skill>/SKILL.md`, distribuída por `python ecossistema.py components sync`.

## Critérios Obrigatórios de Aceite

1. **DoD 1: Diagnóstico com loop vermelho (D8)**
   - `aidd-diagnose` exige um comando que já rodou e fica vermelho no bug antes de qualquer hipótese, reduz a reprodução ao mínimo, lista de 3 a 5 hipóteses em ordem (testadas uma por vez) e marca logs temporários com `[DEBUG-xxxx]`.
   - Compatível com o gate planejado em `docs/auditoria/aidd-diagnose/ciclo-01` (uma hipótese **ativa** por vez).

2. **DoD 2: Tickets em fatias verticais (D10)**
   - `aidd-tickets` produz tickets que entregam um comportamento completo cada, com a lista "Bloqueado por", e trata refatoração ampla como adicionar → migrar em lotes → remover. Mantém "Target Files" e "Validation Command" (nossos, melhores que o original).

3. **DoD 3: Entrevista em rodadas (D2)**
   - `aidd-grill` e `aidd-grill-docs` perguntam em rodadas numeradas com resposta recomendada, buscam fatos sozinhos e mantêm o modo não-interativo (Consolidated Assumptions).

4. **DoD 4: TDD sem testes de fachada (D8)**
   - `aidd-tdd` exige pontos de teste combinados antes e proíbe teste tautológico, acoplado à implementação e fatiado em camadas. Mantém Zero Stubs.

5. **DoD 5: Retrospectiva que vira gate (D12)**
   - Skill nova `aidd-retro` classifica cada erro de sessão como mecânico (vira gate em `gates/`) ou de julgamento (vira regra de revisão) e entrega a lista em ordem de gravidade.

6. **DoD 6: Guia de escrita para agentes (D1)**
   - Skill nova `aidd-escrita-agentes` (referência) cobre ponteiros, regra que não muda nada, sedimento, ordem negativa e fonte única.

7. **DoD 7: Glossário e decisões registradas (D1)**
   - `CONTEXT.md` na raiz com os termos ambíguos do ecossistema e `docs/adr/` com formato definido; ambiguidades não resolvidas ficam listadas para o usuário decidir (nunca decididas pelo agente). `/aidd-reexplica` usa o glossário.

8. **DoD 8: Entrega com evidência (D15)**
   - Skill nova `aidd-entrega` com modelo de fechamento: evidência antes/depois com exit code real, "dá para desfazer?" e "o que pode quebrar".

9. **DoD 9: Wizard para passos humanos (D11)**
   - Skill nova `aidd-wizard` com `template.sh` testado (gravação idempotente no `.env`, entrada de segredo oculta, funciona no Git Bash do Windows).

10. **DoD 10: Distribuição e sem duplicata (D15)**
    - Todas as skills novas/alteradas sincronizadas nos harnesses (`components verify` exit 0), cópia do forge atualizada, relatório de skills globais duplicadas gerado. Remoção de cópias globais só pelo usuário.

11. **DoD 11: Prova de uso real (D13)**
    - `gates/G_PROVA_SKILLS_POCOCK.py` roda as skills alteradas em casos reais e confere o artefato; tem teste provando que reprova artefato ruim; execução real anexada ao `RELATORIO-CONSTRUTOR.md`.

12. **DoD 12: Gate final**
    - `python ecossistema.py audit` retorna exit 0.
