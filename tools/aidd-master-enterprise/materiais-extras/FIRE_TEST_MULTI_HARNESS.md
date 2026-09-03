# FIRE TEST — AIDD Master Pack v5.1 (Teste de Fogo Multi-Harness)

> **Objetivo:** Validar se o ciclo de vida completo da v5.1 se comporta de forma idêntica e determinística em 3 harnesses diferentes, com o mesmo projeto e o mesmo input.
> **Projeto-Alvo:** `plataforma-saas-suite` com módulos `financeiro` e `contratos`
> **Data:** 2026-09-01

---

## PARTE 0 — PREPARAÇÃO DO AMBIENTE (Única — Executar 1 vez)

```powershell
# 1. Criar a pasta raiz do fire test no Desktop
mkdir C:\Users\trcnologia\Desktop\fire-test-v5
cd C:\Users\trcnologia\Desktop\fire-test-v5

# 2. Clonar o repositório três vezes — uma por harness
git clone --branch v5.1.0 https://github.com/heverton-dev/aidd-master-pack.git mimo-test
git clone --branch v5.1.0 https://github.com/heverton-dev/aidd-master-pack.git opencode-test
git clone --branch v5.1.0 https://github.com/heverton-dev/aidd-master-pack.git claude-test

# 3. Verificar que o clone trouxe a tag v5.1.0 e a branch main atualizada
cd mimo-test    && git log --oneline -5 && cd ..
cd opencode-test && git log --oneline -5 && cd ..
cd claude-test   && git log --oneline -5 && cd ..
```

---

## PARTE 1 — INPUT PADRÃO (Idêntico nos 3 Harnesses)

O prompt abaixo é o **input canônico** a ser entregue a cada harness em PT-BR ou EN. **Copie e cole sem alterar uma vírgula.**

---

### Versão PT-BR

```
Você é um engenheiro sênior operando o AIDD Master Pack v5.1.

Seu diretório de trabalho é: [VER TABELA ABAIXO POR HARNESS]

Execute EXATAMENTE os seguintes comandos em ordem, reportando o resultado de cada um:

PASSO 1 — COMPOSIÇÃO DA SUÍTE:
python scripts/aidd.py compose ./app "Plataforma SaaS Suite" financeiro contratos --db sqlite

PASSO 2 — AUDITORIA COMPLETA DOS 7 GATES:
python scripts/aidd.py audit --report --dir ./app

PASSO 3 — EXECUÇÃO DA SUÍTE DE TESTES:
python scripts/aidd.py test --dir ./app

PASSO 4 — BENCHMARK DE CARGA:
python scripts/aidd.py bench -n 100 --dir ./app

PASSO 5 — GERAÇÃO DE INFRAESTRUTURA IaC:
python scripts/aidd.py scaffold-infra --dir ./app

PASSO 6 — EXPORTAÇÃO DO FRONT-END NEXT.JS:
python scripts/aidd.py export-frontend --dir ./app --stack nextjs

PASSO 7 — INICIAR O SERVIDOR E CONFIRMAR OS 5 PORTAIS:
python ./app/src/server.py
(Confirme que as URLs abaixo respondem com HTTP 200:)
- http://localhost:3000/
- http://localhost:3000/docs
- http://localhost:3000/webhooks
- http://localhost:3000/mcp
- http://localhost:3000/metrics

Ao final de cada passo, reporte: status (PASS/FAIL), tempo em ms e qualquer desvio do esperado.
Não pule etapas. Não resuma. Execute e reporte tudo.
```

---

### English Version

```
You are a senior engineer operating the AIDD Master Pack v5.1.

Your working directory is: [SEE TABLE BELOW PER HARNESS]

Execute EXACTLY the following commands in order, reporting the result of each one:

STEP 1 — SUITE COMPOSITION:
python scripts/aidd.py compose ./app "Plataforma SaaS Suite" financeiro contratos --db sqlite

STEP 2 — FULL AUDIT OF ALL 7 QUALITY GATES:
python scripts/aidd.py audit --report --dir ./app

STEP 3 — RUN THE FULL TEST SUITE:
python scripts/aidd.py test --dir ./app

STEP 4 — LOAD BENCHMARK:
python scripts/aidd.py bench -n 100 --dir ./app

STEP 5 — IaC INFRASTRUCTURE GENERATION:
python scripts/aidd.py scaffold-infra --dir ./app

STEP 6 — NEXT.JS FRONT-END EXPORT:
python scripts/aidd.py export-frontend --dir ./app --stack nextjs

STEP 7 — START SERVER AND CONFIRM ALL 5 PORTALS:
python ./app/src/server.py
(Confirm the following URLs respond with HTTP 200:)
- http://localhost:3000/
- http://localhost:3000/docs
- http://localhost:3000/webhooks
- http://localhost:3000/mcp
- http://localhost:3000/metrics

After each step, report: status (PASS/FAIL), elapsed time in ms and any deviation from expected behavior.
Do not skip steps. Do not summarize. Execute and report everything.
```

### Diretório de Trabalho por Harness

| Harness | Modelo | Diretório de Trabalho |
| :--- | :--- | :--- |
| **Mimocode** | Mimo V2.5 Pro | `C:\Users\trcnologia\Desktop\fire-test-v5\mimo-test` |
| **OpenCode** | Provedor Free (OpenCode) | `C:\Users\trcnologia\Desktop\fire-test-v5\opencode-test` |
| **Claude Code** | Claude Sonnet | `C:\Users\trcnologia\Desktop\fire-test-v5\claude-test` |

---

## PARTE 2 — EXECUÇÃO HARNESS A HARNESS

### [H1] — MIMOCODE / Mimo V2.5 Pro

**Como abrir:**
1. Abrir o Mimocode.
2. Apontar o workspace para `C:\Users\trcnologia\Desktop\fire-test-v5\mimo-test`.
3. Colar o **Input Padrão** da Parte 1 (ajustando o diretório de trabalho conforme tabela).
4. Executar e aguardar a conclusão de todos os 7 passos.

**O que coletar ao final:**
```
[ ] Passo 1 — compose:         PASS / FAIL | Tempo: ___ms
[ ] Passo 2 — audit (7 Gates): PASS / FAIL | Score: ___% Nota: ___
[ ] Passo 3 — test:            PASS / FAIL | Testes: ___ passed / ___ failed
[ ] Passo 4 — bench:           PASS / FAIL | RPS: ___ | Latência: ___ms
[ ] Passo 5 — scaffold-infra:  PASS / FAIL | Arquivos gerados: ___
[ ] Passo 6 — export-frontend: PASS / FAIL | Arquivos TS gerados: ___
[ ] Passo 7 — server + portais:PASS / FAIL | Portais respondendo: _/5
```

---

### [H2] — OPENCODE / Provedor Free

**Como abrir:**
1. Abrir o OpenCode.
2. Apontar o workspace para `C:\Users\trcnologia\Desktop\fire-test-v5\opencode-test`.
3. Colar o **Input Padrão** da Parte 1 (ajustando o diretório de trabalho).
4. Executar e aguardar a conclusão de todos os 7 passos.

**O que coletar ao final:**
```
[ ] Passo 1 — compose:         PASS / FAIL | Tempo: ___ms
[ ] Passo 2 — audit (7 Gates): PASS / FAIL | Score: ___% Nota: ___
[ ] Passo 3 — test:            PASS / FAIL | Testes: ___ passed / ___ failed
[ ] Passo 4 — bench:           PASS / FAIL | RPS: ___ | Latência: ___ms
[ ] Passo 5 — scaffold-infra:  PASS / FAIL | Arquivos gerados: ___
[ ] Passo 6 — export-frontend: PASS / FAIL | Arquivos TS gerados: ___
[ ] Passo 7 — server + portais:PASS / FAIL | Portais respondendo: _/5
```

---

### [H3] — CLAUDE CODE / Claude Sonnet

**Como abrir:**
1. Abrir o Claude Code no terminal:
   ```powershell
   cd C:\Users\trcnologia\Desktop\fire-test-v5\claude-test
   claude
   ```
2. Colar o **Input Padrão** da Parte 1 (ajustando o diretório de trabalho).
3. Executar e aguardar a conclusão de todos os 7 passos.

**O que coletar ao final:**
```
[ ] Passo 1 — compose:         PASS / FAIL | Tempo: ___ms
[ ] Passo 2 — audit (7 Gates): PASS / FAIL | Score: ___% Nota: ___
[ ] Passo 3 — test:            PASS / FAIL | Testes: ___ passed / ___ failed
[ ] Passo 4 — bench:           PASS / FAIL | RPS: ___ | Latência: ___ms
[ ] Passo 5 — scaffold-infra:  PASS / FAIL | Arquivos gerados: ___
[ ] Passo 6 — export-frontend: PASS / FAIL | Arquivos TS gerados: ___
[ ] Passo 7 — server + portais:PASS / FAIL | Portais respondendo: _/5
```

---

## PARTE 3 — TABELA COMPARATIVA FINAL (Preencher após os 3 testes)

| Critério de Avaliação | Mimocode (V2.5 Pro) | OpenCode (Free) | Claude Code (Sonnet) |
| :--- | :---: | :---: | :---: |
| Passo 1 — Composição completa | | | |
| Passo 2 — 7 Gates (Score %) | | | |
| Passo 3 — Testes (passed count) | | | |
| Passo 4 — Benchmark (RPS) | | | |
| Passo 5 — IaC gerada | | | |
| Passo 6 — Frontend Next.js | | | |
| Passo 7 — Portais respondendo (n/5) | | | |
| **Score Final (passos aprovados)** | **/7** | **/7** | **/7** |
| **Desvios / Intervenções manuais** | | | |
| **Tokens consumidos** | | | |
| **Tempo total estimado** | | | |

---

## PARTE 4 — CRITÉRIOS DE APROVAÇÃO (O Que Define 100%)

Para um harness ser considerado **Aprovado (100% Determinístico)**:

| Critério | Threshold Mínimo |
| :--- | :--- |
| Score de Auditoria (Gate 2) | **100.0% — Nota A+** |
| Testes unitários aprovados | **Mínimo 4 testes** (2 por módulo gerado) |
| RPS no Benchmark | **Acima de 1.000 RPS** |
| Portais respondendo | **5 de 5 (HTTP 200)** |
| Intervenções manuais necessárias | **Zero (0)** |

---

> **Após completar o fire test, traga o relatório preenchido. Farei a auditoria completa de cada linha e diagnosticarei qualquer desvio de comportamento entre os harnesses.**
