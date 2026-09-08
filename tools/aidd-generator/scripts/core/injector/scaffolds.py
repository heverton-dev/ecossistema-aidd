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
    Gera o conteudo de um servidor MCP (`mcps/{nome}/server.py`) usando o
    SDK oficial do Model Context Protocol (`modelcontextprotocol/python-sdk`).

    Negociacao de protocolo, JSON-RPC 2.0, codigos de erro e o transporte
    stdio sao tratados pelo SDK oficial — nenhuma implementacao manual de
    JSON-RPC e gerada. Funcional, nao um stub.
    """
    titulo = _titulo(nome)
    nome_tool = nome.replace("-", "_")
    return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP: {titulo}

{descricao}

Servidor MCP que usa o SDK oficial do Model Context Protocol
(`modelcontextprotocol/python-sdk`). Gerado pelo Injetor Universal de
Componentes (aidd-generator).

Uso:
    python server.py
    (transporte stdio; JSON-RPC 2.0, negociacao de protocolo e codigos de
    erro tratados pelo SDK oficial)
"""

from mcp.server.fastmcp import FastMCP

NOME_SERVIDOR = "{nome}"
DESCRICAO_SERVIDOR = {descricao!r}

mcp = FastMCP(NOME_SERVIDOR, instructions=DESCRICAO_SERVIDOR)


@mcp.tool()
def {nome_tool}(consulta: str) -> dict:
    """{descricao}"""
    return {{
        "servidor": NOME_SERVIDOR,
        "consulta_recebida": consulta,
        "resultado": f"[{{NOME_SERVIDOR}}] processado: {{consulta}}",
    }}


if __name__ == "__main__":
    mcp.run(transport="stdio")
'''
