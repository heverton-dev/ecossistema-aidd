import http.server
import os
import socketserver
import sys
import threading

import pytest

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
src_abs = os.path.abspath(SRC_DIR)
if sys.path[0] != src_abs:
    sys.path.insert(0, src_abs)

for mod in list(sys.modules.keys()):
    if mod == "server" or mod == "core" or mod.startswith("core."):
        del sys.modules[mod]

import server  # noqa: E402
from core.database import Database  # noqa: E402
from core.mcp_server import LogisticaMCPServer  # noqa: E402
from core.models import init_all_schemas  # noqa: E402
from core.webhooks import WebhookDispatcher  # noqa: E402


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Redireciona os singletons globais de server.py para um banco sqlite
    isolado por teste, para não escrever no suite.db real do exemplo."""
    db_path = tmp_path / "logistica_test.db"
    db = Database(f"sqlite:///{db_path}")
    with db.get_connection() as conn:
        init_all_schemas(conn)

    dispatcher = WebhookDispatcher(db)
    mcp = LogisticaMCPServer(str(db_path))

    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "webhook_dispatcher", dispatcher)
    monkeypatch.setattr(server, "mcp_engine", mcp)
    return server


@pytest.fixture
def db_conn(app):
    with app.db.get_connection() as conn:
        yield conn


@pytest.fixture
def webhook_receiver():
    """Sobe um servidor HTTP local real para receber webhooks disparados
    nos testes, sem depender de acesso à internet."""
    received = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            received.append({"body": body, "headers": dict(self.headers)})
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"recebido": true}')

        def log_message(self, *args):
            pass

    httpd = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{port}/hook", received

    httpd.shutdown()
    thread.join(timeout=2)


@pytest.fixture
def live_server(app):
    """Sobe o servidor HTTP real (AppHandler) numa porta efêmera, já com os
    singletons apontando para o banco de teste isolado."""
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), app.AppHandler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{port}"

    httpd.shutdown()
    thread.join(timeout=2)
