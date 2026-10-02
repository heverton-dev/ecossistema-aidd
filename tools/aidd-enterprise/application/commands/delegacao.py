# -*- coding: utf-8 -*-
"""Delegação dos comandos de construção ao dono (fronteiras-ferramentas ciclo-01, Ticket 18 / D1).

O aidd-enterprise é só blindagem: injetor, selo SHA-256, COMPONENT-REGISTRY,
auditoria e drift. Compor suíte, provisionar projeto, gerar fatia, medir,
exportar front-end e infraestrutura são do aidd-master (que por sua vez entrega
a infra ao aidd-ops). Os comandos continuam na CLI do enterprise por
compatibilidade, mas rodam a CLI do dono com os mesmos argumentos, no mesmo
diretório de trabalho, e devolvem o exit code dele. As cópias antigas em
scripts/ e templates/ ficam no disco até a remoção com o usuário (Ticket 19).
"""

import os
import subprocess
import sys

_ENTERPRISE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TOOLS_DIR = os.path.dirname(_ENTERPRISE_DIR)

DONO_CONSTRUCAO = "aidd-master"


def cli_do_dono(ferramenta: str = DONO_CONSTRUCAO) -> str:
    """Caminho da CLI `scripts/aidd.py` da ferramenta dona do comando."""
    return os.path.join(_TOOLS_DIR, ferramenta, "scripts", "aidd.py")


def delegar(argv, ferramenta: str = DONO_CONSTRUCAO) -> int:
    """Roda `<ferramenta>/scripts/aidd.py <argv...>` e devolve o exit code."""
    argv = [str(a) for a in argv]
    cli = cli_do_dono(ferramenta)
    if not os.path.isfile(cli):
        print(f"[ERRO] CLI do dono não encontrada: {cli}")
        return 1
    print(f"[DELEGADO] aidd-enterprise -> {ferramenta}: {argv[0] if argv else ''}", flush=True)
    env = os.environ.copy()
    raiz_dono = os.path.dirname(os.path.dirname(cli))
    env["PYTHONPATH"] = os.pathsep.join(p for p in (raiz_dono, env.get("PYTHONPATH", "")) if p)
    env["PYTHONIOENCODING"] = "utf-8"
    # A saída do dono passa pelo sys.stdout do enterprise, linha a linha (ao vivo e capturável).
    proc = subprocess.Popen(
        [sys.executable, cli, *argv], cwd=os.getcwd(), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
    )
    for linha in proc.stdout:
        sys.stdout.write(linha)
        sys.stdout.flush()
    proc.stdout.close()
    return proc.wait()


def delegar_ou_sair(argv, ferramenta: str = DONO_CONSTRUCAO) -> None:
    """Delega e encerra com o exit code do dono quando ele falha (contrato dos Use Cases)."""
    codigo = delegar(argv, ferramenta)
    if codigo != 0:
        sys.exit(codigo)
