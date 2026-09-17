# Proposta de Evolução Arquitetural: Os 3 Fluxos Canônicos de Criação e Entrega do Ecossistema AIDD

> **Status:** Aprovado para Implementação  
> **Data:** 17/09/2026  
> **Localização:** `docs/melhorias/MELHORIA-3-FLUXOS-CRIACAO-ECOSSISTEMA.md`  
> **Origem:** Alinhamento Estratégico com a Liderança Técnica  

---

## 1. O Problema Identificado

Anteriormente, as ferramentas de criação de código do ecossistema (`aidd-generator`, `aidd-factory` e `aidd-bridge`) apresentavam sobreposições conceituais e competiam entre si pelo mesmo espaço:
* O `aidd-generator` gerava aplicações do zero, mas sem conexão formal com o planejamento de motores.
* O `aidd-factory` tentava planejar infraestrutura, buscar nichos e gerar código, colidindo com o `aidd-ops` e gerando divergências arquiteturais.
* O `aidd-bridge` operava de forma isolada, sem um pipeline estruturado de recepção e entrega.
* O desenvolvedor não possuía um ponto único de planejamento prévio que permitisse derivar a mesma ideia de negócio em diferentes estratégias de entrega.

---

## 2. A Nova Visão Arquitetural: A Tríade Canônica

Toda aplicação de alta robustez passa a ser criada a partir de uma **Fundação Canônica Universal (`aidd-forge`)** e um **Planejador Interativo Central (`PRÉ-PLANO`)**, que dá ao desenvolvedor a liberdade de escolher qual dos **3 Fluxos Especializados** disparar para o mesmo projeto:

```
                      ┌────────────────────────┐
                      │       aidd-forge       │
                      │ (Governança & Regras)  │
                      └───────────┬────────────┘
                                  │
                                  ▼
                      ┌────────────────────────┐
                      │       PRÉ-PLANO        │
                      │  (Entrevista & Spec)   │
                      └───────────┬────────────┘
                                  │
               Escolha do Desenvolvedor no Pré-Plano
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
   [ FLUXO 01 ]             [ FLUXO 02 ]             [ FLUXO 03 ]
  aidd-generator            aidd-factory             aidd-bridge
 (Do Zero Puro / VSA)    (Motores Open-Source)     (Low-Code Desatado)
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                                  ▼
                      ┌────────────────────────┐
                      │      aidd-master       │
                      │ (Fatias VSA de Domínio)│
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

---

## 3. As Responsabilidades Recalibradas das Ferramentas

### 1. `aidd-forge` — O Ditador Supremo de Regras e Governança
* **Papel:** É a autoridade máxima de governança do projeto.
* **O que faz:**
  * Dita e injeta todas as regras arquiteturais (Vertical Slice Architecture, Clean Architecture).
  * Configura convenções estritas de código, tipagem estática e linting.
  * Injeta as políticas de **economia severa de tokens** e comunicação concisa.
  * Estabelece os Quality Gates de pré-commit e pré-push que impedem regressões.
* **Entrega:** Repositório padronizado, protegido contra contaminação e preparado para os próximos passos.

---

### 2. O Motor de `PRÉ-PLANO` (Planning Engine & Intake Interativo)
* **Papel:** É o cérebro de planejamento e alinhamento prévio antes de qualquer código ser gerado.
* **O que faz:**
  * Realiza uma entrevista interativa com o usuário (ideia de negócio, requisitos, integrações, limites de hardware).
  * Gera o documento canônico `PLANO-MESTRE.json` e a especificação técnica do sistema.
  * Apresenta ao usuário a escolha estratégica:
    * **Opção 1:** Construir a aplicação **do zero puro** sob medida?
    * **Opção 2:** Alavancar a aplicação sobre **motores open-source existentes**?
    * **Opção 3:** Resgatar e unificar **telas e protótipos low-code** (Lovable/v0/Bolt)?
* **Entrega:** Especificação arquitetural validada e o gatilho de execução do fluxo selecionado.

---

### 3. Os 3 Motores Especializados de Construção

| Fluxo | Motor | Especialidade Estrita | O que Produz |
| :--- | :--- | :--- | :--- |
| **FLUXO 01** | **`aidd-generator`** | Código puro do zero sem dependência externa | Pipeline de 8 fases: Spec formal, testes TDD Red-Green, regras de negócio puras em fatias VSA e o Quarteto *Sine Qua Non*. |
| **FLUXO 02** | **`aidd-factory`** | Alavancagem sobre software livre consolidado | Identificação e orquestração de motores open-source (filas, bots, mensageria), gerando fatias VSA de integração e clientes tipados. |
| **FLUXO 03** | **`aidd-bridge`** | Libertação e empacotamento de protótipos | Remoção de vendor lock-in de Lovable/v0/Bolt, reconexão direta ao PostgreSQL corporativo e conteinerização do frontend. |

---

### 4. O Funil Universal de Convergência e Produção

Independentemente do fluxo escolhido, a entrega de código converge obrigatoriamente para a mesma esteira de qualidade:

1. **`aidd-master` (Harmonização em Monólito Modular):**
   * Organiza todas as funcionalidades geradas em **Monólito Modular**:
     * **Eixo Vertical (VSA):** Fatias verticais autônomas por domínio de negócio (`features/`), encapsulando rotas, schemas, regras e repositórios locais.
     * **Eixo Horizontal Compartilhado (`core/` / `shared/`):** Serviços transversais padronizados (banco de dados, autenticação, observabilidade, middlewares, gateway de eventos).
   * Garante isolamento estrito de dependências entre fatias e roteamento unificado.

2. **`aidd-enterprise` (Blindagem de Missão Crítica):**
   * Audita a integridade do código contra adulterações via hash **SHA-256**.
   * Injeta componentes corporativos de resiliência: Circuit Breakers, Rate Limiting distribuído, Retries com backoff, sanitização estrita e trilha de auditoria (`trace_id`).

3. **`aidd-ops` (Infraestrutura, Segurança e Produção):**
   * Provisiona a infraestrutura de destino via SSH determinístico.
   * Criptografa variáveis e segredos de ambiente com `sops + age`.
   * Sobe os containers na VPS com SSL/Reverse Proxy e ativa a observabilidade em tempo real com Uptime Kuma.

---

## 4. O Quarteto *Sine Qua Non* Presente em Todos os Fluxos

Todo e qualquer projeto, independentemente de ter nascido no Fluxo 1, 2 ou 3, **DEVE conter nativamente**:
* 📑 **`/swagger`**: Contratos REST interativos OpenAPI 3.0.
* 🔔 **`/webhooks`**: Gestão e simulação de eventos assíncronos com assinatura HMAC.
* 🤖 **`/mcp`**: Exposição de ferramentas para agentes inteligentes via Model Context Protocol.
* 📚 **`/docs`**: Manuais vivos de utilização e integração para equipes humanas.

---

## 5. Plano de Execução da Melhoria

1. **Documentação e Governança:**
   * Atualizar o `AGENTS.md` e os arquivos de protocolo para refletir oficialmente os 3 Fluxos Canônicos e a soberania do `aidd-forge`.
2. **Criação do Módulo de `PRÉ-PLANO`:**
   * Criar o comando unificado `ecossistema.py plan` (ou integrar via interface interativa de terminal) com o questionário socrático e gerador de `PLANO-MESTRE.json`.
3. **Calibração das Ferramentas:**
   * **`aidd-forge`**: Hardening das regras globais de governança e economia de tokens.
   * **`aidd-generator`**: Foco 100% no fluxo do zero puro.
   * **`aidd-factory`**: Foco 100% no consumo do plano para integração de motores open-source.
   * **`aidd-bridge`**: Foco 100% na limpeza de low-code e entrega de frontend desacoplado.
4. **Validação E2E:**
   * Testar a derivação de um mesmo projeto conceitual nos 3 caminhos com aprovação integral nos Quality Gates.
