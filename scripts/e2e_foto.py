# -*- coding: utf-8 -*-
"""Foto E2E repetível e comparação automática do ecossistema-aidd (Ticket 2, D12).

Uso:
    python scripts/e2e_foto.py rodar --ciclo auto [--raiz DIR] [--worktree DIR]
    python scripts/e2e_foto.py comparar --base ciclo-01 [--novo ultimo]
                                         [--raiz DIR] [--saida ARQ.md]

`rodar` porta os scripts do ciclo-01 (`_evidencias/rodar_fluxo.py`,
`rodar_continuacao.py`, `checar_quarteto.py`, `consolidar.py`) para um comando
só: cria um worktree isolado, roda os 3 fluxos + continuação + sonda do
Quarteto e grava `RESULTADO-E2E.json` por fluxo numa pasta de ciclo fora do
repo (`TESTES_E2E-ecossistema-aidd/ciclo-NN/`).

`comparar` lê a base e o ciclo novo e compara: exit, etapa em que quebrou,
Quarteto, vazamentos, duplicatas, tempo de gate, tokens e órfãos do
inventário. Grava `COMPARACAO-E2E.md` e sai com exit 1 se alguma métrica
piorar (exit 0 = nenhuma piorou; exit 2 = erro de uso/infraestrutura).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

FLUXOS = {
    "pure": ("fluxo-01-pure", "Gestao Tarefas", "gestao-tarefas", "produtividade"),
    "open": ("fluxo-02-open", "Portal Atendimento", "portal-atendimento", "atendimento"),
    "freedom": ("fluxo-03-freedom", "Conexao Hub", "conexao-hub", "hub"),
}
ETAPA_ORDEM = ["forge", "planner", "builder", "master", "enterprise", "ops", "auditoria"]
ETAPA_POR_NUMERO = {"1": "forge", "2": "planner", "3": "builder", "4": "master",
                    "5": "enterprise", "6": "ops", "7": "auditoria"}
IGNORAR = {".git", "node_modules", "__pycache__", ".pytest_cache", ".hypothesis"}
RUIDO = ("__pycache__", "graph.db")
ERRO_RE = re.compile(
    r"(FACTORY_INPUT_INVALID[^\n]*|PIPELINE FALHOU[^\n]*|RuntimeError:[^\n]*|"
    r"fatal:[^\n]*|Timeout ao aguardar[^\n]*|Modo Headless n[^\n]*|No module named[^\n]*)")
FALHA_ETAPA_RE = re.compile(r"FALHA CR[IÍ]TICA na Etapa (\d)")
METRICAS_CICLO = ("duplicatas", "tempo_gate_s", "tokens", "orfaos_inventario")
QUARTETO_PADRAO = {"api": "não (etapa master não alcançada)", "webhook": "não",
                   "mcp": "não", "docs": "não"}
TOKENS_PADRAO = ("não mensurável: nenhuma chamada LLM concluída "
                 "(protocolo delegado sem resposta / sem chave headless)")
ORIGEM_URL = "https://github.com/heverton-dev/conexao-hub"


def raiz_padrao() -> Path:
    """Raiz das pastas de ciclo: env AIDD_E2E_RAIZ > Desktop > Desktop/01_projetos_apps > irmão do repo.
    A pasta foi para Desktop/01_projetos_apps/testes-e2e-ecossistema-aidd em 05/10/2026 (ciclo-03 T21)."""
    env = os.environ.get("AIDD_E2E_RAIZ")
    if env:
        return Path(env)
    candidatos = [
        Path.home() / "Desktop" / "TESTES_E2E-ecossistema-aidd",
        Path.home() / "Desktop" / "01_projetos_apps" / "testes-e2e-ecossistema-aidd",
        Path(__file__).resolve().parents[1].parent / "TESTES_E2E-ecossistema-aidd",
    ]
    for c in candidatos:
        if c.exists():
            return c
    return candidatos[0]


def resolver_ciclo(arg: str, raiz: Path) -> Path:
    if arg == "ultimo":
        candidatos = [p for p in raiz.glob("ciclo-*")
                      if p.name.split("ciclo-", 1)[-1].isdigit()]
        candidatos.sort(key=lambda p: int(p.name.split("ciclo-", 1)[-1]))
        if not candidatos:
            print(f"erro: nenhum ciclo-* em {raiz}", file=sys.stderr)
            sys.exit(2)
        return candidatos[-1]
    direto = Path(arg)
    if direto.exists():
        return direto
    em_raiz = raiz / arg
    if em_raiz.exists():
        return em_raiz
    print(f"erro: ciclo nao encontrado: {arg} (raiz={raiz})", file=sys.stderr)
    sys.exit(2)


def carregar_fluxos(ciclo: Path) -> dict:
    fluxos = {}
    for pasta in sorted(ciclo.glob("fluxo-*")):
        arquivo = pasta / "RESULTADO-E2E.json"
        if arquivo.exists():
            fluxos[pasta.name] = json.loads(arquivo.read_text(encoding="utf-8"))
    return fluxos


def _metricas_baseline_md(ciclo: Path) -> dict:
    """Fallback: extrai duplicatas/tempo de gate do BASELINE-E2E.md do ciclo."""
    md = ciclo / "BASELINE-E2E.md"
    if not md.exists():
        return {}
    texto = md.read_text(encoding="utf-8", errors="replace")
    out = {}
    m = re.search(r"Conteúdos repetidos em 2\+ ferramentas \| (\d+)", texto)
    if m:
        out["duplicatas"] = int(m.group(1))
    m = re.search(r"Bateria de gates[^|\n]*\| exit \d+ em (\d+) s", texto)
    if m:
        out["tempo_gate_s"] = int(m.group(1))
    return out


def carregar_metricas_ciclo(ciclo: Path) -> dict:
    arquivo = ciclo / "METRICAS-CICLO.json"
    if arquivo.exists():
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        return {k: dados[k] for k in METRICAS_CICLO if k in dados}
    return _metricas_baseline_md(ciclo)


def _numero(valor):
    if isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str):
        apenas = valor.strip().replace(",", ".")
        if re.fullmatch(r"-?\d+(\.\d+)?", apenas):
            return float(apenas)
    return None


def rank_quebrou(valor):
    """Menor = quebrou mais cedo. None (não quebrou) = melhor de todos."""
    if valor is None:
        return len(ETAPA_ORDEM) + 10
    nome = str(valor).strip().lower().split()[0] if str(valor).strip() else ""
    if nome in ETAPA_ORDEM:
        return ETAPA_ORDEM.index(nome)
    return -1  # etapa desconhecida tratada como a pior possível


def _rota_responde(valor) -> bool:
    if isinstance(valor, dict):
        return bool(valor.get("responde"))
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().lower().startswith("sim")
    return bool(valor)


def contar_quarteto(resultado: dict) -> int:
    q = resultado.get("quarteto") or {}
    if not isinstance(q, dict):
        return 0
    return sum(1 for v in q.values() if _rota_responde(v))


def conjunto_vazamentos(resultado: dict) -> set:
    bruto = (resultado.get("vazamentos_fora_da_pasta")
             or resultado.get("vazamentos") or {})
    itens: list = []
    if isinstance(bruto, dict):
        for valor in bruto.values():
            if isinstance(valor, list):
                itens.extend(valor)
            elif isinstance(valor, dict):
                for sub in valor.values():
                    if isinstance(sub, list):
                        itens.extend(sub)
                    elif isinstance(sub, str):
                        itens.append(sub)
            elif isinstance(valor, str):
                itens.append(valor)
    elif isinstance(bruto, list):
        itens.extend(bruto)
    return {str(x) for x in itens if not any(r in str(x) for r in RUIDO)}


def _linha(escopo: str, metrica: str, base, novo, pior, obs: str = "") -> dict:
    return {"escopo": escopo, "metrica": metrica, "base": base, "novo": novo,
            "pior": pior, "obs": obs}


def comparar_fluxo(nome: str, base: dict, novo: dict | None) -> list:
    linhas = []
    if novo is None:
        linhas.append(_linha(nome, "presenca", "presente", "AUSENTE", True,
                             "fluxo sumiu do ciclo novo"))
        return linhas

    b_exit, n_exit = base.get("exit_code"), novo.get("exit_code")
    linhas.append(_linha(nome, "exit_code", b_exit, n_exit,
                         (n_exit > b_exit) if _numero(b_exit) is not None
                         and _numero(n_exit) is not None else None))

    b_q, n_q = base.get("quebrou_em"), novo.get("quebrou_em")
    linhas.append(_linha(nome, "quebrou_em", b_q, n_q, rank_quebrou(n_q) < rank_quebrou(b_q)))

    b_rotas, n_rotas = contar_quarteto(base), contar_quarteto(novo)
    linhas.append(_linha(nome, "quarteto", f"{b_rotas}/4 rotas", f"{n_rotas}/4 rotas",
                         n_rotas < b_rotas))

    b_vaz, n_vaz = conjunto_vazamentos(base), conjunto_vazamentos(novo)
    linhas.append(_linha(nome, "vazamentos", len(b_vaz), len(n_vaz), len(n_vaz) > len(b_vaz),
                         "; ".join(sorted(n_vaz - b_vaz)) if n_vaz - b_vaz else ""))

    b_tok, n_tok = _numero(base.get("tokens")), _numero(novo.get("tokens"))
    linhas.append(_linha(nome, "tokens", base.get("tokens"), novo.get("tokens"),
                         (n_tok > b_tok) if b_tok is not None and n_tok is not None else None,
                         "" if b_tok is not None and n_tok is not None else "não mensurável"))
    return linhas


def comparar_metricas(base_ciclo: Path, novo_ciclo: Path) -> list:
    b = carregar_metricas_ciclo(base_ciclo)
    n = carregar_metricas_ciclo(novo_ciclo)
    linhas = []
    for chave in METRICAS_CICLO:
        vb, vn = b.get(chave), n.get(chave)
        nb, nn = _numero(vb), _numero(vn)
        if nb is None or nn is None:
            pior = None
        else:
            pior = nn > nb
        linhas.append(_linha("ciclo", chave,
                             vb if vb is not None else "—",
                             vn if vn is not None else "—",
                             pior,
                             "" if pior is not None else "métrica ausente em um dos ciclos"))
    return linhas


def escrever_relatorio(caminho: Path, base: Path, novo: Path, linhas: list) -> list:
    piores = [l for l in linhas if l["pior"] is True]
    agora = time.strftime("%Y-%m-%d %H:%M:%S")
    linhas_md = [
        f"# Comparação E2E — `{base.name}` × `{novo.name}`",
        "",
        f"> Gerado por `scripts/e2e_foto.py comparar` em {agora}.",
        "",
        "## Fluxos e métricas",
        "",
        "| Escopo | Métrica | Base | Novo | Piorou | Obs |",
        "|---|---|---|---|---|---|",
    ]
    for l in linhas:
        marca = {True: "SIM", False: "não", None: "n/a"}[l["pior"]]
        linhas_md.append(
            f"| {l['escopo']} | {l['metrica']} | {l['base']} | {l['novo']} | {marca} | {l['obs']} |")
    linhas_md += ["", "## Veredito", ""]
    if piores:
        linhas_md.append(f"- ❌ {len(piores)} métrica(s) piorou(aram) vs a base:")
        for l in piores:
            linhas_md.append(
                f"  - `{l['escopo']}/{l['metrica']}`: base={l['base']} → novo={l['novo']}"
                + (f" ({l['obs']})" if l["obs"] else ""))
        linhas_md.append("- Exit 1")
    else:
        linhas_md.append("- ✅ nenhuma métrica piorou vs a base")
        linhas_md.append("- Exit 0")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n".join(linhas_md) + "\n", encoding="utf-8", newline="\n")
    return piores


def cmd_comparar(args) -> int:
    raiz = Path(args.raiz) if args.raiz else raiz_padrao()
    base = resolver_ciclo(args.base, raiz)
    novo = resolver_ciclo(args.novo, raiz)
    fluxos_base = carregar_fluxos(base)
    fluxos_novo = carregar_fluxos(novo)
    tem_metricas = (base / "METRICAS-CICLO.json").exists() or (base / "BASELINE-E2E.md").exists()
    if not fluxos_base and not tem_metricas:
        print(f"erro: nenhum RESULTADO-E2E.json nem métricas de ciclo em {base}",
              file=sys.stderr)
        return 2

    linhas: list = []
    for nome, dados in fluxos_base.items():
        linhas.extend(comparar_fluxo(nome, dados, fluxos_novo.get(nome)))
    linhas.extend(comparar_metricas(base, novo))

    saida = Path(args.saida) if args.saida else novo / "COMPARACAO-E2E.md"
    piores = escrever_relatorio(saida, base, novo, linhas)
    print(f"base={base} novo={novo} relatorio={saida}")
    for l in piores:
        print(f"PIOU {l['escopo']}/{l['metrica']}: {l['base']} -> {l['novo']}")
    if piores:
        print(f"VEREDITO: {len(piores)} metrica(s) piorou(aram) — exit 1")
        return 1
    print("VEREDITO: nenhuma metrica piorou — exit 0")
    return 0


# === PARTE_RODAR ===
# ---------------------------------------------------------------------------
# rodar: port de _evidencias/rodar_fluxo.py + rodar_continuacao.py +
#        checar_quarteto.py + consolidar.py (baseline ciclo-01).
# ---------------------------------------------------------------------------

def repo_raiz() -> Path:
    return Path(__file__).resolve().parents[1]


def git_status(raiz: Path) -> list:
    r = subprocess.run(["git", "status", "--porcelain", "--ignored", "-uall"],
                       cwd=str(raiz), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return sorted(r.stdout.splitlines())


def arquivos_mexidos(raiz: Path, desde: float) -> list:
    """Arquivos com mtime >= desde (pega escrita até dentro de pasta ignorada)."""
    achados = []
    for dirpath, dirnames, filenames in os.walk(raiz):
        dirnames[:] = [d for d in dirnames if d not in IGNORAR]
        for nome_arq in filenames:
            p = Path(dirpath) / nome_arq
            try:
                if p.stat().st_mtime >= desde:
                    achados.append(str(p.relative_to(raiz)))
            except OSError:
                pass
    return sorted(achados)


def topo_nomes(pasta: Path) -> list:
    return sorted(p.name for p in pasta.iterdir())


def nome_ciclo(arg: str, raiz: Path) -> str:
    if arg == "auto":
        numeros = []
        for p in raiz.glob("ciclo-*"):
            resto = p.name.split("ciclo-", 1)[-1]
            if resto.isdigit():
                numeros.append(int(resto))
        proximo = (max(numeros) + 1) if numeros else 1
        return f"ciclo-{proximo:02d}"
    if re.fullmatch(r"\d+", arg):
        return f"ciclo-{int(arg):02d}"
    if re.fullmatch(r"ciclo-\d+", arg):
        return arg
    print(f"erro: --ciclo invalido: {arg} (use auto ou ciclo-NN)", file=sys.stderr)
    sys.exit(2)


def preparar_worktree(repo: Path, wt: Path, nome: str) -> bool:
    """Cria a worktree do ciclo; True quando esta chamada a criou (quem cria remove no fim)."""
    if (wt / ".git").exists():
        print(f"worktree reaproveitado: {wt}")
        return False
    if wt.exists():
        print(f"erro: {wt} existe e nao e um worktree git", file=sys.stderr)
        sys.exit(2)
    branch = f"aidd/e2e-{nome}"
    r = subprocess.run(["git", "-C", str(repo), "worktree", "add", str(wt),
                        "-b", branch, "HEAD"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        r2 = subprocess.run(["git", "-C", str(repo), "worktree", "add", str(wt), branch],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r2.returncode != 0:
            print(f"erro: git worktree add falhou:\n{(r.stderr or r2.stderr)[-2000:]}",
                  file=sys.stderr)
            sys.exit(2)
    print(f"worktree criado: {wt} (branch {branch})")
    return True


def remover_worktree(repo: Path, wt: Path, nome: str) -> None:
    """Apaga a worktree e a branch aidd/e2e-<nome> do ciclo; o resultado fica na pasta do ciclo.
    Sem isso cada E2E deixava worktrees_e2e-ciclo-NN no Desktop (2026-10-02)."""
    for args in (["worktree", "remove", "--force", str(wt)], ["branch", "-D", f"aidd/e2e-{nome}"]):
        subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    print(f"worktree removido: {wt}")


def resolver_origem(ciclo: Path, raiz: Path) -> Path:
    """Export low-code do fluxo 03: empresta de outro ciclo ou clona raso."""
    candidato = ciclo / "_origem" / "conexao-hub"
    if candidato.exists():
        return candidato
    for outro in sorted(raiz.glob("ciclo-*")):
        emprestado = outro / "_origem" / "conexao-hub"
        if emprestado.exists() and emprestado != candidato:
            return emprestado
    candidato.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["git", "clone", "--depth", "1", ORIGEM_URL, str(candidato)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(f"erro: clone da origem do fluxo 03 falhou:\n{r.stderr[-2000:]}",
              file=sys.stderr)
        sys.exit(2)
    return candidato


def consolidar_fluxo(pasta: Path, bruto: dict) -> dict:
    """Port de consolidar.py para 1 fluxo: log -> quebrou_em/erro + JSON final."""
    log = (pasta / "log.txt").read_text(encoding="utf-8", errors="replace")
    falha = FALHA_ETAPA_RE.search(log)
    quebrou = ETAPA_POR_NUMERO[falha.group(1)] if falha else None
    erros = list(dict.fromkeys(m.group(1).strip() for m in ERRO_RE.finditer(log)))
    vaz = {}
    for chave, valor in bruto["vazamentos"].items():
        itens = sorted({x for x in list(valor.get("git_status_novos", []))
                        + list(valor.get("git_status_sumidos", []))
                        + list(valor.get("mtime_mexidos", []))
                        if not any(r in x for r in RUIDO)})
        if itens:
            vaz[chave] = itens
    resultado = {
        "fluxo": bruto["fluxo"],
        "comando": bruto["comando"],
        "cwd": bruto["cwd"],
        "exit_code": bruto["exit_code"],
        "duracao_s": bruto["duracao_s"],
        "quebrou_em": quebrou,
        "erro": erros,
        "quarteto": dict(QUARTETO_PADRAO),
        "arquivos_gerados": bruto["arquivos_gerados"],
        "tokens": TOKENS_PADRAO,
        "vazamentos_fora_da_pasta": vaz,
        "ruido_ignorado": ("arquivos __pycache__ no worktree e .codebase-memory/ "
                           "no main (indexador em segundo plano, mtime muda sem rodar fluxo)"),
        "evidencia_bruta": "RESULTADO-E2E-bruto.json + log.txt",
    }
    (pasta / "RESULTADO-E2E.json").write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    return resultado


def rodar_fluxo(chave: str, pasta_nome: str, nome_app: str, slug: str, dominio: str,
                ciclo: Path, repo: Path, wt: Path, origem: Path, raiz: Path) -> dict:
    pasta = ciclo / pasta_nome
    pasta.mkdir(parents=True, exist_ok=True)
    projeto = pasta / "projeto"
    cmd = [sys.executable, "ecossistema.py", "run-fluxo", "--fluxo", chave,
           "--nome", nome_app, "--slug", slug, "--dominio", dominio,
           "--pasta", str(projeto)]
    if chave == "freedom":
        cmd += ["--origem", str(origem)]

    antes = {"main": git_status(repo), "worktree": git_status(wt),
             "origem": git_status(origem), "topo": topo_nomes(raiz.parent)}
    t0 = time.time()
    time.sleep(1.1)  # garante mtime estritamente posterior
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    log = pasta / "log.txt"
    with open(log, "w", encoding="utf-8") as fh:
        proc = subprocess.run(cmd, cwd=str(wt), stdout=fh, stderr=subprocess.STDOUT, env=env)
    dur = round(time.time() - t0, 1)
    depois = {"main": git_status(repo), "worktree": git_status(wt),
              "origem": git_status(origem), "topo": topo_nomes(raiz.parent)}
    vaz = {}
    for k in ("main", "worktree", "origem"):
        vaz[k] = {"git_status_novos": sorted(set(depois[k]) - set(antes[k])),
                  "git_status_sumidos": sorted(set(antes[k]) - set(depois[k])),
                  "mtime_mexidos": arquivos_mexidos(
                      {"main": repo, "worktree": wt, "origem": origem}[k], t0)}
    novos_topo = sorted(set(depois["topo"]) - set(antes["topo"]))
    sumidos_topo = sorted(set(antes["topo"]) - set(depois["topo"]))
    if novos_topo or sumidos_topo:
        vaz["topo"] = {"git_status_novos": novos_topo, "git_status_sumidos": sumidos_topo,
                       "mtime_mexidos": []}

    gerados = (sum(1 for p in projeto.rglob("*") if p.is_file()
                   and not any(x in IGNORAR for x in p.parts))
               if projeto.exists() else 0)
    bruto = {"fluxo": chave, "comando": " ".join(cmd), "cwd": str(wt),
             "exit_code": proc.returncode, "duracao_s": dur,
             "arquivos_gerados": gerados, "vazamentos": vaz}
    (pasta / "RESULTADO-E2E-bruto.json").write_text(
        json.dumps(bruto, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(json.dumps({"fluxo": chave, "exit": proc.returncode, "dur": dur,
                      "gerados": gerados}))
    return consolidar_fluxo(pasta, bruto)


def rodar_continuacao(ciclo: Path, repo: Path, wt: Path, raiz: Path) -> dict:
    """Port de rodar_continuacao.py: etapas 4-6 na cópia do projeto do fluxo 01."""
    slug, nome_app = "gestao-tarefas", "Gestao Tarefas"
    origem_proj = ciclo / "fluxo-01-pure" / "projeto"
    cont = ciclo / "fluxo-01-pure" / "continuacao"
    cont.mkdir(parents=True, exist_ok=True)
    destino = cont / "projeto"
    if not origem_proj.exists():
        out = {"etapas": [], "aviso": "projeto do fluxo 01 nao existe; continuacao pulada"}
        (cont / "RESULTADO-CONTINUACAO.json").write_text(
            json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
        return out
    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(origem_proj, destino)
    py = sys.executable
    etapas = [
        ("master", [py, "ecossistema.py", "master", "init", slug, "--pasta", str(destino)]),
        ("master", [py, "ecossistema.py", "master", "add-module", slug, "--pasta", str(destino)]),
        ("enterprise", [py, "ecossistema.py", "enterprise", "inject", "rule",
                        f"regra-integridade-{slug}", "--dir", str(destino)]),
        ("enterprise", [py, "ecossistema.py", "enterprise", "verificar-drift",
                        "--dir", str(destino)]),
        ("ops", [py, "ecossistema.py", "ops", "plan",
                 f"Provisionar infraestrutura para {nome_app}", "--pasta", str(destino)]),
    ]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    res = []
    for etapa, cmd in etapas:
        antes = {"main": git_status(repo), "worktree": git_status(wt)}
        t0 = time.time()
        time.sleep(1.1)
        log = cont / f"log_{len(res) + 1}_{etapa}_{cmd[3]}.txt"
        with open(log, "w", encoding="utf-8") as fh:
            p = subprocess.run(cmd, cwd=str(wt), stdout=fh, stderr=subprocess.STDOUT, env=env)
        vaz = {}
        for k, alvo in (("main", repo), ("worktree", wt)):
            novos = sorted(set(git_status(alvo)) - set(antes[k]))
            mex = arquivos_mexidos(alvo, t0)
            vaz[k] = [x for x in novos + mex
                      if "__pycache__" not in x and "graph.db" not in x]
        res.append({"etapa": etapa, "comando": " ".join(cmd[1:]), "exit_code": p.returncode,
                    "duracao_s": round(time.time() - t0, 1), "log": log.name,
                    "vazamentos": vaz})
        print(json.dumps({"etapa": etapa, "arg": cmd[3], "exit": p.returncode}))
    out = {"etapas": res,
           "docker_presente": {"Dockerfile": (destino / "Dockerfile").exists(),
                               "docker-compose.yml": (destino / "docker-compose.yml").exists()},
           "arquivos_gerados": sum(1 for f in destino.rglob("*")
                                   if f.is_file() and ".git" not in f.parts)}
    (cont / "RESULTADO-CONTINUACAO.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    return out


def _http_get(url: str):
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status, r.read(300).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:  # noqa: BLE001
        return None, repr(e)[:200]


ROTAS_QUARTETO = {
    "api": ["/api/principal", "/api", "/openapi.json"],
    "webhook": ["/webhook", "/webhooks"],
    "mcp": ["/mcp"],
    "docs": ["/docs"],
}


def checar_quarteto(ciclo: Path) -> dict:
    """Port de checar_quarteto.py: sobe src/server.py real e testa as 4 rotas."""
    projeto = ciclo / "fluxo-01-pure" / "projeto"
    cont = ciclo / "fluxo-01-pure" / "continuacao"
    cont.mkdir(parents=True, exist_ok=True)
    saida = cont / "QUARTETO.json"
    if not (projeto / "src" / "server.py").exists():
        res = {"servidor_subiu": False, "exit_precoce": None, "rotas": {},
               "motivo": "src/server.py ausente no projeto do fluxo 01"}
        saida.write_text(json.dumps(res, indent=2, ensure_ascii=False),
                         encoding="utf-8", newline="\n")
        return res

    porta = 3917
    env = os.environ.copy()
    env.update({"PORT": str(porta), "PYTHONIOENCODING": "utf-8"})
    log = open(saida.with_suffix(".server.log"), "w", encoding="utf-8")
    p = subprocess.Popen([sys.executable, "src/server.py"], cwd=str(projeto),
                         stdout=log, stderr=subprocess.STDOUT, env=env)
    subiu = False
    for _ in range(40):
        if p.poll() is not None:
            break
        if (_http_get(f"http://127.0.0.1:{porta}/openapi.json")[0] is not None
                or _http_get(f"http://127.0.0.1:{porta}/docs")[0] is not None):
            subiu = True
            break
        time.sleep(0.5)
    res = {"servidor_subiu": subiu, "exit_precoce": p.poll(), "rotas": {}}
    if subiu:
        for chave, caminhos in ROTAS_QUARTETO.items():
            tentativas = {c: _http_get(f"http://127.0.0.1:{porta}{c}")[0] for c in caminhos}
            res["rotas"][chave] = {
                "responde": any(s is not None and 200 <= s < 400 for s in tentativas.values()),
                "status_por_caminho": tentativas}
    p.terminate()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    log.close()
    saida.write_text(json.dumps(res, indent=2, ensure_ascii=False),
                     encoding="utf-8", newline="\n")
    print(json.dumps({"quarteto_subiu": subiu}))
    return res


def gravar_quarteto_no_resultado(ciclo: Path, quarteto: dict) -> None:
    arquivo = ciclo / "fluxo-01-pure" / "RESULTADO-E2E.json"
    if not arquivo.exists():
        return
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    if quarteto.get("servidor_subiu"):
        dados["quarteto"] = {
            chave: ("sim" if info.get("responde") else "não")
            for chave, info in quarteto.get("rotas", {}).items()}
        arquivo.write_text(json.dumps(dados, indent=2, ensure_ascii=False),
                           encoding="utf-8", newline="\n")


def cmd_rodar(args) -> int:
    raiz = Path(args.raiz) if args.raiz else raiz_padrao()
    raiz.mkdir(parents=True, exist_ok=True)
    repo = repo_raiz()
    nome = nome_ciclo(args.ciclo, raiz)
    ciclo = raiz / nome
    ciclo.mkdir(parents=True, exist_ok=True)
    wt = Path(args.worktree) if args.worktree else raiz.parent / f"worktrees_e2e-{nome}"
    criada = preparar_worktree(repo, wt, nome)
    try:
        origem = resolver_origem(ciclo, raiz)
        for chave, (pasta_nome, nome_app, slug, dominio) in FLUXOS.items():
            rodar_fluxo(chave, pasta_nome, nome_app, slug, dominio,
                        ciclo, repo, wt, origem, raiz)
        rodar_continuacao(ciclo, repo, wt, raiz)
        gravar_quarteto_no_resultado(ciclo, checar_quarteto(ciclo))
    finally:
        if criada:
            remover_worktree(repo, wt, nome)
    print(f"ciclo gravado em {ciclo}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="e2e_foto.py",
        description="Foto E2E repetível e comparação automática (Ticket 2, D12).")
    sub = parser.add_subparsers(dest="comando", required=True)

    p_rodar = sub.add_parser(
        "rodar",
        help="cria worktree isolado, roda os 3 fluxos + continuação + Quarteto "
             "e grava RESULTADO-E2E.json por fluxo na pasta do ciclo (fora do repo)")
    p_rodar.add_argument("--ciclo", default="auto",
                         help="auto (próximo ciclo-NN) ou um nome ciclo-NN")
    p_rodar.add_argument("--raiz", default=None,
                         help="raiz das pastas de ciclo (padrão: $AIDD_E2E_RAIZ, "
                              "Desktop/TESTES_E2E-ecossistema-aidd ou "
                              "Desktop/01_projetos_apps/testes-e2e-ecossistema-aidd)")
    p_rodar.add_argument("--worktree", default=None,
                         help="caminho do worktree isolado (padrão: ao lado da raiz)")

    p_comp = sub.add_parser(
        "comparar",
        help="compara base × novo (exit, quebrou_em, quarteto, vazamentos, "
             "duplicatas, tempo de gate, tokens, órfãos) e grava COMPARACAO-E2E.md; "
             "exit 1 se alguma métrica piorar")
    p_comp.add_argument("--base", required=True, help="pasta ou nome do ciclo base")
    p_comp.add_argument("--novo", default="ultimo",
                        help="pasta ou nome do ciclo novo (padrão: ultimo ciclo-NN)")
    p_comp.add_argument("--raiz", default=None, help="raiz das pastas de ciclo")
    p_comp.add_argument("--saida", default=None,
                        help="caminho do COMPARACAO-E2E.md (padrão: <novo>/COMPARACAO-E2E.md)")

    args = parser.parse_args(argv)
    if args.comando == "rodar":
        return cmd_rodar(args)
    return cmd_comparar(args)


if __name__ == "__main__":
    sys.exit(main())
