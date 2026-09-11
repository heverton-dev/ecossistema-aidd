# Item 7 — Definir e documentar convencao unica de nomenclatura PT-BR e ingles entre as ferramentas

> **Escopo:** Entra: apresentar ao usuário as opções reais de convenção de nomenclatura observadas hoje no código, colher a decisão explícita dele (não fabricar escolha), e documentar a convenção escolhida em `AGENTS.md`/`CLAUDE.md` (regra de estilo, não código executável). Não entra: renomear em massa qualquer identificador já existente no código — isso seria uma mudança grande, de alto risco e baixo valor imediato (quebra referências, testes, imports), e fica fora deste item; a convenção documentada vale para código **novo** escrito daqui pra frente.

> **Status:** ✅ Concluído em 2026-09-09 — decisão colhida diretamente do usuário (formalizar o padrão já observado, sem renomear código existente) e documentada em `AGENTS.md`, seção "4.1 CONVENÇÃO DE NOMENCLATURA DE CÓDIGO (PT-BR / INGLÊS)".

---

## Contexto já investigado

- Padrão observado hoje (sem regra escrita): nomes de infraestrutura/framework em inglês (`SecurityGate`, `JWTService`, `MCPServer`, `CircuitBreaker`) e nomes de domínio de negócio em português (`materializar`, `dimensionar`, `reconhecer_nicho`, `sincronizar_componente`) — consistente entre as 5 ferramentas, mas nunca escrito como regra em `AGENTS.md`/`CLAUDE.md`.
- Este item é uma decisão de produto/estilo, não uma correção mecânica — não cabe ao agente escolher a convenção sozinho.

## Definição de Pronto

1. ✅ Opções apresentadas ao usuário (manter o padrão observado hoje formalizado como regra; tudo em inglês; tudo em português) e decisão explícita registrada aqui com data: usuário escolheu "Formalizar o padrão observado" em 2026-09-09.
2. ✅ Regra documentada em `AGENTS.md`, seção nova "4.1 CONVENÇÃO DE NOMENCLATURA DE CÓDIGO (PT-BR / INGLÊS)", com exemplos reais do próprio código (`SecurityGate`, `JWTService`, `MCPServer`, `CircuitBreaker` para técnico/inglês; `materializar`, `dimensionar`, `reconhecer_nicho`, `sincronizar_componente` para domínio/português).
3. ✅ Nenhum identificador existente foi renomeado como parte deste item.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 7: Definir e documentar convencao unica de nomenclatura PT-BR e ingles entre as ferramentas.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 7: Definir e documentar convencao unica de nomenclatura PT-BR e ingles entre as ferramentas.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
