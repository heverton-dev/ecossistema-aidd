# -*- coding: utf-8 -*-
"""
=============================================================================
Testes do CofreCredenciais — NIH #18/#29 (sops + age)
=============================================================================
Reproduz de verdade o ciclo completo cifrar/decifrar com os binarios reais
sops+age (sem mocks de criptografia) sempre que ambos estao disponiveis no
PATH da maquina que roda os testes. Onde o binario nao esta instalado, o
teste e pulado explicitamente (nunca finge sucesso).
"""

import os
import re
import shutil
import sys

import pytest

TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TOOL_ROOT not in sys.path:
    sys.path.insert(0, TOOL_ROOT)
if os.path.join(TOOL_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(TOOL_ROOT, "src"))

from src.core.cofre_credenciais import CofreCredenciais
from src.core.result import Result

SOPS_DISPONIVEL = shutil.which("sops") is not None
AGE_KEYGEN_DISPONIVEL = shutil.which("age-keygen") is not None

requer_sops_e_age = pytest.mark.skipif(
    not (SOPS_DISPONIVEL and AGE_KEYGEN_DISPONIVEL),
    reason="sops e/ou age-keygen nao instalados no PATH desta maquina",
)


class TestGeracaoChaveAge:
    def test_binario_ausente_retorna_falha_explicita(self):
        cofre = CofreCredenciais(age_keygen_bin="binario-que-nao-existe-xyz")
        res = cofre.gerar_chave_age("/tmp/nao-importa/keys.txt")
        assert res.sucesso is False
        assert res.codigo == "AGE_NAO_INSTALADO"

    @requer_sops_e_age
    def test_gerar_chave_age_real(self, tmp_path):
        cofre = CofreCredenciais()
        caminho_chave = str(tmp_path / "age-key.txt")
        res = cofre.gerar_chave_age(caminho_chave)

        assert res.sucesso is True, res.erro
        assert res.valor["chave_publica"].startswith("age1")
        assert os.path.isfile(caminho_chave)
        conteudo = open(caminho_chave, encoding="utf-8").read()
        assert "AGE-SECRET-KEY-1" in conteudo

    @requer_sops_e_age
    def test_gerar_chave_age_nao_sobrescreve_existente(self, tmp_path):
        cofre = CofreCredenciais()
        caminho_chave = str(tmp_path / "age-key.txt")
        primeira = cofre.gerar_chave_age(caminho_chave)
        assert primeira.sucesso is True

        segunda = cofre.gerar_chave_age(caminho_chave)
        assert segunda.sucesso is False
        assert segunda.codigo == "CHAVE_JA_EXISTE"


class TestSopsConfig:
    def test_rejeita_lista_vazia_de_chaves(self, tmp_path):
        cofre = CofreCredenciais()
        res = cofre.gerar_sops_config(str(tmp_path / ".sops.yaml"), [])
        assert res.sucesso is False
        assert res.codigo == "CHAVES_PUBLICAS_VAZIAS"

    def test_rejeita_chave_publica_invalida(self, tmp_path):
        cofre = CofreCredenciais()
        res = cofre.gerar_sops_config(str(tmp_path / ".sops.yaml"), ["nao-e-uma-chave-age"])
        assert res.sucesso is False
        assert res.codigo == "CHAVE_PUBLICA_INVALIDA"

    def test_gera_conteudo_esperado(self, tmp_path):
        cofre = CofreCredenciais()
        caminho = str(tmp_path / ".sops.yaml")
        res = cofre.gerar_sops_config(caminho, ["age1exemplo000000000000000000000000000000000000000000000000000"])
        assert res.sucesso is True
        conteudo = open(caminho, encoding="utf-8").read()
        assert "creation_rules:" in conteudo
        assert "age1exemplo" in conteudo

    def test_padrao_sops_config_casa_com_path_absoluto_windows_e_posix(self, tmp_path):
        # O sops casa a creation rule contra o caminho ABSOLUTO do arquivo de
        # entrada (.env), nao o .env.enc de saida. Por isso o default precisa
        # de separador de diretorio agnostico ([\\/]) — o default antigo
        # (templates/infra/.*\.env\.enc$) nunca casava no Windows nem com o input.
        cofre = CofreCredenciais()
        caminho = str(tmp_path / ".sops.yaml")
        res = cofre.gerar_sops_config(
            caminho,
            ["age1exemplo000000000000000000000000000000000000000000000000000"],
        )
        assert res.sucesso is True
        linha = [l for l in open(caminho, encoding="utf-8").read().splitlines() if "path_regex" in l][0]
        regex = linha.split("'")[1]
        assert re.search(regex, r"C:\Users\ops\templates\infra\calcom\.env")
        assert re.search(regex, "/srv/aidd/templates/infra/calcom/.env")
        assert not re.search(regex, r"C:\Users\ops\templates\infra\calcom\.env.enc")


class TestCifrarRegressaoSmokeCLI:
    """Regressao do fluxo real descoberto em smoke test da CLI.

    (1) `cofre encrypt --chave-publica ...` falhava com "no matching creation
    rules found" sempre que existia um .sops.yaml descoberto que nao casasse
    com o input — corrigido via config temporaria catch-all (--config).
    (2) `cofre encrypt` (sem chave explicita) dependia de um path_regex que
    nunca casava: o default agora casa com o .env de entrada e aguenta
    separador de diretorio do Windows.
    """

    @requer_sops_e_age
    def test_chave_explicita_funciona_mesmo_com_sops_yaml_ambient_nao_correspondente(self, tmp_path):
        cofre = CofreCredenciais()

        caminho_chave = str(tmp_path / "age-key.txt")
        res_chave = cofre.gerar_chave_age(caminho_chave)
        assert res_chave.sucesso is True
        chave_publica = res_chave.valor["chave_publica"]

        # .sops.yaml ambient que NAO casa com o input — o caso que afundava a CLI.
        cofre.gerar_sops_config(
            str(tmp_path / ".sops.yaml"),
            [chave_publica],
            padrao_arquivo=r"templates/infra/.*\.env\.enc$",
        )

        caminho_env = str(tmp_path / ".env")
        with open(caminho_env, "w", encoding="utf-8") as f:
            f.write("POSTGRES_ADMIN_PASSWORD=segredo\n")

        caminho_enc = str(tmp_path / ".env.enc")
        res_cifrar = cofre.cifrar_env(caminho_env, caminho_enc, chave_publica=chave_publica)
        assert res_cifrar.sucesso is True, res_cifrar.erro
        assert "segredo" not in open(caminho_enc, encoding="utf-8").read()

    @requer_sops_e_age
    def test_cifrar_via_sops_config_descoberto_casando_com_o_env(self, tmp_path):
        cofre = CofreCredenciais()

        caminho_chave = str(tmp_path / "age-key.txt")
        res_chave = cofre.gerar_chave_age(caminho_chave)
        assert res_chave.sucesso is True
        chave_publica = res_chave.valor["chave_publica"]

        # Config no estilo real (default novo): casando com o input .env sob
        # templates/infra/ — o caminho absoluto do Windows aguentado pelo [\\/].
        res_config = cofre.gerar_sops_config(str(tmp_path / ".sops.yaml"), [chave_publica])
        assert res_config.sucesso is True

        pasta_servico = tmp_path / "templates" / "infra" / "calcom"
        pasta_servico.mkdir(parents=True)
        caminho_env = str(pasta_servico / ".env")
        with open(caminho_env, "w", encoding="utf-8") as f:
            f.write("CALCOM_DB_PASSWORD=senha-que-nao-vaza\n")

        caminho_enc = str(pasta_servico / ".env.enc")
        res_cifrar = cofre.cifrar_env(caminho_env, caminho_enc)
        assert res_cifrar.sucesso is True, res_cifrar.erro
        assert "senha-que-nao-vaza" not in open(caminho_enc, encoding="utf-8").read()

        res_decifrar = cofre.decifrar_env(caminho_enc, str(tmp_path / "saida.env"), arquivo_chave_privada=caminho_chave)
        assert res_decifrar.sucesso is True, res_decifrar.erro
        assert "CALCOM_DB_PASSWORD=senha-que-nao-vaza" in open(str(tmp_path / "saida.env"), encoding="utf-8").read()


class TestCifrarDecifrarRoundTrip:
    @requer_sops_e_age
    def test_round_trip_real_preserva_conteudo_original(self, tmp_path):
        cofre = CofreCredenciais()

        caminho_chave = str(tmp_path / "age-key.txt")
        res_chave = cofre.gerar_chave_age(caminho_chave)
        assert res_chave.sucesso is True, res_chave.erro
        chave_publica = res_chave.valor["chave_publica"]

        env_plano_original = (
            "POSTGRES_ADMIN_PASSWORD=SenhaSuperSecreta123!\n"
            "AUTHENTIK_SECRET_KEY=abcdef0123456789\n"
        )
        caminho_env = str(tmp_path / ".env")
        with open(caminho_env, "w", encoding="utf-8") as f:
            f.write(env_plano_original)

        caminho_enc = str(tmp_path / ".env.enc")
        res_cifrar = cofre.cifrar_env(caminho_env, caminho_enc, chave_publica=chave_publica)
        assert res_cifrar.sucesso is True, res_cifrar.erro
        assert os.path.isfile(caminho_enc)

        conteudo_cifrado = open(caminho_enc, encoding="utf-8").read()
        assert "SenhaSuperSecreta123!" not in conteudo_cifrado
        assert "abcdef0123456789" not in conteudo_cifrado
        assert "POSTGRES_ADMIN_PASSWORD" in conteudo_cifrado  # chave legivel, valor cifrado

        caminho_env_decifrado = str(tmp_path / ".env.decifrado")
        res_decifrar = cofre.decifrar_env(caminho_enc, caminho_env_decifrado, arquivo_chave_privada=caminho_chave)
        assert res_decifrar.sucesso is True, res_decifrar.erro

        conteudo_decifrado = open(caminho_env_decifrado, encoding="utf-8").read()
        assert "POSTGRES_ADMIN_PASSWORD=SenhaSuperSecreta123!" in conteudo_decifrado
        assert "AUTHENTIK_SECRET_KEY=abcdef0123456789" in conteudo_decifrado

    @requer_sops_e_age
    def test_decifrar_falha_com_chave_privada_errada(self, tmp_path):
        cofre = CofreCredenciais()

        caminho_chave_certa = str(tmp_path / "certa.txt")
        caminho_chave_errada = str(tmp_path / "errada.txt")
        res_certa = cofre.gerar_chave_age(caminho_chave_certa)
        res_errada = cofre.gerar_chave_age(caminho_chave_errada)
        assert res_certa.sucesso and res_errada.sucesso

        caminho_env = str(tmp_path / ".env")
        with open(caminho_env, "w", encoding="utf-8") as f:
            f.write("SEGREDO=valor-que-nao-deve-vazar\n")

        caminho_enc = str(tmp_path / ".env.enc")
        res_cifrar = cofre.cifrar_env(caminho_env, caminho_enc, chave_publica=res_certa.valor["chave_publica"])
        assert res_cifrar.sucesso is True

        res_decifrar = cofre.decifrar_env(caminho_enc, str(tmp_path / "saida.env"), arquivo_chave_privada=caminho_chave_errada)
        assert res_decifrar.sucesso is False
        assert res_decifrar.codigo == "ERRO_DECIFRAGEM"

    def test_cifrar_falha_se_sops_ausente(self, tmp_path):
        cofre = CofreCredenciais(sops_bin="binario-que-nao-existe-xyz")
        caminho_env = str(tmp_path / ".env")
        with open(caminho_env, "w", encoding="utf-8") as f:
            f.write("A=1\n")
        res = cofre.cifrar_env(caminho_env, str(tmp_path / ".env.enc"))
        assert res.sucesso is False
        assert res.codigo == "SOPS_NAO_INSTALADO"

    def test_cifrar_falha_se_env_origem_nao_existe(self):
        cofre = CofreCredenciais(sops_bin="sops-fake-presente")
        res = cofre.cifrar_env("/caminho/que/nao/existe/.env", "/tmp/saida.env.enc")
        assert res.sucesso is False
        assert res.codigo in ("SOPS_NAO_INSTALADO", "ENV_ORIGEM_NAO_ENCONTRADO")


class TestIntegracaoDockerCompose:
    def test_monta_comando_com_detach_por_padrao(self):
        cofre = CofreCredenciais()
        comando = cofre.montar_comando_docker_compose_up("/svc/docker-compose.yml", "/svc/.env")
        assert comando == ["docker", "compose", "-f", "/svc/docker-compose.yml", "--env-file", "/svc/.env", "up", "-d"]

    def test_monta_comando_sem_detach(self):
        cofre = CofreCredenciais()
        comando = cofre.montar_comando_docker_compose_up("/svc/docker-compose.yml", "/svc/.env", detach=False)
        assert comando == ["docker", "compose", "-f", "/svc/docker-compose.yml", "--env-file", "/svc/.env", "up"]

    def test_subir_servico_falha_sem_compose(self, tmp_path):
        cofre = CofreCredenciais(dry_run=True)
        res = cofre.subir_servico_com_cofre(str(tmp_path))
        assert res.sucesso is False
        assert res.codigo == "COMPOSE_NAO_ENCONTRADO"

    @requer_sops_e_age
    def test_subir_servico_dry_run_decifra_e_monta_comando_sem_executar(self, tmp_path):
        cofre = CofreCredenciais(dry_run=True)

        caminho_chave = str(tmp_path / "age-key.txt")
        res_chave = cofre.gerar_chave_age(caminho_chave)
        assert res_chave.sucesso is True

        (tmp_path / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")

        caminho_env = str(tmp_path / ".env")
        with open(caminho_env, "w", encoding="utf-8") as f:
            f.write("POSTGRES_ADMIN_PASSWORD=segredo-real\n")
        res_cifrar = cofre.cifrar_env(caminho_env, str(tmp_path / ".env.enc"), chave_publica=res_chave.valor["chave_publica"])
        assert res_cifrar.sucesso is True
        os.remove(caminho_env)  # simula ambiente limpo: so o .env.enc existe versionado

        res_subir = cofre.subir_servico_com_cofre(str(tmp_path), arquivo_chave_privada=caminho_chave)
        assert res_subir.sucesso is True, res_subir.erro
        assert res_subir.valor["executado"] is False
        assert res_subir.valor["comando"][:2] == ["docker", "compose"]
        assert os.path.isfile(caminho_env)  # .env foi materializado a partir do .env.enc
        assert "segredo-real" in open(caminho_env, encoding="utf-8").read()
