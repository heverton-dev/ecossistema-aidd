# -*- coding: utf-8 -*-
"""
Testes determinísticos do fix NIH #16 — Traefik subutilizado.

Garante que Twenty/Chatwoot/Cal.com passam a ser roteados via labels Traefik
(pelo reverse proxy na rede aidd_internal) e que nenhuma porta de host 3000
é publicada por esses serviços — eliminando a colisão cross-compose que
existia quando as 3 ferramentas subiam juntas (todas com default :3000).

100% estático (sem subir contêineres) e sem dados fabricados: lê os templates
reais sob templates/infra/.
"""

import os
import re
from typing import Dict, List, Set

TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INFRA_DIR = os.path.join(TOOL_ROOT, "templates", "infra")


def _conteudo_compose(bloco: str) -> str:
    caminho = os.path.join(INFRA_DIR, bloco, "docker-compose.yml")
    assert os.path.isfile(caminho), f"docker-compose.yml ausente em {bloco}/"
    with open(caminho, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _separar_servicos(conteudo: str) -> Dict[str, List[str]]:
    """Separa o conteúdo por nome de serviço (blocos em nível 2 do YAML)."""
    servicos: Dict[str, List[str]] = {}
    servico_atual = None
    for linha in conteudo.splitlines():
        strip_l = linha.strip()
        if not strip_l or strip_l.startswith("#"):
            continue
        match_srv = re.match(r"^([a-zA-Z0-9_-]+):\s*$", strip_l)
        indent = len(linha) - len(linha.lstrip())
        if match_srv and indent == 2:
            servico_atual = match_srv.group(1)
            servicos[servico_atual] = []
            continue
        if servico_atual and indent > 2:
            servicos[servico_atual].append(strip_l)
    return servicos


def _portas_host_publicadas(linhas_servico: List[str]) -> Set[str]:
    """Extrai portas de host publicadas (default resolvido) de um serviço."""
    portas: Set[str] = set()
    em_ports = False
    for linha in linhas_servico:
        if re.match(r"^ports:\s*$", linha):
            em_ports = True
            continue
        if em_ports:
            if not linha.startswith("-"):
                em_ports = False
                continue
            item = linha.lstrip("- ").strip("'\"")
            if ":" in item:
                porta_host = item.rsplit(":", 1)[0].strip()
                match_def = re.search(r":-([0-9]+)", porta_host)
                portas.add(match_def.group(1) if match_def else porta_host)
    return portas


def _labels_traefik(linhas_servico: List[str]) -> List[str]:
    """Extrai as linhas de label traefik.* de um serviço."""
    labels = []
    em_labels = False
    for linha in linhas_servico:
        if re.match(r"^labels:\s*$", linha):
            em_labels = True
            continue
        if em_labels:
            if not linha.startswith("-"):
                em_labels = False
                continue
            item = linha.lstrip("- ").strip("'\"")
            if item.startswith("traefik."):
                labels.append(item)
    return labels


class TestRoteamentoTraefikNih16:

    def test_servicos_web_nao_publicam_porta_3000_no_host(self):
        servico_por_bloco = {
            "twenty": ["twenty-server", "twenty-front"],
            "chatwoot": ["chatwoot-rails"],
            "calcom": ["calcom-server"],
        }
        for bloco, nomes in servico_por_bloco.items():
            servicos = _separar_servicos(_conteudo_compose(bloco))
            for nome_servico in nomes:
                bloco_servico = servicos.get(nome_servico)
                assert bloco_servico is not None, f"{nome_servico} não existe em {bloco}/"
                portas = _portas_host_publicadas(bloco_servico)
                assert "3000" not in portas, (
                    f"{bloco}/{nome_servico} ainda publica porta 3000 no host"
                )

    def test_sem_colisao_cross_compose_de_porta_host(self):
        publicadas: Dict[str, str] = {}
        for bloco in sorted(os.listdir(INFRA_DIR)):
            caminho = os.path.join(INFRA_DIR, bloco, "docker-compose.yml")
            if not os.path.isfile(caminho):
                continue
            servicos = _separar_servicos(_conteudo_compose(bloco))
            for nome_servico, linhas in servicos.items():
                for porta in _portas_host_publicadas(linhas):
                    origem = f"{bloco}/{nome_servico}:{porta}"
                    assert porta not in publicadas, (
                        f"Colisão de porta de host: {origem} == {publicadas[porta]}"
                    )
                    publicadas[porta] = origem

    def test_todos_servicos_web_tem_labels_traefik_completas(self):
        servicos_esperados = [
            ("twenty", "twenty-server", "twenty-api", 3000),
            ("twenty", "twenty-front", "twenty-ui", 3001),
            ("chatwoot", "chatwoot-rails", "chatwoot", 3000),
            ("calcom", "calcom-server", "calcom", 3000),
        ]
        for bloco, nome_servico, router_servico, porta_interna in servicos_esperados:
            servicos = _separar_servicos(_conteudo_compose(bloco))
            labels = "\n".join(_labels_traefik(servicos[nome_servico]))

            assert 'traefik.enable=true' in labels
            assert "traefik.http.routers" in labels and "rule=Host(`" in labels
            assert "entrypoints=websecure" in labels
            assert "tls.certresolver=letsencrypt" in labels
            assert (
                f"traefik.http.services.{router_servico}.loadbalancer.server.port={porta_interna}"
                in labels
            ), f"LoadBalancer de {bloco}/{nome_servico} deve apontar para a porta interna {porta_interna}"

    def test_hosts_traefik_declarados_no_env_example(self):
        esperados = {
            "twenty": {"TWENTY_SERVER_HOST", "TWENTY_FRONT_HOST"},
            "chatwoot": {"CHATWOOT_HOST"},
            "calcom": {"CALCOM_HOST"},
        }
        for bloco, variaveis in esperados.items():
            caminho_env = os.path.join(INFRA_DIR, bloco, ".env.example")
            assert os.path.isfile(caminho_env), f".env.example ausente em {bloco}/"
            with open(caminho_env, "r", encoding="utf-8", errors="replace") as f:
                declaradas: Set[str] = set()
                for linha in f:
                    match_var = re.match(r"^([A-Z0-9_]+)\s*=", linha)
                    if match_var:
                        declaradas.add(match_var.group(1))
            faltantes = variaveis - declaradas
            assert not faltantes, (
                f"{bloco}/.env.example não declara: {sorted(faltantes)}"
            )