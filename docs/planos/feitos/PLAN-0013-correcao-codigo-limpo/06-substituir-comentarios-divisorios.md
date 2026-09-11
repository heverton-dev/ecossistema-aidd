# Item 6 — Substituir comentarios-divisorios de secao por decomposicao real em funcao onde o mesmo padrao se repete

> **Escopo:** Entra: confirmar que, depois do item 4 (divisão de `run_all_checks` em métodos), os comentários `# ---... CAMADA N ...---` deixam de existir como "parede divisória" e viram no máximo um comentário curto de uma linha no início de cada método extraído (se ainda fizer sentido); rodar um novo censo (grep) no repositório inteiro pra confirmar que nenhum outro arquivo, fora da família `G_SEGURANCA.py`, repete esse mesmo padrão. Não entra: mexer em qualquer arquivo fora da família `G_SEGURANCA.py` — o censo já feito não achou nenhum outro caso; depende do item 4 ser executado primeiro — este item vira, na prática, uma checagem de consequência dele, não um trabalho novo separado.

> **Status:** ⏳ Rascunho gerado, aguardando aprovação

---

## Contexto já investigado

- Censo real feito em 2026-09-08 (`grep` recursivo pelo padrão `# CAMADA N` / `# LAYER N` em todos os `.py` das 5 ferramentas, excluindo pastas de exemplo/gerado): o padrão só existe nas 4 cópias de `G_SEGURANCA.py` (`scripts/gates` e `templates/gates`, em `aidd-enterprise` e `aidd-master`). Nenhum outro arquivo do ecossistema usa esse estilo de comentário-divisor.
- Esse achado é, na prática, o mesmo arquivo dos itens 4 e 5 — a diferença é a regra do livro Clean Code que está sendo aplicada aqui (comentário não deve substituir estrutura de função). Depende do item 4 ser aprovado/executado primeiro.

## Definição de Pronto

1. Depois do item 4 executado, nenhuma ocorrência de `# CAMADA N` (ou similar) sobrevive como divisor dentro de `run_all_checks` — cada camada agora é um método nomeado.
2. Novo censo (`grep`) rodado após a mudança, confirmando que não sobrou o padrão em nenhum dos 4 arquivos.
3. Se o censo achar o padrão em outro lugar não mapeado aqui, registrar como novo achado — não corrigir por conta própria sem antes atualizar este documento.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Execução (2026-09-08)

- Consequência direta do item 4: cada camada virou método nomeado, os comentários `# CAMADA N` como parede divisória deixaram de existir.
- Novo censo (`grep`) rodado após a mudança: zero ocorrências do padrão em qualquer lugar do ecossistema (mesma varredura de antes, resultado vazio).
- **Veredito: Concluído.**

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 6: Substituir comentarios-divisorios de secao por decomposicao real em funcao onde o mesmo padrao se repete.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 6: Substituir comentarios-divisorios de secao por decomposicao real em funcao onde o mesmo padrao se repete.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
