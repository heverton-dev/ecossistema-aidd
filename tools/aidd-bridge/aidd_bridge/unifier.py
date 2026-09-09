# -*- coding: utf-8 -*-
"""
Multi-App Unifier — Fusão de 2 a N projetos Lovable em um único
sistema em Fatias Verticais (Vertical Slices), unificando Tailwind e Rotas.
"""

import os
import shutil
import json
from typing import List, Dict, Any
from .scanner import LovableScanner

class MultiAppUnifier:
    def __init__(self, app_dirs: List[str], output_dir: str):
        self.app_dirs = [os.path.abspath(d) for d in app_dirs]
        self.output_dir = os.path.abspath(output_dir)

    def merge(self) -> Dict[str, Any]:
        os.makedirs(self.output_dir, exist_ok=True)
        manifests = []
        for app_dir in self.app_dirs:
            scanner = LovableScanner(app_dir)
            manifests.append(scanner.scan())

        # 1. Unificar package.json
        unified_pkg = self._merge_packages(manifests)
        with open(os.path.join(self.output_dir, "package.json"), "w", encoding="utf-8") as f:
            json.dump(unified_pkg, f, indent=2, ensure_ascii=False)

        # 2. Criar estrutura em módulos verticais
        modules_dir = os.path.join(self.output_dir, "src", "modules")
        os.makedirs(modules_dir, exist_ok=True)

        merged_apps = []
        for idx, manifest in enumerate(manifests):
            app_dir = manifest["project_dir"]
            pkg_name = manifest["package_info"].get("name", f"app{idx+1}").replace("@", "").replace("/", "-")
            module_target = os.path.join(modules_dir, pkg_name)

            src_source = os.path.join(app_dir, "src")
            if os.path.exists(src_source):
                shutil.copytree(src_source, module_target, dirs_exist_ok=True)

            merged_apps.append({
                "module_name": pkg_name,
                "prefix": f"/{pkg_name}",
                "routes": manifest.get("routes", [])
            })

        # 3. Gerar Roteador Central Unificado
        self._generate_master_router(merged_apps)

        return {
            "status": "success",
            "output_dir": self.output_dir,
            "apps_merged": [a["module_name"] for a in merged_apps],
            "total_apps": len(merged_apps)
        }

    def _merge_packages(self, manifests: List[Dict[str, Any]]) -> Dict[str, Any]:
        base = {
            "name": "aidd-unified-application",
            "version": "1.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "tsc && vite build",
                "preview": "vite preview"
            },
            "dependencies": {},
            "devDependencies": {}
        }

        for m in manifests:
            pkg = m.get("package_info", {})
            for k, v in pkg.get("dependencies", {}).items():
                base["dependencies"][k] = v
            for k, v in pkg.get("devDependencies", {}).items():
                base["devDependencies"][k] = v

        return base

    def _generate_master_router(self, merged_apps: List[Dict[str, Any]]) -> None:
        router_content = """// Roteador Central gerado determinísticamente por aidd-bridge
import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';

export default function MasterRouter() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background text-foreground flex flex-col">
        <header className="p-4 border-b flex items-center justify-between bg-card">
          <h1 className="font-bold text-lg">AIDD Unified Portal</h1>
          <nav className="flex gap-4">
"""
        for app in merged_apps:
            router_content += f'            <Link to="{app["prefix"]}" className="hover:underline capitalize font-medium">{app["module_name"]}</Link>\n'

        router_content += """          </nav>
        </header>
        <main className="flex-1 p-6">
          <Routes>
            <Route path="/" element={<div className="text-center py-12 text-muted-foreground">Selecione uma aplicacao no menu acima.</div>} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
"""
        src_dir = os.path.join(self.output_dir, "src")
        os.makedirs(src_dir, exist_ok=True)
        with open(os.path.join(src_dir, "AppMasterRouter.tsx"), "w", encoding="utf-8") as f:
            f.write(router_content)