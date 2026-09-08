# Item 1 — Trocar except Exception generico por excecoes especificas nas 5 ferramentas

> **Escopo:** Entra: analisar, ferramenta por ferramenta, os pontos onde `except Exception` (genérico demais) é usado para capturar um erro que na prática só pode ser de um tipo específico (ex.: `json.JSONDecodeError`, `FileNotFoundError`, `subprocess.CalledProcessError`), e trocar pelo tipo real — caso a caso, não substituição mecânica em massa. Não entra: resolver as ~288 ocorrências (197 enterprise + 196 master + 65 generator + 19 ops + 7 forge) numa única execução — o volume é grande demais pra uma passada só seguir com segurança; este item define a priorização e cobre a primeira fatia (arquivos de segurança/gates), deixando o resto registrado para fatias seguintes. Não entra mudar o comportamento observável em caso de erro (a exceção específica deve continuar sendo tratada do mesmo jeito, só deixando de mascarar erros que não eram esse).

> **Status:** ⏳ Rascunho gerado, aguardando aprovação

---

## Contexto já investigado

- Contagem real (`grep` por `^\s*except\s+Exception\b`, 2026-09-08, excluindo pastas de exemplo/gerado e skills materializadas): aidd-enterprise = 198, aidd-master = 196, aidd-generator = 65, aidd-ops = 19, aidd-forge = 7.
- Risco de fazer isso errado: capturar `Exception` genérico às vezes é intencional (ex.: um laço que não pode parar por um item ruim, ou um ponto de entrada de CLI que precisa sempre retornar um código de saída). Trocar sem entender o que o bloco `try` realmente faz por dentro pode fazer o programa quebrar em vez de logar e continuar — por isso este item não é mecânico, precisa de leitura caso a caso.
- Priorização sugerida (não é decisão fabricada, é proposta pro humano aprovar): começar pelos arquivos que o próprio grafo marca como `security_relevant=1` em `risk_index` (ex.: `core/security.py`, `core/mcp_server.py`, os arquivos `G_*.py` de gates) — são os que mais importam se um erro real for mascarado.

## Definição de Pronto

1. Inventário produzido (arquivo + linha + o que o `try` faz) para os arquivos de maior prioridade (gates de segurança e `core/security.py`/`core/mcp_server.py` nas 5 ferramentas) antes de qualquer troca.
2. Para cada ocorrência trocada, o tipo de exceção substituído é o que realmente pode ocorrer ali (verificado lendo o código dentro do `try`, não suposição).
3. Comportamento observável (mensagem de log, código de saída, resultado do gate) idêntico ao anterior para os casos de erro que o tipo específico ainda cobre — reproduzido rodando o gate/teste antes e depois.
4. Ocorrências não cobertas nesta primeira fatia listadas explicitamente neste documento como pendência, não escondidas.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 1: Trocar except Exception generico por excecoes especificas nas 5 ferramentas.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 1: Trocar except Exception generico por excecoes especificas nas 5 ferramentas.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
