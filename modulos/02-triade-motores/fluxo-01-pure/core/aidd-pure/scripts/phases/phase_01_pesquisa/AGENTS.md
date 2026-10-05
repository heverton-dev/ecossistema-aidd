# Phase 01 — Pesquisador (Micro-Ambiente)

## Escopo
Pesquisa projetos de referência reais (GitHub API, HuggingFace API) para qualquer ideia de projeto.

## Restrições
- APENAS Python puro (Zero Token de LLM)
- APIs externas: GitHub (requests), HuggingFace (requests)
- Nenhuma credencial hardcoded — usar .env ou variáveis de ambiente
- Dados REAIS apenas — fallback DADOS_TESTE é PROIBIDO

## Gates
- R1: URLs válidas (começam com https://)
- R2: Atividade recente (pushed_at dentro de 2 anos)
- R3: Estrutura mínima (name, description, url)
- R4: Quantidade mínima (≥3 referências)

## MCPs
- Filesystem MCP (leitura/escrita de cache)

## Saída
- `_phase_01_index.json` em `.aidd/cache/data/`
- `insights_phase1.json` em `.aidd/cache/data/`

## Tokens
- Consumo: 0 (100% determinístico)
- Justificativa: Python puro + requests, zero LLM
