# PROCESSO E DECISOES — codigo-limpo-profundo-ecossistema

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

Defina aqui os objetivos claros, escopo e limites desta iniciativa.
- **Objetivo Principal:** [Descrever objetivo]
- **Limites de Escopo:** Nao inclui decisoes nao aprovadas por humano.

### Metrica da Iniciativa (0-10)

- **Nota Atual:** 1.5 — evidencia: 12-09-2026_melhoria-reanalise-plan-0021.html
- **Nota Alvo:** 10.0
- **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

## 2. Processo Adotado e Estrategia de Execucao

A execucao e fatiada em **3 Ondas Sequenciais por Risco**:
- **Onda 1 — Ganhos Rapidos e Limpeza Mecanica (Baixo Risco):** Itens 08, 09, 10, 12, 13.
- **Onda 2 — Refatoracao de Modulos Isolados (Medio Risco):** Itens 11, 14, 15, 17, 18.
- **Onda 3 — Arquitetura, Injetores e Nucleo Compartilhado (Alto Risco):** Itens 02, 03, 04, 05, 06, 07, 16.

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Onda | Documento |
|---|---|---|---|
| 8 | Refatorar compose_suite.py (multiplas responsabilidades e HTML em f-string) e remover constante morta WEBHOOK_DEMO_URL | Onda 1 | `08-refatorar-compose-suitepy.md` |
| 9 | Corrigir terminacao de linha inconsistente CRLF-LF entre gemeas master-enterprise | Onda 1 | `09-corrigir-terminacao-linha.md` |
| 10 | Simplificar parser defensivo extrair_json_manual e corrigir comentario de numeracao mentiroso | Onda 1 | `10-simplificar-parser-defensivo.md` |
| 12 | Remover imports mortos nos gates locais de master-enterprise | Onda 1 | `12-remover-imports-mortos.md` |
| 13 | Estreitar except Exception e except pass remanescentes em gates da raiz e src-core | Onda 1 | `13-estreitar-except-exception.md` |
| 11 | Refatorar Fase 08 do generator (monolito, classificador por substring, excecoes copy-paste, estado global com sentinela dupla) | Onda 2 | `11-refatorar-fase-08.md` |
| 14 | Corrigir contradicao headless-interativa em cmd_orchestrate e decompor a funcao | Onda 2 | `14-corrigir-contradicao-headless.md` |
| 15 | Corrigir violacao de Lei de Demeter em database.py e unificar reescrita SQL (AST vs regex) | Onda 2 | `15-corrigir-violacao-lei.md` |
| 17 | Polimento estrutural: materializador do generator, idioma try-except-import duplicado, sys.path fragil no ops, funcoes sem decomposicao no ops | Onda 2 | `17-polimento-estrutural-materializador.md` |
| 18 | Polimento de testes e UX: time.sleep em testes e banners-prints misturando UI e log | Onda 2 | `18-polimento-testes-ux.md` |
| 2 | Extrair e proteger templates duplicados (core vs v2 e entre ferramentas) | Onda 3 | `02-extrair-proteger-templates.md` |
| 3 | Extrair e proteger scripts-gates e templates-gates duplicados entre master e enterprise | Onda 3 | `03-extrair-proteger-scripts.md` |
| 4 | Refatorar CLI monolitica aidd.py de master-enterprise (funcoes com multiplas responsabilidades e roteamento duplo) | Onda 3 | `04-refatorar-cli-monolitica.md` |
| 5 | Unificar reconhecimento de dominio (KNOWN_DOMAINS vs IntentRouter) | Onda 3 | `05-unificar-reconhecimento-dominio.md` |
| 6 | Unificar as 4 implementacoes paralelas do dominio Injector (forge-generator-master-enterprise) | Onda 3 | `06-unificar-4-implementacoes.md` |
| 7 | Consolidar Result monad (4 APIs incompativeis) em torno de returns | Onda 3 | `07-consolidar-result-monad.md` |
| 16 | Decompor God class SecurityGate (G_SEGURANCA) e renomear metodos camada-N | Onda 3 | `16-decompor-god-class.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Onda | Documento |
|---|---|---|---|---|
| 8 | Refatorar compose_suite.py e remover WEBHOOK_DEMO_URL | 🔶 Em execucao | Onda 1 | `08-refatorar-compose-suitepy.md` |
| 9 | Corrigir terminacao CRLF-LF | 🔶 Em execucao | Onda 1 | `09-corrigir-terminacao-linha.md` |
| 10 | Simplificar parser extrair_json_manual | 🔶 Em execucao | Onda 1 | `10-simplificar-parser-defensivo.md` |
| 12 | Remover imports mortos nos gates locais | 🔶 Em execucao | Onda 1 | `12-remover-imports-mortos.md` |
| 13 | Estreitar except Exception remanescentes | 🔶 Em execucao | Onda 1 | `13-estreitar-except-exception.md` |
| 11 | Refatorar Fase 08 do generator | 🔶 Em execucao | Onda 2 | `11-refatorar-fase-08.md` |
| 14 | Corrigir contradicao headless-interativa em cmd_orchestrate | 🔶 Em execucao | Onda 2 | `14-corrigir-contradicao-headless.md` |
| 15 | Corrigir violacao de Lei de Demeter em database.py | 🔶 Em execucao | Onda 2 | `15-corrigir-violacao-lei.md` |
| 17 | Polimento estrutural generator e ops | 🔶 Em execucao | Onda 2 | `17-polimento-estrutural-materializador.md` |
| 18 | Polimento de testes e UX (time.sleep e prints) | 🔶 Em execucao | Onda 2 | `18-polimento-testes-ux.md` |
| 2 | Extrair e proteger templates duplicados | 🔶 Em execucao | Onda 3 | `02-extrair-proteger-templates.md` |
| 3 | Extrair e proteger scripts-gates e templates-gates | 🔶 Em execucao | Onda 3 | `03-extrair-proteger-scripts.md` |
| 4 | Refatorar CLI monolitica aidd.py | 🔶 Em execucao | Onda 3 | `04-refatorar-cli-monolitica.md` |
| 5 | Unificar KNOWN_DOMAINS vs IntentRouter | 🔶 Em execucao | Onda 3 | `05-unificar-reconhecimento-dominio.md` |
| 6 | Unificar 4 implementacoes de Injector | 🔶 Em execucao | Onda 3 | `06-unificar-4-implementacoes.md` |
| 7 | Consolidar Result monad | 🔶 Em execucao | Onda 3 | `07-consolidar-result-monad.md` |
| 16 | Decompor God class SecurityGate | 🔶 Em execucao | Onda 3 | `16-decompor-god-class.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
