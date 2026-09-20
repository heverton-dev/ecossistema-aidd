# Item 2 — Avaliar e dividir AGENTS.md em núcleo obrigatório vs seções sob demanda

> **Escopo:** Formalização e registro canônico da arquitetura de particionamento do `AGENTS.md` em Núcleo Obrigatório (operações constantes, leis invioláveis, tríade canônica e restrições de execução) vs Seções Sob Demanda (detalhamentos de ferramentas, tabelas exaustivas de gates, histórico de decisões e catálogo de skills/MCPs em `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`).
> **Status:** CONCLUÍDO
> **Nota Atual (0-10):** 8 — evidência: medição real determinística de redução de tokens via `Measure-Object` e aprovação em 21 testes reais de gates (`test_g_lei_declara_portao.py`, `test_g_harness_compat.py`, `test_g_ecossistema_integridade.py`).
> **Nota Alvo (0-10):** 8
> **Nota Real (pós-implementação):** 8

---

## 1. Arquitetura da Divisão (Operação "Laminated Sheet vs Binder")

O particionamento segue o modelo mental do manual de operações: a folha plastificada fixada na parede contém o que é consultado a cada turno; a pasta no arquivo guarda as especificações e tabelas de referência consultadas sob demanda.

### 1.1 O que permanece no Núcleo Obrigatório (`AGENTS.md`)
O núcleo reside na raiz e é injetado/lido no contexto inicial de todo assistente (Claude, Gemini, Antigravity, Cursor, Qoder, CodeBuddy):

1. **Header & Protocolo de Referência:** Identificação canônica do repositório e link imediato para a referência completa.
2. **§1. Core Execution Constraints:** Restrições operacionais ativas a todo turno (Thinking em inglês compacto, limite de passos, Regra 10 de formato de saída, proibição de stubs/rewrites totais, regra de bash e docs ingestion).
3. **§2. Inviolable Laws:** 100% das 13 Leis Invioláveis do ecossistema, cada uma acompanhada de sua declaração explícita de portão verificador (auditada deterministicamente pelo gate `gates/G_LEI_DECLARA_PORTAO.py`). Nenhuma regra de governança se torna sob demanda.
4. **§3. The 3 Canonical Creation Flows (A Tríade Canônica):** Definição obrigatória dos três fluxos (`aidd-pure`, `aidd-open`, `aidd-freedom`), interoperabilidade universal de Slash Commands e funil de convergência mandatória.
5. **§4. Architecture & Context Dispatch:** Matriz canônica de roteamento por pasta de ferramenta para busca sob demanda (`tools/aidd-*/AGENTS.md`).
6. **§5 e §6. Sumários de Acesso:** Diretiva do knowledge graph (`code-review-graph`) e índice sintético das Skills Procedimentais de Engenharia.

### 1.2 O que se torna Sob Demanda (`docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md` e subsistemas)
Conteúdos consultados somente quando uma tarefa específica do domínio é acionada:

1. **Catálogo Exaustivo de Gates (§4):** Descrição detalhada dos mais de 25 quality gates, flags manuais vs pre-commit e regras históricas de quarentena (`G_SEGREDOS`).
2. **Tabelas de Parâmetros e CLI de Slash Commands (§3):** Flags, contratos de entrada/saída, regras internas do app ORCA e equivalentes CLI completos.
3. **Convenções de Nomenclatura e Design (§4.1 e §4.2):** Diretrizes de código bilíngue (PT-BR domínio / EN-US técnico) e especificações W3C de scrollbar para relatórios HTML.
4. **Compatibilidade Multi-Harness Física (§5):** Detalhamento de diretórios de cada harness (`.claude`, `.opencode`, `.mimocode`, `.gemini`, `.cursor`, `.agents`), matriz de fallback e comandos de trust.
5. **Matriz Detalhada de Ferramentas MCP (§MCP):** Tabela de ferramentas específicas do `code-review-graph` (`detect_changes_tool`, `get_impact_radius_tool`, etc.).
6. **Manuais de Ferramentas Específicas:** Detalhes de subprojetos alocados em `tools/<ferramenta>/AGENTS.md`.

---

## 2. Justificativa Seção por Seção

| Seção | Destino | Justificativa |
| :--- | :--- | :--- |
| **Header & Metadados** | Núcleo (`AGENTS.md`) | Fornece proveniência, padrão de governança e ponteiro direto para carregamento sob demanda. |
| **Core Constraints (§1)** | Núcleo (`AGENTS.md`) | Invariantes de comportamento do modelo a cada turno (Regra 10, formatação, economia de contexto). |
| **Inviolable Laws (§2)** | Núcleo (`AGENTS.md`) | Governança suprema. `G_LEI_DECLARA_PORTAO.py` audita a presença física de todas as 13 leis e portões no núcleo. |
| **Tríade Canônica (§3)** | Núcleo (`AGENTS.md`) | Roteador mestre de criação de projetos; indispensável para entender a arquitetura do ecossistema. |
| **Context Dispatch (§4)** | Núcleo (`AGENTS.md`) | Roteamento mecânico que ensina o assistente a buscar os arquivos específicos de cada ferramenta. |
| **Sumário Graph & Skills (§5, §6)** | Núcleo (`AGENTS.md`) | Alertas de primeiro contato (usar graph antes de grep; usar skills de engenharia anti-vibe). |
| **Tabela Completa de Gates** | Sob Demanda (`AGENTS-REFERENCIA-COMPLETA.md#4`) | Lista exaustiva consome ~1.200 tokens; agentes só precisam dela quando executam auditoria ou depuram gate. |
| **Tabelas de Parâmetros Slash Commands** | Sob Demanda (`AGENTS-REFERENCIA-COMPLETA.md#3`) | Documentação de sintaxe e subcomandos necessária apenas no momento da execução do comando. |
| **Convenções de Código e Design HTML** | Sob Demanda (`AGENTS-REFERENCIA-COMPLETA.md#41`, `#42`) | Regras de estilização e CSS consumidas apenas ao gerar código de domínio ou relatórios visuais. |
| **Matriz Física de Harnesses** | Sob Demanda (`AGENTS-REFERENCIA-COMPLETA.md#5`) | Mecanismo de cópia física gerenciado via `ecossistema.py components sync`; assistente só consulta para diagnosticar harness. |
| **Tabela Extensa MCP Graph** | Sob Demanda (`AGENTS-REFERENCIA-COMPLETA.md#mcp`) | Esquemas de ferramentas já estão disponíveis nativamente via protocolo MCP / tool declarations. |

---

## 3. Mecanismo Real de Carregamento Sob Demanda

A divisão não é um corte arbitrário sem roteamento; opera por quatro mecanismos determinísticos:

1. **Ponteiro de Cabeçalho Explícito:** O `AGENTS.md` declara na linha 5: `> **Full Reference:** docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`. Todo assistente sabe o caminho exato para buscar detalhes aprofundados.
2. **Ingestão Sob Demanda Determinística por Gates:** O gate `gates/G_HARNESS_COMPAT.py` (linhas 114-118) extrai via regex todos os arquivos markdown referenciados em `AGENTS.md` (`re.findall(r"\`(docs/[\w./-]+\.md)\`", agents_md)`) e os ingere programaticamente para auditar a cobertura total de gates sem exigir que todos estejam no arquivo principal.
3. **Dispatch Arquitetural por Domínio:** A seção `## 4. Architecture & Context Dispatch` direciona qualquer alteração contextual para o `AGENTS.md` específico da ferramenta (`tools/<ferramenta>/AGENTS.md`).
4. **Skills Procedimentais Autocontidas:** Cada comando procedimental remete ao seu próprio `SKILL.md` em `componentes/compartilhado/skills/<skill>/SKILL.md`, carregado pelo harness somente quando a skill correspondente é ativada.

---

## 4. Medição Quantitativa (Antes vs Depois)

Medições realizadas diretamente no repositório git (`Measure-Object`):

| Métrica | Monólito Original (`85a1b92~1`) | Núcleo Atual (`AGENTS.md`) | Seção Sob Demanda (`AGENTS-REFERENCIA-COMPLETA.md`) | Redução no Núcleo |
| :--- | :--- | :--- | :--- | :--- |
| **Linhas** | 182 linhas | 114 linhas | 193 linhas | **-37,4%** (-68 linhas) |
| **Palavras** | 3.126 palavras | 1.268 palavras | 1.839 palavras | **-59,4%** (-1.858 palavras) |
| **Caracteres (Bytes)** | 23.330 bytes | 10.104 bytes | 16.753 bytes | **-56,7%** (-13.226 bytes) |
| **Estimativa de Tokens** | ~3.800 tokens | ~1.260 tokens | ~2.100 tokens | **~66,8% de economia de contexto** |

*Nota:* O núcleo atual de ~1.260 tokens atende perfeitamente ao padrão de governança estipulado no cabeçalho: `Context Optimization (<2000 tokens)`.

---

## 5. Resolução dos Arquivos-Ponteiro Multi-Harness

Todos os assistentes mantêm arquivos-ponteiro apontando diretamente para `AGENTS.md`, preservando a fonte única de verdade:

- **Claude:** `CLAUDE.md` e `.claude/CLAUDE.md` apontam para `[AGENTS.md](AGENTS.md)`.
- **Gemini CLI / Antigravity:** `GEMINI.md` aponta para `[AGENTS.md](AGENTS.md)`.
- **Qoder:** `QODER.md` aponta para `[AGENTS.md](AGENTS.md)`.
- **CodeBuddy:** `CODEBUDDY.md` aponta para `[AGENTS.md](AGENTS.md)`.
- **Cursor:** `.cursor/rules/aidd.md` aponta para `AGENTS.md`.

Como o `AGENTS.md` permanece na raiz e mantém integralmente todas as Leis Invioláveis, o formato de resposta da Regra 10 e os ponteiros sob demanda, a resolução para todos os harnesses permanece 100% íntegra (validado por `test_g_harness_compat.py`).

---

## 6. Definição de Pronto e Validação

- [x] Escopo do PLAN-0022 item 2 preenchido com detalhamento do que entra/não entra e razão por seção.
- [x] Núcleo mantém 100% das 13 leis invioláveis e declarações de portão.
- [x] Mecanismo real de carregamento sob demanda documentado e validado deterministicamente.
- [x] Redução do núcleo mensurada quantitativamente em linhas, palavras e bytes.
- [x] Arquivos-ponteiro de todos os assistentes validados e resolvendo sem divergência.
- [x] Bateria de testes de gates aprovada com exit 0 (21 testes em `test_g_lei_declara_portao.py`, `test_g_harness_compat.py`, `test_g_ecossistema_integridade.py`).
