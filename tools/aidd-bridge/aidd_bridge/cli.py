# -*- coding: utf-8 -*-
"""
Ponto de entrada CLI da ferramenta aidd-bridge.
"""

import os
import sys
import json
import argparse
from .scanner import LovableScanner
from .data_bridge import DataBridge
from .unifier import MultiAppUnifier
from .devops import DevOpsPackager
from .teardown import BridgeTeardown
from .auth_migrator import AuthMigrator

def cmd_scan(args):
    scanner = LovableScanner(args.project_dir)
    manifest = scanner.scan()
    out_file = os.path.join(args.project_dir, "bridge-manifest.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"[SUCESSO] Scan concluido. Manifesto gerado em: {out_file}")
    print(f"  - Paginas detectadas: {len(manifest['pages'])}")
    print(f"  - Rotas detectadas: {len(manifest['routes'])}")
    print(f"  - Migracoes Supabase: {len(manifest['database']['migrations'])}")
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

    teardown = BridgeTeardown(
        app_name=args.app_name,
        domain=args.domain,
        vps_host=args.vps_host,
        vps_user=args.vps_user,
        vps_password=args.vps_password,
        cf_api_token=args.cf_token,
        cf_zone_id=args.cf_zone_id
    )

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

def main():
    parser = argparse.ArgumentParser(description="aidd-bridge: Extrator e unificador de apps Low-Code para VPS propria")
    subparsers = parser.add_subparsers(dest="subcommand", help="Comando a executar")

    # scan
    p_scan = subparsers.add_parser("scan", help="Analisa um projeto Lovable e gera manifesto")
    p_scan.add_argument("project_dir", help="Diretorio do projeto")

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
        "destroy": cmd_destroy
    }

    sys.exit(dispatch[args.subcommand](args) or 0)

if __name__ == "__main__":
    main()