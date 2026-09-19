# -*- coding: utf-8 -*-
"""
Testes reais da etapa final dos fluxos: gerador do livro-texto do projeto
(scripts/gerador_livro_projeto.py) e sua trava de honestidade
(gates/G_LIVRO_EVIDENCIA.py).

Cobre o contrato que importa:
  - o livro so afirma o que tem artefato que comprove;
  - artefato ausente vira declaracao explicita, nunca texto inventado;
  - o gate REPROVA de verdade quando o livro cita arquivo inexistente,
    quando falta rastreabilidade, quando sobra marcador de trabalho inacabado
    e quando o manifesto mente sobre o que leu;
  - o gate NAO reprova o apendice de estado honesto por citar o que falta.

Nada aqui e simulado: cada teste monta artefatos reais em disco, roda a CLI
como subprocesso e confere o codigo de saida verdadeiro.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
GERADOR = RAIZ / "scripts" / "gerador_livro_projeto.py"
GATE = RAIZ / "gates" / "G_LIVRO_EVIDENCIA.py"


def rodar(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Fixtures: artefatos reais da esteira
# ---------------------------------------------------------------------------

PLANNER_MINIMO = {
    "meta": {
        "projeto_nome": "Clinica Teste",
        "slug": "clinica",
        "dominio": "saude",
        "descricao": "Sistema de teste do gerador de livro",
        "fluxo_alvo": "fluxo_01_generator",
    },
    "ddd_bounded_contexts": [{
        "modulo": "agenda",
        "descricao": "Contexto de agendamento",
        "entidades": [{
            "nome": "Consulta",
            "atributos": {"id": "str", "paciente": "str", "inicio": "datetime"},
            "regras_invariantes": ["Nao permitir duas consultas no mesmo horario"],
        }],
    }],
    "bdd_cenarios": [{
        "id": "SCN-001", "modulo": "agenda", "titulo": "Agendamento com sucesso",
        "dado": "Um horario livre", "quando": "O paciente agenda",
        "entao": "A consulta e persistida",
    }],
    "quarteto_sine_qua_non": {
        "swagger": {"ativo": True, "prefixo": "/swagger"},
        "webhooks": {"ativo": True, "eventos_suportados": ["consulta.criada"]},
        "mcp": {"ativo": True, "ferramentas_expostas": ["listar_consultas"]},
        "docs": {"ativo": True, "guia_usuario": True},
    },
    "infraestrutura_alvo": {"banco_dados": "postgresql", "porta_api": 8000},
}

HANDOFF_ENGINE = {
    "versao_schema": "1.0.0",
    "origem_engine": "aidd-generator",
    "projeto_slug": "clinica",
    "slices_geradas": [{
        "slice_nome": "agenda",
        "caminho_src": "src/modules/agenda",
        "endpoints": [{"rota": "/api/agenda", "metodo": "GET", "funcao": "listar"}],
        "tabelas_sql": ["agenda"],
    }],
    "artefatos_frontend": {
        "tecnologia": "nextjs_app_router",
        "paginas_geradas": ["/agenda"],
        "origem_design": "custom_tdd",
    },
    "testes_executados": {"total": 12, "passaram": 12, "falharam": 0, "zero_stubs": True},
}


@pytest.fixture
def projeto(tmp_path):
    """Projeto com os artefatos das etapas 2 e 3 da esteira."""
    pasta = tmp_path / "proj"
    pasta.mkdir()
    (pasta / "PLANNER.json").write_text(
        json.dumps(PLANNER_MINIMO, ensure_ascii=False), encoding="utf-8")
    (pasta / "HANDOFF_ENGINE_MASTER.json").write_text(
        json.dumps(HANDOFF_ENGINE, ensure_ascii=False), encoding="utf-8")
    (pasta / "src" / "modules" / "agenda").mkdir(parents=True)
    (pasta / "src" / "modules" / "agenda" / "test_agenda.py").write_text("# teste\n", encoding="utf-8")
    return pasta


# ---------------------------------------------------------------------------
# Gerador
# ---------------------------------------------------------------------------

def test_gerador_recusa_pasta_sem_nenhum_artefato(tmp_path):
    vazia = tmp_path / "vazia"
    vazia.mkdir()
    res = rodar(GERADOR, str(vazia))
    assert res.returncode == 1
    assert "nenhum artefato" in (res.stdout + res.stderr).lower()


def test_gerador_monta_partes_e_manifesto(projeto):
    res = rodar(GERADOR, str(projeto))
    assert res.returncode == 0, res.stderr

    manifesto = json.loads((projeto / "livro" / "livro.json").read_text(encoding="utf-8"))
    assert manifesto["titulo"] == "Clinica Teste"
    assert "PLANNER.json" in manifesto["artefatos_lidos"]
    assert "HANDOFF_ENGINE_MASTER.json" in manifesto["artefatos_lidos"]
    assert any("ORQUESTRACAO" in a for a in manifesto["artefatos_ausentes"])

    for nome in manifesto["partes"]:
        assert (projeto / "livro" / "partes" / nome).is_file()


def test_livro_transcreve_dado_real_do_plano(projeto):
    rodar(GERADOR, str(projeto))
    visao = (projeto / "livro" / "partes" / "01-visao.md").read_text(encoding="utf-8")
    assert "agenda" in visao
    assert "Consulta" in visao
    assert "Nao permitir duas consultas no mesmo horario" in visao      # invariante
    assert "Agendamento com sucesso" in visao                            # cenario BDD


def test_livro_registra_ausencia_em_vez_de_inventar(projeto):
    rodar(GERADOR, str(projeto))
    apendices = (projeto / "livro" / "partes" / "05-apendices.md").read_text(encoding="utf-8")
    assert "ORQUESTRACAO_EXECUCAO.json" in apendices
    assert "relatorio_final.md" in apendices

    operacao = (projeto / "livro" / "partes" / "04-operacao.md").read_text(encoding="utf-8")
    assert "artefato ausente" in operacao.lower()


def test_livro_confronta_promessa_com_disco(projeto):
    rodar(GERADOR, str(projeto))
    arquitetura = (projeto / "livro" / "partes" / "02-arquitetura.md").read_text(encoding="utf-8")
    assert "src/modules/agenda" in arquitetura, "modulo real em disco deve aparecer"
    assert "/api/agenda" in arquitetura, "rota registrada no contrato deve aparecer"


def test_toda_parte_de_conteudo_declara_rastreabilidade(projeto):
    rodar(GERADOR, str(projeto))
    partes = sorted((projeto / "livro" / "partes").glob("0[1-4]*.md"))
    assert partes
    for parte in partes:
        assert "Rastreabilidade" in parte.read_text(encoding="utf-8"), parte.name


# ---------------------------------------------------------------------------
# Gate — precisa aprovar o certo e reprovar o errado
# ---------------------------------------------------------------------------

def test_gate_aprova_livro_integro(projeto):
    rodar(GERADOR, str(projeto))
    res = rodar(GATE, "--projeto", str(projeto))
    assert res.returncode == 0, res.stdout


def test_gate_nao_pune_apendice_por_citar_o_que_falta(projeto):
    """O apendice de estado honesto cita artefatos ausentes — essa e a funcao dele."""
    rodar(GERADOR, str(projeto))
    manifesto = json.loads((projeto / "livro" / "livro.json").read_text(encoding="utf-8"))
    assert manifesto["artefatos_ausentes"], "o cenario exige artefatos ausentes"
    assert rodar(GATE, "--projeto", str(projeto)).returncode == 0


def test_gate_reprova_arquivo_citado_inexistente(projeto):
    rodar(GERADOR, str(projeto))
    parte = projeto / "livro" / "partes" / "01-visao.md"
    parte.write_text(parte.read_text(encoding="utf-8")
                     + "\n\nVeja `modulo/inexistente.py` para detalhes.\n", encoding="utf-8")
    res = rodar(GATE, "--projeto", str(projeto))
    assert res.returncode == 1
    assert "nao existe" in res.stdout


def test_gate_reprova_marcador_de_trabalho_inacabado(projeto):
    rodar(GERADOR, str(projeto))
    parte = projeto / "livro" / "partes" / "01-visao.md"
    parte.write_text(parte.read_text(encoding="utf-8") + "\n\nTODO: escrever isto.\n",
                     encoding="utf-8")
    res = rodar(GATE, "--projeto", str(projeto))
    assert res.returncode == 1
    assert "inacabado" in res.stdout


def test_gate_nao_confunde_palavra_portuguesa_com_marcador(projeto):
    """'Todo sistema nasce com...' e portugues correto, nao trabalho pendente."""
    rodar(GERADOR, str(projeto))
    parte = projeto / "livro" / "partes" / "01-visao.md"
    parte.write_text(parte.read_text(encoding="utf-8")
                     + "\n\nTodo sistema nasce com quatro portas.\n", encoding="utf-8")
    assert rodar(GATE, "--projeto", str(projeto)).returncode == 0


def test_gate_reprova_capitulo_sem_rastreabilidade(projeto):
    rodar(GERADOR, str(projeto))
    parte = projeto / "livro" / "partes" / "01-visao.md"
    parte.write_text("# Capitulo solto\n\nAfirmacao sem nenhuma fonte declarada.\n",
                     encoding="utf-8")
    res = rodar(GATE, "--projeto", str(projeto))
    assert res.returncode == 1
    assert "rastreabilidade" in res.stdout.lower()


def test_gate_reprova_manifesto_que_mente_sobre_o_que_leu(projeto):
    rodar(GERADOR, str(projeto))
    caminho = projeto / "livro" / "livro.json"
    manifesto = json.loads(caminho.read_text(encoding="utf-8"))
    manifesto["artefatos_lidos"].append("ARQUIVO_QUE_NUNCA_EXISTIU.json")
    caminho.write_text(json.dumps(manifesto, ensure_ascii=False), encoding="utf-8")
    res = rodar(GATE, "--projeto", str(projeto))
    assert res.returncode == 1
    assert "afirma ter lido" in res.stdout


def test_gate_reprova_parte_declarada_e_ausente(projeto):
    rodar(GERADOR, str(projeto))
    (projeto / "livro" / "partes" / "01-visao.md").unlink()
    res = rodar(GATE, "--projeto", str(projeto))
    assert res.returncode == 1
    assert "ausente em disco" in res.stdout


def test_gate_sem_livro_falha_com_mensagem_clara(tmp_path):
    res = rodar(GATE, "--projeto", str(tmp_path))
    assert res.returncode == 1
    assert "nao encontrada" in (res.stdout + res.stderr).lower()


def test_gate_modo_json_para_automacao(projeto):
    rodar(GERADOR, str(projeto))
    res = rodar(GATE, "--projeto", str(projeto), "--json")
    assert res.returncode == 0
    dados = json.loads(res.stdout)
    assert dados["aprovado"] is True
    assert dados["partes"] >= 5
    assert dados["citacoes_verificadas"] > 0
