---
name: aidd-orchestrator-runner
description: Orquestrador mestre síncrono da Tríade Canônica. Executa qualquer fluxo com validação formal de contratos de handoff.
---

# AIDD Orchestrator Runner — Orquestrador Síncrono da Tríade Canônica

Esta skill dispara a esteira industrial integrada do ecossistema:
`[FORGE -> PLANNER] -> {GENERATOR | FACTORY | BRIDGE} -> [MASTER -> ENTERPRISE -> OPS]`

## Invariantes de Execução:
1. **Execução Síncrona:** Nenhuma etapa avança sem que a anterior tenha concluído com sucesso (`exit 0`).
2. **Handoffs Validados Mecanicamente:** Validação de JSON Schema estrito entre etapas:
   - `handoff-planner-to-engine.schema.json`
   - `handoff-engine-to-master.schema.json`
   - `handoff-master-to-enterprise.schema.json`
   - `handoff-enterprise-to-ops.schema.json`
3. **Parada Imediata em Falhas (Fail-Fast):** Qualquer divergência ou quebra de gate interrompe o pipeline na hora.
4. **Persistência Estruturada:** Gera o manifesto final `ORQUESTRACAO_EXECUCAO.json` no diretório alvo.

## Comandos CLI
```bash
# Fluxo 01: Do Zero Puro
python ecossistema.py run-fluxo --fluxo 1 --nome "<Nome>" --slug <slug> --dominio <dominio> --pasta <destino>

# Fluxo 02: Open Source
python ecossistema.py run-fluxo --fluxo 2 --nome "<Nome>" --slug <slug> --dominio <dominio> --pasta <destino>

# Fluxo 03: Low-Code Bridge
python ecossistema.py run-fluxo --fluxo 3 --nome "<Nome>" --slug <slug> --dominio <dominio> --pasta <destino> --origem <export_path>
```
Adicione `--dry-run` a qualquer comando para simular e verificar a conformidade dos contratos sem modificar o sistema de arquivos.
