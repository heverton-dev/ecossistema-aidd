# Item — self-healing-imports-python-ecossistema

> **Escopo:** Implementar guarda de auto-recuperação (self-healing) no topo de ecossistema.py antes dos imports de click e dotenv, verificando versão mínima do Python (>=3.10) e oferecendo instalação automática de requirements.txt.
> **Status:** [EM EXECUCAO]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. ecossistema.py nao checa sys.version_info e nao protege os imports de click/dotenv com try/except.

---

## Contexto já investigado

- ecossistema.py importa click e dotenv incondicionalmente no topo [BP-1]. Em máquina virgem sem requirements.txt instalado, crasha com ModuleNotFoundError cru sem orientação.

## Definição de Pronto

1. Adicionar checagem de sys.version_info >= (3, 10) no início do arquivo.
2. Proteger imports de click e dotenv com bloco try/except.
3. Em caso de ausência, exibir banner amigável orientando rodar `python -m pip install -r requirements.txt`.
4. Se executado com `--auto-bootstrap`, disparar a instalação de pip automaticamente.

## Critério de saída

- Execução em Python virgem exibe banner educativo e instrução de correção em vez de traceback cru.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: self-healing-imports-python-ecossistema.
Siga rigorosamente a Definição de Pronto acima:
1. Adicionar checagem de sys.version_info >= (3, 10) no início do arquivo.
2. Proteger imports de click e dotenv com bloco try/except.
3. Em caso de ausência, exibir banner amigável orientando rodar `python -m pip install -r requirements.txt`.
4. Se executado com `--auto-bootstrap`, disparar a instalação de pip automaticamente.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: self-healing-imports-python-ecossistema.
Strictly follow the Definition of Done above:
1. Adicionar checagem de sys.version_info >= (3, 10) no início do arquivo.
2. Proteger imports de click e dotenv com bloco try/except.
3. Em caso de ausência, exibir banner amigável orientando rodar `python -m pip install -r requirements.txt`.
4. Se executado com `--auto-bootstrap`, disparar a instalação de pip automaticamente.
Ensure exit code 0 across relevant tests and gates.
```
