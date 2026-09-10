# Comando /bridge

Extrai, unifica e empacota aplicações Low-Code (Lovable, v0, Bolt) para infraestrutura própria (VPS/Docker).

## Uso:
`/bridge [scan|convert-db|merge|pack] [argumentos...]`

## Ação:
Executa a skill `skills/aidd-bridge-runner` para inspecionar projetos, migrar schemas Supabase para PostgreSQL puro ou gerar pacotes de deploy VPS com Docker e SSL.
Equivalente CLI: `python ecossistema.py bridge <args>`