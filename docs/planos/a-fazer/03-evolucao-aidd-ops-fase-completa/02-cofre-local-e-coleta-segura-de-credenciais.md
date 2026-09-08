# Item 2 — Cofre Local e Coleta Segura de Credenciais

> **Escopo:** Credeciais do aidd-ops saem do codigo/compose versionado e passam a
> viver cifradas num cofre local, integradas ao `docker-compose up`. NAO entra:
> cofre multi-usuario/UI, rotation automatica, integracao com secret/vault externo
> na nuvem. **Status: ✅ CONCLUIDO — implementado em 2026-09-07 (NIH #18/#29).**
> Decisao: **sops+age** (registrada abaixo). Vaultwarden descartado — traz
> servico/banco pra um caso de uso que é pipeline automatizado, nao humano
> compartilhando senha via UI.

---

## Decisao: sops+age vs Vaultwarden (2026-09-07)

| Criterio | **sops + age (ESCOLHIDO)** | Vaultwarden (descartado) |
| :--- | :--- | :--- |
| Modelo | Cifragem assimetrica local, sem rede | Cliente-servidor (Bitwarden-compativel) com banco |
| Infra a manter | Só binario `sops` + gerador de chaves `age-keygen` | Servico + banco + rede + autenticacao de usuarios |
| Fluxo de deploy automatizado (Coolify/Ansible) | Comando local deterministico (exit 0/1) | Requer HTTP, tokens/API, estado do servico |
| Segredo em disco | Nunca (decifra no momento do `up`) | Fica no cofre do servidor |
| Multi-usuario/UI | Nao (fora do escopo) | Sim — mas nao e o caso de uso aqui |

**Conclusao:** para pipeline automatizado sem humanos compartilhando senha, o custo
de manter um servico nao compensa; `sops+age` resolve com zero infra adicional.

## Implementacao (evidencia, 2026-09-07)

- `tools/aidd-ops/src/core/cofre_credenciais.py` — `CofreCredenciais`:
  `gerar_chave_age`, `gerar_sops_config`, `cifrar_env`, `decifrar_env`,
  `montar_comando_docker_compose_up`, `subir_servico_com_cofre`.
- CLI: `pipeline_ops.py cofre init|encrypt|decrypt|up`.
- **Bug real encontrado no smoke da CLI e corrigido:** o sops casava o `path_regex`
  contra o caminho ABSOLUTO do input; no Windows (barra inversa) o regex
  `templates/infra/.*\.env\.enc$` (que ainda mirava o `.env.enc` de saida) nunca
  casava → `no matching creation rules found`. Corrigido com:
  1. default `path_regex` agnostico a separador: `templates[\\/]infra[\\/].*\.env$`
     (mira o `.env` de ENTRADA);
  2. cifragem amarrada explicitamente por `--config` — config temporaria catch-all
     quando `--chave-publica` e informada, e descoberta deterministica do
     `.sops.yaml` (sobe do diretorio do `.env`, fallback cwd) no fluxo normal
     (o sops so descobre config a partir do cwd, nao do arquivo de entrada).
- Cobertura: 17 testes reais em `tools/aidd-ops/tests/test_cofre_credenciais.py`
  (binarios reais `sops` 3.13.3 / `age-keygen`), incluindo regressao do smoke CLI.
- Smoke CLI end-to-end confirmado: init → encrypt (chave explicita **e** config
  descoberta) → decrypt → round-trip identico; `.env.enc` sem segredo em texto.
- Manual de uso: secao "Cofre de Credenciais" em `tools/aidd-ops/README.md`.
- Templates de infra continuam sem credencial hardcoded — apenas interpollacao
  `${VAR:?Defina ... no .env}`; `.env` continua coberto pelo `.gitignore` da raiz.

## Definicao de Pronto

1. Cofre funcional com binarios reais: `cofre init` gera chave age + `.sops.yaml`;
   `encrypt` produz `.env.enc` sem segredo em texto; `decrypt` restaura o `.env`
   identico ao original (round-trip verificado por `diff`).
2. Fluxo de producao nao depende do cwd: config descoberta/amarrada por `--config`.
3. `cofre up` = decifra `.env.enc` e roda `docker compose up -d` com `--env-file`.
4. Credenciais nao hardcoded: templates so usam interpollacao `${VAR:?...}`.
5. Testes executados com exit 0 (17/17) e conformidade com os Quality Gates.

## Criterio de saida

- Arquivos criados/alterados no local correto (`tools/aidd-ops/`, `docs/`).
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai validar o Item 2: Cofre Local e Coleta Segura de Credenciais.
Verifique a Definicao de Pronto acima contra a implementacao existente.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to validate Item 2: Cofre Local e Coleta Segura de Credenciais.
Check the Definition of Done above against the existing implementation.
Do not fabricate approvals and maintain monorepo governance rules.
```