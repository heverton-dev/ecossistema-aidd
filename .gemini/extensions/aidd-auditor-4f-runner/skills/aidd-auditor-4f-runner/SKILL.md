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
Todo o ciclo de vida deste pipeline DEVE ser gerado estritamente dentro de `docs/auditoria/<ferramenta-alvo>/ciclo-NN/` (ex: `docs/auditoria/aidd-melhoria/ciclo-01/`); só o gate `G_auditoria_15D.py` fica na raiz da ferramenta. Cada nova rodada abre o próximo ciclo (`python scripts/scaffold_auditoria.py <ferramenta>`: sem ciclo → `ciclo-01`; ciclo vigente sem `LAUDO-15D-REVISADO.md` → retoma; ciclo concluído → abre `ciclo-NN+1`, herdando o `DOD.md` e comparando Nota Anterior → Nota Nova). É terminantemente proibido jogar artefatos, laudos 15-D, DoD ou Planos de Evolução em `docs/planos/`. O agente orquestrador consolida os artefatos das 4 fases nessa pasta.

## Fluxo de Execução Restrita (4 Fases)
- O Runner intercepta o manifesto JSON do alvo (ex: `docs/auditoria/template-pipeline-4f.json`).
- Cria/Aloca a pasta do ciclo: `docs/auditoria/<tool-name>/ciclo-NN/`. Se todas as fases do manifesto já têm saída, o orquestrador informa `NADA A FAZER` e não declara sucesso.
- Acumula as fases numa branch própria do ciclo (`audit/<pipeline_id>`), sem tocar a branch atual. Cada fase roda seu `gate_fase` antes do commit; reprovou, o pipeline para sem commitar.
- Lança a Fase 1 (Inspetor) e aguarda o EXIT 0 e o `output_handoff` (Laudo 15-D).
- Lança a Fase 2 (Arquiteto) que gera o `PLANO-EVOLUCAO.md` na pasta da auditoria.
- Lança a Fase 3 (Construtor) que efetua o código.
- Lança a Fase 4 (Inspetor de Retorno) que valerá o `DOD`.
- No fim roda o `gate_final` (bateria completa) uma vez. Se EXIT 0, emite o Join Barrier: o merge só acontece com `python scripts/orquestrador_4f.py --manifest <json> --aprovar` (ação humana), e só se a branch do ciclo não mudou depois do `gate_final`.

## Disparo
Quando acionado via linguagem natural ou slash, este agente DEVE parar, solicitar ao usuário a confirmação do Harness/Model que consta no manifesto JSON, e então chamar a ferramenta de Terminal (bash/cmd) para executar o comando Python de orquestração.
