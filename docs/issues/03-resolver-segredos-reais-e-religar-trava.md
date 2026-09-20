---
id: ISSUE-0003
title: Resolver os alertas de segredo fora de teste e religar a trava
status: closed
closed_at: 2026-09-19
blocked_by: [ISSUE-0002]
created: 2026-09-19
source: open-decision sweep 2026-09-19
---

# ISSUE-0003 — Resolver os alertas de segredo fora de teste e religar a trava

**Deliver:** pushing a credential into the repo is automatically blocked again, on
every commit — or it is written down why it is not.

**Blocked by:** ISSUE-0002. With test noise cleared, the remaining alerts become readable.

## Verified this session

Os alertas fora dos diretórios diretos de teste foram inspecionados individualmente:

| Localização | Natureza Factual | Classificação |
|---|---|---|
| `chaves/manifesto/ed25519_public.json:3` | Chave **pública** Ed25519 para verificação de assinaturas do manifesto CAPABILITIES.json | Falso positivo (chave pública não é segredo) |
| `componentes/compartilhado/src-core/database_adapter.py:405` | Comentário de documentação de formato de string de conexão (exemplo genérico na docstring/comentário) | Falso positivo (comentário explicativo) |
| `componentes/compartilhado/src-core/security.py:15` | Constante sentinela de segurança com verificação que aborta imediatamente se usada em ambiente produtivo | Falso positivo (sentinela de segurança local) |
| `tools/aidd-bridge/aidd_bridge/cli.py:154` | Exemplo de formato de DSN em string de ajuda do argumento CLI | Falso positivo (help text) |
| `tools/aidd-master/CAPABILITIES.json:29` | Hash SHA-256 do artefato de segurança MCP para integridade | Falso positivo (checksum de integridade) |

Nenhum segredo real foi identificado no código-fonte. Portanto, nenhuma rotação de credenciais externas foi necessária.

## Decisão de Rota: ROTA A (Reativar o Gate)

A **Rota A** foi adotada com sucesso:
- O hook `g-segredos` teve `stages: [manual]` substituído por `always_run: true` em `.pre-commit-config.yaml`.
- A causa raiz da divergência histórica (2026-09-08) foi esclarecida: `detect-secrets` exige que `.secrets.baseline` esteja staged ao rodar no hook (`raise_exception_if_baseline_file_is_unstaged`) e que o scan de atualização receba a árvore completa de arquivos rastreados para não podar baselines existentes durante o merge.
- Execução do hook real tanto manual quanto com o hook reativado retornou `exit 0` (`Passed`).

## Acceptance criteria

- [x] Each non-test alert classified false-positive or real-secret.
- [x] Every real secret removed from source **and the credential rotated** — (nenhum segredo real no repositório; todos comprovados falsos positivos).
- [x] Real hook (`pre-commit run --hook-stage manual g-segredos --all-files`) exits 0.
- [x] Chosen route (A or B) recorded with justification in `.pre-commit-config.yaml` (Rota A reativada).
- [x] Route A: a test commit proves the gate runs and produces no false positive inside the hook.
