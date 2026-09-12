# Item 4 — Remocao de seed de demo

> **Escopo:** Entra: `scripts/compose_suite.py` (master e enterprise) parar de inserir por padrão o webhook de demonstração no banco do projeto gerado. Não entra: remover a feature de webhook em si — o seed deve virar opt-in explícito e claramente rotulado, não desaparecer.
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** NAO AUDITADO — evidencia: (nota pendente de medicao real - nao preencher com estimativa)
> **Nota Alvo (0-10):** NAO AUDITADO
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- Confirmado via fork de auditoria: todo projeto novo gerado por `compose_suite.py` grava um registro na tabela `webhooks` apontando para `https://webhook.site/demo-aidd-master` (ou `-enterprise`) com secret fixo `sec_demo_2026`, por padrão, direto no banco do projeto — em ambas as ferramentas (núcleo compartilhado).
- Isso contraria a Regra de Ouro #5 do AGENTS.md ("Zero Stubs / Zero Mocks Falsos em Produção").

## Definicao de Pronto

1. Gerar um projeto novo (`python ecossistema.py master add-module <x>` ou fluxo equivalente do enterprise) e confirmar via consulta SQL na tabela `webhooks` que nenhum registro `webhook.site`/secret fixo aparece por padrão.
2. Se uma flag opt-in for criada (ex.: `--com-exemplo-webhook`), confirmar que rodar com ela produz o seed claramente rotulado como exemplo (nome/descrição distinguível de dado real, não indistinguível).
3. A suíte de testes de `compose_suite` (master e enterprise) continua 100% verde após a mudança, e ganha um teste novo que falha se o seed voltar a aparecer sem a flag.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 4: Remocao de seed de demo.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 4: Remocao de seed de demo.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
