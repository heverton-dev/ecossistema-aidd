# Anatomia Técnica: orquestrador-4f

## Cartão de Identidade
- **Nome do Alvo:** orquestrador-4f (Pipeline de Evolução Técnica e Auditoria 4 Fases)
- **Finalidade:** Executar deterministicamente planos de evolução e auditoria técnica ticket a ticket em árvores de trabalho Git isoladas com barreira de sincronização humana.
- **Nível de Maturidade:** Produção / Blindado (O mais maduro e testado do ecossistema AIDD).
- **Trava Principal:** gate_fase obrigatório por ticket (rejeita commits sem exit 0) e verificação criptográfica SHA na aprovação.
- **Comando Acionador:** `python ecossistema.py evolucao <ferramenta>` ou `python scripts/orquestrador_4f.py --manifest <manifesto.json>`
- **Localização:** `scripts/orquestrador_4f.py` (com apoio de `scripts/scaffold_auditoria.py` e `scripts/compilador_plano_evolucao.py`)

---

## Fluxo de Execução
- **Etapa 1 — Inicializa:** **Gera** a pasta do ciclo (`docs/auditoria/<ferramenta>/ciclo-NN/`) e os manifestos base através de `scaffold_auditoria.py`.
- **Etapa 2 — Diagnostica:** **Executa** o agente Inspetor sob a lente 15-D, produzindo o arquivo de evidências `RELATORIO-INSPETOR.md`.
- **Etapa 3 — Projeta:** **Redige** os tickets de correção e evolução com o agente Arquiteto no `PLANO-EVOLUCAO.md`.
- **Etapa 4 — Compila:** **Valida** os prompts em inglês imperativo e campos obrigatórios com `compilador_plano_evolucao.py`, gerando `PLANO-EVOLUCAO.json`.
- **Etapa 5 — Constrói:** **Itera** sequencialmente sobre cada ticket do manifesto:
  - **Abre** uma *worktree* Git efêmera isolada na branch `audit/<pipeline_id>`.
  - **Injeta** o prompt no terminal interativo e aguarda a geração do arquivo de handoff.
  - **Executa** o teste determinístico associado (`gate_fase`).
  - **Comita** o resultado na branch do ciclo apenas se o teste retornar exit 0; em caso de falha, **interrompe** e **preserva** a worktree para inspeção humana.
- **Etapa 6 — Confere:** **Roda** a suíte completa de testes (`gate_final`) em uma pasta limpa (`_gate_final`) e **grava** a referência de integridade `refs/audit/aprovavel/<pipeline_id>`.
- **Etapa 7 — Integra:** **Solicita** ação humana explícita (`--aprovar`) para realizar o merge seguro na branch principal (*Join Barrier*).

---

## Esteira Visual com Blocos

| Bloco | Descrição do Fluxo |
| :--- | :--- |
| **Entrada** | `PLANO-EVOLUCAO.json` validado com lista de fases, tickets, prompts em inglês imperativo e caminhos de gates. |
| **Processo** | Criação de branch dedicada, abertura de worktree por ticket, disparo do harness no terminal TTY e verificação de arquivos de saída. |
| **Trava** | Execução automática de `gate_fase` antes de cada commit e `gate_final` antes de liberar a chave criptográfica de aprovação. |
| **Saída** | Branch `audit/<pipeline_id>` testada e aprovada, pronta para merge humano via `--aprovar`, com histórico limpo de commits. |

---

## Defeitos e Limitações
- **Restringe** a execução estritamente a ferramentas registradas que possuam a estrutura `docs/auditoria/<ferramenta>/ciclo-NN/`.
- **Exige** configuração prévia no arquivo `docs/auditoria/CONFIG-EXECUCAO-USUARIO.json`.
- **Executa** os tickets de forma puramente sequencial, o que impede paralelismo de frentes independentes.

> [!WARNING]
> **Ponto Crítico:** Se qualquer comando da IA for abortado no terminal ou falhar no `gate_fase`, o pipeline para imediatamente. A worktree é preservada no disco e bloqueia novos passos até a resolução manual ou limpeza da worktree.

> [!TIP]
> **Recomendação Prática:** Sempre valide a compilação do plano antes da execução rodando `python scripts/compilador_plano_evolucao.py <caminho-md> <caminho-config>`, garantindo que nenhum prompt contenha termos não-ingleses que violem a Lei #4.
