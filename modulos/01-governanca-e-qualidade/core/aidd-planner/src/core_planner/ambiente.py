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
    ("GEMINI", "gemini-cli"),
)

# Passo a passo oficial do Mobbin (docs.mobbin.com). Só o Claude Code foi exercitado nesta
# máquina; os demais seguem a documentação de cada harness e estão marcados como não verificados.
_PASSOS_MCP = {
    "claude-code": [
        f"claude mcp add --transport http mobbin {URL_MCP_MOBBIN}",
        "Dentro do Claude Code, abra /mcp, escolha 'mobbin' e autorize no navegador.",
    ],
    "opencode": [
        f"Adicione o MCP remoto 'mobbin' ({URL_MCP_MOBBIN}) na configuração do OpenCode.",
        "opencode mcp auth mobbin   (autoriza no navegador) [não verificado nesta máquina]",
    ],
    "mimocode": [
        f"Adicione o MCP remoto 'mobbin' ({URL_MCP_MOBBIN}) na configuração do MiMoCode.",
        "mimo mcp auth mobbin   (autoriza no navegador) [não verificado nesta máquina]",
    ],
    "gemini-cli": [
        f"gemini mcp add --transport http mobbin {URL_MCP_MOBBIN}   [não verificado nesta máquina]",
        "Dentro do Gemini CLI, rode /mcp auth mobbin e autorize no navegador. [não verificado nesta máquina]",
    ],
    "antigravity": [
        f"Adicione o MCP remoto 'mobbin' ({URL_MCP_MOBBIN}) nos servidores MCP do Antigravity CLI.",
        "Autorize no navegador quando o harness pedir. [não verificado nesta máquina]",
    ],
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
    for prefixo, nome in _MARCADORES_HARNESS:
        if any(k == prefixo or k.startswith(prefixo + "_") or k.startswith(prefixo) for k in chaves):
            return nome
    return "desconhecido"


def passo_a_passo_mcp(harness: str) -> List[str]:
    return list(_PASSOS_MCP.get(harness, _PASSO_GENERICO))


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
