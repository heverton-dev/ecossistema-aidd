#!/usr/bin/env python3
"""Stop hook: verifica se a ultima resposta do assistente tem jargao tecnico
nao explicado, em conformidade com a Regra 10 do AGENTS.md e diretrizes de
linguagem simples.

Melhorias implementadas:
1. Ignora blocos de codigo markdown, codigo inline, links e caminhos de arquivo.
2. Reconhece termos que ja venham acompanhados de explicacao ou analogia didatica.
3. Protege tokens: evita re-geracao cara em respostas ultracurtas e suporta modo aviso.
4. Portavel e agnostico a harness.
"""

import json
import os
import re
import sys
import time

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HOOKS_DIR, "regra10_termos.json")
STATE_DIR = os.path.join(HOOKS_DIR, "regra10_state")

TERMOS_PADRAO = [
    "diff", "baseline", "byte a byte", "endpoint", "payload", "pipeline",
    "middleware", "runtime", "framework", "webhook", "schema", "query",
    "cache", "hash", "regex", "merge conflict", "dependency injection",
    "namespace", "singleton", "polimorfismo", "idempotente",
    "race condition", "thread", "socket", "buffer overflow",
    "garbage collector", "stack trace", "refactor", "fuzzing", "CVE",
    "pares de comparacao", "pares de comparação", "instancia", "instância",
    "deploy", "rollback", "sharding", "load balancer", "orquestracao",
    "orquestração", "serializacao", "serialização",
]

PADRAO_EXPLICACAO = re.compile(
    r"\b(ou seja|isto é|funciona como|como um[a]?|como se fosse|pense como|"
    r"quer dizer|significa|em termos práticos|na prática|que é|que são|"
    r"analogia|em resumo|explicando de forma simples)\b",
    re.IGNORECASE,
)

DEFAULT_CONFIG = {
    "ativo": True,
    "modo": "bloqueio",  # "bloqueio" ou "aviso"
    "limite_bloqueios_por_pergunta": 2,
    "ignorar_respostas_curtas": True,
    "min_palavras_para_bloqueio": 30,
    "termos": TERMOS_PADRAO,
}


def carregar_config():
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(HOOKS_DIR, exist_ok=True)
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
                f.write("\n")
        except OSError:
            pass
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, json.JSONDecodeError):
        return DEFAULT_CONFIG

    cfg.setdefault("ativo", True)
    cfg.setdefault("modo", "bloqueio")
    cfg.setdefault("limite_bloqueios_por_pergunta", 2)
    cfg.setdefault("ignorar_respostas_curtas", True)
    cfg.setdefault("min_palavras_para_bloqueio", 30)
    cfg.setdefault("termos", TERMOS_PADRAO)
    return cfg


def limpar_codigo_e_links(texto: str) -> str:
    """Remove blocos de codigo, links e caminhos para evitar falsos positivos."""
    # 1. Remove blocos multilinhas ```...```
    texto = re.sub(r"```[\s\S]*?```", " ", texto)
    # 2. Remove trechos inline `...`
    texto = re.sub(r"`[^`\n]+`", " ", texto)
    # 3. Links markdown [rotulo](url) -> preserva rotulo, descarta URL
    texto = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", texto)
    # 4. URLs diretas
    texto = re.sub(r"(?:https?|file)://\S+", " ", texto)
    # 5. Caminhos de arquivos tipicos (Windows e POSIX)
    texto = re.sub(r"\b[A-Za-z]:\\[\w\\\.\-]+", " ", texto)
    texto = re.sub(r"(?:^|\s)(?:/[\w\.\-]+){2,}", " ", texto)
    return texto


def termo_esta_explicado(termo: str, texto: str) -> bool:
    """Verifica se o termo e acompanhado de analogia, explicacao ou parenteses."""
    padrao_parenteses = re.compile(
        rf"\b{re.escape(termo)}\b\s*\(([^)]{{5,100}})\)", re.IGNORECASE
    )
    if padrao_parenteses.search(texto):
        return True

    sentencas = re.split(r"[.\n;!?]", texto)
    for sentenca in sentencas:
        padrao_termo = re.compile(rf"\b{re.escape(termo)}\b", re.IGNORECASE)
        if padrao_termo.search(sentenca):
            if PADRAO_EXPLICACAO.search(sentenca):
                return True

    return False


def termos_encontrados(texto: str, termos: list) -> list:
    texto_limpo = limpar_codigo_e_links(texto)
    achados = []
    for termo in termos:
        padrao = rf"\b{re.escape(termo)}\b"
        if re.search(padrao, texto_limpo, flags=re.IGNORECASE):
            if not termo_esta_explicado(termo, texto_limpo):
                achados.append(termo)
    return achados


def limpar_estado_antigo():
    if not os.path.isdir(STATE_DIR):
        return
    agora = time.time()
    try:
        for nome in os.listdir(STATE_DIR):
            caminho = os.path.join(STATE_DIR, nome)
            try:
                if agora - os.path.getmtime(caminho) > 86400:
                    os.remove(caminho)
            except OSError:
                pass
    except OSError:
        pass


def contar_bloqueios(chave: str) -> int:
    os.makedirs(STATE_DIR, exist_ok=True)
    caminho = os.path.join(STATE_DIR, f"{chave}.count")
    contagem = 0
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                contagem = int(f.read().strip() or "0")
        except (OSError, ValueError):
            contagem = 0
    contagem += 1
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(str(contagem))
    return contagem


def main():
    try:
        entrada = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    cfg = carregar_config()
    if not cfg.get("ativo", True):
        return 0

    mensagem = entrada.get("last_assistant_message") or ""
    if not mensagem.strip():
        return 0

    palavras = mensagem.split()
    if cfg.get("ignorar_respostas_curtas", True) and len(palavras) < cfg.get("min_palavras_para_bloqueio", 30):
        return 0

    achados = termos_encontrados(mensagem, cfg.get("termos", TERMOS_PADRAO))
    if not achados:
        return 0

    if cfg.get("modo", "bloqueio") == "aviso":
        sys.stderr.write(
            f"[regra10:aviso] Termos tecnicos identificados na resposta: {', '.join(achados)}\n"
        )
        return 0

    limpar_estado_antigo()
    chave = entrada.get("prompt_id") or entrada.get("session_id") or "default"
    limite = int(cfg.get("limite_bloqueios_por_pergunta", 2))
    tentativa = contar_bloqueios(chave)

    if tentativa > limite:
        sys.stderr.write(
            f"[regra10] Limite de {limite} bloqueio(s) atingido para esta pergunta; "
            f"liberando resposta mesmo com termos: {', '.join(achados)}\n"
        )
        return 0

    termos_str = ", ".join(sorted(set(achados)))
    saida = {
        "decision": "block",
        "reason": (
            f"Regra 10: Resposta com termos tecnicos sem explicacao ({termos_str}). "
            f"Reescreva de forma concisa e densa em linguagem simples, usando analogias "
            f"do cotidiano se necessario. Mantenha o rigor tecnico sem inflar tokens."
        ),
    }
    print(json.dumps(saida, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
