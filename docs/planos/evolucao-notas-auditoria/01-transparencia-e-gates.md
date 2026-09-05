# Pacote 1 — Transparência + Gates Mecânicos

> **Status:** ✅ Concluído e validado.
> **Gaps originais cobertos:** bug `--command` (Transparência); ausência de um gate que audite consistência entre `argparse` real e mensagens de erro (Gates Mecânicos).

---

## Diagnóstico (auditoria estendida às 4 ferramentas, não só master/enterprise)

A auditoria original achou o bug em `aidd-enterprise`. Antes de escrever a Definição de Pronto, estendi a varredura para **todos os 14 pontos de entrada com `argparse`** das 4 ferramentas:

`aidd-forge/aidd_forge/cli.py`, `aidd-master/scripts/aidd.py`, `aidd-enterprise/scripts/aidd.py`, e os 11 scripts com `argparse` do `aidd-generator` (`aidd_inject.py`, `pipeline_completo.py`, `verificar_gates.py`, `01_pesquisador.py`...`08_implementador.py`).

Rodei uma checagem sistemática (flags citadas em texto vs. flags realmente definidas via `add_argument`) contra os 14. Apareceram 8 "suspeitos" além do já conhecido — **verifiquei cada um manualmente, nenhum é bug real**:

| Suspeito | Onde | Por que é falso positivo |
|---|---|---|
| `--oneline`, `--count` | `05_criador.py` | Flags de `git log`/`git rev-list` invocado via `subprocess` — ferramenta externa |
| `--modo` | `05_criador.py:737` | Texto de exemplo (`orquestrador.py --modo interativo`) descrevendo o script *gerado*, não a CLI do generator |
| `--primary`, `--bg`, `--text`... (8 no total) | `06_documentador.py` | Variáveis CSS (`--primary: #2563eb;`) dentro de um template HTML — coincidem com a sintaxe `--nome` mas não são flags de CLI |
| `--implementar-codigo` | `07_analisador.py` | Menção correta a uma flag que existe de verdade em `pipeline_completo.py` — só não é definida *neste* arquivo (limite do meu check por-arquivo, não um bug) |
| `--flag`, `--arquivo` | `aidd_inject.py`, `verificar_gates.py` | Docstring/comentário explicando o conceito genérico, não uma citação real |
| `--help` | vários | Flag automática do próprio `argparse`, não custom |

**Conclusão do diagnóstico:** o único bug real confirmado nas 4 ferramentas é `aidd-enterprise/scripts/aidd.py:847`. O achado é preciso e contido — não é a ponta de um iceberg maior. Isso simplifica a Definição de Pronto: não precisamos "caçar mais bugs iguais", precisamos **impedir que este tipo específico volte a acontecer, em qualquer uma das 4 ferramentas, no futuro**.

---

## Definição de Pronto

1. **Correção pontual:** `--command` → `--mcp-command` na mensagem de erro de `aidd-enterprise/scripts/aidd.py:847`.

2. **Gate novo, baseado em AST (não regex ingênua)** — `G_CLI_HELP_CONSISTENCIA.py`:
   - Usa `ast.parse` para extrair, com precisão sintática, todas as flags definidas via `.add_argument(...)` em um arquivo.
   - Usa `ast.parse` para localizar todas as strings literais do arquivo, **excluindo** as que estão dentro de uma chamada `subprocess.run(...)`/`subprocess.Popen(...)`/`subprocess.check_call(...)`/`subprocess.check_output(...)` (são invocações de ferramentas externas, não da própria CLI).
   - Dentro do texto restante, procura tokens `--palavra` e exclui os que são imediatamente seguidos por `:` (padrão de declaração CSS, ex.: `--primary: #2563eb;`) e o `--help` universal do `argparse`.
   - Compara o que sobrar contra as flags definidas. Diverge → gate reprova, apontando arquivo, linha e o texto exato.

3. **Zero falso positivo comprovado:** o gate roda contra os 14 arquivos reais listados acima e não acusa nenhum dos 8 suspeitos já investigados e confirmados como falso positivo.

4. **Detecção comprovada do bug real:** rodar o gate ANTES da correção do item 1 precisa reprovar apontando exatamente `aidd-enterprise/scripts/aidd.py:847`. Depois da correção, precisa passar.

5. **Gate registrado onde faz sentido:** dentro de `scripts/gates/` de cada ferramenta que tem CLI própria via `argparse` (`aidd-master`, `aidd-enterprise`; avaliar se cabe em `aidd-forge`/`aidd-generator` dado que só têm 1 e 11 arquivos argparse respectivamente, não 17 comandos como master/enterprise) — chamado pelo respectivo comando `audit`/`verificar_gates` de cada ferramenta.
   *(Decisão tomada na implementação: registrado como 5º gate raiz em `ecossistema.py audit`, não por-ferramenta — ele audita o CÓDIGO-FONTE das 4 ferramentas, mesma natureza de G_HARNESS_COMPAT e G_DRIFT_NUCLEO_COMPARTILHADO, que também vivem na raiz.)*

6. **Testes automatizados do próprio gate** — não confiar só em "rodei e pareceu certo": um teste sintético com uma flag inconsistente forjada precisa fazer o gate reprovar, e um caso são precisa passar. Mesmo padrão de prova usado nos outros gates desta sessão (`test_compose_suite.py`, `G_DRIFT_NUCLEO_COMPARTILHADO.py`, `G_HARNESS_COMPAT.py`).

7. **Zero regressão:** suítes completas das 4 ferramentas + `ecossistema.py audit` (raiz) rodando depois da mudança, sem quebrar nada que já passava.

---

## Prompt de Implementação (registro retroativo)

> Este pacote já foi implementado diretamente (ver Veredito abaixo), sem passar por um agente executor separado. O prompt abaixo é um registro retroativo — documentado para manter a mesma estrutura dos demais pacotes e para servir de referência caso um pacote equivalente precise ser reaberto ou replicado em `proj_aidd/`.

```
Você vai corrigir um bug real e comprovado de inconsistência entre flags de
CLI e mensagens de erro no ecossistema-aidd (monorepo em
C:\Users\trcnologia\Desktop\ecossistema-aidd), e criar um gate determinístico
permanente contra recorrência desse tipo de bug nas 4 ferramentas
(aidd-forge, aidd-master, aidd-enterprise, aidd-generator).

BUG COMPROVADO: `tools/aidd-enterprise/scripts/aidd.py:847` tem
`print("[ERRO] type 'mcp' exige --command (ex: --command python).")` — mas a
flag realmente definida via `add_argument` é `--mcp-command`, não
`--command`. Corrija a mensagem para citar `--mcp-command`.

DEFINIÇÃO DE PRONTO:

1. Aplique a correção pontual acima.

2. Crie `gates/G_CLI_HELP_CONSISTENCIA.py` (gate raiz, mesmo padrão de
   `gates/G_HARNESS_COMPAT.py` e `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` já
   existentes nesse mesmo diretório — leia um deles primeiro para seguir o
   estilo). Use `ast.parse` (não regex ingênua) para: (a) extrair todas as
   flags definidas via `.add_argument(...)` em cada arquivo; (b) localizar
   citações de flags (`--palavra`) SOMENTE dentro de strings que são
   argumento direto de uma chamada `print(...)` ou de uma exceção construída
   dentro de um `raise ...(...)` — essa restrição de escopo é deliberada:
   elimina por construção os falsos positivos de citações de flags de
   ferramentas externas (`subprocess.run(["git", ...])`), variáveis CSS
   (`--primary: #2563eb;`) e docstrings/comentários explicando conceitos
   genéricos, sem precisar de uma lista de exclusão por caso. Compare as
   flags citadas contra as definidas; divergência = gate reprova, apontando
   arquivo, linha e o trecho exato.

3. Rode o gate contra TODOS os arquivos com `ArgumentParser` das 4
   ferramentas — não assuma que são poucos, faça
   `grep -rl "ArgumentParser" tools/*/scripts` (e `tools/*/aidd_forge` /
   equivalente do aidd-forge) primeiro para ter a lista real e completa.
   Investigue manualmente qualquer divergência que o gate acusar antes de
   decidir se é bug real ou falso positivo — não crie exceção sem entender
   a causa.

4. Se restar algum falso positivo legítimo (ex.: uma flag de ferramenta
   externa citada como aviso dentro de um `print()`, não como flag própria),
   documente em `gates/allowlist_cli_help.json` (mesmo padrão de
   `gates/allowlist_segredos.json`) com justificativa — nunca use a
   allowlist só para silenciar o gate sem entender o caso.

5. Prove que o gate detecta o bug de verdade: reverta temporariamente a
   correção do item 1, rode o gate e confirme que ele reprova apontando a
   linha exata; reaplique a correção e confirme que volta a passar. Reporte
   os dois outputs reais.

6. Registre o gate em `ecossistema.py` (`cmd_audit`, raiz) como mais um gate
   determinístico da bateria, e documente em `AGENTS.md`.

7. Escreva testes automatizados do próprio gate (arquivo
   `gates/test_g_cli_help_consistencia.py`): um caso sintético inconsistente
   que precisa fazer o gate reprovar, um caso são que precisa passar, e um
   teste por cada classe de falso positivo (subprocess externo, CSS não
   impresso, docstring genérica) confirmando que continuam corretamente
   ignorados.

8. Rode e cole o resultado real de: `python ecossistema.py audit` (raiz) e
   as suítes completas de `aidd-forge`, `aidd-master`, `aidd-enterprise`,
   `aidd-generator`. Todos precisam passar sem regressão.

REGRAS DE ESCOPO — NÃO FAÇA: não toque em nenhum outro arquivo; não crie
heurísticas frágeis por caso quando uma restrição de escopo estrutural
resolve; não faça `git commit`/`git push`.

ENTREGÁVEL: lista de arquivos alterados, evidência real (comando + output)
de cada item acima, e qualquer desvio necessário da Definição de Pronto
reportado explicitamente em vez de decidido sozinho.
```

---

## Veredito

**Implementação:**
1. `aidd-enterprise/scripts/aidd.py:847` corrigido: `--command` → `--mcp-command`.
2. `gates/G_CLI_HELP_CONSISTENCIA.py` criado (AST-based: extrai flags de `add_argument`, restringe a checagem de citação a strings argumento de `print(...)`/`raise ...(...)` — escopo que exclui por construção subprocess externo, CSS não impresso e docstrings, sem heurística frágil por classe).
3. `gates/allowlist_cli_help.json` criado (mesmo padrão de `allowlist_segredos.json`) para o único caso legítimo restante: `--no-verify` citado como aviso sobre `git commit`, não como flag própria, em `G_BLOQUEAR_SEGREDOS.py:113`.
4. Gate registrado em `ecossistema.py audit` (5º gate raiz, ao lado de G_ECOSSISTEMA_INTEGRIDADE/G_DRIFT_NUCLEO_COMPARTILHADO/G_HARNESS_COMPAT/G_SEGREDOS) e documentado em `AGENTS.md` — correção de escopo em relação à Definição de Pronto original: não é um gate por-ferramenta (a divergência de CLI é uma questão de *fonte* das 4 ferramentas, auditada da raiz, igual aos outros 4).
5. `gates/test_g_cli_help_consistencia.py` — 8 testes: detecta o caso sintético inconsistente, aprova o caso são, e prova (com fixtures mínimas) que as 3 classes de falso positivo do diagnóstico continuam corretamente ignoradas; mais 2 testes de regressão contra o repositório real (0 falso positivo nos 19 arquivos, `checar()` retorna 0).

**Evidência de teste real:**
- Escopo do diagnóstico corrigido durante a implementação: eram **19 arquivos** com `ArgumentParser` nas 4 ferramentas (não 14 como a auditoria inicial havia contado — faltavam `pipeline_completo.py` e 5 arquivos de `aidd-generator/scripts/gates/` e `core/`). Todos os 19 auditados.
- Detecção comprovada por reprodução real: revertida a correção (`--command` de volta), `python gates/G_CLI_HELP_CONSISTENCIA.py` reprovou apontando exatamente `aidd-enterprise/scripts/aidd.py:847`; reaplicada a correção, gate voltou a aprovar.
- Zero falso positivo nos 19 arquivos reais (rodado após a correção do escopo de detecção — a primeira versão do gate gerou 27 falsos positivos legítimos, corrigidos restringindo a checagem a `print`/`raise`).
- `python ecossistema.py audit`: 5/5 gates raiz aprovados.
- `pytest gates/`: 8/8 passou.
- Suítes completas: aidd-forge 191 passed/1 skipped; aidd-master 191 passed/4 skipped; aidd-enterprise 196 passed/4 skipped; aidd-generator 756 passed. Nenhuma regressão.

**Nota — antes → depois:**
- **Gates Mecânicos: 7/10 → 8/10 (alvo atingido).** Este pacote era o único dono do gap "nenhum gate audita consistência CLI-vs-mensagem"; está fechado por completo.
- **Transparência / Zero Alucinação: 8/10 → 8.5/10 (alvo de 9/10 ainda não atingido).** O diagnóstico original (`PLANO-EVOLUCAO-NOTAS-AUDITORIA.md`, linha 28) lista 3 gaps sob esta dimensão: (a) bug `--command` — **fechado aqui**; (b) `tokens_consumidos` autodeclarado sem marcação — pertence ao Pacote 5; (c) `plan`/`prompt` não avisam que não usam IA — pertence ao Pacote 4. Declarar 9/10 agora seria inflar a nota sem verificação genuína dos outros dois terços do gap; o 9/10 só é honesto quando os Pacotes 4 e 5 também fecharem suas partes desta mesma dimensão.

Atualizado em `00-PROCESSO-E-DECISOES.md` §7 para refletir essa nuance entre dimensões.
