---
name: aidd-bridge
description: Dispara o Fluxo 03 (Low-Code / Apps Unificadas | Slash: /bridge) da Tríade Canônica. Desmonte de lock-in Lovable/v0/Bolt e migração PostgreSQL.
---

# aidd-bridge — Alias do Fluxo 03 Canônico (Novo comando canônico: /freedom)

> **Aviso de Taxonomia:** O comando oficial e canônico para disparar o Fluxo 03 completo da Tríade é **`/freedom`** (skill `aidd-freedom` ou CLI `python ecossistema.py freedom`). O comando `/bridge` é reservado para as operações atômicas da ferramenta (skill `aidd-bridge-runner`).

Dispara e conduz o Fluxo 03 (`aidd-freedom`) da Tríade Canônica de criação de software no Ecossistema AIDD:
`[FORGE -> PLANNER] -> BRIDGE -> [MASTER -> ENTERPRISE -> OPS]`

## Gatilhos Universais:
- Comando Slash: `/freedom <nome_ou_ideia> --origem <pasta_export>` (ou `/bridge` por compatibilidade)
- Invocação por Skill: `/aidd-freedom` ou `/aidd-bridge`
- Linguagem Natural: "libertar app lovable", "desacoplar app low-code", "migrar v0 ou bolt para postgresql", "empacotar projeto low-code"

## Como Executar

### 1. Via CLI Central (Zero Fricção):
```bash
python ecossistema.py bridge --nome "App Hub" --slug app-hub --dominio saas --pasta ./projetos/app-hub --origem ./exports/lovable-app
```
Ou via comando legado:
```bash
python ecossistema.py run-fluxo --fluxo bridge --nome "App Hub" --slug app-hub --dominio saas --pasta ./projetos/app-hub --origem ./exports/lovable-app
```

### 2. Simulação (Dry-Run):
```bash
python ecossistema.py bridge --nome "App Hub" --slug app-hub --dominio saas --pasta ./projetos/app-hub --origem ./exports/lovable-app --dry-run
```

## Ação do Agente:
1. Analisa a pasta exportada (Lovable, v0, Bolt) eliminando vendor lock-in e substituindo client Supabase/BaaS por chamadas à API limpa.
2. Gera schema PostgreSQL e unifica o frontend Next.js/React preservando 100% da UI/UX.
3. Harmoniza em Monólito Modular VSA com blindagem SHA-256 e entrega do *Quarteto Sine Qua Non*.
