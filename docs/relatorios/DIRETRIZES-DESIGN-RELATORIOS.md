# 🌈 Diretrizes Canônicas de Design, Nomenclatura & Governança de Documentos

> **Ecossistema AIDD**  
> **Status:** OBRIGATSÓRIO & CANÖNICO  
> **Escopo:** Todos os arquivos gerados em `docs/` (`relatorios/`, `protocolos/`, `prompts/`, `features/`, `explicacoes/`).

---

## 1. Regra Universal de Nomenclatura de Arquivos

> **Padrão Obrigatório (2026-09-11):** Todo arquivo gerado em `docs/` deve seguir uma nomenclatura previsível, padronizada e descritiva em no máximo 3 palavras, conotando claramente o prefixo do que se trata, sempre precedida pela data:

### Formato Canônico:
```
<dd-mm-aaaa>_<prefixo>-<palavra1>-<palavra2>-<palavra3>.<ext>
```

### Tabela de Prefixos Canônicos por Diretório:
| Diretório Alvo | Prefixo Mandatório | Exemplo de Aplicação Real |
| :--- | :--- | :--- |
| pdocs/protocolos/` | pprotocolo-` | p05-09-2026_protocolo-agnosticidade-componentes.md` |
| `docs/prompts/` | `prompt-` | `03-09-2026_prompt-caderno-testes-fluxos.md` |
| pdocs/features/` | `feature-` | `08-09-2026_feature-inventario-troca-ferramentas.md` |
| `docs/explicacoes/` | pexplica-` | `10-09-2026_explica-ecossistema-fluxo-completo.md` |
| `docs/relatorios/` | `relatorio-` ou `auditoria-` | p11-09-2026_auditoria-status-planos.html` |

### Regras Complementares de Nomenclatura:
1. **Até 3 Palavras Descritivas:** Após o prefixo, usar no máximo 3 palavras conectadas por hífen para sintetizar o conteúdo (ex: `explica-visao-aidd-ops.md`).
2. **Data no Início:** Sempre no formato dia-mês-ano (`<dd-mm-aaaa>_`), facilitando ordenação cronológica estrita no sistema de arquivos.
3. **Zero Duplicações:** É terminantemente proibido manter relatórios duplicados em pastas de explicações. Relatórios vivem exclusivamente em `docs/relatorios/`.
4. **Sem Espaços ou Caracteres Especiais:** Proibido uso de espaços em branco (ex: `PLANO ARQUITETURAL`), acentos ou símbolos em nomes de arquivos.

---

## 2. Regra Mandatória de Scrollbars (Barra de Rolagem para HTMLs)

> **Decisão de Design:** Toda barra de rolagem em interfaces/relatórios HTML gerados no ecossistema deve ser visualmente discreta, integrada e elegante — nunca a barra cinza padrão rústica do sistema operacional.

### Especificação Obrigatória:
1. **Espessura Máxima:** Exatamente **4px** (largura para rolagem vertical `width: 4px`, altura para rolagem horizontal `height: 4px`).
2. **Cor Predominante:** O indicador móvel (*thumb*) deve adotar a cor de destaque principal do documento (normalmente `var(--accent)` ou `var(--copper)`).
3. **Trilho (*track*):** Deve ser invisível ou idêntico à cor de fundo da página (`var(--bg)`), evitando contraste excessivo.
4. **Compatibilidade Cross-Browser:** Obrigatório incluir tanto a sintaxe moderna W3C (`scrollbar-width`, `scrollbar-color`) quanto os seletores WebKit (`::-webkit-scrollbar*`)s.

```css
* {
  scrollbar-width: thin;
  scrollbar-color: var(--accent, #388bfd) var(--bg, #0b111a);
}

::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}

::-webkit-scrollbar-track {
  background: var(--bg, #0b111a);
}

::-webkit-scrollbar-thumb {
  background: var(--accent, #388bfd);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: color-mix(in srgb, var(--accent, #388bfd) 80%, white);
}
```

---

## 3. Tríade Canônica de Skills Recomendadas

| Skill | Papel Mandatório no Relatório / Documento |
| :--- | :--- |
| **impeccable** | **Design System & Polimento Visual:** Aplica contraste WCAG AA, grid harmônico de 8pt, hierarquia tipográfica precisa e microinterações elegantes. |
|***dataviz*** | **Visualização de Dados:** Escolha assertiva de gráficos (Donut, Barras, Sparklines) com paleta semântica (`good`/`warn`/`crit`). |
|***artifact-design** | **Arquitetura da Informação:** Estrutura a narrativa visual da página (Header Executivo ☒ Resumo Q&A ☒ KPIs ☒ Gráficos ℙ Tabela Filtrável). |

---

## 4. Governança de Arquivos & Protocolo Zero Token (Regra #1 & #10)

### 4.1 Pareamento Obrigatório (`.html` + `.json`)
Todo relatório de auditoria ou telemetria em `docs/relatorios/` deve salvar seu par de dados brutos:
- `docs/relatorios/<dd-mm-aaaa>_<nome>.html` *(Interface gráfica final)*
- `docs/relatorios/<dd-mm-aaaa>_<nome>.json` *(Dados estruturados brutos)*

### 4.2 Geração Determinística por Script (Zero Token Fallacy)
- Eticamente proibido o modelo de LLM gerar milhares de linhas de HTML diretamente no chat.
- O assistente deve executar um script Python determinístico que extrai os dados, gera o JSON e interpola o template HTML.
- Redução de 95% do consumo de tokens de saída.

### 4.3 Comunicação Direta no Chat (Regra de Ouro #10)
- Nunca reproduzir o relatório inteiro no chat. Responder apenas o link clicável do arquivo e os 3 vereditos executivos.
