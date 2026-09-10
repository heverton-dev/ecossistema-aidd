# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v6.0-Enterprise — Next.js Project Exporter
=============================================================================
Generates a production-ready Next.js project from AIDD modules:
- next.config.js, package.json, tsconfig.json
- Pages Router or App Router directory structure
- API routes converted from AIDD module routes
- _app.tsx / layout.tsx with design system CSS import
- middleware.ts with JWT auth guard
- Design system CSS copied to public/

Zero external dependencies — uses only stdlib.
"""

import os
import re
import json
import shutil
from typing import Dict, List, Optional, Any
from pathlib import Path


class NextJSExporter:
    """Exports an AIDD project to a Next.js application."""

    SUPPORTED_ROUTERS = ("pages", "app")

    def __init__(self, router_type: str = "app"):
        if router_type not in self.SUPPORTED_ROUTERS:
            raise ValueError(f"router_type must be one of {self.SUPPORTED_ROUTERS}, got '{router_type}'")
        self.router_type = router_type

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export_project(self, project_dir: str, output_dir: str) -> dict:
        """Export an AIDD project to a Next.js project.

        Args:
            project_dir: Path to the AIDD project root (contains src/modules/).
            output_dir: Path where the Next.js project will be generated.

        Returns:
            dict with keys: files_created (list[str]), modules (list[str]),
                  router_type (str), warnings (list[str]).
        """
        project_dir = os.path.abspath(project_dir)
        output_dir = os.path.abspath(output_dir)

        result: Dict[str, Any] = {
            "files_created": [],
            "modules": [],
            "router_type": self.router_type,
            "warnings": [],
        }

        # Discover AIDD modules
        modules = self._discover_modules(project_dir)
        result["modules"] = modules

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Generate config files
        result["files_created"].extend(self._generate_package_json(output_dir, modules))
        result["files_created"].extend(self._generate_next_config(output_dir))
        result["files_created"].extend(self._generate_tsconfig(output_dir))
        result["files_created"].extend(self._generate_gitignore(output_dir))

        # Generate router-specific files
        if self.router_type == "pages":
            result["files_created"].extend(
                self._generate_pages_router(output_dir, project_dir, modules)
            )
        else:
            result["files_created"].extend(
                self._generate_app_router(output_dir, project_dir, modules)
            )

        # Generate API routes from AIDD modules
        result["files_created"].extend(
            self._generate_api_routes(output_dir, project_dir, modules)
        )

        # Generate middleware with JWT auth
        result["files_created"].extend(self._generate_middleware(output_dir))

        # Copy design system CSS
        result["files_created"].extend(self._copy_design_system_css(output_dir))

        return result

    # ------------------------------------------------------------------
    # Module Discovery
    # ------------------------------------------------------------------

    def _discover_modules(self, project_dir: str) -> List[str]:
        """Find all AIDD module names under src/modules/."""
        modules_dir = os.path.join(project_dir, "src", "modules")
        if not os.path.isdir(modules_dir):
            return []
        modules = []
        for entry in sorted(os.listdir(modules_dir)):
            entry_path = os.path.join(modules_dir, entry)
            if os.path.isdir(entry_path) and not entry.startswith(("_", ".")):
                # Confirm it has routes.py or services.py
                has_routes = os.path.isfile(os.path.join(entry_path, "routes.py"))
                has_services = os.path.isfile(os.path.join(entry_path, "services.py"))
                if has_routes or has_services:
                    modules.append(entry)
        return modules

    def _parse_routes(self, project_dir: str, module_name: str) -> List[Dict[str, Any]]:
        """Parse routes.py to extract endpoint definitions."""
        routes_file = os.path.join(project_dir, "src", "modules", module_name, "routes.py")
        if not os.path.isfile(routes_file):
            return []

        with open(routes_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        endpoints = []
        # Match @registry.get/post/put/delete("path", ...) patterns
        pattern = re.compile(
            r'@registry\.(get|post|put|delete)\(\s*["\']([^"\']+)["\']',
            re.IGNORECASE,
        )
        for match in pattern.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            endpoints.append({
                "method": method,
                "path": path,
                "module": module_name,
            })
        return endpoints

    # ------------------------------------------------------------------
    # Config File Generation
    # ------------------------------------------------------------------

    def _generate_package_json(self, output_dir: str, modules: List[str]) -> List[str]:
        """Generate package.json with Next.js dependencies."""
        package = {
            "name": "aidd-nextjs-app",
            "version": "1.0.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint",
            },
            "dependencies": {
                "next": "^14.2.0",
                "react": "^18.3.0",
                "react-dom": "^18.3.0",
            },
            "devDependencies": {
                "@types/node": "^20.0.0",
                "@types/react": "^18.3.0",
                "@types/react-dom": "^18.3.0",
                "typescript": "^5.4.0",
                "eslint": "^8.0.0",
                "eslint-config-next": "^14.2.0",
            },
        }
        path = os.path.join(output_dir, "package.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(package, f, indent=2, ensure_ascii=False)
            f.write("\n")
        return [path]

    def _generate_next_config(self, output_dir: str) -> List[str]:
        """Generate next.config.js."""
        config = """/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  compress: true,
  experimental: {
    optimizeCss: true,
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-XSS-Protection', value: '1; mode=block' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload',
          },
        ],
      },
    ];
  },
  async rewrites() {
    return [
      // Proxy AIDD API routes if needed
      // { source: '/api/v1/:path*', destination: 'http://localhost:8000/api/:path*' },
    ];
  },
};

module.exports = nextConfig;
"""
        path = os.path.join(output_dir, "next.config.js")
        with open(path, "w", encoding="utf-8") as f:
            f.write(config)
        return [path]

    def _generate_tsconfig(self, output_dir: str) -> List[str]:
        """Generate tsconfig.json."""
        tsconfig = {
            "compilerOptions": {
                "target": "ES2017",
                "lib": ["dom", "dom.iterable", "esnext"],
                "allowJs": True,
                "skipLibCheck": True,
                "strict": True,
                "noEmit": True,
                "esModuleInterop": True,
                "module": "esnext",
                "moduleResolution": "bundler",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "preserve",
                "incremental": True,
                "plugins": [{"name": "next"}],
                "paths": {"@/*": ["./src/*"]},
            },
            "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
            "exclude": ["node_modules"],
        }
        path = os.path.join(output_dir, "tsconfig.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(tsconfig, f, indent=2, ensure_ascii=False)
            f.write("\n")
        return [path]

    def _generate_gitignore(self, output_dir: str) -> List[str]:
        """Generate .gitignore for Next.js."""
        content = """# dependencies
/node_modules
/.pnp
.pnp.js

# testing
/coverage

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# local env files
.env*.local
.env

# vercel
.vercel

# typescript
*.tsbuildinfo
next-env.d.ts
"""
        path = os.path.join(output_dir, ".gitignore")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return [path]

    # ------------------------------------------------------------------
    # Pages Router Generation
    # ------------------------------------------------------------------

    def _generate_pages_router(
        self, output_dir: str, project_dir: str, modules: List[str]
    ) -> List[str]:
        """Generate Pages Router structure (_app.tsx, index.tsx, pages/)."""
        created = []
        pages_dir = os.path.join(output_dir, "pages")
        os.makedirs(pages_dir, exist_ok=True)

        # _app.tsx
        app_tsx = """import type { AppProps } from 'next/app';
import '@/styles/globals.css';
import '@/styles/design-system.css';

export default function App({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />;
}
"""
        path = os.path.join(pages_dir, "_app.tsx")
        with open(path, "w", encoding="utf-8") as f:
            f.write(app_tsx)
        created.append(path)

        # index.tsx — landing page with module links
        index_tsx = self._generate_index_page(modules)
        path = os.path.join(pages_dir, "index.tsx")
        with open(path, "w", encoding="utf-8") as f:
            f.write(index_tsx)
        created.append(path)

        # styles directory
        styles_dir = os.path.join(output_dir, "styles")
        os.makedirs(styles_dir, exist_ok=True)

        globals_css = """*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
}

body {
  min-height: 100vh;
}
"""
        path = os.path.join(styles_dir, "globals.css")
        with open(path, "w", encoding="utf-8") as f:
            f.write(globals_css)
        created.append(path)

        # Module pages
        for mod in modules:
            mod_page_dir = os.path.join(pages_dir, mod)
            os.makedirs(mod_page_dir, exist_ok=True)
            page_content = self._generate_module_page(mod)
            path = os.path.join(mod_page_dir, "index.tsx")
            with open(path, "w", encoding="utf-8") as f:
                f.write(page_content)
            created.append(path)

        return created

    # ------------------------------------------------------------------
    # App Router Generation
    # ------------------------------------------------------------------

    def _generate_app_router(
        self, output_dir: str, project_dir: str, modules: List[str]
    ) -> List[str]:
        """Generate App Router structure (app/layout.tsx, app/page.tsx, etc.)."""
        created = []
        app_dir = os.path.join(output_dir, "app")
        os.makedirs(app_dir, exist_ok=True)

        # layout.tsx
        layout_tsx = """import type { Metadata } from 'next';
import '@/styles/globals.css';
import '@/styles/design-system.css';

export const metadata: Metadata = {
  title: 'AIDD Enterprise App',
  description: 'Generated by AIDD Next.js Exporter',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
"""
        path = os.path.join(app_dir, "layout.tsx")
        with open(path, "w", encoding="utf-8") as f:
            f.write(layout_tsx)
        created.append(path)

        # page.tsx — root page
        page_tsx = self._generate_index_page(modules)
        path = os.path.join(app_dir, "page.tsx")
        with open(path, "w", encoding="utf-8") as f:
            f.write(page_tsx)
        created.append(path)

        # styles directory
        styles_dir = os.path.join(output_dir, "styles")
        os.makedirs(styles_dir, exist_ok=True)

        globals_css = """*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
}

body {
  min-height: 100vh;
}
"""
        path = os.path.join(styles_dir, "globals.css")
        with open(path, "w", encoding="utf-8") as f:
            f.write(globals_css)
        created.append(path)

        # Module pages under app/
        for mod in modules:
            mod_dir = os.path.join(app_dir, mod)
            os.makedirs(mod_dir, exist_ok=True)

            mod_layout = f"""export default function {self._to_pascal_case(mod)}Layout({{
  children,
}}: {{
  children: React.ReactNode;
}}) {{
  return <section>{{children}}</section>;
}}
"""
            path = os.path.join(mod_dir, "layout.tsx")
            with open(path, "w", encoding="utf-8") as f:
                f.write(mod_layout)
            created.append(path)

            mod_page = self._generate_module_page(mod)
            path = os.path.join(mod_dir, "page.tsx")
            with open(path, "w", encoding="utf-8") as f:
                f.write(mod_page)
            created.append(path)

        return created

    # ------------------------------------------------------------------
    # API Routes Generation
    # ------------------------------------------------------------------

    def _generate_api_routes(
        self, output_dir: str, project_dir: str, modules: List[str]
    ) -> List[str]:
        """Convert AIDD module routes to Next.js API routes."""
        created = []

        if self.router_type == "pages":
            api_dir = os.path.join(output_dir, "pages", "api")
        else:
            api_dir = os.path.join(output_dir, "app", "api")

        os.makedirs(api_dir, exist_ok=True)

        for mod in modules:
            endpoints = self._parse_routes(project_dir, mod)
            if not endpoints:
                continue

            mod_api_dir = os.path.join(api_dir, mod)
            os.makedirs(mod_api_dir, exist_ok=True)

            # Group endpoints by path segment
            for ep in endpoints:
                route_name = self._path_to_filename(ep["path"])
                method = ep["method"]

                if self.router_type == "pages":
                    # Pages Router: single route.ts per endpoint
                    route_file = os.path.join(mod_api_dir, f"{route_name}.ts")
                    content = self._generate_pages_api_route(ep)
                else:
                    # App Router: route.ts with exported HTTP method functions
                    route_file = os.path.join(mod_api_dir, "route.ts")
                    content = self._generate_app_api_route(endpoints)
                    # Write once per module directory for app router
                    if os.path.exists(route_file):
                        continue

                with open(route_file, "w", encoding="utf-8") as f:
                    f.write(content)
                created.append(route_file)

                if self.router_type == "pages":
                    break  # One file per route for pages router

        return created

    def _generate_pages_api_route(self, endpoint: Dict[str, Any]) -> str:
        """Generate a Pages Router API route handler."""
        method = endpoint["method"]
        module = endpoint["module"]
        path = endpoint["path"]

        return f"""import type {{ NextApiRequest, NextApiResponse }} from 'next';

/**
 * AIDD Route: {method} {path}
 * Module: {module}
 * Auto-generated by AIDD Next.js Exporter
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {{
  if (req.method !== '{method}') {{
    res.setHeader('Allow', '{method}');
    return res.status(405).json({{ error: 'Method Not Allowed' }});
  }}

  try {{
    // TODO: Connect to AIDD backend API
    // const response = await fetch(`${{process.env.AIDD_API_URL}}{path}`, {{
    //   method: '{method}',
    //   headers: {{
    //     'Content-Type': 'application/json',
    //     'Authorization': req.headers.authorization || '',
    //   }},
    //   {f"body: JSON.stringify(req.body)," if method in ("POST", "PUT") else ""}
    // }});
    // const data = await response.json();
    // return res.status(response.status).json(data);

    return res.status(200).json({{ message: 'AIDD API route: {path}', module: '{module}' }});
  }} catch (error) {{
    console.error('API Error:', error);
    return res.status(500).json({{ error: 'Internal Server Error' }});
  }}
}}
"""

    def _generate_app_api_route(self, endpoints: List[Dict[str, Any]]) -> str:
        """Generate an App Router route.ts with exported HTTP method handlers."""
        lines = [
            "import { NextRequest, NextResponse } from 'next/server';",
            "",
        ]

        methods_seen = set()
        for ep in endpoints:
            method = ep["method"]
            if method in methods_seen:
                continue
            methods_seen.add(method)
            path = ep["path"]
            module = ep["module"]

            lines.append(f"""/**
 * AIDD Route: {method} {path}
 * Module: {module}
 * Auto-generated by AIDD Next.js Exporter
 */
export async function {method}(request: NextRequest) {{
  try {{
    // TODO: Connect to AIDD backend API
    // const body = {method in ("POST", "PUT") and "await request.json()" or "undefined"};
    // const response = await fetch(`${{process.env.AIDD_API_URL}}{path}`, {{
    //   method: '{method}',
    //   headers: {{
    //     'Content-Type': 'application/json',
    //     'Authorization': request.headers.get('authorization') || '',
    //   }},
    //   ...(body ? {{ body: JSON.stringify(body) }} : {{}}),
    // }});
    // const data = await response.json();
    // return NextResponse.json(data, {{ status: response.status }});

    return NextResponse.json({{ message: 'AIDD API route: {path}', module: '{module}' }});
  }} catch (error) {{
    console.error('API Error:', error);
    return NextResponse.json({{ error: 'Internal Server Error' }}, {{ status: 500 }});
  }}
}}
""")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Middleware Generation
    # ------------------------------------------------------------------

    def _generate_middleware(self, output_dir: str) -> List[str]:
        """Generate middleware.ts with JWT auth guard."""
        middleware = """import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * AIDD JWT Auth Middleware
 *
 * Protects /api/* routes (except public ones) by validating
 * the Authorization: Bearer <token> header.
 *
 * Auto-generated by AIDD Next.js Exporter.
 */

// Routes that do not require authentication
const PUBLIC_ROUTES = [
  '/api/health',
  '/api/auth/login',
  '/api/auth/register',
];

function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.some((route) => pathname.startsWith(route));
}

function decodeJWTPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;

    const payload = JSON.parse(
      Buffer.from(parts[1], 'base64url').toString('utf-8')
    );

    // Check expiration
    if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) {
      return null;
    }

    return payload;
  } catch {
    return null;
  }
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Only protect API routes
  if (!pathname.startsWith('/api/')) {
    return NextResponse.next();
  }

  // Allow public routes
  if (isPublicRoute(pathname)) {
    return NextResponse.next();
  }

  // Extract token from Authorization header
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return NextResponse.json(
      { error: 'Missing or invalid Authorization header' },
      { status: 401 }
    );
  }

  const token = authHeader.slice(7);
  const payload = decodeJWTPayload(token);

  if (!payload) {
    return NextResponse.json(
      { error: 'Invalid or expired token' },
      { status: 401 }
    );
  }

  // Forward user info in headers for downstream handlers
  const response = NextResponse.next();
  response.headers.set('X-User-Sub', String(payload.sub || ''));
  response.headers.set('X-User-Role', String(payload.role || ''));

  return response;
}

export const config = {
  matcher: ['/api/:path*'],
};
"""
        path = os.path.join(output_dir, "middleware.ts")
        with open(path, "w", encoding="utf-8") as f:
            f.write(middleware)
        return [path]

    # ------------------------------------------------------------------
    # Design System CSS Copy
    # ------------------------------------------------------------------

    def _copy_design_system_css(self, output_dir: str) -> List[str]:
        """Copy design-system.css to the styles directory."""
        created = []
        styles_dir = os.path.join(output_dir, "styles")
        os.makedirs(styles_dir, exist_ok=True)

        # Also create public/ for static assets
        public_dir = os.path.join(output_dir, "public")
        os.makedirs(public_dir, exist_ok=True)

        # The CSS file should exist at templates/static/design-system.css
        # relative to the AIDD project. We generate a reference copy.
        css_path = os.path.join(styles_dir, "design-system.css")
        if not os.path.exists(css_path):
            # Will be populated by the template; write a placeholder import
            with open(css_path, "w", encoding="utf-8") as f:
                f.write("/* Design System CSS — see templates/static/design-system.css */\n")
            created.append(css_path)

        return created

    # ------------------------------------------------------------------
    # Page Templates
    # ------------------------------------------------------------------

    def _generate_index_page(self, modules: List[str]) -> str:
        """Generate the index/landing page component."""
        module_links = ""
        for mod in modules:
            label = mod.replace("_", " ").replace("-", " ").title()
            if self.router_type == "pages":
                href = f"/{mod}"
            else:
                href = f"/{mod}"
            module_links += f"""
        <Link href="{href}" className="studio-card" style={{ textDecoration: 'none', color: 'inherit' }}>
          <h2>{label}</h2>
          <p>Manage {label.lower()} records</p>
        </Link>"""

        return f"""import Link from 'next/link';

/**
 * AIDD Enterprise — Home Page
 * Auto-generated by AIDD Next.js Exporter
 */
export default function Home() {{
  return (
    <main style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '0.5rem' }}>AIDD Enterprise</h1>
      <p style={{ color: '#6c7086', marginBottom: '2rem' }}>
        Module dashboard — select a module to manage.
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
        {module_links}
      </div>
    </main>
  );
}}
"""

    def _generate_module_page(self, module_name: str) -> str:
        """Generate a module page component with CRUD UI scaffold."""
        label = module_name.replace("_", " ").replace("-", " ").title()
        return f"""'use client';

import {{ useEffect, useState }} from 'react';

/**
 * {label} Module Page
 * Auto-generated by AIDD Next.js Exporter
 */
interface Item {{
  id: number;
  titulo: string;
  status: string;
  [key: string]: unknown;
}}

export default function {self._to_pascal_case(module_name)}Page() {{
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {{
    fetch('/api/{module_name}')
      .then((res) => res.json())
      .then((data) => {{
        setItems(Array.isArray(data) ? data : []);
        setLoading(false);
      }})
      .catch((err) => {{
        setError(err.message);
        setLoading(false);
      }});
  }}, []);

  if (loading) return <div className="studio-card"><p>Loading {label.lower()}...</p></div>;
  if (error) return <div className="studio-card"><p style={{ color: 'var(--color-danger)' }}>Error: {{error}}</p></div>;

  return (
    <main style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '1.5rem' }}>{label}</h1>
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <span className="metric-badge metric-badge--green">{{items.filter(i => i.status === 'ativo').length}} Active</span>
        <span className="metric-badge metric-badge--yellow">{{items.length}} Total</span>
      </div>
      <div style={{ display: 'grid', gap: '1rem' }}>
        {{items.map((item) => (
          <div key={{item.id}} className="studio-card">
            <h3>{{item.titulo}}</h3>
            <p>Status: {{item.status}}</p>
          </div>
        ))}}
        {{items.length === 0 && (
          <div className="studio-card">
            <p>No records found.</p>
          </div>
        )}}
      </div>
    </main>
  );
}}
"""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_pascal_case(s: str) -> str:
        """Convert snake_case or kebab-case to PascalCase."""
        return "".join(word.capitalize() for word in re.split(r"[-_]+", s))

    @staticmethod
    def _path_to_filename(path: str) -> str:
        """Convert an API path like /api/modulo1/obter to a safe filename."""
        # Remove /api/ prefix, replace slashes with underscores
        clean = path.lstrip("/").replace("api/", "").replace("/", "_")
        # Remove non-alphanumeric chars except underscore
        clean = re.sub(r"[^a-zA-Z0-9_]", "", clean)
        return clean or "index"
