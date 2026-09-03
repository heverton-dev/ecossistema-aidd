#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCAFFOLDS — Geradores de conteudo real por tipo de componente
aidd-generator — Injetor Universal de Componentes

Cada funcao devolve o texto completo e funcional de um arquivo, pronto
para materializacao. Nenhum scaffold contem stubs (`pass`, `TODO`,
`NotImplementedError`) — o MCP gerado, por exemplo, e um servidor stdio
JSON-RPC minimo porem executavel.
"""

import json
import sys
from datetime import datetime, timezone

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def _titulo(nome: str) -> str:
    return nome.replace("-", " ").replace("_", " ").title()


def gerar_skill(nome: str, descricao: str) -> str:
    """Gera o conteudo de um `SKILL.md` (formato usado por `.claude/skills/*/SKILL.md`)."""
    titulo = _titulo(nome)
    return f"""# Skill: {titulo} v1.0

> {descricao}

---

## 🎯 O que faz

Esta skill foi materializada pelo Injetor Universal de Componentes
(`scripts/core/injector/`) do aidd-generator. Ela cobre:

- {descricao}

---

## 📋 Uso

### No Chat (Claude Code)

```
/{nome}
```

### No Terminal

```bash
python scripts/aidd_inject.py inspect skill {nome}
```

---

## 📦 Compatibilidade

- Claude Code ✅
- Qualquer harness compativel com `.claude/skills/` ✅

---

**Versao:** 1.0
**Gerado em:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
**Status:** 🟢 PRONTO PARA USO
"""


def gerar_rule(nome: str, descricao: str) -> str:
    """Gera o conteudo de uma regra (`rules/{nome}.md`)."""
    titulo = _titulo(nome)
    return f"""# Regra: {titulo}

**Status:** Ativa
**Gerado em:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

---

## Definicao

{descricao}

## Aplicacao

Esta regra e referenciada em `AGENTS.md` (secao "Registro de Componentes
Injetados") e deve ser observada por qualquer agente/harness operando
neste repositorio.

## Verificacao

Regras injetadas nao possuem gate mecanico proprio por padrao; caso esta
regra exija validacao automatizada, crie um gate dedicado em
`scripts/gates/` e registre-o em `scripts/verificar_gates.py`.
"""


def gerar_spec(nome: str, descricao: str) -> str:
    """Gera o conteudo de uma especificacao (`docs/specs/{nome}.md`)."""
    titulo = _titulo(nome)
    return f"""# Spec: {titulo}

**Status:** Rascunho
**Gerado em:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

---

## Objetivo

{descricao}

## Escopo

- [ ] Definir criterios de sucesso mecanicos
- [ ] Definir arquivos/modulos afetados
- [ ] Definir plano de testes

## Rastreamento

Esta spec foi registrada como etapa em `PLANO-EXECUCAO-ESTRUTURADO.json`
pelo Injetor Universal de Componentes.
"""


def gerar_config(nome: str, descricao: str) -> str:
    """Gera o conteudo de um arquivo de configuracao (`config/{nome}.json`)."""
    payload = {
        "nome": nome,
        "descricao": descricao,
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "gerado_por": "aidd_core_injector",
        "parametros": {},
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def gerar_mcp(nome: str, descricao: str) -> str:
    """
    Gera o conteudo de um servidor MCP minimo (`mcps/{nome}/server.py`).

    Implementa um loop JSON-RPC 2.0 sobre stdio em Python puro (sem SDK
    `mcp`, que nao esta em requirements.txt), suportando os metodos
    `initialize`, `tools/list` e `tools/call` — funcional, nao um stub.
    """
    titulo = _titulo(nome)
    nome_tool = nome.replace("-", "_")
    return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP: {titulo}

{descricao}

Servidor MCP minimo (JSON-RPC 2.0 sobre stdio, biblioteca padrao apenas).
Gerado pelo Injetor Universal de Componentes (aidd-generator).

Uso:
    python server.py
    (le requisicoes JSON-RPC, uma por linha, de stdin; escreve respostas
    JSON-RPC, uma por linha, em stdout)
"""

import json
import sys

NOME_SERVIDOR = "{nome}"
DESCRICAO_SERVIDOR = {descricao!r}

TOOLS = [
    {{
        "name": "{nome_tool}",
        "description": DESCRICAO_SERVIDOR,
        "inputSchema": {{
            "type": "object",
            "properties": {{
                "consulta": {{"type": "string", "description": "Entrada da consulta"}}
            }},
            "required": ["consulta"],
        }},
    }}
]


def executar_tool(nome_tool_chamada, argumentos):
    """Executa a unica tool exposta por este servidor."""
    if nome_tool_chamada != "{nome_tool}":
        raise ValueError(f"tool desconhecida: {{nome_tool_chamada}}")

    consulta = argumentos.get("consulta", "")
    return {{
        "servidor": NOME_SERVIDOR,
        "consulta_recebida": consulta,
        "resultado": f"[{{NOME_SERVIDOR}}] processado: {{consulta}}",
    }}


def processar_requisicao(req):
    """Processa uma unica requisicao JSON-RPC 2.0 e devolve a resposta."""
    metodo = req.get("method")
    req_id = req.get("id")

    if metodo == "initialize":
        resultado = {{
            "protocolVersion": "2024-11-05",
            "serverInfo": {{"name": NOME_SERVIDOR, "version": "1.0"}},
            "capabilities": {{"tools": {{}}}},
        }}
    elif metodo == "tools/list":
        resultado = {{"tools": TOOLS}}
    elif metodo == "tools/call":
        params = req.get("params", {{}})
        resultado = executar_tool(params.get("name"), params.get("arguments", {{}}))
    else:
        return {{
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {{"code": -32601, "message": f"metodo nao suportado: {{metodo}}"}},
        }}

    return {{"jsonrpc": "2.0", "id": req_id, "result": resultado}}


def main():
    """Loop principal: le requisicoes de stdin, escreve respostas em stdout."""
    for linha in sys.stdin:
        linha = linha.strip()
        if not linha:
            continue
        try:
            req = json.loads(linha)
            resp = processar_requisicao(req)
        except (json.JSONDecodeError, ValueError) as exc:
            resp = {{"jsonrpc": "2.0", "id": None, "error": {{"code": -32700, "message": str(exc)}}}}
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
'''
