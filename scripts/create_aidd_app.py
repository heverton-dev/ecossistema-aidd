#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — INSTALADOR E SCAFFOLD DE 1 CLIQUE (EXPERIÊNCIA NPX)
=============================================================================
Cria uma nova aplicação completa no Padrão-Ouro RevNault (TanStack Router +
React 19 + TypeScript + Tailwind CSS + FastAPI + SQLite WAL + Quarteto Sine
Qua Non) em segundos, com dependências prontas e scripts de execução.

Uso:
    python scripts/create_aidd_app.py <nome-do-projeto> [--fluxo pure|open|freedom] [--destino CAMINHO]

Exemplo:
    python ecossistema.py novo meu-app
    npx @aidd/create meu-app
=============================================================================
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# Injeta caminho do sintetizador dinâmico de telas
sys.path.insert(0, str(ROOT_DIR / "modulos" / "03-plataforma-e-entrega" / "fatiamento-master" / "aidd-master" / "scripts"))
try:
    from screen_synthesizer import sintetizar_tela_entidade
except ImportError:
    sintetizar_tela_entidade = None

def criar_aplicacao(nome_app: str, fluxo: str = "pure", destino: str = None, instalar_deps: bool = False):
    print("=" * 72)
    print(f"🚀 [AIDD CREATE] Inicializando nova aplicação: {nome_app}")
    print(f"📦 Fluxo Canônico Selecionado: aidd-{fluxo}")
    print("=" * 72)

    # 1. Definir pasta de destino
    if destino:
        pasta_destino = Path(destino).resolve()
    else:
        pasta_destino = ROOT_DIR / "projetos" / nome_app

    pasta_destino.mkdir(parents=True, exist_ok=True)
    print(f"📁 Destino: {pasta_destino}")

    # 2. Copiar template canônico do Padrão-Ouro (aidd-master templates/v2)
    origem_template = ROOT_DIR / "modulos" / "03-plataforma-e-entrega" / "fatiamento-master" / "aidd-master" / "templates" / "v2"
    
    # 2.1 Frontend
    frontend_dest = pasta_destino / "frontend"
    frontend_orig = origem_template / "frontend"
    if frontend_orig.is_dir():
        if frontend_dest.exists():
            shutil.rmtree(frontend_dest)
        shutil.copytree(frontend_orig, frontend_dest, ignore=shutil.ignore_patterns("node_modules", "dist", ".vite"))
        
        # 2.1.1 Síntese Dinâmica de Telas (Zero templates estáticos de negócio, zero window.alert/confirm)
        if sintetizar_tela_entidade:
            pages_dest = frontend_dest / "src" / "pages"
            pages_dest.mkdir(parents=True, exist_ok=True)
            conteudo_tela = sintetizar_tela_entidade(nome_modulo="Tarefas", slug_modulo="modulo1")
            (pages_dest / "TarefasPage.tsx").write_text(conteudo_tela, encoding="utf-8")
            print("  ✓ Telas SINTETIZADAS DINAMICAMENTE (Kanban drag-and-drop, Modal e Toasts proprietários, zero window.alert).")
        else:
            print("  ✓ Frontend TanStack Router + React 19 + Tailwind CSS gerado.")

    # 2.2 Backend src/
    backend_dest = pasta_destino / "src"
    backend_dest.mkdir(parents=True, exist_ok=True)
    
    # Copia arquivos Python do template v2 para src/
    for item in origem_template.glob("*.py"):
        shutil.copy2(item, backend_dest / item.name)
    if (origem_template / "shared").is_dir():
        shutil.copytree(origem_template / "shared", backend_dest / "shared", dirs_exist_ok=True)
    print("  ✓ Backend Python (server.py, FastAPI, repositórios) gerado em src/.")

    # 2.3 Copiar núcleo compartilhado (src-core) para src/core/
    core_dest = backend_dest / "core"
    core_dest.mkdir(parents=True, exist_ok=True)
    src_core = ROOT_DIR / "componentes" / "compartilhado" / "src-core"
    if src_core.is_dir():
        for item in src_core.glob("*.*"):
            shutil.copy2(item, core_dest / item.name)

    # 2.4 Copiar Quarteto Sine Qua Non Dinâmico em Modo Claro
    moldes_quarteto = ROOT_DIR / "componentes" / "compartilhado" / "moldes" / "quarteto"
    static_dest = backend_dest / "static"
    static_dest.mkdir(parents=True, exist_ok=True)
    
    for arquivo_quarteto in ["swagger.html", "webhook_studio.html", "mcp_studio.html", "docs.html"]:
        orig = moldes_quarteto / arquivo_quarteto
        if orig.is_file():
            shutil.copy2(orig, core_dest / arquivo_quarteto)
            shutil.copy2(orig, static_dest / arquivo_quarteto)
    print("  ✓ Quarteto Sine Qua Non Dinâmico (Swagger, Webhook, MCP, Docs) injetado em Modo Claro.")

    # 2.5 Gerar módulo inicial (modulo1) na arquitetura VSA
    try:
        sys.path.insert(0, str(ROOT_DIR / "modulos" / "03-plataforma-e-entrega" / "fatiamento-master" / "aidd-master" / "scripts"))
        from add_module import criar_modulo
        criar_modulo("modulo1", "Gestão de Tarefas e Itens", str(pasta_destino))
        print("  ✓ Módulo VSA 'modulo1' gerado com persistência SQLite WAL e rotas completas.")
    except Exception as e:
        print(f"  [!] Aviso na geração do modulo1 inicial: {e}")

    # 2.4 Arquivos de configuração essenciais
    arquivos_raiz = [
        ("requirements.txt", "fastapi>=0.115.0\nuvicorn>=0.30.0\npydantic>=2.8.0\npytest>=8.0.0\nhttpx>=0.27.0\n"),
        ("pytest.ini", "[pytest]\ntestpaths = tests\npython_files = test_*.py\n"),
        (".gitignore", "node_modules/\n.venv/\nvenv/\n__pycache__/\n*.pyc\n*.db\n*.db-wal\n*.db-shm\n.env\ndist/\n"),
        ("AGENTS.md", f"# Diretrizes Agênticas — {nome_app}\n\n- Padrão Ouro: TanStack Router + React + Tailwind + FastAPI.\n- Modo Claro Soberano (Light Mode Sovereign).\n- Quarteto Sine Qua Non ativo em /docs, /webhook, /mcp, /docs/guia.\n"),
    ]

    for nome_arq, conteudo in arquivos_raiz:
        destino_arq = pasta_destino / nome_arq
        if not destino_arq.exists():
            destino_arq.write_text(conteudo, encoding="utf-8")

    # 2.5 Gerar script de inicialização unificado (1 clique)
    iniciar_ps1 = pasta_destino / "iniciar.ps1"
    iniciar_ps1.write_text(
        "$host.UI.RawUI.WindowTitle = 'AIDD App Server'\n"
        "Write-Host '==================================================' -ForegroundColor Cyan\n"
        f"Write-Host '🚀 Iniciando {nome_app} no Padrão Ouro AIDD' -ForegroundColor Green\n"
        "Write-Host '==================================================' -ForegroundColor Cyan\n"
        "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd frontend; npm run dev' -WindowStyle Normal\n"
        "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'python src/server.py' -WindowStyle Normal\n"
        "Start-Sleep -Seconds 3\n"
        "Start-Process 'http://localhost:5173/'\n"
        "Start-Process 'http://localhost:3000/docs'\n"
        "Write-Host 'Serviços iniciados com sucesso!' -ForegroundColor Green\n",
        encoding="utf-8"
    )

    iniciar_sh = pasta_destino / "iniciar.sh"
    iniciar_sh.write_text(
        "#!/usr/bin/env bash\n"
        f"echo '🚀 Iniciando {nome_app} no Padrão Ouro AIDD...'\n"
        "(cd frontend && npm run dev) &\n"
        "python src/server.py &\n"
        "sleep 2\n"
        "open http://localhost:5173/ || xdg-open http://localhost:5173/ || true\n"
        "wait\n",
        encoding="utf-8"
    )

    # 3. Opcional: Instalar dependências se solicitado
    if instalar_deps:
        print("📦 Instalando dependências do frontend (npm install)...")
        try:
            subprocess.run(["npm", "install"], cwd=str(frontend_dest), check=True, shell=True)
            print("  ✓ Dependências NPM instaladas com sucesso.")
        except Exception as e:
            print(f"  ⚠ Aviso: Execute 'cd frontend && npm install' manualmente ({e}).")

    print("\n" + "=" * 72)
    print("✨ Aplicação criada com sucesso!")
    print(f"👉 Local: {pasta_destino}")
    print("\nPara rodar agora em 1 clique:")
    print(f"   cd {pasta_destino}")
    print("   .\\iniciar.ps1   (no Windows) ou ./iniciar.sh (no Linux/Mac)")
    print("\nOu manualmente:")
    print("   1. Backend:  python src/server.py        -> http://localhost:3000")
    print("   2. Frontend: cd frontend && npm run dev   -> http://localhost:5173")
    print("=" * 72)
    return 0

def main():
    parser = argparse.ArgumentParser(description="Criador de Aplicações de 1 Clique — Ecossistema AIDD")
    parser.add_argument("nome", nargs="?", default="meu-app-aidd", help="Nome da aplicação a criar")
    parser.add_argument("--fluxo", choices=["pure", "open", "freedom"], default="pure", help="Fluxo canônico da Tríade")
    parser.add_argument("--destino", default=None, help="Diretório de destino personalizado")
    parser.add_argument("--instalar", action="store_true", help="Instala automaticamente pacotes npm")

    args = parser.parse_args()
    return criar_aplicacao(args.nome, fluxo=args.fluxo, destino=args.destino, instalar_deps=args.instalar)

if __name__ == "__main__":
    sys.exit(main() or 0)
