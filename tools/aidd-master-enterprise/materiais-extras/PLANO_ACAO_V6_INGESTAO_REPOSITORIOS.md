# Plano de Ação Estruturado: Ingestão & Reconstrução de Repositórios Externos (Onda 0 — V5.1 → alimenta V6)

> **Documento de Engenharia:** Extensão funcional do AIDD, complementar ao `PLANO_ACAO_EVOLUCAO_V5_V6.md`.
> **Decisões de escopo homologadas com o usuário (2026-09-01):**
> 1. **Fidelidade:** o repositório de origem é uma *fonte de requisitos*, não um alvo de tradução linha a linha — a meta é "recriar aplicando todo o processamento e entrega da V5" (SPEC → apply → gates → refine-module → 6 portais), igual a qualquer app nova hoje.
> 2. **Multi-repo:** vários repositórios formam **uma suíte unificada** (cross-domain, um módulo/fatia por repositório), reaproveitando `compose_suite.py`.
> 3. **Versionamento:** entra como **Onda 0**, incremental em v5.x, ortogonal e podendo rodar em paralelo/antes das Ondas 1-4 já planejadas.

---

## 1. Por que isto é uma "Onda 0" e não apenas uma feature da CLI

Auditoria do estado atual do `aidd-master-pack-v5` (2026-09-01) encontrou 3 fatos que mudam o escopo:

1. **`cmd_plan` (Fase 1.5) hoje só faz *keyword matching*** contra uma lista fixa `KNOWN_DOMAINS` dentro de `scripts/aidd.py`. Não há entendimento real de domínio — funciona para um prompt curto, mas não tem como "casar" com um repositório de código real. É preciso um motor de extração de domínio novo, não um ajuste de regex.
2. **Todo módulo gerado hoje tem schema genérico fixo**: `titulo`, `descricao`, `status`, `dados` (JSON blob) — ver `scripts/add_module.py`. Não existe suporte a campos tipados por entidade. Sem resolver isso primeiro, "recriar" um app real cai sempre num blob JSON genérico e perde a fidelidade de dados que é o ponto central do pedido. **Isto é pré-requisito estrutural, não opcional.**
3. **Já existe o mecanismo que fecha a lacuna de lógica de negócio**: `python scripts/aidd.py refine-module` + `templates/agents/agent_domain_refiner.md` (Onda 4.1 do plano anterior) já implementam um loop agente que lê cenários Gherkin (`.feature`) e edita `services.py` até 100% dos cenários passarem, validado por gate determinístico. **Isso já está implementado hoje**, não precisa ser reconstruído — só precisa ser alimentado com `.feature` derivados de um repositório real em vez de escritos à mão.

Além disso, existe uma skill irmã já instalada, `adaptar-lovable-aidd`, que resolve um problema **adjacente e mais raso**: higienizar um export Lovable *no lugar* (env, testes, CI, RLS), sem reconstruir na arquitetura AIDD (fatias verticais, EventBus, gates, MCP). Ela não resolve o pedido do usuário, mas suas heurísticas de detecção de stack Lovable/Supabase (`analisar-projeto.py`) são um ponto de partida reaproveitável para o novo detector de stack (Fase 2).

---

## 2. Visão Geral das Fases

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│      ONDA 0: INGESTÃO & RECONSTRUÇÃO DE REPOSITÓRIOS EXTERNOS (V5.1)              │
├──────────────────────────────────────────────────────────────────────────────────┤
│  Fase 0 — Spike de Viabilidade (sem tocar no motor)                               │
│  Fase 1 — CLI de Ingestão & Clonagem Segura (`aidd.py import`)                    │
│  Fase 2 — Detector de Stack & Extrator de Domínio (Domain Graph)                  │
│  Fase 3 — Upgrade do Motor p/ Schemas Tipados (pré-requisito estrutural)          │
│  Fase 4 — Ponte Domain Graph → SPEC/PLANO (reaproveita Fase 1.5 já existente)     │
│  Fase 5 — Domain Refiner alimentado por evidência de código real                  │
│  Fase 6 — Gate de Paridade Estrutural (G_PARIDADE, informativo)                   │
│  Fase 7 — Integração no Protocolo Conversacional & Documentação                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

Dependência com o plano anterior: Fase 3 (schemas tipados) também **beneficia diretamente** a Onda 1.1 (`DatabaseAdapter` Postgres) do `PLANO_ACAO_EVOLUCAO_V5_V6.md`, já que colunas tipadas mapeiam para Postgres muito melhor que um blob JSON. Fase 5 **depende** apenas do que já existe (Onda 4.1 já implementada), não da Onda 4.1 "futura".

---

## 3. Detalhamento das Fases

### Fase 0 — Spike de Viabilidade
- **O que fazer:** Rodar clone + inspeção manual contra 2-3 repositórios reais (incluir pelo menos um export Lovable/Supabase, caso citado pelo usuário, e um repo com stack diferente, ex. Next.js+Prisma ou Django) *antes* de comprometer qualquer arquitetura nova.
- **Por que fazer:** Validar se as heurísticas de detecção (migrations SQL, rotas, formulários) realmente produzem um domínio utilizável, evitando construir o motor completo em cima de uma suposição errada.
- **Entregável:** relatório curto com os padrões de stack encontrados e uma lista de heurísticas confirmadas/descartadas.

### Fase 1 — CLI de Ingestão & Clonagem Segura
- **O que fazer:** Novo subcomando `python scripts/aidd.py import <url1> [<url2> ...] [--branch NOME] [--token TOKEN]`. Clone raso (`--depth 1`) em `.aidd_cache/import/<hash>/`, **somente leitura estática** — nunca executa `npm install`, `pip install`, scripts de build ou qualquer código do repositório de origem.
- **Por que fazer:** Repositórios de terceiros são código não confiável por definição; a análise precisa ser inteiramente estática para não expor o ambiente do usuário.
- **Como fazer:**
  1. `git clone --depth 1` isolado por repositório.
  2. Rodar `G_SEGREDOS` (já existente) sobre o clone **antes** de qualquer outra etapa, para nunca herdar segredos do repo de origem no novo projeto.
  3. Checar licença do repositório (`LICENSE`/`package.json.license`) e sinalizar na SPEC se a licença restringe redistribuição/uso comercial — decisão de prosseguir é do usuário, nunca automática.
- **Critério de aceite:** URL pública clona; URL privada sem token falha com mensagem clara; nenhum processo do repositório-fonte é executado em nenhum momento.

### Fase 2 — Detector de Stack & Extrator de Domínio
- **O que fazer:** Motor de análise estática multi-stack em detectores plugáveis (`scripts/import_detectors/`):
  - **Dados:** lê `supabase/migrations/*.sql`, `prisma/schema.prisma`, `models.py` (Django/SQLAlchemy) → entidades, colunas, tipos, PK/FK, enums.
  - **Rotas/API:** varre React Router/Next.js (`app/`, `pages/`), chamadas `fetch`/`axios`/`supabase.from(...)`, Express/FastAPI routers → casos de uso por entidade (list/create/update/delete/custom).
  - **UI/telas:** varre componentes de formulário/tabela (`*Form.tsx`, `*Table.tsx`) para inferir campos visíveis, obrigatoriedade e papéis — reaproveitando heurísticas de `analisar-projeto.py` (da skill `adaptar-lovable-aidd`) como ponto de partida, não como dependência rígida.
  - **Saída unificada — Domain Graph** (JSON intermediário, independente de stack):
    ```json
    {
      "modulos": [{
        "slug": "produtos",
        "origem_repo": "https://github.com/...",
        "entidades": [{
          "nome": "Produto",
          "campos": [{"nome": "preco", "tipo": "decimal", "obrigatorio": true}],
          "relacoes": [{"campo": "categoria_id", "entidade_alvo": "Categoria"}],
          "rotas_inferidas": ["listar", "criar", "atualizar", "deletar"],
          "logica_nao_crud": ["calcularDescontoProgressivo() em src/services/pricing.ts"]
        }]
      }]
    }
    ```
- **Por que fazer:** desacopla "de onde veio a informação" (Lovable, Next.js, Django, ...) de "o que a V5 gera" — um stack novo no futuro só precisa de um detector novo que produza o mesmo grafo.
- **Critério de aceite:** rodar contra os repositórios da Fase 0 e produzir um Domain Graph que um humano confirma bater com a realidade do app.

### Fase 3 — Upgrade do Motor de Geração para Schemas Tipados (pré-requisito estrutural)
- **O que fazer:** Estender `scripts/add_module.py` e os templates (`models.py`, `services.py`, `routes.py`, componente UI, OpenAPI) para aceitar uma definição de entidade tipada (campos/tipos/relações), mantendo **100% de retrocompatibilidade**: chamada sem definição de campos continua gerando o schema genérico atual (o path do `plan` por prompt textual não muda).
- **Por que fazer:** sem isso, qualquer importação de repositório real regride para o blob JSON genérico — inaceitável para o objetivo declarado pelo usuário.
- **Critério de aceite:** `add-module --campos <definição>` gera CRUD tipado + testes unitários tipados + OpenAPI com schema real; os 7 gates existentes continuam passando sem alteração no comportamento do fluxo por prompt.

### Fase 4 — Ponte Domain Graph → SPEC/PLANO
- **O que fazer:** Gerador que transforma o Domain Graph (Fase 2) num `SPEC-ARQUITETURA.md` + `PLANO-EXECUCAO-ESTRUTURADO.json` **no mesmo formato** que `cmd_plan` já produz hoje — o restante do pipeline (`apply`, `compose_suite`, gates) não sabe nem precisa saber se a origem foi texto ou repositório clonado.
- **Como fazer:**
  1. Cada repositório de entrada vira um módulo/fatia vertical candidato dentro da mesma suíte (decisão homologada: suíte unificada), via `compose_suite.py`.
  2. Deduplicação de entidades entre repositórios (ex.: "cliente" repetido em dois repos): comparação por similaridade de nome+campos, candidatos de merge **apresentados na SPEC para aprovação manual — nunca mesclados silenciosamente**.
  3. Fluxo de aprovação do usuário permanece idêntico ao de hoje ("Aprovado"/"Pode criar" dispara `apply`).
- **Critério de aceite:** SPEC gerada a partir de repositório(s) reais, aprovada, e `apply` compõe a suíte sem alteração no `compose_suite.py` além do que a Fase 3 adicionou.

### Fase 5 — Domain Refiner Alimentado por Evidência de Código Real
- **O que fazer:** Para funções de negócio não-CRUD identificadas no repo de origem (campo `logica_nao_crud` do Domain Graph), gerar automaticamente cenários Gherkin (`features/<modulo>.feature`) descrevendo o comportamento observado, e rodar o loop **já existente** `refine-module` / `agent_domain_refiner` com o código-fonte original disponível como referência de leitura (nunca copiado literalmente).
- **Por que fazer:** é exatamente o que fecha a frase do usuário — "aplicar todo o processamento e entrega da V5" — pois a V5 já trata lógica de domínio complexa por esse mecanismo para qualquer app nova; aqui só se automatiza a geração dos `.feature` a partir de evidência de código real, em vez de escritos à mão.
- **Critério de aceite:** ao menos uma regra de negócio não-trivial extraída de um repo da Fase 0 é portada e validada com `exit 0` no `refine-module`.

### Fase 6 — Gate de Paridade Estrutural (`G_PARIDADE`, informativo)
- **O que fazer:** Novo gate que compara a suíte gerada contra o Domain Graph de origem (nº de entidades, campos por entidade, rotas por entidade) e reporta um "score de cobertura" no relatório de `audit --report`. **Não bloqueia por padrão** — paridade 100% nem sempre é o objetivo do usuário.
- **Critério de aceite:** `audit --report` inclui seção "Paridade com Origem" quando o projeto foi criado via `import`.

### Fase 7 — Integração no Protocolo Conversacional & Documentação
- **O que fazer:** Atualizar `SKILL.md`/`README.md` com o novo fluxo de entrada (usuário cola 1+ URLs no chat → Maestro roda `import` → apresenta SPEC, Fase 1.5 sem mudança → aprovação → `apply`/`audit` → entrega nos 6 portais). Atualizar `PLANO_ACAO_EVOLUCAO_V5_V6.md` referenciando esta Onda 0. Criar um exemplo ponta a ponta em `examples/`.
- **Critério de aceite:** exemplo completo de importação documentado do início ao fim, replicável por um terceiro.

---

## 4. Matriz Consolidada de Execução

| Fase | Iniciativa | Arquivos Afetados | Complexidade | Depende de |
| :---: | :--- | :--- | :---: | :--- |
| 0 | Spike de Viabilidade | (nenhum, só investigação) | Baixa | — |
| 1 | CLI de Ingestão Segura | `scripts/aidd.py`, `scripts/import_repo.py` (novo) | Baixa | Fase 0 |
| 2 | Detector de Stack & Domain Graph | `scripts/import_detectors/` (novo) | **Alta** | Fase 1 |
| 3 | Schemas Tipados no Motor | `scripts/add_module.py`, `scripts/compose_suite.py`, `templates/v2/*` | **Alta** | — (paralelizável com Fase 2) |
| 4 | Ponte Domain Graph → SPEC/PLANO | `scripts/aidd.py` (`cmd_plan` generalizado) | Média | Fases 2 e 3 |
| 5 | Domain Refiner c/ Evidência Real | `templates/agents/agent_domain_refiner.md`, gerador de `.feature` (novo) | Média | Fase 4 (usa mecanismo já existente) |
| 6 | Gate G_PARIDADE | `scripts/gates/G_PARIDADE.py` (novo) | Baixa | Fase 4 |
| 7 | Protocolo & Documentação | `SKILL.md`, `README.md`, `PLANO_ACAO_EVOLUCAO_V5_V6.md`, `examples/` | Baixa | Fases 1-6 |

**Caminho crítico:** Fase 2 (detector multi-stack) e Fase 3 (schemas tipados) são os dois maiores riscos técnicos e podem rodar em paralelo desde o início — nenhuma depende da outra. Fase 4 é o ponto de junção. Fases 5-7 são sequenciais e de baixo risco.

---

## 5. Riscos e Guardrails Inegociáveis

- **Nunca executar código do repositório de origem** — análise 100% estática (parsers/regex/AST), nunca `npm install`/`build`/scripts arbitrários.
- **Nunca copiar código-fonte de terceiros literalmente** para o novo projeto sem checagem de licença explícita e aprovação do usuário — o Domain Graph carrega *estrutura e comportamento inferido*, não trechos de código brutos.
- **Nunca mesclar entidades entre repositórios silenciosamente** (Fase 4) — todo merge é proposto na SPEC e aprovado pelo usuário, igual ao resto do fluxo conversacional já existente.
- **Repositórios privados exigem token explícito do usuário** — nunca tentar bypass de autenticação.
- **G_PARIDADE é informativo, não bloqueante** — evita forçar 100% de paridade quando o usuário só queria a ideia geral do app de origem.

---

## 6. Como Ativar Este Plano no Futuro

1. **Comando de retomada:** `"Vamos iniciar a Fase X do PLANO_ACAO_V6_INGESTAO_REPOSITORIOS.md"`.
2. **Fase 0 primeiro, sempre** — nenhuma linha de motor é escrita antes do spike confirmar as heurísticas de detecção contra repositórios reais do usuário.
3. **Validação contínua por gates:** nenhuma fase é considerada concluída sem os 7 gates existentes + (a partir da Fase 6) `G_PARIDADE` com `python scripts/aidd.py audit --report`.
