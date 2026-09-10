# -*- coding: utf-8 -*-
"""
DevOps Packager — Geração determinística de Dockerfile, Docker Compose Standalone
e Docker Compose Swarm (Traefik + GoTrue + PostgREST) com SSL automático para VPS.
"""

import os
from typing import Dict, Any, Optional
from .jwt_generator import JWTGenerator

class DevOpsPackager:
    # Versões testadas manualmente (docker pull real) em 2026-09-10 — nunca usar
    # ":latest" nas imagens do stack completo, senão uma atualização upstream
    # pode quebrar a compatibilidade de um dia para o outro sem aviso.
    FULL_STACK_IMAGES = {
        "db": "supabase/postgres:15.14.1.170",
        "auth": "supabase/gotrue:v2.197.0",
        "kong": "kong:3.8.0",
        "storage": "supabase/storage-api:v1.75.0",
        "functions": "supabase/edge-runtime:v1.76.2",
    }

    def __init__(
        self,
        target_dir: str,
        domain: Optional[str] = None,
        traefik_network: str = "network_conexao",
        cert_resolver: str = "letsencryptresolver",
        jwt_secret: Optional[str] = None,
        db_password: Optional[str] = None,
        stack: str = "lite",
    ):
        if stack not in ("lite", "full"):
            raise ValueError(f'stack deve ser "lite" ou "full", recebido: {stack!r}')
        self.target_dir = os.path.abspath(target_dir)
        self.domain = domain or "localhost"
        self.traefik_network = traefik_network
        self.cert_resolver = cert_resolver
        self.db_password = db_password or "aidd_secure_vps_pwd_2026"
        self.jwt = JWTGenerator(jwt_secret=jwt_secret) if jwt_secret else JWTGenerator.novo()
        self.stack = stack
        self.functions = self._detect_edge_functions()

    def _detect_edge_functions(self) -> "list[str]":
        """
        Detecta automaticamente Supabase Edge Functions reais do projeto
        (supabase/functions/<nome>/index.ts, exceto "main"/"_shared") para
        decidir sozinho se o serviço de funções entra no pacote — sem
        precisar de uma flag manual do usuário.
        """
        functions_dir = os.path.join(self.target_dir, "supabase", "functions")
        functions = []
        if os.path.isdir(functions_dir):
            for name in sorted(os.listdir(functions_dir)):
                if name in ("main", "_shared") or name.startswith("."):
                    continue
                full = os.path.join(functions_dir, name)
                if os.path.isdir(full) and os.path.exists(os.path.join(full, "index.ts")):
                    functions.append(name)
        return functions

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
        # Mesmo segredo/senha usados no resto do pacote (.env.production,
        # docker-compose.swarm.yml) — antes este arquivo usava um JWT secret
        # fixo diferente do gerado por self.jwt, então nenhum token emitido
        # pela ferramenta validava contra este PostgREST. Corrigido junto
        # com a adição do Storage em 2026-09-10.
        jwt_secret = self.jwt.jwt_secret
        anon_key = self.jwt.anon_key()
        service_key = self.jwt.service_role_key()
        functions_block = ""
        functions_depends = ""
        if self.functions:
            functions_depends = '\n      - "functions"'
            functions_block = f"""
  functions:
    image: "{self.FULL_STACK_IMAGES['functions']}"
    container_name: "aidd_edge_functions"
    restart: "unless-stopped"
    command:
      - "start"
      - "--main-service"
      - "/home/deno/functions/main"
    environment:
      SUPABASE_URL: "http://caddy:80"
      SUPABASE_ANON_KEY: "{anon_key}"
      SUPABASE_SERVICE_ROLE_KEY: "{service_key}"
      SUPABASE_DB_URL: "postgres://postgres:{db_password}@db:5432/app_db"
    volumes:
      - "./supabase/functions:/home/deno/functions:ro"
    depends_on:
      - "db"
    expose:
      - "9000"
"""
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
      - "storage"{functions_depends}
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
      PGRST_JWT_SECRET: "{jwt_secret}"
      PGRST_DB_USE_LEGACY_GUCS: "true"
    depends_on:
      - "db"
    expose:
      - "3000"

  storage:
    image: "{self.FULL_STACK_IMAGES['storage']}"
    container_name: "aidd_storage_api"
    restart: "unless-stopped"
    environment:
      ANON_KEY: "{anon_key}"
      SERVICE_KEY: "{service_key}"
      POSTGREST_URL: "http://postgrest:3000"
      PGRST_JWT_SECRET: "{jwt_secret}"
      DATABASE_URL: "postgres://postgres:{db_password}@db:5432/app_db"
      FILE_SIZE_LIMIT: "52428800"
      STORAGE_BACKEND: "file"
      FILE_STORAGE_BACKEND_PATH: "/var/lib/storage"
      TENANT_ID: "stub"
      REGION: "stub"
      GLOBAL_S3_BUCKET: "stub"
      ENABLE_IMAGE_TRANSFORMATION: "false"
    volumes:
      - "storage_data:/var/lib/storage"
    depends_on:
      - "db"
    expose:
      - "5000"
{functions_block}{domain_block}

volumes:
  postgres_data:
  storage_data:
  caddy_data:
  caddy_config:
"""

    def generate_docker_compose_swarm(self) -> str:
        """
        Gera o docker-compose.swarm.yml. Modo "lite" (padrão): PostgREST puro
        + GoTrue com Traefik roteando cada serviço direto (stripprefix manual
        por rota). Modo "full": stack oficial self-hosted da Supabase (Kong
        na frente, imagens supabase/*), mais fiel ao Supabase Cloud e sem essa
        reimplementação manual do roteamento — ao custo de mais contêineres.
        """
        if self.stack == "full":
            return self._generate_swarm_full()
        return self._generate_swarm_lite()

    def _generate_swarm_lite(self) -> str:
        app_slug = self.domain.replace(".", "-").replace(":", "-")
        jwt_secret = self.jwt.jwt_secret
        anon_key = self.jwt.anon_key()
        service_key = self.jwt.service_role_key()
        db_password = self.db_password
        protocol = "http" if self.domain == "localhost" else "https"
        functions_service = ""
        if self.functions:
            functions_service = f"""
  functions:
    image: "{self.FULL_STACK_IMAGES['functions']}"
    command:
      - "start"
      - "--main-service"
      - "/home/deno/functions/main"
    environment:
      SUPABASE_URL: "{protocol}://{self.domain}"
      SUPABASE_ANON_KEY: "{anon_key}"
      SUPABASE_SERVICE_ROLE_KEY: "{service_key}"
      SUPABASE_DB_URL: "postgres://postgres:{db_password}@db:5432/app_db"
    volumes:
      - "./supabase/functions:/home/deno/functions:ro"
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
        - "traefik.http.routers.{app_slug}-functions.rule=Host(`{self.domain}`) && PathPrefix(`/functions/v1`)"
        - "traefik.http.routers.{app_slug}-functions.entrypoints=websecure"
        - "traefik.http.routers.{app_slug}-functions.priority=5"
        - "traefik.http.routers.{app_slug}-functions.tls.certresolver={self.cert_resolver}"
        - "traefik.http.routers.{app_slug}-functions.service={app_slug}-functions"
        - "traefik.http.services.{app_slug}-functions.loadbalancer.server.port=9000"
        - "traefik.http.middlewares.{app_slug}-functions-strip.stripprefix.prefixes=/functions/v1"
        - "traefik.http.routers.{app_slug}-functions.middlewares={app_slug}-functions-strip"
"""

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
      PGRST_DB_USE_LEGACY_GUCS: "true"
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
        - "traefik.http.middlewares.{app_slug}-api-strip.stripprefix.prefixes=/rest/v1"
        - "traefik.http.routers.{app_slug}-api.middlewares={app_slug}-api-strip"

  storage:
    image: "{self.FULL_STACK_IMAGES['storage']}"
    environment:
      ANON_KEY: "{anon_key}"
      SERVICE_KEY: "{service_key}"
      POSTGREST_URL: "http://postgrest:3000"
      PGRST_JWT_SECRET: "{jwt_secret}"
      DATABASE_URL: "postgres://postgres:{db_password}@db:5432/app_db"
      FILE_SIZE_LIMIT: "52428800"
      STORAGE_BACKEND: "file"
      FILE_STORAGE_BACKEND_PATH: "/var/lib/storage"
      TENANT_ID: "{app_slug}"
      REGION: "stub"
      GLOBAL_S3_BUCKET: "stub"
      ENABLE_IMAGE_TRANSFORMATION: "false"
    volumes:
      - "{app_slug}_storage_data:/var/lib/storage"
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
        - "traefik.http.routers.{app_slug}-storage.rule=Host(`{self.domain}`) && PathPrefix(`/storage/v1`)"
        - "traefik.http.routers.{app_slug}-storage.entrypoints=websecure"
        - "traefik.http.routers.{app_slug}-storage.priority=4"
        - "traefik.http.routers.{app_slug}-storage.tls.certresolver={self.cert_resolver}"
        - "traefik.http.routers.{app_slug}-storage.service={app_slug}-storage"
        - "traefik.http.services.{app_slug}-storage.loadbalancer.server.port=5000"
        - "traefik.http.middlewares.{app_slug}-storage-strip.stripprefix.prefixes=/storage/v1"
        - "traefik.http.routers.{app_slug}-storage.middlewares={app_slug}-storage-strip"
{functions_service}
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
  {app_slug}_storage_data:
"""

    @staticmethod
    def _kong_entrypoint_yaml() -> str:
        """
        Valor YAML (já escapado) do entrypoint que injeta
        ${SUPABASE_ANON_KEY}/${SUPABASE_SERVICE_KEY} no kong.yml antes de
        subir o Kong. Construído por código (não digitado à mão dentro do
        template) porque tem 3 camadas de escaping (YAML > bash > eval) —
        verificado com um deploy real e descartável em 2026-09-10.
        Usa /tmp em vez de ~ (home do usuário "kong") porque a home não
        existe por padrão nessa imagem e não é gravável pelo uid não-root.
        """
        raw = (
            "bash -c "
            + chr(39)
            + 'eval "echo \\"$$(cat /tmp/temp.yml)\\"" > /tmp/kong.yml '
            + "&& /docker-entrypoint.sh kong docker-start"
            + chr(39)
        )
        return chr(39) + raw.replace(chr(39), chr(39) * 2) + chr(39)

    def generate_functions_main_router(self) -> str:
        """
        Roteador "main" que o supabase/edge-runtime usa para despachar
        /functions/v1/<nome> para a pasta supabase/functions/<nome>/index.ts
        certa dentro do próprio projeto. Boilerplate padrão da Supabase para
        self-host — verificado com uma função real rodando de verdade em
        2026-09-10 (chamou a função, leu variável de ambiente, respondeu).
        """
        return """import { serve } from "https://deno.land/std@0.131.0/http/server.ts";

console.log("main function started");

serve(async (req: Request) => {
  const url = new URL(req.url);
  const { pathname } = url;
  const path_parts = pathname.split("/");
  const service_name = path_parts[1];

  if (!service_name || service_name === "") {
    return new Response(JSON.stringify({ error: "missing function name" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const servicePath = `/home/deno/functions/${service_name}`;
  console.error(`serving the request with ${servicePath}`);

  const createWorker = async () => {
    const memoryLimitMb = 150;
    const workerTimeoutMs = 5 * 60 * 1000;
    const noModuleCache = false;
    const importMapPath = null;
    const envVarsObj = Deno.env.toObject();
    const envVars = Object.keys(envVarsObj).map((k) => [k, envVarsObj[k]]);

    return await EdgeRuntime.userWorkers.create({
      servicePath,
      memoryLimitMb,
      workerTimeoutMs,
      noModuleCache,
      importMapPath,
      envVars,
    });
  };

  try {
    const worker = await createWorker();
    return await worker.fetch(req);
  } catch (e) {
    const error = { msg: String(e) };
    return new Response(JSON.stringify(error), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
});
"""

    def generate_kong_config(self) -> str:
        """
        Config declarativa (DB-less) do Kong para o stack "full". As chaves
        anon/service_role são injetadas via variável de ambiente pelo próprio
        entrypoint do serviço kong (ver _generate_swarm_full) — aqui ficam só
        os placeholders ${SUPABASE_ANON_KEY} / ${SUPABASE_SERVICE_KEY}.
        """
        functions_block = ""
        if self.functions:
            functions_block = """
  - name: functions-v1
    url: http://functions:9000/
    routes:
      - name: functions-v1-all
        strip_path: true
        paths:
          - /functions/v1/
    plugins:
      - name: cors
"""
        return f"""_format_version: '2.1'
_transform: true

services:
  - name: auth-v1
    url: http://auth:9999/
    routes:
      - name: auth-v1-all
        strip_path: true
        paths:
          - /auth/v1/
    plugins:
      - name: cors

  - name: rest-v1
    url: http://rest:3000/
    routes:
      - name: rest-v1-all
        strip_path: true
        paths:
          - /rest/v1/
    plugins:
      - name: cors
      - name: key-auth
        config:
          hide_credentials: true
      - name: acl
        config:
          hide_groups_header: true
          allow:
            - anon
            - admin

  - name: storage-v1
    url: http://storage:5000/
    routes:
      - name: storage-v1-all
        strip_path: true
        paths:
          - /storage/v1/
    plugins:
      - name: cors
{functions_block}
consumers:
  - username: anon
    keyauth_credentials:
      - key: ${{SUPABASE_ANON_KEY}}
  - username: service_role
    keyauth_credentials:
      - key: ${{SUPABASE_SERVICE_KEY}}

acls:
  - consumer: anon
    group: anon
  - consumer: service_role
    group: admin
"""

    def generate_db_passwords_sql(self) -> str:
        """
        Só para o stack "full" (imagem supabase/postgres). auth/rest/storage
        se conectam como supabase_auth_admin / authenticator /
        supabase_storage_admin — mas essas contas nascem SEM senha na imagem
        oficial (verificado com um deploy real e descartável em 2026-09-10:
        toda conexão vinda de outro contêiner falhava com "password
        authentication failed" / "has no password assigned"). E elas são
        "reserved roles" — só supabase_admin (não "postgres", que aqui não é
        superuser de verdade) pode alterá-las, por isso o \\connect explícito.
        Precisa rodar DEPOIS do migrate.sh interno da imagem (que cria essas
        roles), então o nome do arquivo em /docker-entrypoint-initdb.d/ tem
        que ordenar alfabeticamente depois de "migrate.sh" — daí o "zzzz".
        """
        db_password = self.db_password
        return f"""\\connect postgres supabase_admin
ALTER ROLE supabase_auth_admin WITH PASSWORD '{db_password}';
ALTER ROLE supabase_storage_admin WITH PASSWORD '{db_password}';
ALTER ROLE authenticator WITH PASSWORD '{db_password}';
"""

    def _generate_swarm_full(self) -> str:
        """
        Stack oficial self-hosted da Supabase: Postgres já vem com os schemas
        auth/storage/realtime prontos de fábrica (sem a emulação manual de
        auth.users), GoTrue e PostgREST nas mesmas versões que a Supabase testa
        junto, e o Kong na frente cuidando do roteamento /auth/v1 e /rest/v1 —
        elimina a categoria inteira de bug encontrada no modo "lite" (rota sem
        stripprefix, auth.uid() incompatível com a versão do PostgREST etc.),
        ao custo de mais 1 contêiner (kong) e imagens mais pesadas.

        Escopo desta v1: db + auth + rest + storage + kong. Realtime/Studio
        ficam de fora por ora (exigem bootstrap próprio bem mais elaborado —
        Realtime precisa registrar um "tenant" via API antes de funcionar) —
        podem ser adicionados depois se o projeto precisar.
        """
        app_slug = self.domain.replace(".", "-").replace(":", "-")
        jwt_secret = self.jwt.jwt_secret
        anon_key = self.jwt.anon_key()
        service_key = self.jwt.service_role_key()
        db_password = self.db_password
        protocol = "http" if self.domain == "localhost" else "https"
        images = self.FULL_STACK_IMAGES
        functions_prefix = " || PathPrefix(`/functions/v1`)" if self.functions else ""
        functions_service = ""
        if self.functions:
            functions_service = f"""
  functions:
    image: "{images['functions']}"
    command:
      - "start"
      - "--main-service"
      - "/home/deno/functions/main"
    environment:
      SUPABASE_URL: "http://kong:8000"
      SUPABASE_ANON_KEY: "{anon_key}"
      SUPABASE_SERVICE_ROLE_KEY: "{service_key}"
      SUPABASE_DB_URL: "postgres://postgres:{db_password}@db:5432/postgres"
    volumes:
      - "./supabase/functions:/home/deno/functions:ro"
    networks:
      - "default"
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - "node.role == manager"
"""

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

  kong:
    image: "{images['kong']}"
    entrypoint: {self._kong_entrypoint_yaml()}
    environment:
      KONG_DATABASE: "off"
      KONG_DECLARATIVE_CONFIG: "/tmp/kong.yml"
      KONG_DNS_ORDER: "LAST,A,CNAME"
      KONG_PLUGINS: "request-transformer,cors,key-auth,acl"
      KONG_NGINX_PROXY_PROXY_BUFFER_SIZE: "160k"
      KONG_NGINX_PROXY_PROXY_BUFFERS: "64 160k"
      SUPABASE_ANON_KEY: "{anon_key}"
      SUPABASE_SERVICE_KEY: "{service_key}"
    volumes:
      - "./kong.yml:/tmp/temp.yml:ro"
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
        - "traefik.http.routers.{app_slug}-api.rule=Host(`{self.domain}`) && (PathPrefix(`/auth/v1`) || PathPrefix(`/rest/v1`) || PathPrefix(`/storage/v1`){functions_prefix})"
        - "traefik.http.routers.{app_slug}-api.entrypoints=websecure"
        - "traefik.http.routers.{app_slug}-api.priority=2"
        - "traefik.http.routers.{app_slug}-api.tls.certresolver={self.cert_resolver}"
        - "traefik.http.routers.{app_slug}-api.service={app_slug}-api"
        - "traefik.http.services.{app_slug}-api.loadbalancer.server.port=8000"
        - "traefik.http.services.{app_slug}-api.loadbalancer.passHostHeader=true"

  auth:
    image: "{images['auth']}"
    environment:
      GOTRUE_API_HOST: "0.0.0.0"
      GOTRUE_API_PORT: "9999"
      API_EXTERNAL_URL: "{protocol}://{self.domain}/auth/v1"
      GOTRUE_SITE_URL: "{protocol}://{self.domain}"
      GOTRUE_DB_DRIVER: "postgres"
      GOTRUE_DB_DATABASE_URL: "postgres://supabase_auth_admin:{db_password}@db:5432/postgres?search_path=auth"
      GOTRUE_JWT_SECRET: "{jwt_secret}"
      GOTRUE_JWT_EXP: "3600"
      GOTRUE_JWT_DEFAULT_GROUP_NAME: "authenticated"
      GOTRUE_DISABLE_SIGNUP: "false"
      GOTRUE_MAILER_AUTOCONFIRM: "true"
      GOTRUE_SMS_AUTOCONFIRM: "true"
      GOTRUE_OPERATOR_TOKEN: "{service_key}"
    networks:
      - "default"
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - "node.role == manager"

  rest:
    image: "postgrest/postgrest:latest"
    environment:
      PGRST_DB_URI: "postgres://authenticator:{db_password}@db:5432/postgres"
      PGRST_DB_SCHEMAS: "public"
      PGRST_DB_ANON_ROLE: "anon"
      PGRST_JWT_SECRET: "{jwt_secret}"
    networks:
      - "default"
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - "node.role == manager"

  storage:
    image: "{images['storage']}"
    environment:
      ANON_KEY: "{anon_key}"
      SERVICE_KEY: "{service_key}"
      POSTGREST_URL: "http://rest:3000"
      PGRST_JWT_SECRET: "{jwt_secret}"
      DATABASE_URL: "postgres://supabase_storage_admin:{db_password}@db:5432/postgres"
      FILE_SIZE_LIMIT: "52428800"
      STORAGE_BACKEND: "file"
      FILE_STORAGE_BACKEND_PATH: "/var/lib/storage"
      TENANT_ID: "{app_slug}"
      REGION: "stub"
      GLOBAL_S3_BUCKET: "stub"
      ENABLE_IMAGE_TRANSFORMATION: "false"
    volumes:
      - "{app_slug}_storage_data:/var/lib/storage"
    networks:
      - "default"
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - "node.role == manager"
{functions_service}
  db:
    image: "{images['db']}"
    environment:
      POSTGRES_PASSWORD: "{db_password}"
      JWT_SECRET: "{jwt_secret}"
      JWT_EXP: "3600"
    volumes:
      - "{app_slug}_postgres_data:/var/lib/postgresql/data"
      - "./db-passwords.sql:/docker-entrypoint-initdb.d/zzzz-aidd-bridge-passwords.sql:ro"
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
  {app_slug}_storage_data:
"""

    def generate_caddyfile(self) -> str:
        functions_line = "\n    reverse_proxy /functions/v1/* functions:9000" if self.functions else ""
        functions_handle = ""
        if self.functions:
            functions_handle = """
    # EmulaÃ§Ã£o do endpoint Supabase Edge Functions /functions/v1/
    handle_path /functions/v1/* {
        reverse_proxy functions:9000
    }
"""
        if self.domain == "localhost":
            return f"""localhost {{
    reverse_proxy /rest/v1/* postgrest:3000
    reverse_proxy /storage/v1/* storage:5000{functions_line}
    reverse_proxy /* web:80
}}
"""
        return f"""{self.domain} {{
    # EmulaÃ§Ã£o do endpoint Supabase REST /rest/v1/
    handle_path /rest/v1/* {{
        reverse_proxy postgrest:3000
    }}

    # EmulaÃ§Ã£o do endpoint Supabase Storage /storage/v1/
    handle_path /storage/v1/* {{
        reverse_proxy storage:5000
    }}
{functions_handle}
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

        if self.stack == "full":
            targets["kong.yml"] = self.generate_kong_config()
            targets["db-passwords.sql"] = self.generate_db_passwords_sql()

        if self.functions:
            targets[os.path.join("supabase", "functions", "main", "index.ts")] = self.generate_functions_main_router()

        for filename, content in targets.items():
            dest = os.path.join(self.target_dir, filename)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(content)
            files_created[filename] = dest

        return files_created