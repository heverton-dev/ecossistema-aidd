# Análise Técnica Profunda: Arquitetura e Engenharia do AIDD Forge

> **Versão:** 1.0.0 (Homologada em Produção)  
> **Público:** Engenheiros de Software, Arquitetos de Soluções e Especialistas em Sistemas Autônomos de IA.

---

## 1. Topologia da Arquitetura

O **AIDD Forge** foi desenhado sob o princípio de **Desacoplamento Determinístico**: 95% das operações de configuração, cópia, verificação de sintaxe e governança rodam em Python puro local com **custo zero de LLM**. A inteligência artificial opera exclusivamente nas pontas cognitivas necessárias via subagentes efêmeros descartáveis.

```
                                AIDD FORGE CORE
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
   DISCOVERY & HOST              PHASE FENCING &              QUALITY GATES &
     ORCHESTRATION                  GOVERNANCE                  ENFORCEMENT
  ───────────────────          ────────────────────          ─────────────────
  • detector.py                • phase_fencer.py             • 7 Gates Determinísticos
  • orca_bridge.py             • injector.py                 • git_hooks.py (pre-commit)
  • slash_router.py            • token_optimizer.py          • subagent_purger.py (AST)
  • setup.bat / setup.sh       • context_linter.py           • Result Monad Pattern
```

---

## 2. Módulos Centrais e Responsabilidades

### 2.1. `SubagentPurger` (`aidd_forge/core/subagent_purger.py`)
- **Problema resolvido:** O acúmulo infinito de contexto em sessões longas de IA ("context pollution") causa alucinações, esquecimento de diretrizes e explosão de custos de tokens.
- **Implementação:**
  - `run(prompt, output_path)`: impõe teto de 4.000 caracteres (~1.000 tokens) antes de chamar qualquer função do agente.
  - Recebe o código gerado em memória, submete a análise sintática estrita com `ast.parse`.
  - Se houver falha sintática (`SyntaxError`), a sessão é abortada, nenhum arquivo inválido toca o disco e retorna `Result.fail`.
  - Se válido, grava o artefato em disco UTF-8 e invoca `_purge()` que desliga imediatamente a sessão do subagente.

### 2.2. `HostDetector` & `OrcaBridge` (`detector.py` e `orca_bridge.py`)
- **Problema resolvido:** Fragilidade em ambientes heterogêneos onde desenvolvedores possuem ferramentas diferentes instaladas.
- **Implementação:**
  - `shutil.which` silencioso: nunca levanta exceções nem escreve ruídos no terminal ao pesquisar por `claude`, `codex`, `agy`, `cursor` e `ollama`.
  - Fallback determinístico: `single_agent_isolated` gera configurações para que todos os papéis operem no único harness ativo em worktrees git isoladas.
  - Suporte a override explícito via parâmetro ou variável de ambiente `ORCA_DEFAULT_HARNESS`.

### 2.3. `PhaseFencer` (`phase_fencer.py`)
- **Problema resolvido:** Regras de 20 páginas enviadas para agentes executando tarefas simples desperdiçam milhares de tokens a cada mensagem.
- **Implementação:**
  - Provisiona `.aidd/pipeline/phase_XX/` com arquivos cirúrgicos: `AGENTS.md` de ~380 tokens e `mcp_config.json` contendo apenas os servidores MCP necessários para a tarefa atual.

### 2.4. `TokenOptimizer` & `ContextLinter` (`token_optimizer.py` e `context_linter.py`)
- **Problema resolvido:** Desperdício de vocabulário BPE e crescimento descontrolado de arquivos de prompt.
- **Implementação:**
  - Tríade Caveman Ultra: injeta blocos idempotentes padronizando regras em inglês enxuto, raciocínio interno telegráfico e código/saída final em PT-BR.
  - Linter estático com heurística conservadora de 4 caracteres por token, emitindo alerta caso qualquer arquivo de regra ultrapasse 1.500 tokens.

---

## 3. Padrão Arquitetural Result Monad

Em todo o core do AIDD Forge, é proibido lançar exceções não tratadas para fluxos operacionais normais. Todo resultado adota o padrão:

```python
@dataclass(frozen=True)
class Result(Generic[T]):
    value: T | None
    error: str | None

    @property
    def is_ok(self) -> bool:
        return self.error is None
```
Isso garante composição segura, previsibilidade determinística e facilidade de testes unitários com 100% de cobertura.
