# Item 1 — Intake Interativo Web Sem Friccao

> **Escopo:** Intake autônomo via formulário/UI web rodando como app gerenciado no Coolify (Streamlit em porta privada com proxy FQDN), sem serviço/banco novo fora do Coolify e sem depender de frontend custom construído no monorepo.
> **Status:** ✅ IMPLEMENTADO em 2026-09-07 (NIH #19 — Streamlit + Coolify) — aguardando auditoria humana final (não fabricada).

---

## Contexto ja investigado

- NIH #19 (`docs/features/oportunidades-reaproveitamento-oss-nih.md`): intake web planejado era NIH — resolvido com **Streamlit** (app gerenciado pelo Coolify), sem frontend custom.
- `scripts/pipeline_ops.py` já concentrava o intake autônomo (Fase 1-3: nicho → stack → sizing) no CLI; o intake web reusa a MESMA lógica (`montar_plano_em_memoria`) — sem duplicação de regra de negócio.
- Decisão registrada nos itens 03/04 da iniciativa: Coolify adotado como plataforma self-hosted para VPS compartilhada; app gerenciado é o mecanismo de deploy.

## Definicao de Pronto

1. Intake funcional: fluxo completo operável via web (texto livre/nicho → stack → sizing → `PLANO-INFRAESTRUTURA.json`) — atendido por `apps/intake/app.py` + `intake_core.py` (17 testes dedicados, exit 0).
2. Deploy via Coolify: intake elegível como **app gerenciado** (build_pack dockerfile) com subcomandos `pipeline_ops.py coolify create|setenv|deploy` — atendido e testado (dry-run determinístico + client real contra fake server de teste; deploy em instância real exige `COOLIFY_BASE_URL`/`COOLIFY_API_TOKEN`).
3. Composed como imagem própria (`Dockerfile.intake`, porta 8501, headless, healthcheck `/_stcore/health`) com `requirements.txt` pinado.
4. Nenhuma duplicação NIH: reusa Streamlit em vez de escrever frontend próprio.
5. Testes executados com exit 0 e conformidade com os Quality Gates: 144 testes aidd-ops verdes; `G_OPS_MVP` (78 checks) e `G_OPS_SSH` (5 checks) aprovados.

## Criterio de saida

- Arquivos criados em `tools/aidd-ops/apps/intake/`, `tools/aidd-ops/Dockerfile.intake` e subcomando `coolify` em `scripts/pipeline_ops.py`.
- Testes reais passando (144/144) sem stubs falsos.
- Gates G_OPS_MVP e G_OPS_SSH aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 1: Intake Interativo Web Sem Friccao.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 1: Intake Interativo Web Sem Friccao.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
