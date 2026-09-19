# Comando /planner

Interface Zero-Fricção de Planejamento e Intake da Tríade AIDD.
Transforma ideias, requisitos de negócio ou especificações em um `PLANNER.json` canônico validado por schema (SDD/BDD).

## Uso Simples (Zero Fricção para Qualquer Usuário):
- `/planner <sua_ideia_ou_requisito>`
  Ex: `/planner "Sistema de logística e rastreamento com rotas"`
- `/planner <1|2|3> <sua_ideia>`
  Ex: `/planner 1 "App de e-commerce do zero puro"`
  Ex: `/planner 2 "Hub de mensageria WhatsApp com Evolution API"`
  Ex: `/planner 3 "Exportar protótipo Lovable para PostgreSQL"`

## Uso Técnico Avançado (CLI):
- `/planner init --fluxo <1|2|3> --nome <nome> --pasta <destino>`
- `/planner validate <caminho_do_plano>`
- `/planner export <caminho_do_plano> --formato factory`
- `/planner audit [pasta]`

## Ação do Agente:
1. Conduz o alinhamento de requisitos (Intake SDD/BDD) com o usuário.
2. Executa deterministicamente `python ecossistema.py planner init ...` com os parâmetros alinhados.
3. Valida a conformidade binária via `python ecossistema.py planner audit`.
