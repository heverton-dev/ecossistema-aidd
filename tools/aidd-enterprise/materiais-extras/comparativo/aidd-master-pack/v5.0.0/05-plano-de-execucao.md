# O Manifesto de Plano de Execução (`PLANO-EXECUCAO-ESTRUTURADO.json`) — AIDD Master Pack

> **Tag/versão documentada:** `v5.0.0`
> **Fonte primária:** função `cmd_plan()` em `scripts/aidd.py`, extraída via `git archive v5.0.0` — é o único código desta tag que efetivamente escreve o arquivo `PLANO-EXECUCAO-ESTRUTURADO.json`.

---

## O que é este arquivo

`PLANO-EXECUCAO-ESTRUTURADO.json` é o **manifesto de máquina** gerado na Fase 1.5 do ciclo de vida (ver `ciclo-de-vida.md`), no momento em que o usuário pede a criação de um projeto em linguagem natural ou via `aidd.py plan "<prompt>"`. Ele é escrito ao lado do documento legível `SPEC-ARQUITETURA.md`, dentro do diretório de destino recém-criado (`app_<módulos>-suite/`), e serve a dois propósitos:

1. **Contrato de aprovação:** representa o que foi entendido do pedido do usuário, com status inicial `"PLANEJADO"`, antes de qualquer código ser gerado.
2. **Entrada determinística da Fase 2:** o comando `aidd.py apply --dir <pasta>` lê exclusivamente este JSON (não relê o prompt original nem o `SPEC-ARQUITETURA.md`) para saber qual `suite_name` e quais `módulos` compor.

---

## Estrutura real gerada por esta tag

Com base no código-fonte de `cmd_plan()` nesta tag, o arquivo é gravado com exatamente este formato:

```json
{
  "projeto": {
    "nome": "Crm Erp Faturamento Suite",
    "slug": "crm-erp-faturamento-suite",
    "diretorio": "C:/.../app_crm-erp-faturamento-suite",
    "status": "PLANEJADO",
    "prompt_origem": "Crie um CRM e ERP de faturamento",
    "zero_api_key_mode": true,
    "modulos": ["crm", "erp", "faturamento"]
  },
  "arquitetura": {
    "padrao": "AIDD Modular Clean Architecture",
    "banco": "SQLite WAL",
    "mcp_enabled": true
  }
}
```

### Campo a campo

| Campo | Tipo | Significado |
| :--- | :--- | :--- |
| `projeto.nome` | string | Título legível da suíte, derivado dos módulos detectados (ex.: `"Crm Erp Faturamento Suite"`), capitalizando cada palavra. |
| `projeto.slug` | string | Versão em slug (`kebab-case`) do nome, usada para nomear a pasta de destino (`app_<slug>`). |
| `projeto.diretorio` | string | Caminho absoluto do diretório onde o projeto será/foi composto. |
| `projeto.status` | string | Máquina de estados simples do manifesto: começa em `"PLANEJADO"` (gerado pela Fase 1.5, aguardando aprovação humana). O código desta tag não escreve automaticamente um status posterior como `"CONCLUIDO"` neste mesmo campo — o resultado da composição é registrado, em vez disso, no relatório separado `RELATORIO-AUDITORIA.json` produzido por `aidd audit --report`. |
| `projeto.prompt_origem` | string | O texto exato em linguagem natural que originou o plano — preserva rastreabilidade do pedido do usuário. |
| `projeto.zero_api_key_mode` | boolean | Sinaliza que o projeto foi planejado para operar sem exigir nenhuma chave de API paga (alinhado ao princípio de "Zero Fricção" do pacote). |
| `projeto.modulos` | array de strings | Lista de slugs de domínio detectados no prompt (ex.: `crm`, `erp`, `faturamento`) — é esta lista que `aidd.py apply` repassa para `compose_suite()`. |
| `arquitetura.padrao` | string | Fixo em `"AIDD Modular Clean Architecture"` nesta tag — identifica o estilo arquitetural aplicado (fatias verticais desacopladas). |
| `arquitetura.banco` | string | Fixo em `"SQLite WAL"` nesta tag — reflete o motor de persistência padrão. Mesmo quando o parâmetro `--db postgres` existe em `aidd.py compose`, o manifesto gerado por `cmd_plan()` não parametriza esse valor; ele é sempre `"SQLite WAL"` neste ponto do fluxo. |
| `arquitetura.mcp_enabled` | boolean | Fixo em `true` — todo projeto composto por esta tag expõe servidor MCP nativo em `/mcp`. |

---

## Como o manifesto é consumido depois de criado

- **`aidd.py apply --dir <pasta>`:** abre o JSON, lê `projeto.nome` e `projeto.modulos`, e chama `compose_suite(target_dir, suite_name, modulos)` — é o gatilho real da Fase 2 (scaffolding + 7 gates).
- **`aidd.py heal --dir <pasta>`:** relê o mesmo JSON para saber quais módulos recompor em caso de auto-remediação.
- **`aidd.py status --dir <pasta>`:** lê `projeto.nome`, `projeto.versao` (se presente) e `projeto.status` para exibir um resumo de saúde do projeto — note que o manifesto gerado por `cmd_plan()` nesta tag **não inclui** um campo `versao`; esse campo aparece em manifestos manuais/históricos de outros exemplos do repositório, não no gerador atual.
- **`aidd.py export-frontend` / `scaffold-infra`:** ambos leem `projeto.nome` do manifesto (com fallback para um nome genérico caso o arquivo não exista) apenas para rotular a saída gerada — não dependem da lista de módulos do manifesto para funcionar.

---

## Nota sobre variações encontradas nos exemplos do repositório

A pasta `examples/` desta tag contém suítes de referência com arquivos `PLANO-EXECUCAO-ESTRUTURADO.json` que usam um formato **mais rico e diferente** do gerado por `cmd_plan()` — por exemplo, com campos como `fases` (lista de etapas com `id`, `status`, `mesa_orca`, `expected_outputs`), `modulos_instalados`, `versao`, `dual_database`, `docker_ready`. Isso indica que esses exemplos foram compostos manualmente ou por uma versão/fluxo diferente do gerador, e **não** refletem o schema que o código de `cmd_plan()` desta tag produz automaticamente. Para efeitos de "o que esta versão gera quando usada normalmente", o schema de referência é o descrito na seção anterior (`projeto` + `arquitetura`, sem `fases`).

---

## Relação com o `SPEC-ARQUITETURA.md`

O manifesto JSON é deliberadamente enxuto (metadados de máquina); o detalhamento legível por humanos — casos de uso, rotas REST previstas, ferramentas MCP, requisitos de UI/acessibilidade — fica em `SPEC-ARQUITETURA.md`, gerado no mesmo momento e no mesmo diretório. Os dois arquivos formam, juntos, o "SPEC Gate" da Fase 1.5: o JSON é o que a máquina executa; o Markdown é o que a pessoa aprova.

---

*Estrutura descrita a partir da leitura direta da função `cmd_plan()` em `scripts/aidd.py`, extraído via `git archive v5.0.0` deste repositório.*
