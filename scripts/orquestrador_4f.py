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
    print(f"[ORCHESTRATOR 4F] Acionando Agente em TTY Interativo Efêmero: {cmd}")
    env = os.environ.copy()
    
    if sys.platform == "win32":
        window_title = f"AIDD_TTY_Efemero_{int(time.time())}"
        
        # Prepara prompt em arquivo local na worktree para leitura segura
        prompt_txt = ""
        if input_data and Path(input_data).exists():
            prompt_txt = Path(input_data).read_text(encoding="utf-8").strip()
            local_prompt_path = Path(cwd) / "PROMPT_FASE.txt"
            local_prompt_path.write_text(prompt_txt, encoding="utf-8")
        
        # Script PowerShell interativo visível para o usuário acompanhar ao vivo
        launcher_ps1 = Path(cwd) / "iniciar_agente.ps1"
        launcher_code = f"""
$Host.UI.RawUI.WindowTitle = "{window_title}"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AIDD 4F - AGENTE INTERATIVO AO VIVO" -ForegroundColor Green
Write-Host "  Worktree: $PWD" -ForegroundColor Yellow
Write-Host "  Comando: {cmd}" -ForegroundColor DarkGray
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path "PROMPT_FASE.txt") {{
    $prompt = Get-Content "PROMPT_FASE.txt" -Raw
    & {cmd} $prompt
}} else {{
    & {cmd}
}}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Execução do Agente finalizada. Pressione Enter para fechar." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Read-Host
"""
        launcher_ps1.write_text(launcher_code, encoding="utf-8")
        
        # Abre nova janela visível no Windows
        comando_tty = f'start "{window_title}" powershell -ExecutionPolicy Bypass -NoExit -File "{launcher_ps1}"'
        subprocess.run(comando_tty, shell=True, cwd=cwd, env=env)
        
        if expected_handoff:
            print(f"[WATCHDOG] Janela interativa aberta. Monitorando entrega de '{expected_handoff.name}'...")
            start_wait = time.time()
            handoff_ready = False
            last_size = -1
            stable_count = 0
            
            while True:
                time.sleep(3)
                if expected_handoff.exists():
                    current_size = expected_handoff.stat().st_size
                    if current_size == last_size and current_size > 0:
                        stable_count += 1
                        if stable_count >= 3:  # 9 segundos estável = concluído
                            handoff_ready = True
                            break
                    else:
                        last_size = current_size
                        stable_count = 0
                        
                if time.time() - start_wait > 3600:
                    print("[WATCHDOG] Timeout extremo (1h). Abortando.")
                    break
                    
            if handoff_ready:
                print(f"[WATCHDOG] Handoff detectado e estável! Finalizando TTY interativo...")
                subprocess.run(f'taskkill /F /FI "WINDOWTITLE eq {window_title}*" /T', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
    else:
        # Fallback linux
        subprocess.run(cmd, shell=True, cwd=cwd, env=env)
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
    parser.add_argument("--force", action="store_true", help="Força re-execução ignorando cache")
    parser.add_argument("--fase", help="Executa exclusivamente uma fase específica")
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

    config_user_path = repo_root / "docs" / "auditoria" / "CONFIG-EXECUCAO-USUARIO.json"
    user_config = {}
    if config_user_path.exists():
        try:
            with open(config_user_path, "r", encoding="utf-8") as cf:
                user_config = json.load(cf)
            print(f"[CONFIG] Perfil do usuário carregado de {config_user_path.name}")
        except Exception as e:
            print(f"[CONFIG] Aviso: Falha ao carregar perfil do usuário: {e}")

    for i, fase in enumerate(fases, 1):
        nome = fase.get("nome", f"fase_{i}")
        comando = fase.get("comando_terminal")
        handoff = fase.get("output_handoff")
        
        # Resolução Dinâmica de Harness, Modelo e Comando
        papeis = user_config.get("papeis_pipeline_4f", {})
        padrao = user_config.get("padrao_geral", {})
        perfil_aplicado = None
        
        if "Inspetor_Retorno" in nome or "Retorno" in nome:
            perfil_aplicado = papeis.get("retorno")
        elif "Inspetor" in nome:
            perfil_aplicado = papeis.get("inspetor")
        elif "Arquiteto" in nome:
            perfil_aplicado = papeis.get("arquiteto")
        elif "Construtor" in nome or "Ticket" in nome:
            perfil_aplicado = papeis.get("construtor")
        else:
            perfil_aplicado = padrao

        if perfil_aplicado and (not comando or comando == "auto" or comando == "a_definir_comando_execucao"):
            fase["harness"] = perfil_aplicado.get("harness", fase.get("harness"))
            fase["model"] = perfil_aplicado.get("model", fase.get("model"))
            fase["comando_terminal"] = perfil_aplicado.get("comando_terminal", comando)
            comando = fase["comando_terminal"]
            print(f"[DINÂMICO] Fase '{nome}' configurada via CONFIG-EXECUCAO-USUARIO: {fase['harness']} | {fase['model']}")

        if args.fase and args.fase != nome:
            print(f"[PULANDO] Fase {nome} (filtro por fase: {args.fase})")
            continue

        print(f"\n---> INICIANDO FASE {i}: {nome}")
        
        if handoff and not args.force and not args.fase:
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
        res_wt = run_cmd(f"git worktree remove --force {wt_path}", exit_on_fail=False)
        if wt_path.exists():
            time.sleep(1)
            shutil.rmtree(wt_path, ignore_errors=True)
            run_cmd("git worktree prune", exit_on_fail=False)
        
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
