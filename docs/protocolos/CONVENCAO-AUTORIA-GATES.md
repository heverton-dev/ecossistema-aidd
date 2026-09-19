# Convenção Canônica de Autoria e Validação de Quality Gates

> **Status:** Ativo / Obrigatório (Lei Canônica #1 e #8)  
> **Referência:** `docs/issues/11-todo-portao-precisa-provar-que-morde.md`  
> **Última atualização:** 2026-09-19

---

## 1. Princípio Fundamental: "Todo Portão Precisa Provar que Morde"

Um Quality Gate só conta como fiscalização e proteção real do ecossistema a partir do momento em que um **teste determinístico prova que ele falha (exit 1)** quando a condição que ele deveria proteger é violada.

> **Regra Canônica de Autoria de Gates:**  
> **Todo gate DEVE ser acompanhado de teste automatizado que deliberadamente quebra a condição resguardada e asserte `exit 1` (reprovação).**  
> **Testes de caminho feliz (que apenas afirmam `exit 0`) NÃO satisfazem este requisito e são insuficientes por definição.**

Gates que aprovam independentemente do estado do sistema são meras fachadas cosméticas (*vibe enforcement*). Qualquer gate que não possa ser levado a reprovar sob violação real ou sintética comprovada é uma fachada, devendo ser rebaixado em suas afirmações (Lei Canônica #8 — Honestidade de Rótulo).

---

## 2. Requisitos Técnicos para Novos Gates

Ao adicionar ou atualizar qualquer script de gate em `gates/G_*.py`:

1. **Par de Teste Obrigatório:** Deve existir um arquivo de teste espelhado em `gates/test_g_<nome_minusculo>.py`.
2. **Cenário de Falha Obrigatório:** O arquivo de teste DEVE conter pelo menos uma função `test_*_detecta_*` ou `test_*_reprova_*` que:
   - Quebra a invariante protegida (em repositório ou árvore de arquivos sintética isolada, ex: `tmp_path`).
   - Executa o gate e captura o código de retorno.
   - Asserta categoricamente `returncode == 1` e a presença da mensagem descritiva de erro no stdout/stderr.
3. **Cenário de Sucesso Real:** O arquivo de teste deve validar também que no estado íntegro o gate retorna `returncode == 0` (exit 0).
4. **Execução Fidedigna via Hook:** A reprodução e validação do gate devem refletir a execução real do framework `pre-commit` (`pre-commit run --hook-stage manual <id> --all-files`), evitando desvios introduzidos por proxies ou runners intermediários.
5. **Captura Direta de Exit Code:** A captura do código de saída deve ser imediata na mesma linha do comando (`$LASTEXITCODE` ou `returncode`), nunca mascarada através de pipes.
6. **Humildade e Honestidade de Saída:** Mensagens de log de sucesso não podem alegar "zero risco" ou "100% à prova de falhas" se a inspeção se resume a heurísticas de texto ou AST parcial.

---

## 3. Classificação de Falhas e Fachadas

Se um gate existente ou proposto:
- Não reprova mesmo quando o componente protegido está deliberadamente corrompido;
- Possui verificações puramente declarativas que não impedem a execução de processos não conformes;
- Emite reivindicações de segurança desproporcionais à sua mecânica de teste:

O agente **NÃO DEVE** maquiar a situação. Deve:
1. Registrar imediatamente o diagnóstico de fachada no inventário de auditoria.
2. Rebaixar o claim no print do gate (substituir "zero risco" ou "garantia absoluta" pelo escopo real inspecionado).
3. Abrir ou atualizar o plano de aprofundamento do gate.
