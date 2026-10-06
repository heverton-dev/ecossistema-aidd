# Ciclo de Vida Completo de Uso — AIDD Master Pack v2.0.0

> **Tag analisada:** `v2.0.0`
> **Base:** comportamento real de `scripts/provision_project.py`, `scripts/add_module.py` e `templates/v2/` extraídos da tag via `git archive`.
> Este documento descreve o que efetivamente acontece ao usar a v2.0.0 — não o ciclo de vida das versões v4/v5 (que incluem SPEC Gate, benchmark, auto-remediação etc., inexistentes nesta tag).

---

## 1. Visão Geral do Ciclo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 0: OBTENÇÃO DO PACOTE                                                   │
│ 1. Clonagem do repositório (git clone + checkout da tag v2.0.0)             │
│ 2. Instalação da skill em ~/.agents/skills/aidd-master-pack/ (hub local)    │
│    — provision_project.py DEPENDE dessa pasta existir para copiar templates │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 1: PROVISIONAMENTO DO PROJETO BASE                                     │
│ $ python scripts/provision_project.py "descrição do projeto em 3+ palavras" │
│ 1. Slugifica as 3 primeiras palavras da descrição                           │
│ 2. Cria estrutura de pastas: src/core, src/modules, src/static/components,  │
│    tests/unit, tests/load, scripts/gates, docs                              │
│ 3. Copia database.py, events.py, openapi.py do hub para src/core/           │
│ 4. Copia Dockerfile, docker-compose.yml, deploy.sh para a raiz              │
│ 5. Copia locustfile.py (genérico) para tests/load/                          │
│ 6. Copia add_module.py para scripts/                                        │
│ 7. Copia os 3 gates (G_QUALIDADE, G_SEGREDOS, G_HARNESS_COMPAT)             │
│ 8. git init no diretório do projeto                                         │
│ 9. Tenta registrar o projeto no ORCA (orca repo add) — falha silenciosa     │
│    se o CLI orca não estiver disponível                                     │
│ 10. Gera AGENTS.md e replica seu conteúdo em CLAUDE.md, GEMINI.md,          │
│     .cursorrules (4 cópias idênticas do mesmo texto)                        │
│ 11. Grava PLANO-EXECUCAO-ESTRUTURADO.json com 3 fases de status FIXO        │
│     (fase-01 e fase-03 já nascem "CONCLUIDO", sem checagem real)            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 2: CRIAÇÃO DE MÓDULOS DE DOMÍNIO SOB DEMANDA                           │
│ $ python scripts/add_module.py <nome> ["descrição"]                         │
│ 1. Slugifica o nome do módulo                                               │
│ 2. Cria src/modules/<slug>/ com __init__.py                                 │
│ 3. Gera models.py — schema SQLite genérico:                                 │
│    mod_<slug>(id, titulo, dados_json, ativo, criado_em)                     │
│ 4. Gera services.py — classe <Slug>Service com listar/criar/deletar,        │
│    emitindo eventos via EventBus (<slug>_criado / <slug>_deletado)          │
│ 5. Gera routes.py — registra GET/POST em /api/<slug> via RouteRegistry      │
│ 6. Gera componente visual HTML em src/static/components/<slug>.html         │
│    (card com input + botão "Adicionar", zero emojis)                       │
│ 7. Gera teste unitário tests/unit/test_<slug>.py cobrindo criar/listar/     │
│    deletar e a emissão do evento correspondente                             │
│ Este passo é repetido manualmente para cada módulo de negócio desejado      │
│ (ex.: afiliados, cupons — ver examples/plataforma-modular-assinaturas)      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 3: LACUNA MANUAL — LIGAÇÃO DO SERVIDOR HTTP (NÃO AUTOMATIZADA)         │
│ A tag v2.0.0 NÃO gera um src/main.py ou src/server.py que:                  │
│  - importe cada módulo e chame registrar_rotas(service)                     │
│  - sirva /openapi.json via RouteRegistry.generate_openapi_json()            │
│  - sirva /docs via RouteRegistry.get_swagger_html()                         │
│  - trate requisições HTTP reais (GET/POST) despachando para self.routes     │
│ Esse "cabeamento" fica a cargo do desenvolvedor/agente que usa o pacote —   │
│ é o elo que falta entre "módulos gerados" e "API rodando de fato".          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 4: VALIDAÇÃO MECÂNICA (GATES)                                          │
│ $ python scripts/gates/G_QUALIDADE.py     — compila (py_compile) todo .py   │
│ $ python scripts/gates/G_SEGREDOS.py      — regex + Entropia de Shannon     │
│ $ python scripts/gates/G_HARNESS_COMPAT.py — sempre retorna OK (sem checar) │
│ Nenhum gate desta tag executa pytest nem valida os testes gerados no        │
│ Passo 2 automaticamente — isso é feito manualmente com `pytest`.            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 5: TESTES                                                              │
│ $ pytest                       — roda os testes unitários de cada módulo    │
│ $ locust -f tests/load/locustfile.py — teste de carga (rotas genéricas,     │
│   precisam ser editadas manualmente para bater com os módulos reais)        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 6: EMPACOTAMENTO E DEPLOY                                              │
│ $ docker compose up -d          — requer requirements.txt e src/main.py,    │
│                                    NENHUM dos dois é gerado pelo pacote     │
│ $ bash deploy.sh                — git pull + docker compose down/build/up  │
│                                    em uma VPS (Hetzner/Contabo) já preparada│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 7: SAÍDA ENTREGUE                                                      │
│ Estrutura de projeto modular completa (módulos, testes, componentes,        │
│ manifesto de plano, Docker), PORÉM sem servidor HTTP funcional pronto —     │
│ o "produto final" desta tag é um esqueleto avançado, não uma aplicação      │
│ executável fim-a-fim sem intervenção manual adicional.                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Observação sobre os Exemplos Incluídos na Tag

Vale registrar que dos 3 projetos em `examples/` desta tag, apenas `plataforma-modular-assinaturas` percorreu de fato o ciclo acima (Fases 1 e 2). Os outros dois exemplos (`catalogo-digital-whatsapp`, `plataforma-de-membros`) foram construídos manualmente no padrão anterior (v1.0, "AIDD 4 Camadas", servidor `http.server` manual) e apenas foram incluídos no repositório junto com a tag v2.0.0, sem passar pelo fluxo `provision_project.py` → `add_module.py` descrito aqui.
