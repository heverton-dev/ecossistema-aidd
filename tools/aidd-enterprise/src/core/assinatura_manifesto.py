# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — Assinatura Ed25519 do Manifesto Canônico
=============================================================================
Fonte única: componentes/compartilhado/src-core/assinatura_manifesto.py —
byte-idêntico em tools/aidd-master/src/core/ e tools/aidd-enterprise/src/core/
(sincronizado por componentes/compartilhado/src-core/sync.py).

Ameaça mitigada (SEGURANCA-SUPPLY-CHAIN-BASELINE, SEC-8/9): o registro
CAPABILITIES.json guarda hashes SHA-256 dos componentes injetados no MESMO
arquivo que descreve os dados. Um agente comprometido com acesso de escrita
ao repositório pode adulterar um arquivo injetado (ex.: src/core/mcp/*.py) e
recalcular/reescrever o hash correspondente — o SHA-256 sozinho não é
tamper-evident contra quem controla os dois lados.

A assinatura Ed25519 fecha essa lacuna: o manifesto só é confiável se estiver
assinado com a chave PRIVADA (nunca versionada, mantida fora do repositório),
verificável com a chave PÚBLICA versionada em 'chaves/manifesto/'. Um agente
que só tem acesso de escrita ao código-fonte não consegue forjar uma
assinatura válida para um manifesto adulterado.
"""

from __future__ import annotations

import base64
import datetime
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

try:
    from result import Result
except ImportError:
    from core.result import Result


NOME_ARQUIVO_MANIFESTO = "CAPABILITIES.json"
SUFIXO_ASSINATURA = ".ed25519.sig"

_CHAVE_PUBLICA_RELATIVA = os.path.join("chaves", "manifesto", "ed25519_public.json")
_CHAVE_PRIVADA_RELATIVA = os.path.join("chaves", "manifesto", "ed25519_private.pem")
_ENV_CHAVE_PRIVADA = "AIDD_MANIFESTO_CHAVE_PRIVADA"


def _default_ecossistema_root() -> Path:
    """Raiz real do monorepo ecossistema-aidd, descoberta por marcação
    (presença de ecossistema.py). Isolada para monkeypatch em testes — ver
    tests/conftest.py (mesma estratégia usada por materializador.py)."""
    atual = Path(__file__).resolve().parent
    for candidato in atual.parents:
        if (candidato / "ecossistema.py").is_file():
            return candidato
    return atual.parents[3]


def caminho_chave_publica(ecossistema_root: Optional[Path] = None) -> Path:
    """Caminho da chave pública Ed25519 (versionada no repositório)."""
    root = ecossistema_root if ecossistema_root is not None else _default_ecossistema_root()
    return Path(root) / _CHAVE_PUBLICA_RELATIVA


def caminho_chave_privada(ecossistema_root: Optional[Path] = None) -> Path:
    """Caminho da chave privada Ed25519 (NUNCA versionada — *.pem no .gitignore).

    Aceita override explícito via variável de ambiente AIDD_MANIFESTO_CHAVE_PRIVADA
    para ambientes onde a chave fica fora da árvore do monorepo (ex.: CI/CD com
    segredo montado em outro caminho).
    """
    override = os.environ.get(_ENV_CHAVE_PRIVADA)
    if override:
        return Path(override)
    root = ecossistema_root if ecossistema_root is not None else _default_ecossistema_root()
    return Path(root) / _CHAVE_PRIVADA_RELATIVA


def gerar_par_chaves() -> "tuple[bytes, bytes]":
    """Gera um novo par de chaves Ed25519. Retorna (chave_privada_pem, chave_publica_raw)."""
    chave_privada = Ed25519PrivateKey.generate()
    chave_publica = chave_privada.public_key()
    privada_pem = chave_privada.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    publica_raw = chave_publica.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return privada_pem, publica_raw


def salvar_par_chaves(ecossistema_root: Optional[Path] = None, sobrescrever: bool = False) -> Result:
    """Gera e persiste o par de chaves: privada em PEM (gitignored via '*.pem')
    e pública em JSON base64 (versionada — Definição de Pronto item 1)."""
    pub_path = caminho_chave_publica(ecossistema_root)
    priv_path = caminho_chave_privada(ecossistema_root)

    if not sobrescrever and (pub_path.is_file() or priv_path.is_file()):
        return Result.fail(
            f"Par de chaves já existe ({pub_path} / {priv_path}); "
            "use sobrescrever=True para regenerar (invalida assinaturas antigas).",
            codigo="CHAVE_JA_EXISTE",
        )

    privada_pem, publica_raw = gerar_par_chaves()

    pub_path.parent.mkdir(parents=True, exist_ok=True)
    priv_path.parent.mkdir(parents=True, exist_ok=True)

    payload_publico: Dict[str, Any] = {
        "algoritmo": "ed25519",
        "chave_publica_base64": base64.b64encode(publica_raw).decode("ascii"),
        "gerado_em": datetime.datetime.now().isoformat(),
        "uso": (
            "Verificação da assinatura do manifesto canônico CAPABILITIES.json "
            "(sincronizador_harness / MCPServer.register_injected_tools)."
        ),
    }
    with open(pub_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload_publico, f, ensure_ascii=False, indent=2)
        f.write("\n")

    with open(priv_path, "wb") as f:
        f.write(privada_pem)
    try:
        os.chmod(priv_path, 0o600)
    except OSError:
        pass

    return Result.ok({"chave_publica": str(pub_path), "chave_privada": str(priv_path)})


def _carregar_chave_privada(ecossistema_root: Optional[Path] = None) -> Ed25519PrivateKey:
    caminho = caminho_chave_privada(ecossistema_root)
    with open(caminho, "rb") as f:
        chave = serialization.load_pem_private_key(f.read(), password=None)
    if not isinstance(chave, Ed25519PrivateKey):
        raise ValueError(f"Chave privada em {caminho} não é Ed25519.")
    return chave


def _carregar_chave_publica(ecossistema_root: Optional[Path] = None) -> Ed25519PublicKey:
    caminho = caminho_chave_publica(ecossistema_root)
    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)
    if dados.get("algoritmo") != "ed25519" or "chave_publica_base64" not in dados:
        raise ValueError(f"Chave pública em {caminho} tem formato inválido.")
    raw = base64.b64decode(dados["chave_publica_base64"])
    return Ed25519PublicKey.from_public_bytes(raw)


def assinar_manifesto(caminho_manifesto: str, ecossistema_root: Optional[Path] = None) -> Result:
    """Assina os bytes exatos do manifesto canônico em disco com a chave
    privada Ed25519, gravando a assinatura em '<caminho_manifesto>.ed25519.sig'
    (base64, texto puro). Não bloqueia o chamador se a chave privada estiver
    ausente — apenas retorna falha (o manifesto fica sem assinatura, e
    register_injected_tools/verificar_manifesto irão recusar confiar nele)."""
    if not os.path.isfile(caminho_manifesto):
        return Result.fail(f"Manifesto não encontrado: {caminho_manifesto}", codigo="MANIFESTO_AUSENTE")

    priv_path = caminho_chave_privada(ecossistema_root)
    if not priv_path.is_file():
        return Result.fail(
            f"Chave privada de assinatura não encontrada em {priv_path}. "
            "Gere o par com 'python scripts/gerar_chave_manifesto.py'.",
            codigo="CHAVE_PRIVADA_AUSENTE",
        )

    try:
        chave_privada = _carregar_chave_privada(ecossistema_root)
        with open(caminho_manifesto, "rb") as f:
            conteudo = f.read()
        assinatura = chave_privada.sign(conteudo)
        sig_path = caminho_manifesto + SUFIXO_ASSINATURA
        with open(sig_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(base64.b64encode(assinatura).decode("ascii"))
            f.write("\n")
        return Result.ok({"assinatura": sig_path})
    except (OSError, ValueError) as exc:
        return Result.fail(f"Falha ao assinar manifesto: {exc}", codigo="ASSINATURA_FALHOU")


def verificar_manifesto(caminho_manifesto: str, ecossistema_root: Optional[Path] = None) -> Result:
    """Verifica a assinatura Ed25519 do manifesto canônico contra a chave
    pública versionada. Fail-closed: manifesto ausente, chave pública ausente,
    assinatura ausente, corrompida ou inválida — todos retornam Result.fail.
    Nenhum estado de erro é tratado como 'confiar por omissão'."""
    if not os.path.isfile(caminho_manifesto):
        return Result.fail(f"Manifesto não encontrado: {caminho_manifesto}", codigo="MANIFESTO_AUSENTE")

    pub_path = caminho_chave_publica(ecossistema_root)
    if not pub_path.is_file():
        return Result.fail(
            f"Chave pública de verificação não encontrada em {pub_path}.",
            codigo="CHAVE_PUBLICA_AUSENTE",
        )

    sig_path = caminho_manifesto + SUFIXO_ASSINATURA
    if not os.path.isfile(sig_path):
        return Result.fail(
            f"Assinatura ausente para o manifesto: {sig_path}",
            codigo="ASSINATURA_AUSENTE",
        )

    try:
        chave_publica = _carregar_chave_publica(ecossistema_root)
        with open(caminho_manifesto, "rb") as f:
            conteudo = f.read()
        with open(sig_path, "r", encoding="utf-8") as f:
            assinatura = base64.b64decode(f.read().strip())
        chave_publica.verify(assinatura, conteudo)
        return Result.ok({"manifesto": caminho_manifesto})
    except InvalidSignature:
        return Result.fail(
            f"Assinatura Ed25519 inválida para {caminho_manifesto} (manifesto adulterado ou "
            "assinado com outra chave).",
            codigo="ASSINATURA_INVALIDA",
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Result.fail(f"Falha ao verificar assinatura de {caminho_manifesto}: {exc}", codigo="ASSINATURA_INVALIDA")


def obter_hashes_confiaveis(root_dir: str, tipo: str, ecossistema_root: Optional[Path] = None) -> Result:
    """Retorna {caminho_relativo: sha256} das entradas do tipo informado no
    manifesto CAPABILITIES.json de 'root_dir', SOMENTE quando a assinatura
    Ed25519 do manifesto verifica. Fail-closed: qualquer problema de
    verificação propaga a falha — o chamador (ex.: register_injected_tools)
    NÃO deve carregar nada com base em hashes não confirmados."""
    manifesto_path = os.path.join(root_dir, NOME_ARQUIVO_MANIFESTO)

    verificacao = verificar_manifesto(manifesto_path, ecossistema_root=ecossistema_root)
    if not verificacao.sucesso:
        return verificacao

    try:
        with open(manifesto_path, "r", encoding="utf-8") as f:
            catalogo = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return Result.fail(f"Manifesto corrompido: {exc}", codigo="MANIFESTO_INVALIDO")

    hashes: Dict[str, str] = {}
    for componente in catalogo.get(tipo, []) or []:
        if isinstance(componente, dict):
            hashes.update(componente.get("arquivos_hashes") or {})

    return Result.ok(hashes)
