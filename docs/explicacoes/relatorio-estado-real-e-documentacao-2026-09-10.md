# Estado Real do Ecossistema AIDD e Saúde da Documentação

**Data da auditoria:** 2026-09-10
**Commit auditado:** `07fb306` (main)
**Método:** reprodução real — cada número aqui vem de rodar o teste ou o verificador de verdade, não de ler o que outro agente relatou.

> **Atualização (mesmo dia):** este relatório nasceu como diagnóstico puro. Depois disso, dois achados foram corrigidos de verdade, na mesma sessão: o verificador de arquitetura tinha falso-positivo (corrigido, ver Parte 1) e os 5 documentos desatualizados foram atualizados (ver Parte 2). O texto abaixo já reflete o estado final, com nota de "era assim, virou assim" em cada achado.

---

## Resumo executivo

O ecossistema passou hoje por uma reestruturação de arquitetura (10 itens, todos concluídos e mesclados) que atacou duplicação de código, CLIs inchadas e falta de padrão arquitetural entre `aidd-master` e `aidd-enterprise`. Resultado medido: **1.864 testes passando, zero falhas, nas 6 ferramentas**. O verificador `G_ARQUITETURA_DELIVERABLE` (criado nesta mesma reestruturação) reprovava com 524 problemas — auditando arquivo por arquivo, ~340 eram falso-positivo do próprio verificador (corrigido, ver abaixo); o número real e atual é **212**, concentrado nos modelos de projeto (templates), e fica registrado como próxima etapa.

O lado da **documentação** não tinha acompanhado a mesma velocidade: 4 dos 9 documentos centrais (o README raiz e os READMEs de master, enterprise e generator) descreviam uma arquitetura que já não existia mais, e 2 tinham números de teste desatualizados. Todos os 5 já foram corrigidos (Parte 2).

---

## Parte 1 — Estado real do ecossistema

### Verificadores gerais (rodam sobre o repositório inteiro)

| Verificador | O que audita | Resultado hoje |
|---|---|---|
| `G_ECOSSISTEMA_INTEGRIDADE` | Integridade física e sintática das 6 ferramentas e das skills | Aprovado |
| `G_DRIFT_NUCLEO_COMPARTILHADO` | Divergência escondida entre o núcleo de master e enterprise | Aprovado |
| `G_HARNESS_COMPAT` | Sincronização dos comandos/skills entre os diferentes assistentes de IA | Aprovado |
| `G_COMPONENTE_AGNOSTICO` | Todo componente novo funciona em qualquer assistente | Aprovado |
| `G_CLI_HELP_CONSISTENCIA` | O texto de ajuda da linha de comando bate com as opções reais | Aprovado |
| `G_HONESTIDADE_ROTULO` | Nenhum texto de gate exagera o que foi realmente comprovado | Aprovado (51 arquivos, 0 termos proibidos) |
| `G_ARQUITETURA_DELIVERABLE` | Camadas corretas (sem banco de dados direto fora do lugar certo) | Reprovado — 212 violações reais em código legado ainda não migrado (era 564 no início do dia → 524 → corrigido falso-positivo do próprio verificador → 212 hoje) |

### Cada ferramenta, por dentro

| Ferramenta | O que ela faz | Testes reais hoje | Situação |
|---|---|---|---|
| **aidd-forge** | Prepara qualquer projeto novo com a governança e os verificadores de qualidade do ecossistema | 196 passando, 1 pulado | Estável |
| **aidd-generator** | Transforma uma ideia em texto num projeto de software completo, em 8 etapas automáticas | 941 passando | Estável — ganhou correção automática de arquitetura na etapa final (novo hoje) |
| **aidd-master** | Framework modular onde se adicionam funções novas ("blocos de Lego") | 286 passando, 3 pulados | Estável — CLI e módulo de referência reescritos hoje |
| **aidd-enterprise** | Mesma base do master, com validação criptográfica e political de segurança mais rígida | 263 passando, 3 pulados | Estável — mesma reescrita do master, espelhada |
| **aidd-ops** | Pega o software pronto e prepara a infraestrutura (servidores, containers, deploy) | 159 passando | Estável — ganhou teste de integração real do Helm hoje |
| **aidd-bridge** | Tira aplicativos de plataformas sem código (Lovable, Bolt) e os coloca rodando em servidor próprio | 19 passando | Estável, não fez parte da reestruturação de hoje |

**Total: 1.864 testes passando, 0 falhas.**

### O que mudou hoje (10 itens da reestruturação DDD/Clean Architecture)

1. **Núcleo compartilhado unificado** — os 27 arquivos que master e enterprise mantinham duplicados manualmente agora têm uma única fonte real (`componentes/compartilhado/src-core/`), com sincronização automática. As 3 diferenças escondidas que existiam entre as duas cópias foram resolvidas.
2. **Orquestradores duplicados unificados** — tanto o `aidd-generator` quanto o `aidd-ops` tinham dois caminhos de código fazendo a mesma coisa; agora cada um tem um só.
3. **CLIs emagrecidas** — o arquivo de comando de master e enterprise caiu de ~1.160 para ~260 linhas cada; a lógica de negócio foi extraída para um lugar testável separado (`application/commands/`).
4. **Carregamento das fases do generator sem atalhos frágeis** — a forma como o gerador carregava suas 8 etapas internamente foi trocada por um pacote formal, mais robusto.
5. **Contrato formal entre ferramentas** — o arquivo que o `aidd-ops` produz e que `aidd-master`/`aidd-enterprise` consomem agora tem um formato validado (antes era só combinação informal).
6. **Módulo de referência reescrito** — o módulo usado como modelo para todo módulo novo (`modulo1`) foi reorganizado em camadas separadas (regras de negócio / casos de uso / banco de dados / rotas), no padrão conhecido como Clean Architecture.
7. **Checagem automática de arquitetura criada** — um verificador novo (`G_ARQUITETURA_DELIVERABLE`) audita se o código respeita essas camadas.
8. **Geradores de módulo atualizados** — quando alguém pede um módulo novo em master ou enterprise, ele já nasce no formato certo.
9. **Autocorreção na geração automática** — quando o `aidd-generator` cria um projeto do zero, ele agora audita a própria arquitetura gerada e tenta se corrigir sozinho se encontrar erro.
10. **Teste de infraestrutura real** — o `aidd-ops` ganhou um teste que sobe de verdade o pacote de instalação (Helm) e confere se os recursos calculados aparecem certos.

### Dois problemas encontrados no caminho (não causados pela reestruturação, mas descobertos durante ela)

- Um teste do `aidd-generator`, em certas condições, gera e grava sozinho um projeto de exemplo real no controle de versão — efeito colateral de teste que não deveria acontecer.
- O verificador `G_TESTES_REAIS` (que roda os testes das 5 ferramentas peixinho em sequência) tem instabilidade: sujeira de uma ferramenta atrapalha o resultado da próxima.

Os dois ficam registrados como pendência para uma próxima iniciativa — não foram corrigidos agora porque estão fora do escopo do que foi pedido.

---

## Parte 2 — Saúde da documentação

Cada arquivo abaixo foi comparado, ponto a ponto, com o que a reestruturação realmente mudou. Todos os achados abaixo já foram corrigidos.

| Arquivo | Situação | Achado (e correção aplicada) |
|---|---|---|
| `README.md` (raiz) | ✅ Corrigido | Chamava a si mesmo de "6 ferramentas" no topo e de "5 ferramentas" no mapa do repositório (esquecia o `aidd-bridge`); listava 8 verificadores gerais, quando hoje existem 12. Corrigido: mapa com as 6 ferramentas + `componentes/compartilhado/src-core/`; lista completa dos 12 verificadores |
| `tools/aidd-master/README.md` | ✅ Corrigido | Não mencionava `application/commands/` nem a estrutura em camadas do módulo de referência. Corrigido: estrutura do projeto e descrição atualizadas |
| `tools/aidd-enterprise/README.md` | ✅ Corrigido | Mesmos dois problemas do master (arquivos espelhados). Corrigido igual |
| `tools/aidd-generator/README.md` | ✅ Corrigido | Dizia "215 testes" (real: 941); não mencionava a autocorreção de arquitetura na Fase 8. Corrigido: número atualizado + pacote `scripts/phases/` e autocorreção documentados |
| `tools/aidd-forge/README.md` | ✅ Corrigido | Dizia "126 passed" (real: 196). Corrigido |
| `tools/aidd-ops/README.md` | 🟢 Já estava em dia | Já citava corretamente os itens da reestruturação que o afetaram |
| `tools/aidd-bridge/README.md` | 🟢 Não afetado | Não fez parte da reestruturação; nenhuma inconsistência gerada |
| `AGENTS.md` (raiz) | 🟢 Já estava em dia | Lista corretamente os 12 verificadores, incluindo o novo |
| Pasta do plano da reestruturação | ✅ Corrigido | Os 10 itens estavam marcados concluídos no próprio documento, mas a pasta vivia em `docs/planos/a-fazer/`. Movida para `docs/planos/feitos/`, índice regenerado |

---

## O que ficou registrado como próxima etapa (não corrigido agora, por decisão deliberada)

1. **212 violações reais de arquitetura**, concentradas nos modelos de projeto (`templates/`) de master e enterprise — rotas HTTP que mexem direto no banco de dados sem passar por camada nenhuma. Mesmo tipo de correção já feita no módulo de referência hoje, só que ainda não chegou nesses modelos.
2. Um teste do `aidd-generator` que, em certas condições, grava sozinho um projeto de exemplo real no controle de versão.
3. Instabilidade no verificador `G_TESTES_REAIS` quando roda as 5 ferramentas em sequência.

Nenhum dos três trava o dia a dia — ficam anotados para quando fizer sentido abrir uma frente de trabalho dedicada a eles.
