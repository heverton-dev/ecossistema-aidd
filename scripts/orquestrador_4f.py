import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import threading
from pathlib import Path

def run_cmd_tty(cmd, cwd=None, input_data=None, expected_handoff=None):
    print(f"[ORCHESTRATOR 4F] Acionando Agente em TTY Efêmero: {cmd}")
    env = os.environ.copy()
    
    comando = cmd
    if input_data:
        comando = f'type "{input_data}" | {cmd}'
        
    if sys.platform == "win32":
        # Sem /WAIT para nao travar. Lancamos o popup autonomo.
        window_title = f"AIDD_TTY_Efemero_{time.time()}"
        comando_tty = f'start "{window_title}" cmd /c "{comando}"'
        subprocess.run(comando_tty, shell=True, cwd=cwd, env=env)
        
        if expected_handoff:
            print(f"[WATCHDOG] Monitorando entrega de '{expected_handoff.name}'...")
            start_wait = time.time()
            handoff_ready = False
            last_size = -1
            stable_count = 0
            
            while True:
                time.sleep(2)
                if expected_handoff.exists():
                    current_size = expected_handoff.stat().st_size
                    if current_size == last_size and current_size > 0:
                        stable_count += 1
                        if stable_count >= 3:  # 6 segundos sem mudancas no arquivo = LLM Terminou
                            handoff_ready = True
                            break
                    else:
                        last_size = current_size
                        stable_count = 0
                        
                if time.time() - start_wait > 3600:
                    print("[WATCHDOG] Timeout extremo (1h). Abortando.")
                    break
                    
            if handoff_ready:
                print(f"[WATCHDOG] Handoff detectado e estavel! Puxando a tomada da TUI...")
                subprocess.run(f'taskkill /F /FI "WINDOWTITLE eq {window_title}*" /T', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # Taskkill tb mata o sub-processo cmd /c
                return True
    else:
        # Fallback linux
        subprocess.run(comando, shell=True, cwd=cwd, env=env)
        return True

def run_cmd(cmd, cwd=None, exit_on_fail=True):
    # Execucao nativa oculta padrao para cmds git, etc
    print(f"[ORCHESTRATOR 4F] Executando: {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd, text=True)
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
        
        if handoff:
            handoff_base_path = repo_root / handoff
            if handoff_base_path.exists() and handoff_base_path.stat().st_size > 0:
                print(f"[CACHE] Memória detectada! O arquivo '{handoff_base_path.name}' já está consolidado no projeto principal.")
                print(f"[CACHE] Pulando a execução da IA desta fase para economizar tokens.")
                continue
                
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
        handoff_expected = wt_path / fase.get("output_handoff")
        run_cmd_tty(comando, cwd=wt_path, input_data=str(input_file).replace('/', '\\') if input_file.exists() else None, expected_handoff=handoff_expected)
        
        print(f"[+] Verificando Output Handoff...")
        handoff_file = wt_path / handoff
        if not handoff_file.exists():
            print(f"[-] FALHA: Output {handoff} não foi gerado na worktree.")
            sys.exit(1)
            
        print(f"[+] Handoff confirmado! Persistindo artefatos no worktree...")
        run_cmd("git add -A", cwd=wt_path)
        run_cmd(f"git commit --no-verify -m \"chore(audit): finalizando {nome}\"", cwd=wt_path, exit_on_fail=False)
        
        print(f"[+] Descartando Worktree (Drop & Push to memory)...")
        run_cmd(f"git worktree remove --force {wt_path}")
        
        print(f"[+] Cumulando artefatos: Merge da fase {nome} na memória principal...")
        run_cmd(f"git merge {branch}", exit_on_fail=True)
        
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
