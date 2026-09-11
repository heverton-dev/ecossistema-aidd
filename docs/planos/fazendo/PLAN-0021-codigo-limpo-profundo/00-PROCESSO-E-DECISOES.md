# PROCESSO E DECISOES — codigo-limpo-profundo-ecossistema

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

Defina aqui os objetivos claros, escopo e limites desta iniciativa.
- **Objetivo Principal:** [Descrever objetivo]
- **Limites de Escopo:** Nao inclui decisoes nao aprovadas por humano.

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | Extrair nucleo compartilhado src-core entre master e enterprise (27 arquivos idênticos e divergência silenciosa) | `01-extrair-nucleo-compartilhado.md` |
| 2 | Extrair e proteger templates duplicados (core vs v2 e entre ferramentas) | `02-extrair-proteger-templates.md` |
| 3 | Extrair e proteger scripts-gates e templates-gates duplicados entre master e enterprise | `03-extrair-proteger-scripts.md` |
| 4 | Refatorar CLI monolitica aidd.py de master-enterprise (funcoes com multiplas responsabilidades e roteamento duplo) | `04-refatorar-cli-monolitica.md` |
| 5 | Unificar reconhecimento de dominio (KNOWN_DOMAINS vs IntentRouter) | `05-unificar-reconhecimento-dominio.md` |
| 6 | Unificar as 4 implementacoes paralelas do dominio Injector (forge-generator-master-enterprise) | `06-unificar-4-implementacoes.md` |
| 7 | Consolidar Result monad (4 APIs incompativeis) em torno de returns | `07-consolidar-result-monad.md` |
| 8 | Refatorar compose_suite.py (multiplas responsabilidades e HTML em f-string) e remover constante morta WEBHOOK_DEMO_URL | `08-refatorar-compose-suitepy.md` |
| 9 | Corrigir terminacao de linha inconsistente CRLF-LF entre gemeas master-enterprise | `09-corrigir-terminacao-linha.md` |
| 10 | Simplificar parser defensivo extrair_json_manual e corrigir comentario de numeracao mentiroso | `10-simplificar-parser-defensivo.md` |
| 11 | Refatorar Fase 08 do generator (monolito, classificador por substring, excecoes copy-paste, estado global com sentinela dupla) | `11-refatorar-fase-08.md` |
| 12 | Remover imports mortos nos gates locais de master-enterprise | `12-remover-imports-mortos.md` |
| 13 | Estreitar except Exception e except pass remanescentes em gates da raiz e src-core | `13-estreitar-except-exception.md` |
| 14 | Corrigir contradicao headless-interativa em cmd_orchestrate e decompor a funcao | `14-corrigir-contradicao-headless.md` |
| 15 | Corrigir violacao de Lei de Demeter em database.py e unificar reescrita SQL (AST vs regex) | `15-corrigir-violacao-lei.md` |
| 16 | Decompor God class SecurityGate (G_SEGURANCA) e renomear metodos camada-N | `16-decompor-god-class.md` |
| 17 | Polimento estrutural: materializador do generator, idioma try-except-import duplicado, sys.path fragil no ops, funcoes sem decomposicao no ops | `17-polimento-estrutural-materializador.md` |
| 18 | Polimento de testes e UX: time.sleep em testes e banners-prints misturando UI e log | `18-polimento-testes-ux.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Documento |
|---|---|---|---|
| 1 | Extrair nucleo compartilhado src-core entre master e enterprise (27 arquivos idênticos e divergência silenciosa) | ✅ Concluído | `01-extrair-nucleo-compartilhado.md` |
| 2 | Extrair e proteger templates duplicados (core vs v2 e entre ferramentas) | ⏳ Rascunho gerado, aguardando aprovacao | `02-extrair-proteger-templates.md` |
| 3 | Extrair e proteger scripts-gates e templates-gates duplicados entre master e enterprise | ⏳ Rascunho gerado, aguardando aprovacao | `03-extrair-proteger-scripts.md` |
| 4 | Refatorar CLI monolitica aidd.py de master-enterprise (funcoes com multiplas responsabilidades e roteamento duplo) | ⏳ Rascunho gerado, aguardando aprovacao | `04-refatorar-cli-monolitica.md` |
| 5 | Unificar reconhecimento de dominio (KNOWN_DOMAINS vs IntentRouter) | ⏳ Rascunho gerado, aguardando aprovacao | `05-unificar-reconhecimento-dominio.md` |
| 6 | Unificar as 4 implementacoes paralelas do dominio Injector (forge-generator-master-enterprise) | ⏳ Rascunho gerado, aguardando aprovacao | `06-unificar-4-implementacoes.md` |
| 7 | Consolidar Result monad (4 APIs incompativeis) em torno de returns | ⏳ Rascunho gerado, aguardando aprovacao | `07-consolidar-result-monad.md` |
| 8 | Refatorar compose_suite.py (multiplas responsabilidades e HTML em f-string) e remover constante morta WEBHOOK_DEMO_URL | ⏳ Rascunho gerado, aguardando aprovacao | `08-refatorar-compose-suitepy.md` |
| 9 | Corrigir terminacao de linha inconsistente CRLF-LF entre gemeas master-enterprise | ⏳ Rascunho gerado, aguardando aprovacao | `09-corrigir-terminacao-linha.md` |
| 10 | Simplificar parser defensivo extrair_json_manual e corrigir comentario de numeracao mentiroso | ⏳ Rascunho gerado, aguardando aprovacao | `10-simplificar-parser-defensivo.md` |
| 11 | Refatorar Fase 08 do generator (monolito, classificador por substring, excecoes copy-paste, estado global com sentinela dupla) | ⏳ Rascunho gerado, aguardando aprovacao | `11-refatorar-fase-08.md` |
| 12 | Remover imports mortos nos gates locais de master-enterprise | ⏳ Rascunho gerado, aguardando aprovacao | `12-remover-imports-mortos.md` |
| 13 | Estreitar except Exception e except pass remanescentes em gates da raiz e src-core | ⏳ Rascunho gerado, aguardando aprovacao | `13-estreitar-except-exception.md` |
| 14 | Corrigir contradicao headless-interativa em cmd_orchestrate e decompor a funcao | ⏳ Rascunho gerado, aguardando aprovacao | `14-corrigir-contradicao-headless.md` |
| 15 | Corrigir violacao de Lei de Demeter em database.py e unificar reescrita SQL (AST vs regex) | ⏳ Rascunho gerado, aguardando aprovacao | `15-corrigir-violacao-lei.md` |
| 16 | Decompor God class SecurityGate (G_SEGURANCA) e renomear metodos camada-N | ⏳ Rascunho gerado, aguardando aprovacao | `16-decompor-god-class.md` |
| 17 | Polimento estrutural: materializador do generator, idioma try-except-import duplicado, sys.path fragil no ops, funcoes sem decomposicao no ops | ⏳ Rascunho gerado, aguardando aprovacao | `17-polimento-estrutural-materializador.md` |
| 18 | Polimento de testes e UX: time.sleep em testes e banners-prints misturando UI e log | ⏳ Rascunho gerado, aguardando aprovacao | `18-polimento-testes-ux.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
