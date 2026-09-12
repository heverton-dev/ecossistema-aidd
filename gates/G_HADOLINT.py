# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_HADOLINT
=============================================================================
Audita estaticamente todos os Dockerfiles do repositório (e os gerados pelas
ferramentas do ecossistema) utilizando o Hadolint (Haskell Dockerfile Linter),
garantindo melhores práticas OCI, segurança de contêineres, menor privilégio
(OWASP) e consistência sintática (NIH #5).

Checagens executadas:
1. Localização automática do binário 'hadolint' no PATH do sistema ou
   diretórios de instalação padrão (WinGet / Scoop / Homebrew / bin).
2. Descoberta de todos os arquivos Dockerfile e Dockerfile.* rastreados ou
   presentes em tools/ e raiz (excluindo .venv, .git, node_modules).
3. Execução do hadolint com saída estruturada em JSON para parsing exato de
   severidade (error, warning, info) e regras OCI violadas (DLxxxx, SCxxxx).
4. Suporte a argumento opcional de arquivos específicos para execução rápida
   em hooks de pre-commit.

Uso:
  python gates/G_HADOLINT.py [arquivo1] [arquivo2] ...
      exit 0 = todos os Dockerfiles em conformidade com as regras Hadolint.
      exit 1 = falha sintática, regra violada ou hadolint não instalado.
=============================================================================
"""

import json
import os
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def encontrar_binario_hadolint() -> Optional[str]:
    """Localiza o executável hadolint no PATH ou em diretórios comuns de instalação."""
    caminho = shutil.which("hadolint")
    if caminho:
        return caminho

    # Busca em diretórios típicos no Windows (WinGet, WindowsApps, etc.)
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            candidatos_win = [
                os.path.join(local_app_data, "Microsoft", "WindowsApps", "hadolint.exe"),
                os.path.join(os.path.expanduser("~"), ".aidd", "bin", "hadolint.exe"),
            ]
            winget_pkgs = os.path.join(local_app_data, "Microsoft", "WinGet", "Packages")
            if os.path.isdir(winget_pkgs):
                for root, _, files in os.walk(winget_pkgs):
                    if "hadolint.exe" in files:
                        candidatos_win.append(os.path.join(root, "hadolint.exe"))
            for cand in candidatos_win:
                if os.path.isfile(cand):
                    return cand

    # Busca em diretórios típicos POSIX
    for cand in ["/usr/local/bin/hadolint", "/usr/bin/hadolint", os.path.expanduser("~/.local/bin/hadolint"), os.path.expanduser("~/.aidd/bin/hadolint")]:
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand

    return None


def listar_dockerfiles(alvos: Optional[List[str]] = None) -> List[str]:
    """Retorna lista de caminhos absolutos para Dockerfiles a serem auditados."""
    if alvos:
        dockerfiles = []
        for alvo in alvos:
            caminho_abs = os.path.abspath(alvo) if not os.path.isabs(alvo) else alvo
            if os.path.isfile(caminho_abs):
                dockerfiles.append(caminho_abs)
        return dockerfiles

    # Descoberta via git ls-files quando dentro de repositório git
    try:
        resultado = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if resultado.returncode == 0:
            arquivos = []
            for f in resultado.stdout.splitlines():
                nome = os.path.basename(f)
                if nome == "Dockerfile" or nome.startswith("Dockerfile."):
                    caminho_abs = os.path.join(ROOT_DIR, f)
                    if os.path.isfile(caminho_abs):
                        arquivos.append(caminho_abs)
            if arquivos:
                return sorted(arquivos)
    except Exception:
        pass

    # Fallback para varredura de diretório
    encontrados = []
    ignorar = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache"}
    for root, dirs, files in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d not in ignorar]
        for f in files:
            if f == "Dockerfile" or f.startswith("Dockerfile."):
                encontrados.append(os.path.join(root, f))
    return sorted(encontrados)


def auditar_dockerfile(hadolint_bin: str, caminho_dockerfile: str) -> Tuple[int, List[Dict]]:
    """Executa hadolint contra um Dockerfile específico e retorna o exit code e achados."""
    try:
        proc = subprocess.run(
            [hadolint_bin, "--format", "json", caminho_dockerfile],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        achados = []
        if proc.stdout.strip():
            try:
                achados = json.loads(proc.stdout)
            except json.JSONDecodeError:
                achados = [{"line": 0, "code": "RAW", "level": "error", "message": proc.stdout.strip()}]
        return proc.returncode, achados
    except Exception as exc:
        return 1, [{"line": 0, "code": "ERR", "level": "error", "message": str(exc)}]


def escanear(arquivos_alvo: Optional[List[str]] = None) -> int:
    """Executa o gate G_HADOLINT completo e retorna 0 se aprovado ou 1 se reprovado."""
    print("=" * 70)
    print(" [GATE] G_HADOLINT — Linting e Boas Práticas de Dockerfile (hadolint)")
    print("=" * 70)

    hadolint_bin = encontrar_binario_hadolint()
    if not hadolint_bin:
        print("[FALHA] Binário 'hadolint' não encontrado no sistema.")
        print("Instalação recomendada:")
        print("  Windows: winget install hadolint.hadolint")
        print("  macOS:   brew install hadolint")
        print("  Linux:   sudo curl -sL -o /usr/local/bin/hadolint https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64 && sudo chmod +x /usr/local/bin/hadolint")
        print("=" * 70)
        return 1

    dockerfiles = listar_dockerfiles(arquivos_alvo)
    if not dockerfiles:
        print("[OK] Nenhum Dockerfile encontrado para validação.")
        print("=" * 70)
        return 0

    print(f"[INFO] Binário Hadolint: {hadolint_bin}")
    print(f"[INFO] Validando {len(dockerfiles)} arquivo(s) Dockerfile...")

    erros_totais = 0
    arquivos_com_erro = 0

    for df_path in dockerfiles:
        rel_path = os.path.relpath(df_path, ROOT_DIR)
        code, achados = auditar_dockerfile(hadolint_bin, df_path)

        # Filtrar achados de severidade error e warning (ou exit code != 0)
        problemas = [a for a in achados if a.get("level") in ("error", "warning") or code != 0]

        if code == 0 and not problemas:
            print(f"[OK] {rel_path} (100% aderente)")
        else:
            arquivos_com_erro += 1
            erros_totais += len(problemas) if problemas else 1
            print(f"[FALHA] {rel_path}:")
            for prob in problemas:
                linha = prob.get("line", "?")
                regra = prob.get("code", "REGRA")
                nivel = prob.get("level", "erro").upper()
                msg = prob.get("message", "")
                print(f"  - Linha {linha} [{regra}][{nivel}]: {msg}")

    print("=" * 70)
    if arquivos_com_erro > 0:
        print(" [FALHA] Quality Gate G_HADOLINT REPROVADO!")
        print(f" Total de arquivos com violação: {arquivos_com_erro} | Total de problemas: {erros_totais}")
        print("=" * 70)
        return 1

    print(" [SUCESSO] Quality Gate G_HADOLINT APROVADO (100% OK)!")
    print(f" Todos os {len(dockerfiles)} Dockerfiles validados com sucesso.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    alvos = sys.argv[1:] if len(sys.argv) > 1 else None
    sys.exit(escanear(alvos))
