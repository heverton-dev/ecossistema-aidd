import os, sys, shutil, subprocess, json, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from moldes_catalogo import gates_de_projeto, molde  # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def _projeto_tem_fatias_reais(project_dir) -> bool:
    """True quando o projeto tem ao menos uma fatia vertical com implementacao real.

    Uma fatia e real quando o seu `domain/entities.py` nao define o agregado
    generico do catalogo (`class <Pascal>Item`).
    """
    raiz_modulos = os.path.join(project_dir, "src", "modules")
    if not os.path.isdir(raiz_modulos):
        return False
    for modulo in os.listdir(raiz_modulos):
        entities = os.path.join(raiz_modulos, modulo, "domain", "entities.py")
        if not os.path.isfile(entities):
            continue
        try:
            with open(entities, "r", encoding="utf-8") as f:
                conteudo = f.read()
        except OSError:
            continue
        if f"class {modulo.capitalize()}Item" not in conteudo:
            return True
    return False

def _projeto_tem_kernel_proprio(project_dir) -> bool:
    """True quando o projeto tem um kernel compartilhado proprio (implementacao real).

    O TaskFlow implementa `src/core/` com configuracao, erros, seguranca
    (Argon2id + JWT) e dependencias — o proprio. Nesse caso o kernel generico
    do catalogo (database/events/outbox/mcp_server/...) e codigo morto.
    """
    security = os.path.join(project_dir, "src", "core", "security.py")
    if not os.path.isfile(security):
        return False
    try:
        with open(security, "r", encoding="utf-8") as f:
            conteudo = f.read()
    except OSError:
        return False
    return "def hashear_senha(" in conteudo and "class SecurityService" in conteudo

def _copiar_preservando_existente(origem, destino):
    """Copia `origem` -> `destino` SEM sobrescrever um arquivo que ja existe.

    Achado real (validacao E2E do Fluxo 01): o `master init`/`master add-module`
    reescrevia incondicionalmente `src/core/*`, `src/server.py`, `src/modules/<slug>/*`
    e `frontend/` com os moldes genericos do catalogo. Ao rodar o fluxo de novo
    sobre um projeto que JA tem a implementacao real (VSA do engine + frontend
    proprio), o scaffold apagava o codigo entregue e o gate G_TESTES_REAIS quebrava
    com `ImportError` nos modulos reais.

    Regra adotada: arquivo existente e do DONO do projeto — nunca e sobrescrito
    pelo molde. O molde so preenche lacuna (arquivo ausente). Comportamento
    identico ao `aidd-forge init` (que reporta "arquivos ignorados (ja existem)").
    """
    if os.path.exists(destino):
        return False
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    shutil.copyfile(origem, destino)
    return True


def _copiar_arvore_preservando_existente(origem_raiz, destino_raiz, ignore=None):
    """Copia arvore de arquivos preservando os que ja existem no destino."""
    copiados = 0
    for raiz, _, arquivos in os.walk(origem_raiz):
        if ignore is not None:
            ignorados = ignore(raiz, arquivos)
            arquivos = [a for a in arquivos if a not in ignorados]
        rel = os.path.relpath(raiz, origem_raiz)
        destino_pasta = destino_raiz if rel == "." else os.path.join(destino_raiz, rel)
        os.makedirs(destino_pasta, exist_ok=True)
        for arquivo in arquivos:
            destino = os.path.join(destino_pasta, arquivo)
            if os.path.exists(destino):
                continue
            shutil.copyfile(os.path.join(raiz, arquivo), destino)
            copiados += 1
    return copiados


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
    docs_template_path = molde(templates_dir, 'docs.html')
    if not os.path.exists(docs_template_path):
        try:
            from aidd_forge.core.almoxarifado import caminho_peca
            docs_template_path = str(caminho_peca("moldes/quarteto/docs.html"))
        except Exception:
            pass
    if not os.path.exists(docs_template_path):
        return
    with open(docs_template_path, 'r', encoding='utf-8') as f:
        raw_docs_html = f.read()
    from compose_suite import generate_documentation_html
    final_docs_html = generate_documentation_html(suite_name, module_slugs, src_dir, raw_docs_html)
    os.makedirs(static_dir, exist_ok=True)
    with open(os.path.join(static_dir, 'docs.html'), 'w', encoding='utf-8') as f:
        f.write(final_docs_html)

def provision(project_desc, base_dir=None, frontend_stack='tanstack', modulos_iniciais=None):
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
    
    # `src/__init__.py` do projeto pode ter conteudo proprio (o TaskFlow usa-o
    # para registrar `src/` no sys.path e assim o boot `uvicorn src.server:app`
    # funcionar). Truncar o arquivo apagava esse bootstrap — achado real na
    # validacao E2E do Fluxo 01. So cria o arquivo quando ele ainda nao existe.
    src_init = os.path.join(project_dir, 'src', '__init__.py')
    if not os.path.exists(src_init):
        open(src_init, 'w', encoding='utf-8').close()
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
        # Se o projeto JA tem um kernel proprio (implementacao real em
        # src/core/), o molde generico do catalogo nao e materializado: ele
        # reintroduz codigo morto (SQL, ORM, event bus) que dilui a cobertura e
        # nao e importado por nada (achado real na validacao E2E do Fluxo 01).
        kernel_proprio = _projeto_tem_kernel_proprio(project_dir)
        if kernel_proprio:
            print("  [=] Projeto com kernel proprio em src/core — molde generico do catalogo nao materializado.")
        for f in ([] if kernel_proprio else CORE_KERNEL_FILES) + ([] if kernel_proprio else ['repositories.py', 'swagger.html', 'webhook_studio.html', 'mcp_studio.html']):
            src = molde(templates_dir, f)
            if os.path.exists(src):
                _copiar_preservando_existente(src, os.path.join(project_dir, 'src', 'core', f))

        src_output_css = molde(templates_dir, 'output.css')
        if os.path.exists(src_output_css):
            os.makedirs(os.path.join(project_dir, 'src', 'static'), exist_ok=True)
            _copiar_preservando_existente(src_output_css, os.path.join(project_dir, 'src', 'static', 'output.css'))

        # Ticket 17 / D1: infraestrutura (Dockerfile, docker-compose.yml, deploy.sh, nginx/)
        # não é mais gerada pelo aidd-master. Essa responsabilidade pertence ao aidd-ops.

        locust_src = molde(templates_dir, 'locustfile.py')
        if os.path.exists(locust_src):
            _copiar_preservando_existente(locust_src, os.path.join(project_dir, 'tests', 'load', 'locustfile.py'))

    # 3. Copiar scripts (aidd.py, add_module.py)
    hub_scripts = os.path.join(repo_root, 'scripts')
    for s in ['aidd.py', 'add_module.py']:
        src = os.path.join(hub_scripts, s)
        if os.path.exists(src):
            _copiar_preservando_existente(src, os.path.join(project_dir, 'scripts', s))

    # 4. Copiar Gates Rígidos
    for g, origem in sorted(gates_de_projeto(gates_dir).items()):
        _copiar_preservando_existente(origem, os.path.join(project_dir, 'scripts', 'gates', g))

    # 4.1. Garantir pytest.ini isolado para prevencao de colisao de namespace
    pytest_ini_path = os.path.join(project_dir, 'pytest.ini')
    if not os.path.exists(pytest_ini_path):
        with open(pytest_ini_path, 'w', encoding='utf-8') as f_ini:
            f_ini.write(
                "[pytest]\n"
                "testpaths = tests\n"
                "python_files = test_*.py *_test.py\n"
                "norecursedirs = scripts/gates gates .venv node_modules\n"
            )

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

    # 5. Criar módulos iniciais
    # Ticket 13-B: Se foram especificados módulos iniciais, criá-los;
    # Caso contrário, verifica se há fatias em HANDOFF_ENGINE_MASTER.json (C3)
    # ou PLANNER.json / HANDOFF_PLANNER_ENGINE.json. Se não houver nenhum, fallback para ["principal"].
    from add_module import criar_modulo
    modulos_alvo = []
    if modulos_iniciais:
        modulos_alvo = [str(m).strip() for m in modulos_iniciais if str(m).strip()]

    # Remove o modulo "umbrella" com o nome do projeto quando o projeto ja tem
    # fatias verticais REAIS: o C3 de uma execucao anterior pode listar esse
    # modulo generico, e recria-lo a cada rodada (codigo morto). Achado real na
    # validacao E2E do Fluxo 01.
    if _projeto_tem_fatias_reais(project_dir) and slug in modulos_alvo:
        modulos_alvo = [m for m in modulos_alvo if m != slug]
        print(f"  [=] Módulo umbrella '{slug}' removido — o projeto já tem fatias verticais reais.")

    if not modulos_alvo:
        # Checar C3 (HANDOFF_ENGINE_MASTER.json) ou PLANNER.json
        c3_caminho = os.path.join(project_dir, 'HANDOFF_ENGINE_MASTER.json')
        planner_caminho = os.path.join(project_dir, 'PLANNER.json')
        planner_h_caminho = os.path.join(project_dir, 'HANDOFF_PLANNER_ENGINE.json')
        if os.path.isfile(c3_caminho):
            try:
                with open(c3_caminho, 'r', encoding='utf-8') as f_c3:
                    dados_c3 = json.load(f_c3)
                    modulos_alvo = [s.get('slice_nome') for s in dados_c3.get('slices_geradas', []) if s.get('slice_nome')]
            except Exception:
                pass
        if not modulos_alvo and os.path.isfile(planner_caminho):
            try:
                with open(planner_caminho, 'r', encoding='utf-8') as f_pl:
                    dados_pl = json.load(f_pl)
                    modulos_alvo = [c.get('modulo') for c in dados_pl.get('ddd_bounded_contexts', []) if c.get('modulo')]
            except Exception:
                pass
        if not modulos_alvo and os.path.isfile(planner_h_caminho):
            try:
                with open(planner_h_caminho, 'r', encoding='utf-8') as f_plh:
                    dados_plh = json.load(f_plh)
                    modulos_alvo = [c.get('modulo') or c.get('slug') for c in dados_plh.get('modulos_funcionais', []) if c.get('modulo') or c.get('slug')]
            except Exception:
                pass

    if not modulos_alvo:
        modulos_alvo = ["principal"]

    # Cria cada módulo alvo
    for m in modulos_alvo:
        criar_modulo(m, f"Módulo {m}", project_dir)

    # 5.05. Renderizar docs.html de verdade (Jinja2) com todos os módulos criados
    _renderizar_e_escrever_docs_html(
        templates_dir,
        os.path.join(project_dir, 'src', 'static'),
        slug,
        modulos_alvo,
        os.path.join(project_dir, 'src'),
    )

    # 5.1. Gerar o Servidor Monolítico Modular (src/server.py) e o frontend.
    try:
        from compose_suite import generate_modular_server_code
        server_code = generate_modular_server_code(slug, modulos_alvo, db_engine="sqlite", project_dir=project_dir)
        servidor_destino = os.path.join(project_dir, 'src', 'server.py')
        if os.path.exists(servidor_destino):
            print("  [=] 'src/server.py' já existe (implementação do projeto) — preservado.")
        else:
            with open(servidor_destino, 'w', encoding='utf-8') as f:
                f.write(server_code)
            print("  [+] Servidor dinâmico 'src/server.py' gerado com sucesso!")

        if frontend_stack == 'tanstack':
            frontend_dest = os.path.join(project_dir, 'frontend')
            frontend_template = os.path.join(repo_root, 'templates', 'v2', 'frontend')
            if not os.path.isdir(frontend_template):
                frontend_template = os.path.join(repo_root, 'templates', 'frontend')
            if os.path.isdir(frontend_template):
                def _ignorar_build(dir_src, names):
                    return {'node_modules', 'dist', '.git', '__pycache__'}.intersection(names)
                _copiar_arvore_preservando_existente(frontend_template, frontend_dest, ignore=_ignorar_build)
            print("  [+] Front-end 'frontend/' gerado em TanStack Start / Router + TypeScript + Tailwind (Lei #11)!")
        elif frontend_stack == 'nextjs':
            from nextjs_exporter import NextJSExporter
            NextJSExporter().export_project(project_dir, os.path.join(project_dir, 'frontend'), suite_name=slug)
            print("  [+] Front-end 'frontend/' gerado em Next.js + TypeScript + Tailwind!")
        else:
            from compose_suite import generate_superapp_index_html
            index_html = generate_superapp_index_html(slug, modulos_alvo)
            with open(os.path.join(project_dir, 'src', 'static', 'index.html'), 'w', encoding='utf-8') as f:
                f.write(index_html)
            print("  [+] Front-end Super-App 'src/static/index.html' gerado com sucesso!")
    except ImportError as e:
        print(f"  [!] Aviso: não foi possível gerar server.py/frontend: {e}")

    # 6. Gerar requirements.txt
    from compose_suite import CORE_KERNEL_REQUIREMENTS
    requirements_destino = os.path.join(project_dir, 'requirements.txt')
    if os.path.exists(requirements_destino):
        print("  [=] 'requirements.txt' já existe — preservado.")
    else:
        with open(requirements_destino, 'w', encoding='utf-8') as f:
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
    # 9. Integração e emissão de C4 se C3 estiver presente
    try:
        from integrador_master import integrar_fatias_e_emitir_c4
        c3_file = os.path.join(project_dir, 'HANDOFF_ENGINE_MASTER.json')
        if os.path.isfile(c3_file):
            integrar_fatias_e_emitir_c4(project_dir)
    except Exception:
        pass

    print(f"✨ PROJETO '{slug}' 100% PROVISIONADO COM SHARED KERNEL, FATIAS VERTICAIS E GATES RÍGIDOS!")

def provision_backend_only(project_dir, modulo_nome, descricao=""):
    """
    Gera SOMENTE o backend VSA (core kernel, modulo, server.py, gates,
    requirements.txt) num projeto ja existente -- NUNCA toca em Dockerfile,
    docker-compose.yml, nginx/ ou frontend/, porque esses arquivos ja
    pertencem a um frontend preservado (ex: saida do aidd-freedom, FLUXO 03)
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
        # Se o projeto JA tem um kernel proprio (implementacao real em
        # src/core/), o molde generico do catalogo nao e materializado: ele
        # reintroduz codigo morto (SQL, ORM, event bus) que dilui a cobertura e
        # nao e importado por nada (achado real na validacao E2E do Fluxo 01).
        kernel_proprio = _projeto_tem_kernel_proprio(project_dir)
        if kernel_proprio:
            print("  [=] Projeto com kernel proprio em src/core — molde generico do catalogo nao materializado.")
        for f in ([] if kernel_proprio else CORE_KERNEL_FILES) + ([] if kernel_proprio else ['repositories.py', 'swagger.html', 'webhook_studio.html', 'mcp_studio.html']):
            src = molde(templates_dir, f)
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(backend_dir, 'src', 'core', f))
        os.makedirs(os.path.join(backend_dir, 'src', 'static'), exist_ok=True)
        # docs.html NAO e copiado cru aqui (mesmo motivo de provision()): e um
        # molde Jinja2, renderizado de verdade so depois de criar_modulo().
        src_output_css = molde(templates_dir, 'output.css')
        if os.path.exists(src_output_css):
            shutil.copyfile(src_output_css, os.path.join(backend_dir, 'src', 'static', 'output.css'))

    hub_scripts = os.path.join(repo_root, 'scripts')
    for s in ['aidd.py', 'add_module.py']:
        src = os.path.join(hub_scripts, s)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(backend_dir, 'scripts', s))

    for g, origem in sorted(gates_de_projeto(gates_dir).items()):
        shutil.copyfile(origem, os.path.join(backend_dir, 'scripts', 'gates', g))

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
