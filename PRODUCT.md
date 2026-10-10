# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Python `http.server` puro (backend local) com Vanilla HTML5, Modern CSS3 (OKLCH tokens, container queries, dark/light themes) e Vanilla ES6+ (zero build, zero CDN, zero dependências externas).

## Users

Desenvolvedor e Engenheiro de IA operando o ecossistema AIDD localmente. Precisa inspecionar e monitorar pipelines de longa duração, ciclos de auditoria 4F, despacho VSA em worktrees efêmeras, status de baterias de gates e requisições de decisão humana em tempo real.

## Product Purpose

Fornecer um cockpit visual (Quadro Kanban AIDD) para observabilidade em tempo real e rastreabilidade histórica de todos os 12 pipelines do ecossistema, eliminando a opacidade de terminais isolados e permitindo ação rápida com comandos copiáveis.

## Positioning

Observador estritamente local e determinístico: não executa ações destrutivas ou arrasto ambíguo de cartões; traduz eventos de orquestração em uma visão de fluxo industrial límpida com foco em desobstrução de barreiras e ação do operador no terminal (Lei #7 - Desenvolvedor no Controle).

## Operating Context

- Ambiente: Desktop local (Windows/Linux/macOS), rodando em `http://127.0.0.1:8990` via `python ecossistema.py quadro`.
- Consumo: Monitor secundário ou aba fixa ao lado da IDE/Terminal.
- Ciclo de interação: Visão passiva de pulso a cada 2s com intervenção imediata quando surge o selo "precisa de você".

## Capabilities and Constraints

- Capacidades: Grade de pipelines com métricas ao vivo; Kanban detalhado por pipeline com etapas formais do contrato `PIPELINES.json`; Gaveta lateral estruturada em 5 blocos (linha do tempo, entregas, diagnóstico de paradas, comandos para copiar e dados brutos); Aba Arquivo com filtros e busca; Suporte a temas Claro e Escuro.
- Restrições Invioláveis: Zero dependências externas (sem CDN, sem npm, sem frameworks JS); Zero polling desnecessário (pausa quando aba oculta); Segurança local estrita (escrita atômica, leitura segura de artefatos até 512KB sem XSS).

## Brand Commitments

- Estética: Cyber-Industrial Moderno / Dark Mode refinado (estilo Linear/Vercel/Raycast), equilibrado com tema Claro de alta nitidez.
- Cores: Acentos semânticos funcionais (esmeralda para sucesso, azul cibernético para execução viva, âmbar elétrico para espera humana, carmesim para falhas/paradas, ardósia profunda para superfícies).

## Evidence on Hand

- Contrato canônico vivo: `modulos/04-nucleo-compartilhado/contracts/PIPELINES.json`
- Schema de estado de execução: `modulos/04-nucleo-compartilhado/contracts/estado-execucao.schema.json`
- Relatórios factuais de auditoria e evidências: `docs/auditoria/quadro-kanban-pipelines/ciclo-01/`

## Product Principles

1. Densidade sem Ruído: Priorizar scan visual instantâneo dos estados dos pipelines sobre ornamentos vazios.
2. Honestidade de Estado: Nunca mascarar paradas; o motivo e o log devem ser imediatamente visíveis na gaveta.
3. Desobstrução Operacional: Se o pipeline parou por decisão humana, o comando exato para desbloqueio deve estar pronto para cópia em um clique.
4. Robustez Silenciosa: Interface resiliente a reconexões, leve na CPU (< 0.5%) e compatível com preferências do sistema (redução de movimento e tema).

## Accessibility & Inclusion

- WCAG 2.1 AA contraste estrito para texto e estados semânticos.
- Suporte a `prefers-reduced-motion` desativando pulsos ou transições.
- Acessibilidade por teclado (tecla Esc para fechar gavetas, navegação por Tab).
