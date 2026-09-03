# Plano de Execução Estruturado — AIDD Master Pack v3.0.0

> **Tag analisada:** `v3.0.0`
> **Escopo:** Explicar exatamente como o planejamento de execução funciona nesta tag, com base em evidência real do código e dos arquivos de exemplo extraídos do snapshot.

---

## 1. Descoberta Central: o Manifesto Existe como Convenção, Não como Geração Automatizada

Diferente de versões posteriores do framework (onde há um pipeline dedicado de planejamento), **a v3.0.0 não contém nenhum script que gere `PLANO-EXECUCAO-ESTRUTURADO.json`**. Uma busca completa por `PLANO-EXECUCAO` no código-fonte desta tag encontra apenas **um único ponto de leitura**, em `scripts/aidd.py`:

```python
def cmd_status(args):
    print("[AIDD STATUS] Inspecionando saude do projeto modular...")
    import json
    if os.path.exists("PLANO-EXECUCAO-ESTRUTURADO.json"):
        with open("PLANO-EXECUCAO-ESTRUTURADO.json", "r", encoding="utf-8") as f:
            plano = json.load(f)
        print(f"Projeto: {plano.get('projeto', {}).get('nome')} (v{plano.get('projeto', {}).get('versao')})")
        print(f"Status: {plano.get('projeto', {}).get('status')}")
        ...
```

Ou seja: `python scripts/aidd.py status` **lê** o arquivo se ele existir na raiz do projeto, mas **nenhum comando desta tag o cria**. Nem `provision_project.py` nem `add_module.py` escrevem esse JSON.

O arquivo, portanto, não é um "manifesto gerado pela ferramenta" nesta versão — é uma **convenção de documentação** que o operador humano (ou o agente de IA rodando dentro do Harness, seguindo as instruções de `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` de cada projeto) cria manualmente ao final de um ciclo de trabalho, para que `aidd.py status` tenha algo para exibir depois.

---

## 2. Onde o Manifesto Aparece de Fato Nesta Tag

`PLANO-EXECUCAO-ESTRUTURADO.json` está presente em **3 dos 6 projetos de exemplo** do repositório — todos eles pertencentes à geração de exemplos anterior à arquitetura "V3" introduzida nesta tag:

- `examples/catalogo-digital-whatsapp/PLANO-EXECUCAO-ESTRUTURADO.json`
- `examples/plataforma-de-membros/PLANO-EXECUCAO-ESTRUTURADO.json`
- `examples/plataforma-modular-assinaturas/PLANO-EXECUCAO-ESTRUTURADO.json`

Os 3 novos exemplos criados por esta tag (`crm-omnichannel-v3`, `erp-financeiro-v3`, `helpdesk-sla-v3`) **não têm** esse arquivo — reforçando que ele não é parte obrigatória (nem gerada) do fluxo "V3".

---

## 3. Estrutura Real do Manifesto (Campo a Campo)

Conteúdo real de `examples/plataforma-de-membros/PLANO-EXECUCAO-ESTRUTURADO.json`, usado como referência de formato:

```json
{
  "projeto": {
    "nome": "plataforma-de-cursos",
    "descricao": "Plataforma de Cursos e Area de Membros com Checkout",
    "arquitetura": "AIDD 4 Camadas",
    "zero_api_key_mode": true,
    "status": "CONCLUIDO_COM_SUCESSO"
  },
  "fases": [
    {
      "id": "fase-01-analise",
      "nome": "Analise e Modelagem de Contratos",
      "status": "CONCLUIDO",
      "mesa_orca": "mesa-analise",
      "expected_outputs": ["docs/ARQUITETURA.md"],
      "gates_validados": ["G_SEGREDOS", "G_QUALIDADE", "G_HARNESS_COMPAT"]
    },
    {
      "id": "fase-02-implementacao",
      "nome": "Implementacao do Core Determinístico",
      "status": "CONCLUIDO",
      "mesa_orca": "mesa-dev",
      "expected_outputs": ["src/main.py"],
      "gates_validados": ["G_SEGREDOS", "G_QUALIDADE", "G_HARNESS_COMPAT"]
    },
    {
      "id": "fase-03-validacao",
      "nome": "Auditoria de Gates e Testes Finais",
      "status": "CONCLUIDO",
      "mesa_orca": "mesa-qa",
      "expected_outputs": ["tests/"],
      "gates_validados": ["G_SEGREDOS", "G_QUALIDADE", "G_HARNESS_COMPAT"]
    }
  ]
}
```

### Tabela de campos

| Campo | Tipo | Significado Real Observado |
| :--- | :--- | :--- |
| `projeto.nome` | string | Slug/nome curto do projeto (usado no cabeçalho de `aidd.py status`). |
| `projeto.descricao` | string | Frase curta em linguagem natural do que o projeto faz. |
| `projeto.arquitetura` | string | Rótulo textual fixo, `"AIDD 4 Camadas"` nos 3 exemplos observados — não é validado por código. |
| `projeto.zero_api_key_mode` | boolean | Flag informativa (documental); nenhum script desta tag lê ou aplica esse valor. |
| `projeto.status` | string | Valor livre (`"CONCLUIDO_COM_SUCESSO"` nos exemplos). `aidd.py status` apenas imprime o valor, sem validá-lo contra uma lista fechada de estados. |
| `fases[]` | array | Lista de etapas do trabalho já realizado (não é usada por `aidd.py status`, que só lê `projeto.*` e a lista de módulos em `src/modules/`). |
| `fases[].id` | string | Identificador da fase, padrão `fase-NN-nome`. |
| `fases[].nome` | string | Nome descritivo da fase. |
| `fases[].status` | string | Nos 3 exemplos, sempre `"CONCLUIDO"` — não há evidência de estados intermediários (`"EM_ANDAMENTO"`, `"PENDENTE"`) no código ou nos exemplos desta tag. |
| `fases[].mesa_orca` | string | Nome da "mesa de trabalho" ORCA associada (conceito de orquestração multi-agente citado em `SKILL.md`, mas sem código de orquestração ORCA presente nesta tag). |
| `fases[].expected_outputs` | array de strings | Caminhos de arquivo esperados como resultado da fase. Não verificado automaticamente contra o disco. |
| `fases[].gates_validados` | array de strings | Nos 3 exemplos, sempre a lista fixa `["G_SEGREDOS", "G_QUALIDADE", "G_HARNESS_COMPAT"]` — coerente com os 3 gates que de fato existem nesta tag. |

---

## 4. Como o Planejamento de Execução Realmente Funciona na v3.0.0

Sem um gerador de plano, o "planejamento" nesta versão é conduzido por três mecanismos textuais/documentais, não por código executável:

1. **`SKILL.md` (raiz do pacote):** define o papel do orquestrador (`aidd-master-pack`) e promete, em linguagem natural, provisionar "a arquitetura completa das 4 Camadas" e integrar com uma skill `/implementacao` (ciclo `impl -> test -> validate -> verify`) — mas nenhum desses nomes de comando/skill tem implementação de código nesta tag; é um contrato de comportamento esperado do agente de IA que interpreta a skill.
2. **`AGENTS.md`/`CLAUDE.md`/`GEMINI.md` por projeto:** presentes nos 3 exemplos legados, descrevem regras de governança (uso de mesas ORCA, ordem de execução dos gates, economia de tokens) que o agente deve seguir manualmente ao planejar o trabalho.
3. **`PLANO-EXECUCAO-ESTRUTURADO.json`:** funciona como um **registro pós-hoc** do que foi feito (todas as fases aparecem já `"CONCLUIDO"` nos exemplos), não como um plano prospectivo gerado antes da execução. `aidd.py status` o usa apenas para exibir um resumo de saúde do projeto.

**Conclusão:** nesta tag, o planejamento de execução é feito pelo agente/desenvolvedor seguindo instruções em Markdown, e documentado manualmente num JSON de convenção — não há CLI de planejamento (`aidd.py plan`), nem geração automática do manifesto, nem validação de que as fases declaradas correspondem ao estado real do projeto.
