---
name: freedom
description: Dispara o Fluxo 03 (Low-Code / Apps Unificadas | Slash: /freedom) da Tríade Canônica. Desmonte de lock-in Lovable/v0/Bolt e migração PostgreSQL.
---

# /freedom — Fluxo 03 Canônico (Low-Code / Apps Unificadas)

Dispara e conduz o Fluxo 03 (`aidd-freedom`) da Tríade Canônica de criação de software no Ecossistema AIDD:
`[FORGE -> PLANNER] -> BRIDGE -> [MASTER -> ENTERPRISE -> OPS]`

## Gatilhos Universais:
- Comando Slash: `/freedom <caminho_do_export> [nome_do_projeto]`
- Invocação por Skill: `/freedom` ou skill `freedom`
- Linguagem Natural: "libertar app lovable", "desacoplar app low-code", "migrar v0 ou bolt para postgresql", "empacotar projeto low-code"

## Como Executar

### 1. Via CLI Central (Alta Ergonomia):
```bash
python ecossistema.py freedom ./exports/lovable-app "App Hub"
```
Ou com flags explícitas:
```bash
python ecossistema.py freedom --nome "App Hub" --slug app-hub --dominio saas --pasta ./projetos/app-hub --origem ./exports/lovable-app
```

### 2. Simulação (Dry-Run):
```bash
python ecossistema.py freedom ./exports/lovable-app --dry-run
```

## Ação do Agente:
1. Analisa a pasta exportada (Lovable, v0, Bolt) eliminando vendor lock-in e substituindo client Supabase/BaaS por chamadas à API limpa.
2. Gera schema PostgreSQL e unifica o frontend Next.js/React preservando 100% da UI/UX.
3. Harmoniza em Monólito Modular VSA com blindagem SHA-256 e entrega do *Quarteto Sine Qua Non*.
