# Item 1 — Gates rodarem pytest de verdade (nao so estrutura)

> **Escopo:** Entra: criar um gate (ou passo do CLI) que roda `pytest -q --tb=no` de verdade em cada `tools/<ferramenta>` dentro de `python ecossistema.py audit`, falhando (exit 1) se qualquer suíte tiver failed>0. Não entra: corrigir os testes que hoje falham (isso é responsabilidade dos itens 8, 10 e 11) nem reescrever os gates existentes.
> **Status:** [CONCLUÍDO — Aprovado por Humano em 2026-09-07]
> **Modelo sugerido:** Claude Haiku · Antigravity Gemini 3.1 pro · MiMo mimo-v2.5 (tarefa mecânica: `subprocess.run(pytest)` + parse de exit code, sem decisão de arquitetura)

---

## Contexto ja investigado

- Os 8 gates em `gates/*.py` auditam estrutura, sintaxe/AST, drift de núcleo compartilhado, segredos, consistência de CLI help, agnosticismo de componente e zero-headless — nenhum deles invoca `pytest`.
- `python ecossistema.py audit` foi rodado em 2026-09-07 e retornou 100% verde (8/8 gates PASS) no mesmo commit/working-tree em que a suíte real tinha 2 falhas em aidd-master, 2 em aidd-enterprise e 8 em aidd-ops (ver `docs/relatorios/relatorio-auditoria-ecossistema-aidd-sem-maquiagem.html`, seção "Testes: o que o repositório alega vs. o que roda agora").
- `PLANO-EXECUCAO-ESTRUTURADO.json` (raiz) é o único lugar que registra números de teste, e é estático (ver item 2) — hoje nada liga a saúde real dos testes ao veredito do `audit`.

## Definicao de Pronto

1. Existe um gate novo (ex.: `gates/G_TESTES_REAIS.py`) que roda `python -m pytest -q --tb=no` dentro de cada `tools/<ferramenta>` e falha se `failed > 0` em qualquer uma.
2. Reproduzir com falha induzida: introduzir temporariamente um `assert False` em qualquer teste de uma das 5 ferramentas, rodar `python ecossistema.py audit` e confirmar que agora retorna exit 1 apontando a ferramenta certa — depois reverter a falha induzida.
3. Com todas as suítes genuinamente verdes, `python ecossistema.py audit` retorna exit 0.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 1: Gates rodarem pytest de verdade (nao so estrutura).
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 1: Gates rodarem pytest de verdade (nao so estrutura).
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
