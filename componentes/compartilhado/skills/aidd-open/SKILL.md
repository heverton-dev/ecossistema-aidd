---
name: aidd-open
description: Dispara o Fluxo 02 (Motores Open-Source | Slash: /open) da Tríade Canônica. Curadoria e integração de engines open-source em fatias VSA.
---

# aidd-open — Fluxo 02 Canônico (Motores Open-Source | /open)

Dispara e conduz o Fluxo 02 (`aidd-open`) da Tríade Canônica de criação de software no Ecossistema AIDD:
`[FORGE -> PLANNER] -> FACTORY -> [MASTER -> ENTERPRISE -> OPS]`

## Gatilhos Universais:
- Comando Slash: `/open <nome_ou_ideia> [dominio]`
- Invocação por Skill: `/aidd-open` ou skill `aidd-open`
- Linguagem Natural: "criar projeto com base em open-source", "integrar engine open-source", "gerar via open"

## Como Executar

### 1. Via CLI Central (Zero Fricção):
```bash
python ecossistema.py open --nome "ERP Clínicas" --slug erp-clinicas --dominio clinicas --pasta ./projetos/erp-clinicas
```
Ou via comando legado:
```bash
python ecossistema.py run-fluxo --fluxo open --nome "ERP Clínicas" --slug erp-clinicas --dominio clinicas --pasta ./projetos/erp-clinicas
```

### 2. Simulação (Dry-Run):
```bash
python ecossistema.py open --nome "ERP Clínicas" --slug erp-clinicas --dominio clinicas --pasta ./projetos/erp-clinicas --dry-run
```

## Ação do Agente:
1. Alinha os motores open-source de referência, rotas e requisitos de integração com o usuário.
2. Dispara a fábrica com curadoria de engines, contratos OpenAPI e docker compose multi-service.
3. Harmoniza a solução em Monólito Modular VSA + Next.js com blindagem SHA-256 e entrega do *Quarteto Sine Qua Non*.
