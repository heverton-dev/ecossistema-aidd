# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — Injetor Universal: Sincronizador Multi-Harness
=============================================================================
Depois que o Materializador escreve o artefato físico e seus espelhos, este
módulo faz a integração global: atualiza o catálogo 'CAPABILITIES.json' e,
quando o 'tipo' exigir, insere a linha de âncora correspondente em
'AGENTS.md' + templates multi-harness (para 'rule') ou registra um novo
padrão de intenção em 'src/core/intent_router.py' (para 'agent'). Todas as
inserções são feitas entre marcadores idempotentes: rodar duas vezes para o
mesmo 'nome' nunca duplica a linha.
"""

from __future__ import annotations

import datetime
import json
import os
from typing import Any, Dict, List

import hashlib

try:
    from result import Result
except ImportError:
    from core.result import Result


_MARCADOR_TABELA_INICIO = "<!-- AIDD_INJECTOR:COMPONENTES_INICIO -->"
_MARCADOR_TABELA_FIM = "<!-- AIDD_INJECTOR:COMPONENTES_FIM -->"
_MARCADOR_AGENTS_PY_INICIO = "# === INJECTOR:AGENTS START (mantido pelo Sincronizador de Harness — não editar manualmente) ==="
_MARCADOR_AGENTS_PY_FIM = "# === INJECTOR:AGENTS END ==="


def _timestamp() -> str:
    return datetime.datetime.now().isoformat()


def _atualizar_registry(registry_path: str, payload: Dict[str, Any], arquivos_criados: List[str]) -> Result:
    """Cria ou atualiza 'CAPABILITIES.json' com o novo componente (idempotente por nome)."""
    try:
        if os.path.isfile(registry_path):
            with open(registry_path, "r", encoding="utf-8") as f:
                catalogo = json.load(f)
        else:
            catalogo = {}

        root_dir = os.path.dirname(os.path.abspath(registry_path))
        arquivos_hashes: Dict[str, str] = {}
        for arq in arquivos_criados:
            abs_arq = os.path.abspath(arq) if os.path.isabs(arq) else os.path.abspath(os.path.join(root_dir, arq))
            if os.path.isfile(abs_arq):
                with open(abs_arq, "rb") as f_hash:
                    h = hashlib.sha256(f_hash.read()).hexdigest()
                rel_path = os.path.relpath(abs_arq, root_dir).replace("\\", "/")
                arquivos_hashes[rel_path] = h

        tipo = payload["tipo"]
        lista = catalogo.setdefault(tipo, [])
        lista[:] = [e for e in lista if e.get("nome") != payload["nome"]]
        lista.append({
            "nome": payload["nome"],
            "descricao": payload["descricao"],
            "camada_alvo": payload.get("camada_alvo"),
            "alvo_projeto": payload["alvo_projeto"],
            "arquivos": arquivos_criados,
            "arquivos_hashes": arquivos_hashes,
            "atualizado_em": _timestamp(),
        })

        os.makedirs(os.path.dirname(registry_path) or ".", exist_ok=True)
        with open(registry_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(catalogo, f, ensure_ascii=False, indent=2)
            f.write("\n")

        return Result.ok({"registry": registry_path, "tipo": tipo})
    except (OSError, json.JSONDecodeError) as e:
        return Result.fail(f"Falha ao atualizar registry {registry_path}: {e}", codigo="REGISTRY_FALHOU")


def verificar_sincronizacao(root_dir: str) -> Result:
    """Verifica se os arquivos registrados em CAPABILITIES.json existem e batem seus hashes SHA-256."""
    registry_path = os.path.join(root_dir, "CAPABILITIES.json")
    if not os.path.isfile(registry_path):
        return Result.ok({"verificados": 0, "problemas": []})

    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            catalogo = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return Result.fail(f"Falha ao ler registry {registry_path}: {e}", codigo="REGISTRY_INVALIDO")

    problemas: List[str] = []
    total_verificados = 0

    for tipo, componentes in catalogo.items():
        if not isinstance(componentes, list):
            continue
        for comp in componentes:
            if not isinstance(comp, dict):
                continue
            nome = comp.get("nome", "desconhecido")
            hashes = comp.get("arquivos_hashes", {})
            for rel_path, expected_hash in hashes.items():
                total_verificados += 1
                full_path = os.path.join(root_dir, rel_path)
                if not os.path.isfile(full_path):
                    problemas.append(f"Arquivo ausente: {rel_path} (componente '{nome}')")
                else:
                    try:
                        with open(full_path, "rb") as f_arq:
                            actual_hash = hashlib.sha256(f_arq.read()).hexdigest()
                        if actual_hash != expected_hash:
                            problemas.append(
                                f"Hash divergente em {rel_path} (componente '{nome}'): "
                                f"esperado {expected_hash}, obtido {actual_hash}"
                            )
                    except OSError as exc:
                        problemas.append(f"Erro ao ler {rel_path} (componente '{nome}'): {exc}")

    if problemas:
        return Result.fail(
            f"Sincronização divergente: {len(problemas)} problema(s) detectado(s).",
            codigo="SYNC_DIVERGENTE",
            detalhes={"problemas": problemas},
        )

    return Result.ok({"verificados": total_verificados, "problemas": []})


def _upsert_secao_componentes(caminho: str, payload: Dict[str, Any]) -> Result:
    """Insere (ou atualiza) a linha do componente na tabela 'Componentes Injetados' de 'caminho'."""
    try:
        if os.path.isfile(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                conteudo = f.read()
        else:
            conteudo = ""

        linha = f"| `{payload['nome']}` | {payload['descricao']} | `{payload['tipo']}` | {_timestamp()} |"

        if _MARCADOR_TABELA_INICIO not in conteudo:
            secao = (
                "\n\n## 📦 Componentes Injetados (Auto-Gerado pelo Injetor Universal)\n\n"
                f"{_MARCADOR_TABELA_INICIO}\n"
                "| Nome | Descrição | Tipo | Atualizado em |\n"
                "| :--- | :--- | :--- | :--- |\n"
                f"{linha}\n"
                f"{_MARCADOR_TABELA_FIM}\n"
            )
            novo_conteudo = conteudo.rstrip("\n") + secao
        else:
            inicio = conteudo.index(_MARCADOR_TABELA_INICIO)
            fim = conteudo.index(_MARCADOR_TABELA_FIM)
            bloco = conteudo[inicio:fim]
            linhas_existentes = [l for l in bloco.splitlines() if l.startswith("| `")]
            linhas_existentes = [l for l in linhas_existentes if not l.startswith(f"| `{payload['nome']}`")]
            linhas_existentes.append(linha)
            novo_bloco = (
                f"{_MARCADOR_TABELA_INICIO}\n"
                "| Nome | Descrição | Tipo | Atualizado em |\n"
                "| :--- | :--- | :--- | :--- |\n"
                + "\n".join(linhas_existentes) + "\n"
            )
            novo_conteudo = conteudo[:inicio] + novo_bloco + conteudo[fim:]

        os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
        with open(caminho, "w", encoding="utf-8", newline="\n") as f:
            f.write(novo_conteudo)

        return Result.ok({"anchor": caminho})
    except OSError as e:
        return Result.fail(f"Falha ao atualizar âncora {caminho}: {e}", codigo="ANCHOR_FALHOU")


def _registrar_padrao_intent_router(caminho: str, payload: Dict[str, Any]) -> Result:
    """Insere um novo IntentPattern PT-BR entre os marcadores AGENTS de 'intent_router.py'."""
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()

        if _MARCADOR_AGENTS_PY_INICIO not in conteudo or _MARCADOR_AGENTS_PY_FIM not in conteudo:
            return Result.fail(
                f"Marcadores de injeção de agentes não encontrados em {caminho}.",
                codigo="MARCADOR_AUSENTE",
            )

        nome = payload["nome"]
        assinatura = f'action="agent:{nome}"'
        if assinatura in conteudo:
            return Result.ok({"router_anchor": caminho, "acao": "ja_registrado"})

        descricao_escapada = payload["descricao"].replace('"', "'")
        nome_com_espacos = nome.replace("-", " ")
        regex_pattern = f"acionar?\\s+agente\\s+{nome_com_espacos}|agente\\s+de\\s+{nome_com_espacos}"
        template_rel = f"templates/agents/{nome}.md"
        # Nível de indentação 0 (módulo): inserido ANTES do marcador FIM, ou
        # seja, DEPOIS de '_INJECTED_AGENT_PATTERNS: List[...] = []' já ter
        # sido declarada — a chamada .append() sempre encontra a lista viva.
        linhas = [
            "_INJECTED_AGENT_PATTERNS.append(",
            "    IntentPattern(",
            f'        action="agent:{nome}",',
            "        regex=re.compile(",
            f'            r"{regex_pattern}",',
            "            re.IGNORECASE,",
            "        ),",
            f'        default_options={{"template": "{template_rel}"}},',
            f'        description="{descricao_escapada}",',
            "    )",
            ")",
            "",
        ]
        nova_entrada = "\n".join(linhas)

        inicio = conteudo.index(_MARCADOR_AGENTS_PY_FIM)
        novo_conteudo = conteudo[:inicio] + nova_entrada + conteudo[inicio:]

        with open(caminho, "w", encoding="utf-8", newline="\n") as f:
            f.write(novo_conteudo)

        return Result.ok({"router_anchor": caminho, "acao": "registrado"})
    except OSError as e:
        return Result.fail(f"Falha ao registrar padrão em {caminho}: {e}", codigo="ROUTER_ANCHOR_FALHOU")


def sincronizar(payload: Dict[str, Any], resolucao: Dict[str, Any], arquivos_criados: List[str]) -> Result:
    """Executa a integração global pós-materialização para um InjectorRequest já resolvido."""
    passos_ok: List[str] = []
    falhas: List[Dict[str, Any]] = []

    if resolucao.get("registry"):
        r = _atualizar_registry(resolucao["registry"], payload, arquivos_criados)
        (passos_ok if r.sucesso else falhas).append("registry" if r.sucesso else {"passo": "registry", "erro": r.erro})

    for anchor in resolucao.get("anchors", []):
        r = _upsert_secao_componentes(anchor, payload)
        (passos_ok if r.sucesso else falhas).append(anchor if r.sucesso else {"passo": anchor, "erro": r.erro})

    if resolucao.get("router_anchor"):
        r = _registrar_padrao_intent_router(resolucao["router_anchor"], payload)
        (passos_ok if r.sucesso else falhas).append(
            "router_anchor" if r.sucesso else {"passo": "router_anchor", "erro": r.erro}
        )

    if falhas:
        return Result.fail(
            f"Sincronização multi-harness parcialmente falhou: {len(falhas)} passo(s) com erro.",
            codigo="SINCRONIZACAO_PARCIAL",
            detalhes={"falhas": falhas, "passos_ok": passos_ok},
        )

    return Result.ok({"passos_sincronizados": passos_ok})
