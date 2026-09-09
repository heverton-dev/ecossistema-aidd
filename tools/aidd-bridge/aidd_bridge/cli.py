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
    sql = db.generate_consolidated_init_sql()
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
    packager = DevOpsPackager(args.project_dir, domain=args.domain)
    files = packager.export_all()
    print(f"[SUCESSO] Pacote VPS gerado com sucesso em: {args.project_dir}")
    for name, path in files.items():
        print(f"  - {name}")
    return 0

def main():
    parser = argparse.ArgumentParser(description="aidd-bridge: Extrator e unificador de apps Low-Code para VPS própria")
    subparsers = parser.add_subparsers(dest="subcommand", help="Comando a executar")

    # scan
    p_scan = subparsers.add_parser("scan", help="Analisa um projeto Lovable e gera manifesto")
    p_scan.add_argument("project_dir", help="Diretório do projeto")

    # convert-db
    p_db = subparsers.add_parser("convert-db", help="Converte migrações do Supabase em PostgreSQL consolidado")
    p_db.add_argument("project_dir", help="Diretório do projeto")
    p_db.add_argument("--output", "-o", help="Caminho de saída para init-db.sql")

    # merge
    p_merge = subparsers.add_parser("merge", help="Unifica múltiplos apps em um único projeto")
    p_merge.add_argument("apps", nargs="+", help="Diretórios dos apps a unir")
    p_merge.add_argument("--output", "-o", required=True, help="Diretório destino")

    # pack
    p_pack = subparsers.add_parser("pack", help="Gera Dockerfile, Docker Compose e Proxy SSL para VPS")
    p_pack.add_argument("project_dir", help="Diretório do projeto")
    p_pack.add_argument("--domain", "-d", default="localhost", help="Domínio ou IP da VPS (ex: meusite.com)")

    args = parser.parse_args()

    if not args.subcommand:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "scan": cmd_scan,
        "convert-db": cmd_convert_db,
        "merge": cmd_merge,
        "pack": cmd_pack
    }

    sys.exit(dispatch[args.subcommand](args) or 0)

if __name__ == "__main__":
    main()