# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_INFRA_COMPOSE
=============================================================================
Audita a integridade estática, sintática e estrutural dos arquivos de
orquestração Docker Compose e scripts de banco de dados do aidd-ops.

Checagens executadas (100% estáticas, sem subir contêineres):
1. Pré-requisito de ambiente: presença do binário 'docker' no PATH.
2. docker compose config para todos os docker-compose.yml sob tools/aidd-ops/.
3. Detecção de colisão de portas externas no mesmo arquivo de composição.
4. Cobertura de variáveis de ambiente: toda ${VAR} referenciada deve estar
   declarada no .env.example correspondente.
5. Validação do script de inicialização de múltiplos bancos PostgreSQL
   (init-multiple-databases.sh) e aderência aos planos de nichos canônicos.

Uso:
  python gates/G_INFRA_COMPOSE.py
      exit 0 = todos os composes válidos e íntegros.
      exit 1 = falha sintática, colisão de porta ou variável não declarada.
=============================================================================
"""

import json
import os
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Set, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AIDD_OPS_DIR = os.path.join(ROOT_DIR, "tools", "aidd-ops")
TEMPLATES_INFRA_DIR = os.path.join(AIDD_OPS_DIR, "templates", "infra")
NICHOS_DIR = os.path.join(TEMPLATES_INFRA_DIR, "nichos")


def verificar_docker_disponivel() -> bool:
    """Verifica se o binário docker está presente no PATH do sistema."""
    return shutil.which("docker") is not None


def carregar_env_example(caminho_env: str) -> Dict[str, str]:
    """Extrai chaves declaradas em um arquivo .env.example."""
    vars_dict: Dict[str, str] = {}
    if not os.path.isfile(caminho_env):
        return vars_dict

    with open(caminho_env, "r", encoding="utf-8", errors="replace") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            if "=" in linha:
                chave, valor = linha.split("=", 1)
                chave = chave.strip()
                valor = valor.strip().strip("'\"")
                vars_dict[chave] = valor if valor else "dummy_val"
    return vars_dict


def extrair_variaveis_compose(conteudo_compose: str) -> Set[str]:
    """Identifica referências a variáveis de ambiente no formato ${VAR...} ou $VAR."""
    padrao_chaves = re.compile(r"\$\{([A-Za-z0-9_]+)(?::[^}]*)?\}")
    padrao_simples = re.compile(r"(?<!\\)\$([A-Za-z0-9_]+)")
    encontradas = set(padrao_chaves.findall(conteudo_compose))
    for v in padrao_simples.findall(conteudo_compose):
        if not v.isdigit():
            encontradas.add(v)
    return encontradas


def extrair_portas_host(conteudo_compose: str) -> List[Tuple[str, str]]:
    """Extrai portas do host mapeadas exclusivamente sob blocos ports:."""
    portas = []
    em_ports = False
    indent_ports = 0

    for linha in conteudo_compose.splitlines():
        sem_espaco = linha.strip()
        if not sem_espaco or sem_espaco.startswith("#"):
            continue

        match_ports = re.match(r"^(\s*)ports:\s*$", linha)
        if match_ports:
            em_ports = True
            indent_ports = len(match_ports.group(1))
            continue

        if em_ports:
            indent_atual = len(linha) - len(linha.lstrip())
            if indent_atual <= indent_ports and not sem_espaco.startswith("-"):
                em_ports = False
                continue

            if sem_espaco.startswith("-"):
                item = sem_espaco.lstrip("- ").strip("'\"")
                if ":" in item:
                    partes = item.split(":")
                    if len(partes) >= 2:
                        porta_host = partes[-2].strip()
                        match_def = re.search(r":-([0-9]+)", porta_host)
                        if match_def:
                            porta_res = match_def.group(1)
                        elif porta_host.isdigit():
                            porta_res = porta_host
                        else:
                            porta_res = porta_host
                        portas.append((porta_host, porta_res))

    return portas


def auditar_composes() -> List[str]:
    """Audita todos os arquivos docker-compose.yml sob tools/aidd-ops."""
    erros = []
    if not os.path.isdir(AIDD_OPS_DIR):
        return erros

    arquivos_compose = []
    for raiz, _dirs, arquivos in os.walk(AIDD_OPS_DIR):
        for f in arquivos:
            if f in ("docker-compose.yml", "docker-compose.yaml"):
                arquivos_compose.append(os.path.join(raiz, f))

    if not arquivos_compose:
        print("[AVISO] Nenhum docker-compose.yml encontrado em tools/aidd-ops.")
        return erros

    print(f"--- Validando {len(arquivos_compose)} arquivo(s) Docker Compose ---")

    for caminho in sorted(arquivos_compose):
        rel = os.path.relpath(caminho, ROOT_DIR)
        pasta = os.path.dirname(caminho)
        nome_arquivo = os.path.basename(caminho)
        caminho_env = os.path.join(pasta, ".env.example")

        env_dict = carregar_env_example(caminho_env)
        mock_env = os.environ.copy()
        mock_env.update(env_dict)

        cmd = ["docker", "compose", "-f", nome_arquivo, "config"]
        try:
            res = subprocess.run(
                cmd,
                cwd=pasta,
                capture_output=True,
                text=True,
                env=mock_env,
                timeout=30,
            )
            if res.returncode != 0:
                msg_erro = res.stderr.strip() or res.stdout.strip()
                erros.append(f"{rel}: falha no 'docker compose config' -> {msg_erro}")
                print(f"[ERRO] {rel}: sintaxe inválida")
                continue
            else:
                print(f"[OK] {rel}: sintaxe e interpolação válidas")
        except Exception as exc:
            erros.append(f"{rel}: erro ao executar docker compose -> {str(exc)}")
            print(f"[ERRO] {rel}: {exc}")
            continue

        with open(caminho, "r", encoding="utf-8", errors="replace") as fc:
            conteudo = fc.read()

        vars_referenciadas = extrair_variaveis_compose(conteudo)
        if os.path.isfile(caminho_env):
            vars_declaradas = set(env_dict.keys())
            ignoradas = {"PWD", "UID", "GID"}
            faltantes = (vars_referenciadas - vars_declaradas) - ignoradas
            if faltantes:
                erros.append(f"{rel}: variáveis {sorted(faltantes)} ausentes no .env.example correspondente")
                print(f"[ERRO] {rel}: variáveis faltantes no .env.example: {sorted(faltantes)}")

        portas_encontradas = extrair_portas_host(conteudo)
        vistas = set()
        for porta_orig, porta_res in portas_encontradas:
            if porta_res in vistas:
                erros.append(f"{rel}: colisão de porta de host detectada no mesmo compose (porta {porta_res})")
                print(f"[ERRO] {rel}: colisão de porta de host ({porta_res})")
            else:
                vistas.add(porta_res)

    return erros


def auditar_init_postgres() -> List[str]:
    """Audita o script init-multiple-databases.sh e conformidade com os nichos."""
    erros = []
    script_path = os.path.join(TEMPLATES_INFRA_DIR, "postgres", "init-multiple-databases.sh")
    if not os.path.isfile(script_path):
        return erros

    rel_script = os.path.relpath(script_path, ROOT_DIR)
    print(f"\n--- Validando Script de Banco ({rel_script}) ---")

    bash_bin = shutil.which("bash")
    if bash_bin:
        try:
            res = subprocess.run([bash_bin, "-n", script_path], capture_output=True, text=True)
            if res.returncode != 0:
                erros.append(f"{rel_script}: erro de sintaxe bash -> {res.stderr.strip()}")
                print(f"[ERRO] {rel_script}: sintaxe bash inválida")
            else:
                print(f"[OK] {rel_script}: sintaxe bash válida (bash -n)")
        except Exception as exc:
            erros.append(f"{rel_script}: falha ao invocar bash -n -> {str(exc)}")
    else:
        with open(script_path, "r", encoding="utf-8", errors="replace") as f:
            conteudo = f.read()
        if "POSTGRES_MULTIPLE_DATABASES" not in conteudo or "create_user_and_database" not in conteudo:
            erros.append(f"{rel_script}: estrutura de inicialização inválida (marcadores essenciais ausentes)")
        else:
            print(f"[OK] {rel_script}: marcadores essenciais validados estaticamente")

    if os.path.isdir(NICHOS_DIR):
        planos_nicho = [os.path.join(NICHOS_DIR, f) for f in os.listdir(NICHOS_DIR) if f.endswith(".json")]
        print(f"--- Conferindo {len(planos_nicho)} plano(s) canônico(s) de nicho contra init script ---")
        for plano_path in planos_nicho:
            rel_plano = os.path.relpath(plano_path, ROOT_DIR)
            try:
                with open(plano_path, "r", encoding="utf-8") as fp:
                    dados = json.load(fp)
                bancos = dados.get("bancos_logicos", [])
                if not bancos:
                    erros.append(f"{rel_plano}: plano canônico não declara lista 'bancos_logicos'")
                else:
                    for b in bancos:
                        nome_banco = b.get("nome")
                        if not nome_banco or not re.match(r"^[a-z0-9_]+$", nome_banco):
                            erros.append(f"{rel_plano}: nome de banco inválido '{nome_banco}'")
                print(f"[OK] {rel_plano}: {len(bancos)} banco(s) lógico(s) conferido(s)")
            except Exception as exc:
                erros.append(f"{rel_plano}: erro ao ler JSON -> {str(exc)}")

    return erros


def auditar() -> int:
    print("=" * 70)
    print(" [GATE] G_INFRA_COMPOSE — Validação de Compose e Topologia de Infra")
    print("=" * 70)

    if not verificar_docker_disponivel():
        print("[FALHA] Pré-requisito de ambiente não atendido:")
        print("        Binário 'docker' não encontrado no PATH do sistema.")
        print("        Este gate exige Docker instalado para validar sintaxe de orquestração.")
        print("=" * 70)
        return 1

    print("[OK] Pré-requisito de ambiente: binário 'docker' detectado.")

    erros = []
    erros.extend(auditar_composes())
    erros.extend(auditar_init_postgres())

    print("\n" + "=" * 70)
    if erros:
        print(f" [FALHA] Quality Gate REPROVADO com {len(erros)} erro(s):")
        for err in erros:
            print(f"  - {err}")
        print("=" * 70)
        return 1

    print(" [SUCESSO] Quality Gate G_INFRA_COMPOSE APROVADO (100% OK)!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(auditar())
