# PROCESSO E DECISOES — remediar-gaps-auditoria

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

Remediar os gaps imediatos e estruturais diagnosticados na auditoria do ecossistema-aidd:
1. Eliminar falha de testes reais em `aidd-master` e `aidd-enterprise` causada por coleta indevida de requests em `scripts/test_live.py`.
2. Integrar formalmente as ferramentas `aidd-factory` e `aidd-bridge` no despachante raiz `ecossistema.py` e nos gates de integridade.
3. Estabelecer gate de verificação estática para as camadas do Frontend gerado (impedir acoplamento direto entre componentes UI e rede/APIs).

### Metrica da Iniciativa (0-10)

- **Nota Atual:** 6.0 — evidencia: `python ecossistema.py audit` falhou com exit code 1 no gate `G_TESTES_REAIS` (2 falhas reais em 2211 testes).
- **Nota Alvo:** 10.0 — evidencia esperada: `python ecossistema.py audit` retornando exit code 0 com todas as ferramentas integradas e testadas.
- **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | Corrigir test live | `01-corrigir-test-live.md` |
| 2 | Plugar factory bridge | `02-plugar-factory-bridge.md` |
| 3 | Gate camadas frontend | `03-gate-camadas-frontend.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Nota Atual | Nota Alvo | Nota Real | Documento |
|---|---|---|---|---|---|---|
| 1 | Corrigir test live | ✅ Concluído | 0.0 | 10.0 | 10.0 | `01-corrigir-test-live.md` |
| 2 | Plugar factory bridge | ✅ Concluído | 5.0 | 10.0 | 10.0 | `02-plugar-factory-bridge.md` |
| 3 | Gate camadas frontend | ✅ Concluído | 4.0 | 10.0 | 10.0 | `03-gate-camadas-frontend.md` |
