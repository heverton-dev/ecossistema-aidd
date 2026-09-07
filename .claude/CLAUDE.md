# Claude Code Guidelines — Ecossistema AIDD Unificado
Consulte a fonte única de verdade em: ../AGENTS.md

Diretivas essenciais:
- Sempre responder em Português Brasileiro (PT-BR).
- Respeitar a Tríade Caveman Ultra para economia severa de tokens.
- Executar os gates determinísticos antes de qualquer commit.
- Usar a CLI raiz python ecossistema.py para operações unificadas.
- No início da sessão, rodar silenciosamente `python ecossistema.py dependencia verify`; se falhar, rodar `dependencia bootstrap` e informar o resultado em 1 frase — nunca pedir pro usuário digitar isso (ver AGENTS.md §0).
