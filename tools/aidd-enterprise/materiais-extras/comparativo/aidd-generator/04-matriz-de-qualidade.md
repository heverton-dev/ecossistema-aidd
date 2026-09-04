# Matriz Atômica de Qualidade — aidd-generator (v2.1 / Commit `7d63085`)

## 1. Critérios de Qualidade por Camada de Entrega

### A. Camada de Contratos e Schemas (`schemas/*.json`)
- **Conformidade de Especificação:** Schemas declarados no padrão JSON Schema Draft 2020-12 com campos `$schema`, `title`, `type`, `properties` e `required`.
- **Tipagem Estrita sem Campos Amparados:** Proibição de propriedades anônimas sem validação (`additionalProperties: false` onde aplicável).
- **Consistência de Tipos:** Validação cruzada com a biblioteca `jsonschema` de Python; nenhuma entidade pode ser scaffoldada sem o respectivo schema validado.
- **Gate Validador:** `03_designer.py`, `05_criador.py` e testes em `tests/test_schemas.py`.

---

### B. Camada de Segurança e Proteção de Segredos (`scripts/gates/G_BLOQUEAR_SEGREDOS.py`)
- **Varredura Atômica Pré-Commit:** Inspeção recursiva em todos os arquivos de código (`.py`, `.json`, `.yml`, `.env`, `.md`) em busca de credenciais reais.
- **Padrões Detectados:** Chaves de API (`sk-`, `ghp_`, `xoxb-`, etc.), tokens JWT, pares de credenciais e certificados privados.
- **Isolamento de Ambiente:** O arquivo `.env` com chaves reais é expressamente ignorado pelo `.gitignore` e protegido contra commit acidental.
- **Gate Validador:** `G_BLOQUEAR_SEGREDOS.py` (retorna `exit 1` imediato se encontrar qualquer padrão suspeito).

---

### C. Camada de Compatibilidade Multi-Harness (`scripts/gates/G_HARNESS_COMPAT.py`)
- **Agnosticismo de Agentes:** Suporte aos principais ambientes de execução (Claude Code, Gemini CLI, Codex, OpenCode, MimoCode, Antigravity).
- **Fonte Única de Verdade:** Documentos mestres de governança (`AGENTS.md`, `AGENTS-WORKFLOW.md`, `HARNESS-COMPAT.json`) mantidos sem duplicação de regras.
- **Preservação de Symlinks e Links Relativos:** Compatibilidade testada em Windows, Linux e macOS sem quebra de referências de diretório.
- **Gate Validador:** `G_HARNESS_COMPAT.py` e `AUDITAR_COMPARATIVO_HARNESS.py`.

---

### D. Camada de Determinismo Mecânico e AST (`scripts/phases/05_criador.py` e `tests/`)
- **Zero Token Mecânico:** Toda a montagem de pastas, arquivos de configuração, manifestos e esqueletos de código roda sem invocar LLMs.
- **Validação Sintática por AST:** Todo script Python criado passa por compilação sintática estática (`ast.parse()`) antes de ser persistido em disco.
- **Proibição de Falsos Sucessos:** Nenhum teste pode conter `pytest.skip()` não justificado ou asserções triviais (`assert True`).
- **Gate Validador:** Suíte interna de testes unitários (`tests/test_compilador.py` e `tests/test_fases.py`).

---

### E. Camada de Implementação Funcional e Resiliência de Testes (`scripts/phases/08_implementador.py`)
- **Geração de Testes com Execução Real:** Cada script de funcionalidade recebe um arquivo de testes correspondente em `tests/`.
- **Loop de Auto-Correção:** Se a suíte de testes falhar na primeira execução, o erro é capturado e enviado ao LLM para correção cirúrgica por até N tentativas configuráveis.
- **Transparência Factual de Resultado:** Se os testes não passarem após o limite de tentativas, a falha é declarada honestamente (`status: "FALHOU"`, `requer_intervencao_manual: true`) no arquivo `_phase_08_index.json`, sem mascaramento de dados.
- **Gate Validador:** Execução real do `pytest` com relatório consolidado de asserções.

---

### F. Camada de Transparência e Rastreabilidade de Tokens (`.aidd/LEI-FUNDAMENTAL-TRANSPARENCIA.md`)
- **Rastreamento Factual de Custos:** Contagem real de tokens de prompt e conclusão via cabeçalho `usage` da resposta da API (zero números fabricados).
- **Logs Estruturados por Fase:** Cada fase concluída grava um índice JSON com timestamp, modelo utilizado, duração em segundos e status.
- **Auditoria de Produção:** Relatórios transparentes documentando acertos, taxas reais de sucesso e limitações conhecidas (`docs/AUDITORIA-PRODUCAO-*.md`).

---

## 2. Tabela Consolidada de Quality Gates do aidd-generator

| Gate | Objetivo | Tipo | Critério de Aprovação |
| :--- | :--- | :---: | :--- |
| `G_VERIFICAR_LLM_PRONTO` | Assegura que o provedor LLM está configurado ou que o modo delegado está apto. | Pré-voo | Provedor e chave válidos ou flag de delegação ativa. |
| `G_BLOQUEAR_SEGREDOS` | Impede vazamento acidental de chaves e credenciais em arquivos rastreados. | Segurança | Zero correspondências de padrões de segredos no código. |
| `G_HARNESS_COMPAT` | Valida integridade das configurações multi-agente e symlinks. | Compatibilidade | Arquivos essenciais presentes e alinhados ao schema. |
| `GATE_SCHEMAS` | Valida sintaxe e contratos de todos os JSON Schemas gerados. | Contratos | Validação com `Draft202012Validator` sem erros. |
| `GATE_AST` | Verifica se os scripts Python gerados possuem sintaxe compilável. | Mecânico | `ast.parse()` bem-sucedido em 100% dos scripts. |
| `GATE_TESTES_REAIS` | Executa a suíte de testes unitários do projeto via pytest. | Funcional | 100% dos testes passando sem falhas nem skips forçados. |
