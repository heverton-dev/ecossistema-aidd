# PROCESSO E DECISÕES — Refinamento das Notas Pós-Evolução

> **Origem:** `docs/planos/evolucao-notas-auditoria/` (rodada 1, concluída em 05/09/2026, composto final 7,5→8,7/10). O usuário pediu para ir além, aplicando 4 perguntas de rigor a cada avanço possível: **é necessário? é possível? é real (não ilusório)? traz ganho real (não é vaidade)?**
> **Status desta rodada:** iniciada em 05/09/2026, logo após o fechamento da rodada 1.
> **Propósito deste arquivo:** igual ao da rodada 1 — registro único do *processo*, não do conteúdo técnico de cada item (isso vive em documento próprio por item, ver §3).

---

## 1. A decisão

Mesmo ciclo fechado e independente da rodada 1, aplicado a cada item que sobrevive às 4 perguntas de rigor do usuário:

```
análise profunda → aplicar as 4 perguntas → Definição de Pronto travada →
plano exaustivo → prompt de execução → auditoria por reprodução real →
validação → registro → PRÓXIMO ITEM
```

Nenhum item começa a ser implementado sem que eu escreva e o usuário aprove uma Definição de Pronto concreta e checável primeiro — regra idêntica à da rodada 1, sem exceção.

---

## 2. As 4 perguntas de rigor (critério de entrada de qualquer item nesta pasta)

Antes de qualquer item entrar nesta pasta como pacote real, ele precisa passar nas 4 perguntas que o usuário definiu:

1. **É necessário?** — Existe um risco ou lacuna real hoje, não uma preferência estética.
2. **É possível?** — Existe um caminho concreto, sem exigir acesso que não temos (ex.: código-fonte de um harness externo) nem reescrever o propósito da própria ferramenta.
3. **É real, não ilusório?** — A evidência final tem que vir de reprodução de verdade (comando rodado, exit code real, teste que falha antes e passa depois) — nunca de uma frase que soa bem mas não foi verificada.
4. **Traz ganho real, ou é mera perseguição do número?** — Se a resposta for só "sobe a nota", o item não entra. Tem que reduzir um risco real (bug futuro, confusão do usuário, dívida técnica) para valer o esforço.

Dois itens da rodada 1 foram explicitamente **reprovados** nestas 4 perguntas e ficam de fora desta pasta, com a razão registrada:

- **Economia de Tokens (hoje 8/10):** o número de tokens no Modo Delegado é estruturalmente não-verificável (não temos acesso à conta/billing de quem responde). Empurrar a nota além de 8 exigiria fingir uma medição que não existe.
- **Determinismo Primeiro (hoje 9,5/10):** as fases 2, 3 e 8 do `aidd-generator` são LLM por natureza — são o próprio propósito da ferramenta (gerar código a partir de linguagem natural). Remover o LLM ali não seria "mais determinismo", seria descaracterizar o produto.

Estes dois ficam registrados como **teto honesto reafirmado**, não revisitados nesta rodada a menos que a condição estrutural mude (ex.: um provedor passar a expor medição de tokens auditável de fora, ou a ferramenta mudar de propósito).

---

## 3. Onde vive o conteúdo técnico de cada item

Cada item, quando sua vez chegar, ganha o próprio documento nesta mesma pasta:

- `01-cobertura-comandos-forge-generator.md` — Testabilidade: `aidd-forge` e `aidd-generator` nunca passaram pelo mesmo escrutínio comando-a-comando que `aidd-master`/`aidd-enterprise` já passaram nos Pacotes 2 e 4 da rodada 1.
- `02-prova-adversarial-gates-originais.md` — Gates Mecânicos: os gates pré-existentes (`G_ECOSSISTEMA_INTEGRIDADE`, `G_SEGREDOS`) nunca tiveram um teste que prove que eles genuinamente reprovam quando deveriam — só os gates novos desta sessão têm essa prova.
- `03-transparencia-disclosure-plan-prompt.md` — Transparência: `cmd_plan`/`cmd_prompt` (`aidd-master`, `aidd-enterprise`) não avisam no `--help` nem no output que usam casamento de palavras-chave, não LLM.
- `04-unificacao-injetor-aidd-enterprise.md` — Modularização + Distribuição de Componentes: `aidd-enterprise` continua com o injetor monolítico antigo (`aidd_core_injector.py`), nunca migrado para a arquitetura canônica que `aidd-master` já usa desde a rodada 1.
- `05-investigacao-mecanismo-agy.md` — Universalidade: mecanismo real de descoberta de skills do `agy` (Antigravity) continua desconhecido — único harness testado na rodada 1 sem explicação.

Cada um segue a mesma estrutura interna da rodada 1: Definição de Pronto → Diagnóstico específico (com as 4 perguntas respondidas explicitamente) → Prompt de execução PT-BR/EN-US → Veredito da auditoria → Nota final.

---

## 4. Ordem de execução proposta

Por certeza de resultado (do mais garantido ao mais incerto), não por número:

1. **Cobertura de comandos (`aidd-forge`/`aidd-generator`)** — mesmo trabalho mecânico já feito 2x, resultado garantido.
2. **Transparência (disclosure `plan`/`prompt`)** — menor item, resultado trivial e garantido.
3. **Prova adversarial dos gates originais** — mecânico, resultado garantido.
4. **Unificação do injetor `aidd-enterprise`** — maior escopo, resultado garantido mas mais trabalho.
5. **Investigação do mecanismo do `agy`** — único item de resultado incerto (pode não ter solução sem acesso ao código deles); fica por último de propósito, e uma resposta negativa honesta ("mecanismo não identificado, documentado como tal") é um resultado válido, não uma falha do pacote.

---

## 5. Registro de progresso

| # | Item | Dimensão afetada | Status | Documento |
|---|---|---|---|---|
| 1 | Cobertura de comandos — aidd-forge/aidd-generator | Testabilidade (9→10) | ✅ CONCLUÍDO em 05/09/2026 — nota do item 10/10, dimensão Testabilidade sobe para 10/10. Auditado por reprodução independente dos 5 casos (770 testes passando, zero regressão, zero chamada real de LLM confirmada empiricamente, escopo 100% respeitado) | `01-cobertura-comandos-forge-generator.md` |
| 2 | Disclosure plan/prompt | Transparência (8,5→9) | ✅ CONCLUÍDO em 05/09/2026 — nota do item 10/10, dimensão Transparência sobe para 9/10. Auditado por reprodução independente via subprocess real (10 combinações + 2 cenários extras próprios), byte-identidade confirmada entre as 2 ferramentas, zero regressão | `03-transparencia-disclosure-plan-prompt.md` |
| 3 | Prova adversarial dos gates originais | Gates Mecânicos (8→9) | ✅ CONCLUÍDO em 05/09/2026 — nota do item 10/10, dimensão Gates Mecânicos sobe para 9/10. Auditado por reprodução independente com cenários próprios diferentes dos do executor (17 testes passando, zero regressão, zero arquivo órfão) | `02-prova-adversarial-gates-originais.md` |
| 4 | Unificação do injetor aidd-enterprise | Modularização (9→10?) + Distribuição (9→10?) | ⏳ Não iniciado | `04-unificacao-injetor-aidd-enterprise.md` |
| 5 | Investigação do mecanismo do agy | Universalidade (9→10?) | ⏳ Não iniciado | `05-investigacao-mecanismo-agy.md` |

Esta tabela é atualizada ao final de cada item — nunca antes da validação real daquele item.

**Não prometido nesta rodada:** nenhuma nota é declarada "10/10" antes da auditoria real confirmar. Os pontos de interrogação na coluna de dimensão são propositais.

---

## 6. O que nunca muda neste processo

- Nenhuma nota sobe sem o comando de validação correspondente ter sido rodado de verdade nesta sessão.
- Nenhum item é declarado concluído por "parecer suficiente" — só pela Definição de Pronto escrita e aprovada antes de começar.
- Onde a resposta às 4 perguntas for "não" (Economia de Tokens, Determinismo Primeiro), a honestidade sobre o teto é o próprio critério de sucesso — não um obstáculo a esconder nem a forçar.
