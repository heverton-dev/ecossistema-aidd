# Relatório — Bateria 5: AIDD Generator (`tools/aidd-generator`)

> Execução real em 2026-09-06, ambiente Windows 11 (`C:\Users\trcnologia\Desktop\ecossistema-aidd`).
> Scripts de apoio: `docs/testes/testes/05_aidd_generator_sentinela.py`, `05_aidd_generator_responder.py`.
> Prompt (ideia) usado: `docs/testes/prompts/aidd_generator_ideia_todo_api.txt` — `"REST API de lista de tarefas com criar, listar, concluir e remover tarefas"`.
> **Modo de execução: DELEGADO** (zero custo de API). Nenhuma `LLM_MODEL`/chave de API real foi configurada. O próprio executor desta bateria (eu) atuou como o "LLM delegado" em tempo real, lendo cada `_llm_request_*.json` e escrevendo `_llm_response_*.json` com conteúdo genuíno e funcional — nunca fake/stub.

## Veredito final: **PASSOU**

As 8 fases do pipeline completaram com **exit code real 0** do processo. Score de auto-crítica real da Fase 7: **88/100**. `verificar_gates.py` retornou **exit 0** (5/6 gates, o único não aprovado é opcional e depende de `LLM_MODEL`, que deliberadamente não configuramos). A suíte pytest do projeto gerado passa **9/9** de forma real e independente. A suíte pytest completa de `tools/aidd-generator` passa **770/770**, sem regressão.

## Linha do tempo real das 8 fases

| Fase | Nome | Status | Tempo | Tokens (LLM) |
|---|---|---|---|---|
| 1 | Pesquisador | ✅ COMPLETO | 6.3s | 0 (100% determinístico — busca real GitHub/HuggingFace) |
| 2 | Analisador | ✅ COMPLETO | 8.0s | 850 (delegado, 1 requisição) |
| 3 | Designer | ✅ COMPLETO | ~poucos s | 2.830 (delegado, 5 subagentes em paralelo) |
| 4 | Decisor | ✅ COMPLETO | quase instantâneo | 0 (heurístico, sem `--interativo`) |
| 5 | Criador | ✅ COMPLETO | 0.4s | 0 (git init + commit real, SQLite real) |
| 8 | Implementador | ✅ COMPLETO | — | 1.970 (delegado, 2 requisições: script + teste de integração) |
| 6 | Documentador | ✅ COMPLETO | — | 0 (templates determinísticos) |
| 7 | Auto-crítica | ✅ COMPLETO | 0.1s | 0 (determinístico) — **score 88/100** |

**Total de requisições delegadas respondidas de verdade: 8** (1 na Fase 2, 5 na Fase 3, 2 na Fase 8 — script principal + teste de integração). Zero fallback para modo headless, zero resposta fake/stub.

## Achado real #1 (grave) — fallback de `referencias_utilizadas` da Fase 2 está quebrado

Na primeira tentativa desta bateria, deixei o campo `referencias_utilizadas` vazio na resposta da Fase 2, contando com o mecanismo de auto-recuperação descrito no próprio código de `02_analisador.py` (linhas 332-339): se o LLM não citar referências, o código tentaria extrair `titulo`/`url`/`nome` de `referencias.get('referencias', [])`. **O gate A2 (zero alucinação) falhou mesmo assim** ("0 referências rastreadas"), derrubando a Fase 2 e o pipeline inteiro.

Investigação real (não hipotética): o parâmetro `referencias_phase1` recebido por `AnalisadorFase2.executar()` é, na prática (`pipeline_completo.py` linha 192-193), o conteúdo de `insights_phase1.json` — um dicionário com a chave `insights` (lista de `{tipo, descricao, frequencia, fontes}`), **nunca uma chave `referencias`**. O código de fallback busca `referencias.get('referencias', [])`, que portanto **sempre retorna lista vazia** para o formato real produzido pela Fase 1 — o mecanismo de auto-recuperação está morto/inalcançável na prática, não só neste caso de teste.

**Impacto real:** qualquer resposta delegada ou headless que não inclua explicitamente `referencias_utilizadas` não-vazio faz a Fase 2 falhar sempre, mesmo que a Fase 1 tenha encontrado referências reais válidas (neste caso, 10 repositórios GitHub reais). **Correção aplicada no teste:** citei manualmente 2 referências reais e verificáveis extraídas de `referencias_github.json` (`public-apis/public-apis`) e de `insights_phase1.json` (`stack_linguagem Python, frequência 4`) na minha resposta — reexecutando, o gate A2 passou (`2 referências rastreadas`). Recomendação: corrigir o fallback em `02_analisador.py` para ler de `insights.get('insights', [])` (ou receber diretamente a lista de referências do GitHub, não os insights consolidados), e/ou reforçar o prompt para exigir explicitamente `referencias_utilizadas` não-vazio.

## Achado real #2 (menor) — símlinks multi-harness falham no Windows sem privilégio, com fallback correto

Na Fase 5, a criação de `~5 symlinks` (`.claude/CLAUDE.md → AGENTS.md`, etc.) falhou com `[WinError 1314] O cliente não tem o privilégio necessário` (Windows sem modo desenvolvedor/privilégio de symlink) — mas o código tem fallback real e correto: copia o conteúdo em vez de criar o link. Limitação de ambiente documentada, não um bug — o pipeline não quebrou, apenas usou o caminho alternativo.

## Achado real #3 (colateral, corrigido) — `verificar_gates.py` sobrescreveu um arquivo rastreado do repositório real

Rodar `python scripts/verificar_gates.py <projeto-gerado>` (cwd=`tools/aidd-generator`) executa o gate `G_HARNESS_COMPAT`, que faz um teste real de orquestração com timeout de **5 segundos** — muito mais curto que os 30-60s do protocolo real — e, como ninguém respondeu dentro desses 5s (eu não estava com o sentinela rodando nesse instante específico), o gate concluiu (falso-negativo) que "Claude Code" **não suporta** orquestração delegada, e **reescreveu o arquivo rastreado `tools/aidd-generator/HARNESS-COMPAT.json`** no repositório real com essa conclusão incorreta — contradizendo esta própria bateria, que acabara de provar 8 requisições delegadas reais bem-sucedidas segundos antes. Isso é uma fragilidade real do autoteste do gate (timeout curto demais para o próprio mecanismo que ele testa), mas também confirma que `verificar_gates.py`, quando roda a partir de `tools/aidd-generator`, grava no arquivo real da ferramenta em vez de escrever isoladamente dentro do `--pasta` alvo — mesma classe de achado das Baterias 2/3/4 (escrita fora do diretório isolado). **Revertido**: `git checkout -- tools/aidd-generator/HARNESS-COMPAT.json` restaurou o estado commitado; `git status` confirmado limpo depois.

## Exemplos reais completos de pedido + resposta (conteúdo verdadeiro, não resumido)

### Fase 2 (`phase_02`) — 1 requisição

**Prompt real enviado** (trecho relevante, `PROMPT_ANALISADOR_IDEIA` preenchido com a ideia real e as 10 referências reais da Fase 1):
```
# ENTRADA: AIDD Project Analyst — specialized in structured project analysis.
Analyze the PROVIDED project idea and the SIMILAR REFERENCES found.
PROJECT IDEA:
REST API de lista de tarefas com criar, listar, concluir e remover tarefas
SIMILAR REFERENCES (from Phase 1):
{"total_insights": 4, "insights": [{"tipo": "stack_linguagem", "descricao": "Python", "frequencia": 4, ...
...
```

**Resposta real que escrevi** (`_llm_response_76e3e123.json`, campo `conteudo` parseado):
```json
{
  "objetivo": "Fornecer uma API REST simples para gerenciar uma lista de tarefas, permitindo criar, listar, concluir e remover tarefas de forma rapida e confiavel.",
  "publico_alvo": "Desenvolvedores e pequenas equipes que precisam de um servico minimo de gestao de tarefas para uso interno ou como base de estudo.",
  "constraints": [
    "Zero dependencias externas pesadas - usar apenas biblioteca padrao do Python",
    "Armazenamento em memoria durante a execucao do processo",
    "Maxima economia de tokens no pipeline de geracao",
    "Codigo 100% testavel via import direto, sem subir servidor real"
  ],
  "stack_recomendado": {
    "linguagem": "Python 3.10+",
    "framework": "Nenhum",
    "banco": "Nenhum",
    "libs_principais": ["dataclasses", "uuid"]
  },
  "arquitetura": "Modulo unico tarefas.py expõe uma classe RepositorioTarefas que mantem as tarefas em memoria (dict indexado por id) e os metodos criar_tarefa, listar_tarefas, concluir_tarefa e remover_tarefa. Cada operacao e uma funcao pura testavel isoladamente, permitindo que uma camada HTTP fina seja acoplada por cima sem alterar a logica de dominio.",
  "referencias_utilizadas": [
    "public-apis/public-apis (referencia real de API publica encontrada na Fase 1)",
    "insight Fase 1: stack_linguagem Python, frequencia 4 entre os 10 repositorios pesquisados"
  ]
}
```
Resultado real: gates A1-A4 todos PASSOU (`A2_zero_alucinacao: 2 referências rastreadas`). Fase 2 COMPLETO em 8.0s.

### Fase 3 (`phase_03_subagent_engenheiro_scripts`) — 1 dos 5 subagentes

**Prompt real** (`PROMPTS_SUBAGENTES['engenheiro_scripts']` + contexto da ideia): pede scripts Python deterministas por camada, com nome/responsabilidade/pseudocódigo/percentual de determinismo/teste.

**Resposta real que escrevi:**
```json
{
  "scripts": [
    {
      "camada": 2,
      "nome": "tarefas.py",
      "responsabilidade": "CRUD de tarefas em memoria: criar, listar, concluir e remover tarefas",
      "pseudocodigo": "1. Definir dataclass Tarefa (id, titulo, concluida, criada_em)\n2. Classe RepositorioTarefas com dict interno mapeando id para Tarefa\n3. criar_tarefa(titulo) gera id via uuid4, guarda e retorna a Tarefa\n4. listar_tarefas(somente_pendentes=False) retorna lista ordenada por criada_em\n5. concluir_tarefa(id) marca concluida=True, lanca ValueError se id nao existe\n6. remover_tarefa(id) remove do dict, lanca ValueError se id nao existe",
      "determinismo_percentual": 100,
      "teste": "criar duas tarefas, concluir uma, remover a outra e validar listagem final vazia/consistente"
    }
  ]
}
```
Este exato script (`tarefas.py`) é o que a Fase 8 depois implementou de verdade. Os outros 4 subagentes (`arquiteto_camadas`, `especialista_tokens`, `arquiteto_ferramentas`, `especialista_gates`) foram respondidos em paralelo com conteúdo real equivalente (5 camadas AIDD completas, 67% de determinismo estimado, 2 ferramentas recomendadas, 3 gates G0-G2 desenhados) — todos os 5 completaram, gates D1-D3 (5 camadas presentes, scripts viáveis, determinismo ≥65%) PASSARAM. Fase 3 COMPLETO.

### Fase 8 (`phase_08` + `phase_08_integracao`) — implementação real + teste real

**Prompt real** (`PROMPT_IMPLEMENTAR_SCRIPT` preenchido): pedia código Python real e testável para `tarefas.py`, sem stubs, com testes pytest cobrindo casos válidos e inválidos.

**Resposta real que escrevi (código completo, não resumido):**
```python
"""Modulo de dominio: gestao de tarefas em memoria."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List


@dataclass
class Tarefa:
    id: str
    titulo: str
    concluida: bool = False
    criada_em: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RepositorioTarefas:
    """Repositorio em memoria para o CRUD de tarefas."""

    def __init__(self) -> None:
        self._tarefas: Dict[str, Tarefa] = {}

    def criar_tarefa(self, titulo: str) -> Tarefa:
        if not titulo or not titulo.strip():
            raise ValueError("titulo nao pode ser vazio")
        tarefa_id = str(uuid.uuid4())
        tarefa = Tarefa(id=tarefa_id, titulo=titulo.strip())
        self._tarefas[tarefa_id] = tarefa
        return tarefa

    def listar_tarefas(self, somente_pendentes: bool = False) -> List[Tarefa]:
        tarefas = sorted(self._tarefas.values(), key=lambda t: t.criada_em)
        if somente_pendentes:
            tarefas = [t for t in tarefas if not t.concluida]
        return tarefas

    def concluir_tarefa(self, tarefa_id: str) -> Tarefa:
        tarefa = self._tarefas.get(tarefa_id)
        if tarefa is None:
            raise ValueError(f"tarefa nao encontrada: {tarefa_id}")
        tarefa.concluida = True
        return tarefa

    def remover_tarefa(self, tarefa_id: str) -> None:
        if tarefa_id not in self._tarefas:
            raise ValueError(f"tarefa nao encontrada: {tarefa_id}")
        del self._tarefas[tarefa_id]
```

+ 8 testes pytest reais cobrindo criação (válida/inválida), listagem ordenada, conclusão (válida/inexistente), remoção (válida/inexistente) e filtro de pendentes.

**Resultado real:** `tentativa(s): 1` — passou de primeira, **sem precisar de nenhuma correção** (`phase_08_fix` nunca foi acionado). Em seguida, a Fase 8 pediu 1 teste de integração (`phase_08_integracao`), que respondi encadeando criar→listar→concluir→listar-pendentes→remover→listar — **1/1 passando**.

**Gates I1-I5 reais:**
```
✓ I1_scripts_implementados: 1/1 scripts implementados em disco
✓ I2_testes_coletam: Coleta OK
✓ I3_testes_passam: 9/9 testes passando
✓ I4_cli_executa: Sem main.py — gate não aplicável, não bloqueia
✓ I5_teste_integracao: 1/1 teste(s) de integração passando
```

## Verificação independente pós-pipeline (não confiei só no log do próprio pipeline)

- **Estrutura real do projeto gerado** (`<tmp>/todo-api`): `docs/`, `scripts/` (gates, phases, schemas), `src/tarefas.py`, `tests/{test_tarefas.py, test_integracao.py}` — confirmado por `find` direto no disco.
- **`git log --oneline`** dentro do projeto gerado: `b907dde feat: Inicialização de projeto AIDD para 'REST API de lista de tarefa...'` — commit real, feito pela própria Fase 5.
- **`estado_projeto.db`** (SQLite): confirmado existente, 16.0 KB, 2 tabelas criadas (gate `E3_sqlite_schema` real).
- **pytest do projeto gerado, rodado por mim de forma independente** (não só lendo o output do pipeline): `PYTHONPATH=src python -m pytest tests/ -q` → **9 passed** (bate exatamente com o que o pipeline reportou).
- **`python scripts/verificar_gates.py <projeto-gerado>`**: exit **0**. 5/6 gates PASSARAM (`G_BLOQUEAR_SEGREDOS`, `G_HARNESS_COMPAT` em modo degradado, `G_INTEGRACAO_CROSS_SCRIPT` 13/13 checks, `G_CYBERSECURITY_OWASP` 0 vulnerabilidades, `G_INJECT` 4/4 validações). O único gate reprovado, `G_VERIFICAR_LLM_PRONTO`, é **opcional** e falha por design quando `LLM_MODEL` não está configurado (modo delegado puro) — não bloqueia o exit code.
- **Score de auto-crítica real (Fase 7):** **88/100**, status "Profissional", 6 pontos fortes, 1 ponto a melhorar, roadmap de 2 fases até 100/100.
- **Suíte pytest completa de `tools/aidd-generator`** (`python -m pytest tests/ -q`, cwd `tools/aidd-generator`): **770 passed** em 45.17s, 0 falhas.

## Limpeza e critérios de saída

- Diretório temporário do projeto gerado (`<tmp>/aidd_gen_b5/todo-api`) removido ao final.
- Cache do protocolo delegado (`tools/aidd-generator/scripts/.aidd/cache/_llm_request_*` / `_llm_response_*`) limpo — confirmado vazio.
- `tools/aidd-generator/HARNESS-COMPAT.json` (arquivo rastreado, sobrescrito pelo Achado #3) revertido para o estado commitado via `git checkout --`.
- Nenhum processo do pipeline órfão (o processo em background terminou com exit 0, confirmado pela notificação de conclusão).
- Nenhum `git commit`/`push` feito por este processo no repositório real (o único commit real é o da Fase 5, dentro do projeto temporário isolado — esperado e correto).
- **Observação (não relacionada a esta bateria, não tratada):** durante a execução desta bateria, `git status` da raiz revelou modificações não-commitadas em arquivos de `orca-plan-orchestrator` (`agent_spawner.py`, `flight_plan.py`, `orchestrator_engine.py`, `test_agent_spawner.py`, mirrorados em 5 harnesses), `ecossistema.py` e `scripts/gestor_componentes.py` — nenhum desses arquivos foi tocado por qualquer comando desta bateria (nem de nenhuma das Baterias 2-5), e não estavam no `git status` inicial desta sessão. Indício de processo concorrente (outra sessão/agente) trabalhando no mesmo working directory. Não alterado nem revertido por mim — fora do escopo desta bateria, fica registrado para o usuário decidir.

## Resumo (8-10 linhas)

O pipeline completo de 8 fases do AIDD Generator funciona de ponta a ponta em Modo Delegado real: 8 requisições delegadas foram respondidas com conteúdo genuíno e funcional (não fake), cobrindo os 3 tipos exigidos (Fase 2, um dos 5 subagentes da Fase 3, e a implementação real da Fase 8). Exit code real do pipeline: 0. Score de auto-crítica real: 88/100. O projeto gerado tem estrutura real, commit git real, SQLite real, e 9/9 testes reais passando — confirmados de forma independente, não só pela leitura do log do pipeline. A suíte pytest de `tools/aidd-generator` (770 testes) não teve regressão. Dois achados reais relevantes: (1) o fallback de `referencias_utilizadas` em `02_analisador.py` está estruturalmente inalcançável dado o formato real que a Fase 1 produz — recomendado corrigir; (2) `verificar_gates.py`, ao rodar `G_HARNESS_COMPAT`, pode sobrescrever `HARNESS-COMPAT.json` do repositório real com uma conclusão incorreta por causa de um timeout de autoteste (5s) menor que o timeout real do protocolo (30-60s) — revertido nesta sessão. Veredito final: **PASSOU**.
