# Item 12 — Remover imports mortos nos gates locais de master-enterprise

> **Escopo:** Remover importações confirmadamente sem uso em `scripts/gates/G_SEGURANCA.py` e `scripts/gates/G_QUALIDADE.py`, em master e enterprise. Item puramente mecânico, sem decisão de arquitetura.
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]

---

## Contexto ja investigado

Fonte: relatório de auditoria, achado #15, seção 5.5 (confirmado por AST parsing, não por leitura superficial).

- `scripts/gates/G_SEGURANCA.py:35,37,38` (master e enterprise): `import time`, `import hmac`, `import hashlib` — **AST confirma zero usos** no arquivo. Remanescentes de camadas de hash/HMAC que migraram para `core/` (ver Item 1, núcleo compartilhado).
- `scripts/gates/G_QUALIDADE.py:15,17,31` (master e enterprise): `re`, `json` e `FuzzingStrategy` sem uso direto.

## Definicao de Pronto

1. Rodando AST parsing (mesmo método do relatório) sobre `G_SEGURANCA.py` e `G_QUALIDADE.py` em master e enterprise, 0 imports sem uso restantes.
2. Nenhum import removido por engano — confirmar antes de remover, com o mesmo método do relatório, que cada import realmente não é usado nem indiretamente (ex.: via `getattr`, reexport, ou efeito colateral de import).
3. Testes reais dos gates (`G_SEGURANCA`, `G_QUALIDADE`) em master e enterprise passam com exit 0 após a remoção.

## Criterio de saida

- Imports mortos removidos nos 2 arquivos, nas 2 ferramentas.
- Testes reais passando, sem regressão de comportamento dos gates.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 12: remover imports confirmadamente sem uso em
scripts/gates/G_SEGURANCA.py e scripts/gates/G_QUALIDADE.py, em master e enterprise (ver
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, achado #15, secao
5.5).

Fatos que voce precisa saber antes de comecar:
- G_SEGURANCA.py:35,37,38 (master e enterprise): import time, import hmac, import hashlib -
  AST confirma zero usos.
- G_QUALIDADE.py:15,17,31 (master e enterprise): re, json, FuzzingStrategy sem uso direto.

Regras obrigatorias:
1. Item mecanico, sem decisao de arquitetura pendente - pode ser executado sem pausa,
   DESDE QUE voce confirme por AST parsing (nao so leitura visual) que cada import e
   realmente sem uso antes de remover, incluindo uso indireto (getattr, reexport, efeito
   colateral de import).
2. Siga rigorosamente a Definicao de Pronto acima.
3. Nao invente aprovacoes. So marque como concluido apos rodar os testes reais dos gates.
4. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 12: remove confirmed unused imports in
scripts/gates/G_SEGURANCA.py and scripts/gates/G_QUALIDADE.py, in master and enterprise (see
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, finding #15, section
5.5).

Facts you need before starting:
- G_SEGURANCA.py:35,37,38 (master and enterprise): import time, import hmac, import hashlib
  - AST confirms zero uses.
- G_QUALIDADE.py:15,17,31 (master and enterprise): re, json, FuzzingStrategy with no direct
  use.

Mandatory rules:
1. Mechanical item, no pending architectural decision - can be executed without pausing,
   PROVIDED you confirm via AST parsing (not just visual reading) that each import is truly
   unused before removing it, including indirect use (getattr, reexport, import side
   effect).
2. Strictly follow the Definition of Done above.
3. Do not fabricate approvals. Only mark this done after running the real gate tests.
4. Maintain monorepo governance rules (AGENTS.md).
```
