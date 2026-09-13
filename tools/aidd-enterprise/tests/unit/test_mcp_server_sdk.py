# -*- coding: utf-8 -*-
"""
Testes unitários herméticos do MCP Server do núcleo compartilhado (aidd-enterprise).

Cobre o contrato do item 11 do plano anti-NIH (Onda 5 remanescente):
- O servidor usa o SDK oficial do MCP (`mcp.server.fastmcp.FastMCP`) como
  ponte de protocolo (`build_fastmcp()`), com asserções de protocolo feitas
  por `FastMCP.list_tools()` e `FastMCP.call_tool()` reais (asyncio).
- A lógica de negócio continua exercitada pela superfície síncrona
  (`execute_tool`, `handle_json_rpc`) que server.py/webhooks.py/gates usam.

Nenhum mock da lógica de domínio: banco SQLite real em tmp_path.
"""

import asyncio
import hashlib
import importlib.util
import json
import os
import sqlite3
import sys
import unittest
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = TOOL_DIR.parent.parent

# Import por caminho de arquivo (o módulo vive fora do pacote de testes)
_spec = importlib.util.spec_from_file_location(
    "aidd_enterprise_mcp_server", TOOL_DIR / "src" / "core" / "mcp_server.py"
)
mcp_server_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mcp_server_mod)

MCPServer = mcp_server_mod.MCPServer


def _list_tool_names(fastmcp) -> list:
    tools = asyncio.run(fastmcp.list_tools())
    return [t.name for t in tools]


def _call_tool(fastmcp, name: str, args: dict) -> dict:
    resultado = asyncio.run(fastmcp.call_tool(name, args))
    if isinstance(resultado, tuple):
        resultado = resultado[0]
    blocks = list(resultado) if not isinstance(resultado, (list, tuple)) else resultado
    from mcp.types import TextContent

    textos = [b.text for b in blocks if isinstance(b, TextContent)]
    return json.loads(textos[0]) if textos else {}


class _DBFixture(unittest.TestCase):
    """Cria um suite.db real com uma tabela de módulo para os testes."""

    def setUp(self):
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "suite.db")
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "CREATE TABLE mod_crm (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT, "
            "descricao TEXT, dados_json TEXT, status TEXT, ativo INTEGER DEFAULT 1, "
            "atualizado_em TEXT)"
        )
        conn.execute(
            "INSERT INTO mod_crm (titulo, descricao, dados_json, status, ativo) "
            "VALUES ('Cliente Teste', 'desc', '{}', 'ativo', 1)"
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        # No Windows, remover o .db exige que nenhuma conexão SQLite esteja
        # aberta (o sqlite3 coleta e fecha conexões pendentes no GC).
        import gc

        gc.collect()
        self.tmp.cleanup()


class TestSDKProtocolo(_DBFixture):
    """Contrato do SDK oficial: list_tools/call_tool reais via FastMCP."""

    def test_build_fastmcp_expoe_ferramentas_com_inputschema_original(self):
        server = MCPServer(self.db_path)
        fastmcp = server.build_fastmcp()
        tools = asyncio.run(fastmcp.list_tools())

        nomes = {t.name for t in tools}
        self.assertIn("sistema_saude_status", nomes)
        self.assertIn("sistema_executar_consulta", nomes)

        consulta = next(t for t in tools if t.name == "sistema_executar_consulta")
        self.assertEqual(consulta.inputSchema["type"], "object")
        self.assertIn("tabela", consulta.inputSchema["properties"])
        self.assertEqual(consulta.inputSchema["required"], ["tabela"])

    def test_call_tool_via_sdk_executa_handler_real(self):
        server = MCPServer(self.db_path)
        fastmcp = server.build_fastmcp()
        res = _call_tool(fastmcp, "sistema_saude_status", {"detalhado": False})
        self.assertTrue(res["sucesso"])
        self.assertEqual(res["status"], "online")

    def test_call_tool_via_sdk_executa_consulta_sql(self):
        server = MCPServer(self.db_path)
        fastmcp = server.build_fastmcp()
        res = _call_tool(fastmcp, "sistema_executar_consulta", {"tabela": "mod_crm", "limite": 10})
        self.assertTrue(res["sucesso"])
        self.assertEqual(res["total"], 1)
        self.assertEqual(res["registros"][0]["titulo"], "Cliente Teste")

    def test_call_tool_via_sdk_erro_em_ferramenta_desconhecida(self):
        server = MCPServer(self.db_path)
        fastmcp = server.build_fastmcp()
        res = _call_tool(fastmcp, "ferramenta_inexistente", {})
        self.assertFalse(res["sucesso"])
        self.assertIn("não encontrada", res["erro"])

    def test_tools_registradas_dinamicamente_aparecem_no_sdk(self):
        server = MCPServer(self.db_path)
        server.register_module_tools("crm", "CRM")
        fastmcp = server.build_fastmcp()
        nomes = _list_tool_names(fastmcp)
        for esperado in ("crm_listar", "crm_obter_por_id", "crm_criar", "crm_atualizar", "crm_deletar"):
            self.assertIn(esperado, nomes)


class TestSuperficieSincronica(_DBFixture):
    """A superfície síncrona usada por server.py/webhooks.py/gates segue intacta."""

    def test_get_tools_manifest_formato_mcp(self):
        server = MCPServer(self.db_path)
        manifest = server.get_tools_manifest()
        for t in manifest:
            self.assertIn("name", t)
            self.assertIn("description", t)
            self.assertIn("inputSchema", t)
            self.assertEqual(t["inputSchema"]["type"], "object")

    def test_execute_tool_crud_real(self):
        server = MCPServer(self.db_path)
        server.register_module_tools("crm", "CRM")

        criado = server.execute_tool("crm_criar", {"titulo": "Novo item"})
        self.assertTrue(criado["sucesso"])

        listado = server.execute_tool("crm_listar", {})
        self.assertTrue(listado["sucesso"])
        self.assertEqual(listado["total"], 2)

    def test_handle_json_rpc_tools_list_e_call(self):
        server = MCPServer(self.db_path)
        resp_list = server.handle_json_rpc({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        self.assertEqual(resp_list["jsonrpc"], "2.0")
        self.assertIn("tools", resp_list["result"])

        resp_call = server.handle_json_rpc({
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "sistema_saude_status", "arguments": {}},
        })
        self.assertIn("content", resp_call["result"])
        payload = json.loads(resp_call["result"]["content"][0]["text"])
        self.assertTrue(payload["sucesso"])

    def test_handle_request_alias_permanece(self):
        server = MCPServer(self.db_path)
        self.assertIs(server.handle_request.__func__, server.handle_json_rpc.__func__)

    def test_register_injected_tools_sem_diretorio_retorna_zero(self):
        server = MCPServer(self.db_path)
        self.assertEqual(server.register_injected_tools(mcp_dir=os.path.join(self.tmp.name, "inexistente")), 0)


class TestRegisterInjectedToolsAssinaturaEd25519(_DBFixture):
    """Zero-Trust: register_injected_tools() só executa (exec_module) um
    arquivo de src/core/mcp/ quando o manifesto canônico CAPABILITIES.json
    está assinado com Ed25519 (chave pública versionada) E o SHA-256 real do
    arquivo bate com o valor declarado nesse manifesto assinado — item
    'manifest-assinado-ed25519-componentes-enterprise' (PLAN-0018 fase 05)."""

    def _mcp_dir(self) -> str:
        caminho = os.path.join(self.tmp.name, "src", "core", "mcp")
        os.makedirs(caminho, exist_ok=True)
        return caminho

    def _escrever_ferramenta(self, mcp_dir: str, nome: str, extra: str = "") -> str:
        caminho = os.path.join(mcp_dir, f"{nome}.py")
        conteudo = (
            "TOOL_DEF = {\n"
            f"    'name': '{nome}',\n"
            "    'description': 'Ferramenta de teste.',\n"
            "    'input_schema': {'type': 'object', 'properties': {}},\n"
            "}\n\n"
            "def handler(params):\n"
            "    return {'ok': True}\n"
            f"{extra}"
        )
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)
        return caminho

    def _escrever_manifesto(self, hashes_por_arquivo: dict) -> str:
        catalogo = {"mcp": [{"nome": "grupo-teste", "arquivos_hashes": hashes_por_arquivo}]}
        caminho = os.path.join(self.tmp.name, "CAPABILITIES.json")
        with open(caminho, "w", encoding="utf-8", newline="\n") as f:
            json.dump(catalogo, f, ensure_ascii=False, indent=2)
            f.write("\n")
        return caminho

    def test_bloqueia_quando_nao_ha_manifesto_algum(self):
        mcp_dir = self._mcp_dir()
        self._escrever_ferramenta(mcp_dir, "ferramenta_sem_manifesto")
        server = MCPServer(self.db_path)
        self.assertEqual(server.register_injected_tools(mcp_dir=mcp_dir), 0)

    def test_bloqueia_manifesto_com_hash_correto_porem_sem_assinatura(self):
        mcp_dir = self._mcp_dir()
        caminho_tool = self._escrever_ferramenta(mcp_dir, "ferramenta_sem_assinatura")
        rel = os.path.relpath(caminho_tool, self.tmp.name).replace("\\", "/")
        h = hashlib.sha256(open(caminho_tool, "rb").read()).hexdigest()
        self._escrever_manifesto({rel: h})

        server = MCPServer(self.db_path)
        # Manifesto existe e o hash bate, mas não há '.ed25519.sig' — fail-closed.
        self.assertEqual(server.register_injected_tools(mcp_dir=mcp_dir), 0)

    def test_carrega_quando_manifesto_assinado_e_hash_confere(self):
        import assinatura_manifesto
        assinatura_manifesto.salvar_par_chaves()

        mcp_dir = self._mcp_dir()
        caminho_tool = self._escrever_ferramenta(mcp_dir, "ferramenta_ok")
        rel = os.path.relpath(caminho_tool, self.tmp.name).replace("\\", "/")
        h = hashlib.sha256(open(caminho_tool, "rb").read()).hexdigest()
        manifesto = self._escrever_manifesto({rel: h})
        self.assertTrue(assinatura_manifesto.assinar_manifesto(manifesto).sucesso)

        server = MCPServer(self.db_path)
        carregadas = server.register_injected_tools(mcp_dir=mcp_dir)
        self.assertEqual(carregadas, 1)
        self.assertIn("ferramenta_ok", [t["name"] for t in server.get_tools_manifest()])

    def test_bloqueia_arquivo_adulterado_apos_assinatura_do_manifesto(self):
        import assinatura_manifesto
        assinatura_manifesto.salvar_par_chaves()

        mcp_dir = self._mcp_dir()
        caminho_tool = self._escrever_ferramenta(mcp_dir, "ferramenta_adulterada")
        rel = os.path.relpath(caminho_tool, self.tmp.name).replace("\\", "/")
        h = hashlib.sha256(open(caminho_tool, "rb").read()).hexdigest()
        manifesto = self._escrever_manifesto({rel: h})
        self.assertTrue(assinatura_manifesto.assinar_manifesto(manifesto).sucesso)

        # Adulteração DEPOIS da assinatura: manifesto e assinatura continuam
        # íntegros, mas o conteúdo real diverge do hash confiável.
        with open(caminho_tool, "a", encoding="utf-8") as f:
            f.write("\n# linha maliciosa injetada apos a assinatura\n")

        server = MCPServer(self.db_path)
        self.assertEqual(server.register_injected_tools(mcp_dir=mcp_dir), 0)

    def test_bloqueia_ataque_que_reescreve_arquivo_e_hash_no_manifesto(self):
        """O caso central do item: um atacante com acesso de escrita ao
        repositório adultera o arquivo E recalcula/reescreve o hash SHA-256
        correspondente no manifesto para bater — sem a chave privada Ed25519,
        ele não consegue re-assinar, e a verificação recusa o manifesto
        inteiro (nenhuma ferramenta injetada é carregada)."""
        import assinatura_manifesto
        assinatura_manifesto.salvar_par_chaves()

        mcp_dir = self._mcp_dir()
        caminho_tool = self._escrever_ferramenta(mcp_dir, "ferramenta_forjada")
        rel = os.path.relpath(caminho_tool, self.tmp.name).replace("\\", "/")
        h_original = hashlib.sha256(open(caminho_tool, "rb").read()).hexdigest()
        manifesto = self._escrever_manifesto({rel: h_original})
        assinatura_manifesto.assinar_manifesto(manifesto)

        with open(caminho_tool, "a", encoding="utf-8") as f:
            f.write("\n# payload malicioso\n")
        h_novo = hashlib.sha256(open(caminho_tool, "rb").read()).hexdigest()

        with open(manifesto, "r", encoding="utf-8") as f:
            catalogo = json.load(f)
        catalogo["mcp"][0]["arquivos_hashes"][rel] = h_novo
        with open(manifesto, "w", encoding="utf-8", newline="\n") as f:
            json.dump(catalogo, f, ensure_ascii=False, indent=2)

        server = MCPServer(self.db_path)
        self.assertEqual(server.register_injected_tools(mcp_dir=mcp_dir), 0)

    def test_ignora_arquivo_nao_registrado_no_manifesto_mas_carrega_os_demais(self):
        import assinatura_manifesto
        assinatura_manifesto.salvar_par_chaves()

        mcp_dir = self._mcp_dir()
        caminho_registrado = self._escrever_ferramenta(mcp_dir, "ferramenta_registrada")
        self._escrever_ferramenta(mcp_dir, "ferramenta_intrusa")
        rel = os.path.relpath(caminho_registrado, self.tmp.name).replace("\\", "/")
        h = hashlib.sha256(open(caminho_registrado, "rb").read()).hexdigest()
        manifesto = self._escrever_manifesto({rel: h})
        self.assertTrue(assinatura_manifesto.assinar_manifesto(manifesto).sucesso)

        server = MCPServer(self.db_path)
        carregadas = server.register_injected_tools(mcp_dir=mcp_dir)
        nomes = [t["name"] for t in server.get_tools_manifest()]
        self.assertEqual(carregadas, 1)
        self.assertIn("ferramenta_registrada", nomes)
        self.assertNotIn("ferramenta_intrusa", nomes)


class TestIntegracaoSDKOpcional(unittest.TestCase):
    """O import do SDK é condicional: sem o pacote, o JSON-RPC próprio segue funcionando."""

    def test_modulo_importa_sem_dependencia_dura_do_sdk(self):
        # O módulo já foi importado no topo; se o SDK estiver ausente, FastMCP é None
        # e a classe ainda é utilizável (coberto pelos testes síncronos).
        import mcp  # noqa: F401  — ambiente de teste tem o SDK; apenas garante import

        self.assertTrue(hasattr(mcp_server_mod, "MCPServer"))


if __name__ == "__main__":
    unittest.main()
