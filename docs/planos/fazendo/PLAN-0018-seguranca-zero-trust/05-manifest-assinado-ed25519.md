# Item — manifest-assinado-ed25519-componentes-enterprise

> **Escopo:** Implementar assinatura digital Ed25519 para manifestos de componentes no aidd-enterprise, conectando a verificação de assinatura ao carregador register_injected_tools.
> **Status:** [EM EXECUCAO]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. Nenhuma referencia a Ed25519 no codigo; o manifesto nao e assinado.

---

## Contexto já investigado

- Hashes SHA-256 vivem no mesmo arquivo que descreve os dados [SEC-8/9]. Um agente comprometido pode adulterar arquivos e reescrever o hash. MCP carrega ferramentas sem checar assinatura.

## Definição de Pronto

1. Gerar par de chaves Ed25519 com chave pública versionada no repositório.
2. Assinar o manifesto canônico no materializador.
3. Bloquear o carregamento em `register_injected_tools` caso a assinatura do arquivo não confira.

## Critério de saída

- Componentes adulterados não são carregados em tempo de execução.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: manifest-assinado-ed25519-componentes-enterprise.
Siga rigorosamente a Definição de Pronto acima:
1. Gerar par de chaves Ed25519 com chave pública versionada no repositório.
2. Assinar o manifesto canônico no materializador.
3. Bloquear o carregamento em `register_injected_tools` caso a assinatura do arquivo não confira.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: manifest-assinado-ed25519-componentes-enterprise.
Strictly follow the Definition of Done above:
1. Gerar par de chaves Ed25519 com chave pública versionada no repositório.
2. Assinar o manifesto canônico no materializador.
3. Bloquear o carregamento em `register_injected_tools` caso a assinatura do arquivo não confira.
Ensure exit code 0 across relevant tests and gates.
```
