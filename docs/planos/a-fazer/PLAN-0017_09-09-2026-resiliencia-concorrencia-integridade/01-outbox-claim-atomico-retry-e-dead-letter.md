# Item — outbox-claim-atomico-retry-e-dead-letter

> **Escopo:** Implementar claim atômico com exclusão mútua entre workers, contador de tentativas, transição para dead-letter queue após N falhas e deduplicação via seq monotônico no Outbox pattern.
> **Status:** [PARCIAL — parte ja implementada, ver auditoria abaixo]
> **Auditoria por reproducao real (11-09-2026):** PARCIAL. A coluna tentativas existe em _outbox_events (com migracao idempotente) e o dead-letter funciona, provado por test_dead_letter_apos_max_tentativas. Faltam claimed_at, claimed_by e seq monotonico: grep -rn claimed_at componentes tools nao retorna nada, logo nao existe claim atomico.

---

## Contexto já investigado

- outbox_worker.py lê pendentes e dispara sem claim atômico [OUT-2/3]. Dois workers duplicam eventos e falhas de listener geram loop infinito de polling sem dead-letter.

## Definição de Pronto

1. Adicionar colunas tentativas, claimed_at, claimed_by e seq monotônico na tabela _outbox_events.
2. Implementar claim atômico via UPDATE ... WHERE status='pendente' AND claimed_at IS NULL.
3. Encaminhar para status='dead_letter' após N (ex: 5) tentativas consecutivas de falha no listener.
4. Criar tabela de deduplicação _eventos_processados para idempotência do consumidor.

## Critério de saída

- Teste com 2 workers concorrentes processa cada evento exatamente 1 vez. Teste com listener falho move para dead-letter sem loop infinito.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: outbox-claim-atomico-retry-e-dead-letter.
Siga rigorosamente a Definição de Pronto acima:
1. Adicionar colunas tentativas, claimed_at, claimed_by e seq monotônico na tabela _outbox_events.
2. Implementar claim atômico via UPDATE ... WHERE status='pendente' AND claimed_at IS NULL.
3. Encaminhar para status='dead_letter' após N (ex: 5) tentativas consecutivas de falha no listener.
4. Criar tabela de deduplicação _eventos_processados para idempotência do consumidor.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: outbox-claim-atomico-retry-e-dead-letter.
Strictly follow the Definition of Done above:
1. Adicionar colunas tentativas, claimed_at, claimed_by e seq monotônico na tabela _outbox_events.
2. Implementar claim atômico via UPDATE ... WHERE status='pendente' AND claimed_at IS NULL.
3. Encaminhar para status='dead_letter' após N (ex: 5) tentativas consecutivas de falha no listener.
4. Criar tabela de deduplicação _eventos_processados para idempotência do consumidor.
Ensure exit code 0 across relevant tests and gates.
```
