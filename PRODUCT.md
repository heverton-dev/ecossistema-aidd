# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

HTML5 semântico, Vanilla JavaScript moderno (ES2022+), CSS3 com variáveis customizadas (Zero frameworks pesados, zero dependências externas de CDN, compatibilidade local e offline estrita). Servidor backend em Python puro (`http.server`) integrado com SQLite e contracts JSON.

## Users

Engenheiros de software, arquitetos agênticos e operadores do Ecossistema AIDD. O usuário opera tarefas de desenvolvimento autônomo e de longa duração no desktop e utiliza o smartphone conectado à mesma rede Wi-Fi (via QR Code) como painel de monitoramento e intervenção tátil à distância.

## Product Purpose

Quadro AIDD é o console operacional unificado para visualização, rastreamento, diagnóstico e remediação em tempo real dos pipelines do ecossistema AIDD (Tríade Pure, Open, Freedom; Auditoria 4F; Evolução; 72 Quality Gates e Worktrees VSA).

## Positioning

Console determinístico com zero ruído de métricas inventadas: 100% dos dados, status, logs de streaming e LEDs de portões refletem estados factuais do sistema de arquivos e processos locais do AIDD (Lei #8 — Honestidade de Rótulo).

## Operating Context

- **Desktop**: Console denso de monitoramento em tela secundária ou janela dividida (1080p a 4K).
- **Mobile (Smartphones Wi-Fi)**: Companion touch acessado via QR Code no celular (390px a 430px de largura de tela, orientação retrato), com foco em legibilidade, status imediato, inspeção de falhas e disparo de ações remediadoras com uma mão.

## Capabilities and Constraints

- **Visão dos 12 Pipelines**: Cards operacionais com identificação da etapa atual, cronômetro vivo na fase e progresso relativo.
- **Trilha Kanban & Topologia**: Visualização das fatias e etapas canônicas com worktrees efêmeras.
- **Matriz de Gates (72 LEDs)**: Painel de LEDs auditando conformidade instantânea com as 13 Leis Invioláveis.
- **Gaveta Lateral de Inspeção**: Drawer com visão geral de métricas, timeline cronológica, terminal logtail em tempo real e JSON factual colapsado.
- **Acesso Local Seguro**: QR Code com resolução determinística de IP LAN RFC 1918 e bind em porta dedicada (8990).
- **Restrição de Conexão**: Funcionar 100% local sem requisições para a internet aberta (Zero CDNs, fontes locais/do sistema).

## Brand Commitments

- Modo: **Operate** (clareza operacional, contraste nítido, alta densidade sem poluição, sem gradientes de brinquedo ou emojis infantis).
- Cores Semânticas: Ciano elétrico (execução ativa), Esmeralda (sucesso), Carmesim (falha/parado), Âmbar (ação humana necessária), Ardósia (neutro).
- Tipografia: Interface em System Font Stack limpa e métricas/código em JetBrains Mono / SF Mono / Consolas.

## Evidence on Hand

- Código vivo em `scripts/quadro/` (`index.html`, `quadro.css`, `quadro.js`).
- Backend operacional em `scripts/quadro_servidor.py` e `scripts/quadro_leitor.py`.
- Contratos ativos em `modulos/04-nucleo-compartilhado/contracts/PIPELINES.json` e `MAPA-GATES.json`.

## Product Principles

1. **Factualidade Radical**: Nunca simular ou maquiar estado — se um processo morreu, reportar como interrompido.
2. **Zero Poluição Visual**: Hierarquia limpa onde o erro ou necessidade de ação humana salta aos olhos imediatamente.
3. **Ergonomia Mobile-First no Celular**: Toques confortáveis (≥44px), zero rolagem horizontal descontrolada na tela do smartphone, gaveta em folha completa com botões ao alcance do polegar.
