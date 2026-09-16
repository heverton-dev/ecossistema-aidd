# Plano de Implementação Arquitetural: Fatias Lógicas e Isolamento de Dados

> **Relatório Técnico & Plano Estruturado**  
> **Data:** Setembro de 2026  
> **Escopo:** Ecossistema AIDD, Ferramentas (`tools/aidd-*`) e Aplicações Geradas (`planos-ctt-app`)  

---

## 1. Matriz Geral de Implementação

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           MATRIZ DE IMPLEMENTAÇÃO ARQUITETURAL                          │
├─────────────────────────┬───────────────────────────────────┬───────────────────────────┤
│ Nível                   │ Parte 1: Fatias Lógicas (VSA)     │ Parte 2: Isolamento Dados │
├─────────────────────────┼───────────────────────────────────┼───────────────────────────┤
│ 1. Ecossistema          │ Governança, Templates de Slice    │ Protocolo de Repositórios │
│    (`ecossistema-aidd`) │ e Quality Gates de isolamento     │ e Schemas independentes   │
├─────────────────────────┼───────────────────────────────────┼───────────────────────────┤
│ 2. Ferramentas          │ Gerador de código vertical        │ Scaffolding de DB/schemas │
│    (`aidd-master/gen`)  │ automatizado (FE + BE acoplados)  │ com migrações por módulo  │
├─────────────────────────┼───────────────────────────────────┼───────────────────────────┤
│ 3. Aplicação Entregue   │ Fatias completas: Frotas,         │ Tabelas/repositórios      │
│    (`planos-ctt-app`)   │ Encomendas, Rotas, Webhooks       │ estritamente isolados     │
└─────────────────────────┴───────────────────────────────────┴───────────────────────────┘
```

---

## 2. PARTE 1: Camadas Lógicas Verticais (Vertical Slice Architecture)

### A. O Que Fazer
Garantir que cada módulo funcional seja autossuficiente e possua internamente sua árvore completa de responsabilidade, sem acoplamentos ou importações diretas com outros módulos de negócio.

### B. Onde Fazer
1. **No Ecossistema / Ferramentas:**
   - `tools/aidd-master/`: Padronizar o gerador de fatias verticais para novos projetos.
   - `componentes/compartilhado/`: Manter templates espelhados de Frontend (Next.js) e Backend (FastAPI).
2. **Nas Aplicações Entregues (`planos-ctt-app`):**
   - **Backend (`src/modules/<modulo>/`):**
     - `router.py`: Endpoints REST exclusivos do domínio.
     - `service.py`: Casos de uso e regras de negócio.
     - `dtos.py`: Schemas Pydantic de entrada e saída.
     - `events.py`: Eventos de domínio emitidos pela fatia.
   - **Frontend (`web/src/` ou `web/src/modules/<modulo>/`):**
     - `hooks/use<Modulo>.ts`: Gerenciamento de estado e requisições HTTP.
     - `components/`: Componentes de UI exclusivos daquele contexto de negócio.
     - `types.ts`: Tipagens TypeScript espelhando os contratos de API.
     - `page.tsx`: View final que compõe a interface da fatia.

### C. Como Aplicar
- **Regra de Isolamento Rígido:** O módulo `frotas` nunca importa diretamente arquivos internos de `encomendas_ctt`.
- **Comunicação Inter-Módulos:**
  1. Consulta síncrona via interfaces públicas de serviço (ex: `FrotasService.obter_veiculo(id)`).
  2. Notificação assíncrona via barramento de eventos (`EventBus.publish('frota.alerta')`).

---

## 3. PARTE 2: Isolamento da Camada de Dados (Data Access Layer)

### A. O Que Fazer
Garantir que os dados pertençam estritamente a cada módulo, eliminando dependências físicas duras (como `JOINs` SQL cruzados entre tabelas de módulos distintos), permitindo a futura extração de qualquer módulo para um banco ou serviço independente (PostgreSQL, Traccar, Fleetbase) sem reescrever o código.

### B. Onde Fazer
1. **No Backend (`src/modules/<modulo>/`):**
   - Cada fatia possui seu próprio arquivo de repositório:
     - `src/modules/frotas/repository.py`
     - `src/modules/encomendas_ctt/repository.py`
     - `src/modules/roteirizacao/repository.py`
2. **Nas Migrações e DDL (`src/core/database/migrations/`):**
   - Versionamento de scripts DDL por módulo (`001_frotas.sql`, `002_encomendas.sql`).

### C. Como Aplicar
- **Chaves Lógicas em vez de Chaves Estrangeiras Físicas Rígidas:**
  - Armazenar identificadores lógicos (`veiculo_id`, `codigo_rastreio`) na tabela de rotas em vez de `FOREIGN KEY` física acoplada à tabela de frotas.
  - O serviço da fatia valida a integridade consultando o serviço do módulo correspondente.
- **Preparação para Microsserviço:** Se um dia o módulo de frotas for delegado ao Traccar, o módulo de roteirização não sofre quebra estrutural no banco de dados.

---

## 4. Fases de Execução Recomendadas

1. **Fase 1 (Aplicação):** Segregar os repositórios em arquivos `repository.py` dedicados dentro de cada pasta em `proj_ctt/planos-ctt-app/src/modules/`.
2. **Fase 2 (Governança):** Registrar o checklist de validação em `ecossistema-aidd/tools/aidd-master/AGENTS.md` para que o quality gate do AIDD Master audite o isolamento das fatias automaticamente.
