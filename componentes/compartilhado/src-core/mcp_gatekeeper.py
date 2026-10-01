# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — CANONICAL MCP LAZY GATEKEEPER
=============================================================================
Servidor proxy MCP transparente e sob demanda (Lazy-Loading) com Idle Reaping.

Benefícios:
1. Zero RAM antes do primeiro uso: backends não iniciam no boot da sessão.
2. Economia de Tokens: expõe meta-tools compactas ou schemas sob demanda.
3. Idle Reaping: encerra subprocessos ociosos liberando 100% da RAM.
4. Agnóstico e determinístico: executável via stdio em qualquer harness e OS.
=============================================================================
"""

import sys
import os
import json
import time
import argparse
import subprocess
import threading
import psutil

DEFAULT_IDLE_TIMEOUT = 300  # 5 minutos


class LazyBackend:
    def __init__(self, name, config, default_idle_timeout=DEFAULT_IDLE_TIMEOUT):
        self.name = name
        self.command = config.get("command")
        self.args = config.get("args", [])
        self.env = {**os.environ, **config.get("env", {})}
        self.cwd = config.get("cwd", os.getcwd())
        self.idle_timeout = config.get("idle_timeout", default_idle_timeout)
        self.process = None
        self.last_active = 0
        self.cached_tools = None
        self.lock = threading.Lock()

    def is_running(self):
        return self.process is not None and self.process.poll() is None

    def get_ram_mb(self):
        if not self.is_running():
            return 0.0
        try:
            p = psutil.Process(self.process.pid)
            mem = p.memory_info().rss
            for child in p.children(recursive=True):
                mem += child.memory_info().rss
            return round(mem / (1024 * 1024), 2)
        except Exception:
            return 0.0

    def start(self):
        with self.lock:
            if self.is_running():
                return
            cmd = [self.command] + self.args
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.cwd,
                env=self.env,
                bufsize=1
            )
            self.last_active = time.time()
            # Handshake MCP obrigatório
            init_req = {
                "jsonrpc": "2.0",
                "id": f"init-{self.name}",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "aidd-lazy-gatekeeper", "version": "1.0"}
                }
            }
            self.process.stdin.write(json.dumps(init_req) + "\n")
            self.process.stdin.flush()
            _ = self.process.stdout.readline()

    def send_request(self, req):
        self.start()
        with self.lock:
            self.last_active = time.time()
            self.process.stdin.write(json.dumps(req) + "\n")
            self.process.stdin.flush()
            resp_line = self.process.stdout.readline()
            self.last_active = time.time()
            if not resp_line:
                return {"jsonrpc": "2.0", "id": req.get("id"), "error": {"code": -32603, "message": "Backend closed stream"}}
            return json.loads(resp_line)

    def get_tools(self):
        if self.cached_tools is not None and not self.is_running():
            return self.cached_tools
        req = {"jsonrpc": "2.0", "id": f"tools-{self.name}", "method": "tools/list", "params": {}}
        res = self.send_request(req)
        tools = res.get("result", {}).get("tools", [])
        self.cached_tools = tools
        return tools

    def check_idle(self):
        with self.lock:
            if self.is_running() and (time.time() - self.last_active > self.idle_timeout):
                self.terminate()

    def terminate(self):
        if self.process:
            try:
                parent = psutil.Process(self.process.pid)
                for child in parent.children(recursive=True):
                    try:
                        child.kill()
                    except Exception:
                        pass
                parent.kill()
            except Exception:
                pass
            self.process = None


class MCPGatekeeperServer:
    def __init__(self, config_path=None):
        self.backends = {}
        self.idle_timeout = DEFAULT_IDLE_TIMEOUT
        self.running = True
        self.load_config(config_path)

        # Thread de watchdog para encerramento de ociosos
        self.watchdog = threading.Thread(target=self._watchdog_loop, daemon=True)
        self.watchdog.start()

    def load_config(self, config_path):
        if config_path and os.path.isfile(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.idle_timeout = data.get("idle_timeout", DEFAULT_IDLE_TIMEOUT)
            for name, cfg in data.get("backends", {}).items():
                self.backends[name] = LazyBackend(name, cfg, self.idle_timeout)
        else:
            local_default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_gatekeeper_backends.json")
            if os.path.isfile(local_default):
                with open(local_default, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.idle_timeout = data.get("idle_timeout", DEFAULT_IDLE_TIMEOUT)
                for name, cfg in data.get("backends", {}).items():
                    self.backends[name] = LazyBackend(name, cfg, self.idle_timeout)
            else:
                default_backends = {
                    "playwright": {
                        "command": "cmd.exe" if sys.platform == "win32" else "npx",
                        "args": ["/c", "npx", "-y", "@playwright/mcp@latest"] if sys.platform == "win32" else ["-y", "@playwright/mcp@latest"]
                    },
                    "context7": {
                        "command": "cmd.exe" if sys.platform == "win32" else "npx",
                        "args": ["/c", "npx", "-y", "@upstash/context7-mcp"] if sys.platform == "win32" else ["-y", "@upstash/context7-mcp"]
                    }
                }
                for name, cfg in default_backends.items():
                    self.backends[name] = LazyBackend(name, cfg, self.idle_timeout)

    def _watchdog_loop(self):
        while self.running:
            time.sleep(5)
            for b in list(self.backends.values()):
                b.check_idle()

    def handle_request(self, req):
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "aidd-lazy-gatekeeper", "version": "1.0.0"}
                }
            }

        if method == "tools/list":
            meta_tools = [
                {
                    "name": "get_mcp_tools",
                    "description": "Lista ferramentas disponíveis em um servidor MCP secundário gerenciado sob demanda (playwright, context7, etc.).",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "server": {"type": "string", "description": "Nome do servidor MCP (ex: playwright, context7)"}
                        },
                        "required": ["server"]
                    }
                },
                {
                    "name": "list_backends",
                    "description": "Lista todos os servidores MCP secundários disponíveis, indicando status de execução e consumo de RAM.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "call_mcp_tool",
                    "description": "Executa uma ferramenta em um servidor MCP secundário sob demanda com repasse transparente.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "server": {"type": "string", "description": "Nome do servidor MCP (ex: playwright, context7)"},
                            "tool": {"type": "string", "description": "Nome da ferramenta a executar"},
                            "arguments": {"type": "object", "description": "Argumentos da ferramenta"}
                        },
                        "required": ["server", "tool", "arguments"]
                    }
                }
            ]
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": meta_tools}}

        if method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})

            if tool_name == "list_backends":
                status = {
                    name: {"running": b.is_running(), "ram_mb": b.get_ram_mb()}
                    for name, b in self.backends.items()
                }
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(status, indent=2)}]}
                }

            if tool_name == "get_mcp_tools":
                server_name = args.get("server")
                if server_name not in self.backends:
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32602, "message": f"Servidor '{server_name}' desconhecido. Disponíveis: {list(self.backends.keys())}"}
                    }
                tools = self.backends[server_name].get_tools()
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(tools, indent=2)}]}
                }

            if tool_name == "call_mcp_tool":
                server_name = args.get("server")
                sub_tool = args.get("tool")
                sub_args = args.get("arguments", {})

                if server_name not in self.backends:
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32602, "message": f"Servidor '{server_name}' desconhecido. Disponíveis: {list(self.backends.keys())}"}
                    }

                sub_req = {
                    "jsonrpc": "2.0",
                    "id": f"call-{req_id}",
                    "method": "tools/call",
                    "params": {"name": sub_tool, "arguments": sub_args}
                }
                sub_resp = self.backends[server_name].send_request(sub_req)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": sub_resp.get("result", {}),
                    "error": sub_resp.get("error")
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Ferramenta desconhecida: {tool_name}"}
            }

        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    def run(self):
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                try:
                    req = json.loads(line)
                    resp = self.handle_request(req)
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
                except Exception as e:
                    err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}
                    sys.stdout.write(json.dumps(err_resp) + "\n")
                    sys.stdout.flush()
        finally:
            self.running = False
            for b in self.backends.values():
                b.terminate()


def main():
    parser = argparse.ArgumentParser(description="MCP Lazy Gatekeeper")
    parser.add_argument("--config", help="Caminho para arquivo de configuração JSON com os backends", default=None)
    args = parser.parse_args()

    server = MCPGatekeeperServer(config_path=args.config)
    server.run()


if __name__ == "__main__":
    main()
