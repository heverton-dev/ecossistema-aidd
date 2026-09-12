# Item 11 — Sincronizacao requirements generator

> **Escopo:** Entra: a Fase 5 (`05_criador.py`) do pipeline do aidd-generator, que grava `requirements.txt` fixo (`requests>=2.31.0`) no projeto gerado sem nunca revisitar esse arquivo depois que a Fase 8 (`08_implementador.py`) gera código real via LLM (FastAPI/uvicorn/etc., conforme o caso). Não entra: mudar o mecanismo de MCP hand-rolled (já coberto por outro achado do levantamento NIH, fora deste item) nem o restante do pipeline de 8 fases.
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** NAO AUDITADO — evidencia: (nota pendente de medicao real - nao preencher com estimativa)
> **Nota Alvo (0-10):** NAO AUDITADO
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto já investigado

- Achado em 2026-09-07 investigando o item 7 do plano `direcionamento-estrategico-anti-nih` (levantamento de dependências por ferramenta), via leitura real de código, não suposição.
- `tools/aidd-generator/scripts/phases/05_criador.py:772-776` grava `{pasta_projeto}/requirements.txt` com conteúdo fixo: só `requests>=2.31.0`.
- Nenhuma fase posterior atualiza esse arquivo — confirmado via grep por "requirements" em `08_implementador.py` (zero ocorrências), mesmo essa fase instruindo o LLM a gerar código que tipicamente usa FastAPI/uvicorn/outras libs (`08_implementador.py:384` manda expor `/mcp/rpc` e webhook HMAC).
- A checagem de auditoria existente (`05_criador.py:269-272`) só confere se o arquivo `requirements.txt` *existe* — nunca se o conteúdo bate com os imports reais do código gerado.
- Efeito prático: o app entregue ao usuário final frequentemente não sobe (`ModuleNotFoundError`) porque falta declarar as dependências que o próprio LLM usou ao escrever o código, num pipeline que se anuncia como gerador de app funcional.

## Definição de Pronto

1. Reproduzir o bug: gerar um projeto novo via `/generate`, inspecionar os imports reais do código produzido pela Fase 8 e confirmar que `requirements.txt` gerado não cobre todos eles.
2. Implementar extração real dos imports de terceiros usados no código gerado (ex.: AST parsing do(s) arquivo(s) produzidos na Fase 8, ou pedir ao LLM que declare suas próprias dependências como parte do contrato de saída da Fase 8) e sincronizar com `requirements.txt` antes da Fase 5 finalizar ou como pós-processamento da Fase 8.
3. Teste automatizado que gera um projeto de ponta a ponta e confirma que `pip install -r requirements.txt` seguido de start do app não falha por `ModuleNotFoundError` de dependência de terceiro usada no código.
4. Suíte de testes do generator (770 testes) continua 100% verde após a mudança.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 11: Sincronizacao requirements generator.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 11: Sincronizacao requirements generator.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
