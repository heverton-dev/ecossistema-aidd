import re

with open('scripts/compose_suite.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add generate_documentation_html function before compose_suite
func_code = """
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
        spotlight_commands.append(f"{{ id: 'cap-{cap_num}', cat: 'Capítulos do Guia', title: 'Capítulo {cap_num}: {pascal}', desc: 'Documentação do módulo {pascal}', iconType: 'chapter', action: () => {{ window.location.hash = \\'#cap{cap_num}\\'; }} }}")
        
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

    sidebar_str = "\\n            ".join(sidebar_links)
    module_docs_str = "\\n".join(module_docs)
    spotlight_str = "[\\n            " + ",\\n            ".join(spotlight_commands) + "\\n        ]"
    
    return html_template.replace("__SIDEBAR_LINKS__", sidebar_str).replace("__MODULE_DOCS__", module_docs_str).replace("__SPOTLIGHT_COMMANDS__", spotlight_str)

def compose_suite"""

content = content.replace("def compose_suite", func_code)

# Modify the docs generation block
old_block = """    # Copiar docs.html estático se existir
    if os.path.isfile(os.path.join(templates_v2, "docs.html")):
        shutil.copyfile(os.path.join(templates_v2, "docs.html"), os.path.join(static_dir, "docs.html"))"""

new_block = """    # Gerar docs.html dinâmico via AST
    docs_template_path = os.path.join(templates_v2, "docs.html")
    if os.path.isfile(docs_template_path):
        with open(docs_template_path, "r", encoding="utf-8") as tmpf:
            raw_docs_html = tmpf.read()
        final_docs_html = generate_documentation_html(suite_name, clean_modules, src_dir, raw_docs_html)
        with open(os.path.join(static_dir, "docs.html"), "w", encoding="utf-8") as outf:
            outf.write(final_docs_html)
        print("  [+] Front-end Docs 'src/static/docs.html' gerado dinamicamente via AST!")"""

content = content.replace(old_block, new_block)

with open('scripts/compose_suite.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("scripts/compose_suite.py atualizado para ler AST.")
