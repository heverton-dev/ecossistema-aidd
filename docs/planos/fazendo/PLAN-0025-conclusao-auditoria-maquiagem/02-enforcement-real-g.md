# Item 2 — Enforcement real em G_ZERO_HEADLESS

> **Escopo:** Entra: escolher e implementar UMA das duas rotas abaixo para a Regra de Ouro #7 (Zero Subagentes Headless). Não entra: reescrever `orchestrator_engine.py` inteiro ou mexer no protocolo ORCA ADE em geral.
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** NAO AUDITADO — evidencia: (nota pendente de medicao real - nao preencher com estimativa)
> **Nota Alvo (0-10):** NAO AUDITADO
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- `gates/G_ZERO_HEADLESS.py` (37 linhas) apenas confere presença literal de duas strings (`'interactive: bool = True'` num arquivo, `'--dangerously-force-headless'` noutro) — é um grep de configuração, não uma trava de comportamento em runtime.
- `AGENTS.md` §2 regra 7 e `MEMORY.md` §5 apresentam essa regra como proteção ativa contra "subagentes headless paralelos invisíveis", o que hoje não corresponde à implementação: nenhum mecanismo no repositório impede um assistente de disparar `Task`/`Agent` em paralelo — depende inteiramente do assistente obedecer a instrução em texto.

## Definicao de Pronto

**Rota A — enforcement real:** implementar um hook de harness (ex.: Claude Code hook em `settings.json` que intercepta/bloqueia chamadas concorrentes de `Task`/`Agent` sem confirmação) e reproduzir tentando disparar 2 subagentes em paralelo — o hook deve bloquear ou exigir confirmação de verdade.

**Rota B — honestidade de escopo:** reescrever `AGENTS.md`/`MEMORY.md`/a mensagem de saída do próprio gate para deixar explícito que ele é um lint estrutural de *presença de configuração*, não um enforcement de runtime — e mover a responsabilidade real de bloqueio para instrução de prompt/CLAUDE.md, documentada como tal (sem alegar proteção que não existe).

1. Rota escolhida com o usuário, registrada aqui com justificativa antes de codar.
2. Gate e documentação (AGENTS.md, MEMORY.md) ficam coerentes entre si após a mudança — nenhum texto alega mais proteção do que o mecanismo real entrega.
3. Reprodução real documentada (tentativa de burlar e resultado observado), não suposição.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 2: Enforcement real em G_ZERO_HEADLESS.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 2: Enforcement real em G_ZERO_HEADLESS.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
