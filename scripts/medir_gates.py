#!/usr/bin/env python3
"""
scripts/medir_gates.py — Medição real do tempo de execução de cada Quality Gate.

Lê os hooks definidos em .pre-commit-config.yaml (ou arquivo apontado por --config),
executa cada comando medindo a duração com time.perf_counter, e grava os resultados
em formato JSON em secoes/medicoes/gates-<DATE>-<MODE>.json (ou arquivo apontado por --saida).

Suporta as flags:
  --modo: 'rapido' ou 'completo' (define AIDD_GATES_MODO no ambiente do subprocesso)
  --so: id específico de um hook para medição isolada
  --saida: caminho customizado para o arquivo JSON de resultado
  --config: caminho customizado para o arquivo de configuração YAML (padrão: .pre-commit-config.yaml)
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent


def extrair_hooks(caminho_yaml: Path) -> List[Dict[str, Any]]:
    """Lê o arquivo YAML e retorna a lista de hooks com id e entry."""
    if not caminho_yaml.exists():
        raise FileNotFoundError(f"Arquivo de configuracao nao encontrado: {caminho_yaml}")

    with open(caminho_yaml, "r", encoding="utf-8") as f:
        dados = yaml.safe_load(f) or {}

    hooks = []
    repos = dados.get("repos", [])
    for repo in repos:
        for hook in repo.get("hooks", []):
            hook_id = hook.get("id")
            entry = hook.get("entry")
            if hook_id and entry:
                hooks.append(hook)
    return hooks


def formatar_comando(entry: str) -> str:
    """Garante que chamadas a 'python' utilizem o sys.executable atual."""
    entry_limpo = entry.strip()
    if entry_limpo.startswith("python "):
        resto = entry_limpo[len("python "):]
        return f'"{sys.executable}" {resto}'
    elif entry_limpo == "python":
        return f'"{sys.executable}"'
    return entry_limpo


def medir_gates(
    caminho_config: Optional[Path] = None,
    modo: str = "rapido",
    so_hook: Optional[str] = None,
    caminho_saida: Optional[Path] = None,
    cwd: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Executa a medição dos gates e grava o JSON de resultados.
    Retorna a lista de medições.
    """
    if caminho_config is None:
        caminho_config = ROOT_DIR / ".pre-commit-config.yaml"
    if cwd is None:
        cwd = Path.cwd()

    todos_hooks = extrair_hooks(caminho_config)

    # Filtragem por --so
    if so_hook:
        hooks_para_rodar = [h for h in todos_hooks if h.get("id") == so_hook]
        if not hooks_para_rodar:
            print(f"[medir_gates] ERRO: Hook com id '{so_hook}' nao encontrado em {caminho_config}", file=sys.stderr)
            return []
    else:
        hooks_para_rodar = []
        for h in todos_hooks:
            stages = h.get("stages", [])
            # Hooks puramente manuais (como chamadas LLM) nao rodam em lote a menos que especificado
            if "manual" in stages and "pre-commit" not in stages:
                continue
            hooks_para_rodar.append(h)

    # Prepara ambiente com o modo
    env = os.environ.copy()
    env["AIDD_GATES_MODO"] = modo
    # Força buffering desativado para python subprocessos
    env["PYTHONUNBUFFERED"] = "1"

    resultados: List[Dict[str, Any]] = []

    print(f"[medir_gates] Iniciando medicao de {len(hooks_para_rodar)} gates (modo={modo})...")

    for hook in hooks_para_rodar:
        hook_id = hook["id"]
        entry = hook["entry"]
        cmd = formatar_comando(entry)

        print(f"[medir_gates] Executando gate: {hook_id}...")
        t0 = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=str(cwd),
                env=env,
                capture_output=True,
                text=True
            )
            exit_code = proc.returncode
        except Exception as e:
            print(f"[medir_gates] Excecao ao executar {hook_id}: {e}", file=sys.stderr)
            exit_code = 1

        t1 = time.perf_counter()
        segundos = round(t1 - t0, 4)

        status_str = "PASS" if exit_code == 0 else f"FAIL (exit {exit_code})"
        print(f"[medir_gates] {hook_id}: {status_str} em {segundos:.2f}s")

        resultados.append({
            "id": hook_id,
            "segundos": segundos,
            "exit_code": exit_code,
            "modo": modo
        })

    # Determina arquivo de saída se não fornecido
    if caminho_saida is None:
        data_str = datetime.now().strftime("%Y-%m-%d")
        destino_dir = cwd / "secoes" / "medicoes"
        caminho_saida = destino_dir / f"gates-{data_str}-{modo}.json"
    else:
        caminho_saida = Path(caminho_saida)

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_saida, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"[medir_gates] Medicao concluida. Resultado gravado em: {caminho_saida}")
    return resultados


# ---------------------------------------------------------------------------
# pre-push: código só sobe com a bateria completa verde para aquele conteúdo.
#
# O registro verde é por ÁRVORE (tree hash), não por commit: o merge do --aprovar
# tem SHA novo mas a mesma árvore que passou no gate_final, então não repete os
# ~25 min da bateria. Push só de documentação passa sem bateria.
# ---------------------------------------------------------------------------

ZEROS = "0" * 40
PASTA_REGISTROS = Path("secoes") / "medicoes"
PREFIXOS_SO_DOC = ("secoes/", "docs/")


def _git(raiz: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=str(raiz), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", check=True).stdout


def arvore_de(raiz: Path, ref: str) -> str:
    return _git(raiz, "rev-parse", f"{ref}^{{tree}}").strip()


def git_common_dir(raiz: Path) -> Path:
    try:
        saida = _git(raiz, "rev-parse", "--git-common-dir").strip()
        p = Path(saida)
        return p if p.is_absolute() else (Path(raiz) / p).resolve()
    except Exception:
        return Path(raiz) / ".git"


def registro_verde(raiz: Path, arvore: str) -> Path:
    comum = git_common_dir(raiz) / "aidd_audit" / f"completo-{arvore}.json"
    if comum.is_file():
        return comum
    return Path(raiz) / PASTA_REGISTROS / f"completo-{arvore}.json"


def registrar_bateria_verde(raiz: Path, ref: str = "HEAD") -> Path:
    """Grava que a bateria completa passou para a árvore de `ref` (chamado por audit e gate_final)."""
    arvore = arvore_de(raiz, ref)
    caminho = git_common_dir(raiz) / "aidd_audit" / f"completo-{arvore}.json"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conteudo = json.dumps({"arvore": arvore, "ref": _git(raiz, "rev-parse", ref).strip(),
                           "modo": "completo", "exit_code": 0,
                           "em": datetime.now().isoformat(timespec="seconds")},
                          ensure_ascii=False, indent=2) + "\n"
    caminho.write_text(conteudo, encoding="utf-8", newline="\n")
    legado = Path(raiz) / PASTA_REGISTROS / f"completo-{arvore}.json"
    if legado.parent.is_dir():
        legado.write_text(conteudo, encoding="utf-8", newline="\n")
    return caminho



def so_documentacao(arquivos: List[str]) -> bool:
    return all(a.startswith(PREFIXOS_SO_DOC) or a.endswith(".md") for a in arquivos)


def _arquivos_do_push(raiz: Path, sha_local: str, sha_remoto: str) -> List[str]:
    if sha_remoto == ZEROS:  # branch nova no remoto: commits que nenhum remoto tem ainda
        commits = _git(raiz, "rev-list", sha_local, "--not", "--remotes").split()
    else:
        commits = _git(raiz, "rev-list", f"{sha_remoto}..{sha_local}").split()
    arquivos = set()
    for commit in commits:
        arquivos.update(_git(raiz, "diff-tree", "--no-commit-id", "--name-only", "-r", "-m", commit).split())
    return sorted(arquivos)


def _ultimo_commit_aprovado(raiz: Path, sha_local: str, sha_remoto: str) -> Optional[str]:
    """Commit mais novo do push cuja árvore tem registro verde (ex.: o merge do --aprovar)."""
    faixa = [sha_local, "--not", "--remotes"] if sha_remoto == ZEROS else [f"{sha_remoto}..{sha_local}"]
    for commit in _git(raiz, "rev-list", *faixa).split():
        if registro_verde(raiz, arvore_de(raiz, commit)).is_file():
            return commit
    return None


def _bateria_completa(raiz: Path) -> int:
    env = {**os.environ, "AIDD_GATES_MODO": "completo"}
    return subprocess.run([sys.executable, "ecossistema.py", "audit"], cwd=str(raiz), env=env).returncode


def verificar_push(linhas: List[str], raiz: Path, rodar_bateria=_bateria_completa, avisar=print) -> int:
    """Linhas do stdin do pre-push: '<ref local> <sha local> <ref remota> <sha remoto>'."""
    for linha in linhas:
        partes = linha.split()
        if len(partes) != 4 or partes[1] == ZEROS:  # linha vazia ou remoção de branch
            continue
        _, sha_local, ref_remota, sha_remoto = partes
        arquivos = _arquivos_do_push(raiz, sha_local, sha_remoto)
        if not arquivos or so_documentacao(arquivos):
            avisar(f"[pre-push] {ref_remota}: só documentação/sessões ({len(arquivos)} arquivo(s)), sem bateria.")
            continue
        arvore = arvore_de(raiz, sha_local)
        if registro_verde(raiz, arvore).is_file():
            avisar(f"[pre-push] {ref_remota}: bateria completa já aprovada para este conteúdo (árvore {arvore[:10]}).")
            continue
        aprovado = _ultimo_commit_aprovado(raiz, sha_local, sha_remoto)
        if aprovado and so_documentacao(_git(raiz, "diff", "--name-only", aprovado, sha_local).split()):
            avisar(f"[pre-push] {ref_remota}: bateria completa aprovada em {aprovado[:10]}; depois dele só documentação.")
            continue
        avisar(f"[pre-push] {ref_remota}: {len(arquivos)} arquivo(s) de código sem bateria completa verde. Rodando agora...")
        if _git(raiz, "rev-parse", "HEAD").strip() != sha_local:
            avisar(f"[pre-push] BLOQUEADO: o commit enviado ({sha_local[:10]}) não é o HEAD; faça checkout dele e rode de novo.")
            return 1
        if rodar_bateria(raiz) != 0:
            avisar("[pre-push] BLOQUEADO: bateria completa reprovou. Corrija antes do push.")
            return 1
        registrar_bateria_verde(raiz, sha_local)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Medição real do tempo de cada Quality Gate do ecossistema AIDD."
    )
    parser.add_argument(
        "--modo",
        choices=["rapido", "completo"],
        default="rapido",
        help="Modo de execução (define AIDD_GATES_MODO). Padrão: rapido"
    )
    parser.add_argument(
        "--so",
        dest="so_hook",
        metavar="HOOK_ID",
        help="Executa apenas o hook com o ID especificado."
    )
    parser.add_argument(
        "--saida",
        dest="saida",
        metavar="PATH",
        help="Caminho personalizado para salvar o relatório JSON."
    )
    parser.add_argument(
        "--config",
        dest="config",
        metavar="PATH",
        help="Caminho para o arquivo YAML de configuração de gates (padrão: .pre-commit-config.yaml)."
    )

    parser.add_argument(
        "--verificar-push",
        action="store_true",
        help="Modo pre-push: lê o stdin do hook e exige bateria completa verde para push com código."
    )

    args = parser.parse_args(argv)

    if args.verificar_push:
        return verificar_push(sys.stdin.read().splitlines(), Path.cwd())

    caminho_config = Path(args.config) if args.config else None
    caminho_saida = Path(args.saida) if args.saida else None

    try:
        medicoes = medir_gates(
            caminho_config=caminho_config,
            modo=args.modo,
            so_hook=args.so_hook,
            caminho_saida=caminho_saida,
            cwd=Path.cwd()
        )
        if args.so_hook and not medicoes:
            return 1
        return 0
    except Exception as e:
        print(f"[medir_gates] Erro fatal: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
