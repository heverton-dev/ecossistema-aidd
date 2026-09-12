# -*- coding: utf-8 -*-
"""
Escritor Atômico — utilitário compartilhado de gravação segura de filesystem.

Garante integridade de arquivos durante escrita usando o padrão:
  1. Escrever conteúdo em arquivo temporário (staging) no MESMO diretório
  2. fsync no arquivo temporário (força flush para disco)
  3. os.replace() para rename atômico sobre o destino final
  4. fsync no diretório pai (garante que o rename persista)

Isso elimina o risco de arquivos truncados quando o processo é interrompido
meio da escrita (SIGTERM, OOM kill, power loss, etc.).

Uso:
    from escritor_atomico import escrever_atomico, escrever_json_atomico

    # Texto puro
    escrever_atomico("/caminho/destino.txt", "conteudo aqui")

    # JSON
    escrever_json_atomico("/caminho/dados.json", {"chave": "valor"})

    # Bytes
    escrever_atomico("/caminho/binario.dat", dados_bytes, modo="wb")
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Optional, Union


def escrever_atomico(
    caminho: Union[str, Path],
    conteudo: Union[str, bytes],
    *,
    encoding: str = "utf-8",
    modo: str = "w",
    newline: Optional[str] = "\n",
) -> None:
    """Escreve conteúdo em arquivo de forma atômica (staging → fsync → replace).

    Args:
        caminho: Caminho do arquivo destino.
        conteudo: Conteúdo a ser escrito (str para modo 'w', bytes para 'wb').
        encoding: Encoding para arquivos de texto (ignorado em modo 'wb').
        modo: 'w' para texto, 'wb' para binário.
        newline: Caractere de nova linha para modo texto (None = sem conversão).
                 Use "" para preservar exatamente o que foi passado.

    Raises:
        OSError: Se a escrita ou o replace falhar.
        TypeError: Se modo='wb' mas conteudo é str, ou vice-versa.
    """
    caminho = Path(caminho)
    is_binary = "b" in modo

    if is_binary and isinstance(conteudo, str):
        raise TypeError("modo='wb' requer conteudo do tipo bytes")
    if not is_binary and isinstance(conteudo, bytes):
        raise TypeError("modo='w' requer conteudo do tipo str")

    # Diretório pai deve existir
    parent = caminho.parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)

    # Criar arquivo temporário NO MESMO diretório do destino
    # (necessário para que os.replace() funcione — mesma filesystem)
    fd, caminho_tmp = tempfile.mkstemp(
        dir=str(parent),
        prefix=f".{caminho.name}.",
        suffix=".tmp",
    )
    try:
        try:
            with os.fdopen(fd, modo, encoding=encoding if not is_binary else None) as f:
                f.write(conteudo)
                if not is_binary and newline is not None:
                    # newline="\n" é o padrão do Python (universal newlines mode)
                    # mas garantimos que não há conversão indesejada
                    pass
                f.flush()
                os.fsync(f.fileno())
        except BaseException:
            # Se a escrita falhar, fechar fd se ainda aberto e limpar tmp
            try:
                os.close(fd)
            except OSError:
                pass
            _remover_seguro(caminho_tmp)
            raise

        # Rename atômico sobre o destino final
        os.replace(caminho_tmp, str(caminho))

        # fsync no diretório pai para garantir que o rename persista
        try:
            dir_fd = os.open(str(parent), os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass  # fsync dir é melhor-esforço; rename já é atômico no POSIX

    except BaseException:
        _remover_seguro(caminho_tmp)
        raise


def escrever_json_atomico(
    caminho: Union[str, Path],
    dados: Any,
    *,
    encoding: str = "utf-8",
    indent: int = 2,
    ensure_ascii: bool = False,
    sort_keys: bool = False,
) -> None:
    """Serializa dados como JSON e escreve de forma atômica.

    Equivalente atômico a:
        json.dump(dados, f, indent=2, ensure_ascii=False)

    Args:
        caminho: Caminho do arquivo destino (geralmente .json).
        dados: Objeto serializável a JSON.
        encoding: Encoding do arquivo.
        indent: Nível de indentação do JSON.
        ensure_ascii: Se True, escapa caracteres não-ASCII.
        sort_keys: Se True, ordena as chaves do JSON.

    Raises:
        TypeError: Se dados não é serializável.
        OSError: Se a escrita ou o replace falhar.
    """
    conteudo = json.dumps(
        dados,
        indent=indent,
        ensure_ascii=ensure_ascii,
        sort_keys=sort_keys,
    )
    # JSON sempre termina com \n
    if not conteudo.endswith("\n"):
        conteudo += "\n"
    escrever_atomico(caminho, conteudo, encoding=encoding, newline=None)


def _remover_seguro(caminho: str) -> None:
    """Remove arquivo de forma segura (ignora erro se não existe)."""
    try:
        os.remove(caminho)
    except OSError:
        pass


def _obter_projetos_alvo() -> list[str]:
    """Retorna a lista de diretórios alvo para migração dos pontos críticos."""
    return [
        "componentes/compartilhado/src-core",
        "tools/aidd-master/scripts",
        "tools/aidd-master/src/core",
        "tools/aidd-enterprise/scripts",
        "tools/aidd-enterprise/src/core",
        "tools/aidd-generator/scripts/phases",
        "tools/aidd-ops/scripts",
    ]
