# Guia Canônico da Família "Driven Developments" (*DDs) no Ecossistema AI-DD

> **Status:** Referência Canônica de Arquitetura e Engenharia  
> **Caminho:** `docs/explicacoes/GUIA-FAMILIA-DRIVEN-DEVELOPMENT-AI-DD.md`  
> **Guarda-Chuva Central:** AI-DD (AI-Driven Development)  

---

## 1. O Grande Guarda-Chuva: AI-DD (AI-Driven Development)

O **AI-Driven Development (AI-DD)** não é "vibe coding" nem geração caótica de código por prompts soltos. No ecossistema AIDD, é a **disciplina de orquestração sistemática de inteligência artificial governada por determinismo, contratos estritos, economia extrema de tokens e barreiras binárias de qualidade (Quality Gates)**.

Sob o AI-DD, uma constelação de disciplinas clássicas e modernas de engenharia (*-Driven Developments*) é aplicada em cada etapa do ciclo de vida do software.

```
                      ┌──────────────────────────────────────────────┐
                      │          AI-DD (Engenharia Central)          │
                      │  Governança Canônica + Quality Gates + AST   │
                      └──────────────────────┬───────────────────────┘
                                             │
      ┌──────────────────┬───────────────────┼───────────────────┬──────────────────┐
      ▼                  ▼                   ▼                   ▼                  ▼
1. SDD             2. BDD              3. DDD              4. EDD             5. CDD
Spec-Driven        Behavior-Driven     Domain-Driven       Event-Driven       Component/Cognitive
      │                  │                   │                   │                  │
      └──────────────────┴───────────────────┼───────────────────┴──────────────────┘
                                             │
                                             ▼
                                    6. TDD (Test-Driven)
                                    Ciclo Red-Green-Refactor
                                             │
                                             ▼
                               7. Clean Architecture & VSA
                                  Monólito Modular Desacoplado
```

---

## 2. A Família Completa dos "*DDs" e Suas Definições

Abaixo está o detalhamento completo de cada membro da família *Driven Development*, sua essência técnica e o problema que resolve:

| Disciplina | Nome Completo | Foco Central | O que define na Prática |
|---|---|---|---|
| **SDD** | *Spec-Driven Development* | Especificação Formal | Cria contratos de dados prévios (JSON Schema, OpenAPI 3.1) antes de qualquer linha de código. Elimina ambiguidades entre cliente e servidor. |
| **BDD** | *Behavior-Driven Development* | Comportamento Humano e Negócio | Descreve as regras de negócio em formato de estórias com cenários estruturados: *Dado (Contexto) / Quando (Ação) / Então (Resultado Esperado)*. |
| **DDD** | *Domain-Driven Design* | Modelagem do Domínio Real | Divide sistemas complexos em Contextos Delimitados (*Bounded Contexts*), separando Entidades, Objetos de Valor (*Value Objects*) e Agregados com Linguagem Ubíqua. |
| **EDD** | *Event-Driven Development* | Assincronismo e Desacoplamento | Arquitetura orientada a eventos, onde componentes publicam e assinam eventos via barramentos (*EventBus*, *Webhooks*), garantindo tolerância a falhas. |
| **CDD** | *Component-Driven Development* | Modularidade de Interface | Constrói a interface de usuário (UI) a partir de blocos atômicos, reutilizáveis e isolados de dependências de backend. |
| **MDD** | *Model-Driven Development* | Abstração Baseada em Modelos | O modelo de domínio é a fonte primária da verdade, gerando automaticamente esquemas de banco, DTOs e validações. |
| **FDD** | *Feature-Driven Development* | Entrega por Funcionalidades | Organiza a evolução do software em entregas atômicas e tangíveis de funcionalidades de negócio com escopo delimitado. |
| **TDD** | *Test-Driven Development* | Blindagem e Qualidade Binária | Metodologia onde o teste unitário é escrito primeiro, falha obrigatoriamente (*Red*), o código é gerado para passar (*Green*) e então limpo (*Refactor*). |

---

## 3. Quem Gera os Testes? A Fronteira entre `aidd-planner` e os Fluxos

Uma das distinções de engenharia mais vitais no ecossistema é o desacoplamento entre o **critério de aceite** e o **código executável**:

```
 ┌──────────────────────────────────────┐       ┌──────────────────────────────────────┐
 │             aidd-planner             │       │         Motores de Construção        │
 │                                      │       │    (generator / factory / bridge)    │
 │       O "O QUÊ" (A REGRA BDD)        │  ──►  │       O "COMO" (O CÓDIGO TDD)        │
 │                                      │       │                                      │
 │ - Define o caso de aceite abstrato   │       │ - Escreve o arquivo `test_*.py`      │
 │ - Ex: "Se peso > 30kg, erro 422"     │       │ - Cria fixtures e mocks reais        │
 │ - Não escreve código python de teste │       │ - Executa `pytest` (Red -> Green)    │
 └──────────────────────────────────────┘       └──────────────────────────────────────┘
```

1. **No `aidd-planner` (SDD + BDD):**
   - Cria o critério de aceite no `PLANNER.json`:
     ```json
     {
       "cenario": "Rejeitar moto para carga pesada",
       "dado": "Um pacote com peso de 35kg",
       "quando": "Tentamos vincular a uma motocicleta",
       "entao": "Retorna status HTTP 422 e erro 'CAPACIDADE_EXCEDIDA'"
     }
     ```
2. **No Fluxo de Construção (TDD):**
   - O motor de construção (ex: `aidd-generator` na Fase 3) traduz o requisito BDD em código de teste real com asserções estritas:
     ```python
     def test_rejeitar_moto_carga_pesada(client):
         resposta = client.post("/rotas/alocar", json={"veiculo": "moto", "peso": 35})
         assert resposta.status_code == 422
         assert resposta.json()["detalhe"] == "CAPACIDADE_EXCEDIDA"
     ```

---

## 4. Onde Cada "*DD" e Paradigma é Aplicado nos Nossos Fluxos

Cada uma dessas disciplinas possui uma implementação física e verificável dentro das ferramentas do ecossistema:

| Metodologia | Onde é Aplicada no Ecossistema | Como é Materializada no Código |
|---|---|---|
| **SDD** | `aidd-planner` & `aidd-forge` | Governança via `PLANNER.json`, esquemas JSON Schema rígidos e OpenAPI 3.1 (`/swagger`). |
| **BDD** | `aidd-planner` | Casos de aceite formulados no padrão *Dado/Quando/Então* integrados ao manifesto do plano. |
| **DDD** | `aidd-master` & `aidd-planner` | Bounded Contexts mapeados em Fatias Verticais (`src/modules/<dominio>/`), entidades e repositórios seguros anti-SQL injection. |
| **TDD** | `aidd-generator` & `aidd-master` | Fase 3 (Geração de testes `pytest`) e Fase 4 (Implementação Red-Green); suítes isoladas por módulo com zero stubs. |
| **EDD** | `aidd-master`, `aidd-factory` & Quarteto | Barramento `EventBus` pub/sub assíncrono interno e motor de `/webhooks` com assinatura HMAC SHA-256. |
| **CDD** | `aidd-bridge` & UI Super-App | Componentes reutilizáveis desacoplados em `src/static/` e telas isoladas com Design Tokens. |
| **MDD** | `aidd-master` & `aidd-generator` | Entidades tipadas (Pydantic V2 / SQLAlchemy / DTOs) geradas a partir do schema de domínio. |
| **FDD** | Tríade Canônica (Fluxos 1, 2 e 3) | Decomposição em Fatias Verticais Autônomas (VSA), permitindo entregas completas fatia a fatia. |
| **Clean Architecture** | `aidd-master` | **Vertical Slice Architecture (VSA)**: fatias autônomas verticais com shared kernel horizontal desacoplado. |
| **Clean Code** | Quality Gates (`G_ECOSSISTEMA_*`, AST) | Zero stubs, 100% tipado (Type Hints), funções atômicas e código sem comentários mortos ou decorativos. |

---

## 5. Conclusão: A Linha de Montagem Canônica

No ecossistema AIDD, os "DDs" não competem entre si. Eles operam como **estações de trabalho em uma linha de montagem de alta precisão**:

```
[aidd-planner]   ──► SDD (Contratos) + BDD (Regras) + DDD (Contextos)
       │
       ▼
[Fluxos 1, 2, 3] ──► TDD (Testes Reais) + EDD (Eventos/Webhooks) + CDD (Interfaces)
       │
       ▼
[aidd-master]    ──► Clean Architecture (VSA Monólito Modular) + MDD (Modelos de Dados)
       │
       ▼
[Gates Globais]  ──► Clean Code (Conformidade AST, Zero Stubs, Binary Quality Gate)
```
