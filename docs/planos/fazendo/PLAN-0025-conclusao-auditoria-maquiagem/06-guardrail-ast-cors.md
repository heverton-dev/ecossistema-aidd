# Item 6 — Guardrail AST para CORS

> **Escopo:** Entra: o template/fase do aidd-generator que produz `src/app.py` com `CORSMiddleware` — corrigir para não combinar `allow_origins=["*"]` com `allow_credentials=True`. Não entra: mudar outras partes do pipeline de 8 fases.
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** NAO AUDITADO — evidencia: (nota pendente de medicao real - nao preencher com estimativa)
> **Nota Alvo (0-10):** NAO AUDITADO
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- Confirmado por fork de auditoria rodando o app real: `teste-isolado-aidd-generator/src/app.py` tem `app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, ...)` — combinação insegura (navegadores modernos rejeitam essa combinação; onde não rejeitam, expõe CORS amplo com credenciais).
- App gerado é real e funcional (CRUD/MCP/webhook testados ao vivo) — este é o único bug real encontrado nesse projeto de saída, isolado e pontual.

## Definicao de Pronto

1. Gerar um novo projeto via `/generate` e confirmar no `src/app.py` gerado que a combinação insegura não aparece mais (origins explícito e/ou credentials condicionado).
2. Existe um teste automatizado (unit ou lint AST) que falha se `allow_origins=["*"]` aparecer junto de `allow_credentials=True` em qualquer app gerado pelo generator, prevenindo regressão.
3. A suíte de testes do generator (770 testes) continua 100% verde após a mudança.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 6: Guardrail AST para CORS.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 6: Guardrail AST para CORS.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
