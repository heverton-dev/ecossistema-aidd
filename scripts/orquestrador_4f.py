import argparse
import ctypes
import json
import os
import shutil
import subprocess
import sys
import time
import threading
from pathlib import Path
import tkinter as tk
from tkinter import scrolledtext

class LiveHUD:
    def __init__(self, title="AIDD - MONITOR AO VIVO", proc_ref=None):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("900x560+150+100")
        self.root.configure(bg="#0f172a")
        self.proc_ref = proc_ref
        
        # Always on top e foco físico
        self.root.attributes("-topmost", True)
        self.root.lift()

        # Cabeçalho
        header = tk.Label(
            self.root, 
            text="⚡ AIDD ECOSSISTEMA - MONITOR DE EXECUÇÃO & CORREÇÃO AO VIVO ⚡", 
            font=("Consolas", 12, "bold"), 
            fg="#38bdf8", 
            bg="#1e293b",
            pady=8
        )
        header.pack(fill="x")

        # Terminal de Logs
        self.text_area = scrolledtext.ScrolledText(
            self.root, 
            wrap="word", 
            bg="#020617", 
            fg="#f8fafc", 
            font=("Consolas", 10),
            padx=12,
            pady=10
        )
        self.text_area.pack(fill="both", expand=True, padx=12, pady=6)
        self.text_area.tag_config("cyan", foreground="#38bdf8")
        self.text_area.tag_config("green", foreground="#4ade80")
        self.text_area.tag_config("yellow", foreground="#facc15")
        self.text_area.tag_config("magenta", foreground="#f43f5e", font=("Consolas", 10, "bold"))
        self.text_area.tag_config("user", foreground="#a855f7", font=("Consolas", 10, "bold"))

        # Barra de status do Watchdog
        self.status_bar = tk.Label(
            self.root,
            text="[WATCHDOG TERMODINÂMICO] Inicializando...",
            font=("Consolas", 9),
            fg="#94a3b8",
            bg="#0f172a",
            anchor="w",
            padx=15
        )
        self.status_bar.pack(fill="x")

        # Container inferior (Input do Prompt de Correção)
        input_container = tk.Frame(self.root, bg="#1e293b", padx=10, pady=8)
        input_container.pack(fill="x", padx=12, pady=6)

        lbl_input = tk.Label(
            input_container, 
            text="Prompt de Correção:", 
            font=("Consolas", 10, "bold"), 
            fg="#f8fafc", 
            bg="#1e293b"
        )
        lbl_input.pack(side="left", padx=5)

        self.entry_correction = tk.Entry(
            input_container, 
            font=("Consolas", 11), 
            bg="#020617", 
            fg="#ffffff", 
            insertbackground="white"
        )
        self.entry_correction.pack(side="left", fill="x", expand=True, padx=8)
        self.entry_correction.bind("<Return>", lambda event: self.enviar_correcao())

        self.btn_send = tk.Button(
            input_container, 
            text="📤 Enviar Correção", 
            font=("Consolas", 10, "bold"), 
            bg="#38bdf8", 
            fg="#0f172a",
            activebackground="#0284c7",
            padx=10, 
            pady=4,
            command=self.enviar_correcao
        )
        self.btn_send.pack(side="left", padx=4)

        self.btn_close = tk.Button(
            input_container, 
            text="✅ Concluir / Fechar", 
            font=("Consolas", 10, "bold"), 
            bg="#22c55e", 
            fg="#ffffff",
            activebackground="#16a34a",
            padx=10, 
            pady=4,
            command=self.concluir
        )
        self.btn_close.pack(side="right", padx=5)

    def log(self, text, tag=None):
        def _append():
            self.text_area.insert(tk.END, text + ("\n" if not text.endswith("\n") else ""), tag)
            self.text_area.see(tk.END)
        try:
            self.root.after(0, _append)
        except Exception:
            pass

    def update_status(self, text, color="#94a3b8"):
        def _up():
            self.status_bar.config(text=text, fg=color)
        try:
            self.root.after(0, _up)
        except Exception:
            pass

    def enviar_correcao(self):
        texto = self.entry_correction.get().strip()
        if not texto:
            return
        self.log(f"\n[INTERVENÇÃO HUMANA] Enviando Prompt de Correção: \"{texto}\"", "user")
        correcao_file = Path("PROMPT_CORRECAO_USUARIO.txt")
        correcao_file.write_text(texto, encoding="utf-8")
        self.update_status(f"[STATUS] Correção registrada! Injetando no agente...", "#a855f7")
        self.entry_correction.delete(0, tk.END)
        if self.proc_ref and self.proc_ref.poll() is None and self.proc_ref.stdin:
            try:
                self.proc_ref.stdin.write(texto + "\n")
                self.proc_ref.stdin.flush()
            except Exception:
                pass

    def fechar_com_atraso(self, delay=2):
        def _close():
            time.sleep(delay)
            try:
                self.root.after(0, self.root.destroy)
            except Exception:
                pass
        threading.Thread(target=_close, daemon=True).start()

    def concluir(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def start(self):
        self.root.mainloop()

def run_cmd_tty(cmd, cwd=None, input_data=None, expected_handoff=None):
    print(f"[ORCHESTRATOR 4F] Acionando Agente em TTY Efêmero HUD: {cmd}")
    env = os.environ.copy()
    
    # Anexa thread ao Desktop físico Default do Windows
    if sys.platform == "win32":
        try:
            user32 = ctypes.windll.user32
            hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
            if hdesk:
                user32.SetThreadDesktop(hdesk)
        except Exception:
            pass

    # Garante a flag nativa de leitura de prompt via stdin para o harness
    parts = cmd.split()
    final_cmd = cmd
    if any("claude" in p for p in parts[:2]):
        if "-p" not in parts and "--print" not in parts:
            final_cmd = f"{cmd} -p"
    elif any("agy" in p for p in parts[:2]):
        if "-p" not in parts and "--print" not in parts and "-i" not in parts:
            final_cmd = f"{cmd} -p -"

    if input_data:
        comando = f'type "{input_data}" | {final_cmd}'
    else:
        comando = final_cmd

    # Inicia o processo conectando streams de E/S
    proc = subprocess.Popen(
        comando,
        shell=True,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        text=True,
        bufsize=1
    )

    hud_title = f"AIDD - {expected_handoff.name if expected_handoff else 'AGENTE'}"
    hud = LiveHUD(title=hud_title, proc_ref=proc)
    hud.log(f"[INFO] Comando: {comando}", "cyan")
    hud.log(f"[INFO] Worktree: {cwd}", "cyan")
    hud.log("[AGENTE] Sessão iniciada. Transmitindo saída ao vivo...", "green")

    # Thread 1: Leitura de stdout em tempo real linha a linha
    def reader_thread():
        try:
            for line in iter(proc.stdout.readline, ''):
                if line:
                    hud.log(line)
        except Exception:
            pass
        hud.log("\n[PROCESSO] Saída do agente finalizada.", "yellow")

    threading.Thread(target=reader_thread, daemon=True).start()

    # Thread 2: Watchdog Termodinâmico
    def watchdog_thread():
        if not expected_handoff:
            return
        hud.log(f"[WATCHDOG] Monitorando entrega de '{expected_handoff.name}'...", "yellow")
        start_wait = time.time()
        last_size = -1
        stable_count = 0
        
        while True:
            time.sleep(2)
            if expected_handoff.exists():
                current_size = expected_handoff.stat().st_size
                hud.update_status(f"[WATCHDOG] '{expected_handoff.name}' detectado ({current_size} bytes). Aferindo estabilidade térmica...", "#eab308")
                if current_size == last_size and current_size > 0:
                    stable_count += 1
                    if stable_count >= 3:  # 6 segundos de taxa de variação zero = concluído
                        hud.log(f"[WATCHDOG] Handoff detectado e estável ({current_size} bytes)! Finalizando...", "green")
                        hud.update_status(f"[SUCESSO] Handoff concluído com sucesso ({current_size} bytes)! Fechando HUD...", "#4ade80")
                        time.sleep(1)
                        if proc.poll() is None:
                            try:
                                proc.terminate()
                            except Exception:
                                pass
                        hud.fechar_com_atraso(delay=2)
                        break
                else:
                    last_size = current_size
                    stable_count = 0
            else:
                hud.update_status(f"[WATCHDOG] Aguardando criação de '{expected_handoff.name}'...", "#94a3b8")

            if time.time() - start_wait > 3600:
                hud.log("[WATCHDOG] Timeout extremo (1h). Abortando.", "magenta")
                break

    threading.Thread(target=watchdog_thread, daemon=True).start()

    # Abre a interface gráfica (bloqueia até a finalização)
    try:
        hud.start()
    except Exception as e:
        print(f"[HUD] Janela finalizada: {e}")

    # Garante encerramento do processo filho
    if proc.poll() is None:
        try:
            proc.kill()
        except Exception:
            pass

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
