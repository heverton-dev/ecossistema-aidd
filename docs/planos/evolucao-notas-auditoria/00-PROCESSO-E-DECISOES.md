# PROCESSO E DECISÕES — Evolução das Notas da Auditoria Técnica

> **Origem:** `docs/relatorios/relatorio-auditoria-ecossistema-aidd.html` (nota consolidada 7.5/10) e `docs/planos/PLANO-EVOLUCAO-NOTAS-AUDITORIA.md` (diagnóstico profundo dos 8 gaps).
> **Decisão registrada em:** 05/09/2026.
> **Propósito deste arquivo:** registro único e consultável do *processo* que vamos seguir — não do conteúdo técnico de cada correção (isso vive em documentos próprios por pacote, ver §4). Sempre que houver dúvida sobre "como estamos trabalhando isso", a resposta está aqui.

---

## 1. A decisão

Em vez de corrigir os 8 gaps da auditoria em qualquer ordem ou todos de uma vez, decidimos tratar cada um como um **ciclo fechado e independente**:

```
análise profunda → Definição de Pronto travada → plano exaustivo → implementação minuciosa → teste extremo → validação → registro → PRÓXIMO PACOTE
```

Um pacote só é considerado concluído quando passa pela validação — nunca antes. Nenhum pacote começa sem que sua Definição de Pronto (§3) esteja escrita e acordada primeiro.

---

## 2. Por que pacotes, não os 8 gaps originais um a um

Dois dos 8 gaps da auditoria original são, na prática, o mesmo trabalho físico (mesma correção, mesmo arquivo) descrito sob duas dimensões diferentes. Tratá-los como ciclos separados reabriria o mesmo código duas vezes. Por isso, os 8 gaps foram reagrupados em **6 pacotes de trabalho reais**:

| # | Pacote | Gaps originais fundidos aqui |
|---|---|---|
| 1 | Transparência + Gates Mecânicos | Bug `--command`; gate novo de consistência CLI-vs-help |
| 2 | Testabilidade + Determinismo | Cobertura real de `add_module.py` (mesma classe de risco do `compose_suite.py`) |
| 3 | Modularização | Divergência do injector `aidd-master` vs `aidd-enterprise`; ponto cego do gate de drift |
| 4 | Cobertura dos comandos restantes | `audit`, `plan`/`apply`, `compose-orca`, `refine-module`, `bench`, `export-frontend`, `setup` |
| 5 | Economia de Tokens + Engenharia Agêntica | Rotulagem `medido` vs `autodeclarado` no protocolo delegado |
| 6 | Universalidade | Sem ciclo de implementação — ver §5 |

**Pacote 7 — adicionado em 05/09/2026, fora dos 8 gaps originais:** por pedido explícito do usuário, um gap novo (não coberto pela auditoria original) entrou no mesmo processo — distribuição incompleta de componentes (skills/MCPs/specs/config/hooks) entre pastas de harness, violando a Regra de Ouro #6 (Supremacia Agnóstica) do `AGENTS.md`. Diagnosticado inicialmente por um agente externo a pedido do usuário; verificado por amostragem independente antes de ser aceito no processo. Distinto do Pacote 6: aquele é sobre *execução* multi-harness (bloqueado por falta de outros harnesses instalados); este é sobre *distribuição de arquivos* (100% verificável e corrigível nesta máquina, sem bloqueio estrutural). Ver `07-agnosticismo-distribuicao-componentes.md`.

---

## 3. Regra fixa: nenhum pacote começa sem Definição de Pronto escrita antes

Para gaps como "auditar se algum gate pode ser enganado" ou "toda mensagem de erro do produto está certa", não existe um ponto natural de parada — sempre dá para checar mais uma coisa. Sem travar o escopo antes de começar, o ciclo nunca fecha de verdade ou fecha por cansaço, não por critério.

Por isso, **antes de iniciar a implementação de qualquer pacote**, este processo exige que eu escreva e você aprove uma Definição de Pronto concreta e checável — não "deixar mais transparente", e sim algo do tipo "as N mensagens de erro que citam flags de CLI nestas M ferramentas foram verificadas contra o `argparse` real; o gate X foi criado e roda como parte de `ecossistema.py audit`". A Definição de Pronto de cada pacote fica registrada no documento daquele pacote (ver §4) antes do primeiro commit daquele ciclo.

---

## 4. Onde vive o conteúdo técnico de cada pacote

Cada pacote, quando sua vez chegar, ganha o próprio documento nesta mesma pasta:

- `01-transparencia-e-gates.md`
- `02-testabilidade-e-determinismo.md`
- `03-modularizacao-injector.md`
- `04-cobertura-comandos-restantes.md`
- `05-economia-tokens-e-agentico.md`
- `06-universalidade.md` (registro do limite, sem plano de implementação)
- `07-agnosticismo-distribuicao-componentes.md` (adicionado fora dos 8 gaps originais, ver §2)

Cada um segue a mesma estrutura interna: Definição de Pronto → Diagnóstico específico (herdado ou aprofundado a partir do `PLANO-EVOLUCAO-NOTAS-AUDITORIA.md`) → Implementação → Evidência de teste real → Veredito final (nota antes/depois, com justificativa).

---

## 5. Os dois tetos reconhecidos — não tentamos fingir que somem

Dois pacotes têm um limite estrutural que nenhuma quantidade de trabalho remove. Isso está decidido e registrado agora para que nenhum ciclo futuro prometa 10/10 onde isso seria mentira:

- **Pacote 5 (Economia de Tokens / Engenharia Agêntica):** o número de tokens no modo delegado é autodeclarado por quem responde (inclusive por mim, quando respondi manualmente nesta sessão) — não há como verificar de forma independente. "Pronto" aqui significa que essa limitação fica **rotulada e documentada honestamente**, nunca que ela deixa de existir.
- **Pacote 6 (Universalidade):** só há um harness real disponível para teste nesta máquina (Claude Code). Sem Codex, Gemini CLI ou outro ADE instalado, qualquer "correção" seria documentação prometendo algo não comprovado. Este pacote fica registrado como **limite fixo**, sem ciclo de implementação — não avança até que essa condição externa mude.

---

## 6. Ordem de execução acordada

1. Transparência + Gates Mecânicos
2. Testabilidade + Determinismo
3. Modularização — **bloqueado até a decisão A/B/C sobre o injector** (ver `PLANO-EVOLUCAO-NOTAS-AUDITORIA.md` §4)
4. Cobertura dos comandos restantes
5. Economia de Tokens + Engenharia Agêntica
6. Universalidade (registro apenas, sem execução)
7. Agnosticismo de Distribuição de Componentes — implementado antes dos Pacotes 3-6, mesmo entrando depois deles nesta lista.

**Por que o Pacote 7 furou a fila — sem inflar uma justificativa técnica que não existe:**
- **Não há dependência técnica que force essa ordem.** É sequenciamento por oportunidade, não por necessidade estrutural.
- **Pacote 3 continua genuinamente bloqueado** (decisão A/B/C sobre o injector `aidd-master`/`aidd-enterprise` ainda não veio) — não avançaria de qualquer forma, então não está sendo "passado para trás".
- **Pacotes 4 e 5 ainda não têm diagnóstico nem Definição de Pronto escritos** — o Pacote 7 só chegou à frente porque suas 4 decisões de arquitetura foram resolvidas rapidamente, numa única conversa, com o usuário. Ele "amadureceu" primeiro, não tem prioridade técnica sobre os outros.
- **Pacote 6 nunca teve ciclo de execução** (só registro de teto estrutural), não entra nesta comparação.
- **Vantagem real de sequenciamento (não obrigatória, mas vale registrar):** o Pacote 7 mexe em `gates/G_HARNESS_COMPAT.py` e acrescenta gate novo à bateria de `ecossistema.py audit`. Fazer isso antes dos Pacotes 4 e 5 (que também tocam infraestrutura de gates) significa que esses dois já encontram essa parte corrigida, em vez de construir sobre um gate com ponto cego conhecido.
- **Nota de escopo:** os injetores unificados no Pacote 7 (Fase 4 — `aidd-forge`'s `injector_profiles.py`, `aidd-generator`'s `scripts/core/injector/`, que materializam componentes em projetos) são um subsistema diferente do injector do Pacote 3 (`aidd-master`/`aidd-enterprise`'s comando `inject`, que injeta componentes dentro de um projeto já composto). Zero sobreposição de código entre os dois — só risco de confusão de nome a evitar.

---

## 7. Registro de progresso

| Pacote | Status | Nota antes → depois | Documento |
|---|---|---|---|
| 1. Transparência + Gates | ✅ Concluído | Gates Mecânicos 7/10 → **8/10 (alvo atingido)**. Transparência 8/10 → **8.5/10** (alvo 9/10 só fecha quando Pacotes 4 e 5 também resolverem suas partes desta dimensão — ver §3 do documento do pacote) | `01-transparencia-e-gates.md` |
| 2. Testabilidade + Determinismo | ✅ Concluído (implementado por agente externo, auditado e confirmado por mim) | Testabilidade 6→**9/10**; Determinismo 9→**9.5/10** (ambos alvo atingido) | `02-testabilidade-e-determinismo.md` |
| 3. Modularização | ✅ Concluído | Modularização 7→**9/10** (alvo atingido) | `03-modularizacao-injector.md` |
| 4. Cobertura restante | ✅ Concluído | Testabilidade/Cobertura Real permanece **9/10** (alvo já perseguido pelo Pacote 2, agora com evidência completa dos 7 comandos restantes, não parcial) | `04-cobertura-comandos-restantes.md` |
| 5. Tokens + Agêntico | ⏳ Não iniciado | 7/10, 8/10 → alvo 8/10, 8.5/10 | *(a criar)* |
| 6. Universalidade | 📌 Registrado como limite fixo | 8/10 → 8/10 (sem mudança possível) | este arquivo, §5 |
| 7. Agnosticismo de Distribuição | ✅ Concluído | Gap novo, fora da tabela original de 8 dimensões — nota final **9/10** (limitação residual documentada: `aidd-master`/`aidd-enterprise` seguem com injetores antigos fora do mecanismo unificado) | `07-agnosticismo-distribuicao-componentes.md` |

Esta tabela é atualizada ao final de cada pacote — nunca antes da validação real daquele pacote.

---

## 8. O que nunca muda neste processo, mesmo sob pressão de terminar rápido

- Nenhuma nota sobe no relatório sem o comando de validação correspondente ter sido rodado de verdade nesta sessão.
- Nenhum pacote é declarado concluído por "parecer suficiente" — só pela Definição de Pronto escrita antes de começar.
- Onde o teto é estrutural (§5), a honestidade sobre o teto é o próprio critério de sucesso, não um obstáculo a esconder.
