# Arquitetura Agêntica de Auditoria e Evolução (The Audit Scaffold)

> **Governança:** Padrão Canônico para Auditoria e Evolução Contínua de Ferramentas no Ecossistema AIDD.  
> **Framework:** Lens 15-D (The Agentic Anatomical Matrix) + Pipeline 4F em Git Worktrees Efêmeras.

---

## 1. Topologia Estrutural

Toda ferramenta sob auditoria possui uma pasta exclusiva dentro de `docs/auditoria/<ferramenta-alvo>/`. Esta pasta atua como a memória persistente e o centro de comando de todas as 4 fases.

```text
docs/auditoria/
│
├── CONFIG-EXECUCAO-USUARIO.json     <-- SOBERANIA DO USUÁRIO: Harnesses, modelos e comandos
├── PLANO-MESTRE-AUDITORIA.md        <-- MATRIZ DE GOVERNANÇA: Catálogo e progresso geral
├── TEMPLATE-AUDITORIA-FERRAMENTA.md <-- LENS 15-D: Modelo formal das 15 dimensões
│
└── <ferramenta-alvo>/               <-- PASTA EXCLUSIVA DA FERRAMENTA (Ex: aidd-melhoria)
    ├── DOD.md                       <-- Critérios estáticos de "Pronto" (Definition of Done)
    ├── MANIFESTO-4F.json            <-- Manifesto de orquestração do pipeline de auditoria
    │
    ├── PROMPT-FASE-1-INSPETOR.txt   <-- Input parametrizado do Inspetor
    ├── LAUDO-15D-INICIAL.md         <-- Output gerado pelo Inspetor (Fase 1)
    │
    ├── PLANO-EVOLUCAO.md            <-- Output do Arquiteto: decomposição em tickets (Fase 2)
    ├── PLANO-EVOLUCAO.json          <-- Pipeline gerado automaticamente a partir dos tickets
    │
    ├── PROMPT-FASE-4-RETORNO.txt    <-- Input parametrizado do Inspetor de Retorno
    ├── LAUDO-15D-REVISADO.md        <-- Output do Retorno com Honestidade de Rótulo (Fase 4)
    │
    ├── G_auditoria_15D.py           <-- Quality Gate determinístico (EXIT 0 / EXIT 1)
    ├── RESUMO-USUARIO.md            <-- Resumo executivo ("Na Festa")
    └── RELATORIO-TECNICO.md         <-- Rastreabilidade técnica ("Na Casa")
```

---

## 2. As Duas Engrenagens Dinâmicas

### Engrenagem A: Soberania do Usuário (`CONFIG-EXECUCAO-USUARIO.json`)
As ferramentas e agentes **não escolhem seus próprios modelos**. O documento `CONFIG-EXECUCAO-USUARIO.json` na raiz de `docs/auditoria/` define:
- `harness_padrao` e `model_padrao`
- Perfis específicos por papel (`inspetor`, `arquiteto`, `construtor`, `retorno`)
- Comandos de terminal com flags de segurança (ex: `--dangerously-skip-permissions`, `--chrome`)

Ao alterar uma linha neste arquivo, **todos os pipelines (tanto o de auditoria quanto os de evolução) se adaptam automaticamente**, sem edição manual de manifestos JSON.

### Engrenagem B: O Compilador de Planos (`compilador_plano_evolucao.py`)
O Arquiteto (Fase 2) gera o documento textual `PLANO-EVOLUCAO.md`. O compilador determinístico:
1. Extrai cada ticket usando regex estruturado.
2. Mapeia as variáveis estáticas: `nome`, `dimensao_15d`, `input_prompt` e `output_handoff`.
3. Injeta as variáveis dinâmicas de `CONFIG-EXECUCAO-USUARIO.json`.
4. Emite o `PLANO-EVOLUCAO.json` pronto para execução pelo orquestrador.

---

## 3. Matriz Operacional dos 4 Estágios

| Estágio Agêntico | Entradas (Inputs) | O que Processa | Saídas (Outputs) |
| :--- | :--- | :--- | :--- |
| **0. Scaffolder (CLI)** | Nome da ferramenta + `SKILL.md` | Cria o chassi da pasta | `DOD.md`, `PROMPT-*.txt`, `MANIFESTO-4F.json` |
| **1. Inspetor** | `TEMPLATE-AUDITORIA-FERRAMENTA.md` + código | Diagnóstico Lens 15-D | `LAUDO-15D-INICIAL.md` |
| **2. Arquiteto** | `LAUDO-15D-INICIAL.md` + `DOD.md` | Planejamento tático de tickets | `PLANO-EVOLUCAO.md` e `PLANO-EVOLUCAO.json` |
| **3. Construtor** | `PLANO-EVOLUCAO.json` (fase a fase) | TDD em Git Worktree efêmera | Código em `scripts/` e testes em `tests/` |
| **4. Retorno** | `LAUDO-15D-INICIAL.md` + código alterado | Re-auditoria e validação DoD | `LAUDO-15D-REVISADO.md` + `G_auditoria_15D.py` (EXIT 0) |
| **5. Fechamento** | Todos os artefatos gerados | Consolidação de resultados | `RESUMO-USUARIO.md` e `RELATORIO-TECNICO.md` |

---

## 4. Comandos Canônicos do Sistema

**Criar scaffold para uma nova ferramenta:**
```bash
python scripts/scaffold_auditoria.py <nome-da-ferramenta>
```

**Executar pipeline de auditoria 4F:**
```bash
python scripts/orquestrador_4f.py --manifest docs/auditoria/<nome-da-ferramenta>/MANIFESTO-4F.json
```

**Compilar plano textual para pipeline executável:**
```bash
python scripts/compilador_plano_evolucao.py --plano docs/auditoria/<nome-da-ferramenta>/PLANO-EVOLUCAO.md
```

**Executar plano de evolução da ferramenta:**
```bash
python scripts/orquestrador_4f.py --manifest docs/auditoria/<nome-da-ferramenta>/PLANO-EVOLUCAO.json
```
