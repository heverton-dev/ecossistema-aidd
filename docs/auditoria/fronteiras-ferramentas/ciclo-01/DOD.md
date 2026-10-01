# Definição de Pronto (Definition of Done - DoD) — fronteiras-ferramentas

> Alvo: as 8 ferramentas (`tools/aidd-*`), o almoxarifado (`componentes/compartilhado/`), o orquestrador `run-fluxo` e os contratos entre etapas.
> Visão: forge prepara o terreno e guarda todas as peças → planner desenha a planta com tickets roteados → construtores e acabamento consomem as peças sob demanda. Nenhuma ferramenta guarda cópia.
> Origem: `docs/auditoria/meus-prompts/PROMPT-FRONTEIRAS-E-DEDUP-FERRAMENTAS.txt` · Diagnóstico: `DIAGNOSTICO.md` · Foto "antes": `TESTES_E2E-ecossistema-aidd\ciclo-01\BASELINE-E2E.md`.

## Critérios Obrigatórios de Aceite

1. **DoD 1: Inventário e tag de segurança antes de tudo (D15)**
   - Tag `pre-fronteiras-ciclo-01` criada; `INVENTARIO-ANTES.json` gravado com cada função, classe, teste, gate e molde de cada cópia.
   - `scripts/inventario_capacidades.py comparar` acusa capacidade órfã num teste plantado (exit 1).

2. **DoD 2: Mapa de donos aprovado (D1)**
   - `MAPA-DONOS-FERRAMENTAS.json` cobre as 8 ferramentas; cada responsabilidade tem um único dono; só o forge pode guardar peças.
   - As decisões D1, D4 e D5 foram respondidas pelo usuário (registro escrito, nunca presumido).

3. **DoD 3: Gate de fronteira existe e morde (D1)**
   - Acusa arquivo no dono errado e cópia de peça do catálogo dentro de `tools/` (exit 1 em `bloqueio`, relatório com exit 0 em `aviso`).

4. **DoD 4: Contrato só passa com evidência (D2)**
   - `validar_handoff.py` reprova contrato sem prova ou não gravado pela ferramenta dona; `run-fluxo --dry-run` não imprime mais "100% DE APROVAÇÃO".

5. **DoD 5: Almoxarifado único + consumo sob demanda (D15)**
   - `CATALOGO.json` lista cada peça com dono do conteúdo, versão e sha256; a versão do catálogo não perdeu nenhuma capacidade de nenhuma cópia (`comparar` = 0 órfão).
   - `forge fornecer` / `obter_peca` entrega a peça na pasta do projeto e recusa gravar dentro de `tools/`.

6. **DoD 6: Bastão com prova (D2)**
   - O forge só entrega depois do checklist de prontidão (dependências, leis e guardas, harnesses, almoxarifado, commit inicial, IA disponível) — C1.
   - O planner entrega a planta com tickets para o construtor, master, enterprise e ops, mais o `perfil_app` — C2.
   - O orquestrador não escreve contrato; o `dispatch` roda na etapa do master; a etapa 7 audita o projeto.

7. **DoD 7: Cada ferramenta consome do almoxarifado (D1)**
   - factory, bridge, generator, ops, master e enterprise, um ticket por ferramenta, cada um com o seu teste de fronteira verde.
   - Depois de cada ticket, os 3 fluxos E2E rodaram de novo numa pasta `ciclo-NN` nova, e nenhuma métrica piorou contra o ciclo-01.

8. **DoD 8: Cópias removidas sem perder nada (D15)**
   - Zero cópia de peça do catálogo dentro de `tools/` (`contar_duplicatas.py`); baseline: 249 conteúdos repetidos em 727 arquivos, 126 cópias de gate.
   - `comparar INVENTARIO-ANTES.json` = **zero órfão**; total de testes passando **≥ 2352**; cada remoção confirmada pelo usuário.

9. **DoD 9: Fiscal e contratos bloqueando (D13)**
   - `AIDD_FRONTEIRA_MODO` com padrão `bloqueio`; `gates/allowlist_fronteira.json` vazio; bateria completa verde.

10. **DoD 10: A foto "depois" passa — OBRIGATÓRIO (D12)**
    - Os 3 fluxos rodados de novo do zero, num worktree isolado, numa pasta nova `TESTES_E2E-ecossistema-aidd\ciclo-NN\`.
    - `comparar_baseline_e2e.py` sai com exit 0: **igual ou melhor em todas** as métricas contra o ciclo-01 — exit code, etapa onde quebrou, Quarteto (`/api`, `/webhook`, `/mcp`, `/docs`), vazamentos fora da pasta, duplicatas, tempo dos gates (baseline 711 s), tokens e órfãos do inventário (0).
    - Sem este item, o ciclo **não** está pronto, mesmo com todos os outros verdes.

11. **DoD 11: README de cada ferramenta conta a fronteira real (D14)**
    - A seção "faz / não faz / consome do almoxarifado" dos 8 READMEs bate com o mapa (verificado por teste).

12. **DoD 12: Um nome só por construtor (D14)**
    - `tools/aidd-pure`, `tools/aidd-open`, `tools/aidd-freedom` (antes generator, factory, bridge); nenhuma referência ao nome antigo fora da tabela de apelidos e dos documentos históricos.
    - Os comandos antigos ainda funcionam como apelido, com aviso, por 1 ciclo; inventário com zero órfão depois da troca.

13. **DoD 13: Cada ticket com o seu gate, e um manifesto por bloco (D13)**
    - O compilador grava em `gate_fase` o comando da linha `Gate do Ticket` de cada ticket; o teste de cada ticket (inclusive em `tools/` e `gates/`) roda de verdade.
    - Saem 5 manifestos `PLANO-EVOLUCAO-BLOCO-N.json`; cada bloco termina com `gate_final` verde + `--aprovar` do usuário; o Bloco 4 é feito com o usuário, peça por peça.

14. **DoD 14: Mapas visuais e livros contam o estado final (D14)**
    - Os 13 mapas de `docs/mapas-visuais` passam no `scripts/mapa_visual.py <tipo> --check`.
    - Os 3 livros de `docs/livros` (principal, Livro Visual, Mini-livro) foram regenerados com a data do fechamento, em md e pdf, com números lidos do disco e os nomes novos das ferramentas.

## Fora deste ciclo (registrado para o próximo)
- Responder automaticamente o protocolo delegado do generator no E2E sem intervenção humana.
- Renomear os repositórios separados no GitHub (`heverton-dev/aidd-generator` …) — exige confirmação própria.
- Consertar o `pip -e` do aidd-forge (a chamada direta `python -m aidd_forge.cli` fora da pasta da ferramenta).
