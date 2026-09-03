import os, sys, shutil, subprocess, json, re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s_-]+', '-', text)[:40]

def provision(project_desc, base_dir=None):
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
        for f in ['database.py', 'events.py', 'openapi.py', 'webhooks.py', 'security.py', 'mcp_server.py']:
            src = os.path.join(templates_dir, f)
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(project_dir, 'src', 'core', f))
        
        for sf in ['index.html', 'docs.html']:
            src = os.path.join(templates_dir, sf)
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(project_dir, 'src', 'static', sf))

        for f in ['Dockerfile', 'docker-compose.yml', 'deploy.sh']:
            src = os.path.join(templates_dir, f)
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(project_dir, f))
                
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

    # 6. Gerar requirements.txt
    with open(os.path.join(project_dir, 'requirements.txt'), 'w', encoding='utf-8') as f:
        f.write("pytest>=7.0.0\nrequests>=2.28.0\nlocust>=2.15.0\n")

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
