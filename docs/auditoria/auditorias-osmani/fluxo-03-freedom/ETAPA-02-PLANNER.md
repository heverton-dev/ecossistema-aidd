# Relatório de Auditoria de Micropipeline — ETAPA 02: PLANNER

> **Fluxo:** 03 (AIDD-FREEDOM)  
> **Micropipeline Auditado:** `aidd-planner` (`ecossistema.py planner init`)  
> **Localização da Ferramenta na Máquina:** `modulos/01-governanca-e-qualidade/core/aidd-planner/`  
> **Data:** 2026-10-21  
> **Status da Etapa:** **AUDITADA — 3 PONTOS DE BLOQUEIO IDENTIFICADOS (Tickets Abertos)**  

---

## 1. Escopo e Propósito do Micropipeline

O `aidd-planner` é o motor de intake e arquitetura de software (BDD/SDD) do ecossistema. Ele é responsável por:
1. Validação de pré-requisitos de ambiente de benchmarking visual (Mobbin MCP / API Key).
2. Validação da entrevista socrática com direcionamento visual (`.aidd/intake/grill.md`).
3. Validação formal da especificação funcional com critérios mecânicos de aceitação (`.aidd/intake/spec.md`).
4. Geração do contrato criptografado `PLANNER.json` (SHA-256) que alimenta o `aidd-master` e as worktrees.

---

## 2. Inconsistências Fatuais Detectadas na Máquina

### [ERRO #001] Bloqueio por Ambiente sem Provedor Mobbin Definido
- **Fato Auditado:** Ao rodar `ecossistema.py run-fluxo --modo-intake autonomo`, o planner abortou a execução:
  ```
  [ERRO] Ambiente do planner não registrado. Escolha como o Mobbin entra...
  ```
- **Causa Raiz na Máquina:** `src/cli.py` (linhas 82-88) invoca `ambiente.verificar()`. No fluxo autônomo, o `orquestrador_sincrono.py` não injetava `--mobbin 1` (para usar o MCP do harness) por padrão, forçando intervenção manual.
- **Ticket Vinculado:** `TCK-PLAN-01`.

### [ERRO #002] Ausência de Geração Automática de Intake no Modo Autônomo
- **Fato Auditado:** O planner rejeitou o início do projeto com:
  ```
  [ERRO] Intake incompleto; o planner não abre sem grill e spec:
    - Falta a entrevista: rode /aidd-grill e grave em .aidd\intake\grill.md
    - Falta a especificação: rode /aidd-spec e grave em .aidd\intake\spec.md
  ```
- **Causa Raiz na Máquina:** Quando a flag `--modo-intake autonomo` é passada, o orquestrador não possuía um scaffold autônomo para compilar o `grill.md` e `spec.md` a partir do prompt da aplicação, transferindo esse ônus para o agente no meio do fluxo.
- **Ticket Vinculado:** `TCK-PLAN-02`.

### [ERRO #003] Rejeição Sintática de Critérios de Aceitação
- **Fato Auditado:** `intake.py` (`validar_criterios_binarios`) rejeitou a frase discursiva:
  `"Zero referências a bibliotecas cliente de Supabase..."`.
- **Causa Raiz na Máquina:** A validação sintática exige padrões de regex explícitos (`exit code 0`, `HTTP \d{3}`, `assert`, métricas com unidade). Faltava no template de exemplo da spec um molde com os padrões sintáticos aceitos pelo validador.
- **Ticket Vinculado:** `TCK-PLAN-03`.

---

## 3. Veredito e Recomendações

* **Classificação:** **APROVADO APÓS MITIGAÇÃO MANUAL (Requer blindagem nativa na máquina).**
* **Ações Corretivas na Máquina:**
  1. Tornar `--mobbin 1` o valor padrão no modo autônomo em `scripts/orquestrador_sincrono.py`.
  2. Implementar sintetizador determinístico de `grill.md` e `spec.md` no `cmd_entrevista --modo autonomo`.
  3. Atualizar o molde padrão de `spec.md` com critérios binários pré-formatados.
