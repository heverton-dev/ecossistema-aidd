# Estrutura do Manifesto `PLANO-EXECUCAO-ESTRUTURADO.json` — aidd-generator

> **Tag/Commit Documentado:** `7d63085` (Branch `main`)  
> **Fonte Primária:** `PLANO-EXECUCAO-ESTRUTURADO.json` na raiz do repositório `aidd-generator`.  
> **Escopo:** Análise factual dos campos, estrutura de governança e ciclo de leitura/atualização operado por agentes de IA e desenvolvedores.

---

## 1. O Que É Este Arquivo

O **`PLANO-EXECUCAO-ESTRUTURADO.json`** é o **Banco de Verdade Estruturado e Persistente** do projeto. Ele armazena metadados de governança, decisões arquiteturais consolidadas, princípios inegociáveis de engenharia e o estado atualizado de cada uma das etapas de implementação e correção do framework.

Sua finalidade primária é a **economia severa de contexto de LLM**: em vez de um agente de IA precisar carregar 50.000 tokens de histórico de conversa a cada nova sessão, ele lê apenas este arquivo estruturado (~5.000 tokens), identifica as tarefas com status pendente e continua a execução com contexto cirúrgico e sem alucinações.

---

## 2. Estrutura do Schema Observado

O arquivo é organizado em quatro blocos de nível raiz:

```json
{
  "metadata": { ... },
  "decisoes_arquiteturais": { ... },
  "principios_implementacao": { ... },
  "etapas": [ ... ]
}
```

---

### 2.1. Bloco `metadata`

Contém os dados de identificação do projeto, objetivos gerais e as leis inegociáveis de trabalho:

| Campo | Tipo | Descrição | Valor Observado |
| :--- | :--- | :--- | :--- |
| `versao` | string | Versão do manifesto de governança. | `"1.0"` |
| `data_criacao` | string | Data e hora de criação no padrão ISO 8601. | `"2026-08-30T10:35:00Z"` |
| `projeto` | string | Nome do projeto ou identificador do módulo. | `"proj_yt-list / aidd-project-generator"` |
| `objetivo_geral` | string | Declaração da missão da ferramenta e avaliação honesta do percentual concluído. | *"Ser um 'Lovable turbinado com AIDD': criar projeto do zero com engenharia agêntica aplicada..."* |
| `principios_inegociaveis` | array[string] | Regras que não podem ser violadas em nenhuma circunstância. | Transparência Total, Zero Alucinação, Universalidade, Determinismo, Economia de Tokens, Rastreabilidade. |

---

### 2.2. Bloco `decisoes_arquiteturais`

Documenta os consensos técnicos tomados ao longo do desenvolvimento, prevenindo retrabalho ou discussões cíclicas:

- **`protocolo_llm`:** Define a estratégia híbrida de inferência — *Delegado (default)* para interagir via arquivos com orquestradores ativos e *Headless (fallback)* via `litellm` para automações CLI e pipelines de CI/CD.
- **`persistencia_conhecimento`:** Fixa o uso do próprio arquivo JSON estruturado como banco de verdade entre sessões.
- **`versionamento_fase_0`:** Registra as 5 correções cirúrgicas aplicadas na estabilização inicial do núcleo determinístico.

Cada decisão contém campos como: `decisao`, `data_decisao`, `razao`, `implementacao`, `status`, `commits_relacionados` e `arquivo_referencia`.

---

### 2.3. Bloco `principios_implementacao`

Especifica as regras operacionais aplicadas no código-fonte:

- **`sem_alucinacao`:** Proíbe métricas forjadas, dados fabricados e skips de testes.
- **`transparencia`:** Exige que todos os relatórios, planos e auditorias estejam commitados no Git.
- **`determinismo`:** Estabelece a primazia do Python puro sobre chamadas de LLM para tarefas estruturais.

---

### 2.4. Bloco `etapas` (Array de Entregas)

Lista detalhadamente cada uma das etapas do projeto, permitindo o acompanhamento granular:

| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | string | Identificador estável da etapa (ex: `"fase-0-correcao-1"`, `"fase-8-inicio"`). |
| `nome` | string | Nome descritivo da entrega. |
| `descricao` | string | Explicação do problema solucionado ou funcionalidade implementada. |
| `arquivos_afetados` | array[string] | Lista de arquivos de código impactados pela etapa. |
| `decisoes` | array[string] | Critérios técnicos adotados na implementação. |
| `criterios_sucesso` | array[string] | Lista de validações objetivas e verificáveis que comprovam a conclusão. |
| `status` | string | Estado da entrega: `✅` (Concluída), `⏳` (Pendente) ou `🔶` (Provada com ressalvas). |
| `commits_relacionados` | array[string] | Hashes dos commits Git que consolidaram a etapa. |

---

## 3. Dinâmica de Consumo e Atualização

O fluxo operacional padrão de agentes que trabalham no repositório segue a seguinte cadência:

```
1. Agente inicia sessão ➔ Lê PLANO-EXECUCAO-ESTRUTURADO.json (~5k tokens)
2. Localiza a primeira etapa com status ⏳ PENDENTE
3. Lê os critérios de sucesso e arquivos afetados
4. Implementa a solução e executa a suíte de testes
5. Se aprovado em 100% dos testes, atualiza o status para ✅ no JSON
6. Registra o commit correspondente
```
