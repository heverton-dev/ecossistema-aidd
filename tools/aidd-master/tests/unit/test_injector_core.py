# -*- coding: utf-8 -*-
"""
Suíte Pytest do Injetor Universal de Componentes (schema, perfis, detector
híbrido, materializador transacional, sincronizador multi-harness e a
integração real via CLI/IntentRouter). Cobre as 6 Fases do plano mestre:

  Fase 1 — Contrato: schema rejeita payload incompleto/tipo inválido.
  Fase 2 — Perfis: resolução exata de diretórios por tipo em 'aidd-master'.
  Fase 3 — Detector + Materializador: heurística PT-BR e rollback transacional.
  Fase 4 — Sincronizador: catálogo + âncoras idempotentes multi-harness.
  Fase 5 — CLI + IntentRouter: comando explícito e frase PT-BR ponta a ponta.
  Fase 6 — Este próprio arquivo é o gate mecânico executado por G_INJECT.py.
"""

import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_SRC = os.path.join(_ROOT, "src")
_CORE = os.path.join(_SRC, "core")
for _p in (_SRC, _CORE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import profiles_registry  # noqa: E402
import detector_camada  # noqa: E402
import materializador  # noqa: E402
import sincronizador_harness  # noqa: E402
from intent_router import IntentRouter  # noqa: E402


# ---------------------------------------------------------------------------
# Fase 1 — Contrato Universal & Schema Draft 2020-12
# ---------------------------------------------------------------------------

def test_schema_draft_2020_12_carrega_e_exige_6_campos():
    schema = profiles_registry.carregar_schema()
    assert schema["$schema"].endswith("2020-12/schema")
    assert set(schema["required"]) == {"tipo", "nome", "descricao", "alvo_projeto"}
    for campo in ("tipo", "nome", "descricao", "camada_alvo", "conteudo", "alvo_projeto"):
        assert campo in schema["properties"], f"campo '{campo}' ausente do contrato"


def test_gate_rejeita_payload_incompleto():
    resultado = profiles_registry.validar_payload({"tipo": "skill", "nome": "x"})
    assert resultado.sucesso is False
    assert resultado.codigo == "PAYLOAD_INCOMPLETO"
    assert "descricao" in resultado.detalhes["faltantes"]


def test_gate_rejeita_tipo_invalido():
    payload = {"tipo": "tipo_inventado", "nome": "x", "descricao": "abc", "alvo_projeto": "aidd-master"}
    resultado = profiles_registry.validar_payload(payload)
    assert resultado.sucesso is False
    assert resultado.codigo == "TIPO_INVALIDO"


def test_gate_rejeita_nome_fora_de_kebab_case():
    payload = {"tipo": "skill", "nome": "Nome_Invalido!", "descricao": "abc", "alvo_projeto": "aidd-master"}
    resultado = profiles_registry.validar_payload(payload)
    assert resultado.sucesso is False
    assert resultado.codigo == "NOME_INVALIDO"


def test_gate_aceita_payload_completo():
    payload = {"tipo": "skill", "nome": "exemplo-valido", "descricao": "Descrição de teste válida.", "alvo_projeto": "aidd-master"}
    resultado = profiles_registry.validar_payload(payload)
    assert resultado.sucesso is True


def test_gate_aceita_payload_hook():
    payload = {"tipo": "hook", "nome": "meu-hook", "descricao": "Hook de teste válido.", "alvo_projeto": "aidd-master"}
    resultado = profiles_registry.validar_payload(payload)
    assert resultado.sucesso is True


# ---------------------------------------------------------------------------
# Fase 2 — Matriz de Perfis (resolução exata de diretórios)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tipo,sufixo_esperado", [
    ("skill", os.path.join(".skills", "meu-componente", "SKILL.md")),
    ("mcp", os.path.join("src", "core", "mcp", "meu-componente.py")),
    ("rule", os.path.join("templates", "rules", "meu-componente.md")),
    ("spec", os.path.join("docs", "specs", "meu-componente.md")),
    ("config", os.path.join("templates", "core", "config", "meu-componente.json")),
    ("agent", os.path.join("templates", "agents", "meu-componente.md")),
    ("hook", os.path.join(".agent", "hooks", "meu-componente", "meu-componente.json")),
])
def test_perfis_resolvem_destino_exato_por_tipo(tmp_path, tipo, sufixo_esperado):
    payload = {"tipo": tipo, "nome": "meu-componente", "descricao": "abc", "alvo_projeto": "aidd-master"}
    resultado = profiles_registry.resolver_destinos(payload, str(tmp_path))
    assert resultado.sucesso is True
    assert resultado.valor["dest_principal"] == os.path.join(str(tmp_path), sufixo_esperado)


def test_perfis_rejeita_projeto_alvo_nao_suportado(tmp_path):
    payload = {"tipo": "skill", "nome": "x", "descricao": "abc", "alvo_projeto": "aidd-forge"}
    resultado = profiles_registry.resolver_destinos(payload, str(tmp_path))
    assert resultado.sucesso is False
    assert resultado.codigo == "PROJETO_NAO_SUPORTADO"


def test_perfil_skill_inclui_espelhos_multi_harness(tmp_path):
    payload = {"tipo": "skill", "nome": "x", "descricao": "abc", "alvo_projeto": "aidd-master"}
    resultado = profiles_registry.resolver_destinos(payload, str(tmp_path))
    mirrors = resultado.valor["mirrors"]
    for harness in (".claude", ".agent", ".gemini"):
        assert any(harness in m for m in mirrors), f"harness {harness} não espelhado"
    assert not any("mimocode" in m for m in mirrors), "mimocode não deve mais constar em mirrors de skill"


def test_perfis_aidd_master_sem_mimocode_em_nenhum_mirror():
    """Garante que 'mimocode' não aparece em nenhum valor de mirrors em PROFILES['aidd-master']."""
    perfil_master = profiles_registry.PROFILES.get("aidd-master", {})
    for tipo, config in perfil_master.items():
        mirrors = config.get("mirrors", [])
        for m in mirrors:
            assert "mimocode" not in m.lower(), f"mimocode encontrado em mirror de {tipo}: {m}"


# ---------------------------------------------------------------------------
# Fase 3 — Detector Híbrido (heurística determinística + fallback delegado)
# ---------------------------------------------------------------------------

def test_detector_infere_tipo_nome_e_descricao_de_frase_ptbr():
    resultado = detector_camada.detectar_de_texto("Crie uma skill de Segurança Cibernética")
    assert resultado.sucesso is True
    assert resultado.valor["tipo"] == "skill"
    assert resultado.valor["nome"] == "seguranca-cibernetica"
    assert "Segurança Cibernética" in resultado.valor["descricao"]
    assert resultado.valor["camada_alvo"] == "harness_multiplataforma"


def test_detector_infere_mcp_de_frase_ptbr():
    resultado = detector_camada.detectar_de_texto("adicionar um mcp de monitoramento de logs")
    assert resultado.sucesso is True
    assert resultado.valor["tipo"] == "mcp"
    assert resultado.valor["camada_alvo"] == "kernel_core"


def test_detector_delega_quando_tipo_e_ambiguo():
    resultado = detector_camada.detectar_de_texto("crie uma skill e uma regra de auditoria")
    assert resultado.sucesso is False
    assert resultado.codigo == "TIPO_AMBIGUO"
    assert set(resultado.detalhes["candidatos"]) == {"skill", "rule"}


def test_detector_construir_request_valida_tipo():
    resultado = detector_camada.construir_request(tipo="invalido", nome="x", descricao="y")
    assert resultado.sucesso is False
    assert resultado.codigo == "TIPO_INVALIDO"


# ---------------------------------------------------------------------------
# Fase 3 — Materializador Transacional (buffer atômico + rollback)
# ---------------------------------------------------------------------------

def test_materializador_escreve_artefato_e_espelhos(tmp_path):
    payload = {"tipo": "skill", "nome": "skill-teste", "descricao": "Skill de teste do materializador.", "alvo_projeto": "aidd-master"}
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor

    resultado = materializador.materializar(payload, resolucao)
    assert resultado.sucesso is True
    for caminho in resultado.valor["arquivos_criados"]:
        assert os.path.isfile(caminho)
    with open(resolucao["dest_principal"], "r", encoding="utf-8") as f:
        conteudo = f.read()
    assert "Skill de teste do materializador." in conteudo
    assert "name: skill-teste" in conteudo


def test_materializador_nao_sobrescreve_por_padrao(tmp_path):
    payload = {"tipo": "config", "nome": "config-teste", "descricao": "abc", "alvo_projeto": "aidd-master"}
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor

    primeiro = materializador.materializar(payload, resolucao)
    assert primeiro.sucesso is True
    segundo = materializador.materializar(payload, resolucao)
    assert segundo.sucesso is False
    assert segundo.codigo == "DESTINO_JA_EXISTE"


def test_materializador_faz_rollback_completo_em_falha_de_io(tmp_path):
    payload = {"tipo": "skill", "nome": "rollback-teste", "descricao": "Prova de rollback transacional.", "alvo_projeto": "aidd-master"}
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor

    # Induz falha de I/O determinística: cria um ARQUIVO exatamente onde o
    # último espelho (.gemini/...) precisaria de um DIRETÓRIO — os.makedirs
    # falha com OSError, disparando o rollback.
    ultimo_espelho = resolucao["mirrors"][-1]
    diretorio_do_espelho = os.path.dirname(ultimo_espelho)
    os.makedirs(os.path.dirname(diretorio_do_espelho), exist_ok=True)
    with open(diretorio_do_espelho, "w", encoding="utf-8") as f:
        f.write("bloqueio deliberado para forçar falha de materialização")

    resultado = materializador.materializar(payload, resolucao)
    assert resultado.sucesso is False
    assert resultado.codigo == "MATERIALIZACAO_FALHOU"

    # Zero arquivos órfãos: nenhum arquivo desta operação deve ter sobrado.
    assert not os.path.isfile(resolucao["dest_principal"])
    for espelho in resolucao["mirrors"][:-1]:
        assert not os.path.isfile(espelho)


# ---------------------------------------------------------------------------
# Fase 4 — Sincronizador Multi-Harness (catálogo + âncoras idempotentes)
# ---------------------------------------------------------------------------

def test_sincronizador_atualiza_capabilities_json_idempotente(tmp_path):
    payload = {"tipo": "skill", "nome": "sync-teste", "descricao": "abc", "camada_alvo": "harness_multiplataforma", "alvo_projeto": "aidd-master"}
    registry_path = str(tmp_path / "CAPABILITIES.json")
    resolucao = {"registry": registry_path, "anchors": [], "router_anchor": None}

    sincronizador_harness.sincronizar(payload, resolucao, ["algum/arquivo.md"])
    sincronizador_harness.sincronizar(payload, resolucao, ["algum/arquivo.md"])

    with open(registry_path, "r", encoding="utf-8") as f:
        catalogo = json.load(f)
    assert len(catalogo["skill"]) == 1
    assert catalogo["skill"][0]["nome"] == "sync-teste"


def test_sincronizador_insere_ancora_de_rule_sem_duplicar(tmp_path):
    payload = {"tipo": "rule", "nome": "regra-teste", "descricao": "Regra de teste.", "camada_alvo": "governanca_regras", "alvo_projeto": "aidd-master"}
    ancora = tmp_path / "AGENTS_FAKE.md"
    ancora.write_text("# Documento existente\n\nConteúdo prévio não deve ser perdido.\n", encoding="utf-8")
    resolucao = {"registry": None, "anchors": [str(ancora)], "router_anchor": None}

    sincronizador_harness.sincronizar(payload, resolucao, [])
    sincronizador_harness.sincronizar(payload, resolucao, [])

    texto = ancora.read_text(encoding="utf-8")
    assert "Conteúdo prévio não deve ser perdido." in texto
    assert texto.count("regra-teste") == 1
    assert "AIDD_INJECTOR:COMPONENTES_INICIO" in texto


def test_sincronizador_registra_padrao_de_agent_no_router_sem_quebrar_sintaxe(tmp_path):
    copia_router = tmp_path / "intent_router_copia.py"
    with open(os.path.join(_CORE, "intent_router.py"), "r", encoding="utf-8") as f:
        copia_router.write_text(f.read(), encoding="utf-8")

    payload = {"tipo": "agent", "nome": "agente-teste", "descricao": "Agente de teste.", "camada_alvo": "interface_orquestracao", "alvo_projeto": "aidd-master"}
    resolucao = {"registry": None, "anchors": [], "router_anchor": str(copia_router)}

    sincronizador_harness.sincronizar(payload, resolucao, [])
    sincronizador_harness.sincronizar(payload, resolucao, [])

    conteudo = copia_router.read_text(encoding="utf-8")
    assert conteudo.count('action="agent:agente-teste"') == 1

    # Prova real (não apenas string matching): o arquivo mutado ainda compila.
    py_compile.compile(str(copia_router), doraise=True)


# ---------------------------------------------------------------------------
# Fase 5 — CLI + IntentRouter (comando explícito e linguagem natural PT-BR)
# ---------------------------------------------------------------------------

def test_intent_router_reconhece_frases_ptbr_de_injecao():
    router = IntentRouter()
    for frase in (
        "crie uma skill de teste unitario",
        "adicione um mcp de monitoramento",
        "novo agente de suporte",
    ):
        resultado = router.parse_intent_result(frase)
        assert resultado.action == "inject", f"frase não reconhecida como injeção: {frase!r}"


def test_intent_router_nao_confunde_criar_modulo_com_injecao():
    router = IntentRouter()
    resultado = router.parse_intent_result("criar modulo pagamentos")
    assert resultado.action == "add-module"


def test_cli_inject_explicito_ponta_a_ponta(tmp_path):
    aidd_py = os.path.join(_ROOT, "scripts", "aidd.py")
    res = subprocess.run(
        [sys.executable, aidd_py, "inject", "skill", "cli-e2e-skill", "-d", "Skill de teste E2E via CLI", "--dir", str(tmp_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert os.path.isfile(tmp_path / ".skills" / "cli-e2e-skill" / "SKILL.md")
    assert os.path.isfile(tmp_path / ".claude" / "skills" / "cli-e2e-skill" / "SKILL.md")
    with open(tmp_path / "CAPABILITIES.json", "r", encoding="utf-8") as f:
        catalogo = json.load(f)
    assert any(e["nome"] == "cli-e2e-skill" for e in catalogo["skill"])


def test_cli_linguagem_natural_ponta_a_ponta(tmp_path):
    aidd_py = os.path.join(_ROOT, "scripts", "aidd.py")
    res = subprocess.run(
        [sys.executable, aidd_py, "crie", "um", "mcp", "de", "diagnostico", "de", "rede"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(tmp_path),
    )
    assert res.returncode == 0, res.stdout + res.stderr
    caminho_mcp = tmp_path / "src" / "core" / "mcp" / "diagnostico-de-rede.py"
    assert caminho_mcp.is_file()
    py_compile.compile(str(caminho_mcp), doraise=True)


# ---------------------------------------------------------------------------
# Fase 1 (Hook Universal) & Fase 2 (MCP externo via mcp.json)
# ---------------------------------------------------------------------------

def test_materializador_hook_escreve_alvo_espelhos_e_canonico(tmp_path):
    fake_eco = tmp_path / "_ecossistema_fake_root"
    payload = {"tipo": "hook", "nome": "pre-commit-hook", "descricao": "Hook de pre-commit.", "alvo_projeto": "aidd-master"}
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor

    resultado = materializador.materializar(payload, resolucao)
    assert resultado.sucesso is True
    assert (tmp_path / ".agent" / "hooks" / "pre-commit-hook" / "pre-commit-hook.json").is_file()
    assert (tmp_path / ".claude" / "hooks" / "pre-commit-hook" / "pre-commit-hook.json").is_file()
    assert (tmp_path / ".gemini" / "hooks" / "pre-commit-hook" / "pre-commit-hook.json").is_file()

    # Cópia na raiz canônica isolada via fixture
    canon_dest = fake_eco / "componentes" / "aidd-master" / "hooks" / "pre-commit-hook" / "pre-commit-hook.json"
    assert canon_dest.is_file()


def test_cli_inject_hook_ponta_a_ponta(tmp_path):
    aidd_py = os.path.join(_ROOT, "scripts", "aidd.py")
    try:
        res = subprocess.run(
            [sys.executable, aidd_py, "inject", "hook", "ci-audit", "-d", "Hook de auditoria de CI", "--dir", str(tmp_path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        assert res.returncode == 0, res.stdout + res.stderr
        assert (tmp_path / ".agent" / "hooks" / "ci-audit" / "ci-audit.json").is_file()
        assert (tmp_path / ".claude" / "hooks" / "ci-audit" / "ci-audit.json").is_file()
    finally:
        repo_root = Path(_ROOT).parents[1]
        import shutil
        for p in [
            repo_root / "componentes" / "aidd-master" / "hooks" / "ci-audit",
            repo_root / "tools" / "aidd-master" / ".agent" / "hooks" / "ci-audit",
            repo_root / "tools" / "aidd-master" / ".agents" / "hooks" / "ci-audit",
            repo_root / "tools" / "aidd-master" / ".claude" / "hooks" / "ci-audit",
            repo_root / "tools" / "aidd-master" / ".gemini" / "hooks" / "ci-audit",
            repo_root / "tools" / "aidd-master" / ".mimocode" / "hooks" / "ci-audit",
            repo_root / "tools" / "aidd-master" / ".opencode" / "hooks" / "ci-audit",
        ]:
            if p.exists():
                shutil.rmtree(p, ignore_errors=True)


def test_mcp_sem_command_mantem_comportamento_legado(tmp_path):
    payload = {"tipo": "mcp", "nome": "legado-tool", "descricao": "MCP em Python in-process.", "alvo_projeto": "aidd-master"}
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor

    resultado = materializador.materializar(payload, resolucao)
    assert resultado.sucesso is True
    py_tool = tmp_path / "src" / "core" / "mcp" / "legado-tool.py"
    assert py_tool.is_file()
    assert not (tmp_path / "mcp.json").exists()


def test_mcp_com_command_cria_mcp_json_e_nao_cria_py(tmp_path):
    payload = {
        "tipo": "mcp",
        "nome": "db-server",
        "descricao": "Servidor MCP externo.",
        "alvo_projeto": "aidd-master",
        "command": "node",
        "args": ["server.js", "--port", "3000"],
        "env": {"NODE_ENV": "production"},
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor

    resultado = materializador.materializar(payload, resolucao)
    assert resultado.sucesso is True
    mcp_json_path = tmp_path / "mcp.json"
    assert mcp_json_path.is_file()
    # Não cria o .py
    assert not (tmp_path / "src" / "core" / "mcp" / "db-server.py").exists()

    with open(mcp_json_path, "r", encoding="utf-8") as f:
        dados = json.load(f)
    assert "db-server" in dados["mcpServers"]
    assert dados["mcpServers"]["db-server"]["command"] == "node"
    assert dados["mcpServers"]["db-server"]["args"] == ["server.js", "--port", "3000"]
    assert dados["mcpServers"]["db-server"]["env"] == {"NODE_ENV": "production"}


def test_mcp_com_command_faz_merge_preservando_entradas_anteriores(tmp_path):
    # Cria primeiro server
    payload1 = {
        "tipo": "mcp", "nome": "server-um", "descricao": "Primeiro", "alvo_projeto": "aidd-master",
        "command": "cmd1", "args": ["--a"], "env": {},
    }
    resolucao1 = profiles_registry.resolver_destinos(payload1, str(tmp_path)).valor
    r1 = materializador.materializar(payload1, resolucao1)
    assert r1.sucesso is True

    # Cria segundo server
    payload2 = {
        "tipo": "mcp", "nome": "server-dois", "descricao": "Segundo", "alvo_projeto": "aidd-master",
        "command": "cmd2", "args": ["--b"], "env": {"K": "V"},
    }
    resolucao2 = profiles_registry.resolver_destinos(payload2, str(tmp_path)).valor
    r2 = materializador.materializar(payload2, resolucao2)
    assert r2.sucesso is True

    with open(tmp_path / "mcp.json", "r", encoding="utf-8") as f:
        dados = json.load(f)
    assert "server-um" in dados["mcpServers"]
    assert "server-dois" in dados["mcpServers"]
    assert dados["mcpServers"]["server-um"]["command"] == "cmd1"
    assert dados["mcpServers"]["server-dois"]["command"] == "cmd2"


def test_mcp_com_command_rejeita_mcp_json_invalido(tmp_path):
    mcp_json_path = tmp_path / "mcp.json"
    mcp_json_path.write_text("{conteudo-corrompido: json invalido", encoding="utf-8")

    payload = {
        "tipo": "mcp", "nome": "falha-mcp", "descricao": "Falha", "alvo_projeto": "aidd-master",
        "command": "dummy", "args": [], "env": {},
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    resultado = materializador.materializar(payload, resolucao)
    assert resultado.sucesso is False
    assert resultado.codigo == "MCP_JSON_INVALIDO"
    # Preserva o arquivo original sem sobrescrever silenciosamente
    assert mcp_json_path.read_text(encoding="utf-8") == "{conteudo-corrompido: json invalido"


def test_cli_inject_mcp_com_command_ponta_a_ponta(tmp_path):
    aidd_py = os.path.join(_ROOT, "scripts", "aidd.py")
    res = subprocess.run(
        [
            sys.executable, aidd_py, "inject", "mcp", "postgres-live",
            "--descricao", "Servidor Postgres MCP",
            "--mcp-command", "npx",
            "--mcp-args", '["-y", "@modelcontextprotocol/server-postgres"]',
            "--mcp-env", '{"DATABASE_URL": "postgresql://localhost/db"}',
            "--dir", str(tmp_path),
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert res.returncode == 0, res.stdout + res.stderr
    mcp_json_path = tmp_path / "mcp.json"
    assert mcp_json_path.is_file()
    with open(mcp_json_path, "r", encoding="utf-8") as f:
        dados = json.load(f)
    assert "postgres-live" in dados["mcpServers"]
    assert dados["mcpServers"]["postgres-live"]["command"] == "npx"
    assert dados["mcpServers"]["postgres-live"]["args"] == ["-y", "@modelcontextprotocol/server-postgres"]
    assert dados["mcpServers"]["postgres-live"]["env"] == {"DATABASE_URL": "postgresql://localhost/db"}


# ---------------------------------------------------------------------------
# Fase 7 — 5 Novas Capacidades do Injetor Universal Canônico
# ---------------------------------------------------------------------------

def test_sha256_hash_drift_detection(tmp_path):
    """(a) Injeta componente, altera arquivo manualmente e verifica drift; reinjeta e confirma ok."""
    payload = {
        "tipo": "skill",
        "nome": "skill-drift-check",
        "descricao": "Skill para testar drift de hash SHA-256.",
        "alvo_projeto": "aidd-master",
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    mat_res = materializador.materializar(payload, resolucao)
    assert mat_res.sucesso is True
    sync_res = sincronizador_harness.sincronizar(payload, resolucao, mat_res.valor["arquivos_criados"])
    assert sync_res.sucesso is True

    # 1. Antes de alterar, verificação passa
    check1 = sincronizador_harness.verificar_sincronizacao(str(tmp_path))
    assert check1.sucesso is True
    assert check1.valor["verificados"] > 0
    assert len(check1.valor["problemas"]) == 0

    # 2. Edita manualmente um arquivo gerado
    arq_editado = mat_res.valor["arquivos_criados"][0]
    with open(arq_editado, "a", encoding="utf-8") as f:
        f.write("\n# Modificacao manual para gerar drift\n")

    check2 = sincronizador_harness.verificar_sincronizacao(str(tmp_path))
    assert check2.sucesso is False
    assert check2.codigo == "SYNC_DIVERGENTE"
    assert len(check2.detalhes["problemas"]) >= 1
    assert "Hash divergente" in check2.detalhes["problemas"][0]

    # 3. Reinjeta com sobrescrever=True sem editar nada e confirma ok
    mat_res2 = materializador.materializar(payload, resolucao, sobrescrever=True)
    assert mat_res2.sucesso is True
    sync_res2 = sincronizador_harness.sincronizar(payload, resolucao, mat_res2.valor["arquivos_criados"])
    assert sync_res2.sucesso is True

    check3 = sincronizador_harness.verificar_sincronizacao(str(tmp_path))
    assert check3.sucesso is True
    assert len(check3.valor["problemas"]) == 0


def test_remover_componente_e_limpar_diretorios_vazios(tmp_path):
    """(b) Injeta componente, remove via remover_componente() e valida deleção física e limpeza."""
    payload = {
        "tipo": "rule",
        "nome": "regra-remocao",
        "descricao": "Regra para testar remocao completa.",
        "alvo_projeto": "aidd-master",
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    mat_res = materializador.materializar(payload, resolucao)
    assert mat_res.sucesso is True
    sync_res = sincronizador_harness.sincronizar(payload, resolucao, mat_res.valor["arquivos_criados"])
    assert sync_res.sucesso is True

    for arq in mat_res.valor["arquivos_criados"]:
        assert os.path.isfile(arq)

    # Remove o componente
    rem_res = materializador.remover_componente("rule", "regra-remocao", str(tmp_path))
    assert rem_res.sucesso is True

    # Arquivos devem sumir
    for arq in mat_res.valor["arquivos_criados"]:
        assert not os.path.exists(arq)

    # Diretório vazio que continha o arquivo deve ter sido limpo se ficou vazio
    for arq in mat_res.valor["arquivos_criados"]:
        d = os.path.dirname(arq)
        if os.path.exists(d):
            assert len(os.listdir(d)) > 0

    # Registro no CAPABILITIES.json não deve conter mais o componente
    with open(tmp_path / "CAPABILITIES.json", "r", encoding="utf-8") as f:
        catalogo = json.load(f)
    assert all(c.get("nome") != "regra-remocao" for c in catalogo.get("rule", []))

    # Tentar remover de novo deve falhar com COMPONENTE_NAO_ENCONTRADO
    rem_res2 = materializador.remover_componente("rule", "regra-remocao", str(tmp_path))
    assert rem_res2.sucesso is False
    assert rem_res2.codigo == "COMPONENTE_NAO_ENCONTRADO"


def test_remover_componente_hook_limpa_tambem_destino_canonico(tmp_path):
    """remover_componente() de um 'hook' também apaga a cópia canônica
    (componentes/{alvo_projeto}/hooks/{nome}/{nome}.json) escrita por materializar()
    fora da lista 'arquivos_criados' — sem isso, remover deixava esse arquivo órfão."""
    payload = {
        "tipo": "hook",
        "nome": "hook-remocao-canonica",
        "descricao": "Hook para testar limpeza do destino canonico na remocao.",
        "alvo_projeto": "aidd-master",
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    mat_res = materializador.materializar(payload, resolucao)
    assert mat_res.sucesso is True
    sync_res = sincronizador_harness.sincronizar(payload, resolucao, mat_res.valor["arquivos_criados"])
    assert sync_res.sucesso is True

    canon_dest = materializador.resolve_canonical_destination("hook", "hook-remocao-canonica", alvo_projeto="aidd-master")
    assert canon_dest.is_file()

    rem_res = materializador.remover_componente("hook", "hook-remocao-canonica", str(tmp_path))
    assert rem_res.sucesso is True

    for arq in mat_res.valor["arquivos_criados"]:
        assert not os.path.exists(arq)
    assert not canon_dest.exists()


def test_rollback_full_snapshot_restaura_conteudo_previo(tmp_path, monkeypatch):
    """(c) Cria destino pré-existente com conteúdo X; força falha na 2ª escrita; confirma volta de X."""
    payload = {
        "tipo": "skill",
        "nome": "skill-rollback-snap",
        "descricao": "Skill para testar rollback com snapshot prévio.",
        "alvo_projeto": "aidd-master",
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    dest_principal = resolucao["dest_principal"]
    os.makedirs(os.path.dirname(dest_principal), exist_ok=True)

    conteudo_original = "CONTEUDO_ORIGINAL_PRE_EXISTENTE_12345"
    with open(dest_principal, "w", encoding="utf-8") as f:
        f.write(conteudo_original)

    # Interceptar escrever_atomico em materializador para falhar na segunda escrita (quando destino != dest_principal)
    real_escrever = materializador.escrever_atomico
    escritas = []
    falhou = [False]

    def mock_escrever(destino, conteudo, *args, **kwargs):
        escritas.append(str(destino))
        if len(escritas) >= 2 and not falhou[0]:
            falhou[0] = True
            raise OSError("Falha simulada na segunda escrita para forçar rollback")
        return real_escrever(destino, conteudo, *args, **kwargs)

    monkeypatch.setattr(materializador, "escrever_atomico", mock_escrever)

    res = materializador.materializar(payload, resolucao, sobrescrever=True)
    assert res.sucesso is False
    assert res.codigo == "MATERIALIZACAO_FALHOU"

    # Restaura monkeypatch para ler arquivo
    monkeypatch.undo()

    # O arquivo pré-existente deve ter tido seu conteúdo original restaurado
    with open(dest_principal, "r", encoding="utf-8") as f:
        assert f.read() == conteudo_original

    # O segundo arquivo (que falhou) não deve existir
    if len(resolucao.get("mirrors", [])) > 0:
        assert not os.path.exists(resolucao["mirrors"][0])


def test_materializar_dry_run_nao_escreve_em_disco(tmp_path):
    """(d) materializar(dry_run=True) não cria arquivos e retorna destinos esperados."""
    payload = {
        "tipo": "agent",
        "nome": "agente-dry",
        "descricao": "Agente para testar modo dry_run.",
        "alvo_projeto": "aidd-master",
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    res = materializador.materializar(payload, resolucao, dry_run=True)

    assert res.sucesso is True
    assert res.detalhes.get("dry_run") is True

    destinos = res.valor if isinstance(res.valor, list) else res.valor.get("destinos", [])
    assert len(destinos) > 0
    for d in destinos:
        assert not os.path.exists(d), f"Arquivo não deveria ter sido criado: {d}"


def test_config_com_mapa_arbitrario_de_arquivos(tmp_path):
    """(e) Injeta config com 'arquivos', valida rejeição de path traversal e scaffold padrão sem 'arquivos'."""
    # 1. Config com arquivos válidos
    payload_valido = {
        "tipo": "config",
        "nome": "cfg-multi",
        "descricao": "Configuração multi-arquivos.",
        "alvo_projeto": "aidd-master",
        "arquivos": {
            "a/b.json": '{"status": "ok"}',
            "c.txt": "conteudo c",
        },
    }
    resolucao = profiles_registry.resolver_destinos(payload_valido, str(tmp_path)).valor
    res_valido = materializador.materializar(payload_valido, resolucao)
    assert res_valido.sucesso is True
    assert (tmp_path / "a" / "b.json").read_text(encoding="utf-8") == '{"status": "ok"}'
    assert (tmp_path / "c.txt").read_text(encoding="utf-8") == "conteudo c"

    # 2. Config com path traversal (rejeição estrita e nenhum arquivo escrito)
    payload_inseguro = {
        "tipo": "config",
        "nome": "cfg-bad",
        "descricao": "Configuração com path traversal.",
        "alvo_projeto": "aidd-master",
        "arquivos": {
            "../fora.txt": "conteudo malicioso",
        },
    }
    res_inseguro = materializador.materializar(payload_inseguro, resolucao)
    assert res_inseguro.sucesso is False
    assert res_inseguro.codigo == "PATH_TRAVERSAL_REJEITADO"
    assert not (tmp_path.parent / "fora.txt").exists()

    # 3. Config sem 'arquivos' (zero regressão — scaffold fixo padrão)
    payload_sem_arquivos = {
        "tipo": "config",
        "nome": "cfg-padrao",
        "descricao": "Configuração clássica sem mapa de arquivos.",
        "alvo_projeto": "aidd-master",
    }
    res_padrao = materializador.materializar(payload_sem_arquivos, resolucao)
    assert res_padrao.sucesso is True
    dest_principal = resolucao["dest_principal"]
    assert os.path.isfile(dest_principal)
    with open(dest_principal, "r", encoding="utf-8") as f:
        dados = json.load(f)
    assert dados["nome"] == "cfg-padrao"
    assert "parametros" in dados


def test_cli_inject_remover_e_dry_run_ponta_a_ponta(tmp_path):
    """Valida CLI 'aidd inject' com flags --dry-run e --remover ponta a ponta."""
    aidd_py = os.path.join(_ROOT, "scripts", "aidd.py")

    # 1. Executa com --dry-run
    res_dry = subprocess.run(
        [
            sys.executable, aidd_py, "inject", "rule", "regra-cli-dry",
            "--descricao", "Regra dry run CLI",
            "--dry-run",
            "--dir", str(tmp_path),
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert res_dry.returncode == 0, res_dry.stdout + res_dry.stderr
    assert "[DRY-RUN]" in res_dry.stdout
    assert not (tmp_path / "templates" / "rules" / "regra-cli-dry.md").exists()

    # 2. Injeta de verdade
    res_inj = subprocess.run(
        [
            sys.executable, aidd_py, "inject", "rule", "regra-cli-real",
            "--descricao", "Regra real CLI",
            "--dir", str(tmp_path),
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert res_inj.returncode == 0, res_inj.stdout + res_inj.stderr
    regra_path = tmp_path / "templates" / "rules" / "regra-cli-real.md"
    assert regra_path.is_file()

    # 3. Remove com --remover
    res_rem = subprocess.run(
        [
            sys.executable, aidd_py, "inject", "rule", "regra-cli-real",
            "--remover",
            "--dir", str(tmp_path),
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert res_rem.returncode == 0, res_rem.stdout + res_rem.stderr
    assert not regra_path.exists()


def test_cli_verificar_drift_ponta_a_ponta(tmp_path):
    """Valida o subcomando 'aidd verificar-drift' ponta a ponta: passa após injeção
    limpa e reprova (exit 1) depois de uma edição manual do arquivo gerado."""
    aidd_py = os.path.join(_ROOT, "scripts", "aidd.py")

    res_inj = subprocess.run(
        [
            sys.executable, aidd_py, "inject", "rule", "regra-cli-drift",
            "--descricao", "Regra para checar drift via CLI",
            "--dir", str(tmp_path),
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert res_inj.returncode == 0, res_inj.stdout + res_inj.stderr
    regra_path = tmp_path / "templates" / "rules" / "regra-cli-drift.md"
    assert regra_path.is_file()

    res_ok = subprocess.run(
        [sys.executable, aidd_py, "verificar-drift", "--dir", str(tmp_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert res_ok.returncode == 0, res_ok.stdout + res_ok.stderr
    assert "SUCESSO" in res_ok.stdout

    with open(regra_path, "a", encoding="utf-8") as f:
        f.write("\n# Edicao manual para gerar drift via CLI\n")

    res_fail = subprocess.run(
        [sys.executable, aidd_py, "verificar-drift", "--dir", str(tmp_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert res_fail.returncode == 1, res_fail.stdout + res_fail.stderr
    assert "SYNC_DIVERGENTE" in res_fail.stdout



