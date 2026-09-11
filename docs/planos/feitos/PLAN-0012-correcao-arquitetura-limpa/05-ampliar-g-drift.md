# Item 5 — Ampliar G_DRIFT_NUCLEO_COMPARTILHADO para comparar scripts/gates vs templates/gates dentro da mesma ferramenta

> **Escopo:** Entra: registrar no baseline (`gates/baseline_nucleo_compartilhado.json`) um novo par **intra-ferramenta** — `scripts/gates/` (versão viva que protege este monorepo) comparada com `templates/gates/` (versão entregue a projetos novos), dentro de `aidd-enterprise` e dentro de `aidd-master`, separadamente — para que `G_DRIFT_NUCLEO_COMPARTILHADO.py` passe a monitorar essa divergência. Não entra: unificar fisicamente as duas cópias numa fonte só (violaria a Regra Fixa #5 do `00-PROCESSO-E-DECISOES.md` — sem acoplamento de runtime entre ferramentas); não entra comparar `templates/core` vs `templates/v2` (já decidido fora de escopo no item 2); não entra decidir se a camada 8 (CVE audit) deve ser portada para o template — isso é decisão de produto, não deste item.

> **Status:** ✅ Concluído (auditado por reprodução real em 2026-09-08 — `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` executado de fato, aprovado)

---

## Contexto já investigado

- `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` hoje usa uma lista `PARES` (ver `PARES = [...]` no próprio script) que compara, para cada subpasta relativa X (`src/core`, `scripts`, `scripts/gates`, `templates/core`, `templates/v2`), `tools/aidd-master/X` vs `tools/aidd-enterprise/X` — sempre a **mesma subpasta relativa nas duas ferramentas** (comparação cruzada entre ferramentas). O gate **nunca** compara duas subpastas diferentes dentro de uma mesma ferramenta.
- Achado real, confirmado por `diff` direto nesta sessão (2026-09-08), não por suposição de grafo: `tools/aidd-enterprise/scripts/gates/G_SEGURANCA.py` (411 linhas, 8 camadas de auditoria, inclui "CAMADA 8: CVE Dependency Audit via pip-audit") diverge de `tools/aidd-enterprise/templates/gates/G_SEGURANCA.py` (330 linhas, só 7 camadas — a camada 8 está inteiramente ausente). Ou seja: um projeto novo gerado a partir do template recebe um gate de segurança sem uma camada inteira de auditoria que protege este próprio repositório, e hoje nada detecta isso automaticamente.
- Ainda **não confirmado** nesta sessão: se a mesma divergência (scripts/gates vs templates/gates) existe em `aidd-master`, e se existe em outros gates além de `G_SEGURANCA.py` — precisa de `diff` real antes de qualquer alteração no baseline, não suposição por espelhamento.
- Nota lateral, fora do escopo deste item (só registro): as mesmas duas linhas `import subprocess` (linhas 26 e 27) aparecem repetidas por engano em `tools/aidd-enterprise/scripts/gates/G_SEGURANCA.py` — correção mecânica trivial, tratada na iniciativa separada `correcao-codigo-limpo`, não aqui.

## Definição de Pronto

1. Confirmar por `diff` real (não suposição) se a mesma divergência `scripts/gates` vs `templates/gates` existe em `aidd-master`, e para quais gates especificamente (não só `G_SEGURANCA.py`).
2. Adicionar par(es) novo(s) à lista `PARES` em `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` comparando `scripts/gates/` vs `templates/gates/` **dentro de cada ferramenta separadamente** (intra-ferramenta, não cross-tool como os pares existentes) — ex.: um par para `aidd-enterprise` e outro para `aidd-master`.
3. Atualizar o baseline via `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py --atualizar-baseline`, registrando `G_SEGURANCA.py` como `esperado_identico: false` com o motivo real documentado (camada 8 de CVE audit presente só na versão viva) — nunca mascarado como igual.
4. Rodar `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` (sem flag) e confirmar que passa, com as divergências reais documentadas no baseline (não escondidas nem ignoradas).
5. Decisão sobre corrigir ou não a divergência da camada 8 (portar pro template vs manter como está) registrada explicitamente como pendência separada para decisão humana — não fabricar essa decisão dentro deste item.

## Critério de saída

- `gates/baseline_nucleo_compartilhado.json` atualizado e commitado com o(s) novo(s) par(es).
- `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` rodado de verdade e aprovado, refletindo divergências reais (não mascaradas).
- Nenhuma correção de acoplamento de runtime entre ferramentas introduzida (Regra Fixa #5 mantida).
- Nenhum par marcado como idêntico por suposição — todo veredito vem de hash/diff real.

## Resultado da execução (2026-09-08)

- **Diff real confirmado nas duas ferramentas** (não só `aidd-enterprise`, também `aidd-master` — item 1 da Definição de Pronto): comparando todos os arquivos `.py` comuns entre `scripts/gates/` e `templates/gates/`, dentro de cada ferramenta:
  - Idênticos (8 arquivos, ambas as ferramentas): `G_CHAOS.py`, `G_CONTRACTS.py`, `G_ESTRUTURA.py`, `G_HARNESS_COMPAT.py`, `G_SEGREDOS.py`, `G_TESTES.py`.
  - Divergentes (2 arquivos, ambas as ferramentas, com o mesmo diff exato em `aidd-enterprise` e `aidd-master`):
    - `G_SEGURANCA.py`: versão viva (`scripts/gates`, 401 linhas, 8 camadas) tem a Camada 8 (CVE Dependency Audit via pip-audit) ausente na versão de template (`templates/gates`, 322 linhas, 7 camadas).
    - `G_QUALIDADE.py`: versão viva (`scripts/gates`, 146 linhas) roda Fuzzing Contínuo de APIs e Testes de Mutação (AST) via mutmut, ausentes por inteiro na versão de template (`templates/gates`, 85 linhas).
  - `G_ARQUITETURA.py`, `G_INJECT.py` e `G_PERFORMANCE.py` existem só em `scripts/gates/` (sem par em `templates/gates/`) nas duas ferramentas — não entram na comparação por não serem arquivo comum, mesma regra já aplicada aos demais pares do gate.
- Dois pares intra-ferramenta novos adicionados a `PARES` em `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py`: `aidd-enterprise/scripts-gates-vs-templates-gates` e `aidd-master/scripts-gates-vs-templates-gates`. Pares cross-tool existentes não foram alterados.
- `gates/baseline_nucleo_compartilhado.json` atualizado via `--atualizar-baseline` e os motivos placeholder ("REVISAR: ...") substituídos pelos motivos reais descritos acima, para os 4 registros divergentes (`G_SEGURANCA.py` e `G_QUALIDADE.py`, em cada uma das duas ferramentas).
- `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` (sem flag) executado de verdade: **APROVADO (100% OK)**, com as 4 divergências reais listadas como `[INFO] ... divergencia conhecida e documentada`, nenhuma mascarada.
- Teste unitário pré-existente (`tools/aidd-master/tests/unit/test_drift_gate_blind_spot.py`) rodado após a mudança: 5 passed, sem regressão.
- Nenhum acoplamento de runtime introduzido entre `aidd-master`/`aidd-enterprise` nem entre `scripts/` e `templates/` de uma mesma ferramenta — apenas leitura de arquivos para hash, exatamente como os pares cross-tool já existentes fazem (Regra Fixa #5 mantida).

### Pendência separada para decisão humana (fora de escopo deste item)

A Camada 8 (CVE Dependency Audit via pip-audit) existe apenas na versão viva de `G_SEGURANCA.py`, nas duas ferramentas. Este item **não decide** se essa camada deve ser portada para `templates/gates/G_SEGURANCA.py` (para que projetos novos gerados a partir do template também tenham essa auditoria) ou se a divergência deve permanecer como está — essa decisão de produto fica pendente, para o usuário resolver separadamente. O mesmo vale, em menor grau, para o Fuzzing Contínuo e os Testes de Mutação ausentes em `G_QUALIDADE.py` do template.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 5: Ampliar G_DRIFT_NUCLEO_COMPARTILHADO para comparar scripts/gates vs templates/gates dentro da mesma ferramenta.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 5: Ampliar G_DRIFT_NUCLEO_COMPARTILHADO para comparar scripts/gates vs templates/gates dentro da mesma ferramenta.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
