# -*- coding: utf-8 -*-
"""
G_FACTORY_COMPOSE — Valida docker-compose.yml gerado pelo factory.

Verifica:
  1. Sintaxe YAML valida
  2. Todos os services tem healthcheck
  3. Todos os services estao na rede aidd_internal
  4. Nenhuma porta host duplicada
  5. Todos os services com DependsOn apontam para services existentes
"""
import sys
import os

_FACTORY_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "src"))

import yaml


def _validar_compose(caminho: str) -> list:
    """Valida um compose file. Retorna lista de problemas."""
    problemas = []

    if not os.path.isfile(caminho):
        return [f"Arquivo nao encontrado: {caminho}"]

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        return [f"YAML invalido: {exc}"]

    if not dados or "services" not in dados:
        return ["Compose sem secao 'services'"]

    services = dados["services"]
    nomes_services = set(services.keys())
    portas_host = {}

    for nome, svc in services.items():
        # Healthcheck
        if "healthcheck" not in svc:
            problemas.append(f"Service '{nome}' sem healthcheck")

        # Rede
        networks = svc.get("networks", [])
        if "aidd_internal" not in networks:
            problemas.append(f"Service '{nome}' nao conectado a rede aidd_internal")

        # Portas
        for port_str in svc.get("ports", []):
            port_str = str(port_str)
            host_port = port_str.split(":")[0] if ":" in port_str else port_str
            if host_port in portas_host:
                problemas.append(f"Porta host {host_port} duplicada: {nome} e {portas_host[host_port]}")
            portas_host[host_port] = nome

        # DependsOn
        depends = svc.get("depends_on", {})
        if isinstance(depends, dict):
            for dep in depends:
                if dep not in nomes_services:
                    problemas.append(f"Service '{nome}' depende de '{dep}' que nao existe")
        elif isinstance(depends, list):
            for dep in depends:
                dep_name = dep if isinstance(dep, str) else dep.get("service", "")
                if dep_name and dep_name not in nomes_services:
                    problemas.append(f"Service '{nome}' depende de '{dep_name}' que nao existe")

    return problemas


def executar(caminho_compose: str = None) -> int:
    """Executa o gate."""
    print("=" * 72)
    print(" [G_FACTORY_COMPOSE] Validacao de docker-compose.yml")
    print("=" * 72)

    if caminho_compose is None:
        # Buscar compose padrao
        caminho_compose = os.path.join(_FACTORY_ROOT, "output", "docker-compose.yml")
    elif os.path.isdir(caminho_compose):
        caminho_compose = os.path.join(caminho_compose, "docker-compose.yml")

    problemas = _validar_compose(caminho_compose)

    if problemas:
        print(f"\n[FALHA] {len(problemas)} problema(s):")
        for p in problemas:
            print(f"  - {p}")
        return 1

    print(f"\n[SUCESSO] {caminho_compose} validado.")
    return 0


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(executar(path))
