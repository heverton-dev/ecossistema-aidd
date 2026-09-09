# -*- coding: utf-8 -*-
"""
Suíte de testes unitários do Injetor Universal de Componentes em aidd-enterprise.
Valida contrato, matriz de perfis (5 harnesses), materialização transacional,
merge de mcp.json, config com mapa arbitrário, rejeição de path traversal,
rollback com snapshot, detecção de drift via SHA-256, remoção canônica de hook,
e detecção de ambiguidade em linguagem natural PT-BR.
"""

import builtins
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_TEST_DIR, "..", ".."))
_SRC = os.path.join(_REPO_ROOT, "src")
_CORE = os.path.join(_SRC, "core")
for _p in (_SRC, _CORE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import profiles_registry
import detector_camada
import materializador
import sincronizador_harness
from intent_router import IntentRouter


# ---------------------------------------------------------------------------
# 1. Contrato Universal & Validação de Payload
# ---------------------------------------------------------------------------

def test_validate_component_skill_valido():
    payload = {
        "tipo": "skill",
        "nome": "minha-skill",
        "descricao": "Uma skill de exemplo para teste.",
        "alvo_projeto": "aidd-enterprise",
        "conteudo": "corpo da skill",
    }
    resultado = profiles_registry.validar_payload(payload)
    assert resultado.sucesso is True


def test_validate_component_type_invalido():
    payload = {
        "tipo": "nao-existe",
        "nome": "minha-skill",
        "descricao": "descricao valida",
        "alvo_projeto": "aidd-enterprise",
    }
    resultado = profiles_registry.validar_payload(payload)
    assert resultado.sucesso is False
    assert resultado.codigo == "TIPO_INVALIDO"


@pytest.mark.parametrize("nome_invalido", ["Maiuscula", "-comeca-com-hifen", "termina-com-hifen-", "com espaco", "com_underscore", "hifen--duplo"])
def test_validate_component_name_invalido(nome_invalido):
    payload = {
        "tipo": "rule",
        "nome": nome_invalido,
        "descricao": "descricao valida",
        "alvo_projeto": "aidd-enterprise",
    }
    resultado = profiles_registry.validar_payload(payload)
    assert resultado.sucesso is False
    assert resultado.codigo == "NOME_INVALIDO"


def test_validate_component_payload_incompleto():
    resultado = profiles_registry.validar_payload({"tipo": "skill", "nome": "sem-descricao"})
    assert resultado.sucesso is False
    assert resultado.codigo == "PAYLOAD_INCOMPLETO"


# ---------------------------------------------------------------------------
# 2. Resolução de Rotas por Perfis (Topologia Real dos 7 Tipos em aidd-enterprise)
# ---------------------------------------------------------------------------

def test_resolve_targets_skill_fan_out_5_harnesses(tmp_path):
    payload = {
        "tipo": "skill",
        "nome": "minha-skill",
        "descricao": "Skill multi-harness.",
        "alvo_projeto": "aidd-enterprise",
        "conteudo": "corpo",
    }
    resultado = profiles_registry.resolver_destinos(payload, str(tmp_path))
    assert resultado.sucesso is True
    destinos = [resultado.valor["dest_principal"]] + resultado.valor["mirrors"]
    destinos_rel = {os.path.relpath(d, str(tmp_path)).replace("\\", "/") for d in destinos}
    assert destinos_rel == {
        ".claude/skills/minha-skill/SKILL.md",
        ".agent/skills/minha-skill/SKILL.md",
        ".mimocode/skills/minha-skill/SKILL.md",
        ".gemini/skills/minha-skill/SKILL.md",
        ".skills/minha-skill/SKILL.md",
    }


def test_resolve_targets_hook_fan_out_5_harnesses(tmp_path):
    payload = {
        "tipo": "hook",
        "nome": "meu-hook",
        "descricao": "Hook multi-harness.",
        "alvo_projeto": "aidd-enterprise",
        "conteudo": "{}",
    }
    resultado = profiles_registry.resolver_destinos(payload, str(tmp_path))
    assert resultado.sucesso is True
    destinos = [resultado.valor["dest_principal"]] + resultado.valor["mirrors"]
    destinos_rel = {os.path.relpath(d, str(tmp_path)).replace("\\", "/") for d in destinos}
    assert destinos_rel == {
        ".claude/hooks/meu-hook.json",
        ".agent/hooks/meu-hook.json",
        ".mimocode/hooks/meu-hook.json",
        ".gemini/hooks/meu-hook.json",
        ".hooks/meu-hook.json",
    }


def test_resolve_targets_rule_single_file(tmp_path):
    payload = {
        "tipo": "rule",
        "nome": "minha-regra",
        "descricao": "Regra corporativa.",
        "alvo_projeto": "aidd-enterprise",
    }
    resultado = profiles_registry.resolver_destinos(payload, str(tmp_path))
    assert resultado.sucesso is True
    rel = os.path.relpath(resultado.valor["dest_principal"], str(tmp_path)).replace("\\", "/")
    assert rel == "templates/rules/minha-regra.md"


def test_resolve_targets_spec_single_file(tmp_path):
    payload = {
        "tipo": "spec",
        "nome": "minha-spec",
        "descricao": "Especificacao técnica.",
        "alvo_projeto": "aidd-enterprise",
    }
    resultado = profiles_registry.resolver_destinos(payload, str(tmp_path))
    assert resultado.sucesso is True
    rel = os.path.relpath(resultado.valor["dest_principal"], str(tmp_path)).replace("\\", "/")
    assert rel == "docs/specs/minha-spec.md"


def test_resolve_targets_agent_single_file(tmp_path):
    payload = {
        "tipo": "agent",
        "nome": "meu-agente",
        "descricao": "Agente especialista.",
        "alvo_projeto": "aidd-enterprise",
    }
    resultado = profiles_registry.resolver_destinos(payload, str(tmp_path))
    assert resultado.sucesso is True
    rel = os.path.relpath(resultado.valor["dest_principal"], str(tmp_path)).replace("\\", "/")
    assert rel == "templates/agents/meu-agente.md"


def test_resolve_targets_config_single_file(tmp_path):
    payload = {
        "tipo": "config",
        "nome": "minha-config",
        "descricao": "Configuracao padrão.",
        "alvo_projeto": "aidd-enterprise",
    }
    resultado = profiles_registry.resolver_destinos(payload, str(tmp_path))
    assert resultado.sucesso is True
    rel = os.path.relpath(resultado.valor["dest_principal"], str(tmp_path)).replace("\\", "/")
    assert rel == "templates/core/config/minha-config.json"


def test_resolve_targets_mcp_single_file(tmp_path):
    payload = {
        "tipo": "mcp",
        "nome": "meu-mcp",
        "descricao": "Servidor MCP interno.",
        "alvo_projeto": "aidd-enterprise",
    }
    resultado = profiles_registry.resolver_destinos(payload, str(tmp_path))
    assert resultado.sucesso is True
    rel = os.path.relpath(resultado.valor["dest_principal"], str(tmp_path)).replace("\\", "/")
    assert rel == "src/core/mcp/meu-mcp.py"


# ---------------------------------------------------------------------------
# 3. Materialização — Dry Run
# ---------------------------------------------------------------------------

def test_materialize_dry_run_nao_escreve_nada(tmp_path):
    payload = {
        "tipo": "skill",
        "nome": "dry-teste",
        "descricao": "Skill para dry-run.",
        "alvo_projeto": "aidd-enterprise",
        "conteudo": "corpo",
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    resultado = materializador.materializar(payload, resolucao, dry_run=True)

    assert resultado.sucesso is True
    assert resultado.detalhes.get("dry_run") is True
    destinos = resultado.valor if isinstance(resultado.valor, list) else resultado.valor.get("destinos", [])
    assert len(destinos) == 5
    for d in destinos:
        assert not os.path.exists(d)
    assert not (tmp_path / "CAPABILITIES.json").exists()


# ---------------------------------------------------------------------------
# 4. Materialização Real & Registry CAPABILITIES.json
# ---------------------------------------------------------------------------

def test_materialize_skill_fan_out_identico_e_registry(tmp_path):
    payload = {
        "tipo": "skill",
        "nome": "skill-real",
        "descricao": "Uma skill real para teste de integridade.",
        "alvo_projeto": "aidd-enterprise",
        "conteudo": "CONTEUDO IDENTICO EM TODOS HARNESSES",
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    mat_res = materializador.materializar(payload, resolucao)
    assert mat_res.sucesso is True

    arquivos = mat_res.valor["arquivos_criados"]
    assert len(arquivos) == 5

    conteudos = set()
    for arq in arquivos:
        assert os.path.isfile(arq)
        with open(arq, "r", encoding="utf-8") as f:
            conteudos.add(f.read())
    assert conteudos == {"CONTEUDO IDENTICO EM TODOS HARNESSES"}

    # Atualiza registry
    sync_res = sincronizador_harness.sincronizar(payload, resolucao, arquivos)
    assert sync_res.sucesso is True

    reg_path = tmp_path / "CAPABILITIES.json"
    assert reg_path.exists()
    dados = json.loads(reg_path.read_text(encoding="utf-8"))
    assert len(dados["skill"]) == 1
    assert dados["skill"][0]["nome"] == "skill-real"
    assert len(dados["skill"][0]["arquivos_hashes"]) == 5


def test_materialize_hook_fan_out_5_harnesses_e_canonico(tmp_path, monkeypatch):
    monkeypatch.setattr(materializador, "_default_ecossistema_root", lambda: tmp_path)
    payload = {
        "tipo": "hook",
        "nome": "meu-hook",
        "descricao": "Hook para validar integracao canonica.",
        "alvo_projeto": "aidd-enterprise",
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    mat_res = materializador.materializar(payload, resolucao)
    assert mat_res.sucesso is True

    # 5 pastas de harness devem ter meu-hook.json
    for arq in mat_res.valor["arquivos_criados"]:
        assert os.path.isfile(arq)
        assert arq.endswith("meu-hook.json")
        with open(arq, "r", encoding="utf-8") as f:
            dados = json.load(f)
            assert dados["name"] == "meu-hook"

    # Destino canônico em componentes/aidd-enterprise/hooks/meu-hook/meu-hook.json
    canon_dest = materializador.resolve_canonical_destination(
        "hook", "meu-hook", alvo_projeto="aidd-enterprise", ecossistema_root=tmp_path
    )
    assert canon_dest is not None
    assert canon_dest.is_file()
    with open(canon_dest, "r", encoding="utf-8") as f:
        dados_canon = json.load(f)
        assert dados_canon["name"] == "meu-hook"


def test_materialize_reinjecao_atualiza_entrada_sem_duplicar(tmp_path):
    payload = {
        "tipo": "rule",
        "nome": "regra-dup",
        "descricao": "Descricao v1",
        "alvo_projeto": "aidd-enterprise",
        "conteudo": "v1",
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    r1 = materializador.materializar(payload, resolucao)
    assert r1.sucesso is True
    sincronizador_harness.sincronizar(payload, resolucao, r1.valor["arquivos_criados"])

    payload2 = {
        "tipo": "rule",
        "nome": "regra-dup",
        "descricao": "Descricao v2",
        "alvo_projeto": "aidd-enterprise",
        "conteudo": "v2",
    }
    r2 = materializador.materializar(payload2, resolucao, sobrescrever=True)
    assert r2.sucesso is True
    sincronizador_harness.sincronizar(payload2, resolucao, r2.valor["arquivos_criados"])

    reg_path = tmp_path / "CAPABILITIES.json"
    catalogo = json.loads(reg_path.read_text(encoding="utf-8"))
    assert len(catalogo["rule"]) == 1
    assert catalogo["rule"][0]["descricao"] == "Descricao v2"


# ---------------------------------------------------------------------------
# 5. MCP Merge Preservando Servidores Prévios
# ---------------------------------------------------------------------------

def test_materialize_mcp_merge_preserva_servidores_existentes(tmp_path):
    mcp_path = tmp_path / "mcp.json"
    mcp_path.write_text(
        json.dumps({"mcpServers": {"servidor-existente": {"command": "node", "args": [], "env": {}}}}),
        encoding="utf-8",
    )

    payload = {
        "tipo": "mcp",
        "nome": "servidor-novo",
        "descricao": "Novo MCP externo.",
        "alvo_projeto": "aidd-enterprise",
        "command": "python",
        "args": ["s.py"],
        "env": {"VAR": "1"},
    }
    resolucao = {"root_dir": str(tmp_path)}
    resultado = materializador.materializar(payload, resolucao)
    assert resultado.sucesso is True

    dados = json.loads(mcp_path.read_text(encoding="utf-8"))
    assert "servidor-existente" in dados["mcpServers"]
    assert dados["mcpServers"]["servidor-novo"]["command"] == "python"
    assert dados["mcpServers"]["servidor-novo"]["args"] == ["s.py"]


# ---------------------------------------------------------------------------
# 6. Config com Mapa Arbitrário de Arquivos & Rejeição de Path Traversal
# ---------------------------------------------------------------------------

def test_materialize_config_com_mapa_arbitrario_de_arquivos(tmp_path):
    payload = {
        "tipo": "config",
        "nome": "cfg-arquivos",
        "descricao": "Configuração multi-arquivos.",
        "alvo_projeto": "aidd-enterprise",
        "arquivos": {
            "a/b.json": '{"status": "ok"}',
            "c/d.txt": "conteudo livre",
        },
    }
    resolucao = {"root_dir": str(tmp_path)}
    resultado = materializador.materializar(payload, resolucao)
    assert resultado.sucesso is True

    assert (tmp_path / "a" / "b.json").read_text(encoding="utf-8") == '{"status": "ok"}'
    assert (tmp_path / "c" / "d.txt").read_text(encoding="utf-8") == "conteudo livre"


def test_materialize_config_rejeita_path_traversal_sem_escrever(tmp_path):
    payload = {
        "tipo": "config",
        "nome": "cfg-malicioso",
        "descricao": "Configuração com path traversal.",
        "alvo_projeto": "aidd-enterprise",
        "arquivos": {
            "../escapou.txt": "conteudo malicioso",
        },
    }
    resolucao = {"root_dir": str(tmp_path)}
    resultado = materializador.materializar(payload, resolucao)
    assert resultado.sucesso is False
    assert resultado.codigo == "PATH_TRAVERSAL_REJEITADO"
    assert not (tmp_path.parent / "escapou.txt").exists()


# ---------------------------------------------------------------------------
# 7. Rollback Transacional com Snapshot Completo
# ---------------------------------------------------------------------------

def test_materialize_rollback_em_falha_parcial(tmp_path, monkeypatch):
    payload = {
        "tipo": "skill",
        "nome": "rollback-teste",
        "descricao": "Teste de rollback.",
        "alvo_projeto": "aidd-enterprise",
        "conteudo": "CONTEUDO_NOVO",
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    dest_principal = resolucao["dest_principal"]
    os.makedirs(os.path.dirname(dest_principal), exist_ok=True)

    conteudo_antigo = "CONTEUDO_PRE_EXISTENTE"
    with open(dest_principal, "w", encoding="utf-8") as f:
        f.write(conteudo_antigo)

    real_open = builtins.open
    escritas = []
    falhou = [False]

    def mock_open(file, mode="r", *args, **kwargs):
        if "w" in mode and "b" not in mode:
            escritas.append(str(file))
            if len(escritas) >= 2 and not falhou[0]:
                falhou[0] = True
                raise OSError("Falha simulada na segunda escrita para forçar rollback")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", mock_open)
    resultado = materializador.materializar(payload, resolucao, sobrescrever=True)
    monkeypatch.undo()

    assert resultado.sucesso is False
    assert resultado.codigo == "MATERIALIZACAO_FALHOU"

    # Conteúdo pré-existente foi restaurado
    with open(dest_principal, "r", encoding="utf-8") as f:
        assert f.read() == conteudo_antigo

    # Demais destinos limpos
    for espelho in resolucao.get("mirrors", []):
        assert not os.path.exists(espelho)


# ---------------------------------------------------------------------------
# 8. Sincronizador & Drift Detection (SHA-256)
# ---------------------------------------------------------------------------

def test_sync_check_ok_quando_tudo_integro(tmp_path):
    payload = {
        "tipo": "rule",
        "nome": "regra-sync",
        "descricao": "Regra para sync.",
        "alvo_projeto": "aidd-enterprise",
        "conteudo": "corpo integro",
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    mat_res = materializador.materializar(payload, resolucao)
    assert mat_res.sucesso is True
    sync_res = sincronizador_harness.sincronizar(payload, resolucao, mat_res.valor["arquivos_criados"])
    assert sync_res.sucesso is True

    resultado = sincronizador_harness.verificar_sincronizacao(str(tmp_path))
    assert resultado.sucesso is True
    assert resultado.valor["verificados"] == 1


def test_sync_check_detecta_drift(tmp_path):
    payload = {
        "tipo": "rule",
        "nome": "regra-drift",
        "descricao": "Regra para drift.",
        "alvo_projeto": "aidd-enterprise",
        "conteudo": "corpo original",
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    mat_res = materializador.materializar(payload, resolucao)
    sincronizador_harness.sincronizar(payload, resolucao, mat_res.valor["arquivos_criados"])

    # Edição manual fora do injetor
    regra_file = tmp_path / "templates" / "rules" / "regra-drift.md"
    regra_file.write_text("CONTEUDO EDITADO MANUALMENTE", encoding="utf-8")

    resultado = sincronizador_harness.verificar_sincronizacao(str(tmp_path))
    assert resultado.sucesso is False
    assert resultado.codigo == "SYNC_DIVERGENTE"
    assert any("regra-drift" in p for p in resultado.detalhes["problemas"])


# ---------------------------------------------------------------------------
# 9. Remoção Limpa (Arquivos + Catálogo + Destino Canônico)
# ---------------------------------------------------------------------------

def test_remove_component_apaga_arquivos_e_entrada(tmp_path):
    payload = {
        "tipo": "rule",
        "nome": "regra-remover",
        "descricao": "Regra a remover.",
        "alvo_projeto": "aidd-enterprise",
        "conteudo": "corpo",
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    mat_res = materializador.materializar(payload, resolucao)
    sincronizador_harness.sincronizar(payload, resolucao, mat_res.valor["arquivos_criados"])

    resultado = materializador.remover_componente("rule", "regra-remover", str(tmp_path))
    assert resultado.sucesso is True
    assert not (tmp_path / "templates" / "rules" / "regra-remover.md").exists()

    catalogo = json.loads((tmp_path / "CAPABILITIES.json").read_text(encoding="utf-8"))
    assert not any(r["nome"] == "regra-remover" for r in catalogo.get("rule", []))


def test_remove_hook_limpa_destino_canonico_enterprise(tmp_path, monkeypatch):
    monkeypatch.setattr(materializador, "_default_ecossistema_root", lambda: tmp_path)
    payload = {
        "tipo": "hook",
        "nome": "hook-clean",
        "descricao": "Hook com remocao canonica.",
        "alvo_projeto": "aidd-enterprise",
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    mat_res = materializador.materializar(payload, resolucao)
    sincronizador_harness.sincronizar(payload, resolucao, mat_res.valor["arquivos_criados"])

    canon_dest = materializador.resolve_canonical_destination("hook", "hook-clean", alvo_projeto="aidd-enterprise", ecossistema_root=tmp_path)
    assert canon_dest.is_file()

    rem_res = materializador.remover_componente("hook", "hook-clean", str(tmp_path))
    assert rem_res.sucesso is True
    assert not canon_dest.exists()
    for arq in mat_res.valor["arquivos_criados"]:
        assert not os.path.exists(arq)


# ---------------------------------------------------------------------------
# 10. Linguagem Natural PT-BR e Detecção de Ambiguidade
# ---------------------------------------------------------------------------

def test_detector_de_texto_frase_valida():
    resultado = detector_camada.detectar_de_texto("Crie uma skill de Cibersegurança Corporativa", alvo_projeto="aidd-enterprise")
    assert resultado.sucesso is True
    assert resultado.valor["tipo"] == "skill"
    assert resultado.valor["nome"] == "ciberseguranca-corporativa"
    assert resultado.valor["alvo_projeto"] == "aidd-enterprise"


def test_detector_de_texto_detecta_tipo_ambiguo():
    # Frase com 2 tipos de componentes: deve falhar determinísticamente com TIPO_AMBIGUO
    resultado = detector_camada.detectar_de_texto("adicione uma skill ou uma regra de auditoria", alvo_projeto="aidd-enterprise")
    assert resultado.sucesso is False
    assert resultado.codigo == "TIPO_AMBIGUO"
    assert set(resultado.detalhes["candidatos"]) == {"skill", "rule"}


# ---------------------------------------------------------------------------
# 11. Execução CLI Ponta a Ponta
# ---------------------------------------------------------------------------

def test_cli_inject_remover_e_dry_run_ponta_a_ponta(tmp_path):
    aidd_py = os.path.join(_REPO_ROOT, "scripts", "aidd.py")

    # 1. Dry run
    res_dry = subprocess.run(
        [
            sys.executable, aidd_py, "inject", "rule", "regra-cli-dry",
            "--descricao", "Regra dry run",
            "--dry-run",
            "--dir", str(tmp_path),
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert res_dry.returncode == 0, res_dry.stdout + res_dry.stderr
    assert "[INJECTOR - DRY RUN]" in res_dry.stdout
    assert not (tmp_path / "templates" / "rules" / "regra-cli-dry.md").exists()

    # 2. Injeção real
    res_inj = subprocess.run(
        [
            sys.executable, aidd_py, "inject", "rule", "regra-cli-real",
            "--descricao", "Regra real",
            "--dir", str(tmp_path),
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert res_inj.returncode == 0, res_inj.stdout + res_inj.stderr
    regra_file = tmp_path / "templates" / "rules" / "regra-cli-real.md"
    assert regra_file.is_file()

    # 3. Remoção
    res_rem = subprocess.run(
        [
            sys.executable, aidd_py, "inject", "rule", "regra-cli-real",
            "--remover",
            "--dir", str(tmp_path),
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert res_rem.returncode == 0, res_rem.stdout + res_rem.stderr
    assert not regra_file.exists()


def test_cli_natural_language_ambiguidade(tmp_path):
    aidd_py = os.path.join(_REPO_ROOT, "scripts", "aidd.py")
    res = subprocess.run(
        [
            sys.executable, aidd_py, "adicione uma skill ou regra de autenticacao",
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert res.returncode == 1
    assert "TIPO_AMBIGUO" in (res.stdout + res.stderr)


# ---------------------------------------------------------------------------
# 10. Conteúdo Real dos Hashes SHA-256 do Manifesto (mata mutantes de
#     algoritmo sha256->sha1, de entrada trocada e de truncamento de leitura)
# ---------------------------------------------------------------------------

def _hash_arquivo(caminho: str) -> str:
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def test_manifesto_hashes_sha256_batem_conteudo_real(tmp_path):
    """Cada entrada de arquivos_hashes em CAPABILITIES.json deve ser o SHA-256
    exato do conteúdo em disco — recalculado localmente, nunca aceito do manifesto."""
    payload = {
        "tipo": "rule",
        "nome": "regra-hash-conteudo",
        "descricao": "Regra para validar hashes do manifesto.",
        "alvo_projeto": "aidd-enterprise",
        "conteudo": "linha1 da regra\nlinha2 da regra\n",
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    mat_res = materializador.materializar(payload, resolucao)
    assert mat_res.sucesso is True
    sync_res = sincronizador_harness.sincronizar(payload, resolucao, mat_res.valor["arquivos_criados"])
    assert sync_res.sucesso is True

    catalogo = json.loads((tmp_path / "CAPABILITIES.json").read_text(encoding="utf-8"))
    componentes = [c for c in catalogo.get("rule", []) if c["nome"] == "regra-hash-conteudo"]
    assert len(componentes) == 1
    hashes_manifesto = componentes[0]["arquivos_hashes"]
    assert hashes_manifesto, "manifesto precisa registrar arquivos_hashes"

    # Igualdade estrita: hash do manifesto == hash recalculado do conteúdo real
    for rel_path, esperado in hashes_manifesto.items():
        full_path = os.path.join(str(tmp_path), rel_path)
        assert os.path.isfile(full_path), f"arquivo do manifesto ausente: {rel_path}"
        assert _hash_arquivo(full_path) == esperado

    # Algoritmo obrigatoriamente SHA-256 (64 hex): sha1/md5/truncado não passa
    import re as _re
    for h in hashes_manifesto.values():
        assert _re.fullmatch(r"[0-9a-f]{64}", h), f"hash não é SHA-256 de 64 hex: {h}"


def test_adulteracao_1_byte_quebra_verificacao_sincronizacao(tmp_path):
    """Editar 1 byte do conteúdo após a sincronização deve fazer
    verificar_sincronizacao falhar — hash do manifesto não pode ser decorativo."""
    payload = {
        "tipo": "rule",
        "nome": "regra-adulterada",
        "descricao": "Regra para teste de adulteracao minima.",
        "alvo_projeto": "aidd-enterprise",
        "conteudo": "conteudo integro original da regra\n",
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    mat_res = materializador.materializar(payload, resolucao)
    assert mat_res.sucesso is True
    sync_res = sincronizador_harness.sincronizar(payload, resolucao, mat_res.valor["arquivos_criados"])
    assert sync_res.sucesso is True

    # Sanity: íntegro antes da adulteração
    pre = sincronizador_harness.verificar_sincronizacao(str(tmp_path))
    assert pre.sucesso is True

    # Adulteração de 1 byte (substituição do primeiro caractere do corpo)
    regra_file = tmp_path / "templates" / "rules" / "regra-adulterada.md"
    dados = bytearray(regra_file.read_bytes())
    idx = dados.index(b"c")
    dados[idx] = ord("C") if dados[idx] == ord("c") else ord("c")
    assert bytes(dados) != regra_file.read_bytes()
    regra_file.write_bytes(bytes(dados))

    # Verificação deve detectar a divergência de hash
    resultado = sincronizador_harness.verificar_sincronizacao(str(tmp_path))
    assert resultado.sucesso is False
    assert resultado.codigo == "SYNC_DIVERGENTE"
    assert any("regra-adulterada" in p for p in resultado.detalhes["problemas"])
    # E a divergência citada deve ser de hash, não de arquivo ausente
    assert any("Hash divergente" in p for p in resultado.detalhes["problemas"])


def test_sync_recusa_hash_nao_sha256_injetado_manualmente(tmp_path):
    """Um hash não-SHA-256 (ex.: sha1 hex de 40) plantado no manifesto deve
    ser detectado como divergência — mutante que troca o algoritmo morre."""
    payload = {
        "tipo": "rule",
        "nome": "regra-algoritmo",
        "descricao": "Regra para testar algoritmo de hash.",
        "alvo_projeto": "aidd-enterprise",
        "conteudo": "conteudo para algoritmo\n",
    }
    resolucao = profiles_registry.resolver_destinos(payload, str(tmp_path)).valor
    mat_res = materializador.materializar(payload, resolucao)
    assert mat_res.sucesso is True
    sync_res = sincronizador_harness.sincronizar(payload, resolucao, mat_res.valor["arquivos_criados"])
    assert sync_res.sucesso is True

    catalogo_path = tmp_path / "CAPABILITIES.json"
    catalogo = json.loads(catalogo_path.read_text(encoding="utf-8"))
    for comp in catalogo["rule"]:
        if comp["nome"] == "regra-algoritmo":
            primeiro = next(iter(comp["arquivos_hashes"]))
            comp["arquivos_hashes"][primeiro] = hashlib.sha1(b"conteudo para algoritmo\n").hexdigest()
    catalogo_path.write_text(json.dumps(catalogo, ensure_ascii=False, indent=2), encoding="utf-8")

    resultado = sincronizador_harness.verificar_sincronizacao(str(tmp_path))
    assert resultado.sucesso is False
    assert resultado.codigo == "SYNC_DIVERGENTE"

