# Item 9 — Corrigir terminacao de linha inconsistente CRLF-LF entre gemeas master-enterprise

> **Escopo:** Padronizar a terminação de linha (CRLF vs LF) entre os arquivos de master e enterprise, e configurar `.gitattributes` (ou equivalente) para impedir que a inconsistência volte a acontecer. Este item é puramente mecânico e não envolve decisão de arquitetura.
> **Status:** [EM EXECUCAO]

---

## Contexto ja investigado

Fonte: relatório de auditoria, achado #9.

- **23 arquivos CRLF no master** vs **20 no enterprise** — mesmo conjunto lógico de código, terminações diferentes.
- `scripts/aidd.py` é **CRLF no master e LF no enterprise** — o mesmo arquivo (achado #4/#8: 935 linhas comuns entre os dois via `difflib`) tem codificação de quebra de linha diferente.
- Impacto direto: isso **quebra diffs byte-a-byte** entre as duas ferramentas, gera diffs falsos em revisão de código (uma linha que não mudou aparece como alterada só por causa da quebra de linha) e atrapalha qualquer comparação futura entre as "gêmeas" — inclusive a comparação que este próprio plano depende para os Itens 1, 3 e 4.
- Comando de verificação usado no relatório (§1.3): `find tools -name "*.py" -not -path "*__pycache__*" -exec file {} \; | grep CRLF | wc -l` e `file tools/aidd-master/scripts/aidd.py tools/aidd-enterprise/scripts/aidd.py`.

## Definicao de Pronto

1. Terminação de linha padronizada (LF, convenção Unix já predominante no restante do repositório) em todos os arquivos de texto de master e enterprise, incluindo `scripts/aidd.py`.
2. `.gitattributes` (ou mecanismo equivalente já usado no monorepo) configurado para forçar LF em arquivos de texto e prevenir regressão futura.
3. Rodando novamente o comando de verificação do relatório (§1.3), o resultado mostra 0 arquivos CRLF remanescentes fora de exceções documentadas (ex.: arquivos `.bat`/`.ps1` que genuinamente precisam de CRLF no Windows, se existirem).
4. `git diff` entre um commit antes e depois desta mudança mostra apenas a alteração de terminação de linha, sem alteração de conteúdo real (a mudança deve ser "silenciosa" em termos de lógica).
5. Testes reais de master e enterprise continuam passando com exit 0 após a normalização (a terminação de linha não deve afetar comportamento de runtime, mas precisa ser confirmado).

## Criterio de saida

- Terminação de linha uniforme entre master e enterprise.
- Proteção configurada contra regressão (`.gitattributes` ou equivalente).
- Testes reais passando sem alteração de comportamento.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 9: padronizar a terminacao de linha (CRLF vs LF) entre master e
enterprise e configurar protecao contra regressao (ver
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, achado #9).

Fatos que voce precisa saber antes de comecar:
- 23 arquivos CRLF no master vs 20 no enterprise - mesmo conjunto logico de codigo.
- scripts/aidd.py: CRLF no master, LF no enterprise - o MESMO arquivo (935 linhas comuns via
  difflib) com codificacao de quebra de linha diferente.
- Isso quebra diffs byte-a-byte e gera diffs falsos em revisao de codigo.

Regras obrigatorias:
1. Este item e mecanico (normalizar terminacao de linha), sem decisao de arquitetura
   pendente - pode ser executado sem pausa para aprovacao adicional, DESDE QUE a mudanca
   fique restrita a terminacao de linha (nao aproveite para alterar logica de codigo no
   mesmo commit).
2. Confirme com git diff que a mudanca e "silenciosa" em termos de conteudo - so quebra de
   linha, nada de logica.
3. Siga rigorosamente a Definicao de Pronto acima.
4. Nao invente aprovacoes. So marque como concluido apos rodar o comando de verificacao do
   relatorio de novo e os testes reais.
5. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 9: standardize line-ending (CRLF vs LF) between master and
enterprise and configure protection against regression (see
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, finding #9).

Facts you need before starting:
- 23 CRLF files in master vs 20 in enterprise - same logical set of code.
- scripts/aidd.py: CRLF in master, LF in enterprise - the SAME file (935 common lines via
  difflib) with different line-ending encoding.
- This breaks byte-for-byte diffs and creates false diffs in code review.

Mandatory rules:
1. This item is mechanical (normalize line endings), with no pending architectural decision
   - it can be executed without pausing for additional approval, PROVIDED the change stays
   restricted to line endings (do not use the opportunity to also change code logic in the
   same commit).
2. Confirm with git diff that the change is "silent" in terms of content - only line
   endings, no logic.
3. Strictly follow the Definition of Done above.
4. Do not fabricate approvals. Only mark this done after re-running the report's
   verification command and the real tests.
5. Maintain monorepo governance rules (AGENTS.md).
```
