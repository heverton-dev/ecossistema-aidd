# Item 4 — Dividir run_all_checks (G_SEGURANCA.py) em funcoes menores por camada de responsabilidade

> **Escopo:** Entra: dividir o método `SecurityGate.run_all_checks` em métodos privados menores, um por camada de auditoria (ex.: `_camada1_owasp_headers`, `_camada2_jwt`, ..., `_camada8_cve_audit`), chamados em sequência por `run_all_checks`. Vale para as 4 cópias existentes do arquivo: `tools/aidd-enterprise/scripts/gates/G_SEGURANCA.py` (8 camadas, 411 linhas), `tools/aidd-master/scripts/gates/G_SEGURANCA.py` (cópia idêntica hoje), `tools/aidd-enterprise/templates/gates/G_SEGURANCA.py` e `tools/aidd-master/templates/gates/G_SEGURANCA.py` (7 camadas, 330 linhas — sem a camada 8 de CVE audit). Não entra: mudar o comportamento/resultado de nenhuma checagem (refatoração estrutural, sem alteração funcional); não entra decidir se a camada 8 deve existir nos templates (isso é da iniciativa `correcao-arquitetura-limpa`, item 5); não entra consolidar as 4 cópias numa fonte só (acoplamento de runtime entre ferramentas é proibido).

> **Status:** ⏳ Rascunho gerado, aguardando aprovação

---

## Contexto já investigado

- `SecurityGate.run_all_checks` (`tools/aidd-enterprise/scripts/gates/G_SEGURANCA.py:57` em diante) executa 8 responsabilidades diferentes dentro de um único método: headers OWASP, criptografia JWT + timing attack, varredura de SQL Injection, varredura de segredos hardcoded, auditoria de Nginx, auditoria de container Docker, auditoria de persistência SQLite/logs, e CVE dependency audit via `pip-audit`. Cada bloco já está fisicamente separado por comentários `# CAMADA N` — a estrutura lógica para virar métodos já existe implícita no código, falta só extrair.
- Confirmado por `diff` real (2026-09-08): a versão em `templates/gates/` tem só 7 camadas (330 linhas) — a camada 8 (CVE audit) não existe lá. A divisão em métodos deve ser feita nas duas variantes (8 e 7 camadas) mantendo essa diferença real de conteúdo — não inventar a camada 8 na versão de 7 camadas.
- Coordenar sequenciamento com a iniciativa `correcao-arquitetura-limpa`, item 5: aquele item vai registrar um baseline de hash comparando `scripts/gates` vs `templates/gates`. Se este item mudar a estrutura interna do arquivo, o hash muda — combinar ordem de execução com quem tocar o item 5 primeiro, para o baseline não capturar um estado intermediário.

## Definição de Pronto

1. `run_all_checks` chama métodos privados nomeados por camada, cada um com uma única responsabilidade — nenhum método com mais de ~50 linhas.
2. As 4 cópias do arquivo (`scripts/gates` e `templates/gates`, em `aidd-enterprise` e `aidd-master`) refatoradas de forma equivalente, preservando a diferença real de 7 vs 8 camadas entre `scripts/gates` e `templates/gates`.
3. Resultado (`PASS`/`FAIL`/`WARN` por checagem, contagem final de `passed`/`failed`/`warnings`) idêntico ao comportamento anterior — reproduzido rodando o gate antes e depois da refatoração e comparando a saída.
4. Testes existentes que cobrem `G_SEGURANCA.py` (se houver) executados com exit 0 após a mudança.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Execução (2026-09-08)

- `run_all_checks` dividido em `_camada1_owasp_headers` ... `_camada8_cve_audit` + `_relatorio_final`, nas 4 cópias (`scripts/gates` e `templates/gates`, em `aidd-enterprise` e `aidd-master`), preservando a diferença real de 8 vs 7 camadas.
- Reprodução real: saída (`stdout`) e exit code comparados via `diff` entre a versão antes e depois da refatoração, nas 4 cópias — **idênticos em todas**.
- `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` rodado após a mudança nas 4 cópias — **100% OK**, pares `scripts/gates` e `templates/gates` continuam sincronizados entre `aidd-enterprise` e `aidd-master`.
- **Veredito: Concluído.**

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 4: Dividir run_all_checks (G_SEGURANCA.py) em funcoes menores por camada de responsabilidade.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 4: Dividir run_all_checks (G_SEGURANCA.py) em funcoes menores por camada de responsabilidade.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
