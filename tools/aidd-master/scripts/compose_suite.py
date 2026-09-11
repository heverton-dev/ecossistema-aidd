#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — Cross-Project Enterprise Suite Composition Engine
=============================================================================
Compõe suítes empresariais e monólitos modulares completos com:
- Shared Kernel (Database SQLite WAL, EventBus, RouteRegistry, WebhookDispatcher, SecurityService, MCPServer)
- Fatias Verticais completas (models, services, routes, UI components, testes unitários)
- Servidor Monolítico Modular dinâmico (server.py)
- Swagger Studio OpenAPI 3.1 & Webhook Configuration Studio & MCP Native Portal
- Bateria completa de Gates Determinísticos Anti-Fail
- Manifesto estruturado PLANO-EXECUCAO-ESTRUTURADO.json e requirements.txt
"""

import os
import sys
import shutil
import json
import uuid
import datetime
import tempfile

from cookiecutter.main import cookiecutter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Importa o gerador de fatias verticais
try:
    from add_module import criar_modulo, slugify, pascal_case
except ImportError:
    from scripts.add_module import criar_modulo, slugify, pascal_case

SUITE_TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "templates", "cookiecutter-scaffold", "suite"
)

WEBHOOK_DEMO_URL = "https://webhook.site/demo-aidd-master"


def _render_suite_template(extra_context: dict) -> str:
    """Renderiza o template Cookiecutter/Jinja2 da suíte (server.py +
    static/index.html) em um diretório temporário e devolve o conteúdo já
    renderizado de cada arquivo, pronto para os callers gravarem onde
    quiserem."""
    with tempfile.TemporaryDirectory() as tmp_out:
        cookiecutter(
            SUITE_TEMPLATE_DIR,
            no_input=True,
            extra_context=extra_context,
            output_dir=tmp_out,
            overwrite_if_exists=True,
        )
        gerado_dir = os.path.join(tmp_out, "suite_gerada")
        with open(os.path.join(gerado_dir, "server.py.j2"), "r", encoding="utf-8") as f:
            server_code = f.read()
        with open(os.path.join(gerado_dir, "index.html.j2"), "r", encoding="utf-8") as f:
            index_html = f.read()
        return server_code, index_html


def generate_modular_server_code(suite_name: str, module_slugs: list, db_engine: str = "sqlite") -> str:
    """Gera o código-fonte do servidor dinâmico server.py que carrega todos os módulos."""
    imports_lines = []
    init_schema_calls = []
    rls_init_calls = []
    service_inits = []
    routes_regs = []
    mcp_tool_regs = []
    webhook_event_regs = []

    for mod in module_slugs:
        slug = slugify(mod)
        pascal = pascal_case(mod)
        imports_lines.append(f"from modules.{slug}.models import init_schema as init_{slug}_schema")
        imports_lines.append(f"from modules.{slug}.services import {pascal}Service")
        imports_lines.append(f"from modules.{slug}.routes import registrar_rotas as reg_{slug}_routes")

        init_schema_calls.append(f"    init_{slug}_schema(conn)")
        rls_init_calls.append(f"    enable_rls_tenant(conn, '{slug}')")
        service_inits.append(f"service_{slug} = {pascal}Service(db, events)")
        # NOTA: RouteRegistry agora é um Singleton (ver templates/v2/openapi.py) —
        # o registry local de cada módulo já É o mesmo objeto do servidor, então
        # nenhuma mesclagem explícita (include_registry) é necessária ou segura
        # aqui (mesclar um registry singleton nele mesmo causaria loop infinito
        # em RouteRegistry.mount() ao iterar e appendar em self.endpoints).
        routes_regs.append(f"reg_{slug}_routes(service_{slug})")
        mcp_tool_regs.append(f"mcp_server.register_module_tools('{slug}', '{pascal}')")
        webhook_event_regs.append(f"webhook_dispatcher.register_module_events('{slug}', '{pascal}')")

    imports_str = "\n".join(imports_lines)
    init_schemas_str = "\n".join(init_schema_calls)
    rls_init_str = "\n".join(rls_init_calls)
    service_inits_str = "\n".join(service_inits)
    routes_regs_str = "\n".join(routes_regs)
    mcp_tool_regs_str = "\n".join(mcp_tool_regs)
    webhook_event_regs_str = "\n".join(webhook_event_regs)

    if db_engine == "postgres":
        db_init_str = (
            "DATABASE_URL_EXEMPLO = \"postgresql://aidd_user:CHANGE_ME@localhost:5432/aidd_suite\"\n"
            "# MCPServer permanece baseado em SQLite por design proprio (introspeccao via arquivo local),\n"
            "# independente do motor escolhido para a Database principal.\n"
            "DB_PATH = os.path.join(CURRENT_DIR, \"..\", \"mcp_introspection.db\")"
        )
        db_url_expr_str = "os.environ.get(\"DATABASE_URL\", DATABASE_URL_EXEMPLO)"
    else:
        db_init_str = "DB_PATH = os.path.join(CURRENT_DIR, \"..\", \"suite.db\")"
        db_url_expr_str = "f\"sqlite:///{DB_PATH}\""

    server_code, _ = _render_suite_template({
        "suite_name": suite_name,
        "webhook_demo_url": WEBHOOK_DEMO_URL,
        "db_init": db_init_str,
        "db_url_expr": db_url_expr_str,
        "imports": imports_str,
        "init_schemas": init_schemas_str,
        "rls_init": rls_init_str,
        "service_inits": service_inits_str,
        "routes_regs": routes_regs_str,
        "mcp_tool_regs": mcp_tool_regs_str,
        "webhook_event_regs": webhook_event_regs_str,
    })
    return server_code



def generate_superapp_index_html(suite_name: str, module_slugs: list) -> str:
    """Gera front-end Super-App Impeccable com CSS 100% embutido (offline-first)."""
    tabs_nav = []
    sections = []
    scripts = []
    spotlight_items = []

    for i, mod in enumerate(module_slugs):
        slug = slugify(mod)
        pascal = pascal_case(mod)
        is_active = (i == 0)
        active_tab_class = "tab-btn active" if is_active else "tab-btn"
        active_sec_class = "tab-section active" if is_active else "tab-section"
        
        spotlight_items.append(f"""            {{ titulo: 'Novo Registro em {pascal}', subtitulo: 'Cadastrar nova entrada no módulo {pascal}', acao: () => {{ mudarAba('{slug}'); abrirModalNovo('{slug}'); }}, atalho: 'N' }},
            {{ titulo: 'Recarregar Dados de {pascal}', subtitulo: 'Atualiza métricas e listagem da tabela {pascal}', acao: () => {{ mudarAba('{slug}'); carregar{pascal}(); }}, atalho: 'R' }},""")

        tabs_nav.append(f'''
            <button type="button" onclick="mudarAba('{slug}')" id="tab-btn-{slug}" class="{active_tab_class}" aria-label="Acessar módulo {pascal}">
                <span class="tab-indicator"></span>
                <span>{pascal}</span>
            </button>''')

        sections.append(f'''
        <!-- ABA {pascal} -->
        <section id="sec-{slug}" class="{active_sec_class}">
            <!-- CARDS DE KPIS DO MÓDULO -->
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-header">
                        <span class="kpi-title">Total de Registros</span>
                        <span class="kpi-icon sky">
                            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
                        </span>
                    </div>
                    <div class="kpi-val" id="kpi-{slug}-total">--</div>
                    <div class="kpi-sub">Cadastros em {pascal}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-header">
                        <span class="kpi-title">Registros Ativos</span>
                        <span class="kpi-icon emerald">
                            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        </span>
                    </div>
                    <div class="kpi-val" id="kpi-{slug}-ativos">--</div>
                    <div class="kpi-sub">Operando normalmente</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-header">
                        <span class="kpi-title">Concluídos / Arquivados</span>
                        <span class="kpi-icon indigo">
                            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                        </span>
                    </div>
                    <div class="kpi-val" id="kpi-{slug}-concluidos">--</div>
                    <div class="kpi-sub">Finalizados no período</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-header">
                        <span class="kpi-title">Taxa de Conclusão</span>
                        <span class="kpi-icon amber">
                            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>
                        </span>
                    </div>
                    <div class="kpi-val" id="kpi-{slug}-taxa">--%</div>
                    <div class="kpi-sub">Eficiência operacional</div>
                </div>
            </div>

            <!-- TABELA DE DADOS & OPERAÇÕES -->
            <div class="panel">
                <div class="panel-header">
                    <div>
                        <h2 class="panel-title">
                            <span class="dot-sky"></span>
                            Gestão de {pascal}
                        </h2>
                        <p class="panel-desc">Operações, listagem e ciclo de vida da fatia vertical {pascal}</p>
                    </div>
                    <div class="panel-actions">
                        <div class="search-box">
                            <input type="text" id="busca-{slug}" placeholder="Buscar em {pascal}..." onkeyup="filtrar{pascal}()" class="input-search">
                        </div>
                        <button type="button" onclick="carregar{pascal}()" class="btn btn-secondary" title="Recarregar" aria-label="Recarregar dados">
                            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                        </button>
                        <button type="button" onclick="abrirModalNovo('{slug}')" class="btn btn-primary" aria-label="Criar novo {pascal}">
                            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                            <span>Novo {pascal}</span>
                        </button>
                    </div>
                </div>

                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th style="width: 70px;">ID</th>
                                <th>Título</th>
                                <th style="width: 120px;">Status</th>
                                <th style="width: 170px;">Criado em</th>
                                <th style="width: 150px; text-align: right;">Ações</th>
                            </tr>
                        </thead>
                        <tbody id="tabela-{slug}-corpo">
                            <tr><td colspan="5" class="table-empty">Carregando dados do módulo {pascal}...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </section>''')

        scripts.append(f'''
        let dados{pascal}Cache = [];

        async function carregar{pascal}() {{
            try {{
                // 1. Carregar Métricas
                try {{
                    const mRes = await fetch('/api/{slug}/metricas');
                    if (mRes.ok) {{
                        const m = await mRes.json();
                        document.getElementById('kpi-{slug}-total').textContent = m.total ?? 0;
                        document.getElementById('kpi-{slug}-ativos').textContent = m.ativos ?? 0;
                        document.getElementById('kpi-{slug}-concluidos').textContent = m.concluidos ?? 0;
                        document.getElementById('kpi-{slug}-taxa').textContent = (m.taxa_conclusao ?? 0) + '%';
                    }}
                }} catch (e) {{ console.warn('Erro metricas {slug}:', e); }}

                // 2. Carregar Registros
                const res = await fetch('/api/{slug}');
                dados{pascal}Cache = await res.json();
                window.dados{pascal}Cache = dados{pascal}Cache;
                renderizarTabela{pascal}(dados{pascal}Cache);
            }} catch (e) {{
                console.error('Erro ao carregar {slug}:', e);
                mostrarToast('Falha ao carregar registros de {pascal}', 'erro');
            }}
        }}

        function renderizarTabela{pascal}(lista) {{
            const tbody = document.getElementById('tabela-{slug}-corpo');
            if (!lista || lista.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="5" class="table-empty">Nenhum registro ativo localizado.</td></tr>';
                return;
            }}
            tbody.innerHTML = lista.map(item => `
                <tr>
                    <td class="col-id">#${{item.id}}</td>
                    <td class="col-title">
                        <div class="item-title">${{escapeHtml(item.titulo)}}</div>
                        ${{item.descricao ? `<div class="item-desc">${{escapeHtml(item.descricao)}}</div>` : ''}}
                    </td>
                    <td><span class="badge badge-status">${{escapeHtml(item.status || 'ativo')}}</span></td>
                    <td class="col-date">${{escapeHtml(item.criado_em || '--')}}</td>
                    <td class="col-actions" style="text-align: right; white-space: nowrap;">
                        <button type="button" onclick="abrirModalEditar('{slug}', ${{item.id}})" class="btn btn-secondary" style="padding: 4px 8px; font-size: 11px; margin-right: 4px;" title="Editar registro" aria-label="Editar registro">Editar</button>
                        <button type="button" onclick="deletarItem('{slug}', ${{item.id}})" class="btn btn-delete" title="Excluir" aria-label="Excluir registro">Excluir</button>
                    </td>
                </tr>
            `).join('');
        }}

        function filtrar{pascal}() {{
            const termo = (document.getElementById('busca-{slug}').value || '').toLowerCase();
            if (!termo) {{
                renderizarTabela{pascal}(dados{pascal}Cache);
                return;
            }}
            const filtrados = dados{pascal}Cache.filter(i => 
                (i.titulo && i.titulo.toLowerCase().includes(termo)) ||
                (i.descricao && i.descricao.toLowerCase().includes(termo))
            );
            renderizarTabela{pascal}(filtrados);
        }}''')

    tabs_nav_str = "\n".join(tabs_nav)
    sections_str = "\n".join(sections)
    scripts_str = "\n".join(scripts)
    spotlight_modules_str = "\n".join(spotlight_items)
    initial_loads = "\n".join([f"            carregar{pascal_case(m)}();" for m in module_slugs])

    _, index_html = _render_suite_template({
        "suite_name": suite_name,
        "tabs_nav": tabs_nav_str,
        "sections": sections_str,
        "scripts": scripts_str,
        "spotlight_modules": spotlight_modules_str,
        "initial_loads": initial_loads,
    })
    return index_html



def generate_documentation_html(suite_name: str, module_slugs: list, src_dir: str, html_template: str) -> str:
    import ast
    sidebar_links = []
    module_docs = []
    spotlight_commands = []
    
    spotlight_commands.extend([
        "{ id: 'nav-app', cat: 'Navegação', title: 'Super-App Clínico (Home)', desc: 'Dashboard', iconType: 'app', action: () => { window.location.href = '/'; } }",
        "{ id: 'nav-docs', cat: 'Navegação', title: 'Swagger Studio', desc: 'API Docs', iconType: 'docs', action: () => { window.location.href = '/docs'; } }"
    ])

    for i, mod in enumerate(module_slugs):
        cap_num = i + 1
        pascal = mod.title().replace('_', '')
        
        sidebar_links.append(f'<a href="#cap{cap_num}" class="block px-3 py-2 rounded-lg text-slate-300 hover:bg-slate-800/80 hover:text-white transition">{cap_num}. Módulo {pascal}</a>')
        spotlight_commands.append(f"{{ id: 'cap-{cap_num}', cat: 'Capítulos do Guia', title: 'Capítulo {cap_num}: {pascal}', desc: 'Documentação do módulo {pascal}', iconType: 'chapter', action: () => {{ window.location.hash = \'#cap{cap_num}\'; }} }}")
        
        mod_dir = os.path.join(src_dir, "modules", mod)
        models_file = os.path.join(mod_dir, "models.py")
        routes_file = os.path.join(mod_dir, "routes.py")
        
        models_info = []
        routes_info = []
        
        try:
            if os.path.isfile(models_file):
                with open(models_file, "r", encoding="utf-8") as mf:
                    tree = ast.parse(mf.read())
                    for node in tree.body:
                        if isinstance(node, ast.ClassDef):
                            models_info.append(node.name)
        except Exception: pass
        
        try:
            if os.path.isfile(routes_file):
                with open(routes_file, "r", encoding="utf-8") as rf:
                    tree = ast.parse(rf.read())
                    for node in tree.body:
                        if isinstance(node, ast.FunctionDef):
                            routes_info.append(node.name)
        except Exception: pass
        
        m_str = ", ".join(models_info) if models_info else "Nenhum modelo encontrado."
        r_str = ", ".join(routes_info) if routes_info else "Nenhuma rota encontrada."
        
        doc_section = f'''
            <!-- CAPÍTULO {cap_num} -->
            <section id="cap{cap_num}" class="doc-section space-y-4">
                <div class="border-b border-slate-800 pb-2">
                    <span class="text-xs font-mono text-sky-400 uppercase tracking-wider font-bold">Capítulo {cap_num}</span>
                    <h2 class="text-2xl font-bold text-slate-100">Módulo: {pascal}</h2>
                </div>
                <p>Módulo gerado automaticamente via AST. Sem mocks ou dados legados.</p>
                <div class="grid grid-cols-2 gap-3 pt-2">
                    <div class="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                        <div class="text-sky-400 font-bold text-base mb-1">Modelos Detectados</div>
                        <div class="text-xs text-slate-400">{m_str}</div>
                    </div>
                    <div class="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                        <div class="text-emerald-400 font-bold text-base mb-1">Rotas Detectadas</div>
                        <div class="text-xs text-slate-400">{r_str}</div>
                    </div>
                </div>
            </section>
        '''
        module_docs.append(doc_section)

    sidebar_str = "\n            ".join(sidebar_links)
    module_docs_str = "\n".join(module_docs)
    spotlight_str = "[\n            " + ",\n            ".join(spotlight_commands) + "\n        ]"

    # Renderiza via Jinja2 (mesma stack do Cookiecutter) em vez de .replace()
    # manual — o "molde" estático (docs.html) já é um arquivo de template em
    # disco; só o mecanismo de substituição muda.
    from jinja2 import Template
    return Template(html_template).render(
        sidebar_links=sidebar_str,
        module_docs=module_docs_str,
        spotlight_commands=spotlight_str,
    )

def _setup_directories(target_dir: str) -> dict[str, str]:
    """Cria e inicializa a estrutura de diretórios e pacotes da suíte."""
    src_dir = os.path.join(target_dir, "src")
    core_dir = os.path.join(src_dir, "core")
    shared_ui_dir = os.path.join(src_dir, "shared", "ui")
    shared_utils_dir = os.path.join(src_dir, "shared", "utils")
    modules_dir = os.path.join(src_dir, "modules")
    static_dir = os.path.join(src_dir, "static")
    static_comp_dir = os.path.join(static_dir, "components")
    tests_unit_dir = os.path.join(target_dir, "tests", "unit")
    target_gates_dir = os.path.join(target_dir, "scripts", "gates")
    target_scripts_dir = os.path.join(target_dir, "scripts")

    for d in (core_dir, shared_ui_dir, shared_utils_dir, modules_dir, static_comp_dir, tests_unit_dir, target_gates_dir, target_scripts_dir):
        os.makedirs(d, exist_ok=True)

    for init_path in (
        os.path.join(src_dir, "__init__.py"),
        os.path.join(core_dir, "__init__.py"),
        os.path.join(modules_dir, "__init__.py"),
        os.path.join(src_dir, "shared", "__init__.py"),
        os.path.join(shared_ui_dir, "__init__.py"),
        os.path.join(shared_utils_dir, "__init__.py"),
    ):
        open(init_path, "w", encoding="utf-8").close()

    return {
        "src": src_dir,
        "core": core_dir,
        "shared_ui": shared_ui_dir,
        "shared_utils": shared_utils_dir,
        "modules": modules_dir,
        "static": static_dir,
        "tests_unit": tests_unit_dir,
        "gates": target_gates_dir,
        "scripts": target_scripts_dir,
    }


def _copy_shared_kernel(templates_v2: str, core_dir: str, shared_ui_dir: str, shared_utils_dir: str) -> None:
    """Copia componentes do kernel compartilhado e utilitários transversais."""
    core_files = [
        "database.py", "events.py", "outbox_worker.py", "openapi.py", "security.py",
        "webhooks.py", "mcp_server.py", "mcp_repository.py", "result.py", "jobs.py",
        "metrics.py", "cqrs.py", "saga.py", "circuit_breaker.py", "token_revocation.py",
        "local_first.py", "logs.py",
    ]
    for cf in core_files:
        src = os.path.join(templates_v2, cf)
        dst = os.path.join(core_dir, cf)
        if os.path.isfile(src):
            shutil.copyfile(src, dst)
            print(f"  [+] Core Kernel: {cf}")

    # Assets HTML dos Studios referenciados pelo core: webhook_studio.html é
    # lido por core/webhooks.py (get_studio_html) e mcp_studio.html por
    # core/mcp_server.py (get_studio_html). Sem eles, o check comportamental
    # de XSS do G_SEGURANCA e a rota /webhooks do server.py gerado quebram.
    for asset in ("webhook_studio.html", "mcp_studio.html"):
        src = os.path.join(templates_v2, asset)
        dst = os.path.join(core_dir, asset)
        if os.path.isfile(src):
            shutil.copyfile(src, dst)
            print(f"  [+] Core Kernel: {asset}")

    # Copiar Shared UI
    shared_ui_src = os.path.join(templates_v2, "shared", "ui")
    if os.path.isdir(shared_ui_src):
        for f in os.listdir(shared_ui_src):
            src = os.path.join(shared_ui_src, f)
            if os.path.isfile(src):
                shutil.copyfile(src, os.path.join(shared_ui_dir, f))
                print(f"  [+] Shared UI: {f}")

    # Copiar Shared Utils
    shared_utils_src = os.path.join(templates_v2, "shared", "utils")
    if os.path.isdir(shared_utils_src):
        for f in os.listdir(shared_utils_src):
            src = os.path.join(shared_utils_src, f)
            if os.path.isfile(src):
                shutil.copyfile(src, os.path.join(shared_utils_dir, f))
                print(f"  [+] Shared Utils: {f}")


def _generate_structured_plan(suite_name: str, db_engine: str, target_dir: str) -> None:
    """Gerar Manifesto Estruturado PLANO-EXECUCAO-ESTRUTURADO.json."""
    plano_dict = {
        "projeto": {
            "nome": suite_name,
            "slug": slugify(suite_name),
            "versao": "4.1.0",
            "framework": "AIDD Master Enterprise",
            "status": "em_desenvolvimento",
            "criado_em": datetime.datetime.now().isoformat(),
            "db_engine": db_engine,
        },
        "arquitetura": {
            "padrao": "Monólito Modular com Clean Architecture",
            "comunicacao": "EventBus Pub/Sub Assíncrono",
            "documentacao": "OpenAPI 3.1 & Swagger Studio Nativo (/docs)",
            "webhooks": "Webhook Configuration Studio com Assinatura HMAC SHA-256 (/webhooks)",
            "mcp": "Model Context Protocol Native Server (/mcp & JSON-RPC 2.0)",
            "persistencia": "SQLite Concorrente WAL Mode (Write-Ahead Logging)",
            "design_system": "Impeccable Super-App UI com 4px scrollbar e Single-Line Header",
        },
        "modulos": [],
        "gates_qualidade": [
            {"gate": "G_ESTRUTURA", "descricao": "Validação de layout modular, manifestos e Clean Architecture"},
            {"gate": "G_QUALIDADE", "descricao": "Análise estática de sintaxe e eliminação de stubs vazios"},
            {"gate": "G_TESTES", "descricao": "Execução obrigatória de 100% dos testes unitários com pytest"},
            {"gate": "G_CONTRACTS", "descricao": "Validação de esquemas OpenAPI 3.1 e contratos MCP"},
            {"gate": "G_SEGREDOS", "descricao": "Varredura de entropia de Shannon contra vazamento de chaves"},
            {"gate": "G_HARNESS_COMPAT", "descricao": "Conformidade multi-harness (Antigravity, Cline, OpenHands, Cursor)"},
            {"gate": "G_CHAOS", "descricao": "Simulação de Quedas (Chaos) e resiliência do sistema"},
        ],
    }

    with open(os.path.join(target_dir, "PLANO-EXECUCAO-ESTRUTURADO.json"), "w", encoding="utf-8") as f:
        json.dump(plano_dict, f, ensure_ascii=False, indent=2)


def _generate_modules(modules: list, target_dir: str) -> list[str]:
    """Gerar Fatias Verticais para cada Módulo."""
    clean_modules = [slugify(m) for m in modules if m.strip()]
    for mod in clean_modules:
        criar_modulo(mod, target_dir=target_dir)
    return clean_modules


def _generate_server_and_ui(
    suite_name: str, clean_modules: list[str], db_engine: str,
    src_dir: str, static_dir: str, templates_v2: str
) -> None:
    """Gerar Servidor Monolítico Modular src/server.py e Front-ends."""
    server_code = generate_modular_server_code(suite_name, clean_modules, db_engine=db_engine)
    with open(os.path.join(src_dir, "server.py"), "w", encoding="utf-8") as f:
        f.write(server_code)
    print("  [+] Servidor dinâmico 'src/server.py' gerado com sucesso!")

    index_html = generate_superapp_index_html(suite_name, clean_modules)
    with open(os.path.join(static_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    print("  [+] Front-end Super-App 'src/static/index.html' gerado!")

    docs_template_path = os.path.join(templates_v2, "docs.html")
    if os.path.isfile(docs_template_path):
        with open(docs_template_path, "r", encoding="utf-8") as tmpf:
            raw_docs_html = tmpf.read()
        final_docs_html = generate_documentation_html(suite_name, clean_modules, src_dir, raw_docs_html)
        with open(os.path.join(static_dir, "docs.html"), "w", encoding="utf-8") as outf:
            outf.write(final_docs_html)
        print("  [+] Front-end Docs 'src/static/docs.html' gerado dinamicamente via AST!")

    output_css_src = os.path.join(templates_v2, "output.css")
    if os.path.isfile(output_css_src):
        shutil.copyfile(output_css_src, os.path.join(static_dir, "output.css"))
        print("  [+] Tailwind CSS estático: src/static/output.css")


def _generate_manifests(target_dir: str, db_engine: str) -> None:
    """Gerar requirements.txt e config do mutmut."""
    # pyjwt/cryptography sao incondicionais: o server.py gerado sempre registra
    # as rotas de SSO Corporativo (OAuth2/OIDC + PKCE) que chamam
    # OIDCService.validate_id_token (core/security.py), e esse metodo depende
    # de PyJWT + cryptography (RS256/JWKS) em qualquer produto composto aqui.
    req_content = (
        "pytest>=7.4.0\nmutmut>=2.4.0\nrequests>=2.31.0\n"
        "pyjwt>=2.8.0\ncryptography>=42.0.0\nsecure>=2.0.0\n"
        "sqlalchemy>=2.0.0\naiosqlite>=0.20.0\nmcp>=1.28.0\n"
    )
    if db_engine == "postgres":
        req_content += "psycopg2-binary>=2.9.9\n"
    with open(os.path.join(target_dir, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write(req_content)
    with open(os.path.join(target_dir, "setup.cfg"), "w", encoding="utf-8") as f:
        f.write("[mutmut]\npaths_to_mutate=src/\nbackup=False\nrunner=pytest\ntests_dir=tests/\n")
    print("  [+] Manifesto 'requirements.txt' e 'setup.cfg' gerados!")


def _copy_gates_and_automation(
    skill_root: str, templates_v2: str, gates_dir: str, scripts_dir: str,
    target_dir: str, core_dir: str, target_gates_dir: str, target_scripts_dir: str
) -> None:
    """Copiar Quality Gates, Fuzzing, scripts e templates Cookiecutter/Jinja2."""
    if os.path.isdir(gates_dir):
        for g in os.listdir(gates_dir):
            if g.endswith(".py"):
                shutil.copyfile(os.path.join(gates_dir, g), os.path.join(target_gates_dir, g))
                print(f"  [+] Quality Gate: {g}")

    fuzzing_src = os.path.join(templates_v2, "..", "..", "src", "core", "fuzzing.py")
    if os.path.isfile(fuzzing_src):
        shutil.copyfile(fuzzing_src, os.path.join(core_dir, "fuzzing.py"))
        print(f"  [+] Fuzzing Contínuo: fuzzing.py")

    for s in ["aidd.py", "add_module.py", "compose_suite.py", "openapi_to_ts.py", "scaffold_infra.py"]:
        src = os.path.join(scripts_dir, s)
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(target_scripts_dir, s))
            print(f"  [+] Script: {s}")

    cookiecutter_templates_src = os.path.join(skill_root, "templates", "cookiecutter-scaffold")
    cookiecutter_templates_dst = os.path.join(target_dir, "templates", "cookiecutter-scaffold")
    if os.path.isdir(cookiecutter_templates_src):
        if os.path.isdir(cookiecutter_templates_dst):
            shutil.rmtree(cookiecutter_templates_dst)
        shutil.copytree(cookiecutter_templates_src, cookiecutter_templates_dst)
        print("  [+] Templates Cookiecutter/Jinja2 copiados (scaffolding de módulos)")


def _copy_governance_and_rules(
    suite_name: str, clean_modules: list[str], templates_v2: str, target_dir: str
) -> None:
    """Copiar arquivos de produção, Nginx e regras multi-IDE."""
    for prod_f in ["Dockerfile", "docker-compose.yml", "deploy.sh", "AGENTS.md", "CLAUDE.md", "GEMINI.md"]:
        src = os.path.join(templates_v2, prod_f)
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(target_dir, prod_f))
            print(f"  [+] Governança & Deploy: {prod_f}")

    nginx_src = os.path.join(templates_v2, "nginx")
    nginx_dst = os.path.join(target_dir, "nginx")
    if os.path.isdir(nginx_src):
        os.makedirs(nginx_dst, exist_ok=True)
        for root, _, files in os.walk(nginx_src):
            rel = os.path.relpath(root, nginx_src)
            d_dir = os.path.join(nginx_dst, rel) if rel != "." else nginx_dst
            os.makedirs(d_dir, exist_ok=True)
            for f in files:
                shutil.copyfile(os.path.join(root, f), os.path.join(d_dir, f))
        print("  [+] Nginx Shield & Configurações copiadas!")

    cursor_rules_dir = os.path.join(target_dir, ".cursor", "rules")
    claude_dir = os.path.join(target_dir, ".claude")
    agent_rules_dir = os.path.join(target_dir, ".agent", "rules")
    os.makedirs(cursor_rules_dir, exist_ok=True)
    os.makedirs(claude_dir, exist_ok=True)
    os.makedirs(agent_rules_dir, exist_ok=True)

    rules_content = f"""# Governança Anti-Falha e Regras de Ouro — {suite_name}

1. **Zero Acoplamento:** Módulos em `src/modules/` comunicam-se exclusivamente via `EventBus` pub/sub. Proibido import direto entre módulos irmãos.
2. **Clean Architecture:** Toda fatia possui `models.py`, `services.py`, `routes.py`, UI isolada e testes unitários.
3. **Persistência Segura:** SQLite WAL com `busy_timeout=5000` e parametrização de queries (`?`).
4. **Impeccable UI:** SVGs Lucide, modais customizados, toasts assíncronos e conformidade WCAG 2.1.
5. **Quality Gates:** Homologação obrigatória (exit 0) em todos os 7 gates mecânicos (`python scripts/aidd.py audit --report`).
"""
    with open(os.path.join(cursor_rules_dir, "aidd_rules.mdc"), "w", encoding="utf-8") as f:
        f.write(rules_content)
    with open(os.path.join(claude_dir, "CLAUDE.md"), "w", encoding="utf-8") as f:
        f.write(rules_content)
    with open(os.path.join(agent_rules_dir, "rules.md"), "w", encoding="utf-8") as f:
        f.write(rules_content)
    print("  [+] Multi-IDE Rules (.cursor, .claude, .agent) sincronizadas!")

    contexto_md = f"""# Grafo de Contexto e Memória do Projeto: {suite_name}

## 1. Visão Geral
- **Nome:** {suite_name}
- **Framework:** AIDD Master Enterprise
- **Banco de Dados:** SQLite Concorrente WAL (`suite.db`)
- **Portais Ativos:** `/` (Super-App), `/docs` (Swagger Studio), `/mcp` (MCP Server), `/webhooks` (Webhook Studio)

## 2. Fatias Verticais Ativas ({len(clean_modules)})
"""
    for m in clean_modules:
        contexto_md += f"- **Módulo `{m}`**: `src/modules/{m}/` (CRUD, OpenAPI, MCP e testes em `tests/unit/test_{m}.py`)\n"

    contexto_md += """
## 3. Kernel Compartilhado (Shared Kernel)
- `database.py`: Conexão SQLite WAL com busy_timeout e controle de migrações.
- `events.py`: EventBus pub/sub desacoplado com envelope e tracing UUID.
- `result.py`: Monad Result Pattern (`Result.ok()`, `Result.fail()`).
- `jobs.py`: Fila de tarefas em background (`JobQueue`).
- `security.py` & `openapi.py`: Criptografia JWT HS256, RBAC e OpenAPI 3.1.
"""
    with open(os.path.join(target_dir, "CONTEXTO-PROJETO.md"), "w", encoding="utf-8") as f:
        f.write(contexto_md)
    print("  [+] Grafo de Memória 'CONTEXTO-PROJETO.md' gerado!")


def compose_suite(target_dir: str, suite_name: str, modules: list, db_engine: str = "sqlite"):
    """Motor principal de composição cross-project."""
    target_dir = os.path.abspath(target_dir)
    db_engine = (db_engine or "sqlite").lower()
    print("=" * 80)
    print(f"🚀 [AIDD v5.0 Enterprise] Composição de Suíte Modular Cross-Project: {suite_name}")
    print(f"📁 Diretório de Destino: {target_dir}")
    print(f"📦 Fatias Verticais:     {', '.join(modules)}")
    print(f"🗄️  Motor de Persistência: {db_engine}")
    print("=" * 80)

    skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_core = os.path.join(skill_root, "templates", "core")
    templates_v2 = templates_core if os.path.isdir(templates_core) else os.path.join(skill_root, "templates", "v2")
    gates_dir = os.path.join(skill_root, "templates", "gates")
    scripts_dir = os.path.join(skill_root, "scripts")

    dirs = _setup_directories(target_dir)
    _copy_shared_kernel(templates_v2, dirs["core"], dirs["shared_ui"], dirs["shared_utils"])
    _generate_structured_plan(suite_name, db_engine, target_dir)
    clean_modules = _generate_modules(modules, target_dir)
    _generate_server_and_ui(suite_name, clean_modules, db_engine, dirs["src"], dirs["static"], templates_v2)
    _generate_manifests(target_dir, db_engine)
    _copy_gates_and_automation(
        skill_root, templates_v2, gates_dir, scripts_dir,
        target_dir, dirs["core"], dirs["gates"], dirs["scripts"]
    )
    _copy_governance_and_rules(suite_name, clean_modules, templates_v2, target_dir)

    print("\n" + "=" * 80)
    print(f"🏆 [SUCESSO]: Suíte Enterprise '{suite_name}' 100% Composta!")
    print(f"   ➔ Iniciar Servidor: cd {target_dir} && python src/server.py")
    print(f"   ➔ Auditar Qualidade: cd {target_dir} && python scripts/aidd.py audit --report")
    print(f"   ➔ Executar Testes:   cd {target_dir} && python scripts/aidd.py test")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python compose_suite.py <target_dir> <suite_name> [modulo1] [modulo2] ...")
        sys.exit(1)

    target = sys.argv[1]
    name = sys.argv[2]
    mods = sys.argv[3:] if len(sys.argv) > 3 else ["crm", "erp", "helpdesk", "logistica"]
    compose_suite(target, name, mods)
