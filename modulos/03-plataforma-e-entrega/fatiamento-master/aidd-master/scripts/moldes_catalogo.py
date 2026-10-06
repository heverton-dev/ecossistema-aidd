# -*- coding: utf-8 -*-
"""Moldes de templates/core e templates/v2 que viraram peça do almoxarifado.

Bloco 4 do fronteiras-ferramentas (Ticket 19): as cópias dos moldes do Quarteto e
de infra saíram de templates/; quem monta projeto (compose_suite, provision_project)
pede o molde aqui. Molde que continua local (só do aidd-master) é devolvido
do próprio templates/.
"""
from pathlib import Path

def _achar_raiz_repo(inicio: Path) -> Path:
    curr = inicio
    while curr and curr.parent != curr:
        if (curr / "ecossistema.py").is_file():
            return curr
        curr = curr.parent
    return inicio.parents[3]


RAIZ_ECOSSISTEMA = _achar_raiz_repo(Path(__file__).resolve().parent)
ALMOXARIFADO = RAIZ_ECOSSISTEMA / "componentes" / "compartilhado"

PECA_POR_MOLDE = {
    "Dockerfile": "moldes/infra/Dockerfile",
    "deploy.sh": "moldes/infra/deploy.sh",
    "docker-compose.yml": "moldes/infra/docker-compose.yml",
    "nginx": "moldes/infra/nginx",
    "docs.html": "moldes/quarteto/docs.html",
    "mcp_server.py": "moldes/quarteto/mcp_server.py",
    "openapi.py": "moldes/quarteto/openapi.py",
    "webhooks.py": "moldes/quarteto/webhooks.py",
    "mcp_studio.html": "moldes/quarteto/variantes/templates/mcp_studio.html",
    "swagger.html": "moldes/quarteto/variantes/templates/swagger.html",
    "webhook_studio.html": "moldes/quarteto/variantes/templates/webhook_studio.html",
}


def molde(pasta_templates: str, nome: str) -> str:
    """Caminho do molde `nome`: o de templates/ se ainda existe, senão a peça do almoxarifado."""
    local = Path(pasta_templates) / nome
    if local.exists():
        return str(local)
    if nome in PECA_POR_MOLDE:
        return str(ALMOXARIFADO / PECA_POR_MOLDE[nome])
    peca_kernel = ALMOXARIFADO / "src-core" / nome
    if peca_kernel.exists():
        return str(peca_kernel)
    local_src_core = RAIZ_ECOSSISTEMA / "tools" / "aidd-master" / "src" / "core" / nome
    if local_src_core.exists():
        return str(local_src_core)
    v2_fallback = RAIZ_ECOSSISTEMA / "tools" / "aidd-master" / "templates" / "v2" / nome
    if v2_fallback.exists():
        return str(v2_fallback)
    return str(local)


# Gates que todo projeto montado recebe em scripts/gates/ (antes em templates/gates/).
GATES_DE_PROJETO = (
    "G_ARQUITETURA.py", "G_CHAOS.py", "G_CONTRACTS.py", "G_ESTRUTURA.py", "G_HARNESS_COMPAT.py",
    "G_PERFORMANCE.py", "G_QUALIDADE.py", "G_SEGREDOS.py", "G_SEGURANCA.py", "G_TESTES.py",
)


def gates_de_projeto(pasta_gates: str) -> dict:
    """{nome: caminho} dos gates do projeto: os do almoxarifado mais os que ainda são só locais."""
    gates = {nome: str(ALMOXARIFADO / "gates" / nome) for nome in GATES_DE_PROJETO}
    local = Path(pasta_gates)
    if local.is_dir():
        gates.update({g.name: str(g) for g in local.glob("*.py")})
    return gates
