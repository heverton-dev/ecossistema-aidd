# -*- coding: utf-8 -*-
"""
DevOps Packager — Geração determinística de Dockerfile, Docker Compose Standalone
e Docker Compose Swarm (Traefik + GoTrue + PostgREST) com SSL automático para VPS.
"""

import os
from typing import Dict, Any, Optional
from .jwt_generator import JWTGenerator

class DevOpsPackager:
    def __init__(
        self,
        target_dir: str,
        domain: Optional[str] = None,
        traefik_network: str = "network_conexao",
        cert_resolver: str = "letsencryptresolver",
        jwt_secret: Optional[str] = None,
        db_password: Optional[str] = None,
    ):
        self.target_dir = os.path.abspath(target_dir)
        self.domain = domain or "localhost"
        self.traefik_network = traefik_network
        self.cert_resolver = cert_resolver
        self.db_password = db_password or "aidd_secure_vps_pwd_2026"
        self.jwt = JWTGenerator(jwt_secret=jwt_secret) if jwt_secret else JWTGenerator.novo()

    def generate_dockerfile(self) -> str:
        return """# Multi-stage build para SPA Lovable/Vite
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci --prefer-offline || npm install

COPY . .
# .env.production deve existir no diretÃ³rio antes do build:
# contÃ©m VITE_SUPABASE_URL e VITE_SUPABASE_PUBLISHABLE_KEY
# gerado automaticamente por aidd-bridge (generate_env_production)
RUN npm run build

# EstÃ¡gio de ProduÃ§Ã£o com Nginx Alpine
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""

    def generate_nginx_conf(self) -> str:
        return r"""server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    # Cache de assets estÃ¡ticos com hash
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        root /usr/share/nginx/html;
        expires 1y;
        add_header Cache-Control "public, no-transform";
    }

    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
"""

    def generate_docker_compose(self, db_password: str = "aidd_secure_vps_pwd_2026") -> str:
        domain_block = f"""
  caddy:
    image: "caddy:2-alpine"
    container_name: "aidd_caddy_proxy"
    restart: "unless-stopped"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "./Caddyfile:/etc/caddy/Caddyfile:ro"
      - "caddy_data:/data"
      - "caddy_config:/config"
    depends_on:
      - "web"
      - "postgrest"
"""
        return f"""version: '3.8'

services:
  web:
    build:
      context: "."
      dockerfile: "Dockerfile"
    container_name: "aidd_web_app"
    restart: "unless-stopped"
    expose:
      - "80"

  db:
    image: "postgres:16-alpine"
    container_name: "aidd_postgres_db"
    restart: "unless-stopped"
    environment:
      POSTGRES_DB: "app_db"
      POSTGRES_USER: "postgres"
      POSTGRES_PASSWORD: "{db_password}"
    volumes:
      - "postgres_data:/var/lib/postgresql/data"
      - "./init-db.sql:/docker-entrypoint-initdb.d/01-init.sql:ro"
    ports:
      - "127.0.0.1:5432:5432"

  postgrest:
    image: "postgrest/postgrest:latest"
    container_name: "aidd_postgrest_api"
    restart: "unless-stopped"
    environment:
      PGRST_DB_URI: "postgres://postgres:{db_password}@db:5432/app_db"
      PGRST_DB_SCHEMAS: "public"
      PGRST_DB_ANON_ROLE: "anon"
      PGRST_JWT_SECRET: "super-secret-jwt-token-with-at-least-32-chars-long"
    depends_on:
      - "db"
    expose:
      - "3000"
{domain_block}

volumes:
  postgres_data:
  caddy_data:
  caddy_config:
"""

    def generate_docker_compose_swarm(self) -> str:
        app_slug = self.domain.replace(".", "-").replace(":", "-")
        jwt_secret = self.jwt.jwt_secret
        anon_key = self.jwt.anon_key()
        service_key = self.jwt.service_role_key()
        db_password = self.db_password
        protocol = "http" if self.domain == "localhost" else "https"

        return f"""version: '3.8'

services:
  web:
    image: "{app_slug}-web:latest"
    networks:
      - "{self.traefik_network}"
      - "default"
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - "node.role == manager"
      labels:
        - "traefik.enable=1"
        - "traefik.docker.network={self.traefik_network}"
        - "traefik.http.routers.{app_slug}-web.rule=Host(`{self.domain}`)"
        - "traefik.http.routers.{app_slug}-web.entrypoints=websecure"
        - "traefik.http.routers.{app_slug}-web.priority=1"
        - "traefik.http.routers.{app_slug}-web.tls.certresolver={self.cert_resolver}"
        - "traefik.http.routers.{app_slug}-web.service={app_slug}-web"
        - "traefik.http.services.{app_slug}-web.loadbalancer.server.port=80"
        - "traefik.http.services.{app_slug}-web.loadbalancer.passHostHeader=true"

  auth:
    image: "supabase/auth:v2.151.0"
    environment:
      GOTRUE_API_HOST: "0.0.0.0"
      GOTRUE_API_PORT: "9999"
      API_EXTERNAL_URL: "{protocol}://{self.domain}"
      GOTRUE_SITE_URL: "{protocol}://{self.domain}"
      GOTRUE_DB_DRIVER: "postgres"
      GOTRUE_DB_DATABASE_URL: "postgres://postgres:{db_password}@db:5432/app_db?search_path=auth,public"
      GOTRUE_JWT_SECRET: "{jwt_secret}"
      GOTRUE_JWT_EXP: "3600"
      GOTRUE_JWT_DEFAULT_GROUP_NAME: "authenticated"
      GOTRUE_DISABLE_SIGNUP: "false"
      GOTRUE_MAILER_AUTOCONFIRM: "true"
      GOTRUE_SMS_AUTOCONFIRM: "true"
      GOTRUE_OPERATOR_TOKEN: "{service_key}"
    networks:
      - "{self.traefik_network}"
      - "default"
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - "node.role == manager"
      labels:
        - "traefik.enable=1"
        - "traefik.docker.network={self.traefik_network}"
        - "traefik.http.routers.{app_slug}-auth.rule=Host(`{self.domain}`) && PathPrefix(`/auth/v1`)"
        - "traefik.http.routers.{app_slug}-auth.entrypoints=websecure"
        - "traefik.http.routers.{app_slug}-auth.priority=3"
        - "traefik.http.routers.{app_slug}-auth.tls.certresolver={self.cert_resolver}"
        - "traefik.http.routers.{app_slug}-auth.service={app_slug}-auth"
        - "traefik.http.services.{app_slug}-auth.loadbalancer.server.port=9999"
        - "traefik.http.middlewares.{app_slug}-auth-strip.stripprefix.prefixes=/auth/v1"
        - "traefik.http.routers.{app_slug}-auth.middlewares={app_slug}-auth-strip"

  postgrest:
    image: "postgrest/postgrest:latest"
    environment:
      PGRST_DB_URI: "postgres://postgres:{db_password}@db:5432/app_db"
      PGRST_DB_SCHEMAS: "public"
      PGRST_DB_ANON_ROLE: "anon"
      PGRST_JWT_SECRET: "{jwt_secret}"
    networks:
      - "{self.traefik_network}"
      - "default"
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - "node.role == manager"
      labels:
        - "traefik.enable=1"
        - "traefik.docker.network={self.traefik_network}"
        - "traefik.http.routers.{app_slug}-api.rule=Host(`{self.domain}`) && PathPrefix(`/rest/v1`)"
        - "traefik.http.routers.{app_slug}-api.entrypoints=websecure"
        - "traefik.http.routers.{app_slug}-api.priority=2"
        - "traefik.http.routers.{app_slug}-api.tls.certresolver={self.cert_resolver}"
        - "traefik.http.routers.{app_slug}-api.service={app_slug}-api"
        - "traefik.http.services.{app_slug}-api.loadbalancer.server.port=3000"
        - "traefik.http.services.{app_slug}-api.loadbalancer.passHostHeader=true"

  db:
    image: "postgres:16-alpine"
    environment:
      POSTGRES_DB: "app_db"
      POSTGRES_USER: "postgres"
      POSTGRES_PASSWORD: "{db_password}"
    volumes:
      - "{app_slug}_postgres_data:/var/lib/postgresql/data"
    networks:
      - "default"
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - "node.role == manager"

networks:
  {self.traefik_network}:
    external: true
  default:
    driver: overlay

volumes:
  {app_slug}_postgres_data:
"""


    def generate_caddyfile(self) -> str:
        if self.domain == "localhost":
            return """localhost {
    reverse_proxy /rest/v1/* postgrest:3000
    reverse_proxy /* web:80
}
"""
        return f"""{self.domain} {{
    # EmulaÃ§Ã£o do endpoint Supabase REST /rest/v1/
    handle_path /rest/v1/* {{
        reverse_proxy postgrest:3000
    }}

    # Frontend SPA
    handle {{
        reverse_proxy web:80
    }}
}}
"""

    def generate_env_production(self) -> str:
        protocol = "http" if self.domain == "localhost" else "https"
        anon_key = self.jwt.anon_key()
        return (
            "# Variáveis de Produção geradas por aidd-bridge\n"
            "# Vite substitui import.meta.env.VITE_* em build-time usando este arquivo.\n"
            "# ATENÇÃO: NÃO use aspas duplas nos valores — Vite as inclui literalmente.\n"
            f"VITE_SUPABASE_URL={protocol}://{self.domain}\n"
            f"VITE_SUPABASE_PUBLISHABLE_KEY={anon_key}\n"
        )



    def generate_dockerignore(self) -> str:
        """
        Gera .dockerignore seguro para projetos Lovable/Vite.
        Mantém .env.production NO contexto de build (Vite precisa dele).
        Ignora todos os outros .env para evitar vazar credenciais locais.
        """
        return """# Gerado por aidd-bridge — NÃO editar manualmente
node_modules
dist
.git
.github
.lovable
docs
mem
*.md
!README.md
# Ignorar .env locais — mas NÃO .env.production (Vite precisa em build-time)
.env
.env.local
.env.development
.env.test
*.log
coverage
.vscode
.idea
/mnt
"""

    def patch_dockerignore(self) -> str:
        """
        Lê o .dockerignore existente no projeto e remove qualquer regra que
        bloqueie o .env.production. Retorna o conteúdo corrigido.
        """
        dockerignore_path = os.path.join(self.target_dir, ".dockerignore")
        if not os.path.exists(dockerignore_path):
            return self.generate_dockerignore()

        with open(dockerignore_path, encoding="utf-8") as f:
            lines = f.readlines()

        safe_lines = []
        for line in lines:
            stripped = line.strip()
            # Remover regras que bloqueiam .env.production
            if stripped in (".env.*", ".env*") or stripped == "**/.env.*":
                # Substituir por versão segura comentada + regras explícitas
                safe_lines.append("# .env.* substituído por regras explícitas (aidd-bridge)\n")
                safe_lines.append(".env.local\n")
                safe_lines.append(".env.development\n")
                safe_lines.append(".env.test\n")
                safe_lines.append("# .env.production NÃO ignorado — Vite precisa em build-time\n")
            else:
                safe_lines.append(line)

        return "".join(safe_lines)

    def export_all(self) -> Dict[str, str]:
        files_created = {}

        # Corrigir .dockerignore antes de gerar outros arquivos
        dockerignore_content = self.patch_dockerignore()

        targets = {
            ".dockerignore": dockerignore_content,
            "Dockerfile": self.generate_dockerfile(),
            "nginx.conf": self.generate_nginx_conf(),
            "docker-compose.yml": self.generate_docker_compose(),
            "docker-compose.swarm.yml": self.generate_docker_compose_swarm(),
            "Caddyfile": self.generate_caddyfile(),
            ".env.production": self.generate_env_production()
        }

        for filename, content in targets.items():
            dest = os.path.join(self.target_dir, filename)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(content)
            files_created[filename] = dest

        return files_created