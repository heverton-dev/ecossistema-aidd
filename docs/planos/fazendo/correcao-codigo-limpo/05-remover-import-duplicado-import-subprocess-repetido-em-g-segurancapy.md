# Item 5 — Remover import duplicado (import subprocess repetido) em G_SEGURANCA.py

> **Escopo:** Entra: remover a linha `import subprocess` repetida (linhas 26 e 27) em `tools/aidd-enterprise/scripts/gates/G_SEGURANCA.py` e no seu par `tools/aidd-master/scripts/gates/G_SEGURANCA.py` (hoje idêntico byte-a-byte a esse respeito, confirmado por `diff`). Não entra: `templates/gates/G_SEGURANCA.py` (nas duas ferramentas) — confirmado por grep que **não** tem a duplicata, não precisa de mudança.

> **Status:** ⏳ Rascunho gerado, aguardando aprovação

---

## Contexto já investigado

- Confirmado por grep direto (2026-09-08): `import subprocess` aparece duas vezes seguidas (linhas 26 e 27) em `tools/aidd-enterprise/scripts/gates/G_SEGURANCA.py` e em `tools/aidd-master/scripts/gates/G_SEGURANCA.py`. Não aparece duplicado em `templates/gates/G_SEGURANCA.py` de nenhuma das duas ferramentas.
- Como esse arquivo faz parte do par monitorado pelo gate `G_DRIFT_NUCLEO_COMPARTILHADO.py` (par `scripts/gates`, que hoje espera as duas ferramentas idênticas), a correção precisa ser aplicada **igual** nas duas cópias (`aidd-enterprise` e `aidd-master`) na mesma ordem, para não quebrar esse gate de drift.
- Coordenar sequenciamento com o item 4 deste plano (mesmo arquivo) — fazer os dois juntos evita rodar o `diff`/gate de drift duas vezes à toa.

## Definição de Pronto

1. Uma única linha `import subprocess` em cada um dos dois arquivos afetados (a duplicata removida, não a única ocorrência).
2. `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` continua aprovado depois da mudança (as duas cópias seguem idênticas entre si).
3. `python tools/aidd-enterprise/scripts/gates/G_SEGURANCA.py` (e o equivalente em `aidd-master`) executado e aprovado após a remoção, confirmando que nada dependia do import duplicado.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Execução (2026-09-08)

- Feito junto com o item 4 (mesmo arquivo). `import subprocess` duplicado removido em `scripts/gates/G_SEGURANCA.py` de `aidd-enterprise` e `aidd-master` — confirmado por grep que agora aparece exatamente 1 vez em cada.
- `templates/gates/G_SEGURANCA.py` confirmado sem a duplicata desde o início — nada alterado ali, como previsto.
- `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` aprovado (100% OK) após a mudança.
- **Veredito: Concluído.**

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 5: Remover import duplicado (import subprocess repetido) em G_SEGURANCA.py.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 5: Remover import duplicado (import subprocess repetido) em G_SEGURANCA.py.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
