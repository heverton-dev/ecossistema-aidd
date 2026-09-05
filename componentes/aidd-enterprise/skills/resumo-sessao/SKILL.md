---
name: resumo-sessao
description: Registra e exporta todo o histórico factual da sessão de chat em um documento Markdown estruturado na pasta `secoes/`, contendo telemetria de tokens, horários, harness, resumo executivo e histórico completo de User Inputs e Model Outputs.
commands:
  - "/resumo-sessao"
---

# Skill: /resumo-sessao — Registrador Universal de Sessão Agêntica

Esta skill é **agnóstica a qualquer harness** (Antigravity, Claude Code, Cursor, Gemini CLI, OpenCode, MimoCode, Codex) e tem como objetivo gerar um rastro permanente e auditável de tudo o que foi conversado, decidido e executado durante a sessão de trabalho.

---

## 1. Gatilho de Ativação

A skill é disparada quando o usuário digitar no chat:
* `/resumo-sessao`
* Ou comandos em linguagem natural equivalentes como: *"salve o resumo desta sessão"*, *"registre a sessão atual"*, *"gere o histórico desta conversa"*.

---

## 2. Padrão de Nomenclatura e Diretório de Destino

1. **Diretório:** Criar a pasta `secoes/` na raiz do projeto em execução (caso ainda não exista).
2. **Template do Arquivo:**
   ```
   secoes/<dd-mm-yyyy>-<harness-name>_<llm>_<name>.md
   ```
   * `<dd-mm-yyyy>`: Data da sessão (ex: `03-09-2026`).
   * `<harness-name>`: Nome do ambiente/harness em execução (ex: `antigravity`, `claude-code`, `cursor`, `opencode`).
   * `<llm>`: Nome do modelo de linguagem utilizado (ex: `gemini-3.8-flash`, `claude-3-7-sonnet`, `gpt-4o`).
   * `<name>`: Slug descritivo do objetivo central da sessão em minúsculas com hifens (ex: `analise-comparativa-e-planos-aidd`).

---

## 3. Estrutura Obrigatória do Documento Gerado

Todo documento gerado por esta skill **DEVE** seguir rigorosamente a seguinte anatomia:

### A. Cabeçalho e Título Principal
```markdown
# Registro Completo de Sessão: [Nome do Tópico / Objetivo da Sessão]

> **Documento Gerado via Comando:** `/resumo-sessao`  
> **Template:** `<dd-mm-yyyy>-<harness-name>_<llm>_<name>.md`
```

### B. Tabela de Metadados e Telemetria (Mandatória no Topo)
Imediatamente abaixo do título, gerar a tabela factual:

```markdown
## 📊 Metadados de Execução e Telemetria da Sessão

| Métrica / Parâmetro | Valor Registrado |
| :--- | :--- |
| **Harness Utilizado** | `<nome do harness em uso>` |
| **Modelo de Linguagem (LLM)** | `<nome do modelo>` |
| **Horário de Início da Sessão** | `<DD/MM/AAAA HH:MM:SS>` |
| **Horário de Término da Sessão** | `<DD/MM/AAAA HH:MM:SS>` |
| **Duração Total da Sessão** | `<HHh MMmin SSs>` |
| **Tokens de Entrada (Input Tokens)** | `<quantidade de tokens de input>` |
| **Tokens de Saída (Output Tokens)** | `<quantidade de tokens de output>` |
| **Total de Tokens Utilizados** | `<quantidade total de tokens>` |
| **Caminho do Projeto Executado** | `<caminho absoluto da pasta do projeto>` |
```

### C. Resumo Executivo da Sessão
Um texto estruturado respondendo com clareza matemática a 3 perguntas essenciais:
1. **O Que Fizemos:** Lista detalhada dos diagnósticos, códigos criados, análises e decisões tomadas.
2. **Por Que Fizemos:** A motivação de negócio ou de engenharia (problemas resolvidos, gargalos eliminados).
3. **Como Fizemos:** As técnicas, padrões de projeto (Design Patterns), comandos CLI e metodologias aplicadas.

### D. Histórico Cronológico Factual (Input & Output)
Seção dividida por interações cronológicas sequenciais (Interação 1, 2, ... N), documentando:
* **User Input:** A solicitação exata feita pelo usuário (sem cortes do sentido original).
* **Model Output:** A resposta, análise, diffs de código e ações concretas realizadas pelo agente.

### E. Estrutura Consolidada dos Artefatos Gerados
Diagrama em árvore mostrando todos os arquivos criados ou modificados durante a sessão com links clicáveis.

---

## 4. Instruções de Coleta de Métricas para Agentes

1. **Tokens:** Utilize os dados de telemetria da sessão atual fornecidos pelo harness (cabeçalhos de `usage`, contadores de sessão ou estimativas baseadas na contagem de caracteres/BPE quando a API for opaca).
2. **Horários:** Colete o timestamp da primeira mensagem do usuário como início e o timestamp atual do comando `/resumo-sessao` como término.
3. **Encoding:** O arquivo deve ser salvo obrigatoriamente com codificação **UTF-8** para preservar acentuações e formatações Markdown.
