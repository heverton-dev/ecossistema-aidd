# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — BLOCO AMBIENTE DO PLANNER
=============================================================================
O planner abre verificando o ambiente, antes da entrevista, da spec e do plano:

  1. Mobbin (referências visuais), 3 caminhos, nesta ordem:
       1 = MCP oficial, usado pelo harness (OAuth no navegador, sem segredo no projeto);
       2 = chave MOBBIN_API_KEY no .env (REST);
       3 = nenhum (o visual vem da spec/entrevista).
     A escolha é gravada em `.aidd/ambiente.json`, sem segredo. O Mobbin NUNCA bloqueia:
     chave ausente, recusada ou rede fora do ar só registram aviso.
  2. Deploy (só compose-nativo, sem Coolify): as variáveis abaixo BLOQUEIAM o planner.

Nenhum valor de variável é impresso nem gravado: só os nomes.
=============================================================================
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

CAMINHOS_MOBBIN = {"1": "mcp", "2": "chave", "3": "nenhum"}
URL_MCP_MOBBIN = "https://api.mobbin.com/mcp"
ARQUIVO_AMBIENTE = Path(".aidd") / "ambiente.json"

# Cada item é obrigatório; "A ou B" aceita qualquer uma das duas (autenticação SSH).
VARIAVEIS_DEPLOY_OBRIGATORIAS = (
    "VPS_HOST",
    "VPS_USER",
    "CLOUDFLARE_API_TOKEN",
    "CLOUDFLARE_ZONE_ID",
    "DEFAULT_ROOT_DOMAIN",
    "SSH_KEY_PATH ou VPS_PASSWORD",
)

_MARCADORES_HARNESS = (
    ("CLAUDECODE", "claude-code"),
    ("OPENCODE", "opencode"),
    ("MIMO", "mimocode"),
    ("ANTIGRAVITY", "antigravity"),
    ("AGY_", "antigravity"),
    ("GEMINI", "gemini-cli"),
)
# O omp não tem prefixo próprio livre (OMP_NUM_THREADS é do OpenMP): só as variáveis exatas dele.
_VARIAVEIS_OMP = ("OMP_PLUGIN_ROOT", "OMP_PROFILE", "OMP_AUTH_BROKER_URL", "OMP_MCP_TIMEOUT_MS")

# Quanto cada passo a passo do Mobbin foi verificado (Ticket 9-B), do mais forte ao mais fraco:
#   executado    comando rodado nesta máquina (add, list e remove de verdade, e chamada real ao MCP)
#   help         existência e flags conferidas no `--help` do binário instalado
#   binario      texto de uso lido de dentro do binário instalado (a interface é interativa, não foi executada)
#   documentacao só a documentação oficial; o harness não está instalado ou não roda aqui
NIVEIS_VERIFICACAO = ("executado", "help", "binario", "documentacao")

_PASSOS_MCP = {
    "claude-code": ("executado", [
        f"claude mcp add --transport http mobbin {URL_MCP_MOBBIN}",
        "Dentro do Claude Code, abra /mcp, escolha 'mobbin' e autorize no navegador (antes disso o status é 'Needs authentication').",
    ]),
    "antigravity": ("executado", [
        f"agy mcp add mobbin {URL_MCP_MOBBIN}   (o tipo http é detectado pela URL; flags vêm antes do nome)",
        "Autorize no navegador quando o agy pedir. Conferir: agy mcp list.",
    ]),
    "mimocode": ("help", [
        "mimo mcp add   (interativo: nome 'mobbin' e a URL " + URL_MCP_MOBBIN + ")",
        "mimo mcp auth mobbin   (autoriza no navegador; `mimo mcp list` mostra quem ainda precisa de autenticação)",
    ]),
    "opencode": ("documentacao", [
        'No opencode.json: "mcp": {"mobbin": {"type": "remote", "url": "' + URL_MCP_MOBBIN + '"}}   (não existe `opencode mcp add`)',
        "opencode mcp auth mobbin   (autoriza no navegador; o OpenCode também inicia o OAuth sozinho ao receber 401)",
    ]),
    "omp": ("binario", [
        f"Dentro do omp: /mcp add mobbin --scope user --url {URL_MCP_MOBBIN} --transport http",
        "Dentro do omp: /mcp reauth mobbin   (autoriza no navegador); /mcp list mostra o status dos servidores.",
    ]),
    "gemini-cli": ("documentacao", [
        f"gemini mcp add --transport http mobbin {URL_MCP_MOBBIN}",
        "Dentro do Gemini CLI, rode /mcp auth mobbin e autorize no navegador. (Substituído pelo Antigravity CLI em 18/06/2026.)",
    ]),
}
_PASSO_GENERICO = [
    f"Registre no seu harness um servidor MCP remoto chamado 'mobbin' apontando para {URL_MCP_MOBBIN}.",
    "Autorize no navegador (OAuth). A autorização vale só para o harness em que foi feita.",
]

PostFn = Callable[..., Any]


def carregar_env() -> Dict[str, str]:
    """Ambiente do processo mais o `.env` da raiz do ecossistema (o processo tem prioridade)."""
    env: Dict[str, str] = {}
    raiz = next((p for p in Path(__file__).resolve().parents if (p / "ecossistema.py").is_file()), None)
    if raiz is not None and (raiz / ".env").is_file():
        for linha in (raiz / ".env").read_text(encoding="utf-8", errors="replace").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            nome, _, valor = linha.partition("=")
            env[nome.strip()] = valor.strip().strip('"').strip("'")
    env.update(os.environ)
    return env


def detectar_harness(env: Mapping[str, str]) -> str:
    chaves = list(env.keys())
    if any(k in _VARIAVEIS_OMP for k in chaves) and not any(k.startswith("CLAUDECODE") for k in chaves):
        return "omp"
    for prefixo, nome in _MARCADORES_HARNESS:
        if any(k == prefixo or k.startswith(prefixo + "_") or k.startswith(prefixo) for k in chaves):
            return nome
    return "desconhecido"


def nivel_verificacao(harness: str) -> Optional[str]:
    return _PASSOS_MCP[harness][0] if harness in _PASSOS_MCP else None


def passo_a_passo_mcp(harness: str) -> List[str]:
    if harness not in _PASSOS_MCP:
        return list(_PASSO_GENERICO)
    nivel, passos = _PASSOS_MCP[harness]
    return [*passos, f"[verificação deste passo a passo: {nivel}]"]


def variaveis_deploy_faltando(env: Mapping[str, str]) -> List[str]:
    def tem(nome: str) -> bool:
        return bool(str(env.get(nome, "")).strip())

    faltando = []
    for item in VARIAVEIS_DEPLOY_OBRIGATORIAS:
        if " ou " in item:
            if not any(tem(n.strip()) for n in item.split(" ou ")):
                faltando.append(item)
        elif not tem(item):
            faltando.append(item)
    return faltando


def validar_chave_mobbin(env: Mapping[str, str], post: Optional[PostFn] = None) -> Tuple[bool, str]:
    """Uma chamada real mínima (1 tela, modo standard). Nunca levanta exceção e nunca devolve a chave."""
    chave = str(env.get("MOBBIN_API_KEY", "")).strip()
    if not chave:
        return False, "MOBBIN_API_KEY não está definida no .env"
    url = str(env.get("MOBBIN_API_URL", "https://api.mobbin.com")).strip().rstrip("/") + "/v1/screens/search"
    if post is None:
        try:
            import requests
        except ImportError:
            return False, "biblioteca 'requests' ausente; chave não validada"
        post = requests.post
    try:
        resposta = post(
            url,
            headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json",
                     "User-Agent": "ecossistema-aidd/1.0"},
            json={"query": "dashboard", "platform": "web", "mode": "standard", "limit": 1},
            timeout=30,
        )
    except Exception as erro:  # rede fora do ar, timeout, DNS
        return False, f"não consegui falar com o Mobbin ({type(erro).__name__})"
    if resposta.status_code == 200:
        return True, "chave aceita pelo Mobbin"
    return False, f"o Mobbin respondeu {resposta.status_code} para a chave"


def caminho_arquivo(pasta: str) -> Path:
    return Path(pasta) / ARQUIVO_AMBIENTE


def registrar(pasta: str, caminho: str, harness: str, validado: Optional[bool]) -> Path:
    destino = caminho_arquivo(pasta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    dados = {
        "versao": 1,
        "harness": harness,
        "mobbin": {"caminho": caminho, "validado": validado},
        "deploy": {"motor": "compose-nativo", "variaveis_exigidas": list(VARIAVEIS_DEPLOY_OBRIGATORIAS)},
    }
    destino.write_text(json.dumps(dados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return destino


def ler(pasta: str) -> Optional[Dict[str, Any]]:
    arquivo = caminho_arquivo(pasta)
    if not arquivo.is_file():
        return None
    try:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dados if isinstance(dados, dict) else None


def texto_dos_tres_caminhos() -> List[str]:
    return [
        "Escolha como o Mobbin (referências visuais) entra neste projeto, nesta ordem:",
        f"  1. MCP oficial do Mobbin, pelo harness ({URL_MCP_MOBBIN}); sem chave no projeto.",
        "  2. Chave MOBBIN_API_KEY no .env (REST).",
        "  3. nenhum: o visual vem da spec e da entrevista.",
        "Registre com: python ecossistema.py planner ambiente --pasta <pasta> --mobbin <1|2|3>",
    ]


def verificar(pasta: str, env: Mapping[str, str]) -> List[str]:
    """Erros que bloqueiam o `planner init`: ambiente não registrado/inválido e deploy incompleto."""
    erros: List[str] = []
    dados = ler(pasta)
    caminho = (dados or {}).get("mobbin", {}).get("caminho") if isinstance((dados or {}).get("mobbin"), dict) else None
    if caminho not in CAMINHOS_MOBBIN.values():
        erros.append("Ambiente não registrado (ou inválido) em .aidd/ambiente.json.")
        erros.extend("  " + linha for linha in texto_dos_tres_caminhos())
    faltando = variaveis_deploy_faltando(env)
    if faltando:
        erros.append("Variáveis de deploy ausentes no .env (o deploy é só compose-nativo): " + ", ".join(faltando))
    return erros


def cmd_ambiente(args, env: Optional[Mapping[str, str]] = None) -> int:
    env = carregar_env() if env is None else env
    pasta = os.path.abspath(getattr(args, "pasta", None) or ".")
    escolha = getattr(args, "mobbin", None)

    harness = detectar_harness(env)
    print(f"[aidd-planner] Ambiente: harness detectado = {harness}")

    faltando = variaveis_deploy_faltando(env)
    if faltando:
        print("[ERRO] Variáveis de deploy ausentes no .env (deploy só compose-nativo): " + ", ".join(faltando),
              file=sys.stderr)
        print("       Preencha-as no .env (veja .env.example) e rode o comando de novo.", file=sys.stderr)
        return 1

    if escolha not in CAMINHOS_MOBBIN:
        for linha in texto_dos_tres_caminhos():
            print(linha, file=sys.stderr)
        return 1
    caminho = CAMINHOS_MOBBIN[escolha]

    validado: Optional[bool] = None
    if caminho == "mcp":
        print("[aidd-planner] Mobbin pelo MCP oficial. Passo a passo para o seu harness:")
        for passo in passo_a_passo_mcp(harness):
            print("  - " + passo)
    elif caminho == "chave":
        validado, motivo = validar_chave_mobbin(env)
        if validado:
            print(f"[aidd-planner] Mobbin: {motivo}.")
        else:
            print(f"[AVISO] Mobbin não validado: {motivo}. O visual cairá na spec/entrevista; o planner segue.",
                  file=sys.stderr)
    else:
        print("[aidd-planner] Mobbin: nenhum. O visual virá da spec e da entrevista.")

    destino = registrar(pasta, caminho, harness, validado)
    print(f"[aidd-planner] Ambiente registrado em {destino} (sem segredos).")
    return 0
