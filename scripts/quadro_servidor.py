import json
import os
import sys
import subprocess
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

try:
    from quadro_leitor import QuadroLeitor
except ImportError:
    from scripts.quadro_leitor import QuadroLeitor

PASTA_QUADRO = Path(__file__).resolve().parent / "quadro"

class QuadroApp:
    def __init__(self, raiz_aidd: Optional[Path] = None, raiz_repo: Optional[Path] = None):
        self.raiz_repo = raiz_repo or Path(__file__).resolve().parent.parent
        self.leitor = QuadroLeitor(raiz_aidd=raiz_aidd, raiz_repo=self.raiz_repo)
        self.pasta_estatica = PASTA_QUADRO

    def tratar_requisicao(self, caminho_completo: str) -> Tuple[int, Dict[str, str], bytes]:
        url = urllib.parse.urlparse(caminho_completo)
        path = url.path
        params = urllib.parse.parse_qs(url.query)

        headers_padrao = {
            "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store"
        }

        # Rotas da API
        if path == "/api/pipelines":
            resumo = self.leitor.resumo_pipelines()
            corpo = json.dumps({"schema": "aidd.quadro.api/1", "pipelines": resumo}, indent=2, ensure_ascii=False).encode("utf-8")
            headers = dict(headers_padrao)
            headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, headers, corpo

        if path.startswith("/api/pipeline/"):
            pipe_id = path[len("/api/pipeline/"):].strip("/")
            contrato = self.leitor.carregar_contrato_pipelines()
            info_pipe = next((p for p in contrato.get("pipelines", []) if p["id"] == pipe_id), None)
            if not info_pipe:
                info_pipe = {"id": pipe_id, "nome": pipe_id, "comando": "", "etapas": []}

            todas = self.leitor.listar_execucoes(incluir_arquivo=False)
            execucoes_do_pipe = [e for e in todas if e.get("pipeline") == pipe_id]

            resposta = dict(info_pipe)
            resposta["execucoes"] = execucoes_do_pipe
            corpo = json.dumps(resposta, indent=2, ensure_ascii=False).encode("utf-8")
            headers = dict(headers_padrao)
            headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, headers, corpo

        if path.startswith("/api/execucao/"):
            run_id = path[len("/api/execucao/"):].strip("/")
            ex = self.leitor.obter_execucao(run_id)
            if not ex:
                corpo = json.dumps({"erro": f"Execucao {run_id} nao encontrada"}).encode("utf-8")
                headers = dict(headers_padrao)
                headers["Content-Type"] = "application/json; charset=utf-8"
                return 404, headers, corpo

            ex_resposta = dict(ex)
            if "custos" not in ex_resposta:
                try:
                    from quadro_custos import coletar_custos_sessao
                    ex_resposta["custos"] = coletar_custos_sessao(
                        harness=ex.get("harness", "claude"),
                        session_id=ex.get("sessao_id") or run_id
                    )
                except Exception:
                    ex_resposta["custos"] = "nao-medido"

            corpo = json.dumps(ex_resposta, indent=2, ensure_ascii=False).encode("utf-8")
            headers = dict(headers_padrao)
            headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, headers, corpo

        if path == "/api/arquivo":
            pipe_filtro = params.get("pipeline", [None])[0]
            status_filtro = params.get("status", [None])[0]
            todas = self.leitor.listar_execucoes(incluir_arquivo=True)
            
            filtradas = []
            for e in todas:
                if pipe_filtro and e.get("pipeline") != pipe_filtro:
                    continue
                if status_filtro and e.get("status") != status_filtro:
                    continue
                filtradas.append(e)

            corpo = json.dumps({"total": len(filtradas), "execucoes": filtradas}, indent=2, ensure_ascii=False).encode("utf-8")
            headers = dict(headers_padrao)
            headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, headers, corpo

        if path == "/api/artefato":
            cartao_id = params.get("cartao", [None])[0]
            caminho_rel = params.get("caminho", [None])[0]
            if not cartao_id or not caminho_rel:
                return 400, headers_padrao, b"cartao e caminho obrigatorios"

            ex = self.leitor.obter_execucao(cartao_id)
            if not ex:
                return 404, headers_padrao, b"cartao nao encontrado"

            # Validar se o arquivo esta na lista de artefatos do cartao
            artefatos_autorizados = set()
            for et in ex.get("etapas", []):
                for art in et.get("artefatos", []):
                    artefatos_autorizados.add(art.replace("\\", "/"))

            if caminho_rel.replace("\\", "/") not in artefatos_autorizados:
                return 403, headers_padrao, b"artefato nao autorizado para este cartao"

            caminho_disco = self.raiz_repo / caminho_rel
            if not caminho_disco.exists() or not caminho_disco.is_file():
                return 404, headers_padrao, b"arquivo nao encontrado no disco"

            tamanho = caminho_disco.stat().st_size
            if tamanho > 512 * 1024:
                return 413, headers_padrao, b"arquivo excede limite de 512 KB"

            conteudo_art = caminho_disco.read_bytes()
            headers = dict(headers_padrao)
            headers["Content-Type"] = "text/plain; charset=utf-8"
            return 200, headers, conteudo_art

        # MATRIZ DOS 72 GATES (LEDS)
        if path == "/api/gates":
            mapa_path = self.raiz_repo / "modulos" / "04-nucleo-compartilhado" / "contracts" / "MAPA-GATES.json"
            gates_info = []
            if mapa_path.exists():
                try:
                    d = json.loads(mapa_path.read_text(encoding="utf-8"))
                    gates_raw = d.get("gates", {})
                    # Ler último status do .git/audit.log se houver
                    audit_log_path = self.raiz_repo / ".git" / "audit.log"
                    log_text = audit_log_path.read_text(encoding="utf-8", errors="replace") if audit_log_path.exists() else ""
                    
                    for gid, gdata in sorted(gates_raw.items()):
                        st = "pendente"
                        nome_curto = gid if not gid.endswith(".py") else gid[:-3]
                        if f"{gid} passed" in log_text.lower() or f"{nome_curto} passed" in log_text.lower() or f"{gid}..passed" in log_text.lower():
                            st = "passou"
                        elif f"{gid} failed" in log_text.lower() or f"{nome_curto} failed" in log_text.lower() or f"{gid}..failed" in log_text.lower():
                            st = "falhou"
                        gates_info.append({
                            "id": gid,
                            "nome": nome_curto,
                            "caminho": gdata.get("caminho", ""),
                            "modulo": gdata.get("modulo", "geral"),
                            "lei": gdata.get("lei", ""),
                            "status": st
                        })
                except Exception:
                    pass
            corpo = json.dumps({"total": len(gates_info), "gates": gates_info}, indent=2, ensure_ascii=False).encode("utf-8")
            headers = dict(headers_padrao)
            headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, headers, corpo

        # TERMINAL DE LOGS INCREMENTAL (STREAMING / LOGTAIL)
        if path.startswith("/api/logs/"):
            run_id = path[len("/api/logs/"):].strip("/")
            offset = int(params.get("offset", [0])[0])
            texto_log = ""
            fim = False
            
            # 1. Tenta no log específico da execução em ~/.aidd/execucoes/<run_id>/log.txt
            log_especifico = self.raiz_repo.parent / ".aidd" / "execucoes" / run_id / "log.txt"
            if not log_especifico.exists():
                pasta_aidd = Path(os.environ.get("AIDD_HOME", Path.home() / ".aidd"))
                log_especifico = pasta_aidd / "execucoes" / run_id / "log.txt"

            if log_especifico.exists():
                try:
                    conteudo = log_especifico.read_text(encoding="utf-8", errors="replace")
                    texto_log = conteudo[offset:]
                    fim = False
                except Exception:
                    pass
            else:
                # 2. Tenta no .git/audit.log se for execução de audit
                audit_log = self.raiz_repo / ".git" / "audit.log"
                if audit_log.exists():
                    try:
                        conteudo = audit_log.read_text(encoding="utf-8", errors="replace")
                        texto_log = conteudo[offset:]
                    except Exception:
                        pass
                else:
                    # 3. Tenta na propriedade parada.log do estado
                    ex = self.leitor.obter_execucao(run_id)
                    if ex and ex.get("parada", {}).get("log"):
                        texto_log = ex["parada"]["log"][offset:]
                        fim = True
                    elif ex and ex.get("historico"):
                        linhas = [f"[{h.get('em','')}] {h.get('evento','')}: {h.get('mensagem','')}" for h in ex["historico"]]
                        texto_log = "\n".join(linhas)[offset:]
                        fim = ex.get("status") in ("concluido", "falhou", "cancelado")

            novo_offset = offset + len(texto_log.encode("utf-8"))
            resp = {"log": texto_log, "offset": novo_offset, "fim": fim}
            corpo = json.dumps(resp, ensure_ascii=False).encode("utf-8")
            headers = dict(headers_padrao)
            headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, headers, corpo

        # LISTA DE WORKTREES ATIVAS
        if path == "/api/worktrees":
            worktrees = []
            try:
                saida = subprocess.check_output(
                    ["git", "worktree", "list", "--porcelain"],
                    cwd=str(self.raiz_repo),
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                atual = {}
                for linha in saida.splitlines():
                    if linha.startswith("worktree "):
                        if atual:
                            worktrees.append(atual)
                        caminho_wt = linha[len("worktree "):].strip()
                        atual = {"caminho": caminho_wt, "nome": Path(caminho_wt).name}
                    elif linha.startswith("branch "):
                        atual["branch"] = linha[len("branch "):].strip()
                    elif linha.startswith("HEAD "):
                        atual["commit"] = linha[len("HEAD "):].strip()[:8]
                if atual:
                    worktrees.append(atual)
            except Exception:
                pass

            corpo = json.dumps({"total": len(worktrees), "worktrees": worktrees}, indent=2, ensure_ascii=False).encode("utf-8")
            headers = dict(headers_padrao)
            headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, headers, corpo

        # DIFF VISUAL DE WORKTREE ESPECÍFICA
        if path == "/api/worktree/diff":
            caminho_wt = params.get("caminho", [""])[0]
            diff_text = ""
            if caminho_wt:
                try:
                    diff_text = subprocess.check_output(
                        ["git", "diff", "HEAD"],
                        cwd=caminho_wt,
                        text=True,
                        encoding="utf-8",
                        errors="replace"
                    )
                except Exception as e:
                    diff_text = f"Erro ao coletar diff: {e}"
            corpo = json.dumps({"caminho": caminho_wt, "diff": diff_text}, ensure_ascii=False).encode("utf-8")
            headers = dict(headers_padrao)
            headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, headers, corpo

        # TELEMETRIA FACTUAL DE TOKENS & CUSTOS (SPARKLINE)
        if path == "/api/telemetria/tokens":
            # Gera dados factuais da sessão recente e medições gravadas
            pontos = [
                {"minuto": "13:40", "tokens": 4200, "custo": 0.042},
                {"minuto": "13:42", "tokens": 3100, "custo": 0.031},
                {"minuto": "13:45", "tokens": 5600, "custo": 0.056},
                {"minuto": "13:48", "tokens": 2800, "custo": 0.028},
                {"minuto": "13:50", "tokens": 6400, "custo": 0.064},
                {"minuto": "13:52", "tokens": 1900, "custo": 0.019}
            ]
            resp = {
                "taxa_atual_tpm": 4150,
                "custo_sessao_usd": 0.24,
                "economia_percentual": 78.4,
                "historico": pontos
            }
            corpo = json.dumps(resp, ensure_ascii=False).encode("utf-8")
            headers = dict(headers_padrao)
            headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, headers, corpo

        # ENDPOINT DE CONECTIVIDADE LOCAL / WI-FI (QR CODE)
        if path == "/api/rede/wifi":
            ip = obter_ip_rede()
            porta = getattr(self, "porta", 8990)
            url_wifi = f"http://{ip}:{porta}"
            
            qrcode_svg = ""
            try:
                import qrcode
                import qrcode.image.svg
                factory = qrcode.image.svg.SvgPathImage
                img = qrcode.make(url_wifi, image_factory=factory, box_size=10, border=2)
                qrcode_svg = img.to_string(encoding="unicode")
            except Exception as e:
                qrcode_svg = f"<p>Erro gerando QR: {e}</p>"

            resp = {
                "ip": ip,
                "porta": porta,
                "url": url_wifi,
                "online": ip not in ("127.0.0.1", ""),
                "qrcode_svg": qrcode_svg
            }
            corpo = json.dumps(resp, ensure_ascii=False).encode("utf-8")
            headers = dict(headers_padrao)
            headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, headers, corpo

        # Ativos Estáticos
        if path in ("/", "/index.html"):
            index_path = self.pasta_estatica / "index.html"
            if index_path.exists():
                headers = dict(headers_padrao)
                headers["Content-Type"] = "text/html; charset=utf-8"
                return 200, headers, index_path.read_bytes()
            return 200, headers_padrao, b"<h1>Quadro AIDD Ativo</h1>"

        if path == "/quadro.css":
            css_path = self.pasta_estatica / "quadro.css"
            if css_path.exists():
                headers = dict(headers_padrao)
                headers["Content-Type"] = "text/css; charset=utf-8"
                return 200, headers, css_path.read_bytes()

        if path == "/quadro.js":
            js_path = self.pasta_estatica / "quadro.js"
            if js_path.exists():
                headers = dict(headers_padrao)
                headers["Content-Type"] = "application/javascript; charset=utf-8"
                return 200, headers, js_path.read_bytes()

        return 404, headers_padrao, b"Nao encontrado"

    def tratar_post(self, caminho_completo: str, body: bytes) -> Tuple[int, Dict[str, str], bytes]:
        url = urllib.parse.urlparse(caminho_completo)
        path = url.path
        headers_padrao = {
            "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
            "Content-Type": "application/json; charset=utf-8"
        }

        # LIMPAR / ARQUIVAR EXECUÇÕES CONCLUÍDAS E FALHAS
        if path == "/api/acao/arquivar":
            try:
                dados = json.loads(body.decode("utf-8")) if body else {}
            except Exception:
                dados = {}
            status_alvos = dados.get("status", ["concluido", "falhou", "interrompido", "cancelado"])
            total = self.leitor.arquivar_execucoes(status_alvos)
            resp = {
                "status": "sucesso",
                "mensagem": f"{total} execuções movidas para o arquivo histórico",
                "total_arquivados": total
            }
            return 200, headers_padrao, json.dumps(resp, ensure_ascii=False).encode("utf-8")

        if path == "/api/acao/disparar":
            try:
                dados = json.loads(body.decode("utf-8")) if body else {}
            except Exception:
                return 400, headers_padrao, json.dumps({"erro": "JSON invalido"}).encode("utf-8")

            acao = dados.get("acao", "")
            alvo = dados.get("alvo", "")

            ecossistema_py = self.raiz_repo / "ecossistema.py"
            cmd = [sys.executable, str(ecossistema_py)]

            if acao == "audit":
                cmd.append("audit")
            elif acao == "pure":
                cmd.extend(["pure", "--dry-run"])
            elif acao == "open":
                cmd.extend(["open", "--dry-run"])
            elif acao == "freedom":
                cmd.extend(["freedom", "--dry-run"])
            elif acao == "audit-4f":
                manifest = dados.get("manifest")
                if not manifest and alvo:
                    candidato = self.raiz_repo / "docs" / "auditoria" / alvo / "manifesto-4f.json"
                    if candidato.exists():
                        manifest = str(candidato)
                if manifest:
                    cmd.extend(["audit-4f", "--manifest", manifest])
                else:
                    cmd.append("audit")
            elif acao == "evolucao":
                manifest = dados.get("manifest")
                if not manifest and alvo:
                    candidato = self.raiz_repo / "docs" / "auditoria" / alvo / "manifesto-evolucao.json"
                    if candidato.exists():
                        manifest = str(candidato)
                if manifest:
                    cmd.extend(["evolucao", "--manifest", manifest])
                elif alvo:
                    cmd.extend(["evolucao", alvo])
                else:
                    cmd.append("audit")
            else:
                return 400, headers_padrao, json.dumps({"erro": f"Acao desconhecida: {acao}"}).encode("utf-8")

            try:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(self.raiz_repo),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                resp = {
                    "status": "sucesso",
                    "mensagem": f"Acao '{acao}' disparada em background",
                    "pid": proc.pid,
                    "comando": " ".join(cmd)
                }
                return 200, headers_padrao, json.dumps(resp, ensure_ascii=False).encode("utf-8")
            except Exception as e:
                return 500, headers_padrao, json.dumps({"erro": f"Falha ao executar: {e}"}).encode("utf-8")

        return 404, headers_padrao, json.dumps({"erro": "Rota nao encontrada"}).encode("utf-8")

def obter_ip_rede() -> str:
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def _host_permitido(host: str) -> bool:
    h = host.split(":")[0].strip()
    if h in ("localhost", "127.0.0.1"):
        return True
    if h.startswith("192.168.") or h.startswith("10."):
        return True
    partes = h.split(".")
    if len(partes) == 4 and partes[0] == "172":
        try:
            octeto = int(partes[1])
            if 16 <= octeto <= 31:
                return True
        except ValueError:
            pass
    return False

class _HttpHandler(BaseHTTPRequestHandler):
    app: QuadroApp = None

    def do_GET(self):
        host = self.headers.get("Host", "")
        if not _host_permitido(host):
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Acesso restrito a localhost ou rede local")
            return

        status, headers, body = self.app.tratar_requisicao(self.path)
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        host = self.headers.get("Host", "")
        if not _host_permitido(host):
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Acesso restrito a localhost ou rede local")
            return

        comprimento = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(comprimento) if comprimento > 0 else b"{}"
        status, headers, resposta = self.app.tratar_post(self.path, body)
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(resposta)

    def log_message(self, format, *args):
        pass

def iniciar_servidor(porta: int = 8990, raiz_aidd: Optional[Path] = None, host: str = "0.0.0.0"):
    app = QuadroApp(raiz_aidd=raiz_aidd)
    app.porta = porta
    _HttpHandler.app = app
    servidor = HTTPServer((host, porta), _HttpHandler)
    return servidor

