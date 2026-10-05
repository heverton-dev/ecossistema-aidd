# Plano de Execução e Esteira de Delivery: AIDD Forge

> **Versão:** 1.0.0  
> **Objetivo:** Roteiro operacional para engenheiros e agentes de IA executarem projetos sob a governança do AIDD Forge.

---

## 1. Como Iniciar um Projeto com o AIDD Forge

Existem três portas de entrada com experiência zero fricção:

### Opção A — Executável de 1-Clique (Recomendada para Usuários)
1. Navegue até a raiz do repositório onde deseja aplicar a governança.
2. Dê duplo clique em `setup.bat` (Windows) ou execute `./setup.sh` (Linux/Mac).
3. O terminal executa em segundo plano e exibe o feedback visual verde `[OK]`.

### Opção B — Disparo por Chat / Slash Command (Recomendada para IDEs)
No chat do seu agente favorito (Cursor, Claude Code, Antigravity):
```text
/forge
```
ou em linguagem natural:
```text
Por favor, prepare o ambiente e configure este projeto com AIDD Forge.
```

### Opção C — CLI Python para Automações e CI/CD
```bash
pip install -e .
python -m aidd_forge.cli init /caminho/do/projeto [--force]
```

---

## 2. A Esteira Operacional Passo a Passo

```
 [1. BOOTSTRAP] ──────► python -m aidd_forge.cli init
        │
        ▼
 [2. REGRAS] ─────────► Injeção de AGENTS.md, .agent/skills/ e .aidd/pipeline/
        │
        ▼
 [3. FROTA] ──────────► detector.py descobre ferramentas e gera orca_config
        │
        ▼
 [4. EXECUÇÃO] ───────► Subagentes efêmeros geram fatias com Context-Purge
        │
        ▼
 [5. VALIDAÇÃO] ──────► 7 Quality Gates inspecionam o código no pre-commit
        │
        ▼
 [6. COMMIT] ─────────► Git commit homologado com 100% de integridade
```

---

## 3. Gestão de Falhas e Auto-Cura

Caso um subagente produza código defeituoso:
1. O validador AST rejeita a alteração antes da gravação em disco.
2. O erro é devolvido via `Result.fail(motivo)`.
3. Um novo subagente limpo é acionado pontualmente com o motivo do erro no prompt para corrigir o artefato.
4. Nenhuma conversa longa é estendida: cada tentativa opera com contexto zerado.
