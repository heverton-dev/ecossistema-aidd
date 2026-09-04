# Plano de Execução — Como o Planejamento Funciona na `v1.0.0`

> **Tag analisada:** `v1.0.0` (commit `729ce3e`)
> Este documento explica como (e se) a execução do trabalho é planejada e rastreada nesta versão do framework, com base em evidência real encontrada na tag.

---

## 1. Não existe um manifesto de planejamento gerado automaticamente

Diferente de versões posteriores do repositório, que produzem um `PLANO-EXECUCAO-ESTRUTURADO.json` rico (com projeto, arquitetura, lista de módulos com rotas/eventos, e lista de gates de qualidade) como parte do próprio processo de scaffolding, **nenhum script da tag `v1.0.0` gera esse arquivo**. Nem `provision_project.py`, nem `add_module.py`, nem `aidd.py` criam ou escrevem em `PLANO-EXECUCAO-ESTRUTURADO.json` em nenhum ponto do código.

A única relação do framework com esse arquivo é **de leitura**: o comando `python scripts/aidd.py status` tenta abrir `PLANO-EXECUCAO-ESTRUTURADO.json` na raiz do projeto atual, e se o arquivo existir, imprime nome, versão e status do projeto. Se não existir, o comando simplesmente não exibe essa parte do relatório — não há erro, não há criação automática.

## 2. Evidência real: quando o manifesto aparece, ele é simples

Dos 12 projetos de referência empacotados em `examples/`, **apenas 5** contêm um `PLANO-EXECUCAO-ESTRUTURADO.json` (`catalogo-digital-v3`, `catalogo-digital-whatsapp`, `plataforma-de-membros`, `plataforma-membros-v3`, `plataforma-modular-assinaturas`). Os outros 7 (`crm-omnichannel-v2/v3`, `enterprise-suite-v4`, `erp-financeiro-v2/v3`, `helpdesk-sla-v2/v3`) não têm o arquivo — nem `AGENTS.md`/`CLAUDE.md` — sugerindo que o plano é algo criado manualmente (ou pelo agente de IA em texto livre), não uma etapa obrigatória do pipeline.

Quando presente, a estrutura observada é minimalista:

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

Características desse formato observado:
- **3 fases fixas e genéricas** (análise, implementação, validação) — não há granularidade por módulo, rota ou evento.
- Todos os 5 exemplos que possuem o arquivo usam exatamente essas **mesmas 3 fases**, com status `"PENDENTE"` congelado — indicando que o campo `status` não é atualizado automaticamente conforme o trabalho avança (nenhum script da tag escreve nesse JSON).
- Não há lista de módulos, rotas, eventos ou gates dentro do manifesto — apenas metadados de projeto e a lista de fases.
- O campo `"mesa_orca"` referencia um conceito de "mesas de trabalho" do ORCA (ambiente de desenvolvimento multi-agente externo ao pacote), mencionado também em `AGENTS.md`, mas nenhum script desta tag efetivamente cria ou consulta essas mesas — é uma referência textual, não uma integração funcional.

## 3. O processo real de planejamento na v1.0.0

Como não há manifesto obrigatório nem orquestrador que sequencia fases automaticamente, o planejamento real acontece assim:

1. **Decisão humana/agente:** o usuário (ou o agente de IA seguindo `AGENTS.md`/`.cursorrules`) decide o escopo do projeto em linguagem natural.
2. **Provisionamento único:** `aidd.py init "<descrição>"` cria o esqueleto — este é o único momento "automático" de todo o ciclo.
3. **Iteração manual módulo a módulo:** para cada domínio de negócio desejado, roda-se `add_module.py <nome>` e em seguida edita-se manualmente o código gerado.
4. **Checkpoints manuais:** o "plano" de fato é a sequência de comandos que o operador escolhe rodar (`test`, `audit`, `deploy`) — não há uma máquina de estados que force a ordem ou valide que uma fase terminou antes da próxima começar.
5. **Registro opcional em prosa:** quando um `PLANO-EXECUCAO-ESTRUTURADO.json` ou `AGENTS.md` é criado, ele documenta a intenção do projeto para consumo futuro por um agente de IA, mas não é lido nem escrito por nenhuma lógica de controle do framework além do `status` de leitura simples.

## 4. Comparação honesta com o conceito de "planejamento estruturado"

| Aspecto | Existe em `v1.0.0`? |
| :--- | :--- |
| Manifesto de plano gerado automaticamente | Não |
| Fases com granularidade por módulo/rota/evento | Não |
| Atualização automática de status conforme progresso | Não |
| Orquestração que impede pular fases | Não |
| Leitura de manifesto para relatório de status | Sim (`aidd.py status`, leitura simples) |
| Documento de intenção do projeto em prosa (`AGENTS.md`) | Sim, quando criado manualmente |
| Gates de qualidade amarrados a fases do plano | Não — gates rodam isolados, sem relação com o manifesto |

**Conclusão:** `v1.0.0` não possui um sistema de planejamento de execução no sentido formal (documento vivo + orquestração automática). O que existe é um formato de manifesto opcional, estático e ilustrativo, adotado de forma inconsistente entre os próprios exemplos oficiais do pacote, e uma sequência de comandos manuais que o operador decide encadear por conta própria.
