# Item — gate-g-mutacao-mutmut-regras-exatas

> **Escopo:** Configurar o framework de testes de mutação mutmut nos 4 módulos de regras exatas (sizing, injector SHA-256, outbox e RLS) e criar o gate G_MUTACAO com baseline versionado.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- Regras determinísticas de negócio precisam de score de mutação formal para evitar testes fracos. Uso de ferramenta madura OSS cumpre regra #8.

## Definição de Pronto

1. Configurar mutmut para os 4 módulos de regras exatas.
2. Estabelecer score mínimo de 70%.
3. Criar gate gates/G_MUTACAO.py com baseline versionado.

## Critério de saída

- Score de mutação >= 70% nos 4 módulos e gate funcional.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: gate-g-mutacao-mutmut-regras-exatas.
Siga rigorosamente a Definição de Pronto acima:
1. Configurar mutmut para os 4 módulos de regras exatas.
2. Estabelecer score mínimo de 70%.
3. Criar gate gates/G_MUTACAO.py com baseline versionado.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: gate-g-mutacao-mutmut-regras-exatas.
Strictly follow the Definition of Done above:
1. Configurar mutmut para os 4 módulos de regras exatas.
2. Estabelecer score mínimo de 70%.
3. Criar gate gates/G_MUTACAO.py com baseline versionado.
Ensure exit code 0 across relevant tests and gates.
```
