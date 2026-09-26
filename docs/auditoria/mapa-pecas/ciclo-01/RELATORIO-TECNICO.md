# Relatório Técnico — Mapa de Peças do Ecossistema (ciclo-01, Fase 1)

> **Data:** 26/09/2026 · **Base:** `main` em `e71750c`
> **Método:** `python scripts/catalogo_pecas.py`, que grava `docs/auditoria/mapa-pecas/catalogo-pecas.json`. O script é determinístico: `--check` dá exit 0 logo após gerar. A checagem de encaixe roda o `--help` real de cada ferramenta.
> **Tese do ciclo:** as ferramentas não são ilhas. São peças de LEGO que montam fluxos. Os 3 fluxos da Tríade (pure, open, freedom) são uma única receita de 7 etapas em que só a etapa 3 muda.
> **Substitui:** `docs/auditoria/historico_auditorias/catalogo_micro_ferramentas_e_gates.json`, que foi escrito à mão, cobre só skills e gates e está desatualizado (66 skills contra 75 hoje).

## 1. Inventário (totais do catálogo)

| Peça | Qtde | Observação |
|---|---|---|
| Ferramentas (`tools/`) | 8 | 69 subcomandos de CLI no total |
| Skills (`componentes/compartilhado/skills`) | 75 | 13 pares com a mesma descrição |
| Comandos slash | 16 | — |
| MCPs registrados (`.mcp.json`) | 6 | todos de terceiros |
| MCPs internos das ferramentas | 3 | nenhum registrado em config (ver 3.4) |
| Hooks (`.claude/settings.json`) | 3 | — |
| Gates | 86 nomes / 132 arquivos | 53 na raiz, 42 deles no pre-commit |
| Contratos de handoff (`specs/*.schema.json`) | 8 | — |
| Etapas da receita da Tríade | 7 | 2 com encaixe quebrado, 2 de fachada |

## 2. A receita da Tríade (`scripts/orquestrador_sincrono.py`)

| Etapa | Peça chamada | Encaixe |
|---|---|---|
| 01 forge | `forge init` | ok |
| 02 planner | `planner init` + import direto de `aidd_planner.core.planner_engine` | CLI ok; atalho interno (ver 3.3) |
| 03 engine (pure) | `generate <ideia> --pasta --implementar-codigo` | ok |
| 03 engine (open) | `factory curate --dominio --output` | **QUEBRADO**: o factory não tem subcomando nem essas flags; só aceita `--plano` e `--pasta`. Execução real: exit 2 |
| 03 engine (freedom) | `bridge scan --dir` + script interno do master `dispatch_pipeline.py` | **QUEBRADO**: `scan` recebe a pasta como argumento, não `--dir`. Execução real: exit 2 |
| 04 master | `master init`, `master add-module` | ok |
| 05 enterprise | `enterprise inject rule`, `enterprise verificar-drift` | ok |
| 06 ops | nenhuma | **FACHADA**: só confere se existem `Dockerfile` e `docker-compose.yml`; o `aidd-ops` nunca roda |
| 07 auditoria | nenhuma | **FACHADA**: não roda gate; grava `"status": "CONFORME_100_POR_CENTO"` fixo |

Na prática, **só o Fluxo 01 (pure) consegue passar da etapa 3**, e mesmo assim termina com uma auditoria que não confere nada.

## 3. Achados

### 3.1 Encaixe e honestidade da receita (Alta)
- **Etapa 3 quebrada em 2 de 3 fluxos.** A receita chama as ferramentas com parâmetros que elas não têm.
- **Etapas 6 e 7 de fachada.** O pipeline informa 100% de conformidade sem executar ops nem gates. Vai contra a Lei #13 (gate que morde) e o `G_HONESTIDADE_ROTULO`.
- **Validação de contrato abre quando quebra.** Em `_validar_schema`, a falta de `jsonschema` ou do arquivo de schema devolve `True` (aprovado).
- **Ordem invertida entre factory e ops.** O factory exige `PLANO-INFRAESTRUTURA.json`, que é gerado pelo `ops plan`. Só que o ops vem depois do factory na receita.

### 3.2 Master × Enterprise = uma ferramenta mantida duas vezes (Alta)
- 92 arquivos idênticos byte a byte entre os dois (54 só deles; o resto também está no núcleo compartilhado ou no factory), medidos na `main` limpa.
- 20 verbos de CLI repetidos: `init`, `add-module`, `inject`, `audit`, `deploy`, `plan`…
- Na receita os papéis já estão separados: **master = esqueleto** (`init`, `add-module`) e **enterprise = blindagem** (`inject`, `verificar-drift`).

### 3.3 Peça mexendo por dentro de outra (Média)
- A etapa 02 importa uma função interna do planner, quando a CLI já oferece `planner export-dispatch`. Se der erro, ele é rebaixado a `WARN`.
- A etapa 03 (freedom) chama `tools/aidd-master/scripts/dispatch_pipeline.py` direto, sem passar pela CLI do master.
- O motor genérico de pipeline (`orchestrator_pipeline.py`, comando `ecossistema.py pipeline`) mora dentro do `aidd-master`.

### 3.4 Peças soltas (Média)
- Os MCPs `mcp-verificador-cve` (generator), `cloudflare-mcp` e `docker-mcp` (ops) existem, mas não estão registrados em `.mcp.json`, `opencode.jsonc` nem `mimocode.jsonc`. Nenhum agente consegue usá-los.
- 11 dos 53 gates da raiz não estão no pre-commit.

### 3.5 Mesma tarefa, várias donas (Média)

| Tarefa | Donas |
|---|---|
| barrar segredos | enterprise, forge, generator, master, ops, gates |
| compatibilidade de harness | enterprise, forge, generator, master, componentes, gates, scripts |
| injetar componentes | enterprise, forge, generator, master |
| detectar stack/camada | enterprise, forge, generator, master |
| auditar conformidade | enterprise, forge, generator, master, componentes, gates, scripts |
| docker compose | enterprise, factory, master, ops, gates |
| gerar frontend | bridge, enterprise, factory, master, gates |
| ponte com o Orca | forge, generator, componentes |

**10 gates têm o mesmo nome e código diferente:** `G_HARNESS_COMPAT` (4 versões), `G_INJECT` (4), `G_SEGREDOS`, `G_BLOQUEAR_SEGREDOS`, `G_CONTRACTS`, `G_PERFORMANCE`, `G_CYBERSECURITY_OWASP`, `G_QUARTETO_SINE_QUA_NON`, `G_SAIDA_BINARIA`, `G_TESTES_REAIS`.

### 3.6 Skills-alias (Baixa)
São 13 pares com a mesma descrição, como `pure`/`aidd-pure`, `plan`/`aidd-plan`, `orchestrate`/`aidd-orchestrate` e `sessao`/`aidd-sessao`. Cada fluxo ainda tem uma terceira skill (`fluxo-0N-runner`). Parte disso é intencional: serve para contornar colisão de nome de slash, como o `/open` no Antigravity. O plano precisa separar alias necessário de repetição.

## 4. Próximas fases (depende de aprovação)

A **Fase 2 (Arquiteto)** vira `PLANO-EVOLUCAO.md` neste ciclo, com os tickets na ordem abaixo:
1. Consertar os encaixes da etapa 3 e as etapas de fachada 6 e 7, e fazer a validação de contrato reprovar quando quebra.
2. Transformar a receita em dado (um arquivo por fluxo) e tirar o motor de pipeline de dentro do master.
3. Separar master (esqueleto) de enterprise (blindagem).
4. Definir uma dona por tarefa (gates, injetor, detector) e 1 skill por fluxo, mais os aliases que forem necessários.

O catálogo vira gate (`--check` no pre-commit) só depois do item 2, para não travar commits enquanto a receita ainda muda.
