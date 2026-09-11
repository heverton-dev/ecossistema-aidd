# Item — testes-conteudo-sha256-injector-enterprise

> **Escopo:** Substituir asserções de contagem no injector do aidd-enterprise por verificação de conteúdo real dos hashes SHA-256 gerados, matando mutantes de algoritmo e de entrada trocada.
> **Status:** [CONCLUIDO — verificado por reproducao real]
> **Auditoria por reproducao real (11-09-2026):** FEITO. pytest tests/unit/test_aidd_core_injector.py -k 'sha256 or manifesto' em tools/aidd-enterprise/, exit 0. Existem os 3 testes exigidos: hash bate o conteudo real, adulteracao de 1 byte quebra a verificacao, e hash fora de sha256 e recusado.

---

## Contexto já investigado

- test_aidd_core_injector.py afirma apenas contagem de hashes [TS-2]. Mutante sha256->sha1 sobrevive.

## Definição de Pronto

1. Computar localmente hashlib.sha256 do conteúdo real de cada arquivo injetado.
2. Afirmar igualdade estrita com o manifesto.
3. Testar caso de adulteração de 1 byte.

## Critério de saída

- Teste afirma hashes exatos de conteúdos conhecidos e mutantes morrem.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: testes-conteudo-sha256-injector-enterprise.
Siga rigorosamente a Definição de Pronto acima:
1. Computar localmente hashlib.sha256 do conteúdo real de cada arquivo injetado.
2. Afirmar igualdade estrita com o manifesto.
3. Testar caso de adulteração de 1 byte.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: testes-conteudo-sha256-injector-enterprise.
Strictly follow the Definition of Done above:
1. Computar localmente hashlib.sha256 do conteúdo real de cada arquivo injetado.
2. Afirmar igualdade estrita com o manifesto.
3. Testar caso de adulteração de 1 byte.
Ensure exit code 0 across relevant tests and gates.
```
