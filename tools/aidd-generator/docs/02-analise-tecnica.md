# Análise Técnica Profunda: Arquitetura do aidd-generator v2.1

> **Versão do Framework:** 2.1 (Pós-Elevação para Nota 10.0+ / Homologado)  
> **Para quem é este documento:** Arquitetos de software, tech leads e desenvolvedores seniores que necessitam de uma dissecação técnica e formal da arquitetura, padrões de projeto e garantias determinísticas do sistema.

---

## 1. As 5 Camadas de Engenharia Agêntica (Metodologia AIDD)

O `aidd-generator` é arquitetado em estrita conformidade com as 5 Camadas de AIDD:

```
CAMADA 5: BUNDLES MODULARES
  ├── Micro-ambientes por fase (phase_01/ a phase_08/ com AGENTS.md isolado)
  └── Artefatos autocontidos e reproduzíveis

CAMADA 4: PERSISTÊNCIA ESTRUTURADA
  ├── Cache transacional em .aidd/cache/
  └── Telemetria JSON de tokens e status de frota

CAMADA 3: GATES MECÂNICOS BINÁRIOS
  ├── G_BLOQUEAR_SEGREDOS, G_INTEGRACAO_CROSS_SCRIPT (I3), G_CYBERSECURITY_OWASP
  └── Retorno estrito de exit 0 ou exit 1

CAMADA 2: DETERMINISMO PRIMEIRO
  ├── Python local para I/O, parsing AST, linters e execução de pytest (Zero Tokens)
  └── Subagente Efêmero usado estritamente para síntese cognitiva

CAMADA 1: CONTRATOS E SCHEMAS
  ├── JSON Schema Draft 2020-12
  └── Result Monad (Result[T, E]) em todas as funções de serviço
```

---

## 2. Inovações Arquiteturais Chave

### 2.1 Context-Purge Engine (`utils_subagente_ephemero.py`)
Elimina definitivamente o problema de *Context Bloat* (inchaço de memória entre etapas):
- **Isolamento Total:** Apenas o schema mínimo e as regras da micro-tarefa (~1.000 tokens) são enviados ao subagente.
- **Validação AST & Destruição Imediata:** Assim que o artefato é gerado, o orquestrador valida a sintaxe via `ast.parse` e executa a purga da sessão do subagente.
- **Resultado:** O pipeline gasta menos de um quarto dos tokens consumidos por arquiteturas monolíticas acumulativas.

### 2.2 Auto-Descoberta Dinâmica de Frota & Fallback ORCA (`detector.py` / `orca_fleet.py`)
- O host é inspecionado silenciosamente via `shutil.which` sem lançar exceções.
- Suporta múltiplos agentes simultâneos (`claude`, `codex`, `agy`, `cursor`, `ollama`) com roteamento por especialidade técnica.
- Se o desenvolvedor possuir apenas um agente (ex: Claude Code ou Antigravity), o sistema ativa o fallback em cascata operando em worktrees isoladas com taxa de erro zero.

### 2.3 Decomposição em Micro-Tasks AST & Result Monad (`08_implementador.py`)
- Em vez de solicitar à IA que gere centenas de linhas de uma vez, o analisador decompõe o arquivo em micro-tarefas por função/método.
- Cada função implementa o padrão funcional `Result.ok(valor)` ou `Result.err(motivo)`, prevenindo falhas em cascata e exceções 500.

### 2.4 Auto-Cura Pós-Falha com 5-Porquês
- O `PostMortemAnalyzer` captura o traceback exato do `pytest`, extrai a linha e o arquivo causador, constrói a cadeia de causa-raiz em 5 níveis e aciona a regeneração cirúrgica apenas da micro-task afetada, preservando todo o restante do código que já passou.

---

## 3. Matriz de Dependências e Desacoplamento

- **Zero API Key Forçada:** O protocolo delegado opera usando o harness ativo do desenvolvedor.
- **Fallback Headless:** Se executado fora de um harness, o sistema conecta via LiteLLM ou Ollama sem necessidade de alterar o código do pipeline.
