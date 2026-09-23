# O Molde Universal das Ferramentas (The Ecosystem Blueprint)

Este documento define a arquitetura técnica universal que QUALQUER ferramenta deve possuir para ser acoplada ao Ecossistema AIDD. 

O molde é regido pelas 4 Macro-Fases de Engenharia do framework **Lens 15-D**. Se uma ferramenta não cobrir estes pilares estruturais, ela é ilegítima.

## Fase 1: Governança e Blindagem (Segurança)
1. **O Contrato (SKILL.md / AGENTS.md):** A ferramenta precisa declarar suas regras, frontmatter YAML e schema de Handoff exigido.
2. **Blast Radius (Isolamento Mecânico):** É OBRIGATÓRIO provisionar uma "bolha" (Git Worktree efêmera, ou diretório `tmp/`) para executar o processamento. A ferramenta não altera código da master diretamente durante o workflow.

## Fase 2: O Chão de Fábrica (Processamento)
3. **Motores Mecânicos (scripts/):** A lógica de transformação massiva usa bash ou Python AST. É proibido depender exclusivamente da IA (LLM) para codificação estrutural repetitiva (Lei #1: Separação entre Inteligência e Força Bruta).
4. **O Chassi Estático (templates/):** Repositório de moldes e scaffolding. A ferramenta injeta dados; ela nunca alucina o padrão arquitetural do zero.
5. **Recursividade Geométrica (Micro-ferramentas):** Qualquer skill recrutada pela ferramenta deve possuir internamente este exato mesmo molde e isolamento de segurança.

## Fase 3: Resiliência e Frugalidade (Eng. Operacional)
6. **Operação Muda (Lei #4):** Ferramentas operam via `stdout/stderr` canalizado e exit codes. É proibido jorrar textos conversacionais.
7. **Agnosticismo (Lei #6):** Deve executar sem atrito no Windows, Linux ou CLI, indiferente do provedor LLM que orquestra a chamada.

## Fase 4: O Regime Autoritário (Validação e Entrega)
8. **Os Juízes (gates/G_<NOME>.py):** Scripts isolados que validam tipagem, estrutura e regras da saída gerada. Devem retornar `0` ou `1`. E provar que falham (Lei #13).
9. **O Rastro Final (secoes/ e handoff.json):** Emissão da telemetria de decisões e do Handoff validado, atuando como o Input imaculado para o elo seguinte da corrente.
