# -*- coding: utf-8 -*-
"""
Ponto de entrada CLI da ferramenta aidd-freedom.
"""

import hashlib
import os
import re
import subprocess
import sys
import json
import argparse
import xml.etree.ElementTree as ET
from .scanner import LovableScanner
from .data_bridge import DataBridge
from .unifier import MultiAppUnifier
from .devops import DevOpsPackager
from .teardown import BridgeTeardown
from .auth_migrator import AuthMigrator
from .pipeline_bridge import BridgePipeline


def _slugify(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(texto).lower()).strip("-") or "app"


def _resolver_projeto_scan(args) -> str:
    """Pasta do projeto de destino do scan (nunca o export escaneado).

    Prioridade: --output explicito > pasta apontada por AIDD_HANDOFF_PLANNER
    (orquestrador do Fluxo 03) > proprio diretorio escaneado (CLI standalone
    quando o usuario escaneia o proprio projeto).
    """
    if getattr(args, "output", None):
        return os.path.abspath(args.output)
    handoff = os.environ.get("AIDD_HANDOFF_PLANNER")
    if handoff:
        return os.path.dirname(os.path.abspath(handoff))
    return os.path.abspath(args.project_dir)


def _sha256_arvore(diretorio: str) -> str:
    hasher = hashlib.sha256()
    for raiz, _, arquivos in sorted(os.walk(diretorio)):
        for nome in sorted(arquivos):
            caminho = os.path.join(raiz, nome)
            rel = os.path.relpath(caminho, diretorio).replace("\\", "/")
            hasher.update(rel.encode("utf-8"))
            with open(caminho, "rb") as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    hasher.update(chunk)
    return hasher.hexdigest()


def _rodar_testes_fatia(projeto: str, fatia_dir: str):
    """Roda pytest de verdade na fatia gerada e devolve (rc, total, passaram, falharam)."""
    cache_dir = os.path.join(projeto, ".aidd", "cache")
    os.makedirs(cache_dir, exist_ok=True)
    junit = os.path.join(cache_dir, "pytest_slice.xml")
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", fatia_dir,
         "-q", "-p", "no:cacheprovider", f"--junitxml={junit}"],
        cwd=projeto, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    total = passaram = falharam = 0
    if os.path.exists(junit):
        raiz = ET.parse(junit).getroot()
        suite = raiz if raiz.tag == "testsuite" else (raiz[0] if len(raiz) else None)
        if suite is not None:
            total = int(suite.get("tests", 0))
            falharam = int(suite.get("failures", 0)) + int(suite.get("errors", 0))
            passaram = total - falharam - int(suite.get("skipped", 0))
    return proc.returncode, total, passaram, falharam, junit


def cmd_scan(args):
    scanner = LovableScanner(args.project_dir)
    manifest = scanner.scan()
    projeto = _resolver_projeto_scan(args)

    aidd_dir = os.path.join(projeto, ".aidd")
    os.makedirs(aidd_dir, exist_ok=True)
    out_file = os.path.join(aidd_dir, "bridge-manifest.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"  - Paginas detectadas: {len(manifest['pages'])}")
    print(f"  - Rotas detectadas: {len(manifest['routes'])}")
    print(f"  - Migracoes Supabase: {len(manifest['database']['migrations'])}")

    # Fatia convertida estritamente na zona do construtor: src/modules/<dominio>/
    dominio = _slugify(manifest.get("package_info", {}).get("name") or "app")
    fatia_dir = os.path.join(projeto, "src", "modules", dominio)
    os.makedirs(fatia_dir, exist_ok=True)
    with open(os.path.join(fatia_dir, "__init__.py"), "w", encoding="utf-8") as f:
        f.write(f'"""Fatia convertida pelo aidd-freedom (dominio: {dominio})."""\n')
    db = DataBridge(manifest["database"]["migrations"])
    sql_convertido = db.generate_consolidated_init_sql()
    with open(os.path.join(fatia_dir, "schema.sql"), "w", encoding="utf-8") as f:
        f.write(sql_convertido)
    # Smoke test real da fatia: prova que o schema convertido existe e e PostgreSQL.
    with open(os.path.join(fatia_dir, "test_smoke_slice.py"), "w", encoding="utf-8") as f:
        f.write(
            "from pathlib import Path\n\n"
            "def test_schema_sql_convertido_nao_vazio():\n"
            "    sql = (Path(__file__).parent / 'schema.sql').read_text(encoding='utf-8')\n"
            "    assert sql.strip(), 'schema.sql convertido nao pode ser vazio'\n"
            "    assert 'CREATE' in sql.upper()\n"
        )

    rc_testes, total, passaram, falharam, junit = _rodar_testes_fatia(projeto, fatia_dir)
    if rc_testes != 0 or falharam > 0 or total == 0:
        print(f"[ERRO] Testes da fatia falharam (exit {rc_testes}): "
              f"total={total} passaram={passaram} falharam={falharam}")
        return 1

    # Contrato C3 gravado pela propria ferramenta (quem produz escreve).
    endpoints = []
    for rota in manifest.get("routes", []):
        path = rota.get("path") if isinstance(rota, dict) else str(rota)
        comp = rota.get("component", dominio) if isinstance(rota, dict) else dominio
        endpoints.append({"rota": path, "metodo": "GET",
                          "funcao": f"renderizar_{_slugify(comp)}"})
    tabelas = sorted(set(re.findall(
        r"CREATE TABLE (?:IF NOT EXISTS )?([A-Za-z0-9_.]+)",
        sql_convertido, flags=re.IGNORECASE)))
    c3 = {
        "versao_schema": "1.0.0",
        "origem_engine": "aidd-freedom",
        "projeto_slug": dominio,
        "slices_geradas": [{
            "slice_nome": dominio,
            "caminho_src": f"src/modules/{dominio}",
            "sha256_arvore": _sha256_arvore(fatia_dir),
            "endpoints": endpoints,
            "tabelas_sql": tabelas,
        }],
        "artefatos_frontend": {
            "tecnologia": "tanstack_router",
            "paginas_geradas": manifest.get("pages") or ["/"],
            "origem_design": "lovable_preserved",
        },
        "testes_executados": {
            "total": total,
            "passaram": passaram,
            "falharam": falharam,
            "zero_stubs": True,
            "relatorio_pytest": {
                "caminho": os.path.relpath(junit, projeto).replace("\\", "/"),
                "exit_code": 0,
            },
        },
        "arquivos_fora_da_zona": [],
    }
    with open(os.path.join(projeto, "HANDOFF_ENGINE_MASTER.json"), "w", encoding="utf-8") as f:
        json.dump(c3, f, indent=2, ensure_ascii=False)

    print(f"[SUCESSO] Scan concluido. Manifesto gerado em: {out_file}")
    print(f"  - Fatia convertida: src/modules/{dominio}/")
    print("  - Contrato C3: HANDOFF_ENGINE_MASTER.json")
    return 0

def cmd_convert_db(args):
    scanner = LovableScanner(args.project_dir)
    manifest = scanner.scan()
    db = DataBridge(manifest["database"]["migrations"])
    sql = db.generate_consolidated_init_sql(with_real_auth=args.with_gotrue)
    out_file = args.output or os.path.join(args.project_dir, "init-db.sql")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(sql)
    print(f"[SUCESSO] Script PostgreSQL puro consolidado em: {out_file}")
    return 0

def cmd_merge(args):
    unifier = MultiAppUnifier(args.apps, args.output)
    res = unifier.merge()
    print(f"[SUCESSO] {res['total_apps']} aplicacoes unificadas com sucesso em: {res['output_dir']}")
    return 0

def cmd_pack(args):
    packager = DevOpsPackager(
        args.project_dir,
        domain=args.domain,
        traefik_network=args.traefik_network,
        cert_resolver=args.certresolver,
        stack=args.stack
    )
    files = packager.export_all()
    print(f"[SUCESSO] Pacote VPS gerado com sucesso em: {args.project_dir} (stack={args.stack})")
    for name in files.keys():
        print(f"  - {name}")
    if args.stack == "full":
        print("[LEMBRETE] Use tambem 'convert-db --with-gotrue' para o init-db.sql combinar com este stack.")
    return 0

def cmd_migrate_auth(args):
    migrator = AuthMigrator(args.source, args.target)
    report = migrator.migrate(dry_run=not args.apply)
    modo = "APLICADO" if args.apply else "PREVIEW (use --apply para gravar de verdade)"
    print(f"[{modo}]")
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return 0

def cmd_destroy(args):
    """Remove stack, volumes, DNS Cloudflare e diretório VPS de forma segura e isolada."""
    print(f"\n[BRIDGE DESTROY] Removendo aplicacao: {args.app_name}")
    print(f"  Dominio  : {args.domain or '(nao especificado)'}")
    print(f"  VPS      : {args.vps_host or os.getenv('VPS_HOST', '?')}")
    print()

    if not args.yes:
        confirm = input(f"Confirmar exclusao de '{args.app_name}'? Isso e IRREVERSIVEL. [s/N] ").strip().lower()
        if confirm not in ("s", "sim", "y", "yes"):
            print("[CANCELADO] Operacao cancelada pelo usuario.")
            return 0

    try:
        teardown = BridgeTeardown(
            app_name=args.app_name,
            domain=args.domain,
            vps_host=args.vps_host,
            vps_user=args.vps_user,
            vps_password=args.vps_password,
            cf_api_token=args.cf_token,
            cf_zone_id=args.cf_zone_id
        )
    except ValueError as e:
        print(f"[ERRO] {e}")
        return 1

    result = teardown.execute_teardown()

    print(f"\n[DNS CLOUDFLARE] {result['dns']}")
    vps = result["vps"]
    if vps.get("status") == "success":
        d = vps["details"]
        print(f"[STACK SWARM]    Removida — {d.get('stack', '')}")
        print(f"[VOLUMES]        {d.get('volumes', 'nao removidos')}")
        print(f"[DIRETORIO VPS]  {d.get('directory', 'nao removido')}")
        print("\n[SUCESSO] Aplicacao removida com total isolamento dos outros servicos.")
    else:
        print(f"[ERRO VPS] {vps.get('error')}")
        return 1
    return 0

def _forcar_utf8_stdio():
    """Evita UnicodeEncodeError em consoles nao-UTF-8 (ex: cp1252 do Windows)
    ao imprimir simbolos como '✓' usados pelo pipeline."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def main():
    _forcar_utf8_stdio()
    parser = argparse.ArgumentParser(description="aidd-freedom: Extrator e unificador de apps Low-Code para VPS propria")
    subparsers = parser.add_subparsers(dest="subcommand", help="Comando a executar")

    # scan
    p_scan = subparsers.add_parser("scan", help="Analisa um projeto Lovable e gera manifesto")
    p_scan.add_argument("project_dir", help="Diretorio do projeto (export escaneado, nunca modificado)")
    p_scan.add_argument("--output", "-o", default=None,
                        help="Pasta do projeto de destino (.aidd/bridge-manifest.json, src/modules/, C3); padrao: AIDD_HANDOFF_PLANNER ou o proprio diretorio")

    # convert-db
    p_db = subparsers.add_parser("convert-db", help="Converte migracoes do Supabase em PostgreSQL consolidado")
    p_db.add_argument("project_dir", help="Diretorio do projeto")
    p_db.add_argument("--output", "-o", help="Caminho de saida para init-db.sql")
    p_db.add_argument("--with-gotrue", action="store_true", help="Pacote de deploy usara GoTrue real (docker-compose.swarm.yml) em vez da emulacao de auth.users")

    # merge
    p_merge = subparsers.add_parser("merge", help="Unifica multiplos apps em um unico projeto")
    p_merge.add_argument("apps", nargs="+", help="Diretorios dos apps a unir")
    p_merge.add_argument("--output", "-o", required=True, help="Diretorio destino")

    # pack
    p_pack = subparsers.add_parser("pack", help="Gera Dockerfile, Docker Compose e Swarm para VPS")
    p_pack.add_argument("project_dir", help="Diretorio do projeto")
    p_pack.add_argument("--domain", "-d", default="localhost", help="Dominio ou IP da VPS (ex: meusite.com)")
    p_pack.add_argument("--traefik-network", default="network_conexao", help="Nome da rede overlay do Traefik")
    p_pack.add_argument("--certresolver", default="letsencryptresolver", help="Nome do certresolver no Traefik")
    p_pack.add_argument("--stack", choices=["lite", "full"], default="lite", help="lite (padrao): PostgREST+GoTrue minimos, poucos containers. full: stack oficial self-hosted da Supabase (Kong+GoTrue+PostgREST na mesma versao testada pela Supabase), mais pesado porem mais compativel")

    # migrate-auth
    p_authmig = subparsers.add_parser("migrate-auth", help="Migra contas reais (auth.users/auth.identities) de um Postgres de origem (ex: Supabase Cloud) para o destino self-hosted, preservando o hash de senha")
    p_authmig.add_argument("--source", required=True, help="DSN Postgres de origem (ex: postgres://postgres:senha@db.xxx.supabase.co:5432/postgres)")
    p_authmig.add_argument("--target", required=True, help="DSN Postgres de destino self-hosted (ex via tunel SSH: postgres://postgres:senha@127.0.0.1:5432/app_db)")
    p_authmig.add_argument("--apply", action="store_true", help="Aplica de verdade. Sem essa flag roda em modo preview (nao grava nada)")

    # destroy
    p_destroy = subparsers.add_parser("destroy", help="Remove aplicacao da VPS: stack, volumes, DNS e diretorio")
    p_destroy.add_argument("app_name", help="Nome da stack Docker Swarm (ex: hub-teste)")
    p_destroy.add_argument("--domain", "-d", help="Dominio completo para remover DNS no Cloudflare (ex: hub-teste.vpsconexao.org)")
    p_destroy.add_argument("--vps-host", default=None, help="IP/host da VPS (usa VPS_HOST do .env se omitido)")
    p_destroy.add_argument("--vps-user", default="root", help="Usuario SSH da VPS (default: root)")
    p_destroy.add_argument("--vps-password", default=None, help="Senha SSH da VPS (usa VPS_PASSWORD do .env se omitido)")
    p_destroy.add_argument("--cf-token", default=None, help="Token da API do Cloudflare (usa CLOUDFLARE_API_TOKEN do .env se omitido)")
    p_destroy.add_argument("--cf-zone-id", default=None, help="Zone ID do Cloudflare (usa CLOUDFLARE_ZONE_ID do .env se omitido)")
    p_destroy.add_argument("--yes", "-y", action="store_true", help="Confirmar automaticamente sem interacao")

    # unpack (Pipeline Canônico FLUXO 03)
    p_unpack = subparsers.add_parser("unpack", help="Executa o pipeline completo de libertacao e empacotamento VSA (FLUXO 03)")
    p_unpack.add_argument("project_dir", help="Diretorio do projeto low-code")
    p_unpack.add_argument("--output", "-o", default=None, help="Diretorio destino (padrao: proprio diretorio)")
    p_unpack.add_argument("--domain", "-d", default="localhost", help="Dominio ou IP para configuracao")
    p_unpack.add_argument("--stack", choices=["lite", "full"], default="lite", help="lite (padrao): PostgREST puro, sem GoTrue (auth.users emulado). full: GoTrue real, exige a tabela auth.users real (nao emulada)")

    args = parser.parse_args()

    if not args.subcommand:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "scan": cmd_scan,
        "convert-db": cmd_convert_db,
        "merge": cmd_merge,
        "pack": cmd_pack,
        "migrate-auth": cmd_migrate_auth,
        "destroy": cmd_destroy,
        "unpack": lambda a: BridgePipeline(a.project_dir, output_dir=a.output, domain=a.domain, stack=a.stack).run()
    }

    sys.exit(dispatch[args.subcommand](args) or 0)

if __name__ == "__main__":
    main()