# -*- coding: utf-8 -*-
"""
AIDD-Factory — Fase 6: Gerador de .env.

Gera variaveis de ambiente isoladas por servico com senhas criptograficas.
100% deterministico — zero LLM.
"""
import os
import secrets
import string
import sys

_FACTORY_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "src"))
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "..", "..", "componentes", "compartilhado", "src-core"))

from core.result import Result

_AIDD_OPS_ROOT = os.path.join(_FACTORY_ROOT, "..", "aidd-ops")
_INFRA_DIR = os.path.join(_AIDD_OPS_ROOT, "templates", "infra")


def _gerar_senha(tamanho: int = 32) -> str:
    """Gera senha criptografica de alta entropia."""
    alfabeto = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return ''.join(secrets.choice(alfabeto) for _ in range(tamanho))


def _ler_env_example(bloco_slug: str) -> Result:
    """Le .env.example de um template de bloco."""
    caminho = os.path.join(_INFRA_DIR, bloco_slug, ".env.example")
    if not os.path.isfile(caminho):
        return Result.fail(f".env.example nao encontrado: {caminho}", codigo="ENV_EXAMPLE_AUSENTE")
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return Result.ok(f.read())
    except OSError as exc:
        return Result.fail(f"Erro ao ler .env.example: {exc}", codigo="ENV_READ_ERROR")


def _extrair_variaveis(conteudo: str) -> list:
    """Extrai nomes de variaveis de um .env.example (linhas CHAVE=valor)."""
    variaveis = []
    for linha in conteudo.splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        if "=" in linha:
            chave = linha.split("=", 1)[0].strip()
            if chave:
                variaveis.append(chave)
    return variaveis


def _eh_sensivel(chave: str) -> bool:
    """Determina se uma variavel requer senha gerada."""
    indicadores = [
        "password", "secret", "key", "token", "api_key",
        "database_password", "db_pass", "postgres_password",
    ]
    chave_lower = chave.lower()
    return any(ind in chave_lower for ind in indicadores)


def gerar_env(analysis: dict, pasta_saida: str) -> Result:
    """Gera .env por servico a partir do factory_analysis.

    Args:
        analysis: Dicionario do factory_analysis.json.
        pasta_saida: Diretorio onde salvar os .env.

    Returns:
        Result.ok(lista_de_envs) ou Result.fail.
    """
    blocos = analysis.get("blocos", [])
    envs_gerados = []

    # Sempre incluir postgres (tem bancos logicos)
    blocos_slugs = list({b["slug"] for b in blocos})
    if "postgres" not in blocos_slugs:
        blocos_slugs.insert(0, "postgres")

    for slug in blocos_slugs:
        res = _ler_env_example(slug)
        if not res.sucesso:
            continue  # Pular blocos sem .env.example

        conteudo = res.valor
        variaveis = _extrair_variaveis(conteudo)

        # Gerar .env com senhas
        linhas = [f"# AIDD-Factory gerado — {slug}", ""]
        for var in variaveis:
            if _eh_sensivel(var):
                senha = _gerar_senha()
                linhas.append(f"{var}={senha}")
            else:
                # Manter valor do .env.example se existir
                for linha in conteudo.splitlines():
                    if linha.strip().startswith(f"{var}="):
                        linhas.append(linha.strip())
                        break
                else:
                    linhas.append(f"{var}=")

        conteudo_env = "\n".join(linhas) + "\n"

        # Salvar
        os.makedirs(pasta_saida, exist_ok=True)
        caminho = os.path.join(pasta_saida, f".env.{slug}")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo_env)

        envs_gerados.append({"bloco": slug, "caminho": caminho, "variaveis": len(variaveis)})

    return Result.ok(envs_gerados)
