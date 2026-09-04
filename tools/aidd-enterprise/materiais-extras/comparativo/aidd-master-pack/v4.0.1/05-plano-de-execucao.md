# Manifesto de Plano de Execução — AIDD Master Pack v4.0.1

> **Tag analisada:** `v4.0.1`.

---

## 1. Declaração Explícita: Esta Tag NÃO Gera o Manifesto Automaticamente

Diferente de versões posteriores do framework (onde `PLANO-EXECUCAO-ESTRUTURADO.json` é produzido automaticamente como parte do fluxo de planejamento, com dezenas de campos estruturados — arquitetura, módulos com rotas/eventos/testes, lista de gates de qualidade etc.), **nenhum script da tag `v4.0.1` cria esse arquivo**.

Evidência:
- `scripts/aidd.py` possui os comandos `init`, `add-module`, `test`, `audit`, `deploy`, `status`. Nenhum deles escreve um arquivo `PLANO-EXECUCAO-ESTRUTURADO.json`.
- `cmd_status()` (o comando `aidd.py status`) apenas **lê** esse arquivo, se ele já existir na raiz do projeto:

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
- `scripts/provision_project.py` (usado pelo comando `init`) copia apenas o Shared Kernel, os scripts e os gates — não gera nenhum manifesto JSON de plano.

Ou seja: nesta tag, o arquivo `PLANO-EXECUCAO-ESTRUTURADO.json` só existe em um projeto se **alguém (tipicamente o agente de IA que segue o `SKILL.md`, ou o desenvolvedor) o escrever manualmente**. O `aidd.py status` foi construído prevendo essa possibilidade, mas não a automatiza.

---

## 2. Como o Planejamento de Execução Realmente Funciona Nesta Versão

O planejamento de execução na tag `v4.0.1` é **conceitual/documental**, apoiado em três mecanismos:

1. **`SKILL.md`** — instrui o agente de IA a seguir "as 3 Regras de Ouro da Engenharia Agêntica e a arquitetura Vertical Slices" ao construir o sistema, mas não define um formato JSON de plano.
2. **`templates/rules/02_golden_rules.md`** — dita que sessões devem ser "reiniciadas usando o Plano JSON (retoma estado com ~500 tokens)", pressupondo a existência de um plano JSON, mas sem fornecer o template ou o gerador desse arquivo nesta tag.
3. **Convenção observada nos projetos de exemplo (`examples/`)** — todos os 9 exemplos que contêm um `PLANO-EXECUCAO-ESTRUTURADO.json` seguem manualmente um esquema simples e consistente, provavelmente escrito por um agente de IA ao seguir a `SKILL.md`, não gerado por script.

---

## 3. Esquema Real Observado no Manifesto (Exemplo: `catalogo-digital-v3`)

Como referência, este é o `PLANO-EXECUCAO-ESTRUTURADO.json` completo encontrado em `examples/catalogo-digital-v3/` nesta tag:

```json
{
  "projeto": {
    "nome": "catalogo-digital-e",
    "descricao": "Catalogo Digital e Loja com Checkout WhatsApp e Painel Admin",
    "arquitetura": "AIDD 4 Camadas",
    "zero_api_key_mode": true,
    "status": "INICIALIZADO"
  },
  "fases": [
    {
      "id": "fase-01-analise",
      "nome": "Analise e Modelagem de Contratos",
      "status": "PENDENTE",
      "mesa_orca": "mesa-analise",
      "expected_outputs": ["docs/ARQUITETURA.md"]
    },
    {
      "id": "fase-02-implementacao",
      "nome": "Implementacao do Core Determinístico",
      "status": "PENDENTE",
      "mesa_orca": "mesa-dev",
      "expected_outputs": ["src/main.py"]
    },
    {
      "id": "fase-03-validacao",
      "nome": "Auditoria de Gates e Testes Finais",
      "status": "PENDENTE",
      "mesa_orca": "mesa-qa",
      "expected_outputs": ["tests/"]
    }
  ]
}
```

Este mesmo esquema (2 seções: `projeto` e `fases`, cada fase com 3 etapas fixas — análise, implementação, validação) se repete de forma praticamente idêntica em todos os demais exemplos desta tag (`crm-omnichannel-v2/v3`, `erp-financeiro-v2/v3`, `helpdesk-sla-v2/v3`, `plataforma-de-membros`, `plataforma-membros-v3`, `plataforma-modular-assinaturas`), o que confirma tratar-se de um **padrão de convenção seguido manualmente pelo agente de IA**, não um esquema imposto/validado por código.

### 3.1 Descrição dos Campos Reais

| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `projeto.nome` | string | Slug/nome curto do projeto. |
| `projeto.descricao` | string | Descrição em linguagem natural do que o sistema faz. |
| `projeto.arquitetura` | string | Rótulo fixo observado: `"AIDD 4 Camadas"`. |
| `projeto.zero_api_key_mode` | boolean | Indica se o projeto opera sem exigir chaves de API pagas (harness nativo). |
| `projeto.status` | string | Valor observado nos exemplos: `"INICIALIZADO"` (não há evidência de outros valores usados nesta tag). |
| `fases[]` | array | Lista de fases do ciclo de construção. |
| `fases[].id` | string | Identificador da fase (`fase-01-analise`, `fase-02-implementacao`, `fase-03-validacao`). |
| `fases[].nome` | string | Nome descritivo da fase. |
| `fases[].status` | string | Valor observado: `"PENDENTE"` em todos os exemplos (nenhum exemplo desta tag traz uma fase marcada como concluída, sugerindo que o campo não é atualizado automaticamente após a execução). |
| `fases[].mesa_orca` | string | Nome da "mesa de trabalho" ORCA Worktree associada à fase (`mesa-analise`, `mesa-dev`, `mesa-qa`). |
| `fases[].expected_outputs` | array de strings | Caminhos de arquivo/pasta esperados como entrega da fase. |

---

## 4. Consequência Prática

Como o comando `aidd.py status` depende da existência prévia desse arquivo mas nenhum script o cria ou atualiza (`status: "PENDENTE"` nunca muda para `"CONCLUIDO"` automaticamente nos exemplos), o "acompanhamento de progresso" nesta tag é, na prática, **manual**: cabe ao agente de IA ou ao desenvolvedor escrever e manter esse JSON à mão, e o único consumo automatizado é a leitura feita por `aidd.py status` para exibir um resumo no terminal.

---

*Baseado no código de `scripts/aidd.py` (`cmd_status`), `scripts/provision_project.py` e nos 9 arquivos `PLANO-EXECUCAO-ESTRUTURADO.json` presentes em `examples/` na tag `v4.0.1`.*
