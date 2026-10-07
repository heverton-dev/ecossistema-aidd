# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD OPS — COMPOSE PRE-FLIGHT & OCI SYNTACTIC VALIDATOR
=============================================================================
Realiza pre-voo de linting e validacao de estrutura em manifests Docker Compose
antes do deploy em VPS, identificando conflitos de porta, imagens nao pinadas
e configuracoes inseguras sem intervenção de modelo de linguagem.
"""

import os
from typing import Any, Dict, List, Tuple
import yaml


class ComposePreflightValidator:
    """Valida deterministicamente arquivos docker-compose.yml."""

    @staticmethod
    def validate_compose_content(yaml_content: str) -> Tuple[bool, List[str]]:
        """Analisa o conteudo YAML de um compose e aponta violacoes de boas praticas."""
        errors = []
        try:
            data = yaml.safe_load(yaml_content)
        except Exception as e:
            return False, [f"Sintaxe YAML invalida: {str(e)}"]

        if not isinstance(data, dict):
            return False, ["Arquivo Compose deve ser um mapeamento de chave-valor."]

        services = data.get("services")
        if not services or not isinstance(services, dict):
            return False, ["Secao 'services' ausente ou vazia no Compose."]

        used_ports: Dict[str, str] = {}

        for sname, sdef in services.items():
            if not isinstance(sdef, dict):
                errors.append(f"Servico '{sname}' deve ser um dicionario.")
                continue

            # Checar imagem pinada
            image = sdef.get("image", "")
            if image and ":" not in image:
                errors.append(f"Servico '{sname}': imagem '{image}' sem tag explicita (risco de drift).")

            # Checar conflito de portas
            ports = sdef.get("ports", [])
            for p in ports:
                p_str = str(p)
                host_port = p_str.split(":")[0] if ":" in p_str else p_str
                if host_port in used_ports:
                    errors.append(f"Conflito de porta host '{host_port}': usado por '{used_ports[host_port]}' e '{sname}'.")
                else:
                    used_ports[host_port] = sname

        return (len(errors) == 0), errors
