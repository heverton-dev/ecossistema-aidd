# Item 5 — Dry-run padrao aidd inject

> **Escopo:** Entra: mudar o comportamento padrão do comando `inject` de `tools/aidd-enterprise/scripts/aidd.py` para não gravar no working tree sem confirmação explícita. Não entra: mudar a lógica de materialização/hash SHA-256 em si (isso segue igual).
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** NAO AUDITADO — evidencia: (nota pendente de medicao real - nao preencher com estimativa)
> **Nota Alvo (0-10):** NAO AUDITADO
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- Confirmado por fork de auditoria: hoje `enterprise inject <tipo> <nome>` grava direto no repositório do usuário sem `--dry-run` explícito e sem confirmação — comportamento difícil de reverter, silencioso.
- Isso contraria a orientação geral de "Executando ações com cuidado" (ações difíceis de reverter merecem confirmação por padrão).

## Definicao de Pronto

1. Rodar `enterprise inject <tipo> <nome>` sem nenhuma flag adicional NÃO grava arquivo nenhum — mostra o diff/preview do que seria escrito e pede confirmação, ou recusa com mensagem clara exigindo uma flag explícita (`--aplicar`/`--yes`).
2. Existe um modo não interativo explícito e documentado para CI/scripts (`--yes`/`--sim`) que aplica sem prompt, para não quebrar automação legítima.
3. Testes de integração cobrindo os dois caminhos (confirmado vs recusado/sem flag) passam — reproduzir manualmente uma vez cada um.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 5: Dry-run padrao aidd inject.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 5: Dry-run padrao aidd inject.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
