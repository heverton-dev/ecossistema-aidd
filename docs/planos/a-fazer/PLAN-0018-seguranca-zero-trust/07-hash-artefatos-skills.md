# Item — hash-artefatos-skills-mcps-dependencias-externas

> **Escopo:** Adicionar verificação de hash SHA-256 para artefatos de skills e MCPs externos registrados em gates/dependencias_externas.json.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. dependencias_externas.json nao tem campo de sha256; dependencia verify nao confere checksum.

---

## Contexto já investigado

- dependencias_externas.json valida comandos de instalação mas não o checksum dos artefatos baixados [SEC-5/6], vulnerável a dependency confusion e supply chain attacks.

## Definição de Pronto

1. Registrar hashes SHA-256 esperados dos bundles e scripts instalados em `dependencias_externas.json`.
2. Atualizar `python ecossistema.py dependencia verify` para verificar o checksum dos arquivos instalados.
3. Bloquear bootstrap se houver divergência de hash.

## Critério de saída

- Integridade criptográfica de ferramentas externas verificada pelo CLI.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: hash-artefatos-skills-mcps-dependencias-externas.
Siga rigorosamente a Definição de Pronto acima:
1. Registrar hashes SHA-256 esperados dos bundles e scripts instalados em `dependencias_externas.json`.
2. Atualizar `python ecossistema.py dependencia verify` para verificar o checksum dos arquivos instalados.
3. Bloquear bootstrap se houver divergência de hash.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: hash-artefatos-skills-mcps-dependencias-externas.
Strictly follow the Definition of Done above:
1. Registrar hashes SHA-256 esperados dos bundles e scripts instalados em `dependencias_externas.json`.
2. Atualizar `python ecossistema.py dependencia verify` para verificar o checksum dos arquivos instalados.
3. Bloquear bootstrap se houver divergência de hash.
Ensure exit code 0 across relevant tests and gates.
```
