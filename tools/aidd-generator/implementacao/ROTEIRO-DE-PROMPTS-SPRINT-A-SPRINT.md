# 🚀 Roteiro de Implementação Sprint a Sprint: aidd-generator (Elevação para Nota 10.0+)

> **Projeto:** `aidd-generator`  
> **Diretório:** `C:\Users\trcnologia\Desktop\aidd-generator\aidd-generator`  
> **Documento de Referência:** `01-plano-elevacao-aidd-generator-nota-10.md`  
> **Instruções:** Envie **um prompt por vez** ao agente. Só passe para a próxima Sprint após o agente confirmar que os testes da sprint atual foram executados e passaram com aprovação.

---

## 📋 Sumário das Sprints

| Sprint | Foco Principal | Arquivos Chave |
| :---: | :--- | :--- |
| **01** | Engine de Subagentes Efêmeros com Descarte Imediato de Contexto | `scripts/core/subagent_purger.py`, refatoração da chamada LLM |
| **02** | Auto-Descoberta Dinâmica de Frota & Fallback Universal no ORCA ADE | `scripts/core/detector.py`, `scripts/core/orca_fleet.py` |
| **03** | Reestruturação Granular por Fase (Micro-Ambientes de Fases) | `scripts/phases/phase_01/` a `phase_08/` com `AGENTS.md` dedicado |
| **04** | Camada Zero Fricção (Slash Commands, Intent Router, Bat/Sh) | `scripts/commands/slash_gen.py`, `iniciar.bat`, `iniciar.sh` |
| **05** | Protocolo Tríplice Caveman Ultra nos Prompts das Fases | Refatoração de prompts em `scripts/phases/` (Input EN / CoT / PT-BR) |
| **06** | Reestruturação da Fase 8 em Micro-Tasks AST com Result Pattern | `scripts/phases/phase_08_implementador.py`, auto-cura com `post-mortem` |
| **07** | Implementação do Gate I3 e Gate de Cibersegurança OWASP | `scripts/gates/G_INTEGRACAO_CROSS_SCRIPT.py`, `G_CYBERSECURITY.py` |

---

## 🟢 SPRINT 01: Engine de Subagentes Efêmeros com Descarte Imediato de Contexto

### Prompt para enviar ao agente:
```text
Estamos iniciando o plano de elevação do aidd-generator para Nota 10.0+ com base em '01-plano-elevacao-aidd-generator-nota-10.md'.
Execute EXCLUSIVAMENTE a SPRINT 01:

1. Implemente 'scripts/core/subagent_purger.py':
   - Responsável por instanciar subagentes com contexto estritamente isolado (< 1.000 tokens) para tarefas cognitivas de síntese de código.
   - Assim que o subagente gera o arquivo e ele é validado sintaticamente via 'ast.parse', a sessão do subagente é destruída imediatamente.
   - Retorno estruturado usando o padrão Result Monad ('Result.ok(caminho)' / 'Result.fail(motivo)').

2. Refatore a camada de chamada LLM em 'scripts/core/llm_router.py' para utilizar o 'subagent_purger' em vez de sessões cumulativas de chat.
3. Crie testes unitários em 'tests/unit/test_subagent_purger.py'.
4. Execute o pytest e garanta aprovação total.
```

### Validação & Commit:
```powershell
pytest tests/unit/test_subagent_purger.py -v
git add .
git commit -m "feat(gen-sprint-01): engine de subagentes efemeros com descarte imediato de contexto"
```

---

## 🟢 SPRINT 02: Auto-Descoberta de Frota & Fallback Universal no ORCA ADE

### Prompt para enviar ao agente:
```text
Siga estritamente o plano '01-plano-elevacao-aidd-generator-nota-10.md'.
Execute EXCLUSIVAMENTE a SPRINT 02:

1. Implemente 'scripts/core/detector.py':
   - Detecta as ferramentas instaladas no host de forma silenciosa ('claude', 'codex', 'agy', 'cursor', 'ollama').
   - Detecta a presença do ORCA ADE no sistema.

2. Implemente 'scripts/core/orca_fleet.py':
   - Gera dinamicamente o arquivo '.orca/01_orca_inventory.json' com as ferramentas reais do host.
   - Aplica fallback em cascata: se o usuário tiver apenas 1 agente (ex: Antigravity), todos os workers operam nele em worktrees separadas sem falhar.
   - Permite override via variável de ambiente 'ORCA_DEFAULT_HARNESS'.

3. Crie testes em 'tests/unit/test_orca_fleet.py'.
4. Execute o pytest e garanta que todos os testes passem.
```

### Validação & Commit:
```powershell
pytest tests/unit/test_orca_fleet.py -v
git add .
git commit -m "feat(gen-sprint-02): auto-descoberta dinamica de frota e fallback universal orca"
```

---

## 🟢 SPRINT 03: Reestruturação Granular por Fase (Micro-Ambientes de Fases)

### Prompt para enviar ao agente:
```text
Siga estritamente o plano '01-plano-elevacao-aidd-generator-nota-10.md'.
Execute EXCLUSIVAMENTE a SPRINT 03:

1. Reestruture a pasta 'scripts/phases/' em micro-ambientes granulares:
   - 'scripts/phases/phase_01_pesquisa/': AGENTS.md enxuto + Filesystem MCP.
   - 'scripts/phases/phase_02_analisador/': AGENTS.md + regras de negócio.
   - 'scripts/phases/phase_03_designer/': AGENTS.md + Schemas Draft 2020-12.
   - 'scripts/phases/phase_04_planejador/': AGENTS.md + divisão de tarefas.
   - 'scripts/phases/phase_05_criador/': AGENTS.md + linter AST.
   - 'scripts/phases/phase_08_implementador/': AGENTS.md + Result Monad e pytest.

2. Atualize 'scripts/pipeline_completo.py' para carregar dinamicamente apenas o micro-ambiente da fase em execução, reduzindo o consumo de tokens em mais de 65%.
3. Crie testes em 'tests/unit/test_phase_isolation.py'.
4. Execute o pytest e valide a aprovação.
```

### Validação & Commit:
```powershell
pytest tests/unit/test_phase_isolation.py -v
git add .
git commit -m "feat(gen-sprint-03): reestruturacao granular de fases em micro-ambientes com context fencing"
```

---

## 🟢 SPRINT 04: Camada Zero Fricção (Slash Commands, Intent Router, Bat/Sh)

### Prompt para enviar ao agente:
```text
Siga estritamente o plano '01-plano-elevacao-aidd-generator-nota-10.md'.
Execute EXCLUSIVAMENTE a SPRINT 04:

1. Implemente 'scripts/commands/slash_gen.py':
   - Mapeia o comando '/generate <ideia>' e '/aidd-gen <ideia>' para os comandos das IDEs.
   - Adiciona Intent Router no 'AGENTS.md' ("crie um sistema de [X]" dispara o gerador automaticamente).

2. Crie os scripts de 1-Clique na raiz do repositório:
   - 'iniciar.bat' (Windows): executa o servidor web Flask em 'localhost:5000' ou o pipeline silencioso, abrindo o navegador automaticamente.
   - 'iniciar.sh' (Linux/Mac): equivalente bash para Unix.

3. Crie testes em 'tests/unit/test_slash_gen.py'.
4. Execute o pytest e garanta aprovação total.
```

### Validação & Commit:
```powershell
pytest tests/unit/test_slash_gen.py -v
git add .
git commit -m "feat(gen-sprint-04): interface zero friccao com slash commands e executaveis de 1-clique"
```

---

## 🟢 SPRINT 05: Protocolo Tríplice Caveman Ultra nos Prompts das Fases

### Prompt para enviar ao agente:
```text
Siga estritamente o plano '01-plano-elevacao-aidd-generator-nota-10.md'.
Execute EXCLUSIVAMENTE a SPRINT 05:

1. Refatore todos os prompts de sistema e templates em 'scripts/phases/':
   - ENTRADA: System Prompts e instruções operacionais estritamente em Inglês (economia de 30-50% BPE).
   - PROCESSAMENTO: Forçar CoT telegráfico em English Caveman (3 a 5 linhas densas sem artigos).
   - SAÍDA: Resposta, artefatos, código e logs em Português do Brasil (PT-BR) com clareza técnica absoluta.

2. Crie linter estático 'scripts/core/caveman_linter.py' que valida se os prompts seguem essa tríade.
3. Crie testes em 'tests/unit/test_caveman_prompts.py'.
4. Execute o pytest e garanta aprovação.
```

### Validação & Commit:
```powershell
pytest tests/unit/test_caveman_prompts.py -v
git add .
git commit -m "feat(gen-sprint-05): padronizacao formal da triade caveman ultra nos prompts"
```

---

## 🟢 SPRINT 06: Reestruturação da Fase 8 em Micro-Tasks AST com Result Pattern

### Prompt para enviar ao agente:
```text
Siga estritamente o plano '01-plano-elevacao-aidd-generator-nota-10.md'.
Execute EXCLUSIVAMENTE a SPRINT 06:

1. Refatore completamente 'scripts/phases/08_implementador.py' (e sua versão em 'phase_08_implementador/'):
   - Substitua a geração de código monolítico por decomposição em Micro-Tasks AST: uma função por vez.
   - Imponha o padrão Result Monad ('Result.ok' / 'Result.fail') em todas as funções geradas, eliminando exceções não tratadas (Zero 500).
   - Integre o loop de auto-cura da skill 'post-mortem': se o pytest falhar, dispara investigação 5-Porquês, isola o traceback e regenera apenas a função com falha em worktree limpa.
   - Eleve a taxa de sucesso factual da Fase 8 para 100% de aprovação comprovada.

2. Crie testes abrangentes em 'tests/unit/test_phase_08_microtasks.py'.
3. Execute o pytest e valide aprovação de 100%.
```

### Validação & Commit:
```powershell
pytest tests/unit/test_phase_08_microtasks.py -v
git add .
git commit -m "feat(gen-sprint-06): fase 8 com micro-tasks ast, result monad e auto-cura post-mortem"
```

---

## 🟢 SPRINT 07: Implementação do Gate I3 e Gate de Cibersegurança OWASP

### Prompt para enviar ao agente:
```text
Siga estritamente o plano '01-plano-elevacao-aidd-generator-nota-10.md'.
Execute EXCLUSIVAMENTE a SPRINT 07 (Sprint Final):

1. Implemente 'scripts/gates/G_INTEGRACAO_CROSS_SCRIPT.py' (Gate I3):
   - Executa testes automatizados de ponta a ponta validando a compatibilidade entre scripts irmãos gerados pelo pipeline (ex: cliente consumindo a API gerada).
   - Falha com 'exit 1' se houver divergência de tipos ou contratos.

2. Implemente 'scripts/gates/G_CYBERSECURITY_OWASP.py':
   - Varre o código gerado em busca de injeções SQL, vulnerabilidades de autenticação, IDOR e credenciais hardcoded.
   - Falha com 'exit 1' em vulnerabilidades de severidade Alta ou Crítica.

3. Atualize o validador 'scripts/verificar_gates.py' para incluir o Gate I3 e o Gate de Cibersegurança.
4. Execute toda a suíte de testes com 'pytest' e garanta 100% de aprovação.
```

### Validação & Commit:
```powershell
pytest tests/ -v
python scripts/verificar_gates.py
git add .
git commit -m "feat(gen-sprint-07): gate I3 de integracao cross-script e gate de ciberseguranca owasp"
```

---

> **Parabéns!** Ao concluir a Sprint 07, o `aidd-generator` estará formalmente elevado para **Nota 10.0+**, com estabilidade industrial e zero alucinação.
