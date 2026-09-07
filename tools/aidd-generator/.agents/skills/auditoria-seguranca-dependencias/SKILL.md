# Skill: Auditoria Seguranca Dependencias v1.0

> Audita as dependencias declaradas em requirements.txt/requirements-dev.txt do projeto em busca de padroes de risco conhecidos (versoes nao fixadas, pacotes obsoletos, indicadores de CVEs publicamente divulgadas) e sugere acoes de mitigacao antes do deploy.

---

## 🎯 O que faz

Esta skill foi materializada pelo Injetor Universal de Componentes
(`scripts/core/injector/`) do aidd-generator. Ela cobre:

- Audita as dependencias declaradas em requirements.txt/requirements-dev.txt do projeto em busca de padroes de risco conhecidos (versoes nao fixadas, pacotes obsoletos, indicadores de CVEs publicamente divulgadas) e sugere acoes de mitigacao antes do deploy.

---

## 📋 Uso

### No Chat (Claude Code)

```
/auditoria-seguranca-dependencias
```

### No Terminal

```bash
python scripts/aidd_inject.py inspect skill auditoria-seguranca-dependencias
```

---

## 📦 Compatibilidade

- Claude Code ✅
- Qualquer harness compativel com `.claude/skills/` ✅

---

**Versao:** 1.0
**Gerado em:** 2026-09-03
**Status:** 🟢 PRONTO PARA USO
