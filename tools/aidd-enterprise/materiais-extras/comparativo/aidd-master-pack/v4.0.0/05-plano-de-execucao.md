# Manifesto de Plano de Execução — AIDD Master Pack

> **Tag documentada:** `v4.0.0`
> **Base:** Busca exaustiva por `PLANO-EXECUCAO-ESTRUTURADO.json` (ou geradores equivalentes) em todo o snapshot extraído da tag via `git archive`.

---

## 1. Declaração Honesta: Não Há Geração Automática do Manifesto Nesta Tag

Antes de descrever o formato do arquivo, é preciso deixar claro um ponto verificado por leitura completa dos três scripts do pacote (`scripts/aidd.py`, `scripts/provision_project.py`, `scripts/add_module.py`):

**Nenhum script da tag v4.0.0 cria ou escreve o arquivo `PLANO-EXECUCAO-ESTRUTURADO.json`.**

- `provision_project.py` cria pastas, copia arquivos-núcleo (`database.py`, `events.py`, `openapi.py`, `webhooks.py`), copia infraestrutura Docker/deploy e roda `git init`. Em nenhum momento escreve um arquivo `.json` de plano.
- `add_module.py` gera apenas os 5 arquivos de uma fatia vertical (models, services, routes, componente HTML, teste). Também não toca em nenhum manifesto de plano.
- `aidd.py` **lê** o arquivo `PLANO-EXECUCAO-ESTRUTURADO.json` no comando `status` (`cmd_status`), mas apenas se ele já existir no diretório — se não existir, o comando simplesmente pula essa parte do relatório e mostra apenas os módulos instalados em `src/modules/`. Não há nenhum comando que **crie** o arquivo.

Portanto, o manifesto **existe apenas como convenção documental**: ele aparece em 2 dos 12 projetos de exemplo do pacote (`examples/catalogo-digital-v3/PLANO-EXECUCAO-ESTRUTURADO.json` e `examples/plataforma-modular-assinaturas/PLANO-EXECUCAO-ESTRUTURADO.json`), tendo sido escrito manualmente por um agente de IA seguindo as instruções da `SKILL.md` — não por determinismo mecânico do pacote. Os outros 10 exemplos não têm esse arquivo.

---

## 2. Estrutura Real do Manifesto (como encontrado nos exemplos desta tag)

Os dois exemplares encontrados usam um esquema **simples e minimalista** — bem mais enxuto do que versões posteriores do framework. Estrutura consolidada dos campos observados:

```json
{
  "projeto": {
    "nome": "string — slug/nome do projeto",
    "descricao": "string — descrição em linguagem natural do que o projeto faz",
    "versao": "string, opcional — ex: '2.0.0' (nem sempre presente)",
    "arquitetura": "string — ex: 'AIDD 4 Camadas' ou 'AIDD Modular Data-Driven'",
    "zero_api_key_mode": "boolean, opcional — flag de filosofia 'zero fricção de API key'",
    "dual_database": "boolean, opcional — indica suporte SQLite/Postgres",
    "openapi_swagger": "boolean, opcional — indica se a doc de API está ativa",
    "docker_ready": "boolean, opcional — indica se há Dockerfile/compose",
    "status": "string — ex: 'INICIALIZADO'"
  },
  "modulos_instalados": ["array de strings, opcional — nomes dos módulos ativos"],
  "fases": [
    {
      "id": "string — slug da fase, ex: 'fase-01-analise'",
      "nome": "string — nome legível da fase",
      "status": "string — 'PENDENTE' | 'CONCLUIDO'",
      "mesa_orca": "string, opcional — nome da mesa de trabalho ORCA responsável",
      "expected_outputs": ["array de strings — caminhos de arquivos/pastas esperados como resultado da fase"]
    }
  ]
}
```

### Exemplo real 1 — `examples/catalogo-digital-v3/PLANO-EXECUCAO-ESTRUTURADO.json`
3 fases (`fase-01-analise`, `fase-02-implementacao`, `fase-03-validacao`), todas com `status: "PENDENTE"`, cada uma associada a uma `mesa_orca` (`mesa-analise`, `mesa-dev`, `mesa-qa`) e um único `expected_output` por fase.

### Exemplo real 2 — `examples/plataforma-modular-assinaturas/PLANO-EXECUCAO-ESTRUTURADO.json`
3 fases (`fase-01-core-setup`, `fase-02-modulos-iniciais`, `fase-03-infra-e-deploy`), com `status` misto (`CONCLUIDO`/`PENDENTE`), sem campo `mesa_orca`, mas com múltiplos `expected_outputs` por fase e campos extras no objeto `projeto` (`versao`, `dual_database`, `openapi_swagger`, `docker_ready`).

**Observação importante:** os dois exemplos não seguem exatamente o mesmo schema — um usa `mesa_orca`, o outro não; um tem `modulos_instalados`, o outro não. Isso confirma que, nesta tag, o manifesto é **produzido ad hoc por um agente de IA a cada projeto**, sem um gerador determinístico único que garanta um schema fixo e validável.

---

## 3. Como o Planejamento de Execução Realmente Funciona em v4.0.0

Já que não há geração automática do manifesto, o "planejamento" nesta versão depende inteiramente da orientação textual dada em `SKILL.md` e nos arquivos de regras (`templates/rules/*.md`), que descrevem um processo conceitual (não executado por código):

1. O agente de IA (Claude, Cursor, Antigravity etc., conforme o harness) lê a `SKILL.md` do pacote instalado.
2. Segue as **"3 Regras de Ouro"** (`templates/rules/02_golden_rules.md`): não usar o chat como terminal, usar Worktrees ORCA para frentes grandes, e — quando aplicável — reiniciar sessões usando um "Plano JSON" para retomar estado com poucos tokens. É essa terceira regra que motiva a convenção do `PLANO-EXECUCAO-ESTRUTURADO.json`, mesmo sem um gerador mecânico dedicado.
3. O agente decide manualmente quais fases criar, seus nomes, status e outputs esperados, e opcionalmente escreve esse plano em JSON à mão (como visto nos 2 exemplos) para poder retomar o trabalho depois.
4. A validação de progresso é feita rodando os comandos determinísticos do pacote (`aidd.py audit`, `aidd.py test`, `aidd.py status`) manualmente, fase a fase — não há orquestrador automático que leia o manifesto e dispare as fases sozinho.

---

## 4. O Que Isso Significa na Prática

| Pergunta | Resposta nesta tag |
|---|---|
| O pacote gera o manifesto de plano automaticamente? | Não |
| Existe um schema formal/validado para o manifesto? | Não — dois exemplos reais têm estruturas divergentes |
| Algum comando lê o manifesto? | Sim, `aidd.py status` (leitura best-effort, sem validação de schema) |
| Algum comando escreve/atualiza o manifesto conforme o progresso avança? | Não |
| O planejamento de fases é determinístico ou depende do agente de IA? | Depende inteiramente do agente de IA seguindo a `SKILL.md` |

Este ponto é uma das lacunas mais claras desta tag frente ao que o framework viria a ter depois: um manifesto rico, com `gates_qualidade`, lista de `modulos` com rotas/eventos, `arquitetura` detalhada e timestamp de criação (como o encontrado em versões muito mais recentes do projeto) simplesmente não existe em v4.0.0 — o que existe é uma convenção informal, aplicada de forma inconsistente entre os próprios projetos de exemplo do pacote.
