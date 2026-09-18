import os, sys, shutil, subprocess, json, re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s_-]+', '-', text)[:40]

def provision(project_desc, base_dir=None):
    if os.path.isabs(project_desc) or os.sep in project_desc or (os.altsep and os.altsep in project_desc) or os.path.exists(project_desc):
        project_dir = os.path.abspath(project_desc)
        slug = slugify(os.path.basename(project_dir)) or "projeto-modular"
    else:
        words = project_desc.split()
        target_text = ' '.join(words[:3]) if len(words) >= 3 else project_desc
        slug = slugify(target_text)
        
        if not base_dir:
            base_dir = os.path.join(os.path.expanduser('~'), 'orca', 'workspaces', 'PROJETOS Criados com IA')
            
        project_dir = os.path.join(base_dir, f'proj_{slug}')
    
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
        for sf in ['docs.html']:
            src = os.path.join(templates_dir, sf)
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(project_dir, 'src', 'static', sf))

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

    # 5. Criar modulo padrão inicial
    from add_module import criar_modulo
    criar_modulo("principal", "Módulo principal", project_dir)

    # 5.1. Gerar o Servidor Monolítico Modular (src/server.py) e o front-end
    # Super-App (src/static/index.html). criar_modulo() só RELIGA o
    # server.py num módulo novo se ele já existir (ver comentário em
    # add_module.py) — na primeira composição do projeto ele nunca existiu,
    # então precisa ser gerado aqui, do mesmo jeito que compose_suite() faz.
    try:
        from compose_suite import (
            generate_modular_server_code,
            generate_superapp_index_html,
        )
        server_code = generate_modular_server_code(slug, ["principal"], db_engine="sqlite")
        with open(os.path.join(project_dir, 'src', 'server.py'), 'w', encoding='utf-8') as f:
            f.write(server_code)
        print("  [+] Servidor dinâmico 'src/server.py' gerado com sucesso!")

        index_html = generate_superapp_index_html(slug, ["principal"])
        with open(os.path.join(project_dir, 'src', 'static', 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index_html)
        print("  [+] Front-end Super-App 'src/static/index.html' gerado com sucesso!")
    except ImportError as e:
        print(f"  [!] Aviso: não foi possível gerar server.py/index.html: {e}")

    # 6. Gerar requirements.txt
    from compose_suite import CORE_KERNEL_REQUIREMENTS
    with open(os.path.join(project_dir, 'requirements.txt'), 'w', encoding='utf-8') as f:
        f.write(CORE_KERNEL_REQUIREMENTS)

    # 7. Gerar PLANO-EXECUCAO-ESTRUTURADO.json
    plano = {
        "projeto": {
            "nome": slug,
            "descricao": project_desc,
            "arquitetura": "AIDD v5.1 Modular Monolith",
            "zero_api_key_mode": True,
            "status": "INICIALIZADO"
        },
        "fases": [
            {"id": "fase-01-core", "nome": "Core Kernel & Banco WAL", "status": "CONCLUIDO"},
            {"id": "fase-02-modulos", "nome": "Fatias Verticais e Full CRUD", "status": "PENDENTE"},
            {"id": "fase-03-auditoria", "nome": "Auditoria de Gates Rígidos", "status": "PENDENTE"}
        ]
    }
    with open(os.path.join(project_dir, 'PLANO-EXECUCAO-ESTRUTURADO.json'), 'w', encoding='utf-8') as f:
        json.dump(plano, f, indent=2, ensure_ascii=False)

    # 8. Git Init
    if not os.path.exists(os.path.join(project_dir, '.git')):
        subprocess.run(['git', 'init'], cwd=project_dir, capture_output=True)

    print(f"✨ PROJETO '{slug}' 100% PROVISIONADO COM SHARED KERNEL, FATIAS VERTICAIS E GATES RÍGIDOS!")

if __name__ == '__main__':
    prompt = sys.argv[1] if len(sys.argv) > 1 else 'projeto-modular'
    provision(prompt)
