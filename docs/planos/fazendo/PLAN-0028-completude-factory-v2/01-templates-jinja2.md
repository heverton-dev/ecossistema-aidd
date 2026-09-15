# Item 01: Templates Jinja2 para Gateway e Frontend

## Escopo
Criar os templates Jinja2 que as fases LLM (2, 3, 7) usam para gerar codigo.

## Definicao de Pronto
- [ ] `templates/gateway/main.py.jinja2` — FastAPI app com endpoints por servico
- [ ] `templates/gateway/routes.py.jinja2` — Rotas proxy por servico
- [ ] `templates/gateway/models.py.jinja2` — Modelos Pydantic tipados
- [ ] `templates/frontend/next.config.js.j2` — Config Next.js
- [ ] `templates/frontend/layout.tsx.j2` — Layout whitelabel com sidebar
- [ ] `templates/frontend/page.tsx.j2` — Dashboard page
- [ ] `templates/frontend/tenant.config.json.j2` — Config de marca
- [ ] `templates/docs/openapi.json.j2` — Swagger spec
- [ ] `templates/docs/README.md.j2` — Documentacao de deploy
- [ ] Cada template e validado com `jinja2 compiles` (sintaxe)
- [ ] Gate G_FACTORY_TEMPLATES.py verifica existencia e sintaxe

## Dependencias
- Nenhuma (templates sao estaticos)

## Evidencia
- v2 doc §4.2 lista exatamente esses templates
- Padrao Jinja2 ja usado em aidd-master/enterprise (cookiecutter)
