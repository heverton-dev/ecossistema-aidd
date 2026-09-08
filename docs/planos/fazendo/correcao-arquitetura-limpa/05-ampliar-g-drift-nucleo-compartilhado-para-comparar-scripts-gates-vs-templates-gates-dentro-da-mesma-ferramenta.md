# Item 5 — Ampliar G_DRIFT_NUCLEO_COMPARTILHADO para comparar scripts/gates vs templates/gates dentro da mesma ferramenta

> **Escopo:** Entra: registrar no baseline (`gates/baseline_nucleo_compartilhado.json`) um novo par **intra-ferramenta** — `scripts/gates/` (versão viva que protege este monorepo) comparada com `templates/gates/` (versão entregue a projetos novos), dentro de `aidd-enterprise` e dentro de `aidd-master`, separadamente — para que `G_DRIFT_NUCLEO_COMPARTILHADO.py` passe a monitorar essa divergência. Não entra: unificar fisicamente as duas cópias numa fonte só (violaria a Regra Fixa #5 do `00-PROCESSO-E-DECISOES.md` — sem acoplamento de runtime entre ferramentas); não entra comparar `templates/core` vs `templates/v2` (já decidido fora de escopo no item 2); não entra decidir se a camada 8 (CVE audit) deve ser portada para o template — isso é decisão de produto, não deste item.

> **Status:** ⏳ Rascunho gerado, aguardando aprovação

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
