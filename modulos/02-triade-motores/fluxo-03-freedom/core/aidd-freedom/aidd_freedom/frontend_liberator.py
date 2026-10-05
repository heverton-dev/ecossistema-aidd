# -*- coding: utf-8 -*-
"""
Frontend Liberator — copia o codigo-fonte do frontend low-code (preservando
sua stack original: Vite/React/qualquer coisa que a plataforma tenha
exportado) do projeto de origem para o diretorio de saida, e reescreve
ocorrencias hardcoded de nuvem proprietaria (Supabase Cloud, Firebase) para
variaveis de ambiente Vite (VITE_SUPABASE_URL / VITE_SUPABASE_PUBLISHABLE_KEY),
permitindo que o cliente @supabase/supabase-js continue funcionando com zero
refatoracao manual, agora apontando para o PostgREST self-hosted.
"""

import os
import shutil
from typing import Dict, List

from .vendor_patterns import EXTENSOES_VARREDURA, ANON_KEY_ASSIGNMENT, SUPABASE_URL_LITERAL

IGNORAR_DIRS = {"node_modules", "dist", "build", ".git", ".next", ".nuxt", "__pycache__", ".turbo"}

# Nunca copiar .env/.env.local/.env.development/etc para a saida liberada:
# esses arquivos guardam segredos REAIS do projeto de origem (ex: chave da
# Supabase Cloud do cliente, as vezes uma service-role key) -- achado real
# com um projeto Lovable de producao de verdade. O bridge sempre gera seu
# proprio .env.production com credenciais do stack self-hosted; carregar o
# .env original e puro risco de vazamento (alguem faz `git add` da saida
# liberada sem perceber). .env.example fica de fora da lista: por convencao
# so tem placeholders, e documentacao util pro operador saber que variaveis
# configurar.
ENV_FILES_PROIBIDOS = {".env", ".env.local", ".env.development", ".env.production.local", ".env.test"}


class FrontendLiberator:
    def __init__(self, project_dir: str, output_dir: str):
        self.project_dir = os.path.abspath(project_dir)
        self.output_dir = os.path.abspath(output_dir)

    def copy_and_liberate(self) -> Dict[str, List[str]]:
        copiados: List[str] = []
        liberados: List[str] = []
        in_place = os.path.normcase(self.project_dir) == os.path.normcase(self.output_dir)

        for root, dirs, files in os.walk(self.project_dir):
            dirs[:] = [d for d in dirs if d not in IGNORAR_DIRS]
            for filename in files:
                if filename in ENV_FILES_PROIBIDOS:
                    continue
                src_path = os.path.join(root, filename)
                rel_path = os.path.relpath(src_path, self.project_dir)
                dest_path = os.path.join(self.output_dir, rel_path)

                if not in_place:
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy2(src_path, dest_path)
                    copiados.append(rel_path)

                ext = os.path.splitext(filename)[1].lower()
                if ext in EXTENSOES_VARREDURA:
                    if self._liberate_file(dest_path):
                        liberados.append(rel_path)

        return {"copiados": copiados, "liberados": liberados}

    @staticmethod
    def _liberate_file(path: str) -> bool:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            original = f.read()

        content = SUPABASE_URL_LITERAL.sub("import.meta.env.VITE_SUPABASE_URL", original)
        content = ANON_KEY_ASSIGNMENT.sub(
            lambda m: f"{m.group(1)}import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY", content
        )

        if content != original:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        return False
