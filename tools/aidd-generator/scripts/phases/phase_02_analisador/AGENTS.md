# Phase 02 — Analisador (Micro-Ambiente)

## Escopo
Análise estratégica da ideia + referências via LLM (protocolo delegado ou headless).

## Restrições
- LLM via `solicitar_llm()` de `utils_delegacao.py` — NUNCA chamada direta a litellm
- Prompt em Inglês (economia de tokens), output em PT-BR
- Referências citadas devem vir da Fase 1 — NUNCA fabricar citações

## Regras de Negócio
- O analisador DEVE extrair: objetivo, público-alvo, stack recomendado, arquitetura, diferenciais
- Cada campo obrigatório deve ter valor real (nunca vazio ou genérico)
- O JSON de saída DEVE seguir o schema `analise_phase2_schema` com tipagem estrita
- Referências da Fase 1 são input obrigatório — sem referências, a análise é honesta sobre lacunas
- Stack recomendado DEVE ser coerente com as referências encontradas (não inventar stack sem evidência)

## Gates
- A1: Schema do JSON de análise válido
- A2: Zero alucinação (referências reais ou vazio honesto)
- A3: Dados completos (stack, público, diferenciais)
- A4: Qualidade de linguagem (sem TODO/pass)

## MCPs
- Filesystem MCP (leitura de insights_phase1.json)

## Saída
- `_phase_02_index.json` em `.aidd/cache/data/`
- `analise_phase2.json` em `.aidd/cache/data/`

## Tokens
- Consumo: ~5k (LLM estratégica)
- Determinismo: 0% (pura LLM)
