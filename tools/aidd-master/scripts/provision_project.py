import os, sys, shutil, subprocess, json, re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s_-]+', '-', text)[:40]


def _renderizar_e_escrever_docs_html(templates_dir, static_dir, suite_name, module_slugs, src_dir):
    """Le o MOLDE docs.html (Jinja2, placeholders tipo {{ spotlight_commands }})
    e escreve em static_dir a versao renderizada de verdade -- nunca uma copia
    crua do molde. Achado real (Playwright contra a pagina renderizada, nao so
    leitura de codigo): um shutil.copyfile() direto do molde deixava
    `{{ spotlight_commands }}` literal no HTML, JS invalido no navegador
    (SyntaxError: Unexpected token '{'), pagina inteira quebrada. Precisa
    rodar DEPOIS que os modulos ja existem em disco (generate_documentation_html
    faz parsing AST de src/modules/<slug>/{models,routes}.py para o conteudo).
    """
    docs_template_path = os.path.join(templates_dir, 'docs.html')
    if not os.path.exists(docs_template_path):
        return
    with open(docs_template_path, 'r', encoding='utf-8') as f:
        raw_docs_html = f.read()
    from compose_suite import generate_documentation_html
    final_docs_html = generate_documentation_html(suite_name, module_slugs, src_dir, raw_docs_html)
    os.makedirs(static_dir, exist_ok=True)
    with open(os.path.join(static_dir, 'docs.html'), 'w', encoding='utf-8') as f:
        f.write(final_docs_html)

def provision(project_desc, base_dir=None, frontend_stack='nextjs'):
    if os.path.isabs(project_desc) or os.sep in project_desc or (os.altsep and os.altsep in project_desc) or os.path.exists(project_desc):
        project_dir = os.path.abspath(project_desc)
        slug = slugify(os.path.basename(project_dir)) or "projeto-modular"
    else:
        words = project_desc.split()
        target_text = ' '.join(words[:3]) if len(words) >= 3 else project_desc
        slug = slugify(target_text)
        
        if not base_dir:
            base_dir = os.path.join(os.path.expanduser('~'), 'orca', 'workspaces', 'PROJETOS Criados com IA')

        # ISSUE-USA-0003: sem prefixo proj_ — layout achatado <raiz>/<slug>/...
        project_dir = os.path.join(base_dir, slug)
    
    print(f"🚀 [AIDD MASTER] Provisionando ecossistema modular: {slug}")
    print(f"📁 Destino: {project_dir}")
    
    # 1. Estrutura de Diretórios Modulares + Shared Kernel
    os.makedirs(os.path.join(project_dir, 'src', 'core'), exist_ok=True)
    os.makedirs(os.path.join(project_dir, 'src', 'shared', 'ui'), exist_ok=True)
    os.makedirs(os.path.join(project_dir, 'src', 'modules'), exist_ok=True)
    os.makedirs(os.path.join(project_dir, 'src', 'static', 'components'), exist_ok=True)
    os.makedirs(os.path.join(project_dir, 'tests', 'unit'), exist_ok=True)
    os.makedirs(os.path.join(project_dir, 'tests', 'load'), exist_ok=True)
    os.makedirs(os.path.join(project_dir, 'scripts', 'gates'), exist_ok=True)
    
    open(os.path.join(project_dir, 'src', '__init__.py'), 'w', encoding='utf-8').close()
    open(os.path.join(project_dir, 'src', 'core', '__init__.py'), 'w', encoding='utf-8').close()
    open(os.path.join(project_dir, 'src', 'modules', '__init__.py'), 'w', encoding='utf-8').close()
    open(os.path.join(project_dir, 'tests', '__init__.py'), 'w', encoding='utf-8').close()

    # 2. Localização Dinâmica de Templates (Zero Hardcoded Paths)
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_core = os.path.join(repo_root, 'templates', 'core')
    templates_dir = templates_core if os.path.isdir(templates_core) else os.path.join(repo_root, 'templates', 'v2')
    gates_dir = os.path.join(repo_root, 'templates', 'gates')

    if os.path.exists(templates_dir):
        from compose_suite import CORE_KERNEL_FILES
        for f in CORE_KERNEL_FILES + ['repositories.py', 'swagger.html', 'webhook_studio.html', 'mcp_studio.html']:
            src = os.path.join(templates_dir, f)
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(project_dir, 'src', 'core', f))
        
        # index.html NÃO é copiado daqui: templates/core/index.html é uma cópia
        # estática desatualizada (sem as variáveis CSS/modal que G_CONTRACTS
        # exige) — é gerado dinamicamente no passo 5.1 com o mesmo gerador que
        # compose_suite() usa (generate_superapp_index_html), sempre em dia.
        #
        # output.css: achado real (18/09/2026, print do usuário) — docs.html
        # (Swagger/Guia) referencia `<link rel="stylesheet" href="/static/
        # output.css">` para as classes utilitárias Tailwind (w-6, h-4 etc).
        # compose_suite() já copiava esse arquivo; provision_project() nunca
        # copiava — o CSS voltava 404 em produção e TODA a página (ícones,
        # cores, espaçamento) renderizava sem estilo nenhum (ícones SVG
        # gigantes, texto sem layout).
        # docs.html NÃO é copiado cru aqui: é um MOLDE Jinja2 (placeholders
        # tipo {{ spotlight_commands }}) que só é renderizado de verdade mais
        # abaixo, depois que os módulos já existem em disco (ver passo 5.1).
        src_output_css = os.path.join(templates_dir, 'output.css')
        if os.path.exists(src_output_css):
            os.makedirs(os.path.join(project_dir, 'src', 'static'), exist_ok=True)
            shutil.copyfile(src_output_css, os.path.join(project_dir, 'src', 'static', 'output.css'))

        for f in ['Dockerfile', 'docker-compose.yml', 'deploy.sh']:
            src = os.path.join(templates_dir, f)
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(project_dir, f))

        # nginx/ (nginx.conf + ssl/generate_ssl.py): docker-compose.yml monta
        # ./nginx/nginx.conf e ./nginx/ssl — sem esta pasta o serviço nginx
        # nunca sobe (bind mount de arquivo inexistente). compose_suite.py já
        # copiava isto corretamente; provision_project.py nunca copiava
        # (achado real: `docker compose up` do projeto gerado por `master init`
        # falhava com bind mount ausente — validação E2E do Fluxo 01, 17/09/2026).
        nginx_src = os.path.join(templates_dir, 'nginx')
        if os.path.isdir(nginx_src):
            nginx_dst = os.path.join(project_dir, 'nginx')
            for root, _dirs, files in os.walk(nginx_src):
                rel = os.path.relpath(root, nginx_src)
                d_dir = os.path.join(nginx_dst, rel) if rel != '.' else nginx_dst
                os.makedirs(d_dir, exist_ok=True)
                for f in files:
                    shutil.copyfile(os.path.join(root, f), os.path.join(d_dir, f))

        if os.path.exists(os.path.join(templates_dir, 'locustfile.py')):
            shutil.copyfile(os.path.join(templates_dir, 'locustfile.py'), os.path.join(project_dir, 'tests', 'load', 'locustfile.py'))

    # 3. Copiar scripts (aidd.py, add_module.py)
    hub_scripts = os.path.join(repo_root, 'scripts')
    for s in ['aidd.py', 'add_module.py']:
        src = os.path.join(hub_scripts, s)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(project_dir, 'scripts', s))

    # 4. Copiar Gates Rígidos
    if os.path.exists(gates_dir):
        for g in os.listdir(gates_dir):
            if g.endswith('.py'):
                shutil.copyfile(os.path.join(gates_dir, g), os.path.join(project_dir, 'scripts', 'gates', g))

    # 4.5. Gerar PLANO-EXECUCAO-ESTRUTURADO.json ANTES do módulo padrão inicial.
    # Achado real (18/09/2026): quando o plano só era escrito no passo 7 (depois
    # do módulo "principal" já criado), `criar_modulo()` via `add_module.py`
    # não encontrava o arquivo ainda e pulava o registro do módulo no
    # manifesto — "principal" ficava só como pasta física em disco, nunca
    # religado a `src/server.py` nem contabilizado no `modulos`. O
    # `NextJSExporter` descobre módulos varrendo `src/modules/` no disco
    # (independente do manifesto), então gerava uma página para "principal"
    # chamando uma rota que o backend nunca registrou -> HTTP 404 real no
    # frontend. Escrever o plano aqui garante que `criar_modulo()` registre
    # e religue "principal" corretamente desde o primeiro módulo.
    plano_path = os.path.join(project_dir, 'PLANO-EXECUCAO-ESTRUTURADO.json')
    with open(plano_path, 'w', encoding='utf-8') as f:
        json.dump({
            "projeto": {
                "nome": slug,
                "descricao": project_desc,
                "arquitetura": "AIDD v5.1 Modular Monolith",
                "zero_api_key_mode": True,
                "status": "INICIALIZADO"
            },
            "modulos": []
        }, f, indent=2, ensure_ascii=False)

    # 5. Criar modulo padrão inicial
    from add_module import criar_modulo
    criar_modulo("principal", "Módulo principal", project_dir)

    # 5.05. Renderizar docs.html de verdade (Jinja2), agora que "principal" já
    # existe em disco (generate_documentation_html faz parsing AST do módulo).
    _renderizar_e_escrever_docs_html(
        templates_dir,
        os.path.join(project_dir, 'src', 'static'),
        slug,
        ["principal"],
        os.path.join(project_dir, 'src'),
    )

    # 5.1. Gerar o Servidor Monolítico Modular (src/server.py) e o frontend.
    # criar_modulo() só RELIGA o server.py num módulo novo se ele já existir
    # (ver comentário em add_module.py) — na primeira composição do projeto
    # ele nunca existiu, então precisa ser gerado aqui, do mesmo jeito que
    # compose_suite() faz.
    #
    # Lei Inviolável #11 (Padrão-Ouro de Stack, `AGENTS.md`): o frontend
    # default é Next.js + TypeScript + Tailwind CSS (`frontend_stack=
    # "nextjs"`). O Super-App em HTML/CSS/JS Python puro só é gerado se
    # pedido explicitamente (`frontend_stack="python-html"`).
    try:
        from compose_suite import generate_modular_server_code
        server_code = generate_modular_server_code(slug, ["principal"], db_engine="sqlite", project_dir=project_dir)
        with open(os.path.join(project_dir, 'src', 'server.py'), 'w', encoding='utf-8') as f:
            f.write(server_code)
        print("  [+] Servidor dinâmico 'src/server.py' gerado com sucesso!")

        if frontend_stack == 'nextjs':
            from nextjs_exporter import NextJSExporter
            NextJSExporter().export_project(project_dir, os.path.join(project_dir, 'frontend'), suite_name=slug)
            print("  [+] Front-end 'frontend/' gerado em Next.js + TypeScript + Tailwind (Lei #11)!")
        else:
            from compose_suite import generate_superapp_index_html
            index_html = generate_superapp_index_html(slug, ["principal"])
            with open(os.path.join(project_dir, 'src', 'static', 'index.html'), 'w', encoding='utf-8') as f:
                f.write(index_html)
            print("  [+] Front-end Super-App 'src/static/index.html' gerado com sucesso!")
    except ImportError as e:
        print(f"  [!] Aviso: não foi possível gerar server.py/frontend: {e}")

    # 6. Gerar requirements.txt
    from compose_suite import CORE_KERNEL_REQUIREMENTS
    with open(os.path.join(project_dir, 'requirements.txt'), 'w', encoding='utf-8') as f:
        f.write(CORE_KERNEL_REQUIREMENTS)

    # 7. Completar PLANO-EXECUCAO-ESTRUTURADO.json com as fases do projeto.
    # Atualiza (não sobrescreve) o arquivo escrito no passo 4.5, preservando
    # o "modulos" que `criar_modulo()` já registrou para "principal".
    with open(plano_path, 'r', encoding='utf-8') as f:
        plano = json.load(f)
    plano["fases"] = [
        {"id": "fase-01-core", "nome": "Core Kernel & Banco WAL", "status": "CONCLUIDO"},
        {"id": "fase-02-modulos", "nome": "Fatias Verticais e Full CRUD", "status": "PENDENTE"},
        {"id": "fase-03-auditoria", "nome": "Auditoria de Gates Rígidos", "status": "PENDENTE"}
    ]
    with open(plano_path, 'w', encoding='utf-8') as f:
        json.dump(plano, f, indent=2, ensure_ascii=False)

    # 8. Git Init
    if not os.path.exists(os.path.join(project_dir, '.git')):
        subprocess.run(['git', 'init'], cwd=project_dir, capture_output=True)

    print(f"✨ PROJETO '{slug}' 100% PROVISIONADO COM SHARED KERNEL, FATIAS VERTICAIS E GATES RÍGIDOS!")

def provision_backend_only(project_dir, modulo_nome, descricao=""):
    """
    Gera SOMENTE o backend VSA (core kernel, modulo, server.py, gates,
    requirements.txt) num projeto ja existente -- NUNCA toca em Dockerfile,
    docker-compose.yml, nginx/ ou frontend/, porque esses arquivos ja
    pertencem a um frontend preservado (ex: saida do aidd-bridge, FLUXO 03)
    que nao pode ser sobrescrito pelo Super-App/Next.js que `provision()`
    geraria por padrao. Usado por `master attach-vsa`.

    O backend nasce isolado em `<project_dir>/backend/` (nao direto na raiz)
    porque o frontend preservado tambem usa a convencao `src/` na raiz
    (src/pages, src/integrations — layout Vite/Lovable original); gerar o
    backend em `<project_dir>/src/core` misturaria os dois namespaces no
    mesmo diretorio.
    """
    project_dir = os.path.abspath(project_dir)
    backend_dir = os.path.join(project_dir, 'backend')
    slug = slugify(os.path.basename(project_dir)) or "projeto-modular"

    os.makedirs(os.path.join(backend_dir, 'src', 'core'), exist_ok=True)
    os.makedirs(os.path.join(backend_dir, 'src', 'modules'), exist_ok=True)
    os.makedirs(os.path.join(backend_dir, 'tests', 'unit'), exist_ok=True)
    os.makedirs(os.path.join(backend_dir, 'scripts', 'gates'), exist_ok=True)

    for p in ['src/__init__.py', 'src/core/__init__.py', 'src/modules/__init__.py', 'tests/__init__.py']:
        full = os.path.join(backend_dir, *p.split('/'))
        if not os.path.exists(full):
            open(full, 'w', encoding='utf-8').close()

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_core = os.path.join(repo_root, 'templates', 'core')
    templates_dir = templates_core if os.path.isdir(templates_core) else os.path.join(repo_root, 'templates', 'v2')
    gates_dir = os.path.join(repo_root, 'templates', 'gates')

    if os.path.exists(templates_dir):
        from compose_suite import CORE_KERNEL_FILES
        for f in CORE_KERNEL_FILES + ['repositories.py', 'swagger.html', 'webhook_studio.html', 'mcp_studio.html']:
            src = os.path.join(templates_dir, f)
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(backend_dir, 'src', 'core', f))
        os.makedirs(os.path.join(backend_dir, 'src', 'static'), exist_ok=True)
        # docs.html NAO e copiado cru aqui (mesmo motivo de provision()): e um
        # molde Jinja2, renderizado de verdade so depois de criar_modulo().
        src_output_css = os.path.join(templates_dir, 'output.css')
        if os.path.exists(src_output_css):
            shutil.copyfile(src_output_css, os.path.join(backend_dir, 'src', 'static', 'output.css'))

    hub_scripts = os.path.join(repo_root, 'scripts')
    for s in ['aidd.py', 'add_module.py']:
        src = os.path.join(hub_scripts, s)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(backend_dir, 'scripts', s))

    if os.path.exists(gates_dir):
        for g in os.listdir(gates_dir):
            if g.endswith('.py'):
                shutil.copyfile(os.path.join(gates_dir, g), os.path.join(backend_dir, 'scripts', 'gates', g))

    plano_path = os.path.join(backend_dir, 'PLANO-EXECUCAO-ESTRUTURADO.json')
    if not os.path.exists(plano_path):
        with open(plano_path, 'w', encoding='utf-8') as f:
            json.dump({
                "projeto": {
                    "nome": slug,
                    "descricao": descricao or modulo_nome,
                    "arquitetura": "AIDD v5.1 Modular Monolith (Bridge VSA Attach)",
                    "zero_api_key_mode": True,
                    "status": "INICIALIZADO"
                },
                "modulos": []
            }, f, indent=2, ensure_ascii=False)

    from add_module import criar_modulo
    criar_modulo(modulo_nome, descricao or f"Modulo {modulo_nome}", backend_dir)

    _renderizar_e_escrever_docs_html(
        templates_dir,
        os.path.join(backend_dir, 'src', 'static'),
        slug,
        [modulo_nome],
        os.path.join(backend_dir, 'src'),
    )

    from compose_suite import generate_modular_server_code, CORE_KERNEL_REQUIREMENTS
    # project_dir aqui e so pra resolver a paleta (DESIGN-SYSTEM.json vive na
    # raiz do projeto, gerado pelo aidd-planner -- nao dentro de backend/).
    # Passar backend_dir por engano faz cair no fallback por hash e gerar uma
    # cor diferente da que o frontend preservado ja usa (two-tone mismatch).
    server_code = generate_modular_server_code(slug, [modulo_nome], db_engine="sqlite", project_dir=project_dir)
    with open(os.path.join(backend_dir, 'src', 'server.py'), 'w', encoding='utf-8') as f:
        f.write(server_code)

    with open(os.path.join(backend_dir, 'requirements.txt'), 'w', encoding='utf-8') as f:
        f.write(CORE_KERNEL_REQUIREMENTS)

    print(f"[+] Backend VSA ('{modulo_nome}') anexado em {backend_dir} -- frontend/Docker preservados intactos.")
    return {"project_dir": project_dir, "backend_dir": backend_dir, "slug": slug, "modulo": modulo_nome}


if __name__ == '__main__':
    prompt = sys.argv[1] if len(sys.argv) > 1 else 'projeto-modular'
    provision(prompt)
