# -*- coding: utf-8 -*-
"""
Testes automatizados dos comandos CLI do AIDD Enterprise (scripts/aidd.py):
- cmd_audit
- cmd_plan
- cmd_apply
- cmd_compose_orca
- cmd_bench
- cmd_export_frontend
- cmd_refine_module
- cmd_setup
"""

import json
import os
import re
import subprocess
import sys
import pytest

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

AIDD_SCRIPT = os.path.join(SCRIPTS_DIR, "aidd.py")


@pytest.fixture
def suite_composta(tmp_path):
    """Compõe uma suíte real com módulo 'produtos' para os testes de audit e bench."""
    from compose_suite import compose_suite
    target = tmp_path / "suite-teste"
    compose_suite(str(target), "Suite Teste", ["produtos"])
    return target


# =============================================================================
# FASE 1 — AUDIT
# =============================================================================

def test_cmd_audit_sucesso_todos_gates_passam(suite_composta):
    """1.3 e 1.5: Executa cmd_audit contra projeto composto e confirma exit 0 e todos PASS."""
    proc = subprocess.run(
        [sys.executable, AIDD_SCRIPT, "audit", "--report", "--dir", str(suite_composta)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert proc.returncode == 0, f"cmd_audit falhou com exit {proc.returncode}:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    report_path = suite_composta / "RELATORIO-AUDITORIA.json"
    assert report_path.exists(), "RELATORIO-AUDITORIA.json não foi gerado"

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["resumo"]["status_geral"] == "APROVADO"
    assert report["resumo"]["falhas"] == 0
    assert report["resumo"]["aprovados"] >= 6

    # Confirma que cada gate reportou PASS
    for gate in report["gates"]:
        assert gate["status"] == "PASS", f"Gate {gate['gate']} falhou: {gate}"
        assert gate["exit_code"] == 0

    # Confirma lista canônica de gates executados
    nomes_gates = [g["gate"] for g in report["gates"]]
    for g_esperado in ["G_ESTRUTURA", "G_QUALIDADE", "G_TESTES", "G_CONTRACTS", "G_SEGREDOS", "G_HARNESS_COMPAT"]:
        assert g_esperado in nomes_gates, f"Gate {g_esperado} ausente da auditoria"


def test_cmd_audit_falha_deliberada_especifica_g_estrutura(suite_composta):
    """1.4 e 1.5: Remove PLANO-EXECUCAO-ESTRUTURADO.json e confirma exit 1 com G_ESTRUTURA FAIL."""
    plano_file = suite_composta / "PLANO-EXECUCAO-ESTRUTURADO.json"
    assert plano_file.exists()
    os.remove(str(plano_file))

    proc = subprocess.run(
        [sys.executable, AIDD_SCRIPT, "audit", "--report", "--dir", str(suite_composta)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert proc.returncode == 1, f"cmd_audit deveria retornar exit 1, retornou {proc.returncode}"

    report_path = suite_composta / "RELATORIO-AUDITORIA.json"
    assert report_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["resumo"]["status_geral"] == "REPROVADO"
    assert report["resumo"]["falhas"] >= 1

    # Confirma que especificamente G_ESTRUTURA falhou
    gate_estrutura = next((g for g in report["gates"] if g["gate"] == "G_ESTRUTURA"), None)
    assert gate_estrutura is not None, "G_ESTRUTURA não consta no relatório"
    assert gate_estrutura["status"] == "FAIL"
    assert gate_estrutura["exit_code"] != 0


# =============================================================================
# FASE 2 — PLAN / APPLY
# =============================================================================

def test_cmd_plan_dominio_conhecido(tmp_path):
    """2.1a e 2.3: Prompt com domínio conhecido detecta módulo e grava arquivos."""
    from aidd import cmd_plan
    cmd_plan("crie um crm", base_dir=str(tmp_path))

    target_dir = tmp_path / "app_crm-suite"
    assert target_dir.is_dir(), f"Diretório {target_dir} não foi criado"

    plano_path = target_dir / "PLANO-EXECUCAO-ESTRUTURADO.json"
    spec_path = target_dir / "SPEC-ARQUITETURA.md"
    assert plano_path.exists()
    assert spec_path.exists()

    plano = json.loads(plano_path.read_text(encoding="utf-8"))
    assert "crm" in plano["projeto"]["modulos"]
    assert plano["projeto"]["status"] == "PLANEJADO"

    spec = spec_path.read_text(encoding="utf-8")
    assert "CRM" in spec


def test_cmd_plan_dominio_desconhecido_fallback_palavras(tmp_path):
    """2.1b e 2.3: Prompt sem domínio conhecido extrai palavras (>3 letras sem stopwords)."""
    from aidd import cmd_plan
    cmd_plan("desenvolva consultoria veterinaria agendamento", base_dir=str(tmp_path))

    target_dir = tmp_path / "app_desenvolva-consultoria-veterinaria-suite"
    assert target_dir.is_dir()

    plano_path = target_dir / "PLANO-EXECUCAO-ESTRUTURADO.json"
    spec_path = target_dir / "SPEC-ARQUITETURA.md"
    assert plano_path.exists()
    assert spec_path.exists()

    plano = json.loads(plano_path.read_text(encoding="utf-8"))
    modulos = plano["projeto"]["modulos"]
    assert modulos == ["desenvolva", "consultoria", "veterinaria", "agendamento"]

    spec = spec_path.read_text(encoding="utf-8")
    for m in modulos:
        assert m.upper() in spec


def test_cmd_plan_prompt_sem_substancia_fallback_final(tmp_path):
    """2.1c e 2.3: Prompt sem palavras substanciais recorre a ['principal', 'configuracao']."""
    from aidd import cmd_plan
    cmd_plan("crie uma aplicacao com", base_dir=str(tmp_path))

    target_dir = tmp_path / "app_principal-configuracao-suite"
    assert target_dir.is_dir()

    plano_path = target_dir / "PLANO-EXECUCAO-ESTRUTURADO.json"
    spec_path = target_dir / "SPEC-ARQUITETURA.md"
    assert plano_path.exists()
    assert spec_path.exists()

    plano = json.loads(plano_path.read_text(encoding="utf-8"))
    assert plano["projeto"]["modulos"] == ["principal", "configuracao"]

    spec = spec_path.read_text(encoding="utf-8")
    assert "PRINCIPAL" in spec
    assert "CONFIGURACAO" in spec


def test_cmd_apply_executa_plano_com_sucesso(tmp_path):
    """2.2 e 2.3: cmd_apply lê PLANO-EXECUCAO-ESTRUTURADO.json e executa compose_suite."""
    import argparse
    from aidd import cmd_plan, cmd_apply

    cmd_plan("crie um crm", base_dir=str(tmp_path))
    target_dir = tmp_path / "app_crm-suite"
    assert (target_dir / "PLANO-EXECUCAO-ESTRUTURADO.json").exists()

    cmd_apply(argparse.Namespace(dir=str(target_dir)))

    # Verifica fatias verticais geradas fisicamente
    crm_module = target_dir / "src" / "modules" / "crm"
    assert crm_module.is_dir()
    for arq in ["__init__.py", "models.py", "services.py", "routes.py"]:
        assert (crm_module / arq).exists(), f"Arquivo {arq} ausente no módulo crm"

    assert (target_dir / "src" / "server.py").exists()


def test_cmd_apply_falha_quando_manifesto_ausente(tmp_path):
    """2.2 e 2.3 (falha): cmd_apply retorna exit 1 quando manifesto não existe."""
    proc = subprocess.run(
        [sys.executable, AIDD_SCRIPT, "apply", "--dir", str(tmp_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert proc.returncode == 1
    assert "não encontrado" in proc.stdout or "não encontrado" in proc.stderr


# =============================================================================
# FASE 3 — COMPOSE-ORCA
# =============================================================================

def test_cmd_compose_orca_sucesso_gera_estrutura_e_manifesto(tmp_path):
    """3.1, 3.2 e 3.4: cmd_compose_orca gera arquivos padrão por módulo e manifesto com status APROVADO."""
    target_dir = tmp_path / "orca-suite"
    modulos = ["produtos", "pedidos"]

    proc = subprocess.run(
        [sys.executable, AIDD_SCRIPT, "compose-orca", "--dir", str(target_dir), "--suite-name", "Orca Test Suite"] + modulos,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert proc.returncode == 0, f"compose-orca falhou: {proc.stdout}\n{proc.stderr}"

    # 3.1: Cada módulo gera __init__.py, models.py, services.py, routes.py, mcp_tools.py e tests/unit/test_{modulo}.py
    for mod in modulos:
        mod_dir = target_dir / "src" / "modules" / mod
        assert mod_dir.is_dir(), f"Pasta do módulo {mod} não criada"
        for arq in ["__init__.py", "models.py", "services.py", "routes.py", "mcp_tools.py"]:
            assert (mod_dir / arq).exists(), f"Arquivo {arq} ausente no módulo {mod}"

        test_file = target_dir / "tests" / "unit" / f"test_{mod}.py"
        assert test_file.exists(), f"Teste unitário do módulo {mod} não criado"

    # 3.2: COMPOSE-ORCA-MANIFEST.json gerado com schema esperado
    manifest_file = target_dir / "COMPOSE-ORCA-MANIFEST.json"
    assert manifest_file.exists(), "COMPOSE-ORCA-MANIFEST.json não gerado"

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest["total_modules"] == 2
    assert manifest["success"] == 2
    assert manifest["failed"] == 0
    assert manifest["errors"] == 0
    assert manifest["status"] == "APROVADO"
    for mod in modulos:
        assert mod in manifest["modules"]
        assert manifest["modules"][mod]["status"] == "success"
        assert manifest["modules"][mod]["files_created"] == 6


def test_cmd_compose_orca_falha_retorna_exit_1(tmp_path):
    """3.3 e 3.4: Força falha em módulo (nome com aspas gerando erro sintático no script worker) e valida exit 1."""
    target_dir = tmp_path / "orca-fail"
    modulo_invalido = 'inv"alid'

    proc = subprocess.run(
        [sys.executable, AIDD_SCRIPT, "compose-orca", "--dir", str(target_dir), modulo_invalido],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert proc.returncode == 1, f"Esperava exit 1, obteve {proc.returncode}"

    manifest_file = target_dir / "COMPOSE-ORCA-MANIFEST.json"
    assert manifest_file.exists()

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest["status"] == "REPROVADO"
    assert (manifest["failed"] > 0 or manifest["errors"] > 0)


# =============================================================================
# FASE 4 — BENCH
# =============================================================================

def test_cmd_bench_sucesso_concorrencia_wal(suite_composta):
    """4.1 a 4.4: Executa cmd_bench contra projeto composto, exit 0, zero falhas e contagem exata."""
    num_operacoes = 60
    proc = subprocess.run(
        [sys.executable, AIDD_SCRIPT, "bench", "-n", str(num_operacoes), "--dir", str(suite_composta)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert proc.returncode == 0, f"cmd_bench falhou:\n{proc.stdout}\n{proc.stderr}"

    stdout = proc.stdout
    # 4.3: Confirma números reportados
    m_ops = re.search(r"Total de Operações:\s*(\d+)", stdout)
    assert m_ops is not None, "Contagem de operações ausente na saída do benchmark"
    assert int(m_ops.group(1)) == num_operacoes

    m_pass = re.search(r"Sucessos \(PASS\):\s*(\d+)", stdout)
    assert m_pass is not None
    assert int(m_pass.group(1)) == num_operacoes

    m_fail = re.search(r"Falhas \(FAIL\):\s*(\d+)", stdout)
    assert m_fail is not None
    assert int(m_fail.group(1)) == 0

    assert "Throughput (RPS):" in stdout
    assert (suite_composta / "app.db").exists(), "app.db não foi criado no benchmark"


def test_cmd_bench_falha_quando_banco_inacessivel(tmp_path):
    """4.2 e 4.4 (falha): cmd_bench retorna exit 1 quando o diretório impede criação do app.db."""
    # Cria uma pasta chamada app.db para forçar falha no SQLite ao abrir
    app_db_block = tmp_path / "app.db"
    app_db_block.mkdir()

    proc = subprocess.run(
        [sys.executable, AIDD_SCRIPT, "bench", "-n", "10", "--dir", str(tmp_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert proc.returncode == 1
    assert "Falha ao executar benchmark" in proc.stdout or "Falha ao executar benchmark" in proc.stderr


# =============================================================================
# FASE 5 — EXPORT-FRONTEND
# =============================================================================

def _validar_balanceamento_delimitadores(codigo: str) -> bool:
    """Valida estruturalmente o balanceamento de delimitadores ({}, (), [])
    no código TS/TSX, desconsiderando strings e comentários via lexer."""
    pattern = re.compile(
        r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`|//[^\n]*|/\*[\s\S]*?\*/)',
        re.MULTILINE
    )
    limpo = pattern.sub(" ", codigo)

    stack = []
    pares = {")": "(", "}": "{", "]": "["}
    for ch in limpo:
        if ch in "({[":
            stack.append(ch)
        elif ch in ")}]":
            if not stack or stack[-1] != pares[ch]:
                return False
            stack.pop()
    return len(stack) == 0


def test_cmd_export_frontend_sucesso_gera_arquivos_ts(suite_composta):
    """5.1 e 5.4: Executa cmd_export_frontend contra suite composta e confirma geracao dos arquivos .ts/.tsx."""
    proc = subprocess.run(
        [sys.executable, AIDD_SCRIPT, "export-frontend", "--dir", str(suite_composta)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert proc.returncode == 0, f"cmd_export_frontend falhou:\n{proc.stdout}\n{proc.stderr}"

    frontend_dir = suite_composta / "frontend"
    assert frontend_dir.is_dir(), "Diretório frontend/ não foi criado"

    arquivos_esperados = [
        "package.json",
        "tsconfig.json",
        "next.config.js",
        "tailwind.config.ts",
        "postcss.config.js",
        "types.ts",
        os.path.join("lib", "api.ts"),
        os.path.join("app", "globals.css"),
        os.path.join("app", "layout.tsx"),
        os.path.join("app", "page.tsx"),
        os.path.join("app", "produtos", "page.tsx"),
    ]
    for rel_path in arquivos_esperados:
        arq = frontend_dir / rel_path
        assert arq.is_file(), f"Arquivo esperado '{rel_path}' não foi gerado em frontend/"


def test_cmd_export_frontend_validacao_sintatica_estrutural_ts(suite_composta):
    """5.3 e 5.4: Valida sintaxe e integridade estrutural do TypeScript gerado."""
    proc = subprocess.run(
        [sys.executable, AIDD_SCRIPT, "export-frontend", "--dir", str(suite_composta)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert proc.returncode == 0

    frontend_dir = suite_composta / "frontend"

    # 1. Validação de formato JSON válido
    pkg = json.loads((frontend_dir / "package.json").read_text(encoding="utf-8"))
    assert pkg["name"] == "aidd-frontend"
    assert "next" in pkg["dependencies"]

    tsconfig = json.loads((frontend_dir / "tsconfig.json").read_text(encoding="utf-8"))
    assert "compilerOptions" in tsconfig

    # 2. Tipos exportados em types.ts
    types_ts = (frontend_dir / "types.ts").read_text(encoding="utf-8")
    assert _validar_balanceamento_delimitadores(types_ts), "types.ts possui delimitadores desbalanceados"
    assert "export interface Produtos" in types_ts
    assert "export interface ProdutosCreatePayload" in types_ts
    assert "id: number;" in types_ts

    # 3. Biblioteca de API em lib/api.ts
    api_ts = (frontend_dir / "lib" / "api.ts").read_text(encoding="utf-8")
    assert _validar_balanceamento_delimitadores(api_ts), "lib/api.ts possui delimitadores desbalanceados"
    assert "export async function apiGet<T>" in api_ts
    assert "export async function apiPost<T>" in api_ts

    # 4. Componentes Next.js / React (layout.tsx, page.tsx, produtos/page.tsx)
    layout_tsx = (frontend_dir / "app" / "layout.tsx").read_text(encoding="utf-8")
    assert _validar_balanceamento_delimitadores(layout_tsx), "layout.tsx possui delimitadores desbalanceados"
    assert "export default function RootLayout" in layout_tsx
    assert "<html" in layout_tsx and "</html>" in layout_tsx

    home_tsx = (frontend_dir / "app" / "page.tsx").read_text(encoding="utf-8")
    assert _validar_balanceamento_delimitadores(home_tsx), "page.tsx possui delimitadores desbalanceados"
    assert "export default function Home" in home_tsx
    assert '"produtos"' in home_tsx

    prod_tsx = (frontend_dir / "app" / "produtos" / "page.tsx").read_text(encoding="utf-8")
    assert _validar_balanceamento_delimitadores(prod_tsx), "produtos/page.tsx possui delimitadores desbalanceados"
    assert "export default async function ProdutosPage" in prod_tsx
    assert "apiGet<Produtos[]>" in prod_tsx


def test_cmd_export_frontend_stack_invalida_lanca_erro(suite_composta):
    """5.2, 5.3 e 5.4: Valida rejeição explícita de stack diferente de nextjs."""
    from openapi_to_ts import export_frontend
    with pytest.raises(ValueError, match="Stack de frontend não suportado"):
        export_frontend(str(suite_composta), stack="vue")


# =============================================================================
# FASE 6 — REFINE-MODULE
# =============================================================================

def test_cmd_refine_module_executa_behave_cenario_real_sucesso(suite_composta):
    """6.1, 6.2 e 6.4: Executa cmd_refine_module com behave real e confirma cenarios aprovados."""
    features_dir = suite_composta / "features"
    steps_dir = features_dir / "steps"
    steps_dir.mkdir(parents=True, exist_ok=True)

    feat_path = features_dir / "produtos.feature"
    feat_path.write_text(
        "Feature: Validacao do modulo produtos\n"
        "  Scenario: Obter servico de produtos com integridade\n"
        "    Given que o servico de produtos esta disponivel\n"
        "    When eu instancio o servico\n"
        "    Then a resposta deve ser integra\n",
        encoding="utf-8"
    )

    step_path = steps_dir / "produtos_steps.py"
    step_path.write_text(
        "from behave import given, when, then\n"
        "from core.database import Database\n"
        "from core.events import EventBus\n"
        "from modules.produtos.services import ProdutosService\n"
        "\n"
        "@given('que o servico de produtos esta disponivel')\n"
        "def step_given_service(context):\n"
        "    context.db = Database('sqlite:///:memory:')\n"
        "    context.events = EventBus()\n"
        "\n"
        "@when('eu instancio o servico')\n"
        "def step_when_instanciar(context):\n"
        "    context.service = ProdutosService(context.db, context.events)\n"
        "\n"
        "@then('a resposta deve ser integra')\n"
        "def step_then_integro(context):\n"
        "    assert context.service is not None\n",
        encoding="utf-8"
    )

    proc = subprocess.run(
        [sys.executable, AIDD_SCRIPT, "refine-module", "produtos", "--dir", str(suite_composta)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert proc.returncode == 0, f"cmd_refine_module falhou:\n{proc.stdout}\n{proc.stderr}"
    assert "1 feature passed" in proc.stdout
    assert "1 scenario passed" in proc.stdout
    assert "100% dos cenários BDD do módulo 'produtos' homologados" in proc.stdout


def test_cmd_refine_module_falha_quando_cenario_bdd_falha(suite_composta):
    """6.2 e 6.4 (falha): Cenário BDD com asserção com falha retorna exit code diferente de zero."""
    features_dir = suite_composta / "features"
    steps_dir = features_dir / "steps"
    steps_dir.mkdir(parents=True, exist_ok=True)

    feat_path = features_dir / "produtos.feature"
    feat_path.write_text(
        "Feature: Falha deliberada de produto\n"
        "  Scenario: Validacao invalida\n"
        "    Given que forco uma falha no behave\n",
        encoding="utf-8"
    )

    step_path = steps_dir / "produtos_steps.py"
    step_path.write_text(
        "from behave import given\n"
        "@given('que forco uma falha no behave')\n"
        "def step_falha(context):\n"
        "    assert False, 'Falha BDD deliberada para teste'\n",
        encoding="utf-8"
    )

    proc = subprocess.run(
        [sys.executable, AIDD_SCRIPT, "refine-module", "produtos", "--dir", str(suite_composta)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert proc.returncode != 0
    assert "Cenários BDD do módulo 'produtos' falharam" in proc.stdout or "failed" in proc.stdout


def test_cmd_refine_module_falha_quando_spec_nao_encontrado(suite_composta):
    """6.2 e 6.4 (spec ausente): Retorna exit 1 quando o arquivo .feature não existe."""
    proc = subprocess.run(
        [sys.executable, AIDD_SCRIPT, "refine-module", "modulo_sem_feature", "--dir", str(suite_composta)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert proc.returncode == 1
    assert "Arquivo de especificação não encontrado" in proc.stdout


def test_cmd_refine_module_estrutural_argumentos_behave(tmp_path, monkeypatch):
    """6.3 e 6.4: Confirma que cmd_refine_module monta argumentos e ambiente corretos para invocar behave."""
    import argparse
    from aidd import cmd_refine_module

    feat_dir = tmp_path / "features"
    feat_dir.mkdir()
    feat_file = feat_dir / "modulo_mock.feature"
    feat_file.write_text("Feature: Mock", encoding="utf-8")

    chamadas = []

    def mock_subprocess_run(cmd, cwd=None, env=None, **kwargs):
        chamadas.append({"cmd": cmd, "cwd": cwd, "env": env})
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    args = argparse.Namespace(modulo="modulo_mock", spec=None, dir=str(tmp_path))
    cmd_refine_module(args)

    assert len(chamadas) == 1
    chamada = chamadas[0]
    expected_spec = os.path.abspath(str(feat_file))
    assert chamada["cmd"] == [sys.executable, "-m", "behave", expected_spec, "--no-capture"]
    assert chamada["cwd"] == str(tmp_path)
    src_esperado = os.path.abspath(os.path.join(str(tmp_path), "src"))
    assert src_esperado in chamada["env"]["PYTHONPATH"]


# =============================================================================
# FASE 7 — SETUP
# =============================================================================

def test_cmd_setup_diagnostico_completo_com_pip_isolado(monkeypatch, capsys):
    """7.1, 7.2 e 7.3: Testa a parte diagnóstica de cmd_setup isolando o pip install para não mutar o ambiente."""
    import argparse
    from aidd import cmd_setup

    pip_calls = []
    orig_run = subprocess.run

    def mock_run(cmd, *args, **kwargs):
        if isinstance(cmd, (list, tuple)) and ("pip" in cmd or any("install" == arg for arg in cmd)):
            pip_calls.append(list(cmd))
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="Sucesso mock", stderr="")
        return orig_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_run)

    args = argparse.Namespace()
    cmd_setup(args)

    captured = capsys.readouterr()
    stdout = captured.out

    assert len(pip_calls) >= 1
    pip_cmd_str = " ".join(pip_calls[0])
    assert "pip" in pip_cmd_str and "install" in pip_cmd_str

    assert "[AIDD SETUP] Diagnóstico e Inicialização Automática do Ambiente" in stdout
    assert "Python Runtime:" in stdout
    assert "Git CLI:" in stdout
    assert "ORCA ADE:" in stdout
    assert "Fleet Discovery:" in stdout
    assert "[SUCESSO]: Ambiente 100% pronto para compor e executar projetos AIDD" in stdout


def test_cmd_setup_tolerante_a_aviso_instalacao(monkeypatch, capsys):
    """7.2 e 7.3: Confirma que cmd_setup emite [WARN] e não retorna código de falha quando instalação falha."""
    import argparse
    from aidd import cmd_setup

    def mock_run_falha(cmd, *args, **kwargs):
        if isinstance(cmd, (list, tuple)) and ("pip" in cmd or any("install" == arg for arg in cmd)):
            return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="Rede offline mock")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", mock_run_falha)

    args = argparse.Namespace()
    cmd_setup(args)

    captured = capsys.readouterr()
    stdout = captured.out

    assert "[WARN] Aviso ao instalar requirements: Rede offline mock" in stdout
    assert "[SUCESSO]: Ambiente 100% pronto" in stdout

