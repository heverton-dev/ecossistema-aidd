# Item — bootstrapper-assistido-multi-os-fix

> **Escopo:** Implementar a funcionalidade `--fix` no preflight-host com detecção automática do gerenciador de pacotes do SO (winget/choco no Windows, brew no macOS, apt/dnf no Linux) e fallback em espaço de usuário.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. Nao ha deteccao de gerenciador de pacotes do host (winget/choco/brew/apt/dnf).

---

## Contexto já investigado

- O ecossistema não auxiliava na instalação de ferramentas de sistema faltantes, exigindo pesquisa manual de comandos pelo usuário.

## Definição de Pronto

1. Detectar package manager ativo no host (winget > choco no Win, brew no Mac, apt > dnf no Linux).
2. Montar comandos oficiais de instalação e solicitar confirmação explícita do usuário.
3. Suportar fallback user-space (`~/.aidd/bin`) para ferramentas portáteis (Node standalone, Hadolint) sem exigir privilégios de administrador.
4. Adicionar flag `--dry-run` para exibição dos comandos sem execução.

## Critério de saída

- Modo `--fix` orienta ou instala ferramentas faltantes com consentimento do usuário.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: bootstrapper-assistido-multi-os-fix.
Siga rigorosamente a Definição de Pronto acima:
1. Detectar package manager ativo no host (winget > choco no Win, brew no Mac, apt > dnf no Linux).
2. Montar comandos oficiais de instalação e solicitar confirmação explícita do usuário.
3. Suportar fallback user-space (`~/.aidd/bin`) para ferramentas portáteis (Node standalone, Hadolint) sem exigir privilégios de administrador.
4. Adicionar flag `--dry-run` para exibição dos comandos sem execução.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: bootstrapper-assistido-multi-os-fix.
Strictly follow the Definition of Done above:
1. Detectar package manager ativo no host (winget > choco no Win, brew no Mac, apt > dnf no Linux).
2. Montar comandos oficiais de instalação e solicitar confirmação explícita do usuário.
3. Suportar fallback user-space (`~/.aidd/bin`) para ferramentas portáteis (Node standalone, Hadolint) sem exigir privilégios de administrador.
4. Adicionar flag `--dry-run` para exibição dos comandos sem execução.
Ensure exit code 0 across relevant tests and gates.
```
