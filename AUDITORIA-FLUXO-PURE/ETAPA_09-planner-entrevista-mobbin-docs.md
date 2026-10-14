# Auditoria de Etapa: Planner, passos 2 a 5 — entrevista (grill e spec), Mobbin, extrator, forge e documentação

> **EXECUTADO EM MODO AUTÔNOMO (`/goal`, 13/10/2026).** O usuário não estava no chat: as decisões técnicas abaixo foram tomadas por recomendação própria, uma a uma, e estão registradas como "Decisão autônoma". Nenhuma resposta de entrevista foi atribuída ao usuário: as fixtures de teste do grill usam `Recommended: <resposta>, porque <motivo>`.

Fecha os Tickets 2, 3, 4, 5, 6, 7 e 8 da ETAPA_05 e o 8-C da ETAPA_08. Correção feita no clone; o espelho no motor original está na branch `fix/pure-etapa-09-planner-jornada` (ver ETAPA_10 para o resultado do espelho).

### [RECURSO]: Passo 2 — Entrevista (grill) e spec antes do planner (Ticket 2)
- **Ordem de Execução:** após o Ambiente (ETAPA_08). Teste primeiro.
- **Ação Executada:** novo `src/core_planner/intake.py` (+ re-exportação) e subcomando `planner entrevista --pasta P --modo interativo|autonomo`. O `planner init` e a etapa 2 do `/pure` só abrem com `.aidd/intake/grill.md` e `.aidd/intake/spec.md`: o grill passa em `ecossistema.py grill validar` **e** pergunta o visual (tom, cor, referências, público); a spec passa em `spec validar` **e** tem um bloco `### Visual Direction` com `tom`, `cor_primaria` (#RRGGBB), `referencias`, `publico`. A orquestração (`--modo-intake`) repassa o modo; o registro `.aidd/intake/intake.json` guarda os sha256 e o modo (`autonomo` marca execução sem usuário no chat).
- **Entrega / Artefato Gerado:** `tests/test_intake.py` (18 testes), fixtures reais `tests/fixtures/intake/{grill,spec}.md` (validadas pelas CLIs reais), `scripts/test_orquestrador_ambiente.py` (+2).
  - *Caminho Exato (100% concluído):* `modulos/01-governanca-e-qualidade/core/aidd-planner/src/core_planner/intake.py`, `src/cli.py`, `scripts/orquestrador_sincrono.py`.
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. Red: erro de coleta (módulo inexistente). Green: 16 passed; depois da regressão natural (testes antigos de `init`/orquestrador reprovaram, o que provou o bloqueio) e do ajuste de fixtures, planner **105 passed**; raiz (orquestrador, extrator, forge, docs, guarda do Next.js) **56 passed**.
  - *Prova real (sem mocks):* `planner ambiente --mobbin 3` → `planner entrevista --modo autonomo` (exit 0, registro com hashes) → `planner init` (exit 0; Design System com a cor da spec); pasta sem intake: exit 1 listando o que falta (`/aidd-grill`, `/aidd-spec` e os caminhos).
  - *Falhas / Anomalias:*
    - *Ocorrência (erro meu):* nomeei o subcomando `intake`, mas o `ecossistema.py planner` já trata a palavra `intake` como apelido antigo de `init` (`cmd_planner`, linhas 475-476): o comando nunca chegava ao planner e o orquestrador falhava com "intake incompleto". Achado ao reproduzir isolado (`argumento --fluxo exigido`). **Decisão autônoma:** renomear o comando para `entrevista` (combina com o vocabulário do usuário); a pasta e o módulo continuam `intake`.
    - *Bug achado de passagem (nano-ticket resolvido):* `DESIGN-SYSTEM.json` lia `paleta.get("primary")`, mas a chave da paleta é `primaria`: o modo dual saía **sempre** `#3b82f6`, qualquer que fosse a paleta do projeto (`design_system.py`). Corrigido com teste (`test_dual_mode_usa_a_primaria_do_catalogo_...`).
  - *Decisão autônoma:* a cor decidida na entrevista/spec (`cor_primaria`) **vence** a extraída do Mobbin; o Mobbin complementa (arquétipo, tokens neutros, links).

### [RECURSO]: Passo 4 — Mobbin no `planner init` (Ticket 3)
- **Ação Executada:** novo `src/core_planner/referencias.py`: com o caminho 2 (chave), uma **consulta descritiva por tela** (apps de referência da spec × dashboard/tabela/formulário, mais o domínio), modo `standard` explícito, cache por hash em `.aidd/cache/mobbin/`, tokens agregados das telas e `referencias-ui.json` com **só tokens e links** (nunca imagens nem as URLs delas, que expiram em ~30 dias); caminho 1 (MCP): o harness grava `.aidd/intake/referencias-mcp.json` (telas e fluxos) e o planner valida e registra; caminho 3 ou falha: cai na **spec**, com aviso em stderr e no arquivo (nunca em silêncio e nunca no catálogo por palavras-chave). O `DESIGN-SYSTEM.json` ganha `referencias_ui` e `direcao_visual`.
- **Entrega / Artefato Gerado:** `tests/test_mobbin_planner.py` (16 testes) e 2 testes de `init` em `tests/test_intake.py`.
- **Status & Diagnóstico:**
  - *Sucesso:* Sim.
  - *Prova real com a API do Mobbin (chave do `.env`):* `planner init` → exit 0 em **29,8 s**: 8 consultas, **46 telas**, 8 arquivos de cache; segunda execução com `--force` → exit 0 em **3,5 s** (só cache); `referencias-ui.json` sem URL de imagem; arquétipo `rail_two_level` (apps Linear/Stripe); a cor do Design System seguiu a da spec (`#0F766E`).
  - *Falhas / Anomalias:* ver Passo 3 (a prova real achou um defeito que os testes sintéticos não pegaram).

### [RECURSO]: Passo 3 — Extrator de tokens (Ticket 4)
- **Ação Executada:** em `componentes/compartilhado/mcps/mobbin_mcp/token_extractor.py`: recorte do rodapé "curated by Mobbin" (~48 px em 768 px, proporcional); tons parecidos fundidos (16 níveis por canal); o laço **percorre todas as cores** (o `break` aos 6 tons de fundo foi removido); a primária é a de maior saturação×frequência; uso de `image.url` (o `image_url` é só reserva); download injetável; novo `extrair_tokens_de_telas` (várias telas votam; tela que não baixa não derruba as outras); o resultado declara `nao_extraido_da_imagem: [tipografia, espacamentos, raios_borda]`. No cliente do planner (`mobbin_client.py`): `MobbinError` no lugar de `sys.exit`, só `standard|deep` (`fast` levanta `ValueError`) e `image.url` na saída.
- **Entrega / Artefato Gerado:** `tests/test_mobbin_tokens_extrator.py` (11 testes, imagens sintéticas) e os testes do cliente em `test_mobbin_planner.py`.
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. Red: 6 de 7 falharam, incluindo a reprodução do defeito (primária quase branca).
  - *Falhas / Anomalias:*
    - *Ocorrência (a prova real pegou o que o teste sintético não pegou):* nas telas reais do Linear (quase cinzas, destaques pastéis de poucos pixels) a primária ainda saía `#f9f9f9`, porque o contraste mínimo de 3:1 reprovava todas e o código caía em `paleta_hex[1]` (um tom de fundo). Diagnosticado com as imagens reais baixadas **só em memória** (nada gravado). **Correção:** segundo passe com contraste ≥ 1,8; se mesmo assim não houver cor, o resultado declara `primaria_detectada: false` e usa o neutro `#3b82f6` em vez de inventar um tom de fundo; o agregado só vota entre as telas com primária detectada. Nas 6 telas reais: roxo `#7883d4`, `#707cd3` e verdes, todas detectadas.
    - *Erro meu nos testes:* primeiro escrevi um teste "tela cinza com um traço de destaque não tem primária"; estava errado (com o segundo passe o traço conta). Refeito com uma tela cinza **sem** destaque, que é o caso real de "não detectada".
    - *Limite declarado, não corrigido:* tipografia (tabela por nome do app), espaçamentos e raios são convenção do ecossistema: a imagem não informa fonte nem raio. O resultado agora diz isso (`nao_extraido_da_imagem`).

### [RECURSO]: `forge mobbin` duplicado (Ticket 5)
- **Ação Executada:** o subcomando `mobbin` do `aidd-forge` (`componentes/compartilhado/skills/aidd-forge/scripts/cli.py`) estava **só declarado**, sem tratamento algum, e duplicava `planner mobbin`; removido da fonte e dos 6 espelhos (todos byte-idênticos à fonte antiga). O relatório E2E de 05/10 (que mandava remover) e o `aidd-forge.md` §9 de 03/10 (que dizia ter adicionado) se contradiziam; o estado real agora é: o Mobbin é do planner.
- **Entrega / Artefato Gerado:** `tests/test_forge_sem_mobbin.py` (2 testes).
- **Status & Diagnóstico:** Sim. Red: 2 falharam; Green: 2 passed. *Pendente no espelho:* `handoff-forge.json` precisa ser reemitido (`forge handoff emit`) por mudança em `scripts/*.py` do forge (regra da skill).

### [RECURSO]: Documentação, chave e emenda (Tickets 6 e 7; 8-C da ETAPA_08)
- **Ação Executada:** a skill `aidd-planner`, o comando `/planner` e o `.env.example` agora documentam a jornada (Ambiente com a ordem 1 MCP, 2 chave, 3 nenhum; as 6 variáveis de deploy; entrevista; `Visual Direction`; `referencias-ui.json`; `--modo autonomo`), copiados para os espelhos idênticos (6 da skill, 5 do comando). `planner mobbin status` **não imprime mais nenhum caractere da chave** (só "sim/não"). Emenda no `ETAPA_03_v4` corrigindo o diagnóstico de que o PURE não lia o `.env`.
- **Entrega / Artefato Gerado:** `tests/test_planner_skill_documenta_jornada.py` (4 testes).
- **Status & Diagnóstico:** Sim (Red: 4 falharam; Green: 4 passed). *Decisão autônoma (Ticket 8, harnesses):* manter `gemini-cli` **e** `antigravity` no manifesto (a substituição do Gemini CLI vale só para o plano gratuito, segundo a documentação lida) e passar a detectar também o Gemini CLI no Ambiente, com o passo a passo marcado como não verificado.

## TICKETS
- **Resolvidos neste relatório:** 2 (entrevista/spec), 3 (Mobbin no init), 4 (extrator, com o defeito extra achado na prova real), 5 (forge mobbin), 6 (docs e chave), 7 (emenda), 8 (harnesses, por decisão autônoma), 8-C (docs do Ambiente), mais o bug do `dual_mode`.
- **Ticket 9-A: limites do extrator de tokens — ABERTO (limite conhecido, não defeito):** tipografia, espaçamentos e raios não saem da imagem. *Prompt (EN):* derive typography and radii from the Visual Direction or from MCP flow data instead of the per-app table.
- **Ticket 9-B: passos a passo dos harnesses OpenCode, MiMoCode, Antigravity e Gemini CLI — ABERTO:** não verificados em instalação real (mantido do 8-D).
- **Ticket 9-C: `.codebuddy/` desatualizado nas cópias locais da skill e do comando do planner — ABERTO (local, não versionado):** copiar a fonte para `.codebuddy/skills/aidd-planner/SKILL.md` e `.codebuddy/commands/planner.md` no original, senão `G_HARNESS_COMPAT` reprova.
