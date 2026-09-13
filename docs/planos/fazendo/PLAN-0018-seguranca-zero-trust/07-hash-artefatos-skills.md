# Item — hash-artefatos-skills-mcps-dependencias-externas

> **Escopo:** Adicionar verificação de hash SHA-256 para artefatos de skills e MCPs externos registrados em gates/dependencias_externas.json.
> **Status:** [FEITO]
> **Auditoria por reproducao real (12-09-2026):** FEITO (com limite tecnico registrado, ver detalhe abaixo). `dependencias_externas.json` agora guarda `sha256` esperado para as 2 skills cujo `verificar` aponta pra um arquivo unico (`impeccable`, `code-review-graph`) — hashes reais computados dos artefatos instalados nesta maquina. `dependencia verify`/`dependencia bootstrap` recalculam o SHA-256 real e bloqueiam (`exit 1`) em divergencia, tanto pra skill ja instalada quanto logo apos instalar; corrigido tambem um bug onde `dependencia bootstrap` retornava `exit 0` mesmo com `[FALHA]` na tela. `scripts/test_gestor_dependencias.py`: 21/21 testes passando (12 novos). Reproducao real do ataque nesta sessao: adulterei o `SKILL.md` real da `impeccable`, confirmei bloqueio real (`exit 1`) em `verify` e `bootstrap`, restaurei e confirmei `exit 0`. Suite completa do repo: 133/133 passando; `python ecossistema.py audit`: gates deterministicos aprovados. Limite honesto e documentado (nao fabricado): a skill `sandeco-token-reduce` (verificada por diretorio `.venv`, nao arquivo — hash de pasta nao e reprodutivel entre maquinas) e os 5 MCPs (npx/docker, sem artefato local sob controle deste repo) ficam de fora do hash de arquivo unico, com a razao tecnica registrada em `sha256_nota`/`descricao` do manifesto e em `00-PROCESSO-E-DECISOES.md` §9-10. Ver `00-PROCESSO-E-DECISOES.md` para o registro completo.

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
