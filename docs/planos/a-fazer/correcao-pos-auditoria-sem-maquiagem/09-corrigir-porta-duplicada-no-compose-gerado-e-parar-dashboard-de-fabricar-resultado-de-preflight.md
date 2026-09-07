# Item 9 — Corrigir porta duplicada no compose gerado e parar dashboard de fabricar resultado de preflight

> **Escopo:** Entra duas correções relacionadas: (a) o template/sizing do docker-compose gerado não deve mais atribuir a mesma porta host a dois serviços; (b) `dashboard_server.py` `/api/preflight` deixa de devolver JSON hardcoded e passa a computar de verdade, reaproveitando a mesma chamada a `docker compose config` que `preflight_check.py` já faz. Não entra: redesenhar o dashboard inteiro.
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]
> **Modelo sugerido:** Claude Sonnet · Antigravity Gemini 3.7 · MiMo mimo-v2.5-pro (lógica real de detecção de colisão + reuso de código existente)
> **Dependência com o plano estratégico:** este item é **condicional à decisão Coolify/CapRover** da Fase 2 de `direcionamento-estrategico-anti-nih/`. Se a decisão for "adotar", o roteamento por host do Coolify elimina a colisão de porta por design e este item pode encolher para só corrigir o dashboard. Se a decisão for "manter infra própria", este item continua 100% necessário como está escrito abaixo. Não presuma qual caminho foi escolhido — confirme antes de começar.

---

## Contexto ja investigado

- Confirmado por fork de auditoria com Docker real instalado: projeto gerado para o nicho "clínicas" publica `twenty-server`, `chatwoot-rails` e `calcom-server` todos na porta host `3000` (`.env`/`.env.example`: `CALCOM_PORT=3000`, `CHATWOOT_RAILS_PORT=3000`, `TWENTY_SERVER_PORT=3000`) — `docker compose up` falharia com "port is already allocated" no segundo/terceiro serviço. `docker compose config` só valida sintaxe, não pega isso.
- `dashboard_server.py:78-99` retorna um JSON 100% hardcoded no código do servidor alegando "8 portas mapeadas, sem colisão" (80, 443, 3000, 3002, 3003, 5432, 8082, 9000) — números que não existem no compose real, e que nem sequer citam a colisão real em 3000. `dashboard.html` faz `fetch('/api/preflight')` e exibiria essa mentira como se fosse checagem ao vivo.
- `preflight_check.py` já faz uma chamada real a `docker compose config` para outra checagem — é a base a reaproveitar em vez de reescrever do zero.

## Definicao de Pronto

1. Gerar um novo plano de infra para o mesmo nicho ("clínicas") e confirmar, de forma determinística (parseando `docker compose config` e comparando portas publicadas), que nenhuma porta host se repete entre serviços.
2. `/api/preflight` do dashboard chama a mesma lógica real (não hardcoded); testando contra um compose com colisão induzida de propósito, o endpoint reporta a colisão corretamente — e contra um compose limpo, reporta "sem colisão" de verdade.
3. Teste automatizado cobrindo os dois casos (sem colisão / com colisão induzida) passa.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 9: Corrigir porta duplicada no compose gerado e parar dashboard de fabricar resultado de preflight.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 9: Corrigir porta duplicada no compose gerado e parar dashboard de fabricar resultado de preflight.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
