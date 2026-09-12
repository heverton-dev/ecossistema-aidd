# Item 2 — Extrair e proteger templates duplicados (core vs v2 e entre ferramentas)

> **Escopo:** Resolver a duplicação sem nenhuma proteção entre `templates/core` e `templates/v2` dentro de cada ferramenta (master e enterprise), e entre `templates/core` das duas ferramentas. Definir uma fonte única (ou gate de drift novo, se a extração completa não for viável agora) para essas 3 relações. Não entra: `src/core` (Item 1) nem `scripts/gates`/`templates/gates` (Item 3).
> **Status:** [EM EXECUCAO]

---

## Contexto ja investigado

Fonte: relatório de auditoria, achado #2 e tabela §8.1 (medido por hash MD5, não estimado).

- `master/templates/core` ≡ `master/templates/v2`: **28 arquivos idênticos, 8.087 linhas**.
- `enterprise/templates/core` ≡ `enterprise/templates/v2`: **29 arquivos idênticos, 8.130 linhas**.
- `templates/core` do master ≡ `templates/core` do enterprise: **29 arquivos idênticos, 8.126 linhas**.
- **Nenhum gate monitora esses 3 pares hoje** — diferente de `src/core`, que ao menos tem `G_DRIFT_NUCLEO_COMPARTILHADO` detectando (Item 1). Aqui, uma divergência futura entre `core` e `v2`, ou entre as duas ferramentas, seria **silenciosa** — ninguém saberia até um bug aparecer em produção do usuário final.
- Contexto adicional: `src/core` ↔ `templates/core` (mesma ferramenta) também tem 14 arquivos idênticos somando 2.424 linhas (achado da tabela §8.1) — indício de que o problema de fundo é mais amplo que só "templates vs templates".
- O caso `get_studio_html` (achado do Item 16 do plano 01, XSS corrigido em 6 cópias) atravessa exatamente esses diretórios de template — é a prova concreta de que a falta de proteção aqui já causou retrabalho manual real.

## Decisao Registrada (verificada tecnicamente e confirmada com o usuario em 2026-09-09)

- **Verificacao feita:** `templates_dir = templates_core if os.path.isdir(templates_core) else templates/v2`
  em `provision_project.py:44-45` (master) — `templates/core` sempre existe no repo, entao
  `templates/v2` nunca e alcancado por esse fallback. Hash MD5 confirma que todo arquivo
  presente nos dois e byte-identico, e `templates/core` tem arquivos extras que `v2` nao tem
  (`deploy.sh`, `logs.py`, `nginx/`, `shared/`). Nenhum outro ponto do codigo (grep por flag
  ou selecao deliberada de "v2") escolhe `templates/v2` de proposito.
- **Decisao:** `templates/v2` e legado morto. Remover `templates/v2` de master e enterprise,
  remover o fallback no codigo que referencia esse caminho, manter `templates/core` como
  unica pasta.
- **Duplicacao remanescente** (`templates/core` entre master e enterprise) resolve dentro do
  "almoxarifado compartilhado" decidido no Item 1 — nao precisa de solucao separada aqui.

## Definicao de Pronto

1. Decisão registrada (humana) sobre a estratégia: eliminar `templates/v2` como cópia de `templates/core` (se for legado morto), OU implementar sincronização mecânica determinística entre os 3 pares, OU no mínimo adicionar gate de drift cobrindo os 3 pares enquanto a extração completa não acontece.
2. Se a decisão for eliminar `v2`: confirmar via grep/uso real que nenhum fluxo do produto gerado depende especificamente de `templates/v2` antes de remover.
3. Gate de drift (novo ou estendido de `G_DRIFT_NUCLEO_COMPARTILHADO`) cobrindo os 3 pares documentados, rodando nos Quality Gates.
4. Rodando de novo o hash MD5 dos 3 pares (comando §1.3 do relatório, adaptado para os diretórios de template), o resultado bate com o que o gate está monitorando — sem arquivo "invisível" ao gate.
5. Testes reais das ferramentas (inclusive os que geram projeto a partir do template) passam com exit 0.

## Criterio de saida

- Duplicação eliminada ou protegida por gate de drift ativo nos 3 pares.
- Nenhuma divergência entre `core`/`v2` ou entre ferramentas passa despercebida por falta de monitoramento.
- Testes reais passando.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 2: resolver a duplicacao sem protecao entre templates/core e
templates/v2 (dentro de master e de enterprise) e entre templates/core das duas ferramentas
(ver docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, achado #2 e
tabela da secao 8.1, para evidencia completa).

Fatos que voce precisa saber antes de comecar:
- master: templates/core === templates/v2 (28 arquivos, 8.087 linhas).
- enterprise: templates/core === templates/v2 (29 arquivos, 8.130 linhas).
- templates/core do master === templates/core do enterprise (29 arquivos, 8.126 linhas).
- Nenhum gate monitora esses 3 pares hoje - diferenca aqui e silenciosa.
- O XSS do Item 16 do plano 01 (get_studio_html) atravessava exatamente esses diretorios e
  foi corrigido manualmente em 6 copias - prova do custo real de nao ter protecao aqui.

Regras obrigatorias:
1. JA FOI VERIFICADO E DECIDIDO (ver secao "Decisao Registrada" acima): templates/v2 e
   legado morto, confirmado por leitura do fallback em provision_project.py e por hash MD5.
   Remova templates/v2 de master e enterprise e o fallback de codigo que aponta pra ele.
   Antes de remover, rode voce mesmo o grep/hash de novo para confirmar que nada mudou desde
   a verificacao original.
2. Siga rigorosamente a Definicao de Pronto acima.
3. Nao invente aprovacoes. So marque como concluido apos rodar de novo o hash MD5 e confirmar
   que o gate de drift cobre os 3 pares.
4. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 2: resolve the unprotected duplication between
templates/core and templates/v2 (within master and within enterprise) and between
templates/core of the two tools (see docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html,
finding #2 and the table in section 8.1, for full evidence).

Facts you need before starting:
- master: templates/core === templates/v2 (28 files, 8,087 lines).
- enterprise: templates/core === templates/v2 (29 files, 8,130 lines).
- master's templates/core === enterprise's templates/core (29 files, 8,126 lines).
- No gate monitors these 3 pairs today - drift here is silent.
- The XSS from Item 16 of plan 01 (get_studio_html) crossed exactly these directories and
  was manually fixed in 6 copies - proof of the real cost of having no protection here.

Mandatory rules:
1. This has ALREADY BEEN VERIFIED AND DECIDED (see "Decisao Registrada" section above):
   templates/v2 is dead legacy, confirmed by reading the fallback in provision_project.py
   and by MD5 hash. Remove templates/v2 from master and enterprise, and the code fallback
   pointing to it. Before removing, re-run the grep/hash yourself to confirm nothing changed
   since the original verification.
2. Strictly follow the Definition of Done above.
3. Do not fabricate approvals. Only mark this done after re-running the MD5 hash and
   confirming the drift gate covers all 3 pairs.
4. Maintain monorepo governance rules (AGENTS.md).
```
