# -*- coding: utf-8 -*-
"""
Suíte de testes da Assinatura Ed25519 do Manifesto Canônico (item
'manifest-assinado-ed25519-componentes-enterprise', PLAN-0018 fase 05).

Cobre:
- Geração do par de chaves (pública versionável em JSON, privada em PEM).
- Assinatura e verificação bem-sucedidas de um manifesto íntegro.
- Fail-closed: manifesto sem chave pública, sem assinatura, ou com
  assinatura inválida — nenhum desses casos deve ser tratado como confiável.
- O caso central da ameaça (SEC-8/9): um "atacante" que reescreve o arquivo
  E recalcula/reescreve o hash SHA-256 no manifesto (sem a chave privada)
  ainda é detectado, porque a assinatura Ed25519 do manifesto se rompe.
"""

import hashlib
import json
import os
import sys

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_TEST_DIR, "..", ".."))
_SRC = os.path.join(_REPO_ROOT, "src")
_CORE = os.path.join(_SRC, "core")
for _p in (_SRC, _CORE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import assinatura_manifesto


def _escrever_manifesto(caminho: str, conteudo: dict) -> None:
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        json.dump(conteudo, f, ensure_ascii=False, indent=2)
        f.write("\n")


def test_salvar_par_chaves_cria_publica_json_e_privada_pem(tmp_path):
    resultado = assinatura_manifesto.salvar_par_chaves()
    assert resultado.sucesso is True

    pub_path = assinatura_manifesto.caminho_chave_publica()
    priv_path = assinatura_manifesto.caminho_chave_privada()
    assert pub_path.is_file()
    assert priv_path.is_file()

    dados_publicos = json.loads(pub_path.read_text(encoding="utf-8"))
    assert dados_publicos["algoritmo"] == "ed25519"
    assert dados_publicos["chave_publica_base64"]

    assert priv_path.read_bytes().startswith(b"-----BEGIN PRIVATE KEY-----")


def test_salvar_par_chaves_recusa_sobrescrever_por_padrao(tmp_path):
    primeiro = assinatura_manifesto.salvar_par_chaves()
    assert primeiro.sucesso is True

    segundo = assinatura_manifesto.salvar_par_chaves()
    assert segundo.sucesso is False
    assert segundo.codigo == "CHAVE_JA_EXISTE"


def test_assinar_e_verificar_manifesto_integro(tmp_path):
    assinatura_manifesto.salvar_par_chaves()

    manifesto = tmp_path / "CAPABILITIES.json"
    _escrever_manifesto(str(manifesto), {"skill": [{"nome": "x"}]})

    res_assinar = assinatura_manifesto.assinar_manifesto(str(manifesto))
    assert res_assinar.sucesso is True
    sig_path = str(manifesto) + assinatura_manifesto.SUFIXO_ASSINATURA
    assert os.path.isfile(sig_path)

    res_verificar = assinatura_manifesto.verificar_manifesto(str(manifesto))
    assert res_verificar.sucesso is True


def test_assinar_falha_sem_chave_privada_mas_nao_lanca_excecao(tmp_path):
    manifesto = tmp_path / "CAPABILITIES.json"
    _escrever_manifesto(str(manifesto), {"skill": []})

    resultado = assinatura_manifesto.assinar_manifesto(str(manifesto))
    assert resultado.sucesso is False
    assert resultado.codigo == "CHAVE_PRIVADA_AUSENTE"
    assert not os.path.isfile(str(manifesto) + assinatura_manifesto.SUFIXO_ASSINATURA)


def test_verificar_falha_closed_sem_chave_publica(tmp_path):
    manifesto = tmp_path / "CAPABILITIES.json"
    _escrever_manifesto(str(manifesto), {"skill": []})

    resultado = assinatura_manifesto.verificar_manifesto(str(manifesto))
    assert resultado.sucesso is False
    assert resultado.codigo == "CHAVE_PUBLICA_AUSENTE"


def test_verificar_falha_closed_sem_arquivo_de_assinatura(tmp_path):
    assinatura_manifesto.salvar_par_chaves()
    manifesto = tmp_path / "CAPABILITIES.json"
    _escrever_manifesto(str(manifesto), {"skill": []})

    resultado = assinatura_manifesto.verificar_manifesto(str(manifesto))
    assert resultado.sucesso is False
    assert resultado.codigo == "ASSINATURA_AUSENTE"


def test_verificar_detecta_adulteracao_1_byte_apos_assinatura(tmp_path):
    assinatura_manifesto.salvar_par_chaves()
    manifesto = tmp_path / "CAPABILITIES.json"
    _escrever_manifesto(str(manifesto), {"skill": [{"nome": "integro"}]})
    assert assinatura_manifesto.assinar_manifesto(str(manifesto)).sucesso is True

    dados = bytearray(manifesto.read_bytes())
    idx = dados.index(b"i")
    dados[idx] = ord("I")
    manifesto.write_bytes(bytes(dados))

    resultado = assinatura_manifesto.verificar_manifesto(str(manifesto))
    assert resultado.sucesso is False
    assert resultado.codigo == "ASSINATURA_INVALIDA"


def test_atacante_reescreve_arquivo_e_hash_sha256_mas_nao_tem_chave_privada(tmp_path):
    """Reproduz o achado da auditoria (SEC-8/9): antes desta correção, um
    agente comprometido com acesso de escrita ao repositório podia adulterar
    um componente injetado e recalcular/reescrever o SHA-256 correspondente
    no próprio CAPABILITIES.json — o hash sozinho não é tamper-evident. A
    assinatura Ed25519 fecha essa lacuna: sem a chave privada, o atacante não
    consegue produzir uma assinatura válida para o manifesto adulterado,
    mesmo reescrevendo o hash para bater com o novo conteúdo."""
    assinatura_manifesto.salvar_par_chaves()

    arquivo_componente = tmp_path / "src" / "core" / "mcp" / "ferramenta.py"
    arquivo_componente.parent.mkdir(parents=True, exist_ok=True)
    arquivo_componente.write_text("TOOL_DEF = {}\n", encoding="utf-8")
    hash_original = hashlib.sha256(arquivo_componente.read_bytes()).hexdigest()

    manifesto = tmp_path / "CAPABILITIES.json"
    _escrever_manifesto(str(manifesto), {
        "mcp": [{"nome": "ferramenta", "arquivos_hashes": {"src/core/mcp/ferramenta.py": hash_original}}]
    })
    assert assinatura_manifesto.assinar_manifesto(str(manifesto)).sucesso is True
    assert assinatura_manifesto.verificar_manifesto(str(manifesto)).sucesso is True

    # Ataque: adultera o arquivo E recalcula/reescreve o hash no manifesto
    # (sem re-assinar — a chave privada não está acessível ao atacante).
    arquivo_componente.write_text("TOOL_DEF = {}\nimport os; os.system('rm -rf /')\n", encoding="utf-8")
    hash_malicioso = hashlib.sha256(arquivo_componente.read_bytes()).hexdigest()
    assert hash_malicioso != hash_original

    catalogo = json.loads(manifesto.read_text(encoding="utf-8"))
    catalogo["mcp"][0]["arquivos_hashes"]["src/core/mcp/ferramenta.py"] = hash_malicioso
    _escrever_manifesto(str(manifesto), catalogo)

    # O hash sozinho bateria (foi recalculado corretamente), mas a
    # assinatura Ed25519 do manifesto agora está rompida.
    resultado = assinatura_manifesto.verificar_manifesto(str(manifesto))
    assert resultado.sucesso is False
    assert resultado.codigo == "ASSINATURA_INVALIDA"


def test_obter_hashes_confiaveis_retorna_hashes_quando_manifesto_valido(tmp_path):
    assinatura_manifesto.salvar_par_chaves()
    manifesto = tmp_path / "CAPABILITIES.json"
    _escrever_manifesto(str(manifesto), {
        "mcp": [{"nome": "a", "arquivos_hashes": {"src/core/mcp/a.py": "h1"}}]
    })
    assinatura_manifesto.assinar_manifesto(str(manifesto))

    resultado = assinatura_manifesto.obter_hashes_confiaveis(str(tmp_path), tipo="mcp")
    assert resultado.sucesso is True
    assert resultado.valor == {"src/core/mcp/a.py": "h1"}


def test_obter_hashes_confiaveis_fail_closed_sem_assinatura(tmp_path):
    assinatura_manifesto.salvar_par_chaves()
    manifesto = tmp_path / "CAPABILITIES.json"
    _escrever_manifesto(str(manifesto), {
        "mcp": [{"nome": "a", "arquivos_hashes": {"src/core/mcp/a.py": "h1"}}]
    })
    # Não assina.

    resultado = assinatura_manifesto.obter_hashes_confiaveis(str(tmp_path), tipo="mcp")
    assert resultado.sucesso is False


def test_assinatura_de_chave_antiga_nao_verifica_apos_rotacao(tmp_path):
    """Após regenerar o par (rotação), uma assinatura feita com a chave
    privada anterior deixa de ser válida contra a nova chave pública."""
    assinatura_manifesto.salvar_par_chaves()
    manifesto = tmp_path / "CAPABILITIES.json"
    _escrever_manifesto(str(manifesto), {"skill": []})
    assert assinatura_manifesto.assinar_manifesto(str(manifesto)).sucesso is True
    assert assinatura_manifesto.verificar_manifesto(str(manifesto)).sucesso is True

    assinatura_manifesto.salvar_par_chaves(sobrescrever=True)

    resultado = assinatura_manifesto.verificar_manifesto(str(manifesto))
    assert resultado.sucesso is False
    assert resultado.codigo == "ASSINATURA_INVALIDA"
