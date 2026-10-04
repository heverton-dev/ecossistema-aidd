# Estruturação dos Gates em 2 Níveis (Shift-Left)

> **Documento de Arquitetura de Qualidade:** Separação entre Micro-Gates locais por worktree e Macro-Gates globais pós-convergência.
> **Iniciativa:** Calibração do Pipeline AIDD (ciclo-01)
> **Data:** 2026-10-04

---

## 1. Visão Geral da Pirâmide de Gates

Para acelerar a esteira de desenvolvimento e evitar desperdício de tokens e ciclos de CPU, a validação de qualidade foi particionada em dois níveis estritos:

```
                  ▲
                 / \
                /   \     Nível 2: Macro-Gates Globais (54 gates)
               / 54  \    [Pós-Merge / Consolidação / Release]
              / GATES \   python ecossistema.py audit
             /---------\
            /  MICRO-   \ Nível 1: Micro-Gates de Worktree (Shift-Left)
           /   GATES     \[Isolamento por fatia / Pré-rebase / Instantâneo]
          /---------------\gates/micro_gates_worktree.py
```

---

## 2. Nível 1: Micro-Gates de Worktree (Shift-Left)

Executados de forma síncrona dentro da Git Worktree efêmera de cada fatia vertical (VSA), antes de qualquer tentativa de rebase ou integração na branch base:

| Ordem | Micro-Gate | O que valida | Tempo Médio |
|---|---|---|---|
| **1** | `verificar_sintaxe_python` | Compilação estrita via `py_compile` de todos os arquivos `.py` modificados pela fatia | < 0.1s |
| **2** | `verificar_stubs_fatia` | Varredura de strings proibidas pela Lei #5 (`TODO`, `FIXME`, `PLACEHOLDER`, `dummy`, `stub`) | < 0.2s |
| **3** | `comandos_teste` (Unit) | Testes unitários focados exclusivamente no escopo da fatia (ex: `pytest tests/slices/test_<slug>.py`) | 0.5s - 2.0s |
| **4** | `validar_fronteiras_fatia` | Garante que a fatia não modificou arquivos fora do seu escopo declarado | < 0.1s |

**Resultado:** Se qualquer micro-gate reprovar, a worktree é desmontada e o pipeline aborta antes de poluir a branch de consolidação.

---

## 3. Nível 2: Macro-Gates Globais (54 Gates)

Executados exclusivamente após a convergência de todas as fatias aprovadas na branch base e consolidação do Monólito Modular:

- Disparado via: `python ecossistema.py audit`
- Cobre: Integridade global, segredos fora da baseline, conformidade de contratos OpenAPI/MCP, drift arquitetural, hadolint, integridade de pacotes, etc.
- Garante integridade holística sem sobrecarregar cada micro-fatia individualmente.
