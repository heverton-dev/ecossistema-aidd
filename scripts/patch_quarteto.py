import os
import sys
import json
from pathlib import Path

def aplicar_patch_08():
    caminho = Path('modulos/02-triade-motores/fluxo-01-pure/core/aidd-pure/scripts/phases/08_implementador.py')
    conteudo = caminho.read_text(encoding='utf-8')

    bloco_antigo = """        elif "quarteto" in nome_m or "studio" in nome_m:
            codigo = (
                '\"\"\"Módulo de integração do Quarteto Sine Qua Non Dinâmico.\"\"\"\\n'
                'from typing import Dict, Any\\n\\n'
                'def obter_openapi_spec() -> Dict[str, Any]:\\n'
                '    \"\"\"Retorna especificação OpenAPI 3.1 do sistema.\"\"\"\\n'
                '    return {\\n'
                '        \"openapi\": \"3.1.0\",\\n'
                '        \"info\": {\"title\": \"API Quarteto\", \"version\": \"1.0.0\"},\\n'
                '        \"paths\": {\"/api\": {\"get\": {\"summary\": \"OpenAPI Studio\"}}}\\n'
                '    }\\n\\n'
                'def obter_mcp_manifest() -> Dict[str, Any]:\\n'
                '    \"\"\"Retorna manifesto JSON-RPC MCP Studio.\"\"\"\\n'
                '    return {\"protocol\": \"jsonrpc-2.0\", \"endpoint\": \"/mcp\", \"tools\": []}\\n\\n'
                'def obter_webhook_manifest() -> Dict[str, Any]:\\n'
                '    \"\"\"Retorna manifesto do Webhook Studio.\"\"\"\\n'
                '    return {\"endpoint\": \"/webhook\", \"hmac_algorithm\": \"sha256\", \"events\": []}\\n\\n'
                'def obter_docs_info() -> Dict[str, str]:\\n'
                '    \"\"\"Retorna informações da Central de Documentação.\"\"\"\\n'
                '    return {\"endpoint\": \"/docs\", \"status\": \"online\"}\\n'
            )
            teste = (
                '\"\"\"Testes unitários para quarteto_studios.\"\"\"\\n'
                f'from {modulo} import (\\n'
                '    obter_openapi_spec,\\n'
                '    obter_mcp_manifest,\\n'
                '    obter_webhook_manifest,\\n'
                '    obter_docs_info,\\n'
                ')\\n\\n'
                'def test_quarteto_studios_contratos():\\n'
                '    spec = obter_openapi_spec()\\n'
                '    assert spec[\"openapi\"] == \"3.1.0\"\\n'
                '    mcp = obter_mcp_manifest()\\n'
                '    assert mcp[\"endpoint\"] == \"/mcp\"\\n'
                '    wh = obter_webhook_manifest()\\n'
                '    assert wh[\"endpoint\"] == \"/webhook\"\\n'
                '    docs = obter_docs_info()\\n'
                '    assert docs[\"endpoint\"] == \"/docs\"\\n'
            )"""

    bloco_novo = """        elif "quarteto" in nome_m or "studio" in nome_m:
            # Deriva o Quarteto dinamicamente do PLANNER.json (Lei #10)
            modulos_planner = []
            for arq_p in [self.pasta_projeto / "PLANNER.json", self.pasta_projeto / "HANDOFF_PLANNER_ENGINE.json"]:
                if arq_p.exists():
                    try:
                        with open(arq_p, "r", encoding="utf-8") as fp:
                            dp = json.load(fp)
                            modulos_planner = dp.get("modulos_funcionais") or []
                            if modulos_planner:
                                break
                    except Exception:
                        pass
            
            slugs = [m.get("slug", "item") for m in modulos_planner] if modulos_planner else ["tarefas", "usuarios"]
            paths_codigo = ", ".join([f'\\"/api/{s}\\": {{\"get\": {{\"summary\": \\"Listar {s}\\"}}, \\"post\": {{\"summary\": \\"Criar {s}\\"}}}}' for s in slugs])
            tools_codigo = ", ".join([f'{{\"name\": \\"listar_{s}\\", \\"description\": \\"Listar {s}\\"}}, {{\"name\": \\"criar_{s}\\", \\"description\": \\"Criar {s}\\"}}' for s in slugs])
            events_codigo = ", ".join([f'\\"{s}.criado\\", \\"{s}.atualizado\\", \\"{s}.removido\\"' for s in slugs])
            
            codigo = (
                '\"\"\"Módulo de integração do Quarteto Sine Qua Non Dinâmico (Lei #10).\"\"\"\\n'
                'from typing import Dict, Any, List\\n\\n'
                'def obter_openapi_spec() -> Dict[str, Any]:\\n'
                '    \"\"\"Retorna especificação OpenAPI 3.1 derivada dos módulos do Planner.\"\"\"\\n'
                f'    return {{\\n'
                f'        \"openapi\": \"3.1.0\",\\n'
                f'        \"info\": {{\"title\": \"API Quarteto\", \"version\": \"1.0.0\"}},\\n'
                f'        \"paths\": {{{paths_codigo}}}\\n'
                f'    }}\\n\\n'
                'def obter_mcp_manifest() -> Dict[str, Any]:\\n'
                '    \"\"\"Retorna manifesto JSON-RPC MCP Studio derivado do Planner.\"\"\"\\n'
                f'    return {{\"protocol\": \"jsonrpc-2.0\", \"endpoint\": \"/mcp\", \"tools\": [{tools_codigo}]}}\\n\\n'
                'def obter_webhook_manifest() -> Dict[str, Any]:\\n'
                '    \"\"\"Retorna manifesto do Webhook Studio derivado do Planner.\"\"\"\\n'
                f'    return {{\"endpoint\": \"/webhook\", \"hmac_algorithm\": \"sha256\", \"events\": [{events_codigo}]}}\\n\\n'
                'def obter_docs_info() -> Dict[str, Any]:\\n'
                '    \"\"\"Retorna informações da Central de Documentação.\"\"\"\\n'
                f'    return {{\"endpoint\": \"/docs\", \"status\": \"online\", \"modulos\": {json.dumps(slugs)}}}\\n'
            )
            teste = (
                '\"\"\"Testes unitários para quarteto_studios consistente com o Planner.\"\"\"\\n'
                f'from {modulo} import (\\n'
                '    obter_openapi_spec,\\n'
                '    obter_mcp_manifest,\\n'
                '    obter_webhook_manifest,\\n'
                '    obter_docs_info,\\n'
                ')\\n\\n'
                'def test_quarteto_studios_contratos():\\n'
                '    spec = obter_openapi_spec()\\n'
                '    assert spec[\"openapi\"] == \"3.1.0\"\\n'
                '    assert len(spec[\"paths\"]) >= 1\\n'
                '    mcp = obter_mcp_manifest()\\n'
                '    assert mcp[\"endpoint\"] == \"/mcp\"\\n'
                '    assert len(mcp[\"tools\"]) >= 1\\n'
                '    wh = obter_webhook_manifest()\\n'
                '    assert wh[\"endpoint\"] == \"/webhook\"\\n'
                '    assert len(wh[\"events\"]) >= 1\\n'
                '    docs = obter_docs_info()\\n'
                '    assert docs[\"endpoint\"] == \"/docs\"\\n'
                '    assert len(docs.get(\"modulos\", [])) >= 1\\n'
            )"""

    if bloco_antigo in conteudo:
        conteudo = conteudo.replace(bloco_antigo, bloco_novo)
        caminho.write_text(conteudo, encoding='utf-8')
        print("SUCESSO: 08_implementador.py atualizado para Quarteto dinâmico!")
    else:
        print("AVISO: Bloco antigo não encontrado em 08_implementador.py")

if __name__ == '__main__':
    aplicar_patch_08()
