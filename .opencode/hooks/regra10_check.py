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

import argparse
import json
import os
import re
import sys
import tempfile
import time

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HOOKS_DIR, "regra10_termos.json")
STATE_DIR = os.path.join(tempfile.gettempdir(), "aidd_regra10_state")

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

RE_PREAMBULO_INICIO = re.compile(
    r"^\s*(?:"
    r"olá|oi|bom dia|boa tarde|boa noite|com certeza|certamente|claro|perfeito|com prazer|hello|hi|"
    r"você pediu|como solicitado|conforme solicitado|de acordo com|você solicitou|conforme você pediu|atendendo ao seu pedido|"
    r"entendido|entendi|compreendido|"
    r"vou te ajudar|vou explicar|vou resumir|aqui está o resumo|aqui estão as alterações|neste passo vou|deixe-me explicar"
    r")\b",
    re.IGNORECASE,
)

RE_NARRACAO_PASSOS = re.compile(
    r"\b(?:"
    r"primeiro eu|em seguida eu|depois eu|então eu|após isso eu|"
    r"em seguida verifiquei|depois verifiquei|primeiro analisei|em seguida analisei|"
    r"depois li|em seguida li|depois executei|em seguida executei|agora vou|"
    r"como podemos ver acima|"
    r"first i|then i|after that i|next i|i started by|i then"
    r")\b",
    re.IGNORECASE,
)

RE_OPCOES_SEM_RECOMENDACAO = re.compile(
    r"\b(?:"
    r"você pode optar por|as opções são|as alternativas são|você pode escolher entre|"
    r"temos duas opções|temos 3 opções|há duas formas|você decide entre|"
    r"you can choose between|the options are|you can either"
    r")\b",
    re.IGNORECASE,
)

RE_PALAVRAS_RECOMENDACAO = re.compile(
    r"\b(?:"
    r"recomendo|recomendação|sugiro|sugestão|recomenda-se|preferível|indico|"
    r"recommend|recommendation|suggest|suggestion|preferred"
    r")\b",
    re.IGNORECASE,
)

RE_BULLET_ITEM = re.compile(r"^\s*(?:[-*•]|\d+\.)\s+", re.MULTILINE)

DEFAULT_CONFIG = {
    "ativo": True,
    "modo": "bloqueio",  # "bloqueio" ou "aviso"
    "limite_bloqueios_por_pergunta": 2,
    "ignorar_respostas_curtas": True,
    "min_palavras_para_bloqueio": 30,
    "verificar_shape": True,
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
    cfg.setdefault("verificar_shape", True)
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


def verificar_shape(mensagem: str, cfg: dict) -> list[str]:
    """Valida deterministicamente o formato da resposta do assistente segundo a Regra 10 e ISSUE-0013.

    Formato obrigatório para respostas explicativas/prolixas:
    1. One top sentence declarando o fato/ação imediata sem preâmbulo/saudação.
    2. Short bulleted body com fatos, métricas e achados. Proibido narrar passos passados.
    3. One closing suggestion block separado do corpo.
    Proibido: saudações/polidez, repetição da solicitação, listar opções sem recomendar.
    """
    erros = []
    texto_sem_blocos = re.sub(r"```[\s\S]*?```", "", mensagem).strip()
    if not texto_sem_blocos:
        return erros

    palavras = texto_sem_blocos.split()
    min_palavras = cfg.get("min_palavras_para_bloqueio", 30)

    # 1. Proibicoes estritas (aplicam-se a qualquer mensagem)
    linhas = [l.strip() for l in texto_sem_blocos.splitlines() if l.strip()]
    if linhas and RE_PREAMBULO_INICIO.search(linhas[0]):
        erros.append("Preâmbulo ou saudação proibida no início. A primeira linha deve ser direta.")

    texto_limpo = limpar_codigo_e_links(texto_sem_blocos)
    if RE_NARRACAO_PASSOS.search(texto_limpo):
        erros.append("Narração de processo/passos tomados. Use apenas fatos, números e achados objetivos.")

    if RE_OPCOES_SEM_RECOMENDACAO.search(texto_limpo) and not RE_PALAVRAS_RECOMENDACAO.search(texto_limpo):
        erros.append("Listagem de alternativas sem recomendação explícita de escolha.")

    # 2. Exigencia de topicos/bullets: apenas para respostas com corpo explicativo (> 2 linhas ou >= min_palavras)
    # Status curtos de 1-2 linhas factuais sao permitidos sem bullets por Law #4 (Silent executor).
    if len(linhas) > 2 or len(palavras) >= min_palavras:
        bullets = RE_BULLET_ITEM.findall(texto_sem_blocos)
        if not bullets:
            erros.append("Ausência de corpo estruturado em tópicos/bullets (fatos, números, achados).")

    return erros


def main():
    parser = argparse.ArgumentParser(description="Stop hook Regra 10 - Validador de formato e jargão.")
    parser.add_argument("--strict", action="store_true", help="Retorna exit 1 quando a resposta for bloqueada.")
    args, _ = parser.parse_known_args()

    try:
        conteudo_raw = sys.stdin.read()
        if not conteudo_raw.strip():
            return 0
        try:
            entrada = json.loads(conteudo_raw)
            if isinstance(entrada, dict):
                mensagem = entrada.get("last_assistant_message") or ""
            elif isinstance(entrada, str):
                mensagem = entrada
            else:
                mensagem = str(entrada)
        except (json.JSONDecodeError, ValueError):
            entrada = {}
            mensagem = conteudo_raw
    except Exception:
        return 0

    cfg = carregar_config()
    if not cfg.get("ativo", True):
        return 0

    if not mensagem.strip():
        return 0

    motivos_bloqueio = []

    # 1. Validacao de Shape / Formato deterministico
    if cfg.get("verificar_shape", True):
        erros_shape = verificar_shape(mensagem, cfg)
        if erros_shape:
            motivos_bloqueio.extend(erros_shape)

    # 2. Validacao de Jargao Tecnico
    achados = termos_encontrados(mensagem, cfg.get("termos", TERMOS_PADRAO))
    if achados:
        termos_str = ", ".join(sorted(set(achados)))
        motivos_bloqueio.append(
            f"Termos técnicos sem explicação ({termos_str})"
        )

    if not motivos_bloqueio:
        return 0

    if cfg.get("modo", "bloqueio") == "aviso":
        sys.stderr.write(
            f"[regra10:aviso] Violações identificadas na resposta: {'; '.join(motivos_bloqueio)}\n"
        )
        return 0

    limpar_estado_antigo()
    chave = entrada.get("prompt_id") or entrada.get("session_id") or "default"
    limite = int(cfg.get("limite_bloqueios_por_pergunta", 2))
    tentativa = contar_bloqueios(chave)

    if tentativa > limite:
        sys.stderr.write(
            f"[regra10] Limite de {limite} bloqueio(s) atingido para esta pergunta; "
            f"liberando resposta mesmo com violações: {'; '.join(motivos_bloqueio)}\n"
        )
        return 0

    razao_formatada = (
        f"Regra 10 (ISSUE-0013): Resposta fora do padrão ({'; '.join(motivos_bloqueio)}). "
        "Formato obrigatório: 1 frase direta no topo (sem preâmbulo/saudação), "
        "corpo em tópicos objetivos (fatos, números, achados; sem narrar processo), "
        "e bloco final de sugestão/próximo passo isolado."
    )
    saida = {
        "decision": "block",
        "reason": razao_formatada,
    }
    print(json.dumps(saida, ensure_ascii=False))
    if args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
