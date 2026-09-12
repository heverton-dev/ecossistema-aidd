# Item 3 — Reversao de CSP relaxado

> **Escopo:** Entra: `templates/core/security.py` e `templates/v2/security.py` (tools/aidd-master e tools/aidd-enterprise, núcleo compartilhado) — reverter para CSP estrito ou trocar `unsafe-inline` por nonce/hash. Não entra: redesenhar toda a stack de segurança do enterprise (isso é item 7).
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** NAO AUDITADO — evidencia: (nota pendente de medicao real - nao preencher com estimativa)
> **Nota Alvo (0-10):** NAO AUDITADO
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- Diff pendente (não commitado no momento da auditoria) mudou `templates/core/security.py:73` de `script-src 'self'` para `script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net` — mesma mudança espelhada em `templates/v2/security.py:73` e nos dois arquivos equivalentes de `tools/aidd-master` e `tools/aidd-enterprise` (núcleo compartilhado, coberto por `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py`).
- `unsafe-inline` anula boa parte do valor de um CSP — numa ferramenta que se apresenta como "Zero-Trust"/missão-crítica isso é retrocesso de postura de segurança, não decisão neutra.

## Definicao de Pronto

1. CSP gerado por padrão não contém `unsafe-inline` em `script-src` (inspecionar o HTML/header gerado por um projeto novo).
2. Se o CDN externo (Tailwind/jsdelivr) for mantido, a página usa nonce ou hash de subresource — verificável abrindo o HTML e conferindo que o script tag correspondente tem o nonce/hash batendo com o header CSP.
3. `python -m pytest -q` em tools/aidd-master e tools/aidd-enterprise continuam 100% verde após a mudança (reexecutar as duas suítes completas).
4. `python -c "from gates.G_DRIFT_NUCLEO_COMPARTILHADO import ..."` (ou `python ecossistema.py audit`) continua aprovando — master e enterprise seguem sincronizados no novo baseline.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 3: Reversao de CSP relaxado.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 3: Reversao de CSP relaxado.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
