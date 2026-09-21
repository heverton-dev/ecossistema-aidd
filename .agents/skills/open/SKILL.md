---
name: open
description: Dispara o Fluxo 02 (Motores Open-Source | Slash: /open) da Tríade Canônica. Curadoria de motores e fatias verticais VSA.
---

# /open — Fluxo 02 Canônico (Motores Open-Source)

Dispara e conduz o Fluxo 02 (`aidd-open`) da Tríade Canônica de criação de software no Ecossistema AIDD:
`[FORGE -> PLANNER] -> FACTORY -> [MASTER -> ENTERPRISE -> OPS]`

## Gatilhos Universais:
- Comando Slash: `/open <nome_ou_ideia> [dominio]`
- Invocação por Skill: `/open` ou skill `open`
- Linguagem Natural: "criar com open-source", "integrar motor open source", "gerar app via factory"

## Como Executar

### 1. Via CLI Central (Alta Ergonomia):
```bash
python ecossistema.py open "Meu ERP" saas
```
Ou com flags explícitas:
```bash
python ecossistema.py open --nome "Meu ERP" --slug meu-erp --dominio saas --pasta ./projetos/meu-erp
```

### 2. Simulação (Dry-Run):
```bash
python ecossistema.py open "Meu ERP" --dry-run
```

## Ação do Agente:
1. Curadoria de motores open-source de padrão industrial compatíveis com o domínio solicitado.
2. Integração em fatias verticais VSA sob Monólito Modular com persistência unificada.
3. Blindagem de integridade SHA-256 e entrega do *Quarteto Sine Qua Non*.
