# PLANO DE EVOLUÇÃO — Das notas da auditoria (7.5/10) a uma suíte comprovadamente confiável

> **Origem:** `docs/relatorios/relatorio-auditoria-ecossistema-aidd.html` (auditoria de 04/09/2026, nota consolidada 7.5/10)
> **Status:** DIAGNOSTICADO EM PROFUNDIDADE — AGUARDANDO SUA REVISÃO ANTES DE QUALQUER IMPLEMENTAÇÃO
> **Método desta segunda passada:** não reformulei o texto da auditoria — investiguei mais fundo cada uma das 8 dimensões, com evidência nova e mais precisa que a da primeira rodada. Onde a análise original já era suficiente, mantive; onde não era, está marcado explicitamente.

---

## 0. O que mudou desde a primeira auditoria

A primeira rodada encontrou os sintomas. Esta segunda foi atrás da causa raiz de cada um, e achou 3 problemas **mais profundos e mais graves** do que os relatados originalmente:

1. **A divergência entre `aidd-master` e `aidd-enterprise` não é de nomenclatura de CLI — é de subsistema inteiro.** `aidd-enterprise` não tem mais `detector_camada.py`; ele foi inteiramente substituído por `scripts/injector/aidd_core_injector.py` (262 linhas, suporte a MCP/hooks/dry-run), nunca retroportado para `aidd-master` (151 linhas, sem suporte a MCP). Isso também revela um **ponto cego no meu próprio gate de drift** (`G_DRIFT_NUCLEO_COMPARTILHADO.py`): ele só compara arquivos que existem **nos dois lados** — um arquivo removido de um lado é invisível para ele.
2. **47% dos comandos do CLI (`aidd-master`) não têm nenhuma cobertura de teste no nível de comando** — não é só `compose_suite.py`. `add_module.py` (a funcionalidade mais anunciada do produto: "Suíte Modular com **Fatias Verticais**") está no mesmo ponto cego: existe um teste (`test_modulo1.py`) que testa um módulo **já gerado e commitado**, mas nenhum teste chama `add_module.py` de verdade para gerar um módulo novo. É o padrão exato do bug do `compose_suite.py`, só que ainda não expliodiu.
3. **`cmd_plan`/`cmd_prompt`, anunciados como "geração a partir de linguagem natural", são casamento de palavras-chave contra uma lista fixa de ~24 termos em português** (`scripts/aidd.py:759-764`) — zero chamada de LLM. Isso é uma vitória para determinismo, mas é uma lacuna de transparência: nada no `--help` avisa que não há IA ali.

Essas três descobertas mudam onde o esforço de melhoria deveria realmente ir — por isso o plano abaixo não é "corrigir o que já foi achado", é uma investigação nova que aponta para trabalho novo.

---

## 1. Tabela de evolução alvo

| Dimensão | Nota atual | O que a segura | Nota alvo pós-plano |
|---|---|---|---|
| Testabilidade / Cobertura Real | 6/10 | 8 de 17 comandos do CLI sem teste algum; `add_module.py` no ponto cego do `compose_suite.py` | 9/10 |
| Modularização | 7/10 | Subsistema de injeção inteiro divergiu sem detecção; gate de drift tem ponto cego estrutural | 9/10 |
| Gates Mecânicos | 7/10 | Nenhum gate audita "todo comando documentado tem teste" | 8/10 |
| Transparência / Zero Alucinação | 8/10 | Bug `--command`; `tokens_consumidos` autodeclarado sem marcação; `plan`/`prompt` não avisam que não usam IA | 9/10 |
| Economia de Tokens | 7/10 | Mesma raiz do item acima — número "medido" e "estimado" indistinguíveis no schema | 8/10 |
| Engenharia Agêntica Aplicada | 8/10 | Mesma raiz — mas o protocolo delegado em si funciona bem | 8.5/10 |
| Determinismo Primeiro | 9/10 | `add_module.py` precisa da mesma bateria de testes que já fechou `compose_suite.py` | 9.5/10 |
| Universalidade / Agnosticismo | 8/10 | Só testado com 1 harness na prática; não dá para resolver sem outro harness instalado | 8/10 (sem mudança possível agora — documentado como limite real) |

**Composto alvo: ~8.6/10** — não é 10 de propósito. Universalidade fica honestamente em 8 porque testar de verdade com Codex/Gemini CLI exige ter essas ferramentas instaladas, o que está fora do meu alcance nesta máquina agora. Qualquer plano que prometesse 10/10 estaria mentindo do mesmo jeito que os bugs que encontramos mentiam.

---

## 2. FASE 1 — Fechar a mentira mais barata primeiro (Transparência)

**Por quê primeiro:** é o menor esforço, maior clareza, e fecha exatamente o tipo de bug que a auditoria mostrou (mensagem de erro que não bate com a realidade).

2.1. Corrigir `aidd-enterprise/scripts/aidd.py:847` — trocar `--command` por `--mcp-command` na mensagem de erro. Replicar a checagem em `aidd-master` também (mesma classe de bug pode existir lá sem eu ter achado ainda).

2.2. **Formalizar a checagem que eu fiz manualmente como um gate novo**, `G_CLI_HELP_CONSISTENCIA.py`: para cada subcomando do `argparse`, extrai as flags citadas dentro de mensagens de erro (`print`, `raise`) e confere contra as flags realmente definidas via `add_argument`. Isso transforma um achado manual único em proteção permanente contra recorrência — exatamente o padrão que já uso nos outros gates desta sessão.

2.3. Validar rodando os 2 gates novos contra os 4 tools + confirmar que nenhum outro par flag/mensagem diverge.

---

## 3. FASE 2 — `add_module.py`: repetir a receita que já funcionou em `compose_suite.py`

**Por quê:** é literalmente a mesma classe de risco que já paguei o preço de descobrir do jeito difícil. Ignorar agora que eu já sei onde procurar seria negligência, não economia de esforço.

3.1. Confirmar que `add_module.py` compila sem erro de sintaxe (`ast.parse`) — o mínimo que faltou em `compose_suite.py`.

3.2. Escrever teste real: chamar `add_module.py` para gerar um módulo novo dentro de um projeto já composto (`compose` + `add_module`), e confirmar:
   - Rotas do módulo novo aparecem em `src/server.py` automaticamente
   - O servidor sobe com o módulo novo registrado (teste de fogo via subprocess, mesmo padrão do `test_compose_suite.py`)
   - O manifesto `PLANO-EXECUCAO-ESTRUTURADO.json` é atualizado corretamente

3.3. Duplicar em `aidd-enterprise` (mesmo arquivo, mesmo padrão de risco compartilhado).

**Critério de aceite:** se existir qualquer bug estrutural em `add_module.py` do mesmo tipo do `SyntaxError`/`logs.py ausente` que achei em `compose_suite.py`, este teste precisa pegar.

---

## 4. FASE 3 — A divergência do injector: decisão explícita, não silêncio

Esta é a única fase que **exige uma decisão sua antes de eu tocar em código** — não é uma correção mecânica, é uma escolha de arquitetura.

**O problema:** `aidd-master` só sabe injetar `skill/mcp/rule/spec/config/agent` sem suporte real a servidor MCP (sem `--mcp-command`); `aidd-enterprise` tem tudo isso mais `hook`. Um usuário que aprende a usar `enterprise inject mcp` e depois tenta o mesmo em `master` encontra um comando que aceita a sintaxe mas não faz o que ele espera.

**Três caminhos possíveis — preciso que você escolha um:**

| Opção | O que significa | Risco |
|---|---|---|
| **A. Portar o injector novo para `aidd-master`** | Copiar `aidd_core_injector.py` (262 linhas) para `aidd-master`, igualando as capacidades | Reintroduz duplicação de ~260 linhas — mas já temos o gate de drift pra vigiar isso daqui pra frente |
| **B. Documentar a diferença como intencional** | `aidd-master` continua mais simples de propósito (é a versão "básica"); atualizar `--help`, `README.md` e `AGENTS.md` das duas ferramentas para deixar isso explícito | Não resolve a lacuna de capacidade, só a lacuna de expectativa |
| **C. Depreciar o injector antigo em `aidd-master`** e apontar `--help` para "funcionalidade completa disponível em aidd-enterprise" | Reduz escopo do `aidd-master` deliberadamente | Pode não ser o que você quer para o produto |

4.1 (independente da opção escolhida). **Corrigir o ponto cego do gate de drift**: `G_DRIFT_NUCLEO_COMPARTILHADO.py` hoje só compara arquivos com o mesmo nome presentes nos dois lados. Adicionar uma checagem nova: se um arquivo do baseline (`baseline_nucleo_compartilhado.json`) que era `esperado_identico: true` **desaparecer** de um dos lados, o gate deve reprovar em vez de simplesmente não ter nada para comparar. Isso teria pego a substituição do `detector_camada.py` no momento em que aconteceu.

---

## 5. FASE 4 — Fechar a cobertura dos 7 comandos restantes sem teste

Ordem por risco real de uso (não por ordem alfabética):

| Comando | Por que importa | Teste mínimo proposto |
|---|---|---|
| `audit` | É o próprio mecanismo de garantia de qualidade do produto — se ele mesmo não é testado, quem garante que garante? | Rodar `aidd.py audit` num projeto composto de verdade, confirmar que retorna exit 0 quando tudo está ok e exit 1 quando eu quebro algo de propósito (mesmo padrão usado nos gates da raiz) |
| `plan` / `apply` | Fluxo de "descrever em linguagem natural" — maior superfície de confusão do usuário se falhar | Teste com prompts reais cobrindo: domínio conhecido (`"crie um crm"`), domínio desconhecido (fallback por palavras), e o caso vazio (fallback para `principal/configuracao`) — **e a doc do `--help` precisa deixar claro que não há LLM envolvido (Fase 1 de Transparência)** |
| `compose_orca` | Composição via subagentes efêmeros — mecanismo agêntico mais complexo do produto, nunca verificado nesta auditoria | No mínimo, confirmar que gera a mesma estrutura que `compose` para os módulos padrão, já que ambos compartilham `compose_suite` por baixo |
| `refine_module` | Suíte BDD (`behave`) até 100% dos cenários passarem — depende de `behave` instalado, mesma classe de "binário ausente" do `helm`/`terraform` | Teste com `skipif` se `behave` não estiver instalado (mesmo padrão já usado para helm/terraform), mais um teste estrutural que não depende do binário |
| `bench` | Benchmark de concorrência SQLite WAL — determinístico, sem desculpa para estar sem teste | Teste direto, roda rápido, sem dependência externa |
| `export-frontend` | Gera frontend Next.js/TypeScript a partir do OpenAPI | Teste estrutural (confirma que o TypeScript gerado é sintaticamente válido, mesmo padrão usado para YAML/Terraform antes) |
| `setup` | Diagnóstico + instalação automática de dependências | Teste do diagnóstico (não da instalação em si, que mexe no ambiente de verdade) |

---

## 6. FASE 5 — Tornar "medido" e "estimado" campos diferentes, não o mesmo campo

**O problema exato:** `utils_delegacao.py:369` mede tokens de verdade via `resposta.usage.total_tokens` no modo headless. Nos modos delegado (linhas 216, 255, 316), `tokens_consumidos` é só o que quem responde escreveu no JSON — o meu, quando respondi manualmente nesta sessão, incluído.

6.1. Adicionar um campo `origem_medicao` (`"medido_api"` ou `"autodeclarado"`) ao schema de resposta do protocolo delegado.

6.2. Atualizar `07_analisador.py` (auto-crítica) para exibir essa distinção explicitamente no relatório — em vez de só somar todos os números como se tivessem a mesma confiabilidade.

6.3. Atualizar `docs/PRINCIPIO-UNIVERSALIDADE.md` para documentar essa limitação honestamente (ela já é honesta sobre outras coisas — esta harmoniza com o próprio estilo do documento).

---

## 7. FASE 6 — Validação final: repetir a auditoria original com os mesmos testes

7.1. Reconstruir as duas aplicações da auditoria original (biblioteca de 4 módulos + estoque com regra de negócio) do zero, agora com as correções aplicadas.

7.2. Rodar a suíte completa das 4 ferramentas + o novo gate de CLI-help-consistência + o gate de drift corrigido.

7.3. Gerar um relatório de "antes/depois" com as mesmas 8 dimensões, mesma metodologia, sem inflar nota — se alguma dimensão não melhorar de verdade, isso fica escrito também.

---

## 8. O que este plano deliberadamente não tenta resolver

- **Universalidade multi-harness de verdade** — precisaria de Codex, Gemini CLI ou outro ADE instalado nesta máquina para testar de verdade. Sem isso, qualquer correção seria só mais documentação, não mais evidência. Não vou fingir que resolvi isso.
- **Portabilidade do protocolo delegado para fora do Claude Code** — o mecanismo é genérico no papel (qualquer harness que leia/escreva arquivo), mas nunca foi provado fora desta sessão.

---

## 9. O que preciso de você antes de começar

Só a **Fase 3, seção 4** (a escolha entre as opções A/B/C para a divergência do injector) bloqueia o início. Todo o resto (Fases 1, 2, 4, 5, 6) pode começar assim que você aprovar o plano como um todo — não precisa de mais nenhuma decisão de arquitetura, só execução.
