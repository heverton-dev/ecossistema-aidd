import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from quadro_leitor import _pid_vivo, QuadroLeitor
except ImportError:
    from scripts.quadro_leitor import _pid_vivo, QuadroLeitor

def verificar_alertas(raiz_aidd: Optional[Path] = None, raiz_repo: Optional[Path] = None) -> List[Dict[str, str]]:
    raiz_a = raiz_aidd or Path(os.environ.get("AIDD_HOME", Path.home() / ".aidd"))
    repo = raiz_repo or Path(__file__).resolve().parent.parent
    alertas = []

    leitor = QuadroLeitor(raiz_aidd=raiz_a, raiz_repo=repo)
    execucoes = leitor.listar_execucoes(incluir_arquivo=False)

    alvos_vivos = {}
    pids_vivos = set()

    for ex in execucoes:
        run_id = ex.get("run_id", "desconhecido")
        st = ex.get("status")
        pid = ex.get("processo", {}).get("pid")
        chave = ex.get("chave")

        # Alerta 1: Processo morto ou interrompido
        if (st == "interrompido" and pid and not _pid_vivo(pid)) or (st == "executando" and pid and not _pid_vivo(pid)):
            alertas.append({
                "tipo": "pid_morto",
                "mensagem": f"Execucao '{run_id}' esta marcada como executando mas o PID {pid} nao esta ativo.",
                "run_id": run_id
            })
        elif st == "executando" and pid:
            pids_vivos.add(pid)
            # Alerta 3: Conflito de alvo em duas execucoes vivas
            if chave:
                if chave in alvos_vivos:
                    alertas.append({
                        "tipo": "conflito_alvo",
                        "mensagem": f"Alvo '{chave}' em execucao concorrente simultanea em '{run_id}' e '{alvos_vivos[chave]}'.",
                        "chave": chave
                    })
                else:
                    alvos_vivos[chave] = run_id

    # Alerta 2: Worktrees orfas no diretorio pai
    pasta_pai = repo.parent
    if pasta_pai.exists():
        for wt in pasta_pai.glob("worktrees_*"):
            if wt.is_dir():
                # Verificar se pertence a algum ciclo vivo
                nome_wt = wt.name[len("worktrees_"):]
                tem_dono_vivo = any(ex.get("chave") == nome_wt and ex.get("status") == "executando" for ex in execucoes)
                if not tem_dono_vivo:
                    alertas.append({
                        "tipo": "worktree_orfa",
                        "mensagem": f"Pasta de worktree orfa '{wt.name}' sem execucao viva associada.",
                        "caminho": str(wt)
                    })

    return alertas
