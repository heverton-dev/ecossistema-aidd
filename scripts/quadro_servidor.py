import json
import os
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

class _HttpHandler(BaseHTTPRequestHandler):
    app: QuadroApp = None

    def do_GET(self):
        # Validação de segurança: escuta apenas Host local
        host = self.headers.get("Host", "")
        if not (host.startswith("localhost") or host.startswith("127.0.0.1")):
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Acesso restrito a 127.0.0.1")
            return

        status, headers, body = self.app.tratar_requisicao(self.path)
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Silencioso para não poluir terminal
        pass

def iniciar_servidor(porta: int = 8990, raiz_aidd: Optional[Path] = None):
    app = QuadroApp(raiz_aidd=raiz_aidd)
    _HttpHandler.app = app
    servidor = HTTPServer(("127.0.0.1", porta), _HttpHandler)
    return servidor
