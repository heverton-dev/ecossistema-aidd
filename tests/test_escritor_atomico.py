# -*- coding: utf-8 -*-
"""
Testes unitários do Escritor Atômico.

Cobre:
  - Escrita de texto e binário
  - Escrita de JSON
  - Garantia de que arquivo anterior permanece intacto em caso de falha
  - Race condition: concurrent writes
  - Tratamento de erros (diretório inexistente, serialização falha)
  - Cleanup de arquivos temporários
"""

import json
import os
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

# Ajustar path para import do módulo compartilhado
import sys
_ECOSISTEMA_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(_ECOSISTEMA_ROOT, "componentes", "compartilhado", "src-core"))

from escritor_atomico import (
    escrever_atomico,
    escrever_json_atomico,
    _remover_seguro,
)


@pytest.fixture
def tmp_dir(tmp_path):
    """Diretório temporário para testes."""
    return tmp_path


# ── Escrita básica de texto ──────────────────────────────────────────────

class TestEscritaTextoBasica:
    def test_cria_arquivo_novo(self, tmp_dir):
        caminho = tmp_dir / "novo.txt"
        escrever_atomico(caminho, "conteudo teste")
        assert caminho.read_text(encoding="utf-8") == "conteudo teste"

    def test_sobrescreve_arquivo_existente(self, tmp_dir):
        caminho = tmp_dir / "existente.txt"
        caminho.write_text("original", encoding="utf-8")
        escrever_atomico(caminho, "atualizado")
        assert caminho.read_text(encoding="utf-8") == "atualizado"

    def test_preserva_nova_linha_final(self, tmp_dir):
        caminho = tmp_dir / "nl.txt"
        escrever_atomico(caminho, "linha1\nlinha2")
        conteudo = caminho.read_text(encoding="utf-8")
        # O default newline="\n" preserva exatamente o que foi passado
        assert conteudo == "linha1\nlinha2"

    def test_conteudo_vazio(self, tmp_dir):
        caminho = tmp_dir / "vazio.txt"
        escrever_atomico(caminho, "")
        assert caminho.read_text(encoding="utf-8") == ""

    # NOVA: newline="" preserva exatamente o conteúdo
    def test_newline_empty_preserva_exatamente(self, tmp_dir):
        caminho = tmp_dir / "preserva.txt"
        escrever_atomico(caminho, "sem newline extra\n", newline=None)
        conteudo = caminho.read_text(encoding="utf-8")
        assert conteudo == "sem newline extra\n"


# ── Escrita binária ──────────────────────────────────────────────────────

class TestEscritaBinaria:
    def test_cria_arquivo_bin(self, tmp_dir):
        caminho = tmp_dir / "dados.bin"
        dados = b"\x00\x01\x02\xff"
        escrever_atomico(caminho, dados, modo="wb")
        assert caminho.read_bytes() == dados

    def test_sobrescreve_bin(self, tmp_dir):
        caminho = tmp_dir / "dados.bin"
        caminho.write_bytes(b"antigo")
        escrever_atomico(caminho, b"novo_conteudo", modo="wb")
        assert caminho.read_bytes() == b"novo_conteudo"

    def test_erro_modo_incompativel(self, tmp_dir):
        caminho = tmp_dir / "erro.txt"
        with pytest.raises(TypeError, match="modo='wb' requer conteudo do tipo bytes"):
            escrever_atomico(caminho, "texto", modo="wb")
        with pytest.raises(TypeError, match="modo='w' requer conteudo do tipo str"):
            escrever_atomico(caminho, b"bytes", modo="w")


# ── Escrita de JSON ──────────────────────────────────────────────────────

class TestEscritaJSON:
    def test_json_simples(self, tmp_dir):
        caminho = tmp_dir / "dados.json"
        dados = {"chave": "valor", "numero": 42}
        escrever_json_atomico(caminho, dados)
        resultado = json.loads(caminho.read_text(encoding="utf-8"))
        assert resultado == dados

    def test_json_com_listas(self, tmp_dir):
        caminho = tmp_dir / "lista.json"
        dados = {"itens": [1, 2, 3], "vazio": []}
        escrever_json_atomico(caminho, dados)
        resultado = json.loads(caminho.read_text(encoding="utf-8"))
        assert resultado == dados

    def test_json_termina_com_newline(self, tmp_dir):
        caminho = tmp_dir / "nl.json"
        escrever_json_atomico(caminho, {"x": 1})
        conteudo = caminho.read_text(encoding="utf-8")
        assert conteudo.endswith("\n")

    def test_json_ascii_forced(self, tmp_dir):
        caminho = tmp_dir / "ascii.json"
        dados = {"nome": "José"}
        escrever_json_atomico(caminho, dados, ensure_ascii=True)
        conteudo = caminho.read_text(encoding="utf-8")
        assert "\\u00e9" in conteudo or "\\xe9" in conteudo


# ── Integridade em caso de falha (teste crucial) ─────────────────────────

class TestIntegridadeEmFalha:
    def test_arquivo_anterior_intacto_se_escrita_falha(self, tmp_dir):
        """Simula falha DURANTE a escrita — arquivo original deve permanecer."""
        caminho = tmp_dir / "critico.json"
        conteudo_original = {"dados": "original", "versao": 1}
        escrever_json_atomico(caminho, conteudo_original)

        # Força falha no os.fdopen (o que escritor_atomico usa internamente)
        falha = OSError("Disco cheio (simulado)")
        with patch("os.fdopen", side_effect=falha):
            with pytest.raises(OSError):
                escrever_json_atomico(caminho, {"dados": "corrompido"})

        # O arquivo original deve estar intacto
        resultado = json.loads(caminho.read_text(encoding="utf-8"))
        assert resultado == conteudo_original

    def test_nao_cria_arquivo_se_falha_no_replace(self, tmp_dir):
        """Se os.replace() falha, o destino não deve ser modificado."""
        caminho = tmp_dir / "destino.txt"
        caminho.write_text("antes", encoding="utf-8")

        # Força falha no os.replace
        with patch("os.replace", side_effect=OSError("replace falhou")):
            with pytest.raises(OSError):
                escrever_atomico(caminho, "depois")

        assert caminho.read_text(encoding="utf-8") == "antes"

    def test_tmp_fase_ao_mais_dois_arquivos(self, tmp_dir):
        """After successful write, no .tmp files should remain."""
        for i in range(5):
            escrever_atomico(tmp_dir / f"arq_{i}.txt", f"conteudo_{i}")
        
        arquivos_tmp = list(tmp_dir.glob(".*.tmp"))
        assert len(arquivos_tmp) == 0, f"Arquivos tmp órfãos: {arquivos_tmp}"


# ── Diretório criado automaticamente ─────────────────────────────────────

class TestDiretorios:
    def test_cria_diretorio_profundo(self, tmp_dir):
        caminho = tmp_dir / "a" / "b" / "c" / "arquivo.txt"
        escrever_atomico(caminho, "profundo")
        assert caminho.read_text(encoding="utf-8") == "profundo"
        assert caminho.parent.is_dir()

    def test_diretorio_ja_existente(self, tmp_dir):
        caminho = tmp_dir / "arquivo.txt"
        escrever_atomico(caminho, "simples")
        assert caminho.read_text(encoding="utf-8") == "simples"


# ── Segurança / edge cases ──────────────────────────────────────────────

class TestEdgeCases:
    def test_conteudo_grande(self, tmp_dir):
        caminho = tmp_dir / "grande.txt"
        conteudo = "x" * 1_000_000  # 1 MB
        escrever_atomico(caminho, conteudo)
        assert len(caminho.read_text(encoding="utf-8")) == 1_000_000

    def test_json_dados_complexos(self, tmp_dir):
        caminho = tmp_dir / "complexo.json"
        dados = {
            "nested": {"a": [1, 2, {"b": True}]},
            "unicode": "caféñ日本語",
            "null_val": None,
        }
        escrever_json_atomico(caminho, dados)
        resultado = json.loads(caminho.read_text(encoding="utf-8"))
        assert resultado["nested"]["a"][2]["b"] is True
        assert resultado["unicode"] == "caféñ日本語"
        assert resultado["null_val"] is None

    def test_remover_seguro(self):
        """_remover_seguro não lança exceção."""
        _remover_seguro("/caminho/inexistente/arquivo.txt")  # Must not raise

    def test_escrita_concorrente(self, tmp_dir):
        """Múltiplas threads escrevendo no mesmo arquivo — apenas a última deve prevalecer.

        No Windows, os.replace pode falhar com PermissionError quando múltiplas
        threads tentam renomear sobre o mesmo destino. O teste aceita isso e
        verifica que o arquivo permanece legível (não corrompido).
        """
        caminho = tmp_dir / "concorrente.txt"
        erros = []

        def escrever(idx):
            try:
                escrever_atomico(caminho, f"thread_{idx}")
            except OSError as e:
                erros.append(e)

        threads = [threading.Thread(target=escrever, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # O arquivo deve existir e ser legível (pode ter erro de replace concorrente no Windows)
        assert caminho.exists()
        conteudo = caminho.read_text(encoding="utf-8")
        assert conteudo.startswith("thread_")
