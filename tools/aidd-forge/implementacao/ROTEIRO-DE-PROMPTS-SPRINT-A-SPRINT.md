# 🚀 Roteiro de Implementação Sprint a Sprint: AIDD Forge

> **Projeto:** `AIDD Forge`  
> **Diretório:** `C:\Users\trcnologia\Desktop\aidd-forge`  
> **Documento de Referência:** `03-plano-arquitetura-aidd-forge-nota-10.md`  
> **Instruções:** Envie **um prompt por vez** ao agente. Só passe para a próxima Sprint após o agente confirmar que os testes da sprint atual foram executados e passaram com aprovação.

---

## 📋 Sumário das Sprints

| Sprint | Foco Principal | Arquivos Chave |
| :---: | :--- | :--- |
| **01** | Estrutura Base & Engine de Subagentes com Descarte de Contexto | `aidd_forge/__init__.py`, `cli.py`, `core/subagent_purger.py` |
| **02** | Auto-Descoberta Dinâmica de Frota & Fallback no ORCA ADE | `core/detector.py`, `core/orca_bridge.py`, templates orca |
| **03** | Modularização Granular por Fase (Phase Fencer) | `core/phase_fencer.py`, templates de micro-fases 00 a 04 |
| **04** | Interface Zero Fricção (Slash Router, Bat/Sh, Intent Router) | `commands/slash_router.py`, `setup.bat`, `setup.sh`, `AGENTS.md` |
| **05** | Protocolo Tríplice Caveman Ultra de Economia de Tokens | `core/token_optimizer.py`, gerador de regras de economia |
| **06** | Injeção das 6 Skills Físicas Especializadas | `.skills/` com os 6 SKILL.md oficiais injetáveis |
| **07** | Blindagem de 7 Quality Gates Mecânicos & Cibersegurança | `gates/` com AST, contratos, pytest e auditoria OWASP |

---

## 🟢 SPRINT 01: Estrutura Base & Engine de Subagentes com Descarte de Contexto

### Prompt para enviar ao agente:
```text
Estamos iniciando a implementação do AIDD Forge com base no arquivo '03-plano-arquitetura-aidd-forge-nota-10.md'.
Execute EXCLUSIVAMENTE a SPRINT 01:

1. Crie a estrutura básica do pacote Python 'aidd_forge/':
   - 'aidd_forge/__init__.py' (com __version__ = "1.0.0")
   - 'aidd_forge/cli.py' (entrypoint básico com argparse / click para o comando 'init')
   - 'setup.py' para instalação local via 'pip install -e .'

2. Implemente o motor de subagentes efêmeros em 'aidd_forge/core/subagent_purger.py':
   - Classe 'SubagentPurger': instancia um subagente com prompt enxuto (< 1.000 tokens), captura o artefato gerado, valida via AST ('ast.parse') e destrói imediatamente o contexto/sessão do subagente após salvar em disco.
   - Padrão Result Monad para retorno ('Result.ok(artefato)' / 'Result.fail(erro)').

3. Crie os testes unitários em 'tests/unit/test_subagent_purger.py' e 'tests/unit/test_cli.py'.
4. Execute o pytest e garanta 100% de aprovação antes de finalizar.
```

### Validação & Commit:
```powershell
pytest tests/unit/test_subagent_purger.py tests/unit/test_cli.py -v
git add .
git commit -m "feat(forge-sprint-01): estrutura base e engine de subagentes com descarte de contexto"
```

---

## 🟢 SPRINT 02: Auto-Descoberta Dinâmica de Frota & Fallback no ORCA ADE

### Prompt para enviar ao agente:
```text
Siga estritamente o plano '03-plano-arquitetura-aidd-forge-nota-10.md'.
Execute EXCLUSIVAMENTE a SPRINT 02:

1. Implemente 'aidd_forge/core/detector.py':
   - Detecta o Sistema Operacional (Windows/Linux/Mac).
   - Detecta a frota de ferramentas instaladas no host: executa busca silenciosa ('which' / 'Get-Command') por 'claude', 'codex', 'agy', 'cursor', 'ollama'.
   - Detecta se o ORCA ADE está presente no sistema.

2. Implemente 'aidd_forge/core/orca_bridge.py':
   - Gera dinamicamente o arquivo '01_orca_inventory.json' contendo APENAS as ferramentas realmente existentes na máquina.
   - Gera '02_routing_rules.json' com fallback em cascata: se o usuário tiver apenas 1 agente (ex: Antigravity), todos os workers do Orca operam nele em worktrees separadas sem dar erro.
   - Suporta override via variável de ambiente 'ORCA_DEFAULT_HARNESS'.

3. Crie os templates em 'aidd_forge/templates/orca/' e testes em 'tests/unit/test_detector_orca.py'.
4. Execute o pytest e garanta que todos os testes passem.
```

### Validação & Commit:
```powershell
pytest tests/unit/test_detector_orca.py -v
git add .
git commit -m "feat(forge-sprint-02): auto-descoberta dinamica de frota e fallback orca ade"
```

---

## 🟢 SPRINT 03: Modularização Granular por Fase (Phase Fencer)

### Prompt para enviar ao agente:
```text
Siga estritamente o plano '03-plano-arquitetura-aidd-forge-nota-10.md'.
Execute EXCLUSIVAMENTE a SPRINT 03:

1. Implemente 'aidd_forge/core/phase_fencer.py':
   - Responsável por provisionar a árvore de micro-ambientes granulares no projeto de destino sob '.aidd/pipeline/'.
   - Cada fase recebe seu próprio 'AGENTS.md' cirúrgico (~380 tokens) e seu 'mcp_config.json' exclusivo.

2. Crie os templates em 'aidd_forge/templates/pipeline_phases/':
   - 'phase_00_bootstrap/': diagnóstico de hardware e git.
   - 'phase_01_requirements/': escopo e regras (apenas Filesystem MCP).
   - 'phase_02_architecture/': schemas Draft 2020-12 (Schemas MCP).
   - 'phase_03_implementation/': Result Monad, pytest (Database MCP).
   - 'phase_04_audit_security/': auditoria OWASP Top 10.

3. Crie os testes em 'tests/unit/test_phase_fencer.py'.
4. Execute o pytest e garanta 100% de aprovação.
```

### Validação & Commit:
```powershell
pytest tests/unit/test_phase_fencer.py -v
git add .
git commit -m "feat(forge-sprint-03): phase fencer e micro-ambientes granulares de pipeline"
```

---

## 🟢 SPRINT 04: Interface Humana Zero Fricção

### Prompt para enviar ao agente:
```text
Siga estritamente o plano '03-plano-arquitetura-aidd-forge-nota-10.md'.
Execute EXCLUSIVAMENTE a SPRINT 04:

1. Implemente 'aidd_forge/commands/slash_router.py':
   - Mapeia o Slash Command '/forge' (e '/aidd-init') para as pastas de comandos das IDEs ('.cursor/rules/', '.claude/commands/', '.agent/commands/').
   - Injeta a seção de Intent Router em Linguagem Natural no template 'AGENTS.md' ("se usuário disser 'configure este projeto' -> dispara o setup").

2. Crie os executáveis de 1-Clique na raiz:
   - 'setup.bat' (Windows): executa 'python -m aidd_forge.cli init' sem exibir erros feios e emite mensagem amigável com saída em verde.
   - 'setup.sh' (Linux/Mac): script bash equivalente com permissão de execução.

3. Crie os testes em 'tests/unit/test_slash_router.py'.
4. Execute o pytest e garanta aprovação total.
```

### Validação & Commit:
```powershell
pytest tests/unit/test_slash_router.py -v
git add .
git commit -m "feat(forge-sprint-04): interface zero friccao com slash commands e executaveis de 1-clique"
```

---

## 🟢 SPRINT 05: Protocolo Tríplice Caveman Ultra de Economia de Tokens

### Prompt para enviar ao agente:
```text
Siga estritamente o plano '03-plano-arquitetura-aidd-forge-nota-10.md'.
Execute EXCLUSIVAMENTE a SPRINT 05:

1. Implemente 'aidd_forge/core/token_optimizer.py':
   - Injeta nos templates de governança a regra obrigatória da Tríade Caveman Ultra:
     * ENTRADA: System prompts e regras em Inglês (30-50% economia BPE).
     * PROCESSAMENTO: Internal Thinking (CoT) em English Caveman telegráfico (3-5 linhas sem artigos).
     * SAÍDA: Resposta e código estritamente em Português do Brasil (PT-BR) de alta precisão.

2. Crie linter estático de contexto 'aidd_forge/core/context_linter.py':
   - Alerta quando arquivos de regras ultrapassarem 1.500 tokens.

3. Crie testes em 'tests/unit/test_token_optimizer.py'.
4. Execute o pytest e valide a aprovação.
```

### Validação & Commit:
```powershell
pytest tests/unit/test_token_optimizer.py -v
git add .
git commit -m "feat(forge-sprint-05): protocolo triplice caveman ultra e linter de tokens"
```

---

## 🟢 SPRINT 06: Injeção das 6 Skills Físicas Especializadas

### Prompt para enviar ao agente:
```text
Siga estritamente o plano '03-plano-arquitetura-aidd-forge-nota-10.md'.
Execute EXCLUSIVAMENTE a SPRINT 06:

1. Provisione os arquivos físicos completos das 6 Skills em 'aidd_forge/templates/skills/':
   - 'caveman-ultra/SKILL.md': Economia severa de tokens e CoT telegráfico.
   - 'orca-orchestration/SKILL.md': Orquestração multi-agente, worktrees e decision gates.
   - 'impeccable-ui/SKILL.md': Design System Tailwind Slate/Indigo, modais WCAG 2.1 e zero emojis.
   - 'open-code-review/SKILL.md': Linter de acoplamento e grafo de Clean Architecture.
   - 'post-mortem/SKILL.md': Investigação de causa-raiz com técnica dos 5-Porquês.
   - 'cybersecurity-audit/SKILL.md': Varredura estática de OWASP Top 10 (SQLi, IDOR, XSS).

2. Implemente o vinculador de skills no 'aidd_forge/core/injector.py' para salvar na pasta canônica '.agent/skills/' com symlinks automáticos.
3. Crie testes em 'tests/unit/test_skills_injection.py'.
4. Execute o pytest e garanta aprovação.
```

### Validação & Commit:
```powershell
pytest tests/unit/test_skills_injection.py -v
git add .
git commit -m "feat(forge-sprint-06): pacote fisico das 6 skills especializadas e injetor canonico"
```

---

## 🟢 SPRINT 07: Blindagem de 7 Quality Gates Mecânicos & Cibersegurança

### Prompt para enviar ao agente:
```text
Siga estritamente o plano '03-plano-arquitetura-aidd-forge-nota-10.md'.
Execute EXCLUSIVAMENTE a SPRINT 07 (Sprint Final):

1. Crie os 7 scripts de Quality Gates determinísticos em 'aidd_forge/templates/gates/':
   - 'G_BLOQUEAR_SEGREDOS.py': Bloqueia commits com chaves de API, senhas ou tokens expostos.
   - 'G_ESTRUTURA_AST.py': Valida sintaxe de todos os arquivos .py via 'ast.parse'.
   - 'G_HARNESS_COMPAT.py': Garante symlinks ativos entre .agent, .claude e .cursor.
   - 'G_CONTRACTS.py': Valida integridade e compatibilidade de Schemas JSON Draft 2020-12.
   - 'G_TESTES_REAIS.py': Executa a suíte do pytest e exige 100% de aprovação (Zero Fail).
   - 'G_CYBERSECURITY_OWASP.py': Varre vulnerabilidades estáticas de segurança.
   - 'G_PERFORMANCE.py': Checa latência de execução dos endpoints.

2. Crie o instalador de Git Hooks em 'aidd_forge/core/git_hooks.py' configurando o 'pre-commit' com bloqueio binário ('exit 0' / 'exit 1').
3. Crie a suíte completa de testes de integração em 'tests/integration/test_full_forge_pipeline.py'.
4. Execute toda a suíte de testes com 'pytest' e garanta 100% de aprovação.
```

### Validação & Commit:
```powershell
pytest tests/ -v
git add .
git commit -m "feat(forge-sprint-07): 7 quality gates mecanicos, ciberseguranca owasp e git hooks"
```

---

> **Parabéns!** Ao concluir a Sprint 07, o `AIDD Forge` estará 100% implementado com nota 10+ e pronto para uso em produção.
