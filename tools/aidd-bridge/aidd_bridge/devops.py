# -*- coding: utf-8 -*-
"""
DevOps Packager — Geração determinística de Dockerfile, Docker Compose,
Nginx SPA e Proxy Reverso Caddy/Traefik com SSL automático para VPS.
"""

import os
from typing import Dict, Any, Optional

class DevOpsPackager:
    def __init__(self, target_dir: str, domain: Optional[str] = None):
        self.target_dir = os.path.abspath(target_dir)
        self.domain = domain or "localhost"

    def generate_dockerfile(self) -> str:
        return """# Multi-stage build para SPA Lovable/Vite
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci --prefer-offline || npm install

COPY . .
RUN npm run build

# Estágio de Produção com Nginx Alpine
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""

    def generate_nginx_conf(self) -> str:
        return """server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    # Cache de assets estáticos com hash
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
    image: caddy:2-alpine
    container_name: aidd_caddy_proxy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - web
      - postgrest
"""
        return f"""version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: aidd_web_app
    restart: unless-stopped
    expose:
      - "80"

  db:
    image: postgres:16-alpine
    container_name: aidd_postgres_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: app_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: {db_password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/01-init.sql:ro
    ports:
      - "127.0.0.1:5432:5432"

  postgrest:
    image: postgrest/postgrest:latest
    container_name: aidd_postgrest_api
    restart: unless-stopped
    environment:
      PGRST_DB_URI: postgres://authenticator:aidd_authenticator_pwd@db:5432/app_db
      PGRST_DB_SCHEMAS: public
      PGRST_DB_ANON_ROLE: anon
      PGRST_JWT_SECRET: "super-secret-jwt-token-with-at-least-32-chars-long"
    depends_on:
      - db
    expose:
      - "3000"
{domain_block}

volumes:
  postgres_data:
  caddy_data:
  caddy_config:
"""

    def generate_caddyfile(self) -> str:
        if self.domain == "localhost":
            return """localhost {
    reverse_proxy /rest/v1/* postgrest:3000
    reverse_proxy /* web:80
}
"""
        return f"""{self.domain} {{
    # Emulação do endpoint Supabase REST /rest/v1/
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
        return f"""# Variáveis de Produção geradas por aidd-bridge
VITE_SUPABASE_URL={protocol}://{self.domain}
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy_anon_key
POSTGRES_PASSWORD=aidd_secure_vps_pwd_2026
DOMAIN={self.domain}
"""

    def export_all(self) -> Dict[str, str]:
        files_created = {}

        targets = {
            "Dockerfile": self.generate_dockerfile(),
            "nginx.conf": self.generate_nginx_conf(),
            "docker-compose.yml": self.generate_docker_compose(),
            "Caddyfile": self.generate_caddyfile(),
            ".env.production": self.generate_env_production()
        }

        for filename, content in targets.items():
            dest = os.path.join(self.target_dir, filename)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(content)
            files_created[filename] = dest

        return files_created