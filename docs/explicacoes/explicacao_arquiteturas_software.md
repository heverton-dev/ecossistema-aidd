# Comparativo de Arquiteturas de Software no Ecossistema AIDD

> **Documento:** Explicação Técnica e Guia Arquitetural  
> **Data:** Setembro de 2026  
> **Status:** Referência Canônica de Arquitetura  

---

## 1. Visão Geral dos Principais Modelos

```
┌────────────────────────┐      ┌────────────────────────┐      ┌────────────────────────┐
│  Monólito Tradicional  │      │    Monólito Modular    │      │     Microsserviços     │
│  (Camadas Horizontais) │      │ (Vertical Slices / VSA)│      │  (Serviços Distribuídos│
├────────────────────────┤      ├────────────────────────┤      ├────────────────────────┤
│   Controllers Todos    │      │  [Frota: UI+BE+DB]     │      │   [Serviço Frota]      │
│   Services Todos       │  ──> │  [Encomenda: UI+BE+DB] │  ──> │   [Serviço Encomenda]  │
│   Repositories Todos   │      │  [Rotas: UI+BE+DB]     │      │   [Serviço Rotas]      │
│   Banco de Dados Único │      │  Shared Kernel Único   │      │   Bancos Separados     │
└────────────────────────┘      └────────────────────────┘      └────────────────────────┘
```

---

## 2. Detalhamento dos Quatro Modelos

### A. Monólito Tradicional (Horizontal / Layered Architecture)
- **Estrutura:** Organização por tipo técnico de arquivo (`controllers/`, `services/`, `models/`, `repositories/`).
- **Pontos Positivos:** Rápido para protótipos de 1 ou 2 dias.
- **Pontos Negativos:** Acoplamento horizontal descontrolado ("código espaguete"). Alterações na regra de um módulo (ex: Frotas) frequentemente quebram regras de outros módulos (ex: Encomendas) devido ao compartilhamento desordenado de classes e queries.

### B. Monólito Modular (Vertical Slice Architecture — VSA)
- **Estrutura:** A aplicação executa como um processo único unificado, mas cada funcionalidade de negócio (`frotas`, `encomendas_ctt`, `roteirizacao`) é tratada como uma **fatia vertical autossuficiente** (UI + Controller + Service + Schema/Repositório).
- **Pontos Positivos:** Alto isolamento, coesão máxima, deploy em passo único, comunicação em memória com latência de microssegundos (sem overhead de rede) e ausência de transações distribuídas complexas.
- **Pontos Negativos:** Requer governança de código rígida para impedir importações diretas cruzadas entre fatias sem passar por contratos ou eventos.

### C. Microsserviços (Microservices / Distributed Architecture)
- **Estrutura:** Cada fatia funcional vira um serviço e repositório autônomo, com banco de dados físico próprio e deploy individual em container, comunicando-se via REST/gRPC/Kafka.
- **Pontos Positivos:** Independência de escala para times massivos (100+ engenheiros).
- **Pontos Negativos:** Complexidade exponencial de infraestrutura, latência de rede entre chamadas, necessidade de padrões complexos de consistência eventual (Saga Pattern, Outbox, 2-Phase Commit) e custos elevados de computação e monitorização.

### D. Arquitetura Orientada a Eventos / Hexagonal (Ports & Adapters)
- **Estrutura:** O núcleo da regra de negócio é puro e agnóstico ao meio de entrada/saída. A conexão com motores externos (ex: VROOM) ou canais de comunicação (Webhooks CTT, MCP Studio, REST API) ocorre via adaptadores intercambiáveis.
- **Pontos Positivos:** Altíssima testabilidade e facilidade de substituição de infraestrutura sem tocar nas regras de domínio.

---

## 3. Matriz de Impacto no Ecossistema AIDD

| Critério de Avaliação | Monólito Tradicional | Monólito Modular (VSA) | Microsserviços |
| :--- | :--- | :--- | :--- |
| **Impacto no Ecossistema (`ecossistema-aidd`)** | Auditoria frágil; testes quebram em cascata. | **Excelente**: Auditoria determinística por fatia (`ecossistema.py audit`). | Excessivo: orquestração de dezenas de repositórios e contratos de rede. |
| **Impacto nas Ferramentas (`tools/aidd-*`)** | Geração de código acoplada e difícil manutenção. | **Ideal**: O `aidd-master` e `aidd-generator` geram fatias completas e isoladas. | O `aidd-ops` precisaria gerenciar dezenas de pipelines e service meshes. |
| **Impacto na Aplicação Entregue (`planos-ctt-app`)** | Degradação rápida de manutenibilidade. | **Alta performance, coesa e robusta**: Frontend Next.js + Backend Python comunicando localmente. | Custo desnecessário de infraestrutura e latência de rede. |
| **Deploy e Infraestrutura (VPS / Swarm)** | 1 container monolítico sem separação clara. | **Otimizado**: 2 containers principais (`web` + `api`) + motores dedicados (VROOM). | 6 a 15 containers + Brokers de Mensageria + API Gateway. |
| **Consumo de Memória RAM** | ~200 MB | **~350 MB a 400 MB (Stack completa ativa)** | > 2.5 GB a 4 GB |
| **Latência entre Módulos** | Baixa (< 5ms) | **Ultrabaixa (< 1ms)** | Média/Alta (20ms - 100ms via rede) |

---

## 4. Situação Atual da Aplicação em Produção

A aplicação **`planos-ctt-app`** opera hoje em **Monólito Modular com Vertical Slice Architecture (VSA)**:
1. **Shared Kernel (`src/core/`):** Fornece criptografia PBKDF2/HMAC-SHA256, barramento de eventos, transações SQLite em modo WAL e auditoria imutável (WORM).
2. **Fatias Verticais (`src/modules/` e `web/src/`):**
   - `frotas`: Gestão de 5 veículos reais CTT com especificações técnicas.
   - `encomendas_ctt`: Rastreamento de remessas com códigos de envio portugueses.
   - `roteirizacao`: Intermediação com o motor **VROOM** em C++.
   - `webhooks`: Ingestão assíncrona orientada a eventos.
   - `mcp`: Servidor JSON-RPC 2.0 para agentes de inteligência artificial.

---

## 5. Veredito e Modelo Mais Elegível

O modelo mais elegível e recomendado para o Ecossistema AIDD é o **Monólito Modular com Vertical Slice Architecture (VSA)**, pois:
1. Garante isolamento real de código e de dados sem pagar o preço da complexidade e dos custos de infraestrutura de microsserviços.
2. Permite migração futura imediata: caso um módulo (ex: telemetria de frotas) precise rodar isolado no Traccar, a extração é limpa porque a fatia já é 100% autônoma.
