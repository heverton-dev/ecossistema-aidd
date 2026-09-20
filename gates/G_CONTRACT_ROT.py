#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_CONTRACT_ROT (ISSUE-0014 & Lei Canônica #10)
=============================================================================
Portão determinístico de prevenção de Contract Rot.
Compara a árvore de rotas e formatos de resposta expostos pelo servidor em execução
com o contrato canônico openapi.json commitado.

Audita:
1. Existência e enumeração a partir do servidor em execução (HTTP real).
2. Conformidade de caminhos (paths) e métodos HTTP (GET, POST, PUT, DELETE, PATCH).
3. Status codes de resposta declarados e servidos para cada rota.
4. Parâmetros de consulta (query params): presença, obrigatoriedade e tipo.
5. Tipos de campos (field types) nos schemas de request body e responses.
6. Trava conhecida: validação do caminho servido real /docs (em vez do histórico /swagger).

Saída:
  exit 0 = Zero divergências entre servidor em execução e openapi.json commitado.
  exit 1 = Ao menos uma divergência detectada, nomeando a rota e elemento divergente.
=============================================================================
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def encontrar_porta_livre() -> int:
    """Retorna uma porta TCP livre alocada efemeramente pelo SO."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def extrair_campos_schema(schema_obj: Any) -> Dict[str, str]:
    """Extrai recursivamente o mapeamento {nome_campo: tipo} de um JSON schema OpenAPI."""
    campos: Dict[str, str] = {}
    if not isinstance(schema_obj, dict):
        return campos

    props = schema_obj.get("properties")
    if isinstance(props, dict):
        for campo, prop_def in props.items():
            if isinstance(prop_def, dict):
                tipo = prop_def.get("type", "desconhecido")
                campos[campo] = str(tipo)
                # Sub-objetos
                if tipo == "object" and "properties" in prop_def:
                    sub_campos = extrair_campos_schema(prop_def)
                    for sub_nome, sub_tipo in sub_campos.items():
                        campos[f"{campo}.{sub_nome}"] = sub_tipo
            else:
                campos[campo] = "desconhecido"

    # Caso schema seja array de objetos
    if schema_obj.get("type") == "array" and isinstance(schema_obj.get("items"), dict):
        sub_campos = extrair_campos_schema(schema_obj["items"])
        for sub_nome, sub_tipo in sub_campos.items():
            campos[f"[item].{sub_nome}"] = sub_tipo

    return campos


def extrair_campos_de_content(content_obj: Any) -> Dict[str, str]:
    """Extrai tipos de campos de blocos content (ex: application/json)."""
    campos: Dict[str, str] = {}
    if not isinstance(content_obj, dict):
        return campos

    app_json = content_obj.get("application/json")
    if isinstance(app_json, dict):
        schema = app_json.get("schema")
        if schema:
            campos.update(extrair_campos_schema(schema))
        # Se schema não estiver explícito mas houver example estruturado
        example = app_json.get("example")
        if isinstance(example, dict) and not campos:
            for k, v in example.items():
                t = type(v).__name__
                if t == "str":
                    t = "string"
                elif t == "int":
                    t = "integer"
                elif t == "bool":
                    t = "boolean"
                elif t == "float":
                    t = "number"
                elif t == "dict":
                    t = "object"
                elif t == "list":
                    t = "array"
                campos[k] = t
        elif isinstance(example, list) and len(example) > 0 and isinstance(example[0], dict) and not campos:
            for k, v in example[0].items():
                t = type(v).__name__
                if t == "str":
                    t = "string"
                elif t == "int":
                    t = "integer"
                elif t == "bool":
                    t = "boolean"
                elif t == "float":
                    t = "number"
                elif t == "dict":
                    t = "object"
                elif t == "list":
                    t = "array"
                campos[f"[item].{k}"] = t
    return campos


def diff_specs(live_spec: Dict[str, Any], committed_spec: Dict[str, Any]) -> Tuple[List[str], Dict[str, int]]:
    """Compara deterministicamente a spec do servidor vivo com a spec commitada.

    Retorna:
      (lista_de_divergencias, estatisticas_verificadas)
    """
    divergencias: List[str] = []
    stats = {
        "rotas": 0,
        "metodos": 0,
        "status_codes": 0,
        "query_params": 0,
        "campos_schema": 0,
    }

    live_paths = live_spec.get("paths", {})
    comm_paths = committed_spec.get("paths", {})

    all_path_keys = sorted(set(live_paths.keys()) | set(comm_paths.keys()))
    stats["rotas"] = len(all_path_keys)

    for path in all_path_keys:
        if path not in comm_paths:
            divergencias.append(
                f"Rota '{path}': presente no servidor em execução, mas ausente no openapi.json commitado."
            )
            continue
        if path not in live_paths:
            divergencias.append(
                f"Rota '{path}': declarada no openapi.json commitado, mas ausente no servidor em execução."
            )
            continue

        live_methods_dict = live_paths[path]
        comm_methods_dict = comm_paths[path]

        http_verbs = {"get", "post", "put", "delete", "patch", "options", "head"}
        live_methods = {k.lower() for k in live_methods_dict.keys() if k.lower() in http_verbs}
        comm_methods = {k.lower() for k in comm_methods_dict.keys() if k.lower() in http_verbs}

        all_methods = sorted(live_methods | comm_methods)
        stats["metodos"] += len(all_methods)

        for method in all_methods:
            method_upper = method.upper()
            rota_id = f"[{method_upper}] {path}"

            if method not in comm_methods:
                divergencias.append(
                    f"Rota {rota_id}: método presente no servidor em execução, mas ausente no openapi.json commitado."
                )
                continue
            if method not in live_methods:
                divergencias.append(
                    f"Rota {rota_id}: método declarado no openapi.json commitado, mas ausente no servidor em execução."
                )
                continue

            live_op = live_methods_dict[method]
            comm_op = comm_methods_dict[method]

            # 1. Comparar Status Codes de Resposta
            live_responses = {str(k) for k in live_op.get("responses", {}).keys()}
            comm_responses = {str(k) for k in comm_op.get("responses", {}).keys()}
            stats["status_codes"] += max(len(live_responses), len(comm_responses))

            if live_responses != comm_responses:
                divergencias.append(
                    f"Rota {rota_id}: divergência de status codes de resposta. "
                    f"Servidor vivo={sorted(live_responses)} vs Commitado={sorted(comm_responses)}."
                )

            # 2. Comparar Query Params
            live_params = live_op.get("parameters", [])
            comm_params = comm_op.get("parameters", [])

            live_qp = {
                p["name"]: {
                    "required": bool(p.get("required", False)),
                    "type": str(p.get("schema", {}).get("type", "string")),
                }
                for p in live_params
                if isinstance(p, dict) and p.get("in") == "query" and "name" in p
            }
            comm_qp = {
                p["name"]: {
                    "required": bool(p.get("required", False)),
                    "type": str(p.get("schema", {}).get("type", "string")),
                }
                for p in comm_params
                if isinstance(p, dict) and p.get("in") == "query" and "name" in p
            }
            stats["query_params"] += max(len(live_qp), len(comm_qp))

            all_qp_names = sorted(set(live_qp.keys()) | set(comm_qp.keys()))
            for qp_name in all_qp_names:
                if qp_name not in comm_qp:
                    divergencias.append(
                        f"Rota {rota_id}: query param '{qp_name}' exposto pelo servidor vivo, mas ausente no openapi.json commitado."
                    )
                elif qp_name not in live_qp:
                    divergencias.append(
                        f"Rota {rota_id}: query param '{qp_name}' declarado no commitado, mas ausente no servidor vivo."
                    )
                else:
                    live_def = live_qp[qp_name]
                    comm_def = comm_qp[qp_name]
                    if live_def["type"] != comm_def["type"]:
                        divergencias.append(
                            f"Rota {rota_id}: tipo do query param '{qp_name}' diverge. "
                            f"Servidor vivo='{live_def['type']}' vs Commitado='{comm_def['type']}'."
                        )
                    if live_def["required"] != comm_def["required"]:
                        divergencias.append(
                            f"Rota {rota_id}: obrigatoriedade ('required') do query param '{qp_name}' diverge. "
                            f"Servidor vivo={live_def['required']} vs Commitado={comm_def['required']}."
                        )

            # 3. Comparar Field Types (Request Body)
            live_rb = live_op.get("requestBody", {}).get("content", {}) if isinstance(live_op.get("requestBody"), dict) else {}
            comm_rb = comm_op.get("requestBody", {}).get("content", {}) if isinstance(comm_op.get("requestBody"), dict) else {}

            live_req_fields = extrair_campos_de_content(live_rb)
            comm_req_fields = extrair_campos_de_content(comm_rb)
            stats["campos_schema"] += max(len(live_req_fields), len(comm_req_fields))

            all_req_fields = sorted(set(live_req_fields.keys()) | set(comm_req_fields.keys()))
            for f_name in all_req_fields:
                if f_name not in comm_req_fields:
                    divergencias.append(
                        f"Rota {rota_id}: campo '{f_name}' no requestBody exposto pelo servidor vivo, mas ausente no openapi.json commitado."
                    )
                elif f_name not in live_req_fields:
                    divergencias.append(
                        f"Rota {rota_id}: campo '{f_name}' no requestBody declarado no commitado, mas ausente no servidor vivo."
                    )
                else:
                    lt = live_req_fields[f_name]
                    ct = comm_req_fields[f_name]
                    if lt != ct:
                        divergencias.append(
                            f"Rota {rota_id}: tipo do campo '{f_name}' no requestBody diverge. "
                            f"Servidor vivo='{lt}' vs Commitado='{ct}'."
                        )

            # 4. Comparar Field Types (Responses 200/201)
            for sc in ("200", "201"):
                live_resp_c = live_op.get("responses", {}).get(sc, {}).get("content", {})
                comm_resp_c = comm_op.get("responses", {}).get(sc, {}).get("content", {})

                live_res_fields = extrair_campos_de_content(live_resp_c)
                comm_res_fields = extrair_campos_de_content(comm_resp_c)
                stats["campos_schema"] += max(len(live_res_fields), len(comm_res_fields))

                all_res_fields = sorted(set(live_res_fields.keys()) | set(comm_res_fields.keys()))
                for f_name in all_res_fields:
                    if f_name not in comm_res_fields:
                        divergencias.append(
                            f"Rota {rota_id}: campo '{f_name}' na resposta {sc} presente no servidor vivo, mas ausente no openapi.json commitado."
                        )
                    elif f_name not in live_res_fields:
                        divergencias.append(
                            f"Rota {rota_id}: campo '{f_name}' na resposta {sc} declarado no commitado, mas ausente no servidor vivo."
                        )
                    else:
                        lt = live_res_fields[f_name]
                        ct = comm_res_fields[f_name]
                        if lt != ct:
                            divergencias.append(
                                f"Rota {rota_id}: tipo do campo '{f_name}' na resposta {sc} diverge. "
                                f"Servidor vivo='{lt}' vs Commitado='{ct}'."
                            )

    return divergencias, stats


def coletar_spec_servidor_vivo(base_url: str, timeout_s: float = 8.0) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Acessa o servidor em execução via HTTP real e coleta a spec /openapi.json."""
    erros: List[str] = []
    base_url = base_url.rstrip("/")
    openapi_url = f"{base_url}/openapi.json"

    # Sondagem ativa com retry
    deadline = time.time() + timeout_s
    ultimo_erro = ""
    conteudo_bytes = None

    while time.time() < deadline:
        try:
            req = urllib.request.Request(openapi_url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    conteudo_bytes = resp.read()
                    break
        except Exception as e:
            ultimo_erro = str(e)
            time.sleep(0.2)

    if conteudo_bytes is None:
        erros.append(
            f"Falha ao conectar ao servidor vivo em {openapi_url} após {timeout_s:.1f}s. Último erro: {ultimo_erro}"
        )
        return None, erros

    try:
        spec = json.loads(conteudo_bytes.decode("utf-8"))
        if not isinstance(spec, dict) or "paths" not in spec:
            erros.append(f"Servidor vivo retornou JSON OpenAPI inválido em {openapi_url}.")
            return None, erros
        return spec, erros
    except json.JSONDecodeError as e:
        erros.append(f"Erro ao decodificar JSON de {openapi_url}: {e}")
        return None, erros


def verificar_quarteto_rotas_reais(base_url: str) -> List[str]:
    """Verifica que o servidor vivo atende as rotas canônicas do Quarteto Sine Qua Non.

    Trava conhecida (ISSUE-0001 / ISSUE-0014): o Swagger é servido em /docs, NÃO /swagger.
    """
    avisos_ou_erros: List[str] = []
    base_url = base_url.rstrip("/")

    # Rotas canônicas obrigatórias servidas pelo backend
    rotas_quarteto = [
        ("/docs", "Swagger Studio"),
        ("/webhooks", "Webhook Studio"),
        ("/mcp", "MCP Portal"),
        ("/docs/guia", "Guia do Utilizador"),
    ]

    for rota, nome in rotas_quarteto:
        url = f"{base_url}{rota}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status != 200:
                    avisos_ou_erros.append(
                        f"Quarteto Sine Qua Non: rota '{rota}' ({nome}) retornou status HTTP {resp.status} (esperado 200)."
                    )
        except urllib.error.HTTPError as he:
            avisos_ou_erros.append(
                f"Quarteto Sine Qua Non: rota '{rota}' ({nome}) falhou com status {he.code}."
            )
        except Exception as e:
            # Nem todos os projetos geram docs/guia como rota estática; se for 404 registramos
            avisos_ou_erros.append(f"Quarteto Sine Qua Non: rota '{rota}' inacessível ({e}).")

    return avisos_ou_erros


def auditar_servidor_e_spec(
    base_url: str, committed_spec_path: str, checar_quarteto: bool = True
) -> Tuple[int, List[str], Dict[str, int]]:
    """Audita o servidor em execução contra um openapi.json commitado."""
    erros: List[str] = []

    if not os.path.isfile(committed_spec_path):
        return 1, [f"Arquivo OpenAPI commitado não encontrado: {committed_spec_path}"], {}

    try:
        with open(committed_spec_path, "r", encoding="utf-8") as f:
            committed_spec = json.load(f)
    except Exception as e:
        return 1, [f"Erro ao carregar openapi.json commitado ({committed_spec_path}): {e}"], {}

    live_spec, erros_conexao = coletar_spec_servidor_vivo(base_url)
    if live_spec is None:
        return 1, erros_conexao, {}

    # Diff determinístico
    divergencias, stats = diff_specs(live_spec, committed_spec)

    # Checagem complementar do Quarteto Sine Qua Non (caminho real /docs)
    if checar_quarteto:
        erros_quarteto = verificar_quarteto_rotas_reais(base_url)
        divergencias.extend(erros_quarteto)

    codigo_saida = 0 if not divergencias else 1
    return codigo_saida, divergencias, stats


def auditar_projeto(project_dir: str) -> Tuple[int, List[str], Dict[str, int]]:
    """Localiza server.py e openapi.json no projeto, sobe o servidor em porta efêmera e audita."""
    project_dir = os.path.abspath(project_dir)

    # Procura server.py
    candidatos_server = [
        os.path.join(project_dir, "src", "server.py"),
        os.path.join(project_dir, "server.py"),
    ]
    server_script = next((c for c in candidatos_server if os.path.isfile(c)), None)
    if not server_script:
        return 1, [f"Nenhum script server.py encontrado em {project_dir}"], {}

    # Procura openapi.json commitado
    candidatos_spec = [
        os.path.join(project_dir, "openapi.json"),
        os.path.join(project_dir, "docs", "openapi.json"),
        os.path.join(project_dir, "src", "openapi.json"),
    ]
    spec_path = next((c for c in candidatos_spec if os.path.isfile(c)), None)
    if not spec_path:
        return 1, [f"Nenhum arquivo openapi.json commitado encontrado em {project_dir}"], {}

    porta = encontrar_porta_livre()
    env = dict(os.environ)
    env["PORT"] = str(porta)
    env["PYTHONUNBUFFERED"] = "1"

    # Sobe o servidor como subprocesso
    server_cwd = os.path.dirname(server_script)
    proc = subprocess.Popen(
        [sys.executable, server_script],
        env=env,
        cwd=server_cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    base_url = f"http://127.0.0.1:{porta}"
    try:
        codigo, erros, stats = auditar_servidor_e_spec(base_url, spec_path, checar_quarteto=True)
        return codigo, erros, stats
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=3.0)
        except Exception:
            proc.kill()


def descobrir_projetos_no_repositorio(root_dir: str = ROOT_DIR) -> List[str]:
    """Descobre diretórios que contenham openapi.json e server.py."""
    projetos = []
    for root, dirs, files in os.walk(root_dir):
        # Evitar diretórios pesados
        if any(ign in root for ign in [".git", ".venv", "node_modules", "__pycache__", "site-packages"]):
            continue
        if "openapi.json" in files:
            # Verifica se há server.py no mesmo diretório ou em src/
            if os.path.isfile(os.path.join(root, "server.py")) or os.path.isfile(os.path.join(root, "src", "server.py")):
                projetos.append(root)
    return projetos


def main() -> int:
    parser = argparse.ArgumentParser(
        description="G_CONTRACT_ROT: Prevenção determinística de Contract Rot entre servidor vivo e openapi.json."
    )
    parser.add_argument("--url", default="", help="URL base de servidor HTTP já em execução.")
    parser.add_argument("--committed-spec", default="", help="Caminho do openapi.json commitado de referência.")
    parser.add_argument("--projeto", default="", help="Caminho da pasta do projeto contendo server.py e openapi.json.")
    args = parser.parse_args()

    print("=" * 72)
    print(" [GATE] G_CONTRACT_ROT — Auditoria de Contract Rot (ISSUE-0014 & Lei #10)")
    print("=" * 72)

    # Modo 1: URL explícita e spec commitada
    if args.url:
        if not args.committed_spec:
            print("[ERRO] Ao informar --url, é obrigatório informar --committed-spec.")
            return 1
        codigo, divergencias, stats = auditar_servidor_e_spec(args.url, args.committed_spec)
    # Modo 2: Projeto explícito
    elif args.projeto:
        codigo, divergencias, stats = auditar_projeto(args.projeto)
    # Modo 3: Auto-descoberta no repositório
    else:
        projetos = descobrir_projetos_no_repositorio(ROOT_DIR)
        if not projetos:
            print("[INFO] Nenhum projeto com openapi.json e server.py encontrado para auditoria.")
            print("[INFO] Rótulo honesto: verificação concluída sem projetos alvos detectados.")
            return 0

        print(f"[INFO] {len(projetos)} projeto(s) com openapi.json encontrado(s) para auditoria:")
        todas_divergencias = []
        stats_totais = {"rotas": 0, "metodos": 0, "status_codes": 0, "query_params": 0, "campos_schema": 0}

        for p in projetos:
            rel = os.path.relpath(p, ROOT_DIR)
            print(f"\n--- Auditando Projeto: {rel} ---")
            cod, divs, st = auditar_projeto(p)
            for k, v in st.items():
                stats_totais[k] = stats_totais.get(k, 0) + v
            if cod != 0 or divs:
                todas_divergencias.extend([f"[{rel}] {d}" for d in divs])

        codigo = 0 if not todas_divergencias else 1
        divergencias = todas_divergencias
        stats = stats_totais

    # Exibição Honestidade de Rótulo (Lei #8): relata estritamente o que foi verificado
    print("\n--- Estatísticas da Verificação Determinística ---")
    print(f"  Rotas auditadas:             {stats.get('rotas', 0)}")
    print(f"  Métodos HTTP verificados:    {stats.get('metodos', 0)}")
    print(f"  Status codes comparados:     {stats.get('status_codes', 0)}")
    print(f"  Query params comparados:     {stats.get('query_params', 0)}")
    print(f"  Campos de schema checados:   {stats.get('campos_schema', 0)}")

    if divergencias:
        print("\n" + "=" * 72)
        print(f" [BLOQUEIO] {len(divergencias)} divergência(s) de contrato detectada(s) (Contract Rot):")
        print("=" * 72)
        for div in divergencias:
            print(f"  [DIVERGÊNCIA] {div}")
        print("\n" + "=" * 72)
        print(" REGRA CANÔNICA VIOLADA (ISSUE-0014 & Lei #10):")
        print(" Rotas reais servidas devem ser 100% fiéis ao openapi.json commitado.")
        print(" Atualize o contrato commitado ou corrija a implementação da rota.")
        print("=" * 72)
        return 1

    print("\n" + "=" * 72)
    print(" [APROVADO] Zero divergências entre rotas servidas e contrato openapi.json.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
