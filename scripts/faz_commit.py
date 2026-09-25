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
  7. Resumo final: sucesso em 1 linha, ou falha com etapa, gate, arquivo:linha
     e o comando exato para reproduzir só aquele ponto.
"""

import sys
import os
import subprocess
import json
import urllib.request
import urllib.error
import argparse
import re
import shutil
import threading
import time
from dataclasses import dataclass, field


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

    ui.info(f"Gerando mensagem via Ollama local (modelo: {model_name})...")
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
        ui.aviso(f"Ollama: {e}")

    # 2. Gemini API
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            ui.info("Gerando mensagem via Gemini API...")
            return gerar_mensagem_gemini(diff_summary, gemini_key)
        except Exception as e:
            ui.aviso(f"Gemini: {e}")

    # 3. Groq API
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            ui.info("Gerando mensagem via Groq API...")
            return gerar_mensagem_openai_compatible(
                diff_summary, groq_key, "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"
            )
        except Exception as e:
            ui.aviso(f"Groq: {e}")

    # 4. OpenAI API
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            ui.info("Gerando mensagem via OpenAI API...")
            return gerar_mensagem_openai_compatible(
                diff_summary, openai_key, "https://api.openai.com/v1", "gpt-4o-mini"
            )
        except Exception as e:
            ui.aviso(f"OpenAI: {e}")

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


# =============================================================================
# SAÍDA VISUAL
# Cor e ícones só para humano no terminal. Agente, pipe ou NO_COLOR recebem
# texto simples com o mesmo número de linhas (nenhum token a mais).
#
# Grade fixa monoespaçada: todo conteúdo começa na coluna 6 (largura de
# "[1/4] "), detalhes na coluna 8. Só ícones de largura 1 (nada de emoji, que
# ocupa 2 colunas em vários terminais e desalinha tudo).
# =============================================================================

RECUO = " " * 6
LARGURA_GATE = 34

_ICONES = {
    "ok": ("✓", "+"),
    "erro": ("✗", "x"),
    "aviso": ("!", "!"),
    "info": ("›", ">"),
    "seta": ("▸", ">"),
    "ponto": ("∙", "|"),
    "rodando": ("⋯", "."),
}


def _usar_cor(stream):
    # FORCE_COLOR genérico é ignorado de propósito: harnesses de agente (Claude
    # Code exporta FORCE_COLOR=3) o definem e isso gastaria tokens com ANSI.
    # Para forçar/desligar só aqui: FAZ_COMMIT_COR=1 ou FAZ_COMMIT_COR=0.
    escolha = os.environ.get("FAZ_COMMIT_COR")
    if escolha in ("0", "1"):
        return escolha == "1"
    if os.environ.get("NO_COLOR"):
        return False
    return hasattr(stream, "isatty") and stream.isatty()


class Estilo:
    """Formata as mensagens do faz-commit num padrão único."""

    def __init__(self, cor=None, stream=None, stream_erro=None):
        self.stream = stream or sys.stdout
        self.stream_erro = stream_erro or sys.stderr
        self.cor = _usar_cor(self.stream) if cor is None else cor
        # Terminal humano: permite reescrever a linha do gate em andamento (\r).
        self.interativo = hasattr(self.stream, "isatty") and self.stream.isatty()
        self._detecta_unicode()

    def _detecta_unicode(self):
        encoding = getattr(self.stream, "encoding", None) or "utf-8"
        try:
            "".join(u for u, _ in _ICONES.values()).encode(encoding)
            self.unicode = True
        except (UnicodeEncodeError, LookupError):
            self.unicode = False

    def preparar_console(self):
        """UTF-8 na saída (acentos intactos também em pipe/agente) e ANSI no console do Windows."""
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        if (self.cor or self.interativo) and os.name == "nt":
            os.system("")
        self._detecta_unicode()

    def icone(self, nome):
        uni, asc = _ICONES[nome]
        return uni if self.unicode else asc

    def pinta(self, codigo, texto):
        return f"\033[{codigo}m{texto}\033[0m" if self.cor else texto

    def escreve(self, texto, erro=False):
        print(texto, file=self.stream_erro if erro else self.stream, flush=True)

    def etapa(self, n, total, texto):
        self.escreve(self.pinta("1;36", f"[{n}/{total}]") + " " + self.pinta("1", texto))

    def item(self, icone, cor, texto, erro=False):
        """Linha dentro de uma etapa: ícone na coluna 6, texto na coluna 8."""
        self.escreve(f"{RECUO}{self.pinta(cor, self.icone(icone))} {texto}", erro=erro)

    def detalhe(self, texto, erro=False, nivel=1):
        """Texto sem ícone, alinhado com o texto dos itens (coluna 8, ou 10 no nível 2)."""
        self.escreve(f"{RECUO}{'  ' * nivel}{texto}", erro=erro)

    def campo(self, rotulo, texto, erro=False):
        self.escreve(f"{RECUO}{rotulo:<10}{texto}", erro=erro)

    def info(self, texto):
        self.item("info", "2", texto)

    def aviso(self, texto):
        self.item("aviso", "1;33", texto)

    def _final(self, icone, cor, texto, erro=False):
        """Linha de resultado: ícone na coluna 2, texto na mesma coluna 6 das etapas."""
        self.escreve(f"  {self.pinta(cor, self.icone(icone))}   {texto}", erro=erro)

    def ok(self, texto):
        self._final("ok", "1;32", texto)

    def erro(self, texto):
        self._final("erro", "1;31", texto, erro=True)


ui = Estilo()


# =============================================================================
# DIAGNÓSTICO CIRÚRGICO DE FALHAS
# Lê a saída do git/pre-commit e extrai: gate que reprovou, arquivo:linha de
# cada erro e o comando exato para reproduzir só aquele ponto. Nunca inventa
# local: se a saída não traz arquivo/linha, o resumo diz só o que sabe.
# =============================================================================

_RE_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_RE_STATUS_HOOK = re.compile(r"^(?P<nome>\S.*?)\.{3,}.*?(?P<status>Passed|Failed|Skipped)\s*$")
_RE_HOOK_ID = re.compile(r"^- hook id:\s*(?P<id>\S+)")
_RE_TRACEBACK = re.compile(r'^\s*File "(?P<arq>[^"]+)", line (?P<linha>\d+)')
_RE_EXCECAO = re.compile(r"^[A-Za-z_][\w.]*(?:Error|Exception|Exit|Interrupt)\b")
_RE_ARQ_LINHA = re.compile(
    r"^\s*(?P<arq>(?:[A-Za-z]:)?[\w./\\-]+\.\w+):(?P<linha>\d+)(?::\d+)?:\s*(?P<msg>.*)$"
)
# "-> Em scripts/x.py:282": arquivo:linha no fim da linha; o motivo vem na linha anterior.
_RE_ARQ_LINHA_FIM = re.compile(r"(?:^|\s)(?P<arq>(?:[A-Za-z]:)?[\w./\\-]+\.\w+):(?P<linha>\d+)\s*$")
_RE_PYTEST = re.compile(r"^(?:FAILED|ERROR)\s+(?P<teste>\S+::\S+?)(?:\s+-\s+(?P<msg>.*))?$")
_RE_BIBLIOTECA = re.compile(r"site-packages|[\\/]lib[\\/]python|\\Lib\\|^<", re.IGNORECASE)

_DICAS_PUSH = [
    (("non-fast-forward", "fetch first", "[rejected]"),
     "o remoto tem commits que você ainda não tem",
     "git pull --rebase origin {branch} && git push origin {branch}"),
    (("authentication failed", "permission denied", "403", "could not read username"),
     "sem permissão/credencial para enviar ao remoto",
     "gh auth status"),
    (("could not resolve host", "timed out", "unable to access"),
     "sem conexão com o remoto",
     "git push origin {branch}"),
    (("does not appear to be a git repository", "no such remote"),
     "remoto 'origin' não configurado",
     "git remote -v"),
]

_MAX_LOCAIS = 10
_MAX_MSG = 110


@dataclass
class Local:
    arquivo: str
    linha: str = ""
    mensagem: str = ""

    def __str__(self):
        ref = f"{self.arquivo}:{self.linha}" if self.linha else self.arquivo
        msg = self.mensagem.strip()
        if len(msg) > _MAX_MSG:
            msg = msg[:_MAX_MSG - 3] + "..."
        return f"{ref}  {msg}" if msg else ref


@dataclass
class GateFalho:
    nome: str
    hook_id: str = ""
    locais: list = field(default_factory=list)

    @property
    def comando(self):
        return f"python -m pre_commit run {self.hook_id}" if self.hook_id else ""


@dataclass
class Diagnostico:
    etapa: str
    gates: list = field(default_factory=list)
    locais: list = field(default_factory=list)
    causa: str = ""
    comando: str = ""


def _limpa(texto):
    return _RE_ANSI.sub("", texto or "").replace("\r", "")


def _nome_curto_gate(nome):
    m = re.search(r"G_\w+", nome)
    return m.group(0) if m else nome.strip()


def _ultima_linha_util(linhas):
    for linha in reversed(linhas):
        if linha.strip() and not linha.strip().startswith("- "):
            return linha.strip()
    return ""


def _relativo(caminho):
    """Encurta caminho absoluto dentro do diretório atual (repo) para relativo."""
    if not os.path.isabs(caminho):
        return caminho
    try:
        rel = os.path.relpath(caminho)
    except ValueError:  # outro drive no Windows
        return caminho
    return caminho if rel.startswith("..") else rel.replace("\\", "/")


def extrair_locais(linhas):
    """Extrai arquivo:linha + mensagem de tracebacks, linters/pytest e do resumo do pytest."""
    locais, vistos = [], set()
    frame_pendente = None
    anterior = ""

    def adiciona(local):
        local.arquivo = _relativo(local.arquivo)
        chave = (local.arquivo, local.linha)
        if chave not in vistos and len(locais) < _MAX_LOCAIS:
            vistos.add(chave)
            locais.append(local)

    for linha in linhas:
        m = _RE_TRACEBACK.match(linha)
        if m:
            # Guarda o frame mais profundo que é código do projeto (não biblioteca).
            if not _RE_BIBLIOTECA.search(m.group("arq")):
                frame_pendente = Local(m.group("arq"), m.group("linha"))
            continue
        if frame_pendente and _RE_EXCECAO.match(linha.strip()):
            frame_pendente.mensagem = linha.strip()
            adiciona(frame_pendente)
            frame_pendente = None
            continue
        m = _RE_PYTEST.match(linha.strip())
        if m:
            adiciona(Local(m.group("teste"), mensagem=m.group("msg") or ""))
            continue
        m = _RE_ARQ_LINHA.match(linha)
        if m and not _RE_BIBLIOTECA.search(m.group("arq")):
            adiciona(Local(m.group("arq"), m.group("linha"), m.group("msg")))
            continue
        m = _RE_ARQ_LINHA_FIM.search(linha)
        if m and not _RE_BIBLIOTECA.search(m.group("arq")):
            adiciona(Local(m.group("arq"), m.group("linha"), anterior))
        if linha.strip():
            anterior = linha.strip()
    return locais


def diagnosticar(etapa, saida, branch=""):
    """Transforma a saída bruta de uma etapa que falhou num diagnóstico acionável."""
    linhas = _limpa(saida).split("\n")
    diag = Diagnostico(etapa=etapa)

    # Divide a saída do pre-commit por hook e só olha o que veio de hook reprovado:
    # com --verbose os hooks aprovados também imprimem, e isso seria ruído.
    blocos, atual, fora_de_hook = [], None, []
    for linha in linhas:
        m = _RE_STATUS_HOOK.match(linha.strip())
        if m:
            atual = GateFalho(_nome_curto_gate(m.group("nome"))) if m.group("status") == "Failed" else None
            if atual:
                blocos.append((atual, []))
            continue
        if atual is None:
            if not blocos:
                fora_de_hook.append(linha)
            continue
        m = _RE_HOOK_ID.match(linha.strip())
        if m and not atual.hook_id:
            atual.hook_id = m.group("id")
            continue
        blocos[-1][1].append(linha)

    for gate, saida_gate in blocos:
        gate.locais = extrair_locais(saida_gate)
        diag.gates.append(gate)

    if not diag.gates:
        diag.locais = extrair_locais(fora_de_hook)

    if etapa == "push":
        texto = "\n".join(linhas).lower()
        for gatilhos, causa, comando in _DICAS_PUSH:
            if any(g in texto for g in gatilhos):
                diag.causa = causa
                diag.comando = comando.format(branch=branch or "<branch>")
                break

    if not diag.causa and not diag.gates:
        diag.causa = _ultima_linha_util(linhas)
    return diag


def _duracao(inicio):
    return f"{time.time() - inicio:.1f}s".replace(".", ",")


def imprimir_falha(diag, inicio, estilo=None, caminho_log=""):
    estilo = estilo or ui
    seta = estilo.icone("seta")
    estilo.escreve("", erro=True)
    estilo.erro(estilo.pinta("1", f"FALHOU em: {diag.etapa}") + f" {estilo.icone('ponto')} {_duracao(inicio)}")
    for gate in diag.gates:
        estilo.item("erro", "1;31", estilo.pinta("1", gate.nome), erro=True)
        for local in gate.locais:
            estilo.detalhe(f"{seta} {local}", erro=True, nivel=2)
        if not gate.locais:
            estilo.detalhe(estilo.pinta("2", "(o gate não informou arquivo/linha)"), erro=True, nivel=2)
        if gate.comando:
            estilo.detalhe(f"{'repetir:':<10}{estilo.pinta('36', gate.comando)}", erro=True, nivel=2)
    for local in diag.locais:
        estilo.item("seta", "0", str(local), erro=True)
    if diag.causa:
        estilo.campo("Causa", diag.causa, erro=True)
    if diag.comando:
        estilo.campo("Corrigir", estilo.pinta("36", diag.comando), erro=True)
    if caminho_log:
        estilo.campo("Log", caminho_log, erro=True)


def ler_shortstat(texto):
    """'3 files changed, 10 insertions(+), 2 deletions(-)' -> (3, 10, 2)."""
    def num(padrao):
        m = re.search(padrao, texto or "")
        return int(m.group(1)) if m else 0
    return num(r"(\d+) files? changed"), num(r"(\d+) insertions?"), num(r"(\d+) deletions?")


def imprimir_sucesso(inicio, destino, estilo=None):
    estilo = estilo or ui
    p = estilo.icone("ponto")
    hash_curto = run_git(["rev-parse", "--short", "HEAD"])
    arquivos, adicoes, remocoes = ler_shortstat(run_git(["show", "--shortstat", "--format=", "HEAD"]))
    estilo.escreve("")
    estilo.ok(
        f"{estilo.pinta('1;33', hash_curto)} {p} {arquivos} arquivo(s) {p} "
        f"{estilo.pinta('32', f'+{adicoes}')}/{estilo.pinta('31', f'-{remocoes}')} {p} {_duracao(inicio)} "
        f"{estilo.icone('seta')} {destino}"
    )


# O pre-commit imprime "NOME......" ao começar o hook e completa com o status ao terminar.
_RE_INICIO_HOOK = re.compile(r"^(?P<nome>[^\s\-\[].*?)\.{6,}$")


def _tempo(segundos):
    """12,3s até 1 minuto; depois 2m58s (mesma largura curta nas duas formas)."""
    if segundos < 60:
        return f"{segundos:.1f}s".replace(".", ",")
    return f"{int(segundos // 60)}m{int(segundos % 60):02d}s"


_RE_PREFIXO_GATE = re.compile(r"^\[G_\w+\]\s*")


class PainelGates:
    """Mostra 1 linha por gate (✓/✗ + duração) em vez do relatório bruto de cada um.

    Em terminal humano, a linha do gate em andamento é reescrita a cada segundo
    com cronômetro e, se o gate publicar progresso (AIDD_PROGRESSO_AO_VIVO),
    com a última mensagem dele.
    """

    def __init__(self, estilo, caminho_progresso=None):
        self.estilo = estilo
        self.caminho_progresso = caminho_progresso
        self.atual = None
        self.inicio_gate = 0.0
        self.offset_progresso = 0
        self.contagem = {"Passed": 0, "Failed": 0, "Skipped": 0}
        self.trava = threading.Lock()

    def _escreve(self, texto, fim="\n"):
        self.estilo.stream.write(texto + fim)
        self.estilo.stream.flush()

    def _linha_rodando(self, progresso=""):
        e = self.estilo
        base = f"{RECUO}{e.icone('rodando')} {self.atual:<{LARGURA_GATE}}{_tempo(time.time() - self.inicio_gate).rjust(7)}"
        livre = shutil.get_terminal_size((100, 24)).columns - len(base) - 3
        extra = f"  {progresso[:livre]}" if progresso and livre > 10 else ""
        # Recorta antes de pintar: a linha nunca pode quebrar, senão o \r não a reescreve.
        return e.pinta("2", base + extra)

    def _ultimo_progresso(self):
        if not self.caminho_progresso:
            return ""
        try:
            with open(self.caminho_progresso, "r", encoding="utf-8", errors="replace") as f:
                f.seek(self.offset_progresso)
                linhas = [l.strip() for l in f.read().splitlines() if l.strip()]
        except OSError:
            return ""
        return _RE_PREFIXO_GATE.sub("", linhas[-1]) if linhas else ""

    def parcial(self, texto):
        """Linha ainda incompleta: detecta o gate que acabou de começar."""
        with self.trava:
            if self.atual is not None:
                return
            m = _RE_INICIO_HOOK.match(texto)
            if m:
                self.atual = _nome_curto_gate(m.group("nome"))
                self.inicio_gate = time.time()
                try:
                    self.offset_progresso = os.path.getsize(self.caminho_progresso) if self.caminho_progresso else 0
                except OSError:
                    self.offset_progresso = 0
                if self.estilo.interativo:
                    self._escreve(self._linha_rodando(), fim="")

    def tique(self):
        """Chamado a cada segundo: atualiza cronômetro/progresso do gate em andamento."""
        with self.trava:
            if self.atual is not None and self.estilo.interativo:
                self._escreve("\r\033[K" + self._linha_rodando(self._ultimo_progresso()), fim="")

    def linha(self, texto):
        """Linha completa: se for o status de um gate, imprime o resultado."""
        m = _RE_STATUS_HOOK.match(texto.strip())
        if not m:
            return
        with self.trava:
            nome, status = _nome_curto_gate(m.group("nome")), m.group("status")
            duracao = time.time() - self.inicio_gate if self.atual else 0.0
            self.atual = None
            self.contagem[status] += 1
            limpa = "\r\033[K" if self.estilo.interativo else ""
            if status == "Skipped":
                if limpa:
                    self._escreve(limpa, fim="")
                return
            icone = (self.estilo.pinta("1;32", self.estilo.icone("ok")) if status == "Passed"
                     else self.estilo.pinta("1;31", self.estilo.icone("erro")))
            tempo = self.estilo.pinta("2", _tempo(duracao).rjust(7))
            self._escreve(f"{limpa}{RECUO}{icone} {nome:<{LARGURA_GATE}}{tempo}")

    def resumo(self):
        c = self.contagem
        if not sum(c.values()):
            return
        p = self.estilo.icone("ponto")
        partes = [f"{c['Passed']} aprovado(s)"]
        if c["Failed"]:
            partes.append(f"{c['Failed']} reprovado(s)")
        if c["Skipped"]:
            partes.append(f"{c['Skipped']} pulado(s)")
        self.estilo.detalhe(self.estilo.pinta("2", f" {p} ".join(partes)))


def caminho_log_commit(nome="faz-commit.log"):
    """Log bruto do último commit fica dentro de .git (nunca é versionado)."""
    try:
        return run_git(["rev-parse", "--git-path", nome])
    except Exception:
        return nome


def executar_commit(cmd, caminho_log, verboso=False, estilo=None):
    """Roda o git commit guardando a saída completa em log e para o diagnóstico.

    verboso=True repassa tudo para a tela (comportamento antigo); senão mostra
    só o painel compacto de gates.
    """
    estilo = estilo or ui
    env, painel = None, None
    if not verboso:
        # Gates que falam direto com o terminal (G_TESTES_REAIS) passam a gravar
        # o progresso neste arquivo; o painel mostra na linha do gate.
        caminho_progresso = os.path.abspath(caminho_log_commit("faz-commit.progresso"))
        open(caminho_progresso, "w").close()
        env = dict(os.environ, AIDD_PROGRESSO_AO_VIVO=caminho_progresso)
        painel = PainelGates(estilo, caminho_progresso)
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", env=env,
    )
    parar = threading.Event()
    if painel and estilo.interativo:
        def _relogio():
            while not parar.wait(1):
                painel.tique()
        threading.Thread(target=_relogio, daemon=True).start()
    capturado, buffer = [], []
    with open(caminho_log, "w", encoding="utf-8") as log:
        # Lê caractere a caractere: o nome do gate chega antes do "\n", enquanto ele roda.
        while True:
            ch = proc.stdout.read(1)
            if not ch:
                break
            capturado.append(ch)
            log.write(ch)
            if verboso:
                sys.stdout.write(ch)
                if ch == "\n":
                    sys.stdout.flush()
                continue
            if ch == "\n":
                painel.linha(_limpa("".join(buffer)))
                buffer = []
            elif ch != "\r":
                buffer.append(ch)
                if ch == ".":
                    painel.parcial(_limpa("".join(buffer)).strip())
    proc.wait()
    parar.set()
    if painel:
        painel.resumo()
    return proc.returncode, "".join(capturado)


def _detalhes_brutos(texto, estilo=None):
    """Mensagem original do git, recuada na grade (curta: só em falha de add/push)."""
    estilo = estilo or ui
    for linha in (texto or "").strip().splitlines():
        estilo.detalhe(estilo.pinta("2", linha.rstrip()), erro=True)


def _rodar(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def main():
    parser = argparse.ArgumentParser(
        prog="faz-commit",
        description="Script determinístico para git add, git commit e git push com geração probabilística de mensagem via IA."
    )
    parser.add_argument("mensagem", nargs="?", default=None, help="Mensagem opcional de commit (se omitida, será gerada por IA)")
    parser.add_argument("-m", "--message", dest="mensagem_flag", default=None, help="Mensagem explícita de commit")
    parser.add_argument("--no-push", action="store_true", help="Executa git add e commit, mas pula o git push")
    parser.add_argument("--dry-run", action="store_true", help="Apenas simula o processo e exibe a mensagem")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Mostra a saída completa dos quality gates (padrão: 1 linha por gate)")

    args = parser.parse_args()

    ui.preparar_console()
    inicio = time.time()

    # 1. Determinismo: Validação de repositório Git
    try:
        is_git = run_git(["rev-parse", "--is-inside-work-tree"])
        if is_git != "true":
            ui.erro("Este diretório não é um repositório git válido.")
            sys.exit(1)
    except Exception:
        ui.erro("Falha ao verificar repositório git.")
        sys.exit(1)

    # Dry-run fotografa o stage atual para devolvê-lo exatamente como estava
    # (um 'git reset' tiraria do stage também o que o usuário já tinha preparado).
    stage_original = None
    if args.dry_run:
        foto = _rodar(["git", "write-tree"])
        stage_original = foto.stdout.strip() if foto.returncode == 0 else None

    ui.etapa(1, 4, "git add -A")
    res = _rodar(["git", "add", "-A"])
    if res.returncode != 0:
        _detalhes_brutos(res.stderr)
        imprimir_falha(diagnosticar("git add", res.stderr), inicio)
        sys.exit(res.returncode)

    # 2. Determinismo: Verifica se há alterações staged
    status_cached = run_git(["diff", "--cached", "--name-status"])
    if not status_cached:
        ui.info("Nenhuma alteração pendente para commit.")
        sys.exit(0)
    ui.info(f"{len(status_cached.splitlines())} arquivo(s) no stage")

    # 3. Probabilismo: Geração da mensagem
    msg_final = args.mensagem_flag or args.mensagem

    ui.etapa(2, 4, "mensagem de commit")
    if not msg_final:
        ui.info("Gerando via IA a partir do diff...")
        diff_resumo = obter_diff_resumido()
        msg_final = gerar_mensagem_probabilistica(diff_resumo)

        if not msg_final:
            status_short = run_git(["status", "--short"])
            ui.aviso("Nenhuma API de IA configurada (GEMINI_API_KEY, GROQ_API_KEY ou OPENAI_API_KEY).")
            # Tenta prompt interativo se stdin for tty
            if sys.stdin.isatty():
                try:
                    sugerida = fallback_mensagem(status_short)
                    msg_digitada = input(f"{RECUO}Digite a mensagem [{sugerida}]: ").strip()
                    msg_final = msg_digitada if msg_digitada else sugerida
                except EOFError:
                    msg_final = fallback_mensagem(status_short)
            else:
                msg_final = fallback_mensagem(status_short)

    # Só o título: corpo de várias linhas sairia fora da grade (ele vai inteiro no commit).
    linhas_msg = msg_final.strip().splitlines() or [""]
    extra = f"  (+{len(linhas_msg) - 1} linha(s) de corpo)" if len(linhas_msg) > 1 else ""
    ui.info(ui.pinta("1", linhas_msg[0]) + ui.pinta("2", extra))

    if args.dry_run:
        if stage_original:
            run_git(["read-tree", stage_original])
            ui.ok("DRY-RUN: nada foi commitado nem enviado (stage restaurado como estava).")
        else:
            # write-tree falha com conflito de merge pendente: não há foto confiável.
            ui.aviso("DRY-RUN: nada foi commitado, mas o stage não pôde ser restaurado "
                     "(conflito de merge pendente?). Confira com: git status")
        sys.exit(0)

    # 4. Determinismo: Executa commit (painel compacto de gates + log completo)
    ui.etapa(3, 4, "git commit" + ("" if args.verbose else " (quality gates)"))
    caminho_log = caminho_log_commit()
    codigo, saida = executar_commit(["git", "commit", "-m", msg_final], caminho_log, verboso=args.verbose)
    if codigo != 0:
        imprimir_falha(diagnosticar("commit (quality gates)", saida), inicio, caminho_log=caminho_log)
        sys.exit(codigo)

    # 5. Determinismo: Executa push
    if args.no_push:
        imprimir_sucesso(inicio, "local (--no-push)")
        sys.exit(0)

    ui.etapa(4, 4, "git push")
    branch_atual = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    push = ["git", "push", "origin", branch_atual]
    res = _rodar(push)
    if res.returncode != 0 and ("has no upstream branch" in res.stderr or "set-upstream" in res.stderr):
        ui.info(f"Configurando upstream para origin/{branch_atual}...")
        push.insert(2, "--set-upstream")
        res = _rodar(push)
    if args.verbose:
        for texto in (res.stdout, res.stderr):
            if texto.strip():
                print(texto.strip(), flush=True)
    if res.returncode != 0:
        _detalhes_brutos(res.stderr)
        imprimir_falha(diagnosticar("push", res.stderr, branch_atual), inicio)
        sys.exit(res.returncode)
    ui.item("ok", "1;32", f"origin/{branch_atual}")

    imprimir_sucesso(inicio, f"origin/{branch_atual}")


if __name__ == "__main__":
    main()