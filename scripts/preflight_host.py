# -*- coding: utf-8 -*-
"""
Preflight Host — diagnostico instantaneo (< 2s) de binarios do sistema
+ bootstrapper assistido multi-OS (--fix).

Detecta presenca, caminho e versao de: Git, Node, Docker, Hadolint, Checkov.
Reutiliza detectores de G_HADOLINT e G_INFRA_COMPOSE como fonte unica de verdade.
Sem dependencia de rede no diagnostico (só o --fix/--dry-run, quando acionado,
monta/executa plano de instalacao assistida).

Uso standalone:
    python scripts/preflight_host.py [--json] [--fix] [--dry-run]

Uso via ecossistema.py:
    python ecossistema.py preflight-host [--json] [--fix] [--dry-run]

Flags:
    --json     Saida estruturada (diagnostico).
    --fix      Bootstrapper assistido: detecta o package manager do host
               (winget > choco no Windows, brew no macOS, apt-get > dnf no
               Linux), monta o plano de instalacao oficial e executa cada
               passo somente apos confirmacao explicita do usuario. Ferramentas
               portateis (Node standalone, Hadolint) usam fallback user-space
               em ~/.aidd/bin, sem privilegios de administrador.
    --dry-run  Exibe exatamente o que o --fix faria (comandos e estrategias)
               sem executar nada — testavel em qualquer SO em CI.
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from typing import Dict, List, Optional, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AIDD_DIR = os.path.join(os.path.expanduser("~"), ".aidd")
AIDD_BIN = os.path.join(AIDD_DIR, "bin")

# Detectores canonicos de gates reutilizados como fonte unica de verdade.
# Guarded: se algum gate mudar de assinatura, o preflight continua funcional.
sys.path.insert(0, os.path.join(ROOT_DIR, "gates"))
try:
    from G_HADOLINT import encontrar_binario_hadolint as _encontrar_binario_hadolint
except Exception:
    _encontrar_binario_hadolint = None
try:
    from G_INFRA_COMPOSE import verificar_checkov_disponivel as _verificar_checkov_disponivel
except Exception:
    _verificar_checkov_disponivel = None

# ---------------------------------------------------------------------------
# Utilitarios
# ---------------------------------------------------------------------------

def _run(cmd: List[str], timeout: float = 5.0) -> Tuple[int, str]:
    """Executa comando e retorna (exit_code, stdout.strip()). Nunca levanta excecao."""
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def _versao_de_output(stdout: str) -> Optional[str]:
    """Extrai a primeira string que parece versao (X.Y.Z ou vX.Y.Z) de um stdout."""
    import re
    m = re.search(r"v?(\d+\.\d+[\.\d]*[^\s]*)", stdout)
    return m.group(1) if m else stdout.splitlines()[0] if stdout.strip() else None


def _candidato_aidd(binario: str) -> Optional[str]:
    """Retorna o caminho do binario instalado em ~/.aidd/bin (fallback user-space)."""
    ext = ".exe" if os.name == "nt" else ""
    candidato = os.path.join(AIDD_BIN, f"{binario}{ext}")
    if os.path.isfile(candidato) and os.access(candidato, os.X_OK):
        return candidato
    return None


def _para_texto(comando) -> str:
    """Converte um comando (argv list ou string de shell) em texto exibivel."""
    if isinstance(comando, str):
        return comando
    return " ".join(str(p) for p in comando)


# ---------------------------------------------------------------------------
# Detectores por binario
# ---------------------------------------------------------------------------

def _detectar_git() -> Dict:
    caminho = shutil.which("git")
    if not caminho:
        return {"binario": "git", "presente": False, "caminho": None, "versao": None, "instalar": "https://git-scm.com/downloads"}
    _, out = _run(["git", "--version"])
    return {"binario": "git", "presente": True, "caminho": caminho, "versao": _versao_de_output(out), "instalar": None}


def _detectar_node() -> Dict:
    caminho = shutil.which("node") or _candidato_aidd("node")
    if not caminho:
        return {"binario": "node", "presente": False, "caminho": None, "versao": None, "instalar": "https://nodejs.org/"}
    _, out = _run([caminho, "--version"])
    return {"binario": "node", "presente": True, "caminho": caminho, "versao": _versao_de_output(out), "instalar": None}


def _detectar_docker() -> Dict:
    caminho = shutil.which("docker")
    if not caminho:
        return {"binario": "docker", "presente": False, "caminho": None, "versao": None, "instalar": "https://docs.docker.com/get-docker/"}
    code, out = _run(["docker", "--version"])
    versao = _versao_de_output(out) if code == 0 else None
    return {"binario": "docker", "presente": True, "caminho": caminho, "versao": versao, "instalar": None}


def _detectar_hadolint() -> Dict:
    """Reutiliza G_HADOLINT.encontrar_binario_hadolint como fonte unica de verdade."""
    caminho = _encontrar_binario_hadolint() if _encontrar_binario_hadolint else None
    if not caminho:
        caminho = shutil.which("hadolint") or _candidato_aidd("hadolint")
    if not caminho:
        return {"binario": "hadolint", "presente": False, "caminho": None, "versao": None,
                "instalar": "winget install hadolint.hadolint / brew install hadolint (ou preflight-host --fix)"}
    _, out = _run([caminho, "--version"])
    return {"binario": "hadolint", "presente": True, "caminho": caminho, "versao": _versao_de_output(out), "instalar": None}


def _detectar_checkov() -> Dict:
    """Reutiliza G_INFRA_COMPOSE.verificar_checkov_disponivel como fonte unica de verdade."""
    presente = _verificar_checkov_disponivel() if _verificar_checkov_disponivel else None
    if presente is None:
        presente = shutil.which("checkov") is not None
    if not presente:
        return {"binario": "checkov", "presente": False, "caminho": None, "versao": None,
                "instalar": "pip install checkov"}
    caminho = shutil.which("checkov") or shutil.which("checkov.cmd") or "checkov"
    _, out = _run([caminho, "--version"])
    return {"binario": "checkov", "presente": True, "caminho": caminho, "versao": _versao_de_output(out), "instalar": None}


# ---------------------------------------------------------------------------
# Orquestracao principal (diagnostico)
# ---------------------------------------------------------------------------

_DETECTORES = [
    _detectar_git,
    _detectar_node,
    _detectar_docker,
    _detectar_hadolint,
    _detectar_checkov,
]


def executar_preflight() -> Dict:
    """Executa todos os detectores e retorna resultado consolidado."""
    resultados = []
    for detector in _DETECTORES:
        resultados.append(detector())
    ausentes = [r["binario"] for r in resultados if not r["presente"]]
    return {
        "sucesso": len(ausentes) == 0,
        "total": len(resultados),
        "presentes": sum(1 for r in resultados if r["presente"]),
        "ausentes": ausentes,
        "detalhes": resultados,
        "sistema": {
            "os": platform.system(),
            "arquitetura": platform.machine(),
            "python": platform.python_version(),
        },
    }


def _formatar_tabela(resultado: Dict) -> str:
    """Formata resultado como tabela legivel para terminal."""
    linhas = []
    linhas.append("=" * 72)
    linhas.append(" PREFLIGHT HOST — Diagnostico de Binarios do Sistema")
    linhas.append("=" * 72)
    linhas.append(f" OS: {resultado['sistema']['os']} | Arch: {resultado['sistema']['arquitetura']} | Python: {resultado['sistema']['python']}")
    linhas.append("-" * 72)
    linhas.append(f" {'Binario':<12} {'Status':<10} {'Versao':<22} {'Caminho'}")
    linhas.append("-" * 72)
    for d in resultado["detalhes"]:
        status = "[OK]" if d["presente"] else "[FALTA]"
        versao = d["versao"] or "-"
        caminho = d["caminho"] or "-"
        linhas.append(f" {d['binario']:<12} {status:<10} {versao:<22} {caminho}")
    linhas.append("-" * 72)
    if resultado["sucesso"]:
        linhas.append(f" RESULTADO: {resultado['presentes']}/{resultado['total']} binarios detectados — OK")
    else:
        linhas.append(f" RESULTADO: {resultado['presentes']}/{resultado['total']} binarios — AUSENTES: {', '.join(resultado['ausentes'])}")
        linhas.append("")
        for d in resultado["detalhes"]:
            if not d["presente"] and d.get("instalar"):
                linhas.append(f"   Instalar {d['binario']}: {d['instalar']}")
    linhas.append("=" * 72)
    return "\n".join(linhas)


# ---------------------------------------------------------------------------
# Bootstrapper assistido multi-OS
# ---------------------------------------------------------------------------

# Comandos oficiais de instalacao por (binario, gerente de pacotes).
# O valor e (comando, exige_sudo). Comando pode ser argv list ou string de
# shell (quando depende de pipe/encadeamento, ex.: nodesource no Debian).
_CONFIG_INSTALACAO = {
    "git": {
        "winget": (["winget", "install", "--id", "Git.Git", "-e", "--source", "winget"], False),
        "choco": (["choco", "install", "git", "-y"], False),
        "brew": (["brew", "install", "git"], False),
        "apt-get": ("sudo apt-get update && sudo apt-get install -y git", True),
        "dnf": ("sudo dnf install -y git", True),
    },
    "node": {
        "winget": (["winget", "install", "--id", "OpenJS.NodeJS.LTS", "-e", "--source", "winget"], False),
        "choco": (["choco", "install", "nodejs-lts", "-y"], False),
        "brew": (["brew", "install", "node"], False),
        "apt-get": ("curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs", True),
        "dnf": (["sudo", "dnf", "install", "-y", "nodejs"], True),
    },
    "docker": {
        "winget": (["winget", "install", "--id", "Docker.DockerDesktop", "-e", "--source", "winget"], False),
        "choco": (["choco", "install", "docker-desktop", "-y"], False),
        "brew": (["brew", "install", "--cask", "docker"], False),
        "apt-get": ("sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin", True),
        "dnf": ("sudo dnf install -y docker docker-compose-plugin", True),
    },
    "hadolint": {
        "winget": (["winget", "install", "--id", "hadolint.hadolint", "-e", "--source", "winget"], False),
        "choco": (["choco", "install", "hadolint", "-y"], False),
        "brew": (["brew", "install", "hadolint"], False),
    },
}

_URLS_MANUAIS = {
    "git": "https://git-scm.com/downloads",
    "node": "https://nodejs.org/",
    "docker": "https://docs.docker.com/get-docker/",
}


def detectar_package_manager() -> Dict:
    """Detecta o gerenciador de pacotes ativo no host.

    Prioridade: winget > choco (Windows), brew (macOS), apt-get > dnf (Linux).
    Retorna {"sistema", "gerenciador", "caminho"}; gerenciador None se ausente.
    """
    sistema = platform.system().lower()
    if sistema == "windows":
        for nome in ("winget", "choco"):
            caminho = shutil.which(nome)
            if caminho:
                return {"sistema": sistema, "gerenciador": nome, "caminho": caminho}
        return {"sistema": sistema, "gerenciador": None, "caminho": None}
    if sistema == "darwin":
        caminho = shutil.which("brew")
        if not caminho:
            for cand in ("/opt/homebrew/bin/brew", "/usr/local/bin/brew"):
                if os.path.isfile(cand) and os.access(cand, os.X_OK):
                    caminho = cand
                    break
        if caminho:
            return {"sistema": sistema, "gerenciador": "brew", "caminho": caminho}
        return {"sistema": sistema, "gerenciador": None, "caminho": None}
    for nome in ("apt-get", "dnf"):
        caminho = shutil.which(nome)
        if caminho:
            return {"sistema": sistema, "gerenciador": nome, "caminho": caminho}
    return {"sistema": sistema, "gerenciador": None, "caminho": None}


def montar_comando_instalacao(binario: str, gerenciador: str) -> Optional[Dict]:
    """Monta o comando oficial de instalacao de um binario no gerenciador dado.

    Retorna dict com 'comandos' (argv lists e/ou strings de shell),
    'comando_texto', 'exige_sudo' e 'gerenciador'; None se nao ha comando
    oficial mapeado para o par.
    """
    entrada = _CONFIG_INSTALACAO.get(binario, {}).get(gerenciador)
    if not entrada:
        return None
    comando, exige_sudo = entrada
    comandos = [comando] if isinstance(comando, str) else [comando]
    return {
        "binario": binario,
        "gerenciador": gerenciador,
        "comandos": comandos,
        "comando_texto": " && ".join(_para_texto(c) for c in comandos),
        "exige_sudo": exige_sudo,
        "estrategia": "package-manager",
        "execucao": "package-manager",
        "instrucao_path": None,
    }


def _comando_pip_checkov() -> List[str]:
    """pip install checkov — preferindo --user fora de venv (sem admin)."""
    base = [sys.executable, "-m", "pip", "install"]
    if sys.prefix == sys.base_prefix:
        base.append("--user")
    base.append("checkov")
    return base


def _instrucao_path() -> str:
    """Instrucao para colocar ~/.aidd/bin no PATH do usuario."""
    if os.name == "nt":
        return f"Adicione '{AIDD_BIN}' ao PATH do usuario (System Properties > Environment Variables)"
    return f"Adicione '{AIDD_BIN}' ao PATH: export PATH=\"{AIDD_BIN}:$PATH\" (em ~/.bashrc ou ~/.zshrc)"


def _passo_userspace(binario: str) -> Dict:
    """Monta passo de fallback user-space (~/.aidd/bin) para ferramenta portatil."""
    if binario == "node":
        return {
            "binario": "node",
            "estrategia": "user-space",
            "execucao": "node-standalone",
            "comandos": [],
            "comando_texto": (f"Baixar o pacote oficial do Node LTS (nodejs.org/dist) e ativa-lo em {AIDD_BIN} "
                              "— sem privilegios de administrador"),
            "exige_sudo": False,
            "instrucao_path": _instrucao_path(),
        }
    return {
        "binario": "hadolint",
        "estrategia": "user-space",
        "execucao": "hadolint-standalone",
        "comandos": [],
        "comando_texto": (f"Baixar o binario standalone do hadolint (GitHub releases) para {AIDD_BIN} "
                          "— sem privilegios de administrador"),
        "exige_sudo": False,
        "instrucao_path": _instrucao_path(),
    }


def _passos_para_ausente(binario: str, gerenciador: Optional[str]) -> List[Dict]:
    """Decide a estrategia de reparo para um binario ausente."""
    if binario == "checkov":
        cmd = _comando_pip_checkov()
        return [{
            "binario": "checkov",
            "estrategia": "pip-user",
            "execucao": "package-manager",
            "comandos": [cmd],
            "comando_texto": " ".join(cmd),
            "exige_sudo": False,
            "instrucao_path": None,
        }]

    # Portateis (Node standalone, Hadolint) usam PM de privilegio baixo quando
    # disponivel; senao caem no fallback user-space ~/.aidd/bin.
    if binario in ("node", "hadolint"):
        if gerenciador in ("winget", "choco", "brew"):
            passo = montar_comando_instalacao(binario, gerenciador)
            return [passo] if passo else [_passo_userspace(binario)]
        return [_passo_userspace(binario)]

    # git / docker: PM se houver; sem PM, instrucao manual com URL oficial.
    if gerenciador:
        passo = montar_comando_instalacao(binario, gerenciador)
        if passo:
            return [passo]
    return [{
        "binario": binario,
        "estrategia": "manual",
        "execucao": None,
        "comandos": [],
        "comando_texto": f"Instalar {binario} manualmente — fonte oficial: {_URLS_MANUAIS.get(binario, 'site do fabricante')}",
        "exige_sudo": False,
        "instrucao_path": None,
    }]


def montar_plano_fix(resultado: Dict, pm: Optional[Dict]) -> List[Dict]:
    """Monta o plano assistido de reparo (passos) para os binarios ausentes."""
    gerenciador = (pm or {}).get("gerenciador")
    plano = []
    for detalhe in resultado.get("detalhes", []):
        if detalhe.get("presente"):
            continue
        plano.extend(_passos_para_ausente(detalhe["binario"], gerenciador))
    return plano


def _sudo_silencioso_disponivel() -> bool:
    """True se sudo nao pede senha (sudo -n) — necessario p/ execucao nao-interativa."""
    if sys.platform == "win32" or shutil.which("sudo") is None:
        return False
    codigo, _ = _run(["sudo", "-n", "true"], timeout=5.0)
    return codigo == 0


def _executar_passo(passo: Dict) -> Tuple[int, str]:
    """Executa um passo do plano. Retorna (exit_code, mensagem)."""
    execucao = passo.get("execucao")
    if execucao == "node-standalone":
        return instalar_node_standalone()
    if execucao == "hadolint-standalone":
        return instalar_hadolint_aidd()

    comandos = passo.get("comandos") or []
    if not comandos:
        return False, "passo sem comando executavel"
    for cmd in comandos:
        shell = isinstance(cmd, str)
        caminho = cmd if shell else list(cmd)
        try:
            proc = subprocess.run(
                caminho,
                shell=shell,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=900,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, f"falha ao executar '{_para_texto(cmd)}': {exc}"
        if proc.returncode != 0:
            detalhe = (proc.stderr or "").strip() or (proc.stdout or "").strip()
            return False, f"comando falhou (exit {proc.returncode}): {_para_texto(cmd)} — {detalhe[:200]}"
    return True, "comando(s) executado(s) com sucesso"


def bootstrapper_assistido(resultado: Dict, dry_run: bool = False, pm: Optional[Dict] = None) -> int:
    """Bootstrapper assistido multi-OS.

    - Monta plano para os binarios ausentes usando o package manager ativo.
    - dry_run=True: apenas exibe os comandos, nunca executa nem pergunta.
    - dry_run=False: pede confirmacao explicita por passo antes de executar.
    Retorna 0 se nenhum binario falta ao final; 1 caso contrario.
    """
    pm = pm if pm is not None else detectar_package_manager()
    gerenciador = (pm or {}).get("gerenciador")
    plano = montar_plano_fix(resultado, pm)

    if not plano:
        if dry_run:
            print("[DRY-RUN] Nenhuma correcao necessaria — todos os binarios presentes.")
        else:
            print("Todos os binarios detectados. Nenhuma correcao necessaria.")
        return 0

    modo = "dry-run (nada sera executado)" if dry_run else "com confirmacao por passo"
    print("=" * 72)
    print(" BOOTSTRAPPER ASSISTIDO MULTI-OS")
    print("=" * 72)
    print(f" Gerenciador de pacotes ativo: {gerenciador or 'nenhum detectado'}")
    print(f" Modo: {modo}")
    print("=" * 72)

    interativo = sys.stdin.isatty()
    total = len(plano)
    for idx, passo in enumerate(plano, start=1):
        print(f"\n[{idx}/{total}] {passo['binario']} — estrategia '{passo['estrategia']}'")
        print(f"   Comando: {passo['comando_texto']}")
        if passo.get("instrucao_path"):
            print(f"   PATH:    {passo['instrucao_path']}")
        if passo.get("exige_sudo"):
            print("   (exige privilegios de administrador)")
        if dry_run:
            print("   [DRY-RUN] comando exibido, NAO executado.")
            continue
        if passo["estrategia"] == "manual":
            print("   Execute o comando acima no seu terminal e rode preflight-host --fix novamente.")
            continue
        if passo.get("exige_sudo") and not _sudo_silencioso_disponivel():
            print("   Sudo/senha nao podem ser fornecidos em modo nao-interativo.")
            print("   Rode o comando acima manualmente e depois rode preflight-host --fix de novo.")
            continue
        if not interativo:
            print("   Terminal nao-interativo detectado: execute o comando acima manualmente.")
            continue
        resposta = input("   Executar agora? [s/N]: ").strip().lower()
        if resposta not in ("s", "sim", "y", "yes"):
            print("   Pulado pelo usuario.")
            continue
        ok, msg = _executar_passo(passo)
        print(f"   -> {msg}")
        if not ok:
            print("   Instalacao falhou. Instale manualmente e rode --fix novamente.")

    if dry_run:
        print("\n[DRY-RUN] Plano exibido. Nenhum comando foi executado.")
        return 1

    print("\nReexecutando diagnostico para verificar o delta...")
    resultado_final = executar_preflight()
    print(_formatar_tabela(resultado_final))
    if resultado_final["sucesso"]:
        print("FIX CONCLUIDO — todos os binarios agora estao presentes.")
        return 0
    print(f"FIX PARCIAL — ainda faltam: {', '.join(resultado_final['ausentes'])}")
    return 1


# ---------------------------------------------------------------------------
# Instaladores user-space (~/.aidd/bin)
# ---------------------------------------------------------------------------

def _plataforma_user_space() -> Dict[str, str]:
    """Mapeia sistema/arquitetura corrente para o sufixo oficial do pacote."""
    sistema = platform.system().lower()
    maquina = platform.machine().lower()
    if sistema == "windows":
        arch = "arm64" if maquina in ("arm64", "aarch64") or "arm" in maquina else "x64"
        return {"os": "win", "arch": arch, "ext": "zip"}
    if sistema == "darwin":
        arch = "arm64" if maquina in ("arm64", "aarch64") else "x64"
        return {"os": "darwin", "arch": arch, "ext": "tar.gz"}
    arch = "arm64" if maquina in ("arm64", "aarch64") else "x64"
    return {"os": "linux", "arch": arch, "ext": "tar.xz"}


def _baixar(url: str, destino: str, timeout: int = 120) -> Tuple[int, str]:
    """Baixa conteudo de URL oficial para diretoria. Retorna (exit_code, msg)."""
    req = urllib.request.Request(url, headers={"User-Agent": "aidd-preflight-bootstrapper/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp, open(destino, "wb") as f:
            shutil.copyfileobj(resp, f)
        return 0, f"baixado: {os.path.basename(destino)}"
    except Exception as exc:
        return 1, f"falha no download de {url}: {exc}"


def url_node_lts() -> Tuple[Optional[str], Optional[str]]:
    """Resolve a URL oficial de download do Node LTS atual.

    Consulta nodejs.org/dist/index.json e retorna (url, versao).
    Sem rede ou em erro, retorna (None, None) — o chamador decide.
    """
    try:
        req = urllib.request.Request(
            "https://nodejs.org/dist/index.json",
            headers={"User-Agent": "aidd-preflight-bootstrapper/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            indice = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None, None
    for entrada in indice:
        if entrada.get("lts"):
            versao = entrada["version"]  # ex.: "v22.14.0"
            pl = _plataforma_user_space()
            arquivo = f"node-{versao}-{pl['os']}-{pl['arch']}.{pl['ext']}"
            return f"https://nodejs.org/dist/{versao}/{arquivo}", versao
    return None, None


def _extrair_arquivo(caminho: str, destino: str) -> None:
    """Extrai zip/tar.gz/tar.xz em destino (cria a pasta)."""
    os.makedirs(destino, exist_ok=True)
    if caminho.endswith(".zip"):
        with zipfile.ZipFile(caminho) as zf:
            zf.extractall(destino)
        return
    modo = "r:xz" if caminho.endswith(".tar.xz") else "r:gz"
    with tarfile.open(caminho, modo) as tf:
        try:
            tf.extractall(destino, filter="data")
        except TypeError:
            tf.extractall(destino)


def _localizar_node_exe(dir_node: str) -> Optional[str]:
    """Localiza o executavel 'node'/'node.exe' dentro do pacote extraido."""
    nome = "node.exe" if os.name == "nt" else "node"
    for root, _, files in os.walk(dir_node):
        if nome in files:
            return os.path.join(root, nome)
    return None


def _escrever_shim_cmd(destino_bin: str, nome: str, origem_abs: str) -> None:
    """Cria shim .cmd apontando para o comando real do pacote extraido (Windows)."""
    shim = os.path.join(destino_bin, f"{nome}.cmd")
    origem = origem_abs.replace("/", os.sep)
    conteudo = f'@echo off\r\n"{origem}" %*\r\n'
    with open(shim, "w", encoding="utf-8") as f:
        f.write(conteudo)


def _criar_link_posix(origem: str, destino: str) -> None:
    """Cria symlink se possivel; senao wrapper de shell (POSIX)."""
    if os.path.exists(destino):
        os.remove(destino)
    try:
        os.symlink(origem, destino)
        return
    except OSError:
        pass
    with open(destino, "w", encoding="utf-8") as f:
        f.write(f'#!/bin/sh\nexec "{origem}" "$@"\n')
    os.chmod(destino, 0o755)


def _ativar_node(dir_node: str, destino_bin: str) -> Tuple[int, str]:
    """Cria shims (~/.aidd/bin) para node/npm/npx a partir do pacote extraido."""
    os.makedirs(destino_bin, exist_ok=True)
    node_bin = _localizar_node_exe(dir_node)
    if not node_bin:
        return 1, f"binario 'node' nao encontrado dentro de {dir_node}"

    if os.name == "nt":
        shutil.copy2(node_bin, os.path.join(destino_bin, "node.exe"))
        base = os.path.dirname(node_bin)
        ativados = ["node"]
        for nome in ("npm", "npx", "corepack"):
            origem = os.path.join(base, f"{nome}.cmd")
            if os.path.isfile(origem):
                _escrever_shim_cmd(destino_bin, nome, origem)
                ativados.append(nome)
        return 0, f"Node ativado em {destino_bin} ({', '.join(ativados)})"

    base = os.path.dirname(node_bin)
    ativados = []
    for nome in ("node", "npm", "npx", "corepack"):
        origem = os.path.join(base, nome)
        if not os.path.isfile(origem):
            continue
        _criar_link_posix(origem, os.path.join(destino_bin, nome))
        ativados.append(nome)
    if not ativados:
        return 1, "nenhum executavel node/npm/npx encontrado no pacote"
    return 0, f"Node ativado em {destino_bin} ({', '.join(ativados)})"


def instalar_node_standalone(destino_bin: Optional[str] = None, url: Optional[str] = None,
                             versao: Optional[str] = None, dir_aidd: Optional[str] = None) -> Tuple[int, str]:
    """Baixa a distribuicao oficial do Node LTS (zip/tar) e ativa em ~/.aidd/bin.

    Sem privilegios de administrador. Retorna (exit_code, mensagem).
    """
    destino_bin = destino_bin or AIDD_BIN
    dir_aidd = dir_aidd or AIDD_DIR
    if not url or not versao:
        url, versao = url_node_lts()
    if not url or not versao:
        return 1, "nao foi possivel resolver a versao LTS do Node (sem acesso a nodejs.org?)"
    if not versao.startswith("v"):
        versao = f"v{versao}"

    os.makedirs(destino_bin, exist_ok=True)
    tmp_dir = tempfile.mkdtemp(prefix="aidd-node-")
    pl = _plataforma_user_space()
    arquivo = f"node-{versao}-{pl['os']}-{pl['arch']}.{pl['ext']}"
    destino_arquivo = os.path.join(tmp_dir, arquivo)

    codigo, msg = _baixar(url, destino_arquivo)
    if codigo != 0:
        return codigo, msg

    dir_node = os.path.join(dir_aidd, f"node-{versao}")
    try:
        _extrair_arquivo(destino_arquivo, dir_node)
    except Exception as exc:
        return 1, f"falha ao extrair pacote do Node: {exc}"
    return _ativar_node(dir_node, destino_bin)


def url_hadolint_release() -> str:
    """URL oficial do binario standalone do hadolint (GitHub releases)."""
    os_name = platform.system().lower()
    maquina = platform.machine().lower()
    is_arm = maquina in ("arm64", "aarch64") or "arm" in maquina
    if os_name == "windows":
        suf = "Windows-arm64.exe" if is_arm else "Windows-x86_64.exe"
    elif os_name == "darwin":
        suf = "Darwin-arm64" if is_arm else "Darwin-x86_64"
    else:
        suf = "Linux-arm64" if is_arm else "Linux-x86_64"
    return f"https://github.com/hadolint/hadolint/releases/latest/download/hadolint-{suf}"


def instalar_hadolint_aidd(destino_bin: Optional[str] = None, url: Optional[str] = None) -> Tuple[int, str]:
    """Baixa o binario standalone do hadolint para ~/.aidd/bin (sem admin)."""
    destino_bin = destino_bin or AIDD_BIN
    os.makedirs(destino_bin, exist_ok=True)
    url = url or url_hadolint_release()
    sufixo = ".exe" if os.name == "nt" else ""
    destino = os.path.join(destino_bin, f"hadolint{sufixo}")
    codigo, msg = _baixar(url, destino)
    if codigo != 0:
        return codigo, msg
    if os.name != "nt":
        os.chmod(destino, 0o755)
    return 0, f"hadolint instalado em {destino}"


# ---------------------------------------------------------------------------
# CLI standalone
# ---------------------------------------------------------------------------

def main():
    # Windows abre stdout/stderr no codepage local (cp1252), que nao representa
    # emojis/travessoes — forca UTF-8 (mesmo padrao de ecossistema.py).
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Preflight Host — diagnostico de binarios + bootstrapper assistido multi-OS")
    parser.add_argument("--json", action="store_true", help="Saida em formato JSON")
    parser.add_argument("--fix", action="store_true",
                        help="Bootstrapper assistido: monta plano de instalacao e executa com confirmacao explicita")
    parser.add_argument("--dry-run", action="store_true",
                        help="Exibe os comandos de instalacao sem executar nada (so com --fix)")
    args = parser.parse_args()

    resultado = executar_preflight()

    if args.fix:
        if args.json:
            print(json.dumps(resultado, indent=2, ensure_ascii=False))
        sys.exit(bootstrapper_assistido(resultado, dry_run=args.dry_run))

    if args.json:
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    else:
        print(_formatar_tabela(resultado))
    sys.exit(0 if resultado["sucesso"] else 1)


if __name__ == "__main__":
    main()