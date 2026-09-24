# Arquitetura Agêntica de Auditoria e Evolução (The Audit Scaffold)

> **Governança:** Padrão Canônico para Auditoria e Evolução Contínua de Ferramentas no Ecossistema AIDD.  
> **Framework:** Lens 15-D (The Agentic Anatomical Matrix) + Pipeline 4F em Git Worktrees Efêmeras.

---

## 1. Topologia Estrutural

Toda ferramenta sob auditoria tem uma pasta exclusiva, `docs/auditoria/<ferramenta>/`. **Cada rodada de auditoria é um ciclo numerado** (`ciclo-01/`, `ciclo-02/`, ...) com todos os artefatos daquela rodada; só o gate `G_auditoria_15D.py` fica na raiz da ferramenta, compartilhado entre os ciclos. A topologia abaixo é lida **de cima para baixo, na ordem de execução**. Cada estágio lista o que entra (`IN`), o que sai (`OUT`) e o que prova que saiu certo (`GATE`). Todo `OUT` de um estágio reaparece como `IN` de algum estágio seguinte, com o mesmo nome e a marca `← N`.

**Legenda de autoria** (quem escreve o arquivo):

| Marca | Quem escreve | Regra |
| :--- | :--- | :--- |
| `[HUMANO]` | Só o usuário | Nenhum script ou agente edita. Scripts só leem. |
| `[FIXO]` | Governança do repositório | Referência comum a todas as ferramentas. |
| `[SCAFFOLD]` | `scripts/scaffold_auditoria.py` | Determinístico. `MANIFESTO-4F.json` é regerado a cada execução; os demais só são criados se não existirem. |
| `[LLM]` | Agente do estágio (harness/model do config) | Inteligência; sempre validada por um `GATE`. |
| `[COMPILADOR]` | `scripts/compilador_plano_evolucao.py` | Determinístico, sem LLM. Regerado a cada compilação. |

`<raiz>` = `docs/auditoria/<ferramenta>` · `<f>` = `<raiz>/ciclo-NN` (ciclo vigente) · `<f-1>` = ciclo anterior

**Regra de ciclo** (aplicada pelo estágio 0):

| Situação da ferramenta | O que o scaffold faz |
| :--- | :--- |
| Nunca auditada | Abre `ciclo-01/` |
| Ciclo vigente sem `LAUDO-15D-REVISADO.md` | **Retoma** o mesmo ciclo (regera só o manifesto) |
| Ciclo vigente concluído | **Abre** `ciclo-NN+1/`, herda o `DOD.md` de `<f-1>` e a Fase 1 compara Nota Anterior → Nota Nova |
| Layout plano antigo (artefatos na raiz) | Migra tudo para `ciclo-01/`, reescrevendo os caminhos |

Como todo `output_handoff` fica dentro do ciclo, o cache do orquestrador (pular fase cuja saída já existe) vale **por ciclo**. Se todas as fases já têm saída, o orquestrador diz `NADA A FAZER` e não declara sucesso.

```text
[0] SCAFFOLD ─ python scripts/scaffold_auditoria.py <ferramenta>   (determinístico, sem LLM)
    IN   docs/auditoria/CONFIG-EXECUCAO-USUARIO.json    [HUMANO]   só leitura; chave pipeline_auditoria_4f
    IN   <f-1>/DOD.md                                   [SCAFFOLD ← 0 do ciclo anterior]  se houver
    OUT  <f>/                                           [SCAFFOLD] ciclo aberto ou retomado (regra de ciclo)
    OUT  <raiz>/G_auditoria_15D.py                      [SCAFFOLD] compartilhado; sem argumento valida o ciclo vigente
    OUT  <f>/DOD.md                                     [SCAFFOLD] herdado de <f-1> ou padrão
    OUT  <f>/MANIFESTO-4F.json                          [SCAFFOLD] harness/model/comando_terminal = config
    OUT  <f>/PROMPT-FASE-1-INSPETOR.txt                 [SCAFFOLD]
    OUT  <f>/PROMPT-FASE-2-ARQUITETO.txt                [SCAFFOLD] inglês, caminhos reais, formato de ticket
    OUT  <f>/PROMPT-FASE-3-CONSTRUTOR.txt               [SCAFFOLD] inglês
    OUT  <f>/PROMPT-FASE-4-RETORNO.txt                  [SCAFFOLD]
    GATE config incompleto (papel ou campo ausente)  -> exit 1, nada é gerado

[1] INSPETOR ─ config.pipeline_auditoria_4f.inspetor
    IN   <f>/PROMPT-FASE-1-INSPETOR.txt                 [SCAFFOLD ← 0]
    IN   docs/auditoria/TEMPLATE-AUDITORIA-FERRAMENTA.md [FIXO]    Lens 15-D
    IN   código-fonte da skill alvo                     (reprodução real, nunca só leitura)
    IN   <f-1>/LAUDO-15D-REVISADO.md                    [LLM ← 4 do ciclo anterior]  se houver: Nota Anterior
    OUT  <f>/LAUDO-15D-INICIAL.md                       [LLM]
    GATE python <raiz>/G_auditoria_15D.py <f>/LAUDO-15D-INICIAL.md  -> exit 0 / exit 1

[2] ARQUITETO ─ config.pipeline_auditoria_4f.arquiteto
    IN   <f>/PROMPT-FASE-2-ARQUITETO.txt                [SCAFFOLD ← 0]
    IN   <f>/LAUDO-15D-INICIAL.md                       [LLM ← 1]
    IN   <f>/DOD.md                                     [SCAFFOLD ← 0]
    IN   docs/auditoria/aidd-melhoria/ciclo-01/PLANO-EVOLUCAO.md [FIXO] molde de formato
    OUT  <f>/PLANO-EVOLUCAO.md                          [LLM]      1 ticket por dimensão FAILED
    GATE estágio 2b (o compilador reprova ticket fora do formato)

[2b] COMPILADOR ─ python scripts/compilador_plano_evolucao.py --plano <f>/PLANO-EVOLUCAO.md
    IN   <f>/PLANO-EVOLUCAO.md                          [LLM ← 2]
    IN   docs/auditoria/CONFIG-EXECUCAO-USUARIO.json    [HUMANO]   só leitura; chave pipeline_evolucao_rotativo
    OUT  <f>/PLANO-EVOLUCAO.json                        [COMPILADOR] rodízio harness/model/comando por ticket
    OUT  <f>/prompts_tickets/PROMPT-TICKET-NN.txt       [COMPILADOR] inglês telegráfico imperativo
    GATE exit 1 se: ticket sem **Artefato de Handoff:**, sem **Construtor Prompt (EN):**,
         prompt com PT-BR/não-ASCII, ou config ausente/incompleto; nada parcial fica em disco

[3] CONSTRUTOR ─ fase: config.pipeline_auditoria_4f.construtor | tickets: PLANO-EVOLUCAO.json
    IN   <f>/PROMPT-FASE-3-CONSTRUTOR.txt               [SCAFFOLD ← 0]
    IN   <f>/PLANO-EVOLUCAO.json                        [COMPILADOR ← 2b]
    IN   <f>/prompts_tickets/PROMPT-TICKET-NN.txt       [COMPILADOR ← 2b]
    OUT  output_handoff de cada ticket                  [LLM]      código + testes, em Git Worktree efêmera
    OUT  <f>/RELATORIO-CONSTRUTOR.md                    [LLM]      ticket, arquivo, comando, exit antes/depois
    GATE pytest do ticket: exit 1 antes da correção (RED) e exit 0 depois (GREEN)

[4] RETORNO ─ config.pipeline_auditoria_4f.retorno
    IN   <f>/PROMPT-FASE-4-RETORNO.txt                  [SCAFFOLD ← 0]
    IN   <f>/LAUDO-15D-INICIAL.md                       [LLM ← 1]
    IN   <f>/DOD.md                                     [SCAFFOLD ← 0]
    IN   <f>/RELATORIO-CONSTRUTOR.md                    [LLM ← 3]
    IN   código alterado (output_handoff)               [LLM ← 3]
    OUT  <f>/LAUDO-15D-REVISADO.md                      [LLM]      honestidade de rótulo
    GATE python <raiz>/G_auditoria_15D.py <f>/LAUDO-15D-REVISADO.md  -> exit 0 / exit 1

[5] FECHAMENTO ─ consolidação
    IN   todos os OUT de 0 a 4
    OUT  <f>/RESUMO-USUARIO.md                          [LLM]      linguagem simples ("Na Festa")
    OUT  <f>/RELATORIO-TECNICO.md                       [LLM]      rastreabilidade: comandos e exit codes ("Na Casa")
    GATE aprovação humana (Join Barrier): --aprovar
```

**Fluxo git do orquestrador** (`scripts/orquestrador_4f.py`):

| Passo | O que acontece | Se falhar |
| :--- | :--- | :--- |
| Início | Cria a branch `audit/<pipeline_id>` a partir do HEAD; a branch atual não muda mais até a aprovação | — |
| Cada fase | Worktree efêmera sobre a branch do ciclo → agente → `gate_fase` → commit na branch do ciclo | Pipeline para, nada é commitado, worktree preservada |
| Fim | `gate_final` (`python ecossistema.py audit`) roda uma vez; se passar, o commit testado é marcado como aprovável | Ciclo não fica aprovável |
| Aprovação (humano) | `--aprovar`: merge `--no-ff` na branch atual, só se a branch do ciclo ainda é o commit aprovado | Recusa (exit 1) |

Commit de fase usa `--no-verify` de propósito: o gate da própria fase acabou de passar, e a bateria completa roda uma vez no `gate_final`, e não a cada fase.

**Índice físico** (a mesma pasta vista como árvore; a lógica está nos blocos acima):

```text
docs/auditoria/
├── CONFIG-EXECUCAO-USUARIO.json       [HUMANO]
├── TEMPLATE-AUDITORIA-FERRAMENTA.md   [FIXO]
├── PLANO-MESTRE-AUDITORIA.md          [FIXO]   catálogo e progresso geral
└── <ferramenta>/                      <raiz>
    ├── G_auditoria_15D.py             [SCAFFOLD]    0 -> 1, 4   (compartilhado)
    ├── ciclo-01/                      <f-1>  ciclo concluído (histórico preservado)
    │   └── ...
    └── ciclo-02/                      <f>    ciclo vigente
        ├── DOD.md                     [SCAFFOLD]    0 -> 2, 4
        ├── MANIFESTO-4F.json          [SCAFFOLD]    0
        ├── PROMPT-FASE-1-INSPETOR.txt [SCAFFOLD]    0 -> 1
        ├── LAUDO-15D-INICIAL.md       [LLM]         1 -> 2, 4
        ├── PROMPT-FASE-2-ARQUITETO.txt [SCAFFOLD]   0 -> 2
        ├── PLANO-EVOLUCAO.md          [LLM]         2 -> 2b
        ├── PLANO-EVOLUCAO.json        [COMPILADOR]  2b -> 3
        ├── prompts_tickets/           [COMPILADOR]  2b -> 3
        ├── PROMPT-FASE-3-CONSTRUTOR.txt [SCAFFOLD]  0 -> 3
        ├── RELATORIO-CONSTRUTOR.md    [LLM]         3 -> 4
        ├── PROMPT-FASE-4-RETORNO.txt  [SCAFFOLD]    0 -> 4
        ├── LAUDO-15D-REVISADO.md      [LLM]         4 -> 5, e 1 do próximo ciclo
        ├── RESUMO-USUARIO.md          [LLM]         5
        └── RELATORIO-TECNICO.md       [LLM]         5
```

**Proibido:** gravar qualquer artefato de auditoria em `docs/planos/`.

---

## 2. As Duas Engrenagens Dinâmicas

### Engrenagem A: Soberania do Usuário (`CONFIG-EXECUCAO-USUARIO.json`)
As ferramentas e agentes **não escolhem seus próprios modelos**. O `CONFIG-EXECUCAO-USUARIO.json` na raiz de `docs/auditoria/` define `harness`, `model` e `comando_terminal` em duas chaves:
- `pipeline_auditoria_4f`: um perfil por papel (`inspetor`, `arquiteto`, `construtor`, `retorno`), que é lido pelo scaffold para montar o `MANIFESTO-4F.json`.
- `pipeline_evolucao_rotativo`: uma lista em rodízio (ticket 1 → item 1, ticket 2 → item 2, ...), que é lida pelo compilador para montar o `PLANO-EVOLUCAO.json`.

Só o humano edita este arquivo; scaffold e compilador apenas leem. Papel, item ou campo ausente reprova com exit 1, sem valor padrão inventado. Depois de editar o config, rode de novo o scaffold (que regera o `MANIFESTO-4F.json`) e o compilador (que regera o `PLANO-EVOLUCAO.json` e os `prompts_tickets/`).

### Engrenagem B: O Compilador de Planos (`compilador_plano_evolucao.py`)
O Arquiteto (Fase 2) gera o documento textual `PLANO-EVOLUCAO.md`. O compilador determinístico:
1. Extrai cada ticket (`### Ticket N: <Título> (Refere-se a Dx / DoD y)`) por regex.
2. Lê `**Falha 15-D:**` → `dimensao_15d`; `**Artefato de Handoff:**` → `output_handoff`; `**Construtor Prompt (EN):**` → corpo do prompt.
3. Reprova (exit 1) um ticket sem handoff, sem prompt EN, ou com prompt em PT-BR ou não-ASCII.
4. Injeta `harness`/`model`/`comando_terminal` do `pipeline_evolucao_rotativo`, em rodízio.
5. Emite `PLANO-EVOLUCAO.json` e `prompts_tickets/PROMPT-TICKET-NN.txt`. Tudo é validado antes de gravar: em caso de falha, nenhum arquivo parcial fica em disco.

---

## 3. Matriz Operacional (resumo da Seção 1)

| Estágio | Harness vem de | IN principal | OUT | GATE |
| :--- | :--- | :--- | :--- | :--- |
| **0. Scaffold** | — (determinístico) | `CONFIG-EXECUCAO-USUARIO.json`, ciclo anterior | `ciclo-NN/` (aberto ou retomado), `DOD.md`, `MANIFESTO-4F.json`, `PROMPT-FASE-1..4`; `G_auditoria_15D.py` na raiz | config incompleto → exit 1 |
| **1. Inspetor** | `pipeline_auditoria_4f.inspetor` | `PROMPT-FASE-1`, template, código, laudo revisado anterior | `LAUDO-15D-INICIAL.md` | `G_auditoria_15D.py` |
| **2. Arquiteto** | `pipeline_auditoria_4f.arquiteto` | `PROMPT-FASE-2`, laudo, `DOD.md` | `PLANO-EVOLUCAO.md` | compilador (2b) |
| **2b. Compilador** | — (determinístico) | `PLANO-EVOLUCAO.md`, config | `PLANO-EVOLUCAO.json`, `prompts_tickets/` | formato/idioma/config → exit 1 |
| **3. Construtor** | `pipeline_auditoria_4f.construtor` + rodízio por ticket | `PROMPT-FASE-3`, `PLANO-EVOLUCAO.json` | `output_handoff` de cada ticket + `RELATORIO-CONSTRUTOR.md` | pytest RED → GREEN |
| **4. Retorno** | `pipeline_auditoria_4f.retorno` | `PROMPT-FASE-4`, laudo inicial, código | `LAUDO-15D-REVISADO.md` | `G_auditoria_15D.py` |
| **5. Fechamento** | — | todos os OUT | `RESUMO-USUARIO.md`, `RELATORIO-TECNICO.md` | aprovação humana |

---

## 4. Comandos Canônicos do Sistema

**Abrir ou retomar o ciclo de auditoria de uma ferramenta:**
```bash
python scripts/scaffold_auditoria.py <nome-da-ferramenta>
```

**Executar pipeline de auditoria 4F:**
```bash
python scripts/orquestrador_4f.py --manifest docs/auditoria/<nome-da-ferramenta>/ciclo-NN/MANIFESTO-4F.json
```

**Compilar plano textual para pipeline executável:**
```bash
python scripts/compilador_plano_evolucao.py --plano docs/auditoria/<nome-da-ferramenta>/ciclo-NN/PLANO-EVOLUCAO.md
```

**Executar plano de evolução da ferramenta:**
```bash
python scripts/orquestrador_4f.py --manifest docs/auditoria/<nome-da-ferramenta>/ciclo-NN/PLANO-EVOLUCAO.json
```

**Aprovar o ciclo (Join Barrier, ação humana; merge na branch atual):**
```bash
python scripts/orquestrador_4f.py --manifest docs/auditoria/<nome-da-ferramenta>/ciclo-NN/MANIFESTO-4F.json --aprovar
```
