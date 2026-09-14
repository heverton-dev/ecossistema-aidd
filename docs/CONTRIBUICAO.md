# Guia de Contribuição

> **Versão:** 1.0  
> **Última atualização:** 2026-09-14  
> **Escopo:** Como contribuir com gates, ferramentas, skills e componentes.

---

## 1. Regras Fundamentais

1. **Zero Stubs:** Todo código deve ser funcional, tipado e testado. Sem `pass`, sem mocks.
2. **Determinismo:** Tarefas mecânicas usam scripts. LLM apenas para cognição.
3. **Result Monad:** Operações retornam `Result.ok()` ou `Result.fail()`.
4. **AGENTS.md como fonte única:** Governança vive em `AGENTS.md` (raiz ou tool).

---

## 2. Adicionar um Quality Gate

### Local (por tool)

Crie o gate em `tools/<ferramenta>/scripts/gates/G_<NOME>.py`:

```python
from pathlib import Path

def scan(repo_root: Path) -> dict:
    """Retorna {'passed': bool, 'details': str}"""
    violations = []
    # ... lógica de verificação ...
    return {
        "passed": len(violations) == 0,
        "details": "\n".join(violations) if violations else "OK"
    }

if __name__ == "__main__":
    import sys
    result = scan(Path("."))
    print(result["details"])
    sys.exit(0 if result["passed"] else 1)
```

### Global (ecossistema)

Crie o gate em `gates/G_<NOME>.py` seguindo o mesmo padrão. Adicione ao `ecossistema.py` se necessário.

### Validação

```bash
# Gate local
python tools/<ferramenta>/scripts/gates/G_<NOME>.py

# Gate global
python gates/G_<NOME>.py

# Todos os gates
python ecossistema.py audit
```

---

## 3. Adicionar uma Skill

### Via CLI

```bash
python ecossistema.py dependencia add-skill \
  --nome <nome-da-skill> \
  --pacote <pacote-pip-ou-git> \
  --instalar "<comando-de-instalacao>" \
  --verificar "<comando-de-verificacao>"
```

### Manualmente

1. Crie `skills/<nome-da-skill>/SKILL.md` na tool ou no ecossistema
2. Adicione o frontmatter padronizado (1 linha em inglês)
3. Distribua para todos os harnesses via `components sync`

### Frontmatter Padrão

```yaml
---
name: <nome>
description: <descrição em inglês, 1 linha, ~15 palavras>
location: file:///caminho/para/SKILL.md
---
```

---

## 4. Adicionar um MCP Server

### Via CLI

```bash
python ecossistema.py dependencia add-mcp \
  --nome <nome> \
  --pacote <pacote> \
  --tipo stdio \
  --comando "<comando>" \
  --args "<args>" \
  --harnesses "claude-code,mimo"
```

### Registrando manualmente

Adicione a configuração no arquivo `.mcp.json` (ou equivalente do harness) do diretório alvo.

---

## 5. Adicionar um Componente Compartilhado

1. Coloque o código-fonte em `componentes/compartilhado/` (para código usado por Master e Enterprise)
2. Execute a sincronização:

```bash
python ecossistema.py components sync --tipo todos
python ecossistema.py components verify --tipo todos
```

3. Verifique que nenhum gate falhou:

```bash
python ecossistema.py audit
```

---

## 6. Estrutura de um Novo Módulo (Master)

Ao criar um módulo via `/master`, a estrutura segue Clean Architecture:

```
src/modules/<nome>/
├── domain/
│   ├── entities.py       ← Entidades de negócio
│   └── interfaces.py     ← Contratos
├── application/
│   └── use_cases.py      ← Casos de uso
├── infrastructure/
│   ├── database.py       ← SQL isolado
│   └── schema.py         ← Schema SQLite/PG
├── interfaces/
│   ├── routes.py         ← Rotas HTTP (finas)
│   └── schemas.py        ← Pydantic schemas
├── models.py             ← Fachada (imports do domain)
├── services.py           ← Fachada (Result Monad)
└── routes.py             ← Fachada (delega para interfaces/)
```

**Invariantes:**
- Zero imports cruzados entre módulos (comunicação via EventBus ou `src/core/`)
- Todos os services retornam `Result[T, E]`
- SQLite em modo WAL (`PRAGMA journal_mode=WAL;`)
- SQL com placeholders (`?`), zero concatenação

---

## 7. Checklist de Validação

Antes de submeter qualquer mudança:

```bash
# 1. Gates locais da ferramenta
pytest tools/<ferramenta>/tests/ -v

# 2. Gates globais
python ecossistema.py audit

# 3. Sincronização de componentes
python ecossistema.py components verify --tipo todos

# 4. Sem segredos
python gates/G_SEGREDOS.py
```

Todos devem retornar exit 0.

---

## 8. Convenções de Código

| Área | Padrão |
|:---|:---|
| Linguagem | Python puro (sem dependências nativas de SO) |
| Minimo | Python >= 3.10 |
| Testes | `pytest` com Arrange-Act-Assert |
| Erros | `Result[T, E]` (nunca `raise` em lógica de negócio) |
| SQL | Placeholders `?`, WAL mode, soft-delete |
| Commits | Mensagens concisas em PT-BR ou EN |
| Docs | Markdown, PT-BR (usuário) ou EN (governança) |
