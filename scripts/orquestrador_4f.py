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

ORCA_TIMEOUT_AGENTE_S = 3600
ORCA_ESPERA_CHECK_MS = 900000
PREAMBULO = ".aidd-preambulo.md"
_run_orca = {}


def orca(*args, timeout=120):
    """orca CLI com --json. Devolve o 'result' ou None (CLI ausente, runtime fora, erro)."""
    try:
        res = subprocess.run(["orca", *args, "--json"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=timeout)
        dados = json.loads(res.stdout or "{}")
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        print(f"[ORCA] erro em 'orca {' '.join(args[:2])}': {type(e).__name__}")
        return None
    if not dados.get("ok"):
        erro = dados.get("error") or {}
        print(f"[ORCA] erro em 'orca {' '.join(args[:2])}': {erro.get('code')} {erro.get('message', '')}".rstrip())
        return None
    return dados.get("result")


def comando_interativo(cmd):
    """No terminal visível o agente roda em modo interativo: sem -p/--print (modo headless)."""
    partes = cmd.split()
    return " ".join(p for i, p in enumerate(partes)
                    if p not in ("-p", "--print") and not (p == "-" and i and partes[i - 1] in ("-p", "--print")))


def run_orca(objetivo):
    """Um Run de orquestração por pipeline: caixa de entrada onde chegam os worker_done."""
    if "id" not in _run_orca:
        run = orca("orchestration", "run-create", "--objective", objetivo)
        _run_orca["id"] = ((run or {}).get("run") or {}).get("id")
    return _run_orca["id"]


def tela(handle):
    """O que o terminal mostra AGORA (read --screen); o agentWait do Orca fica velho no mimo."""
    lido = orca("terminal", "read", "--terminal", handle, "--screen") or {}
    return "\n".join(lido.get("terminal", {}).get("tail", []))


def enviar_linha(handle, texto):
    """Texto e Enter em envios separados: 'texto + --enter' passa pela observação de prompt do
    Orca, que retém o envio quando acha que o harness ainda espera confiança (mimo, 2026-09-24)."""
    if orca("terminal", "send", "--terminal", handle, "--text", texto) is None:
        return False
    time.sleep(1)
    return orca("terminal", "send", "--terminal", handle, "--enter") is not None


def confirmar_confianca_pasta(handle, tentativas=3):
    """Harness novo numa worktree nova pergunta "confiar nesta pasta?". Sem isso, o texto
    enviado é consumido pela pergunta e o prompt se perde (visto com mimo, 2026-09-24)."""
    for _ in range(tentativas):
        atual = tela(handle).lower()
        if "accept the risks" in atual:
            # Aviso de risco (mimo --yolo) tem "No, exit" como padrão: Enter fecharia o agente.
            print("[ORCA] AVISO: harness abriu confirmação de risco; Enter não será enviado. "
                  "Use a variável de ambiente do harness no lugar da flag (ex.: MIMOCODE_DANGEROUSLY_SKIP_PERMISSIONS=1).")
            return
        if "trust this folder" not in atual and "trust the contents" not in atual:
            return
        print("[ORCA] Confirmando 'confiar nesta pasta' do harness.")
        orca("terminal", "send", "--terminal", handle, "--enter")
        orca("terminal", "wait", "--terminal", handle, "--for", "tui-idle", "--timeout-ms", "30000", timeout=60)


def aguardar_worker_done(run_id, dispatch_id, timeout_s=None):
    """Bloqueia no inbox do Run (sem polling) até o worker_done/escalation deste dispatch."""
    timeout_s = timeout_s or ORCA_TIMEOUT_AGENTE_S
    espera_ms = min(ORCA_ESPERA_CHECK_MS, timeout_s * 1000)
    inicio = time.time()
    while time.time() - inicio < timeout_s:
        lote = orca("orchestration", "check", "--run", run_id, "--wait", "--types", "worker_done,escalation",
                    "--timeout-ms", str(espera_ms), timeout=espera_ms // 1000 + 60)
        if not lote:
            time.sleep(5)
            continue
        achado = None
        for msg in lote.get("messages", []):
            payload = json.loads(msg.get("payload") or "{}")
            if payload.get("dispatchId") != dispatch_id:
                continue
            achado = ("failed" if msg.get("type") == "escalation" else payload.get("outcome", "failed"),
                      msg.get("subject", ""))
        if lote.get("deliveryId"):
            orca("orchestration", "check", "--run", run_id, "--ack", lote["deliveryId"])
        if achado:
            return achado
    return "timeout", f"sem worker_done em {timeout_s}s"


def excluir_do_git(cwd, nome):
    """Registra 'nome' no info/exclude local do repositório (compartilhado pelas worktrees)."""
    caminho = subprocess.run(["git", "rev-parse", "--git-path", "info/exclude"], cwd=cwd,
                             capture_output=True, text=True).stdout.strip()
    if not caminho:
        return
    exclude = Path(cwd) / caminho
    atual = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    if nome not in atual.splitlines():
        exclude.parent.mkdir(parents=True, exist_ok=True)
        exclude.write_text(atual + ("" if atual.endswith("\n") or not atual else "\n") + nome + "\n", encoding="utf-8")


def run_agente_orca(cmd, cwd, input_data=None, expected_handoff=None, titulo="AIDD"):
    """Agente num terminal VISÍVEL do Orca, com a tarefa entregue por orchestration dispatch.
    Devolve None se o Orca não abriu o terminal (chamador cai no modo oculto); senão o outcome."""
    run_id = run_orca(f"Pipeline 4F: {Path(cwd).parent.name}")
    seletor = f"path:{cwd}"
    terminal = None
    for _ in range(5):  # o Orca pode levar alguns segundos para enxergar uma worktree recém-criada
        terminal = run_id and orca("terminal", "create", "--worktree", seletor, "--title", titulo,
                                   "--command", comando_interativo(cmd))
        if terminal:
            break
        time.sleep(2)
    if not terminal:
        return None

    handle = terminal["terminal"]["handle"]
    preambulo = Path(cwd) / PREAMBULO
    print(f"[ORCA] Agente visível na aba '{titulo}' ({handle}). Acompanhe pelo Orca.")
    try:
        orca("terminal", "wait", "--terminal", handle, "--for", "tui-idle", "--timeout-ms", "60000", timeout=90)
        confirmar_confianca_pasta(handle)
        # Prompt embutido na spec: o agente não precisa ler nada fora da worktree (mimo pede
        # permissão de "external directory" mesmo com auto-aprovação, 2026-09-24).
        spec = Path(input_data).read_text(encoding="utf-8-sig").strip() if input_data else titulo
        if expected_handoff:
            spec += f" Required deliverable: {Path(expected_handoff).relative_to(cwd).as_posix()}."
        # Commit é do orquestrador, depois do gate_fase. Commit do agente na worktree roda o
        # pre-commit ali (reprova por arquivos gerados fora do git) e já poluiu a branch do ciclo.
        spec += " Do NOT run git commit, git push or git reset: the orchestrator commits after the phase gate."
        tarefa = orca("orchestration", "task-create", "--run", run_id, "--task-title", titulo, "--spec", spec)
        # --inject digita o preâmbulo mas o Orca bloqueia o Enter em harness que ele não reconhece
        # (agent_prompt_blocked no agy, 2026-09-24). Preâmbulo em arquivo + 1 linha funciona em todos.
        envio = tarefa and orca("orchestration", "dispatch", "--task", tarefa["task"]["id"], "--to", handle,
                                "--run", run_id, "--return-preamble")
        if not envio:
            print("[ORCA] FALHA: dispatch da tarefa recusado pelo Orca.")
            return "failed"
        # O preâmbulo tem a credencial do dispatch: ignorado pelo git e apagado antes do gate/commit.
        excluir_do_git(cwd, PREAMBULO)
        preambulo.write_text(envio["preamble"], encoding="utf-8")
        instrucao = f"Read the file {PREAMBULO} and follow its instructions exactly."
        if not enviar_linha(handle, instrucao):
            print("[ORCA] FALHA: instrução não entregue ao terminal.")
            return "failed"
        outcome, resumo = aguardar_worker_done(run_id, envio["dispatch"]["id"])
        print(f"[ORCA] worker_done: {outcome} — {resumo}")
        return outcome
    finally:
        # Terminal aberto trava a pasta da worktree: fecha antes de qualquer remoção.
        orca("terminal", "close", "--worktree", seletor, "--all")
        preambulo.unlink(missing_ok=True)


def run_cmd_tty(cmd, cwd=None, input_data=None, expected_handoff=None, titulo="AIDD"):
    if os.environ.get("AIDD_AGENTE_MODO", "orca") == "orca":
        outcome = run_agente_orca(cmd, cwd, input_data, expected_handoff, titulo=titulo)
        if outcome is not None:
            return outcome
        print("[ORCA] Orca indisponível. Caindo no modo oculto (HUD).")
    return run_hud_oculto(cmd, cwd, input_data, expected_handoff)


def run_hud_oculto(cmd, cwd=None, input_data=None, expected_handoff=None):
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


def git(args, cwd, exit_on_fail=True):
    """git com argumentos em lista (caminhos com espaço/acento seguros no Windows)."""
    res = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0 and exit_on_fail:
        print(f"[ORCHESTRATOR 4F] FALHA: git {' '.join(args)} -> exit {res.returncode}\n{res.stderr.strip()}")
        sys.exit(1)
    return res


def ref_existe(ref, cwd):
    return git(["rev-parse", "--verify", "--quiet", ref], cwd, exit_on_fail=False).returncode == 0


def sha_de(ref, cwd):
    return git(["rev-parse", ref], cwd).stdout.strip()


def saida_ja_existe(caminho, branch_ciclo, repo_root):
    """Saída já consolidada: aprovada na branch atual OU produzida neste ciclo e aguardando aprovação."""
    no_projeto = repo_root / caminho
    if no_projeto.exists() and no_projeto.stat().st_size > 0:
        return True
    return git(["cat-file", "-e", f"{branch_ciclo}:{Path(caminho).as_posix()}"], repo_root, exit_on_fail=False).returncode == 0


def rodar_gate(comando, cwd):
    print(f"[GATE] {comando}")
    return subprocess.run(comando, shell=True, cwd=cwd).returncode


def abrir_worktree(branch, wt_path, repo_root):
    fechar_worktree(wt_path, repo_root)
    wt_path.parent.mkdir(parents=True, exist_ok=True)
    git(["worktree", "add", str(wt_path), branch], repo_root)


def fechar_worktree(wt_path, repo_root, tentativas=12, intervalo=5):
    # Terminal recém-fechado ainda segura a pasta por alguns segundos no Windows: tenta de novo.
    for i in range(tentativas):
        if not wt_path.exists():
            break
        git(["worktree", "remove", "--force", str(wt_path)], repo_root, exit_on_fail=False)
        shutil.rmtree(wt_path, ignore_errors=True)
        if wt_path.exists() and i < tentativas - 1:
            time.sleep(intervalo)
    if wt_path.exists():
        print(f"[ORCHESTRATOR 4F] AVISO: pasta ainda travada, remova depois: {wt_path}")
    git(["worktree", "prune"], repo_root, exit_on_fail=False)


def ref_aprovavel(pipeline_id):
    return f"refs/aidd/aprovavel/{pipeline_id}"


def aprovar(pipeline_id, repo_root):
    """Join Barrier: ação HUMANA. Merge na branch atual só do commit que passou no gate_final."""
    branch_ciclo = f"audit/{pipeline_id}"
    ref = ref_aprovavel(pipeline_id)
    if not ref_existe(ref, repo_root) or not ref_existe(branch_ciclo, repo_root):
        print(f"[APROVAÇÃO] RECUSADA: '{branch_ciclo}' não tem execução aprovada pelo gate_final.")
        return 1
    if sha_de(branch_ciclo, repo_root) != sha_de(ref, repo_root):
        print(f"[APROVAÇÃO] RECUSADA: '{branch_ciclo}' mudou depois do gate_final. Rode o pipeline de novo.")
        return 1
    res = git(["merge", "--no-ff", "-m", f"chore(audit): aprova {pipeline_id}", branch_ciclo], repo_root, exit_on_fail=False)
    if res.returncode != 0:
        print(f"[APROVAÇÃO] FALHA no merge de '{branch_ciclo}':\n{res.stdout}{res.stderr}")
        return 1
    git(["branch", "-D", branch_ciclo], repo_root, exit_on_fail=False)
    git(["update-ref", "-d", ref], repo_root, exit_on_fail=False)
    print(f"[APROVAÇÃO] '{branch_ciclo}' mergeada na branch atual e removida.")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--force", action="store_true", help="Força re-execução ignorando cache")
    parser.add_argument("--fase", help="Executa exclusivamente uma fase específica")
    parser.add_argument("--aprovar", action="store_true",
                        help="Join Barrier (ação humana): mergeia a branch do ciclo aprovada pelo gate_final")
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

    if args.aprovar:
        sys.exit(aprovar(pipeline_id, repo_root))

    # As fases acumulam numa branch própria do ciclo; a branch atual só muda com --aprovar.
    branch_ciclo = f"audit/{pipeline_id}"
    worktrees_base = repo_root.parent / f"worktrees_{pipeline_id}"

    print(f"============================================================")
    print(f" PIPELINE 4F INICIADO: {pipeline_id}")
    print(f" Total de Fases: {len(fases)}")
    print(f" Branch do ciclo: {branch_ciclo}")
    print(f" Worktrees geradas em: {worktrees_base}")
    print(f"============================================================")

    if not ref_existe(branch_ciclo, repo_root):
        git(["branch", branch_ciclo, "HEAD"], repo_root)

    fases_em_cache = 0
    for i, fase in enumerate(fases, 1):
        nome = fase.get("nome", f"fase_{i}")
        comando = fase.get("comando_terminal")
        handoff = fase.get("output_handoff")
        gate_fase = fase.get("gate_fase")

        if args.fase and args.fase != nome:
            print(f"[PULANDO] Fase {nome} (filtro por fase: {args.fase})")
            continue

        print(f"\n---> INICIANDO FASE {i}: {nome}")

        if handoff and not args.force and not args.fase and saida_ja_existe(handoff, branch_ciclo, repo_root):
            print(f"[CACHE] '{handoff}' já existe (projeto ou {branch_ciclo}). Pulando a execução da IA desta fase.")
            fases_em_cache += 1
            continue

        if not gate_fase:
            print(f"[-] FALHA: fase '{nome}' sem 'gate_fase' no manifesto. Nenhuma fase é commitada sem gate.")
            print("    Regere o manifesto (scaffold_auditoria.py ou compilador_plano_evolucao.py).")
            sys.exit(1)

        wt_path = worktrees_base / nome
        print(f"[+] Isolando Worktree na branch do ciclo...")
        abrir_worktree(branch_ciclo, wt_path, repo_root)

        print(f"[+] Lendo Input Prompt via nativo: {fase.get('input_prompt')}")
        input_file = repo_root / fase.get("input_prompt")
        if not input_file.exists():
            print(f"[-] AVISO: Prompt input não encontrado em {input_file}")

        print(f"[+] Acionando Agente ({fase.get('harness')} | {fase.get('model')})...")
        handoff_file = wt_path / handoff
        outcome = run_cmd_tty(comando, cwd=wt_path,
                              input_data=str(input_file).replace('/', '\\') if input_file.exists() else None,
                              expected_handoff=handoff_file, titulo=fase.get("ticket_id", nome))
        if outcome in ("failed", "timeout"):
            print(f"[-] FALHA: agente de '{nome}' encerrou com '{outcome}'. Worktree preservada para inspeção: {wt_path}")
            sys.exit(1)

        print(f"[+] Verificando Output Handoff...")
        if not handoff_file.exists():
            print(f"[-] FALHA: Output {handoff} não foi gerado. Worktree preservada para inspeção: {wt_path}")
            sys.exit(1)

        # Gate da fase ANTES do commit: saída não conferida nunca entra no histórico.
        if rodar_gate(gate_fase, wt_path) != 0:
            print(f"[-] FALHA: gate_fase de '{nome}' reprovou. Nada foi commitado; fases seguintes não rodam.")
            print(f"    Worktree preservada para inspeção: {wt_path}")
            sys.exit(1)

        git(["add", "-A"], wt_path)
        # --no-verify aqui é deliberado: o gate específico da fase acabou de passar, e a bateria
        # completa (gate_final) roda uma única vez no fim, antes de liberar a aprovação.
        git(["commit", "--no-verify", "-m", f"chore(audit): {nome} (gate_fase exit 0)"], wt_path, exit_on_fail=False)
        fechar_worktree(wt_path, repo_root)
        print(f"[+] Fase {nome} commitada em {branch_ciclo}.")

    if fases and fases_em_cache == len(fases):
        # Nenhum agente foi chamado: declarar sucesso aqui seria rótulo desonesto (Lei #8).
        alvo = data.get("target_tool", "<ferramenta>")
        print("\n============================================================")
        print(f" NADA A FAZER: as {len(fases)} fases deste manifesto já têm saída ({data.get('ciclo', 'ciclo atual')}).")
        print(" Nenhum agente foi executado. Para uma nova rodada, abra o próximo ciclo:")
        print(f"   python scripts/scaffold_auditoria.py {alvo}")
        print(" Para refazer este mesmo ciclo por cima: --force")
        print("============================================================")
        return

    if args.fase:
        print(f"\n[FASE ÚNICA] '{args.fase}' concluída em {branch_ciclo}. gate_final não roda com --fase.")
        return

    gate_final = data.get("gate_final")
    if not gate_final:
        print("[-] FALHA: manifesto sem 'gate_final'. O ciclo não pode ficar aprovável sem a bateria completa.")
        sys.exit(1)

    wt_final = worktrees_base / "_gate_final"
    abrir_worktree(branch_ciclo, wt_final, repo_root)
    codigo_final = rodar_gate(gate_final, wt_final)
    fechar_worktree(wt_final, repo_root)
    if codigo_final != 0:
        print(f"[-] FALHA: gate_final reprovou (exit {codigo_final}). {branch_ciclo} NÃO está aprovável.")
        sys.exit(1)

    git(["update-ref", ref_aprovavel(pipeline_id), branch_ciclo], repo_root)
    print("\n============================================================")
    print(f" PIPELINE CONCLUÍDO: {branch_ciclo} passou no gate_final.")
    print(" A branch atual NÃO foi alterada. Aprovação humana (Join Barrier) requerida:")
    print(f"   python scripts/orquestrador_4f.py --manifest {args.manifest} --aprovar")
    print("============================================================")


if __name__ == "__main__":
    main()
