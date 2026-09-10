# -*- coding: utf-8 -*-
"""Use Case: plan — geração de SPEC e plano estruturado + execução (apply) por plano aprovado."""

import json
import os
import re
import sys
import types

from application.commands.inject import _tentar_injecao_por_linguagem_natural
from application.commands.setup import ensure_environment


def cmd_plan(prompt: str, base_dir: str = ".", auto_apply: bool = False):
    """Fase 1.5: Gera especificação técnica (SPEC) e plano estruturado antes da criação."""
    ensure_environment()
    if _tentar_injecao_por_linguagem_natural(prompt, base_dir=base_dir):
        return
    prompt_lower = prompt.lower()

    KNOWN_DOMAINS = [
        "crm", "erp", "faturamento", "financeiro", "vendas", "helpdesk",
        "suporte", "logistica", "estoque", "membros", "cursos", "catalogo",
        "produtos", "pedidos", "whatsapp", "afiliados", "assinaturas", "fiscal",
        "analytics", "lead", "leads", "campanhas", "marketing", "tickets"
    ]

    found_modules = []
    for d in KNOWN_DOMAINS:
        if re.search(r'\b' + d + r'\b', prompt_lower):
            slug = "crm" if d in ["lead", "leads"] else ("helpdesk" if d in ["suporte", "tickets"] else d)
            if slug not in found_modules:
                found_modules.append(slug)

    if found_modules:
        mecanismo_usado = f"casamento de palavra-chave — domínio(s) reconhecido(s): {', '.join(found_modules)} (lista fixa, SEM LLM)"
    else:
        words = re.findall(r'\b[a-zA-Z]{4,}\b', prompt_lower)
        stop_words = {"crie", "uma", "aplicacao", "aplicativo", "sistema", "para", "com", "suite", "modulo", "faca", "gere"}
        found_modules = [w for w in words if w not in stop_words][:4]
        if found_modules:
            mecanismo_usado = "⚠️ fallback de extração de palavras — NENHUM domínio conhecido reconhecido, sem LLM (heurística mais fraca)"
        else:
            found_modules = ["principal", "configuracao"]
            mecanismo_usado = "⚠️ nenhuma palavra significativa encontrada — usando módulos padrão fixos, sem LLM"

    slug_name = "-".join(found_modules[:3]) + "-suite"
    target_path = os.path.abspath(os.path.join(base_dir, f"app_{slug_name}"))
    suite_title = " ".join(m.capitalize() for m in found_modules) + " Suite"

    os.makedirs(target_path, exist_ok=True)

    # 1. Gerar SPEC-ARQUITETURA.md em 3 Níveis Estruturados
    spec_content = f"""# Especificação Técnica de Arquitetura em 3 Níveis (SPEC / PRD)

**Projeto:** {suite_title}  
**Diretório:** `{target_path}`  
**Status do Planejamento:** AGUARDANDO_APROVACAO  
**Prompt Original:** "{prompt}"  

---

## NÍVEL 1: ESPECIFICAÇÃO DE NEGÓCIO & REGRAS DE DOMÍNIO
"""
    for m in found_modules:
        spec_content += f"""
### Domínio / Subdomínio: `{m.upper()}`
- **Entidade Principal:** `{m.capitalize()}` (identificador, título descritivo, status de ciclo de vida e carga útil JSON).
- **Casos de Uso Primários:** Cadastrar, Consultar por ID, Listar com Filtro/Busca, Atualizar Campos e Excluir com Soft-Delete.
- **Eventos de Domínio:** Publicação obrigatória de `{m}_criado`, `{m}_atualizado` e `{m}_deletado` no `EventBus`.
- **Auditoria:** Rastreabilidade temporal com campos `criado_em`, `atualizado_em` e `deletado_em`.
"""

    spec_content += """
---

## NÍVEL 2: ESPECIFICAÇÃO DE BACK-END, PERSISTÊNCIA & CONTRATOS
"""
    for m in found_modules:
        spec_content += f"""
### Contratos de API & MCP: `{m}`
- **Rotas REST:**
  - `GET /api/{m}/listar`: Retorna coleção filtrada e paginada.
  - `GET /api/{m}/metricas`: Retorna KPIs agregados (total, ativos, concluídos, taxa de conversão).
  - `GET /api/{m}/obter?id=N`: Retorna registro único ativo.
  - `POST /api/{m}/criar`: Insere novo registro e emite evento.
  - `POST /api/{m}/atualizar`: Altera dados do registro.
  - `POST /api/{m}/deletar`: Marca exclusão lógica (soft-delete).
- **Ferramentas MCP (JSON-RPC 2.0):** `mod_{m}_listar`, `mod_{m}_criar`, `mod_{m}_obter`, `mod_{m}_atualizar`, `mod_{m}_deletar`.
- **Persistência SQLite WAL:** Tabela `mod_{m}` com índices de status e exclusão.
"""

    spec_content += """
---

## NÍVEL 3: ESPECIFICAÇÃO DE FRONT-END, DESIGN SYSTEM & UX
- **Design System:** Padrão Impeccable UI com Tailwind CSS, paleta Slate/Indigo e SVGs Lucide.
- **Componentes:** Componente visual isolado em `src/static/components/<modulo>.html` para cada fatia vertical.
- **Acessibilidade WCAG 2.1:** Botões com `type="button"`, `aria-label`, foco visível e zero diálogos nativos (`alert`).
- **Dashboard Super-App:** Header unificado, cards de KPIs no topo, tabela paginada com busca em tempo real e modais de Full CRUD.

---

## PRÓXIMO PASSO: APROVAÇÃO E EXECUÇÃO
Execute `python scripts/aidd.py apply --dir "{target_path}"` para compor o código e homologar os 7 Quality Gates.
"""
    spec_path = os.path.join(target_path, "SPEC-ARQUITETURA.md")
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(spec_content)

    # 2. Gerar PLANO-EXECUCAO-ESTRUTURADO.json inicial
    plano_data = {
        "projeto": {
            "nome": suite_title,
            "slug": slug_name,
            "diretorio": target_path,
            "status": "PLANEJADO",
            "prompt_origem": prompt,
            "zero_api_key_mode": True,
            "modulos": found_modules
        },
        "arquitetura": {
            "padrao": "AIDD Modular Clean Architecture",
            "banco": "SQLite WAL",
            "mcp_enabled": True
        }
    }
    plano_path = os.path.join(target_path, "PLANO-EXECUCAO-ESTRUTURADO.json")
    with open(plano_path, "w", encoding="utf-8") as f:
        json.dump(plano_data, f, indent=2, ensure_ascii=False)

    print("=" * 80)
    print("📋 [FASE 1.5 - SPEC & PLANEJAMENTO ARQUITETURAL]")
    print("=" * 80)
    print(f"Projeto:       {suite_title}")
    print(f"Destino:       {target_path}")
    print(f"Status:        PLANEJADO (Aguardando Aprovação)")
    print(f"Fatias ({len(found_modules)}):   {', '.join(found_modules)}")
    print(f"Mecanismo:     {mecanismo_usado}")
    print(f"Documentos:    SPEC-ARQUITETURA.md | PLANO-EXECUCAO-ESTRUTURADO.json")
    print("=" * 80)

    if auto_apply:
        cmd_apply(types.SimpleNamespace(dir=target_path))
    else:
        print("\n👉 Para aprovar e compor imediatamente, execute:")
        print(f"   python scripts/aidd.py apply --dir \"{target_path}\"")
        print("👉 Ou edite o plano/especificação acima para ajustar o escopo antes da execução.\n")


def cmd_apply(args):
    """Fase 2: Lê o plano estruturado planejado e executa a composição e gates."""
    ensure_environment()
    target_dir = os.path.abspath(getattr(args, "dir", "."))
    plano_path = os.path.join(target_dir, "PLANO-EXECUCAO-ESTRUTURADO.json")

    if not os.path.exists(plano_path):
        print(f"[ERRO] Manifesto '{plano_path}' não encontrado. Execute 'plan' primeiro.")
        sys.exit(1)

    with open(plano_path, "r", encoding="utf-8") as f:
        plano = json.load(f)

    suite_name = plano.get("projeto", {}).get("nome", "Enterprise Suite")
    modulos = plano.get("projeto", {}).get("modulos", ["crm", "erp"])

    print("=" * 80)
    print(f"🚀 [FASE 2 - PROCESSAMENTO] Executando Plano Aprovado: '{suite_name}'")
    print("=" * 80)

    try:
        from compose_suite import compose_suite
    except ImportError:
        from scripts.compose_suite import compose_suite

    compose_suite(target_dir, suite_name, modulos)


def parse_natural_language_intent(prompt: str, base_dir: str = "."):
    """Ponto de entrada por Linguagem Natural — Gera o Plano / SPEC (Fase 1.5)."""
    cmd_plan(prompt, base_dir=base_dir, auto_apply=False)