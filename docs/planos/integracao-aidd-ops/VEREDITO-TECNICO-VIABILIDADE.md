# Veredito Técnico de Viabilidade — Feature AIDD-Ops

> **Data:** 06/09/2026. **Metodologia:** cada pergunta abaixo foi respondida com evidência real coletada no código do repositório (grep, leitura de linha exata, teste de comportamento de gate) — nunca por impressão ou leitura da proposta em si. Onde a resposta é "não" ou "parcial", isso fica registrado honestamente, sem inflar a nota.

---

## 1. A feature agrega valor real ao ecossistema?

**Sim.** O gap de mercado é real (alternativa self-hosted/white-label ao GoHighLevel, sem contadores de contato) e a arquitetura técnica da Seção 5 da proposta (Cenário A de banco centralizado com bancos lógicos isolados; Gateway próprio vs. n8n; imagens oficiais vs. Dockerfile) está tecnicamente correta e bem justificada — confirmei que essas decisões batem com boas práticas reais de engenharia (isolamento de credenciais por serviço, healthcheck antes de dependência, preferência por imagens oficiais). Além disso, a proposta usa exatamente o vocabulário e os diretórios reais deste repositório (`tools/`, `gates/`, `componentes/`) — não é um documento genérico colado por cima.

## 2. É viável, ou não?

**Sim, viável — com uma condição:** tratar como mudança de categoria de produto (de "governança de geração de código local" para "operador de infraestrutura remota"), não como "mais uma ferramenta igual às outras 4". Toda a tecnologia envolvida (SSH via biblioteca determinística tipo Paramiko, API REST da Cloudflare, `docker compose`, scripts `psql`) é madura e sem dependência de tecnologia exótica ou não comprovada. O risco real não é técnico-de-viabilidade, é de **blast radius**: as 4 ferramentas atuais só leem/escrevem no workspace local; AIDD-Ops, por desenho, ganha SSH em servidor real, DNS público e credenciais mestre de bancos com dados reais de clientes — categoria de risco nova, maior que qualquer coisa hoje governada pelo ecossistema. É exatamente por isso que o processo de integração (`00-PROCESSO-E-DECISOES.md`) exige aprovação pontual, não geral, para os pacotes 4/5/7/9.

## 3. O fluxo de 10 fases, como um todo, realmente gera o que se propõe?

**Sim, tecnicamente sólido — nenhuma fase depende de algo inexistente ou não comprovado.** Mapeei as 10 fases contra tecnologia real:

| Fase | Mecanismo real | Maduro/comprovado? |
|---|---|---|
| 1. Intake | Coleta estruturada + parsing de texto livre | Sim (mesmo padrão de `detector_camada.py`/análise de fase 2 do aidd-generator) |
| 2. Curadoria | Lookup em catálogo curado + matriz de nicho (já definida na própria proposta §6) | Sim — **e pode ser 100% determinístico, ver §6 abaixo** |
| 3. Sizing | Soma aritmética de requisitos de recursos por ferramenta selecionada | Sim, trivial |
| 4. Bootstrapping VPS | SSH determinístico (apt, docker install, ufw, fail2ban) | Sim, script padrão de qualquer plataforma de IaC |
| 5. DNS | API REST da Cloudflare (criação de registro A/CNAME) | Sim, API pública estável e documentada |
| 6. Artefatos/Segredos | Geração criptográfica (`openssl rand`) + templating de `.env`/`init.sh` | Sim, mesmo padrão do `materializador.py` já usado em 3 das 4 ferramentas |
| 7. Frontend/Gateway | Build a partir de templates (Next.js) + serviço HTTP simples (FastAPI/Fastify) | Sim, tecnologia madura |
| 8. Deploy Docker | `docker compose config` + `up` com healthcheck | Sim, padrão da indústria |
| 9. Pre-Flight | `curl` real a `/healthz`, validação de DNS/SSL, webhook simulado | Sim, mesmo padrão que gates existentes já fazem (ex.: `test_full_forge_pipeline.py` já roda hook real via subprocess) |
| 10. Backup/Entrega | `pg_dumpall` + upload S3 (R2) + relatório | Sim, ferramentas padrão do Postgres |

Nenhuma fase depende de "mágica de IA" para funcionar — isso é uma boa notícia de viabilidade, não uma limitação (ver §6).

## 4. Cada fase pode ser executada INDIVIDUALMENTE ou só EM CONJUNTO?

**As duas coisas, com papéis diferentes — mesmo padrão já usado no `aidd-generator` (o análogo real mais próximo já homologado neste repositório).** Confirmei em `tools/aidd-generator/tests/test_phase_02.py`, `test_phase_03.py`, `test_phase_08.py`: cada fase é testável **individualmente** dado um estado de entrada fixo/mockado (isso já é feito hoje, e deve ser replicado para AIDD-Ops). Mas **em produção real**, as fases formam um pipeline **sequencial e com estado** — a Fase 3 explicitamente depende da seleção de ferramentas da Fase 2 (a própria proposta diz isso: "a partir da seleção de ferramentas da Fase 2"), a Fase 8 depende dos artefatos da Fase 6, etc. Não existe um cenário real em que a Fase 5 (DNS) rode com sentido sem a Fase 4 (VPS) já ter dado um IP real. **Recomendação para o Pacote 3:** mesma arquitetura do `aidd-generator` — cada fase é um script próprio (`scripts/phases/0N_nome.py`), estado persistido em cache entre fases (equivalente a `.aidd/cache/`), orquestrado por um script principal (`pipeline_ops.py`), com testes unitários por fase usando fixtures/mocks do estado anterior.

## 5. TODAS as ferramentas são PURAMENTE agnósticas?

**Não — e isso já era conhecido e documentado honestamente antes desta pergunta, não uma novidade desta análise.** Evidência real, coletada nesta mesma sessão (Rodada 2, Item 5, `docs/planos/refinamento-notas-auditoria/05-investigacao-mecanismo-agy.md`):
- `agy` (Antigravity): mecanismo de descoberta real não plenamente confirmado — a documentação oficial do `agy` alega suporte retroativo a `.agent/skills` (singular, formato que o ecossistema gera), mas o teste comportamental real (2 chamadas de LLM) encontrou 0/5 skills descobertas, contradição ainda não resolvida.
- `freebuff`: instalado, mas sem modo não-interativo testável via automação — nunca confirmado.
- Além disso (achado desta sessão, ao investigar o Pacote 2 da AIDD-Ops): `aidd-forge` **não usa o mesmo mecanismo de distribuição de componentes** (`componentes/` + `gestor_componentes.py sync`) que `aidd-master`, `aidd-enterprise` e `aidd-generator` usam — tem seu próprio materializador autocontido (`aidd_forge/materializador.py`). Isso não quebra o agnosticismo de **saída** (o projeto que o `aidd-forge` gera ainda funciona em múltiplos harnesses), mas é uma inconsistência real de **arquitetura interna** entre as 4 ferramentas — cada uma resolve "multi-harness" à sua própria maneira, não por um único mecanismo compartilhado.

**Conclusão honesta:** o ecossistema é agnóstico "na prática, na maioria dos harnesses testados, com gaps documentados" — não "puramente" agnóstico em 100% dos casos. Isso é uma característica válida e defensável (a alternativa seria fingir uma cobertura que não existe), mas não corresponde a "sim, todas, sempre".

## 6. TODAS as ferramentas seguem ECONOMIA SEVERA DE TOKENS / tornam determinístico o que PODE ser determinístico?

**Sim, com forte evidência real — e este é o ponto mais favorável de todo o veredito.**

| Ferramenta | LLM usado onde? | Verificado |
|---|---|---|
| `aidd-forge` | **Nenhum lugar.** 100% templating + AST/regex. | Confirmado por investigação de código nesta sessão (Explore agent, zero hits de API key/LiteLLM/protocolo delegado) |
| `aidd-master` / `aidd-enterprise` | Detecção de intenção em linguagem natural (`plan`/`prompt`) é casamento de palavras-chave, **"SEM uso de LLM/IA generativa"** — texto literal do próprio `--help` do CLI, confirmado várias vezes nesta sessão. | Confirmado |
| `aidd-generator` | Só as fases 2, 3 e 8 (análise, design paralelo, geração de código) usam LLM (via Protocolo Delegado, sem custo de API, ou headless com custo real e opt-in). As fases 1, 4, 5, 6, 7 são determinísticas (pesquisa via API pública, heurística/decisão estruturada, templating, auto-crítica por regras fixas). | Confirmado por investigação de código nesta sessão (Explore agent) |

**Isso estabelece um precedente real e forte para o Pacote 3 do AIDD-Ops seguir.** E a análise da Fase 2 (Curadoria) da proposta original revela uma oportunidade que a proposta não explora: como a própria Seção 6 da proposta já define uma **matriz fixa de nicho→stack** (5 combinações pré-definidas: Clínicas, Delivery, Farmácias, B2B, Energia Solar), a Fase 2 do MVP **pode e deve ser um lookup 100% determinístico** contra essa matriz (sem LLM nenhum) para os 5 nichos já catalogados — reservando qualquer curadoria assistida por LLM só para nichos futuros, fora da matriz fixa. **Recomendação concreta para o Pacote 3:** implementar a Fase 2 do MVP como lookup determinístico, não como chamada de LLM — isso reduz o escopo probabilístico do MVP a **zero**, já que as Fases 1 e 3 (as únicas do MVP) também são, respectivamente, coleta estruturada (determinística, ou com um parsing leve de texto livre) e aritmética pura (100% determinística).

## 7. A nova feature segue os princípios de Engenharia Agêntica Aplicada e as demais regras do ecossistema já homologado?

**Sim, no desenho — a proposta original já usa o vocabulário certo** (subagentes especializados, MCP para ferramentas externas, gates determinísticos binários — "Guardião Determinístico"). Isso bate com os padrões já estabelecidos: Result monad (`result.py`, usado por `aidd-master`/`aidd-enterprise`), contratos JSON Schema Draft 2020-12 (`schema_injector_request.json`, contratos do `aidd-generator`), gates binários (`exit 0`/`exit 1`, todos os 6 gates de raiz + os de cada ferramenta). **A adesão real só se confirma na implementação** — é por isso que o Pacote 3 (a seguir) precisa nascer usando exatamente esses padrões (Result monad para retorno de cada fase, JSON Schema para o contrato de estado entre fases, gate determinístico próprio), não reinventar um padrão novo. Vou desenhar o Pacote 3 já amarrado a esses padrões, não como sugestão solta.

## 8. SKILLS, MCPs, CONFIGS, HOOKS, MEMORY, AGENTS.md, SCRIPTS, SPECS, SUBAGENTS, COMANDOS da nova feature serão criados em `componentes/` e propagados conforme já homologado?

**Sim — mas só depois de uma correção real que fiz agora, ao escrever o Pacote 2.** Meu primeiro rascunho do Pacote 2 mandava criar `skills/aidd-ops-runner/SKILL.md` e os slash commands **direto no destino** (`.claude/commands/ops.md`, `.agent/commands/ops.md`) — isso estava **errado** e violaria o processo já homologado. Verifiquei em `gates/manifesto_harnesses.json` que esses são **destinos gerados por sync**, nunca editados manualmente; a fonte canônica real é `componentes/compartilhado/skills/` e `componentes/compartilhado/comandos/`. Já corrigi o Pacote 2 (`02-fundamentos-governanca-gates.md`) para criar a fonte canônica em `componentes/compartilhado/` e propagar via `python ecossistema.py components sync --tipo skill|command --ferramenta compartilhado`, nunca escrever os destinos à mão. Também vou registrar `aidd-ops` como escopo válido em `gates/manifesto_harnesses.json["escopos"]` (mesmo formato que `aidd-forge` já tem hoje), preparando o terreno para quando a ferramenta ganhar componentes próprios injetáveis (mcps, hooks, specs, sub-agentes) num pacote futuro — o Pacote 3 (MVP, Fases 1-3) provavelmente **não precisa** de nenhum componente injetável próprio ainda, já que seu papel é provisionar infraestrutura, não injetar artefatos em um projeto-alvo como `aidd-master`/`aidd-enterprise` fazem. Isso será reavaliado pacote a pacote, à medida que cada um definir sua Definição de Pronto.

---

## Veredito consolidado

| Pergunta | Resposta |
|---|---|
| Agrega valor real? | ✅ Sim |
| Viável? | ✅ Sim, com blast radius novo (infra real) exigindo aprovação pontual por pacote |
| O fluxo de 10 fases gera o que propõe? | ✅ Sim, tecnologia madura em todas as 10 fases |
| Fases individuais ou em conjunto? | Ambos — testáveis individualmente, mas um pipeline sequencial com estado em produção (mesmo padrão do `aidd-generator`) |
| Todas as ferramentas são puramente agnósticas? | ⚠️ Não — gaps reais e já documentados (`agy`, `freebuff`, `aidd-forge` fora do mecanismo compartilhado de componentes) |
| Todas seguem economia severa de tokens / determinismo máximo? | ✅ Sim, com forte evidência real — e o MVP do AIDD-Ops pode (e deve) ser 100% determinístico |
| Segue Engenharia Agêntica Aplicada e regras do ecossistema? | ✅ Sim no desenho da proposta; a implementação real (Pacote 3) precisa confirmar na prática |
| Componentes vão para `componentes/` e propagam conforme homologado? | ✅ Sim — só depois de uma correção real que apliquei no Pacote 2 antes de você perguntar |

**Recomendação final:** seguir para o Pacote 3, desenhando o MVP (Fases 1-3) como **100% determinístico** (zero chamada de LLM), usando Result monad + JSON Schema + gate próprio, e roteado através de `componentes/` desde o primeiro componente real que a ferramenta precisar.
