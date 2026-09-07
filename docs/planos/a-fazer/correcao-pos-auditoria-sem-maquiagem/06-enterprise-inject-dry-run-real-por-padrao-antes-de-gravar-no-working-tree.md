# Item 6 — enterprise inject: dry-run real por padrao antes de gravar no working tree

> **Escopo:** Entra: mudar o comportamento padrão do comando `inject` de `tools/aidd-enterprise/scripts/aidd.py` para não gravar no working tree sem confirmação explícita. Não entra: mudar a lógica de materialização/hash SHA-256 em si (isso segue igual).
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]
> **Modelo sugerido:** Claude Sonnet · Antigravity Gemini 3.7 · MiMo mimo-v2.5-pro (mudança de contrato de CLI com dois caminhos a testar)

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
Voce vai implementar o Item 6: enterprise inject: dry-run real por padrao antes de gravar no working tree.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 6: enterprise inject: dry-run real por padrao antes de gravar no working tree.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
