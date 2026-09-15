# Item 03: Fase 4 — Gerador de Compose Unificado

## Escopo
Implementar `src/core/docker_composer.py` que faz merge dos compose templates selecionados pelo nicho em um docker-compose.yml unificado.

## Definicao de Pronto
- [ ] `docker_composer.py` implementado com 100% determinismo
- [ ] Le factory_analysis.json e monta lista de blocos obrigatorios + opcionais
- [ ] Le cada `templates/infra/<bloco>/docker-compose.yml` via PyYAML
- [ ] Merge: redes unificadas, depends_on encadeados, resource limits
- [ ] Resolve colisoes de portas (NIH #16 — Traefik labels, sem host port)
- [ ] Gera `docker-compose.yml` unificado no diretorio de saida
- [ ] Valida com `docker compose config` (sintaxe)
- [ ] Testes com nichos clinicas, delivery, b2b_industrial
- [ ] Gate G_FACTORY_COMPOSE.py verifica sem colisao de portas

## Dependencias
- Item 02 (analisador)

## Evidencia
- 8 templates compose existem em `templates/infra/*/docker-compose.yml`
- `compose_preflight.py` do aidd-ops ja tem validador YAML reutilizavel
- `clinicas.json` define portas_host para evitar colisao
