import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import threading
from pathlib import Path

def run_cmd(cmd, cwd=None, exit_on_fail=True, input_data=None):
    print(f"[ORCHESTRATOR 4F] Executando em TTY Efêmero: {cmd}")
    env = os.environ.copy()
    
    # Monta o pipe nativo do windows
    comando = cmd
    if input_data:
        comando = f'type "{input_data}" | {cmd}'
        
    # Injeção estrutural: Criação de TTY Físico (Nova Janela CMD)
    # Isso resolve a Síndrome do Node.js IsTTY falso.
    if sys.platform == "win32":
        # /WAIT bloqueia o python até a janela fechar
        # cmd /c fecha o popup quando o processo concluir
        # O titulo da janela leva a marcação do Pipeline
        comando_tty = f'start "AIDD TTY Efemero - Pipeline 4F" /WAIT cmd /c "{comando}"'
    else:
        # Fallback linux/mac
        comando_tty = comando

    print(f"[TELEMETRIA] Aguardando janela efêmera TTY concluir a fase... (veja o pop-up)")
    
    res = subprocess.run(
        comando_tty, shell=True, cwd=cwd, env=env
    )
    
    if res.returncode != 0 and exit_on_fail:
        print(f"[ORCHESTRATOR 4F] FALHA CRÍTICA. Exit {res.returncode}")
        sys.exit(res.returncode)
    return res

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.exists():
        print(f"Manifesto não encontrado: {manifest_path}")
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    pipeline_id = data.get("pipeline_id", "audit")
    fases = data.get("fases", [])
    repo_root = Path.cwd()
    worktrees_base = repo_root.parent / f"worktrees_{pipeline_id}"
    
    print(f"============================================================")
    print(f" PIPELINE 4F INICIADO: {pipeline_id}")
    print(f" Total de Fases: {len(fases)}")
    print(f" Worktrees geradas em: {worktrees_base}")
    print(f"============================================================")

    for i, fase in enumerate(fases, 1):
        nome = fase.get("nome", f"fase_{i}")
        comando = fase.get("comando_terminal")
        handoff = fase.get("output_handoff")
        
        print(f"\n---> INICIANDO FASE {i}: {nome}")
        
        wt_path = worktrees_base / nome
        branch = f"audit/{pipeline_id}/{nome}"
        
        if wt_path.exists():
            shutil.rmtree(wt_path, ignore_errors=True)
            run_cmd(f"git worktree remove --force {wt_path}", exit_on_fail=False)
        run_cmd(f"git branch -D {branch}", exit_on_fail=False)

        print(f"[+] Isolando Worktree...")
        run_cmd(f"git worktree add -b {branch} {wt_path}")
        
        print(f"[+] Lendo Input Prompt via nativo: {fase.get('input_prompt')}")
        input_file = repo_root / fase.get("input_prompt")
        
        if not input_file.exists():
            print(f"[-] AVISO: Prompt input não encontrado em {input_file}")
            
        print(f"[+] Acionando Agente ({fase.get('harness')} | {fase.get('model')})...")
        run_cmd(comando, cwd=wt_path, exit_on_fail=True, input_data=str(input_file).replace('/', '\\') if input_file.exists() else None)
        
        print(f"[+] Verificando Output Handoff...")
        handoff_file = wt_path / handoff
        if not handoff_file.exists():
            print(f"[-] FALHA: Output {handoff} não foi gerado na worktree.")
            sys.exit(1)
            
        print(f"[+] Handoff confirmado! Persistindo artefatos no worktree...")
        run_cmd("git add -A", cwd=wt_path)
        run_cmd(f"git commit -m \"chore(audit): finalizando {nome}\"", cwd=wt_path, exit_on_fail=False)
        
        print(f"[+] Descartando Worktree (Drop & Push to memory)...")
        run_cmd(f"git worktree remove --force {wt_path}")
        
        # A próxima fase vai partir dessa mesma branch ou da master?
        # Num fluxo cumulativo (Fase 1->2->3), todas devem alterar a mesma base sucessivamente.
        # Portanto, o pipeline linear puxa o branch anterior, faz merge ou continua.
        # Mas o usuário instruiu: "the next phase then audit and drop the next phase, drop the work tree and start your work and so successively until the end"
        # Para ser estritamente sequencial na mesma base de branch, fazemos merge na master (ou branch alvo) ap??s cada fase?
        # N?o, o pipeline opera de forma independente para n?o sujar a master at? a aprova??o,
        # Ent?o ns pr?ximas fases DEVEM puxar da branch da fase anterior!
        
    print("\n============================================================")
    print(" PIPELINE FINALIZADO COM SUCESSO!")
    print(" A aprovação humana (Join Barrier) agora é requerida.")
    print("============================================================")

if __name__ == "__main__":
    main()
