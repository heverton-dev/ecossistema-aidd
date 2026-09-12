# Item — escritor-atomico-compartilhado-e-migracao-fs

> **Escopo:** Criar utilitário compartilhado escritor_atomico (staging -> os.replace -> fsync) e migrar os 8 pontos críticos de gravação de filesystem para eliminar risco de arquivos truncados.
> **Status:** [EM EXECUCAO]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. componentes/compartilhado/src-core/escritor_atomico.py nao existe.

---

## Contexto já investigado

- materializador.py, scaffold_infra.py, add_module.py e as fases do generator usam open(destino, 'w') direto no destino final [FS-2/3/4, PIPE-2]. Kill durante a escrita corrompe o arquivo sem rollback.

## Definição de Pronto

1. Criar `componentes/compartilhado/src-core/escritor_atomico.py` com escrita em tmp e atomic rename via os.replace.
2. Migrar gravações de materializador, scaffold_infra, compose_suite, fases 1-8 e _gravar_plano.
3. Criar gate AST verificando ausência de open(w) direto nos pontos críticos.

## Critério de saída

- Zero gravações diretas sem staging nos pontos críticos. Teste de injeção de falha no meio da escrita mantém arquivo anterior intacto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: escritor-atomico-compartilhado-e-migracao-fs.
Siga rigorosamente a Definição de Pronto acima:
1. Criar `componentes/compartilhado/src-core/escritor_atomico.py` com escrita em tmp e atomic rename via os.replace.
2. Migrar gravações de materializador, scaffold_infra, compose_suite, fases 1-8 e _gravar_plano.
3. Criar gate AST verificando ausência de open(w) direto nos pontos críticos.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: escritor-atomico-compartilhado-e-migracao-fs.
Strictly follow the Definition of Done above:
1. Criar `componentes/compartilhado/src-core/escritor_atomico.py` com escrita em tmp e atomic rename via os.replace.
2. Migrar gravações de materializador, scaffold_infra, compose_suite, fases 1-8 e _gravar_plano.
3. Criar gate AST verificando ausência de open(w) direto nos pontos críticos.
Ensure exit code 0 across relevant tests and gates.
```
