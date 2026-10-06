# Convenção Canônica de Códigos de Saída (Exit Codes) e Saída Estruturada

> **Status:** Ativo / Obrigatório (Lei Canônica #1, #2 e #6)  
> **Referência:** Governança AIDD e Determinismo de Execução  
> **Última atualização:** 2026-10-05  

---

## 1. Princípio Fundamental: Controle de Fluxo Binário e Semântico

Em ambientes de desenvolvimento orientado por IA (AIDD), agentes e orquestradores automatizados **nunca devem depender de heurísticas ou expressões regulares sobre texto livre** para saber se uma operação foi bem-sucedida ou onde ela falhou.

1. **Exit Code controla o fluxo de decisão** (avançar, bloquear, corrigir argumentos, alertar ambiente).
2. **Payload JSON em stdout detalha o diagnóstico** (código de erro interno, mensagem humana, arquivo afetado, diff sugerido).
3. **Stderr é reservado para logs humanos, avisos de runtime ou rastros de exceção imprevistos**.

---

## 2. Taxonomia Canônica Universal de Códigos de Saída

Para preservar total compatibilidade com POSIX (intervalo de 0 a 255) e evitar colisões com sinais reservados do shell (126+), o ecossistema AIDD adota estritamente **6 classes semânticas universais**:

| Código | Nome Canônico | Significado Prático | Ação Esperada do Agente / Harness |
| :---: | :--- | :--- | :--- |
| **0** | `SUCCESS` | Execução concluída com sucesso e conformidade plena. | Prosseguir para a próxima etapa do pipeline. |
| **1** | `RULE_VIOLATION` | Violação de regra de negócio, qualidade, invariante ou Quality Gate. | Bloquear pipeline; analisar causas no JSON e corrigir o código. |
| **2** | `INVALID_USAGE` | Argumento de linha de comando inválido, flag ausente ou sintaxe CLI incorreta. | Corrigir a invocação do comando sem alterar o código de produção. |
| **3** | `ENVIRONMENT_ERROR` | Dependência externa faltante, binário ausente no PATH ou serviço offline. | Provisionar pré-requisito ou alertar intervenção do desenvolvedor. |
| **4** | `IO_OR_TIMEOUT` | Timeout de execução, bloqueio de lock de arquivo (deadlock) ou falha de disco. | Reexecutar com backoff exponencial ou liberar locks travados. |
| **5** | `INTERNAL_BUG` | Exceção não tratada no próprio script/ferramenta (regressão de código do script). | Submeter o script ao ciclo de diagnóstico e reparo determinístico. |

---

## 3. Contrato de Saída Estruturada (Payload JSON)

Quando um script opera em modo determinístico ou de máquina (`--json` ou padrão de gate), o canal de saída padrão (`stdout`) DEVE emitir um JSON estruturado com o seguinte envelope canônico:

```json
{
  "status": "success | failure | error",
  "exit_code": 0,
  "reason_code": "VIOLACAO_INVARIANTE_LEI_X",
  "summary": "Descrição clara e objetiva do resultado em PT-BR simples.",
  "data": {
    "target": "caminho/do/arquivo.py",
    "details": []
  }
}
```

### Regras Estritas de Redirecionamento:
* **`stdout`**: Exclusivamente o payload JSON ou o veredito final limpo.
* **`stderr`**: Avisos contextuais (*warnings*), rastros de depuração e logs informativos.
* Nenhum caractere não-JSON pode preceder ou suceder o payload quando invocado em modo máquina.

---

## 4. Implementação de Referência

O módulo central em `scripts/exit_codes.py` disponibiliza o `Enum` tipado e métodos utilitários determinísticos (`emit_result`, `fail_rule`, `fail_usage`, `fail_env`).
