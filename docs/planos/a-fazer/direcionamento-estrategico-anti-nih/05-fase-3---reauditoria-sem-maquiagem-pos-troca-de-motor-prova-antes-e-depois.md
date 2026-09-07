# Item 5 — Fase 3 - Reauditoria sem maquiagem pos-troca de motor, prova antes e depois

> **Escopo:** Entra: repetir, depois de concluída a Fase 2 (troca de motor), exatamente o mesmo método da auditoria de 2026-09-07 (pytest ao vivo + subir os projetos gerados) e publicar um segundo relatório mostrando a diferença real. Não entra: fazer a troca de motor em si (isso é o item 4/Fase 2).
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana — só pode rodar depois de pelo menos uma sub-troca da Fase 2 estar implementada]
> **Modelo sugerido:** Claude Sonnet · Antigravity Gemini 3.7 · MiMo mimo-v2.5-pro (reexecução de método já definido, não decisão nova)

---

## Contexto ja investigado

- Método original documentado e reprodutível: `docs/relatorios/relatorio-auditoria-ecossistema-aidd-sem-maquiagem.html` — rodar `pytest -q` de verdade em cada `tools/<ferramenta>`, subir os projetos de saída (`teste-isolado-aidd-*`, `teste-integrado-ecossistema-aidd`) numa porta local e testar requisição real, comparar contra a telemetria estática do repo.
- Sem essa reauditoria, "trocamos pra Cookiecutter"/"corrigimos o CSP" viram alegação não verificada — exatamente o padrão que a auditoria original expôs (gate verde sem rodar pytest, telemetria sem remedir).

## Definicao de Pronto

1. Gerar novos projetos de saída (equivalentes a `teste-isolado-aidd-master`, `-enterprise`, `-ops`, `-generator`) depois da Fase 2 concluída, usando o motor novo.
2. Rodar `pytest -q` real em cada ferramenta + subir os novos projetos de saída, exatamente como na auditoria original.
3. Publicar um relatório novo (mesmo formato do artifact original) com uma seção explícita "antes → depois" por achado do relatório original — cada achado crítico/atenção precisa aparecer como "corrigido (com evidência)" ou "ainda pendente", nunca omitido silenciosamente.
4. Notas por dimensão (heatmap 0-10) remedidas, não copiadas do relatório anterior.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 5: Fase 3 - Reauditoria sem maquiagem pos-troca de motor, prova antes e depois.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 5: Fase 3 - Reauditoria sem maquiagem pos-troca de motor, prova antes e depois.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
