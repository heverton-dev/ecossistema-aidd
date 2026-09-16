# Item 3 — Gate camadas frontend

> **Escopo:** Desenvolver regras de verificação estática (linter AST ou script determinístico de arquitetura) para garantir separação estrita de camadas nas entregas Frontend do ecossistema.
> **Status:** [CONCLUÍDO]
> **Nota Atual (0-10):** 4.0 — evidencia: Nao existia nenhum gate estatico verificando chamadas de rede em componentes de apresentacao pura.
> **Nota Alvo (0-10):** 10.0
> **Nota Real (pos-implementacao):** 10.0 — evidencia: gates/G_FRONTEND_LAYERS.py criado e integrado ao pre-commit e ecossistema.py; suíte gates/test_g_frontend_layers.py 100% aprovada.

---

## Contexto ja investigado

- O ecossistema gera e exporta código frontend (Next.js/React) através de `aidd-master export-frontend` e templates do `aidd-generator`.
- Diferente do Backend (onde `G_ARQUITETURA_DELIVERABLE.py` bloqueia SQL cru fora de infra e imports de módulos vizinhos via AST), o Frontend não tem gate impedindo chamadas diretas de API dentro de arquivos de apresentação visual (ex: `components/ui/*`).

## Definicao de Pronto

1. Definir a especificação de camadas do Frontend gerado:
   - Apresentação Pura / Dumb Components (`components/ui/*`): Proibido fazer `fetch`, chamar SDKs de rede diretamente ou conter efeitos colaterais de persistência.
   - Smart Components / Hooks (`hooks/*`, `features/*/hooks/*`, `services/*`): Onde vive a orquestração e chamada à API.
2. Implementar gate determinístico (ex: script Python `gates/G_FRONTEND_LAYERS.py` analisando via regex/AST as entregas e templates de frontend).
3. Registrar o gate no pipeline de auditoria do monorepo.
4. Validar o gate contra os templates de frontend existentes com exit code 0.

## Criterio de saida

- Novo gate `gates/G_FRONTEND_LAYERS.py` funcional e com teste unitário correspondente em `gates/test_g_frontend_layers.py`.
- Integrado ao runner de auditoria do ecossistema.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 3: Gate camadas frontend.
1. Crie gates/G_FRONTEND_LAYERS.py para inspecionar os templates e componentes frontend.
2. Imponha a regra: componentes em components/ui/ nao podem chamar fetch() ou clientes HTTP inline diretamente.
3. Crie o teste unitario em gates/test_g_frontend_layers.py.
4. Execute o novo gate e seus testes, garantindo exit code 0.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 3: Gate camadas frontend.
1. Create gates/G_FRONTEND_LAYERS.py to inspect frontend components and templates.
2. Enforce: components inside components/ui/ cannot invoke fetch() or inline HTTP clients directly.
3. Create test suite in gates/test_g_frontend_layers.py.
4. Run the gate and test suite, ensuring exit code 0.
```
