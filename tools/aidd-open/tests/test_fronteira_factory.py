# -*- coding: utf-8 -*-
"""
Teste de Fronteira e Almoxarifado do AIDD-Open / Factory (Ticket 13, D1 / DoD 7).

Regras de conformidade:
1. vsa_generator deve buscar moldes e templates exclusivamente através do
   almoxarifado unico do ecossistema via `aidd_forge.core.almoxarifado.caminho_peca`.
2. A factory deve ler tickets de `HANDOFF_PLANNER_ENGINE.json` (C2).
3. A factory deve gravar estritamente dentro de sua zona permitida no projeto:
   `src/modules/<dominio>/**` e `HANDOFF_ENGINE_MASTER.json` (C3).
   Nenhum arquivo de Shared Kernel (src/core), servidor (src/server.py),
   estúdios/static, gateway, compose ou env deve ser gravado pela factory.
"""
import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch

# Garantir imports da ferramenta e do ecossistema
ROOT_DIR = Path(__file__).resolve().parents[3]
OPEN_DIR = ROOT_DIR / "tools" / "aidd-open"
FORGE_DIR = ROOT_DIR / "tools" / "aidd-forge"

for p in (str(ROOT_DIR), str(OPEN_DIR), str(OPEN_DIR / "src"), str(FORGE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from aidd_forge.core.almoxarifado import caminho_peca
from core import vsa_generator
from scripts import pipeline_factory


def _criar_handoff_planner_c2(pasta: Path, modulos: list[str]) -> Path:
    """Cria um HANDOFF_PLANNER_ENGINE.json determinístico com tickets roteados."""
    tickets = []
    modulos_funcionais = []
    for idx, slug in enumerate(modulos, 1):
        modulos_funcionais.append({
            "nome": slug.capitalize(),
            "slug": slug,
            "entidades": [
                {
                    "nome": f"Item{slug.capitalize()}",
                    "campos": [
                        {"nome": "titulo", "tipo": "string", "obrigatorio": True},
                        {"nome": "descricao", "tipo": "string", "obrigatorio": False},
                    ],
                }
            ],
            "regras_negocio": [
                {"id": f"RN-{slug}-01", "descricao": f"Regra {slug}", "criterio_aceitacao": "Sucesso"}
            ],
        })
        tickets.append({
            "id": f"TCK-C{idx:02d}",
            "ferramenta_destino": "aidd-open",
            "entrada": {
                "modulo": slug.capitalize(),
                "slug": slug,
                "entidades": [f"Item{slug.capitalize()}"],
                "regras_negocio": [f"RN-{slug}-01"],
                "fatia_esperada": f"src/modules/{slug}/",
            },
            "saida_esperada": f"Fatia vertical `{slug}` em src/modules/{slug}/",
            "pecas_do_almoxarifado": [
                "moldes/quarteto/variantes/aidd-open/openapi.py",
                "moldes/quarteto/variantes/aidd-open/webhooks.py",
                "moldes/quarteto/variantes/aidd-open/mcp_server.py",
            ],
            "criterio_de_aceite": f"`src/modules/{slug}/` gerada e C3 emitido",
        })

    c2_dados = {
        "versao_schema": "1.0.0",
        "fluxo_alvo": 2,
        "metadados_projeto": {
            "nome": "Clinica Open",
            "slug": "clinica-open",
            "dominio": "saude",
            "descricao": "Sistema de gestão de clínicas integrado com open-source",
        },
        "quarteto_sine_qua_non": {
            "swagger": True,
            "webhooks": True,
            "mcp": True,
            "documentacao": True,
        },
        "arquitetura_alvo": {
            "padrao_frontend": "tanstack_router_typescript_tailwind",
            "padrao_backend": "fastapi_modular_vsa",
            "persistencia": "sqlite_wal",
        },
        "modulos_funcionais": modulos_funcionais,
        "camadas": ["dominio", "aplicacao", "infraestrutura", "interfaces"],
        "fases": ["F01-planejamento", "F02-construtor-open", "F03-master"],
        "tickets": tickets,
        "entrada_construtor": {
            "plano_motores": {
                "nicho_slug": "clinica",
                "nicho_nome_exibicao": "Clínica Médica",
                "ferramentas": [{"nome": m.capitalize(), "descricao": f"Serviço {m}"} for m in modulos],
            }
        },
        "perfil_app": {
            "modulos": modulos,
            "entidades": [f"Item{m.capitalize()}" for m in modulos],
            "banco": "sqlite",
            "rotas_quarteto": ["/openapi.json", "/webhooks", "/mcp", "/docs"],
            "portas": [3000, 8000],
        },
    }

    caminho = pasta / "HANDOFF_PLANNER_ENGINE.json"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(c2_dados, indent=2, ensure_ascii=False), encoding="utf-8")
    return caminho


def test_vsa_generator_consome_templates_do_almoxarifado():
    """Valida que vsa_generator consulta templates exclusivamente via caminho_peca do almoxarifado."""
    assert hasattr(vsa_generator, "caminho_peca"), (
        "vsa_generator deve importar e disponibilizar caminho_peca de aidd_forge.core.almoxarifado"
    )

    chamadas_almoxarifado = []

    def fake_caminho_peca(nome: str, raiz=None):
        chamadas_almoxarifado.append(nome)
        return caminho_peca(nome, raiz=ROOT_DIR)

    with patch.object(vsa_generator, "caminho_peca", side_effect=fake_caminho_peca):
        # Dispara resolução/carregamento de moldes em vsa_generator
        if hasattr(vsa_generator, "obter_molde_vsa"):
            vsa_generator.obter_molde_vsa("openapi.py")
        elif hasattr(vsa_generator, "_carregar_template"):
            vsa_generator._carregar_template("openapi.py")
        else:
            # Invoca rotina de moldes ou shared_kernel para disparar caminho_peca
            assert False, "vsa_generator não possui rotina de consumo via almoxarifado caminho_peca"

    assert len(chamadas_almoxarifado) > 0, "caminho_peca não foi chamado para obter moldes"


def test_factory_escreve_apenas_fatias_e_c3(tmp_path: Path):
    """Valida que a factory escreve APENAS src/modules/<dominio>/ e HANDOFF_ENGINE_MASTER.json."""
    c2_file = _criar_handoff_planner_c2(tmp_path, ["prontuarios", "agendamentos"])
    
    # Executa a factory apontando para tmp_path
    exit_code = pipeline_factory.executar_pipeline(
        plano_path=str(c2_file),
        pasta_destino=str(tmp_path),
        incluir_llm=False
    )
    assert exit_code == 0, "Execução da factory falhou"

    # Verificar que C3 foi gerado
    c3_file = tmp_path / "HANDOFF_ENGINE_MASTER.json"
    assert c3_file.is_file(), "HANDOFF_ENGINE_MASTER.json (C3) não foi gerado pela factory"

    c3_dados = json.loads(c3_file.read_text(encoding="utf-8"))
    assert c3_dados.get("origem_engine") == "aidd-open"
    assert len(c3_dados.get("slices_geradas", [])) == 2
    assert c3_dados.get("arquivos_fora_da_zona") == []

    # Verificar fatias geradas
    for slug in ("prontuarios", "agendamentos"):
        modulo_dir = tmp_path / "src" / "modules" / slug
        assert modulo_dir.is_dir(), f"Fatia src/modules/{slug} não foi criada"
        assert (modulo_dir / "models.py").is_file()
        assert (modulo_dir / "repositories.py").is_file()
        assert (modulo_dir / "services.py").is_file()
        assert (modulo_dir / "routes.py").is_file()

    # Validação estrita de fronteira: NENHUM arquivo fora de src/modules/ e C3
    todos_arquivos = [
        p.relative_to(tmp_path).as_posix()
        for p in tmp_path.rglob("*")
        if p.is_file()
    ]

    arquivos_ilegais = []
    for arq in todos_arquivos:
        if arq in ("HANDOFF_PLANNER_ENGINE.json", "HANDOFF_ENGINE_MASTER.json"):
            continue
        if arq.startswith("src/modules/"):
            continue
        if arq.startswith(".aidd/cache/"):
            continue
        arquivos_ilegais.append(arq)

    assert not arquivos_ilegais, (
        f"A factory violou a fronteira de escrita! Arquivos proibidos gerados: {arquivos_ilegais}. "
        "A factory deve escrever exclusivamente src/modules/<dominio>/ e HANDOFF_ENGINE_MASTER.json."
    )
