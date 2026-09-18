# Os 3 Fluxos Canônicos de Criação e Entrega do Ecossistema AIDD

> **Status:** Implementado. **Fluxo 01 validado ponta a ponta com aplicação real rodando em Docker** (18/09/2026). Fluxos 02 e 03 implementados, mas ainda não validados ponta a ponta na mesma bateria de testes.
> **Última atualização:** 18/09/2026 — revisão factual pós-validação E2E (ver `docs/teste-end-to-end/17-09-2026_relatorio-testes-triade-fluxos-1-2-3.md`).
> **Localização:** `docs/melhorias/16-09-2026_MELHORIA-3-FLUXOS-CRIACAO-ECOSSISTEMA.md`

---

## 1. O Problema Original

As ferramentas de criação de código do ecossistema (`aidd-generator`, `aidd-factory` e `aidd-bridge`) apresentavam sobreposições conceituais e competiam entre si pelo mesmo espaço, sem um ponto único de planejamento prévio que permitisse derivar a mesma ideia de negócio em diferentes estratégias de entrega.

---

## 2. A Visão Arquitetural: A Tríade Canônica

Toda aplicação é criada a partir de uma **Fundação de Governança (`aidd-forge`)** e um **Planejador de Intake (`aidd-planner`)**, que dá ao desenvolvedor a liberdade de escolher qual dos **3 Fluxos Especializados** disparar para o mesmo projeto:

```
                      ┌────────────────────────┐
                      │       aidd-forge       │
                      │ (Governança & Regras)  │
                      └───────────┬────────────┘
                                  │
                                  ▼
                      ┌────────────────────────┐
                      │      aidd-planner      │
                      │ (Intake BDD/SDD →      │
                      │  PLANNER.json)         │
                      └───────────┬────────────┘
                                  │
               Escolha do Desenvolvedor no Planner
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
   [ FLUXO 01 ]             [ FLUXO 02 ]             [ FLUXO 03 ]
  aidd-generator            aidd-factory             aidd-bridge
 (Do Zero Puro)          (Motores Open-Source)     (Low-Code Desatado)
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                                  ▼
                      ┌────────────────────────┐
                      │      aidd-master       │
                      │ (Monólito Modular VSA) │
                      └───────────┬────────────┘
                                  │
                                  ▼
                      ┌────────────────────────┐
                      │    aidd-enterprise     │
                      │  (Blindagem SHA-256)   │
                      └───────────┬────────────┘
                                  │
                                  ▼
                      ┌────────────────────────┐
                      │        aidd-ops        │
                      │(Deploy VPS & Observab.)│
                      └────────────────────────┘
```

**Achado real da validação E2E:** hoje não existe handoff automático de dados entre etapas adjacentes — cada ferramenta é invocada isoladamente via CLI (`ecossistema.py <ferramenta> <comando>`) e não lê o artefato JSON da etapa anterior:
- `aidd-generator` recebe a ideia como **texto livre posicional** (`generate "<ideia>"`), não lê o `PLANNER.json` do `aidd-planner`.
- `aidd-master` (`master init`) não importa o código já escrito pelo `aidd-generator`/`aidd-factory` — gera um scaffold CRUD genérico do zero a partir do nome do módulo.
- A "convergência" do diagrama acima é hoje **conceitual/manual**: o desenvolvedor decide separadamente rodar cada etapa. Fechar esse handoff está registrado como pendência (fora do escopo desta rodada de correções).

---

## 3. As Responsabilidades Reais das Ferramentas

### 1. `aidd-forge` — Governança e Isolamento
Injeta governança, Git, pre-commit hooks e regras de isolamento no repositório alvo. **Pré-requisito real não documentado antes:** `forge init` só instala o hook de pre-commit se o diretório alvo **já for** um repositório Git (`git init` precisa rodar antes, na primeira vez).

### 2. `aidd-planner` — Intake e Especificação (BDD/SDD)
Faz a entrevista/intake e gera o artefato canônico **`PLANNER.json`** (não existe um arquivo chamado "PLANO-MESTRE.json" — esse nome nunca existiu no código). Validado por `planner validate`/`planner audit` contra o Quarteto Sine Qua Non e a coerência do fluxo escolhido.

### 3. Os 3 Motores Especializados de Construção

| Fluxo | Motor | O que Produz Hoje | Status de Validação |
| :--- | :--- | :--- | :--- |
| **FLUXO 01** | **`aidd-generator`** | Pipeline de 8 fases (Spec → Arquitetura → Testes Red → Implementação Green → Quarteto), 100% guiado por um agente de IA real via Protocolo Delegado. | ✅ Validado E2E. 4 bugs reais corrigidos (incluindo um mock hardcoded que substituía silenciosamente o protocolo delegado real). |
| **FLUXO 02** | **`aidd-factory`** | Aplicação Modular VSA + Gateway FastAPI complementar + frontend, a partir de um `PLANO-INFRAESTRUTURA.json` curado por nicho OSS (`aidd-ops plan`). | ⚠️ Corrigido nesta rodada (frontend duplicado/divergente — ver Seção 4), mas não re-executado ponta a ponta com Docker real. |
| **FLUXO 03** | **`aidd-bridge`** | Unificação de múltiplos apps Lovable/v0/Bolt (Vite+React SPA), conversão de banco Supabase→PostgreSQL (`init-db.sql`), empacotamento Docker+Nginx, contratos VSA (Quarteto). | ❌ Não testado nesta rodada nem na anterior. |

### 4. O Funil de Convergência

1. **`aidd-master`** — Organiza o código em Monólito Modular: fatias verticais em **`src/modules/<slug>/`** (não `src/features/` — esse nome nunca existiu no código real) + núcleo horizontal compartilhado em `src/core/`.
2. **`aidd-enterprise`** — Injeta componentes assinados por SHA-256 (`inject`) e detecta adulteração pós-injeção (`verificar-drift`). **Bug grave corrigido nesta sessão:** o comando `verificar-drift` — a funcionalidade central da ferramenta — nunca havia sido implementado; chamá-lo caía num fallback que criava um projeto indevido no lugar.
3. **`aidd-ops`** — Provisiona infraestrutura. **Reescopo nesta sessão:** cobre agora dois tipos de origem — stacks OSS curadas por nicho (Fluxo 02, comando `ops plan "<texto>"`) **e** monólitos customizados do `aidd-master` (Fluxo 01/03, comando `ops plan --dir-projeto <pasta>`), com o `deploy` selecionando o motor certo automaticamente (`coolify` vs `compose-nativo`). Antes desta correção, `ops deploy` sempre implantava a mesma stack fixa (Twenty/Chatwoot/Calcom/Postgres/UptimeKuma) **independente do nicho realmente curado** — bug real corrigido nesta sessão, não apenas o suporte a monólito que faltava.

---

## 4. Lei Inviolável #11 — Padrão-Ouro de Stack Tecnológica (adicionada 18/09/2026)

Todo fluxo que gera frontend (`aidd-generator`, `aidd-master`, `aidd-factory`) passa a produzir por padrão **Next.js 14 (App Router) + TypeScript + Tailwind CSS**, nunca mais HTML/CSS/JS puro por padrão — só se o usuário pedir explicitamente essa stack para aquela camada. Ver `docs/protocolos/PADRAO-OURO-STACK-TECNOLOGICA.md`.

- **Gerador único e compartilhado** (`componentes/compartilhado/src-core/nextjs_exporter.py`, sincronizado em `aidd-master` e `aidd-enterprise`): gera `frontend/` com uma única camada de acesso à API (`lib/api-client.ts`) e uma única variável de ambiente (`NEXT_PUBLIC_API_URL`). Os Studios nativos do backend (`/docs`, `/webhooks`, `/mcp`) **não são reimplementados em React** — continuam servidos pelo processo Python, roteados pelo Nginx por prefixo.
- **`aidd-master`**: `master init`/`master add-module` geram o frontend Next.js automaticamente; `docker-compose.yml`/`nginx.conf` ganharam um serviço `web` novo.
- **`aidd-factory`**: eliminada a duplicação — o pipeline gerava **dois frontends divergentes** para o mesmo projeto (Super-App Python via `vsa_generator.py` + Next.js via um `frontend_generator.py` próprio e incompatível). Agora os dois caminhos convergem para o mesmo gerador compartilhado.
- **`aidd-generator`**: o prompt da IA (Fase 8) foi atualizado para mandar Next.js por padrão — mudança de texto de instrução, não de gerador de arquivo (esta ferramenta não gera frontend diretamente, delega à IA).
- **Validação real:** aplicação de exemplo (Fluxo 01) rodando de verdade em Docker (`app` + `web` Next.js + `nginx`), com build real (`npm install && npm run build`) confirmado tanto no `aidd-master` quanto no `aidd-factory`.
- **Pendência conhecida:** `aidd-bridge` não entra nesta Lei da mesma forma — ele não gera frontend, importa o que já existe no projeto Lovable/v0/Bolt de origem (tipicamente Vite+React). Forçar conversão para Next.js ali é um projeto à parte, não feito nesta rodada.

---

## 5. O Quarteto *Sine Qua Non* — Rotas Reais

Todo projeto gerado por `aidd-master`/`aidd-factory` expõe nativamente:
* **`/docs`** — Swagger Studio (documentação interativa OpenAPI **3.1**). *(Não é `/swagger` — esse path não existe no código; é um erro herdado de versões antigas da documentação.)*
* **`/docs/guia`** — Manual vivo de utilização (gerado a partir de `docs.html`).
* **`/webhooks`** — Gestão e simulação de eventos assíncronos com assinatura HMAC.
* **`/mcp`** — Servidor Model Context Protocol nativo para agentes de IA.

---

## 6. Estado Real de Validação (18/09/2026)

| Item | Status |
| :--- | :--- |
| Fluxo 01 completo (Etapas 1-7: forge→planner→generator→master→enterprise→ops→auditoria final) | ✅ 100% — 13 bugs reais encontrados e corrigidos, aplicação rodando em Docker, `python ecossistema.py audit` verde |
| Lei #11 (Next.js) em `aidd-master`, `aidd-factory`, `aidd-generator` | ✅ Implementada e validada com build real |
| `aidd-ops` cobrindo monólito customizado + OSS por nicho + rotação de segredos | ✅ Implementado e validado (`rotate_secrets.py` em /run/secrets com permissão 0600) |
| Blindagem Arquitetural VSA & Quality Gates AST | ✅ 100% — `G_ISOLATION_AUDIT`, `G_DRIFT_ANALYZER`, `G_PROTOTYPE_REWRITE` e `G_PROTOCOL_FALLBACK` integrados ao pre-commit |
| Segurança & Defesa no Core (`PromptShield` + Fake Adapters) | ✅ 100% — `G_LLM_PROMPT_SHIELD`, sanitização determinística e `InMemoryFakeExternalAdapter` (Lei #5) |
| Telemetria Total de Testes Reais em `tools/` | ✅ **2.213 testes unitários reais passando** (294 forge, 1.019 generator, 386 master, 336 enterprise, 178 ops) |
| Fluxo 02 completo (mesma ideia, ponta a ponta) | ⏳ Pendente |
| Fluxo 03 completo (mesma ideia, ponta a ponta) | ⏳ Pendente |
| Handoff automático entre etapas adjacentes (planner→generator, generator→master) | ❌ Não existe — lacuna registrada, fora do escopo desta rodada |
| `aidd-bridge` reconhecendo corretamente projetos Next.js de origem (hoje só reconhece Vite/SPA) | ❌ Não corrigido — pendência separada |

