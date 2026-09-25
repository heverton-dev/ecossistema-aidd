# docs/diagnosticos

Sessões do `aidd-diagnose`, uma pasta por sessão: `<AAAAMMDD>_<slug>/`.

Cada sessão guarda:
- `sessao.json`: sintoma, data de início e fases concluídas (`diagnose iniciar` / `diagnose fase`).
- `fase_NN_<hora>.log`: registro de cada fase (`diagnose registrar`).
- `RELATORIO-CAUSA-RAIZ.md`: relatório final (`diagnose relatorio`), conferido por `gates/G_aidd_diagnose.py`.
- `handoff-diagnose.json`: bastão para a próxima ferramenta (`handoff.py emitir`).

Os testes nunca gravam aqui: eles usam `AIDD_DIAGNOSE_RAIZ` apontando para uma pasta temporária.
