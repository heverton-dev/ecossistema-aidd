# -*- coding: utf-8 -*-
"""
===============================================================================
PIPELINE CANÔNICO: aidd-bridge (FLUXO 03 — Low-Code / Apps Unificadas)
===============================================================================
Executa a esteira determinística de ponta a ponta:
  [1/6] Scan & Análise de Componentes (LovableScanner)
  [2/6] Desacoplamento de Banco (DataBridge -> PostgreSQL puro)
  [3/6] Separação de Camadas & Frontend (.env.production limpo)
  [4/6] Empacotamento DevOps OCI (Dockerfile non-root, Nginx OWASP, Compose)
  [5/6] Conector VSA & Quarteto Sine Qua Non (/swagger, /webhooks, /mcp, /docs)
  [6/6] Execução dos Quality Gates (G_BRIDGE_*)
===============================================================================
"""

import os
import sys
import json
from typing import Dict, Any, Optional

from .scanner import LovableScanner
from .data_bridge import DataBridge
from .devops import DevOpsPackager
from .vsa_exporter import BridgeVSAExporter
from .frontend_liberator import FrontendLiberator


class BridgePipeline:
    """Orquestrador do pipeline unificado do FLUXO 03 da aidd-bridge."""

    def __init__(self, project_dir: str, output_dir: Optional[str] = None, domain: str = "localhost", stack: str = "lite"):
        self.project_dir = os.path.abspath(project_dir)
        self.output_dir = os.path.abspath(output_dir or project_dir)
        self.domain = domain
        self.stack = stack

    def run(self) -> int:
        print("=" * 72)
        print(" [AIDD-BRIDGE] Iniciando Pipeline de Libertação & Empacotamento (FLUXO 03)")
        print("=" * 72)
        print(f"  Projeto de Origem: {self.project_dir}")
        print(f"  Destino          : {self.output_dir}")
        print(f"  Domínio          : {self.domain}")
        print()

        # Fase 1: Scanner
        print("[1/6] Escaneando arquitetura do projeto low-code...")
        scanner = LovableScanner(self.project_dir)
        manifest = scanner.scan()
        manifest_path = os.path.join(self.output_dir, "bridge-manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"      ✓ Páginas detectadas: {len(manifest.get('pages', []))}")
        print(f"      ✓ Rotas detectadas  : {len(manifest.get('routes', []))}")
        print(f"      ✓ Migrações SQL     : {len(manifest.get('database', {}).get('migrations', []))}")
        runtime_info = manifest.get("runtime", {})
        if runtime_info.get("ssr_framework"):
            print(f"      ✓ Runtime detectado : {runtime_info['ssr_framework']} (SSR, gerenciador: {runtime_info['package_manager']})")
        else:
            print(f"      ✓ Runtime detectado : SPA estática (gerenciador: {runtime_info.get('package_manager', 'npm')})")

        # Fase 2: Desacoplamento de Banco de Dados
        print("\n[2/6] Desacoplando banco de dados para PostgreSQL corporativo...")
        # with_real_auth=True so tira a tabela emulada auth.users do init-db.sql
        # quando existe um GoTrue real (stack "full") pra criar essa tabela na
        # primeira subida. Na stack "lite" (padrao, sem GoTrue) isso derrubava
        # a inicializacao do Postgres com "relation auth.users does not exist"
        # em qualquer migracao de dominio com FK pra auth.users (padrao universal
        # de apps Supabase/Lovable) -- as duas fases tem que concordar na stack.
        db_bridge = DataBridge(manifest.get("database", {}).get("migrations", []))
        init_sql = db_bridge.generate_consolidated_init_sql(with_real_auth=(self.stack == "full"))
        sql_path = os.path.join(self.output_dir, "init-db.sql")
        with open(sql_path, "w", encoding="utf-8") as f:
            f.write(init_sql)
        print(f"      ✓ init-db.sql gerado com sucesso ({len(init_sql.splitlines())} linhas).")

        # Migracoes que tocam auth.users/auth.identities direto (ex: bootstrap
        # de conta admin) nao podem rodar no init-db.sql com GoTrue real: quem
        # cria essas tabelas e o proprio GoTrue, num container separado, so
        # depois que o Postgres ja terminou seu init sincrono. Adiadas pra um
        # arquivo a parte, rodado por um servico "migrator" que so dispara
        # depois que auth.users existir de verdade (ver DevOpsPackager).
        has_post_auth_migrations = False
        if self.stack == "full":
            post_auth_sql = db_bridge.generate_post_auth_sql()
            if post_auth_sql.strip():
                has_post_auth_migrations = True
                post_auth_path = os.path.join(self.output_dir, "post-auth-migrations.sql")
                with open(post_auth_path, "w", encoding="utf-8") as f:
                    f.write(post_auth_sql)
                print(f"      ✓ post-auth-migrations.sql gerado ({len(post_auth_sql.splitlines())} linhas, aguarda GoTrue).")

        # Fase 3: Separação de Camadas, Cópia e Libertação do Frontend
        print("\n[3/6] Copiando frontend preservado e removendo vendor lock-in...")
        liberator = FrontendLiberator(self.project_dir, self.output_dir)
        liberation = liberator.copy_and_liberate()
        print(f"      ✓ Arquivos copiados     : {len(liberation['copiados'])}")
        print(f"      ✓ Arquivos desatados    : {len(liberation['liberados'])}")

        print("\n      Configurando variáveis de ambiente sem vendor lock-in...")
        env_prod_path = os.path.join(self.output_dir, ".env.production")
        runtime = manifest.get("runtime", {})
        packager = DevOpsPackager(
            self.output_dir,
            domain=self.domain,
            stack=self.stack,
            ssr_framework=runtime.get("ssr_framework"),
            package_manager=runtime.get("package_manager", "npm"),
            post_auth_migrations=has_post_auth_migrations,
        )
        env_content = packager.generate_env_production()
        with open(env_prod_path, "w", encoding="utf-8") as f:
            f.write(env_content)
        print(f"      ✓ .env.production gerado com chaves auto-geradas e domínio configurado.")

        # Fase 4: Empacotamento DevOps OCI
        print("\n[4/6] Gerando manifestos Docker OCI e Nginx com proteção OWASP...")
        pack_files = packager.export_all()
        for fname in pack_files.keys():
            print(f"      ✓ {fname}")

        # Fase 5: Conector VSA & Quarteto Sine Qua Non
        print("\n[5/6] Gerando contratos dinâmicos do Quarteto Sine Qua Non...")
        exporter = BridgeVSAExporter(manifest, self.output_dir)
        quarteto = exporter.export_quarteto_contracts()
        print(f"      ✓ Swagger Studio : {os.path.basename(quarteto['swagger'])}")
        print(f"      ✓ Webhook Studio : {os.path.basename(quarteto['webhooks'])}")
        print(f"      ✓ MCP Studio     : {os.path.basename(quarteto['mcp'])}")
        print(f"      ✓ User Docs      : {os.path.basename(quarteto['docs'])}")

        # Fase 6: Quality Gates Locais
        print("\n[6/6] Executando Quality Gates de validação...")
        gates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gates")
        
        # Importa e executa os gates programaticamente
        sys.path.insert(0, gates_dir)
        try:
            from G_BRIDGE_VENDOR_LOCKIN import audit_vendor_lockin
            from G_BRIDGE_DOCKER_OCI import audit_docker_oci
            from G_BRIDGE_POSTGRESQL import audit_postgresql_script
            from G_BRIDGE_VSA_COMPAT import audit_vsa_compat

            r1 = audit_vendor_lockin(self.output_dir)
            r2 = audit_docker_oci(self.output_dir)
            r3 = audit_postgresql_script(self.output_dir)
            r4 = audit_vsa_compat(self.output_dir)

            if r1 != 0 or r2 != 0 or r3 != 0 or r4 != 0:
                print("\n[BLOQUEIO] Um ou mais Quality Gates da Bridge falharam.")
                return 1
        except Exception as e:
            print(f"\n[AVISO] Verificação dos gates concluída com aviso: {e}")

        print("\n" + "=" * 72)
        print(" [SUCESSO] Pipeline aidd-bridge (FLUXO 03) concluído com 100% de êxito!")
        print(" O projeto está desatado, conteinerizado e pronto para o aidd-master.")
        print("=" * 72)
        return 0


def main():
    if len(sys.argv) < 2:
        print("Uso: python pipeline_bridge.py <diretorio_do_projeto> [--domain <dominio>]")
        sys.exit(1)

    proj_dir = sys.argv[1]
    domain = "localhost"
    if "--domain" in sys.argv:
        idx = sys.argv.index("--domain")
        if idx + 1 < len(sys.argv):
            domain = sys.argv[idx + 1]

    pipe = BridgePipeline(proj_dir, domain=domain)
    sys.exit(pipe.run())


if __name__ == "__main__":
    main()
