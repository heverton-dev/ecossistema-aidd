# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops — COFRE DE CREDENCIAIS VIA SOPS + AGE (NIH #18/#29)
=============================================================================
Decisao registrada em docs/planos/a-fazer/03-evolucao-aidd-ops-fase-completa/
02-cofre-local-e-coleta-segura-de-credenciais.md: sops + age escolhidos
contra Vaultwarden. Vaultwarden foi descartado por trazer servico/banco de
dados pra um caso de uso que e pipeline automatizado (decrypt on demand
antes de `docker compose up`), nao humano compartilhando senha via UI.

sops (Mozilla) cifra o VALOR de cada variavel de um arquivo dotenv mantendo
as CHAVES legiveis (dotenv em texto claro de comparação/diff), usando age
(FiloSottile) como backend de criptografia assimetrica moderna (X25519 +
ChaCha20-Poly1305) — sem servidor, sem banco, sem processo daemon.

Fluxo:
  1. `cofre init`    -> gera par de chaves age (uma vez, por operador/maquina).
  2. `cofre encrypt` -> cifra um .env de trabalho em .env.enc (seguro pra
     versionar/compartilhar; a chave privada NUNCA sai da maquina do operador).
  3. `cofre decrypt` -> decifra .env.enc de volta a .env (usado logo antes do
     `docker compose up`; o .env plano fica de fora do git via .gitignore).
  4. `cofre up`      -> decifra e sobe o stack via `docker compose up -d`
     com --env-file apontando pro .env decifrado (integracao real, nao so
     leitura de variavel).

Nenhum metodo aqui fabrica sucesso: toda chamada a `sops`/`age-keygen`
ausente do PATH retorna Result.fail com codigo especifico, nunca lanca
excecao solta nem finge que funcionou.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from typing import Any, Callable, Dict, List, Optional

try:
    from core.result import Result
except ImportError:
    from src.core.result import Result


def _executor_padrao(comando: List[str], **kwargs: Any) -> subprocess.CompletedProcess:
    return subprocess.run(comando, capture_output=True, text=True, encoding="utf-8", errors="replace", **kwargs)


class CofreCredenciais:
    """Cofre local de credenciais (NIH #18/#29): wrapper determinístico sobre sops+age."""

    def __init__(
        self,
        sops_bin: Optional[str] = None,
        age_keygen_bin: Optional[str] = None,
        executor_fn: Optional[Callable[..., subprocess.CompletedProcess]] = None,
        dry_run: bool = False,
    ):
        self._sops_bin_explicito = sops_bin
        self._age_keygen_bin_explicito = age_keygen_bin
        self.executor = executor_fn or _executor_padrao
        self.dry_run = dry_run

    def _resolver_binario(self, nome: str, explicito: Optional[str]) -> Optional[str]:
        if explicito:
            return explicito
        return shutil.which(nome)

    def _sops(self) -> Optional[str]:
        return self._resolver_binario("sops", self._sops_bin_explicito)

    def _age_keygen(self) -> Optional[str]:
        return self._resolver_binario("age-keygen", self._age_keygen_bin_explicito)

    def _executar(self, comando: List[str], **kwargs: Any) -> Result[subprocess.CompletedProcess]:
        """Executa `comando` capturando FileNotFoundError/OSError como falha monadica
        (binario informado explicitamente mas inexistente no disco/PATH), em vez de
        deixar a excecao vazar para fora do cofre."""
        try:
            return Result.ok(self.executor(comando, **kwargs))
        except OSError as exc:
            return Result.fail(
                erro=f"Nao foi possivel executar '{comando[0]}': {exc}",
                codigo="BINARIO_NAO_ENCONTRADO",
                detalhes={"comando": comando},
            )

    # -------------------------------------------------------------------
    # 1. Geracao de chave age
    # -------------------------------------------------------------------
    def gerar_chave_age(self, caminho_chave: str) -> Result[Dict[str, str]]:
        """Gera um par de chaves age (X25519) real via `age-keygen -o <arquivo>`.

        Retorna a chave publica (age1...) extraida da saida do binario e o
        caminho do arquivo com a chave privada (AGE-SECRET-KEY-1...), que
        NUNCA deve ser commitado.
        """
        binario = self._age_keygen()
        if not binario:
            return Result.fail(
                erro="Binario 'age-keygen' nao encontrado no PATH. Instale age "
                     "(https://github.com/FiloSottile/age) antes de gerar o cofre.",
                codigo="AGE_NAO_INSTALADO",
            )

        if os.path.exists(caminho_chave):
            return Result.fail(
                erro=f"Ja existe um arquivo de chave em {caminho_chave} — "
                     "gerar por cima sobrescreveria uma chave existente e "
                     "tornaria .env.enc ja cifrados irrecuperaveis.",
                codigo="CHAVE_JA_EXISTE",
                detalhes={"caminho_chave": caminho_chave},
            )

        os.makedirs(os.path.dirname(os.path.abspath(caminho_chave)) or ".", exist_ok=True)
        res_proc = self._executar([binario, "-o", caminho_chave])
        if not res_proc.sucesso:
            return Result.fail(
                erro=f"Binario age-keygen informado ('{binario}') nao pode ser executado: {res_proc.erro}",
                codigo="AGE_NAO_INSTALADO",
                detalhes=res_proc.detalhes,
            )
        processo = res_proc.valor
        if processo.returncode != 0:
            return Result.fail(
                erro=f"Falha ao gerar chave age: {processo.stderr.strip()}",
                codigo="ERRO_GERACAO_CHAVE",
                detalhes={"stderr": processo.stderr},
            )

        chave_publica = None
        for linha in processo.stderr.splitlines():
            if linha.strip().lower().startswith("public key:"):
                chave_publica = linha.split(":", 1)[1].strip()
                break
        if chave_publica is None and os.path.exists(caminho_chave):
            # Fallback: age-keygen tambem grava "# public key: age1..." como
            # comentario dentro do proprio arquivo de chave.
            with open(caminho_chave, "r", encoding="utf-8") as f:
                for linha in f:
                    if linha.strip().lower().startswith("# public key:"):
                        chave_publica = linha.split(":", 1)[1].strip()
                        break

        if not chave_publica:
            return Result.fail(
                erro="Chave privada gerada, mas nao foi possivel extrair a chave publica da saida.",
                codigo="CHAVE_PUBLICA_NAO_EXTRAIDA",
                detalhes={"stderr": processo.stderr},
            )

        return Result.ok({"chave_publica": chave_publica, "caminho_chave": os.path.abspath(caminho_chave)})

    # -------------------------------------------------------------------
    # 2. Configuracao .sops.yaml
    # -------------------------------------------------------------------
    def gerar_sops_config(
        self,
        caminho_config: str,
        chaves_publicas: List[str],
        padrao_arquivo: str = r"templates[\\/]infra[\\/].*\.env$",
    ) -> Result[str]:
        """Escreve .sops.yaml com creation_rules apontando pras chaves age publicas.

        Conteudo e 100% publico (chave publica age nao e segredo) — seguro
        pra versionar. A chave PRIVADA nunca entra neste arquivo.

        O ``path_regex`` casa com o arquivo .env de ENTRADA (nao o .env.enc de
        saida): o sops resolve o caminho a ser cifrado para caminho absoluto e
        casa a regex contra ele. Por isso o separador de diretorio e agnostico
        (``[\\\\/]``) — o default antigo (``templates/infra/.*\\.env\\.enc$``)
        nunca casava no Windows (barra invertida) e nem com o input (.env).
        """
        if not chaves_publicas:
            return Result.fail(
                erro="Nenhuma chave publica age informada para o .sops.yaml",
                codigo="CHAVES_PUBLICAS_VAZIAS",
            )
        for chave in chaves_publicas:
            if not chave.startswith("age1"):
                return Result.fail(
                    erro=f"Chave publica invalida (esperado prefixo 'age1'): {chave}",
                    codigo="CHAVE_PUBLICA_INVALIDA",
                    detalhes={"chave": chave},
                )

        recipients = ",".join(chaves_publicas)
        conteudo = (
            "# AIDD-Ops — Cofre de Credenciais (NIH #18/#29: sops + age)\n"
            "# Gerado por core/cofre_credenciais.py. Contem apenas chave(s)\n"
            "# PUBLICA(S) age — seguro versionar. A chave privada correspondente\n"
            "# fica fora do repositorio (ver README, secao Cofre de Credenciais).\n"
            "creation_rules:\n"
            f"  - path_regex: '{padrao_arquivo}'\n"
            f"    age: '{recipients}'\n"
        )
        os.makedirs(os.path.dirname(os.path.abspath(caminho_config)) or ".", exist_ok=True)
        with open(caminho_config, "w", encoding="utf-8", newline="\n") as f:
            f.write(conteudo)
        return Result.ok(os.path.abspath(caminho_config))

    # -------------------------------------------------------------------
    # 3. Cifrar / decifrar .env
    # -------------------------------------------------------------------
    def _localizar_sops_config(self, caminho_input: str) -> Optional[str]:
        """Localiza o .sops.yaml para cifragem de forma deterministica.

        O sops so descobre `.sops.yaml` a partir do cwd (e ancestrais) — nao
        a partir do diretorio do arquivo cifrado. Como o padrao do ecossistema
        e executar o CLI do cofre do diretorio `tools/aidd-ops` (que nao e o
        mesmo do .env sob `templates/infra/...`), procuramos primeiro subindo
        do arquivo de entrada e, como fallback, do cwd — e passamos o caminho
        explícito via `--config` para eliminar a dependencia de cwd.
        """
        diretorios = [os.path.dirname(os.path.abspath(caminho_input)), os.getcwd()]
        visitados: set = set()
        for inicio in diretorios:
            dir_atual = os.path.abspath(inicio)
            while dir_atual not in visitados:
                visitados.add(dir_atual)
                candidato = os.path.join(dir_atual, ".sops.yaml")
                if os.path.isfile(candidato):
                    return candidato
                pai = os.path.dirname(dir_atual)
                if pai == dir_atual:
                    break
                dir_atual = pai
        return None

    def cifrar_env(
        self,
        caminho_env_plano: str,
        caminho_saida_enc: str,
        chave_publica: Optional[str] = None,
    ) -> Result[str]:
        """Cifra um .env de trabalho em .env.enc real via `sops --encrypt`.

        Se `chave_publica` for informada, e passada explicitamente via
        `--age` (uso avulso/teste) junto com um `.sops.yaml` temporario
        catch-all via `--config`. A config temporaria evita o erro real
        "no matching creation rules found" que o sops dispara quando existe
        um `.sops.yaml` descoberto (cwd/ancestrais) cujo path_regex nao casa
        com o arquivo sendo cifrado. Caso contrario, sops resolve o(s)
        destinatario(s) a partir do .sops.yaml mais proximo (uso normal).
        """
        binario = self._sops()
        if not binario:
            return Result.fail(
                erro="Binario 'sops' nao encontrado no PATH. Instale sops "
                     "(https://github.com/getsops/sops) antes de cifrar o cofre.",
                codigo="SOPS_NAO_INSTALADO",
            )
        if self._sops_bin_explicito and not (
            shutil.which(self._sops_bin_explicito) or os.path.isfile(self._sops_bin_explicito)
        ):
            return Result.fail(
                erro=f"Binario 'sops' informado explicitamente ('{self._sops_bin_explicito}') "
                     "nao existe no disco nem no PATH.",
                codigo="SOPS_NAO_INSTALADO",
                detalhes={"binario": self._sops_bin_explicito},
            )
        if not os.path.isfile(caminho_env_plano):
            return Result.fail(
                erro=f"Arquivo .env de origem nao encontrado: {caminho_env_plano}",
                codigo="ENV_ORIGEM_NAO_ENCONTRADO",
                detalhes={"caminho": caminho_env_plano},
            )

        comando = [binario, "--encrypt", "--input-type", "dotenv", "--output-type", "dotenv"]
        config_temporaria = None
        try:
            if chave_publica:
                comando += ["--age", chave_publica]
                fd, config_temporaria = tempfile.mkstemp(suffix=".sops.yaml", prefix="aidd-cofre-")
                with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                    f.write(
                        "# Config temporaria catch-all (uso avulso/teste com --age explicito).\n"
                        "creation_rules:\n"
                        "  - path_regex: '.*'\n"
                        f"    age: '{chave_publica}'\n"
                    )
                comando += ["--config", config_temporaria]
            else:
                config_opcoes = self._localizar_sops_config(caminho_env_plano)
                if config_opcoes is None:
                    return Result.fail(
                        erro="Nenhum .sops.yaml encontrado nem perto do .env nem no diretorio atual. "
                             "Rode 'pipeline_ops.py cofre init' antes de cifrar.",
                        codigo="SOPS_CONFIG_NAO_ENCONTRADO",
                        detalhes={"caminho_env": os.path.abspath(caminho_env_plano)},
                    )
                comando += ["--config", config_opcoes]
            comando.append(caminho_env_plano)

            res_proc = self._executar(comando)
            if not res_proc.sucesso:
                return Result.fail(
                    erro=f"Binario sops informado ('{binario}') nao pode ser executado: {res_proc.erro}",
                    codigo="SOPS_NAO_INSTALADO",
                    detalhes=res_proc.detalhes,
                )
            processo = res_proc.valor
            if processo.returncode != 0:
                return Result.fail(
                    erro=f"Falha ao cifrar {caminho_env_plano}: {processo.stderr.strip()}",
                    codigo="ERRO_CIFRAGEM",
                    detalhes={"stderr": processo.stderr, "comando": comando},
                )

            os.makedirs(os.path.dirname(os.path.abspath(caminho_saida_enc)) or ".", exist_ok=True)
            with open(caminho_saida_enc, "w", encoding="utf-8", newline="\n") as f:
                f.write(processo.stdout)
            return Result.ok(os.path.abspath(caminho_saida_enc))
        finally:
            if config_temporaria and os.path.exists(config_temporaria):
                try:
                    os.remove(config_temporaria)
                except OSError:
                    pass

    def decifrar_env(
        self,
        caminho_env_enc: str,
        caminho_saida_env: str,
        arquivo_chave_privada: Optional[str] = None,
    ) -> Result[str]:
        """Decifra um .env.enc real via `sops --decrypt` para uso imediato pelo docker compose."""
        binario = self._sops()
        if not binario:
            return Result.fail(
                erro="Binario 'sops' nao encontrado no PATH. Instale sops "
                     "(https://github.com/getsops/sops) antes de decifrar o cofre.",
                codigo="SOPS_NAO_INSTALADO",
            )
        if not os.path.isfile(caminho_env_enc):
            return Result.fail(
                erro=f"Arquivo .env.enc nao encontrado: {caminho_env_enc}",
                codigo="ENV_ENC_NAO_ENCONTRADO",
                detalhes={"caminho": caminho_env_enc},
            )

        ambiente = None
        if arquivo_chave_privada:
            if not os.path.isfile(arquivo_chave_privada):
                return Result.fail(
                    erro=f"Arquivo de chave privada age nao encontrado: {arquivo_chave_privada}",
                    codigo="CHAVE_PRIVADA_NAO_ENCONTRADA",
                    detalhes={"caminho": arquivo_chave_privada},
                )
            ambiente = dict(os.environ)
            ambiente["SOPS_AGE_KEY_FILE"] = os.path.abspath(arquivo_chave_privada)

        comando = [binario, "--decrypt", "--input-type", "dotenv", "--output-type", "dotenv", caminho_env_enc]
        res_proc = self._executar(comando, env=ambiente) if ambiente else self._executar(comando)
        if not res_proc.sucesso:
            return Result.fail(
                erro=f"Binario sops informado ('{binario}') nao pode ser executado: {res_proc.erro}",
                codigo="SOPS_NAO_INSTALADO",
                detalhes=res_proc.detalhes,
            )
        processo = res_proc.valor
        if processo.returncode != 0:
            return Result.fail(
                erro=f"Falha ao decifrar {caminho_env_enc} — verifique se a chave privada age "
                     f"correta esta disponivel (SOPS_AGE_KEY_FILE): {processo.stderr.strip()}",
                codigo="ERRO_DECIFRAGEM",
                detalhes={"stderr": processo.stderr, "comando": comando},
            )

        os.makedirs(os.path.dirname(os.path.abspath(caminho_saida_env)) or ".", exist_ok=True)
        with open(caminho_saida_env, "w", encoding="utf-8", newline="\n") as f:
            f.write(processo.stdout)
        return Result.ok(os.path.abspath(caminho_saida_env))

    # -------------------------------------------------------------------
    # 4. Integracao com docker compose
    # -------------------------------------------------------------------
    def montar_comando_docker_compose_up(
        self,
        caminho_compose: str,
        caminho_env: str,
        detach: bool = True,
    ) -> List[str]:
        """Monta o comando real do `docker compose up` consumindo o .env decifrado."""
        comando = ["docker", "compose", "-f", caminho_compose, "--env-file", caminho_env, "up"]
        if detach:
            comando.append("-d")
        return comando

    def subir_servico_com_cofre(
        self,
        diretorio_servico: str,
        arquivo_chave_privada: Optional[str] = None,
        nome_compose: str = "docker-compose.yml",
        nome_env_enc: str = ".env.enc",
        nome_env: str = ".env",
    ) -> Result[Dict[str, Any]]:
        """Decifra o .env.enc do servico e sobe o docker compose correspondente.

        Fluxo completo: .env.enc -> decrypt real -> docker compose up -d
        --env-file <.env decifrado>. Em dry_run, o comando e montado e
        retornado sem executar (usado em teste/CI sem daemon Docker).
        """
        caminho_enc = os.path.join(diretorio_servico, nome_env_enc)
        caminho_env = os.path.join(diretorio_servico, nome_env)
        caminho_compose = os.path.join(diretorio_servico, nome_compose)

        if not os.path.isfile(caminho_compose):
            return Result.fail(
                erro=f"docker-compose.yml nao encontrado em {diretorio_servico}",
                codigo="COMPOSE_NAO_ENCONTRADO",
                detalhes={"caminho": caminho_compose},
            )

        res_decrypt = self.decifrar_env(caminho_enc, caminho_env, arquivo_chave_privada)
        if not res_decrypt.sucesso:
            return res_decrypt

        comando = self.montar_comando_docker_compose_up(caminho_compose, caminho_env)

        if self.dry_run:
            return Result.ok({"comando": comando, "env_decifrado": res_decrypt.valor, "executado": False})

        res_proc = self._executar(comando)
        if not res_proc.sucesso:
            return Result.fail(
                erro=f"Binario 'docker' nao encontrado no PATH: {res_proc.erro}",
                codigo="DOCKER_NAO_INSTALADO",
                detalhes=res_proc.detalhes,
            )
        processo = res_proc.valor
        if processo.returncode != 0:
            return Result.fail(
                erro=f"docker compose up falhou para {diretorio_servico}: {processo.stderr.strip()}",
                codigo="ERRO_DOCKER_COMPOSE_UP",
                detalhes={"stderr": processo.stderr, "comando": comando},
            )
        return Result.ok({"comando": comando, "env_decifrado": res_decrypt.valor, "executado": True})
