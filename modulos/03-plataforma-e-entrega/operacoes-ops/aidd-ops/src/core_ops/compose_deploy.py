# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops — DEPLOY `compose-nativo` POR SSH (único motor; o Coolify foi abolido)
=============================================================================
Copia o projeto gerado pelo aidd-master para a VPS e sobe com `docker compose up -d --build`:

  1. valida o nome do ambiente (vira diretório remoto: nada de shell injection);
  2. empacota o projeto SEM segredos (`.env`, `.env.*` exceto `.env.example`, chaves), `.git`, `node_modules`,
     caches e builds;
  3. `mkdir -p /opt/aidd/<ambiente>`, envia o `.tgz`, extrai, `docker compose up -d --build`;
  4. confere `docker compose ps --format json`: todo serviço precisa estar `running` e sem `unhealthy`.

O transporte SSH é injetado (`executar(comando) -> (rc, saida)` e `enviar(bytes, destino)`), o que torna o
encadeamento testável sem VPS. O transporte real (`TransporteParamiko`) usa paramiko e NÃO foi exercitado contra
um servidor de verdade nesta etapa. As variáveis de runtime do projeto (`.env`) não sobem: o operador as cria na VPS.
=============================================================================
"""

import fnmatch
import io
import json
import os
import re
import tarfile
from typing import Any, Dict, List, Optional, Tuple

try:
    from src.core_ops.result import Result
except ImportError:
    from core_ops.result import Result

BASE_REMOTA = "/opt/aidd"
_RE_AMBIENTE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,62}$")
_PASTAS_EXCLUIDAS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache", "dist", ".aidd"}
_PADROES_EXCLUIDOS = (".env", ".env.*", "*.pem", "*.key", "id_rsa*", "id_ed25519*")
_EXCECOES = (".env.example",)


def _excluido(rel_posix: str) -> bool:
    partes = rel_posix.split("/")
    if any(p in _PASTAS_EXCLUIDAS for p in partes[:-1]):
        return True
    nome = partes[-1]
    if nome in _EXCECOES:
        return False
    return any(fnmatch.fnmatch(nome, padrao) for padrao in _PADROES_EXCLUIDOS)


def listar_arquivos_do_pacote(dir_projeto: str) -> List[str]:
    arquivos: List[str] = []
    for raiz, pastas, nomes in os.walk(dir_projeto):
        pastas[:] = [p for p in pastas if p not in _PASTAS_EXCLUIDAS]
        for nome in nomes:
            rel = os.path.relpath(os.path.join(raiz, nome), dir_projeto).replace(os.sep, "/")
            if not _excluido(rel):
                arquivos.append(rel)
    return sorted(arquivos)


def _empacotar(dir_projeto: str) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for rel in listar_arquivos_do_pacote(dir_projeto):
            tar.add(os.path.join(dir_projeto, rel), arcname=rel, recursive=False)
    return buf.getvalue()


def _ler_ps(saida: str) -> List[Dict[str, Any]]:
    """`docker compose ps --format json` devolve um array ou um objeto JSON por linha, conforme a versão."""
    saida = (saida or "").strip()
    if not saida:
        return []
    try:
        dados = json.loads(saida)
        return dados if isinstance(dados, list) else [dados]
    except ValueError:
        itens = []
        for linha in saida.splitlines():
            linha = linha.strip()
            if linha.startswith("{"):
                try:
                    itens.append(json.loads(linha))
                except ValueError:
                    continue
        return itens


class ComposeDeployer:
    def __init__(self, host: str, user: str = "root", port: int = 22, transporte: Any = None,
                 dry_run: bool = False, chave: Optional[str] = None, senha: Optional[str] = None):
        self.host, self.user, self.port = host, user, port
        self.transporte = transporte
        self.dry_run = dry_run
        self.chave, self.senha = chave, senha

    def _comandos(self, base: str) -> List[str]:
        return [
            f"mkdir -p {base}",
            f"cd {base} && tar -xzf pacote.tgz && rm -f pacote.tgz",
            f"cd {base} && docker compose up -d --build",
            f"cd {base} && docker compose ps --format json",
        ]

    def deploy(self, dir_projeto: str, ambiente: str) -> Result:
        if not _RE_AMBIENTE.match(ambiente or ""):
            return Result.fail(
                f"Nome de ambiente inválido para diretório remoto: '{ambiente}'. Use letras minúsculas, números, '.', '_' ou '-'.",
                codigo="AMBIENTE_INVALIDO")
        compose = os.path.join(dir_projeto, "docker-compose.yml")
        if not os.path.isfile(compose):
            return Result.fail(f"docker-compose.yml não encontrado em '{dir_projeto}'.", codigo="COMPOSE_AUSENTE",
                               detalhes={"dir_projeto": dir_projeto})

        base = f"{BASE_REMOTA}/{ambiente}"
        arquivos = listar_arquivos_do_pacote(dir_projeto)
        if self.dry_run:
            return Result.ok({"dry_run": True, "host": self.host, "diretorio_remoto": base,
                              "arquivos": len(arquivos), "comandos": self._comandos(base)})

        transporte = self.transporte or TransporteParamiko(self.host, self.user, self.port, self.chave, self.senha)
        rc, saida = transporte.executar(f"mkdir -p {base}")
        if rc != 0:
            return Result.fail("Não foi possível criar o diretório remoto.", codigo="SSH_FALHOU",
                               detalhes={"log_final": saida[-800:]})
        transporte.enviar(_empacotar(dir_projeto), f"{base}/pacote.tgz")
        rc, saida = transporte.executar(self._comandos(base)[1])
        if rc != 0:
            return Result.fail("Falha ao extrair o pacote na VPS.", codigo="EXTRACAO_FALHOU",
                               detalhes={"log_final": saida[-800:]})
        rc, saida = transporte.executar(self._comandos(base)[2])
        if rc != 0:
            return Result.fail("`docker compose up -d --build` falhou na VPS.", codigo="COMPOSE_UP_FALHOU",
                               detalhes={"log_final": "\n".join(saida.splitlines()[-20:])})
        rc, saida = transporte.executar(self._comandos(base)[3])
        servicos = _ler_ps(saida) if rc == 0 else []
        ruins = [{"servico": s.get("Service") or s.get("Name"), "estado": s.get("State"), "saude": s.get("Health")}
                 for s in servicos if s.get("State") != "running" or s.get("Health") == "unhealthy"]
        if rc != 0 or not servicos or ruins:
            return Result.fail("Serviço(s) fora do ar depois do deploy.", codigo="SERVICO_NAO_SAUDAVEL",
                               detalhes={"servicos": ruins or "nenhum serviço reportado"})
        return Result.ok({"dry_run": False, "host": self.host, "diretorio_remoto": base,
                          "servicos": [s.get("Service") or s.get("Name") for s in servicos]})


class TransporteParamiko:
    """Transporte SSH real. NÃO exercitado contra uma VPS de verdade nesta etapa (só com injeção nos testes)."""

    def __init__(self, host: str, user: str = "root", port: int = 22, chave: Optional[str] = None,
                 senha: Optional[str] = None):
        try:
            import paramiko
        except ImportError as erro:
            raise RuntimeError("paramiko ausente: instale as dependências do aidd-ops.") from erro
        self._cliente = paramiko.SSHClient()
        self._cliente.set_missing_host_key_policy(paramiko.RejectPolicy())
        self._cliente.load_system_host_keys()
        self._cliente.connect(hostname=host, port=port, username=user, key_filename=chave or None,
                              password=senha or None, timeout=30, allow_agent=False, look_for_keys=False)

    def executar(self, comando: str) -> Tuple[int, str]:
        _, saida, erro = self._cliente.exec_command(comando, timeout=1800)
        texto = saida.read().decode("utf-8", "replace") + erro.read().decode("utf-8", "replace")
        return saida.channel.recv_exit_status(), texto

    def enviar(self, conteudo: bytes, destino_remoto: str) -> None:
        sftp = self._cliente.open_sftp()
        try:
            with sftp.file(destino_remoto, "wb") as arquivo:
                arquivo.write(conteudo)
        finally:
            sftp.close()
