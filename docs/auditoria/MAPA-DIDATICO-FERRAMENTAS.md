# Mapa Mental: A Anatomia de uma Ferramenta (Lens 15-D)

Para criar ou debugar uma ferramenta no Ecossistema AIDD, imagine uma **Fábrica de Alta Precisão** operando dentro de uma **Redoma de Vidro**.

Este mapa usa essa analogia para gravar na sua mente a arquitetura inquebrável (Lens 15-D) de todas as nossas ferramentas, agrupada em 4 grandes fases.

---

## Fase 1: Governança e Blindagem (Preparação)
Antes das máquinas ligarem, ocorre a triagem e segurança.
- **O Regulamento (D1):** O livro de regras da fábrica (o arquivo `SKILL.md` ou `AGENTS.md` local).
- **A Esteira de Entrada (D2):** A matéria-prima chega, via pedido do usuário ou caminhão do turno anterior (Handoff).
- **A Redoma de Vidro (D3):** Para proteger a cidade (repositório real), a fábrica é montada num ambiente hermético (Git Worktrees isoladas). Risco zero de impacto colateral.
- **As Caixas de Ferramentas (D4):** O carregamento de MCPs, Hooks e Micro-ferramentas (A natureza fractal) que a fábrica utilizará.

## Fase 2: O Chão de Fábrica (Workflow - D5 a D10)
Aqui é onde a transformação ocorre. 
A esteira passa por várias micro-estações (Estágios). Em cada estação, observamos microscopicamente: **O que a máquina faz, o que ela engole (recebe), a prensa descendo (processa) e a peça nova saindo (entrega)**.
Tudo isso amarrado por uma rede de trilhos (Orquestração). Os "Templates" operam aqui, como as formas estáticas de ferro fundido nas quais a máquina injeta os dados crus.

## Fase 3: Resiliência e Operação Segura
Operários inteligentes lidam com o caos.
- **A Sirene de Emergência (D11 - Exceções):** Se a peça cair, a fábrica tem um loop de autocorreção ou ela paralisa?
- **Trabalho Silencioso (D12 - Frugalidade):** A fábrica não fala alto (gasto de tokens). Ela produz e carimba relatórios enxutos nos arquivos da chefia (pasta `secoes/`).

## Fase 4: O Inspetor e a Saída
- **O Inspetor Linha-Dura (D13 e D14 - Quality Gates):** Um script determinístico sem coração fica na porta de saída. Se a peça estiver milímetros menor: **EXIT 1** (Rollback/Rejeição). Se estiver perfeita: **EXIT 0**.
- **O Caminhão de Saída (D15 - Output e Handoff):** A peça validada vai para o mundo real, junto com a prancheta de instruções para a próxima fábrica começar seu turno.

---

### Diagnóstico Visual (Engenharia Reversa)
- A peça falhou na montagem? Inspecione a **Fase 2 (Workflow)**.
- O sistema caiu e ninguém avisou? Inspecione a **Fase 3 (Tratamento de Exceções)**.
- A peça saiu quebrada para o cliente final? Demita o Inspetor na **Fase 4 (Quality Gate)**.
- Tudo explodiu e destruiu a cidade inteira? O defeito estava na redoma da **Fase 1 (Isolamento)**.
