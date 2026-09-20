#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
FAZ-COMMIT — EXECUÇÃO DETERMINÍSTICA DE GIT COM MENSAGEM PROBABILÍSTICA (IA)
=============================================================================
Fluxo determinístico:
  1. git rev-parse (valida se é repo git)
  2. git add -A
  3. git diff --cached (valida se há alterações)
  4. Geração probabilística da mensagem (LLM baseada no diff) ou parâmetro CLI
  5. git commit -m "<mensagem>"
  6. git push origin <branch>
"""

import sys
import os
import subprocess
import json
import urllib.request
import urllib.error
import argparse


def carregar_env():
    """Carrega variáveis do arquivo .env no diretório atual ou raiz do repo se existirem."""
    for env_path in [".env", os.path.expanduser("~/.faz-commit.env")]:
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'\"")
                            if k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass


def run_git(args, check=True, capture_output=True):
    """Executa um comando git determinístico."""
    try:
        res = subprocess.run(
            ["git"] + args,
            check=check,
            capture_output=capture_output,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        return res.stdout.strip() if capture_output else ""
    except subprocess.CalledProcessError as e:
        if capture_output and e.stderr:
            print(f"[ERRO GIT] {e.stderr.strip()}", file=sys.stderr)
        raise e


def obter_diff_resumido():
    """Obtém status e diff truncado para minimizar tokens enviados à LLM."""
    status = run_git(["status", "--short"])
    stat = run_git(["diff", "--cached", "--stat"])
    raw_diff = run_git(["diff", "--cached"])

    # Limita o diff a no máximo 4000 caracteres para extrema economia de tokens
    if len(raw_diff) > 4000:
        raw_diff = raw_diff[:4000] + "\n... [diff truncado para economia de tokens]"

    return f"STATUS DOS ARQUIVOS:\n{status}\n\nESTATÍSTICAS:\n{stat}\n\nTRECHO DO DIFF:\n{raw_diff}"


def gerar_mensagem_gemini(diff_summary, api_key):
    """Gera mensagem de commit usando Gemini REST API nativa."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    prompt = (
        "Você é um assistente sênior de git especializado em Conventional Commits. "
        "Analise as alterações a seguir e gere UMA ÚNICA linha de mensagem de commit "
        "no formato: <tipo>(<escopo opcional>): <descrição em português>. "
        "Tipos válidos: feat, fix, docs, style, refactor, perf, test, chore. "
        "Retorne APENAS a linha de commit, sem aspas, sem crases, sem explicações.\n\n"
        f"{diff_summary}"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 100
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        texto = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Remove eventuais aspas ou quebras
        return texto.split("\n")[0].strip("`\"' ")


def gerar_mensagem_openai_compatible(diff_summary, api_key, base_url, model):
    """Gera mensagem de commit para provedores compatíveis com OpenAI (Groq, OpenAI, Ollama)."""
    url = f"{base_url.rstrip('/')}/chat/completions"
    prompt = (
        "Analise as alterações do git e gere UMA ÚNICA linha de mensagem de commit "
        "no formato Conventional Commits (<tipo>: <descrição em português>). "
        "Exemplos: feat: adicionar funcionalidade X, fix: corrigir bug no login, docs: atualizar readme. "
        "Responda EXCLUSIVAMENTE a linha do commit, sem explicações, sem crases e sem aspas."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": diff_summary}
        ],
        "temperature": 0.2,
        "max_tokens": 100
    }

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers
    )

    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        texto = data["choices"][0]["message"]["content"].strip()
        return texto.split("\n")[0].strip("`\"' ")


def obter_modelo_ollama():
    """Consulta os modelos instalados no Ollama e retorna o primeiro disponível."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("models", [])
            if models:
                return models[0].get("name") or models[0].get("model")
    except Exception:
        pass
    return None


def gerar_mensagem_ollama(diff_summary):
    """Gera mensagem via Ollama local com detecção automática do modelo instalado."""
    model_name = obter_modelo_ollama()
    if not model_name:
        return None

    print(f" -> Gerando mensagem via Ollama local (modelo: {model_name})...")
    url = "http://localhost:11434/api/generate"
    prompt = (
        "Você é um assistente de desenvolvimento sênior. Analise as alterações do git e retorne "
        "EXCLUSIVAMENTE UMA ÚNICA linha de mensagem de commit no formato Conventional Commits em português.\n"
        "Exemplo: feat: adicionar funcionalidade X\n"
        "NÃO coloque aspas, NÃO coloque crases (backticks), NÃO adicione explicações adicionais.\n\n"
        f"{diff_summary}"
    )
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        raw = data.get("response", "").strip()
        # Pega a primeira linha não vazia e remove crases/aspas
        linhas = [l.strip("`\"' ") for l in raw.split("\n") if l.strip("`\"' ")]
        return linhas[0] if linhas else None


def gerar_mensagem_probabilistica(diff_summary):
    """
    Tenta provedores de IA em ordem:
    1. Ollama local (se ativo e com modelo baixado, 100% offline e sem custo)
    2. Gemini API (GEMINI_API_KEY)
    3. Groq API (GROQ_API_KEY)
    4. OpenAI API (OPENAI_API_KEY)
    """
    carregar_env()

    # 1. Prioridade: Ollama Local (100% offline)
    try:
        msg_ollama = gerar_mensagem_ollama(diff_summary)
        if msg_ollama:
            return msg_ollama
    except Exception as e:
        print(f" [Aviso Ollama] {e}")

    # 2. Gemini API
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            print(" -> Gerando mensagem via Gemini API...")
            return gerar_mensagem_gemini(diff_summary, gemini_key)
        except Exception as e:
            print(f" [Aviso Gemini] {e}")

    # 3. Groq API
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            print(" -> Gerando mensagem via Groq API...")
            return gerar_mensagem_openai_compatible(
                diff_summary, groq_key, "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"
            )
        except Exception as e:
            print(f" [Aviso Groq] {e}")

    # 4. OpenAI API
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            print(" -> Gerando mensagem via OpenAI API...")
            return gerar_mensagem_openai_compatible(
                diff_summary, openai_key, "https://api.openai.com/v1", "gpt-4o-mini"
            )
        except Exception as e:
            print(f" [Aviso OpenAI] {e}")

    return None


def fallback_mensagem(status_short):
    """Gera mensagem determinística básica de fallback caso nenhuma IA esteja configurada."""
    linhas = [l.strip() for l in status_short.split("\n") if l.strip()]
    if not linhas:
        return "chore: atualizar alterações no repositório"
    primeiro = linhas[0].split()[-1]
    total = len(linhas)
    if total == 1:
        return f"chore: atualizar {os.path.basename(primeiro)}"
    return f"chore: atualizar {os.path.basename(primeiro)} e mais {total - 1} arquivo(s)"


def main():
    parser = argparse.ArgumentParser(
        prog="faz-commit",
        description="Script determinístico para git add, git commit e git push com geração probabilística de mensagem via IA."
    )
    parser.add_argument("mensagem", nargs="?", default=None, help="Mensagem opcional de commit (se omitida, será gerada por IA)")
    parser.add_argument("-m", "--message", dest="mensagem_flag", default=None, help="Mensagem explícita de commit")
    parser.add_argument("--no-push", action="store_true", help="Executa git add e commit, mas pula o git push")
    parser.add_argument("--dry-run", action="store_true", help="Apenas simula o processo e exibe a mensagem")

    args = parser.parse_args()

    # 1. Determinismo: Validação de repositório Git
    try:
        is_git = run_git(["rev-parse", "--is-inside-work-tree"])
        if is_git != "true":
            print("[ERRO] Este diretório não é um repositório git válido.", file=sys.stderr)
            sys.exit(1)
    except Exception:
        print("[ERRO] Falha ao verificar repositório git.", file=sys.stderr)
        sys.exit(1)

    print("==> 1/4 [Determinístico] Executando: git add -A")
    run_git(["add", "-A"], capture_output=False)

    # 2. Determinismo: Verifica se há alterações staged
    status_cached = run_git(["diff", "--cached", "--name-status"])
    if not status_cached:
        print("[-] Nenhuma alteração pendente para commit.")
        sys.exit(0)

    # 3. Probabilismo: Geração da mensagem
    msg_final = args.mensagem_flag or args.mensagem

    if not msg_final:
        print("==> 2/4 [Probabilístico] Analisando diff para geração da mensagem via IA...")
        diff_resumo = obter_diff_resumido()
        msg_final = gerar_mensagem_probabilistica(diff_resumo)

        if not msg_final:
            status_short = run_git(["status", "--short"])
            print(" [!] Nenhuma API de IA configurada (GEMINI_API_KEY, GROQ_API_KEY ou OPENAI_API_KEY).")
            # Tenta prompt interativo se stdin for tty
            if sys.stdin.isatty():
                try:
                    sugerida = fallback_mensagem(status_short)
                    msg_digitada = input(f" Digite a mensagem de commit [{sugerida}]: ").strip()
                    msg_final = msg_digitada if msg_digitada else sugerida
                except EOFError:
                    msg_final = fallback_mensagem(status_short)
            else:
                msg_final = fallback_mensagem(status_short)

    print(f"\n[MENSAGEM DE COMMIT]: {msg_final}\n")

    if args.dry_run:
        run_git(["reset"], capture_output=True)
        print("[DRY-RUN] Nenhuma alteração foi commitada ou enviada (staging desfeito).")
        sys.exit(0)

    # 4. Determinismo: Executa commit
    print("==> 3/4 [Determinístico] Executando: git commit")
    run_git(["commit", "-m", msg_final], capture_output=False)

    # 5. Determinismo: Executa push
    if args.no_push:
        print("[+] Commit concluído com sucesso (--no-push ativo, push ignorado).")
        sys.exit(0)

    print("==> 4/4 [Determinístico] Executando: git push")
    try:
        branch_atual = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        # Tenta push simples; se não houver upstream configurado, configura automaticamente
        res = subprocess.run(
            ["git", "push", "origin", branch_atual],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if res.returncode != 0:
            if "has no upstream branch" in res.stderr or "set-upstream" in res.stderr:
                print(f" -> Configurando upstream para origin/{branch_atual}...")
                run_git(["push", "--set-upstream", "origin", branch_atual], capture_output=False)
            else:
                print(res.stderr, file=sys.stderr)
                sys.exit(res.returncode)
        else:
            if res.stdout:
                print(res.stdout.strip())
            if res.stderr:
                print(res.stderr.strip())
        print(f"\n[OK] Commit e push concluídos com sucesso na branch '{branch_atual}'!")
    except Exception as e:
        print(f"[ERRO] Falha durante o git push: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
