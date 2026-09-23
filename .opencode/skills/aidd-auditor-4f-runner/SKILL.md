---
name: aidd-auditor-4f-runner
description: "Motor agnóstico do Pipeline Linear de Auditoria 4 Fases (Inspetor, Arquiteto, Construtor, Retorno). Executa em Git Worktrees efêmeras."
---

# `aidd-auditor-4f-runner` (AIDD Pipeline 4F)

Este motor orquestra as 4 fases estritas de auditoria e correção contínua do Ecossistema, validando ferramentas através da Lens 15-D.

## Invariância e Agnosticismo
1. **OS Agnostic:** Os scripts e shells devem usar `os.path.join` e chamadas cross-platform, garantindo sucesso em Windows, Linux e Mac.
2. **Harness/LLM Agnostic:** O pipeline engole qualquer LLM. Os campos "Harness" e "Model" no JSON de orquestração governam a injeção.
3. **Omni-Ativação:** 
   - **Terminal:** `python ecossistema.py audit-4f --manifest <path.json>`
   - **Slash Command:** `/audit-4f <path_to_json>`
   - **Natural Language:** "Inicie a auditoria 4F na ferramenta X", "rode o pipeline de auditoria".

## Regra Estrutural de Pastas (Motor de Refração)
Todo o ciclo de vida deste pipeline DEVE ser gerado estritamente dentro da raiz `docs/auditoria/<ferramenta-alvo>-v<N>/` (ex: `docs/auditoria/aidd-melhoria-v2/`). É terminantemente proibido jogar artefatos, laudos 15-D, DoD ou Planos de Evolução em `docs/planos/`. O agente orquestrador tem a obrigação de detectar o versionamento anterior (se existir v1, cria v2) e consolidar os 4 passos ali.

## Fluxo de Execução Restrita (4 Fases)
- O Runner intercepta o manifesto JSON do alvo (ex: `docs/auditoria/template-pipeline-4f.json`).
- Cria/Aloca a pasta versionada: `docs/auditoria/<tool-name>-v<N>/`.
- Isola o branch (`git checkout -b audit/<tool-name>`).
- Lança a Fase 1 (Inspetor) e aguarda o EXIT 0 e o `output_handoff` (Laudo 15-D).
- Lança a Fase 2 (Arquiteto) que gera o `PLANO-EVOLUCAO.md` na pasta versionada.
- Lança a Fase 3 (Construtor) que efetua o código.
- Lança a Fase 4 (Inspetor de Retorno) que valerá o `DOD`.
- Se EXIT 0, emite alerta de bloqueio (Join Barrier) aguardando APROVAÇÃO HUMANA para fazer o merge.

## Disparo
Quando acionado via linguagem natural ou slash, este agente DEVE parar, solicitar ao usuário a confirmação do Harness/Model que consta no manifesto JSON, e então chamar a ferramenta de Terminal (bash/cmd) para executar o comando Python de orquestração.
