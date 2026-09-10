# Item 4 — Isolamento Estrito em VPS Compartilhada e Uninstall Atomico (NIH #21)

> **Escopo:** Substituir o mecanismo manual de isolamento de processos e portas em VPS compartilhada pela orquestração nativa do Coolify (redes Docker dedicadas por projeto/ambiente, zero portas de host expostas no 0.0.0.0, roteamento via Traefik FQDN e limites estritos de recursos CPU/RAM).
> **Status:** [CONCLUÍDO em 2026-09-07 — Isolamento nativo Coolify validado via `CoolifyManager`]

---

## Contexto ja investigado

- O levantamento NIH #21 apontou que inventar isolamento multi-tenant em VPS do zero seria um dos erros mais custosos de NIH, uma vez que plataformas como Coolify foram concebidas especificamente para hospedar múltiplas stacks com segurança em uma mesma VPS.
- No Coolify:
  - Cada projeto roda em sua própria rede Docker interna (`coolify_net_<slug>_<ambiente>`).
  - Nenhuma porta colidente de aplicação (ex: :3000) é exposta no host 0.0.0.0 — todo tráfego externo passa pelo Traefik com TLS automático e roteamento por FQDN.
  - Limites de CPU e memória são aplicados por contêiner, mitigando 'noisy neighbors'.
- Implementado em `tools/aidd-ops/src/core/coolify.py` com o método `CoolifyManager.verificar_isolamento_vps` e testes determinísticos em `test_coolify.py`.

## Definicao de Pronto

1. ✅ Orquestração de todos os contêineres sem bind direto em portas do host (zero exposição 0.0.0.0).
2. ✅ Redes Docker privativas por projeto/ambiente implementadas deterministicamente.
3. ✅ Verificação estrita de isolamento (`verificar_isolamento_vps`) integrada ao pipeline de deploy.
4. ✅ Testes de isolamento cobrindo detecção de colisão de FQDN, exposição de porta e limites de CPU/RAM com 100% de sucesso.
5. ✅ Conformidade mantida com todos os Quality Gates do monorepo.

## Criterio de saida

- `tools/aidd-ops/src/core/coolify.py` com validação de isolamento.
- Testes passando em `tools/aidd-ops/tests/test_coolify.py`.
- Inventário de reaproveitamento OSS atualizado.
