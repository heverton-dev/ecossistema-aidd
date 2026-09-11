# Item — testes-resiliencia-outbox-crash-pos-emit-dead-letter

> **Escopo:** Adicionar testes de resiliência ao Outbox worker cobrindo crash pós-emit (antes de marcar como processado) e listener que falha sistematicamente (dead-letter queue).
> **Status:** [CONCLUIDO — verificado por reproducao real]
> **Auditoria por reproducao real (11-09-2026):** FEITO. pytest tests/unit/test_outbox_worker.py -q em tools/aidd-enterprise/, 8 testes, exit 0. Inclui test_crash_pos_emit_redespacha_idempotente e test_dead_letter_apos_max_tentativas.

---

## Contexto já investigado

- test_outbox_worker.py testa apenas crash em memória antes do emit [TS-6]. Crash pós-emit e loop infinito de listener falho precisam de cobertura.

## Definição de Pronto

1. Criar teste simulando crash imediatamente após envio do evento mas antes de atualizar status.
2. Verificar redespacho idempotente.
3. Criar teste de dead-letter após N falhas.

## Critério de saída

- Redespacho idempotente e dead-letter comprovados por testes.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: testes-resiliencia-outbox-crash-pos-emit-dead-letter.
Siga rigorosamente a Definição de Pronto acima:
1. Criar teste simulando crash imediatamente após envio do evento mas antes de atualizar status.
2. Verificar redespacho idempotente.
3. Criar teste de dead-letter após N falhas.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: testes-resiliencia-outbox-crash-pos-emit-dead-letter.
Strictly follow the Definition of Done above:
1. Criar teste simulando crash imediatamente após envio do evento mas antes de atualizar status.
2. Verificar redespacho idempotente.
3. Criar teste de dead-letter após N falhas.
Ensure exit code 0 across relevant tests and gates.
```
