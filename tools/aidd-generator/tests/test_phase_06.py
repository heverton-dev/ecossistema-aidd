# -*- coding: utf-8 -*-
"""
Testes reais da Phase 6 (Documentador Tripartite) — Correção 5/5.

Cobre: gates F1-F3 (validam arquivos REAIS no disco), DocumentadorFase6
(narrativas, renderização HTML/MD/PDF via ReportLab, fallback de emergência,
branch Typst mockado, index) e main(). Gera arquivos reais em tmp_path.
"""

import json
import sys
from pathlib import Path

import pytest

# PDF mínimo válido (parseável pelo pypdf) + padding para > 500 bytes
PDF_MINIMO_VALIDO = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n"
    b" " * 400
)


# =============================================================================
# GATE (estrutura base)
# =============================================================================

def test_gate_to_dict(documentador_06):
    assert documentador_06.Gate('F1', 'd', True, 'x').to_dict()['status'] == 'PASSOU'
    assert documentador_06.Gate('F1', 'd', False, 'x').to_dict()['status'] == 'FALHOU'


# =============================================================================
# GATES F1-F3 (arquivos reais)
# =============================================================================

def test_gate_f1_html_renderiza_ok(documentador_06, tmp_path):
    html = tmp_path / 'index.html'
    html.write_text(
        '<!DOCTYPE html><html><head></head><body><h1>Doc</h1></body></html>'
        + 'x' * 300, encoding='utf-8'
    )
    gate = documentador_06.ValidadorGatesPhase6._gate_f1_html_renderiza(
        {'documentos': {'html': str(html)}}
    )
    assert gate.passou is True
    assert 'DOM completo' in gate.detalhes


def test_gate_f1_html_inexistente(documentador_06, tmp_path):
    gate = documentador_06.ValidadorGatesPhase6._gate_f1_html_renderiza(
        {'documentos': {'html': str(tmp_path / 'nao-existe.html')}}
    )
    assert gate.passou is False
    assert 'não existe' in gate.detalhes


def test_gate_f1_html_sem_caminho(documentador_06):
    gate = documentador_06.ValidadorGatesPhase6._gate_f1_html_renderiza({'documentos': {}})
    assert gate.passou is False


def test_gate_f1_html_malformado(documentador_06, tmp_path):
    html = tmp_path / 'index.html'
    html.write_text('<p>sem doctype nem body</p>', encoding='utf-8')
    gate = documentador_06.ValidadorGatesPhase6._gate_f1_html_renderiza(
        {'documentos': {'html': str(html)}}
    )
    assert gate.passou is False


def test_gate_f2_pdf_gerado_ok(documentador_06, tmp_path):
    pdf = tmp_path / 'doc.pdf'
    pdf.write_bytes(PDF_MINIMO_VALIDO)
    gate = documentador_06.ValidadorGatesPhase6._gate_f2_pdf_gerado(
        {'documentos': {'pdf': str(pdf)}}
    )
    assert gate.passou is True


def test_gate_f2_pdf_sem_cabecalho(documentador_06, tmp_path):
    pdf = tmp_path / 'doc.pdf'
    pdf.write_bytes(b'NOTAPDF' + b'x' * 600)
    gate = documentador_06.ValidadorGatesPhase6._gate_f2_pdf_gerado(
        {'documentos': {'pdf': str(pdf)}}
    )
    assert gate.passou is False
    assert 'Cabeçalho' in gate.detalhes


def test_gate_f2_pdf_pequeno(documentador_06, tmp_path):
    pdf = tmp_path / 'doc.pdf'
    pdf.write_bytes(b'%PDF-1.4\n')
    gate = documentador_06.ValidadorGatesPhase6._gate_f2_pdf_gerado(
        {'documentos': {'pdf': str(pdf)}}
    )
    assert gate.passou is False


def test_gate_f3_markdown_valido_ok(documentador_06, tmp_path):
    md = tmp_path / 'doc.md'
    md.write_text('# Título\n\n## Seção\n\nConteúdo ' + 'x' * 200, encoding='utf-8')
    gate = documentador_06.ValidadorGatesPhase6._gate_f3_markdown_valido(
        {'documentos': {'md': str(md)}}
    )
    assert gate.passou is True


def test_gate_f3_markdown_sem_titulo(documentador_06, tmp_path):
    md = tmp_path / 'doc.md'
    md.write_text('texto sem cabeçalho ' + 'x' * 200, encoding='utf-8')
    gate = documentador_06.ValidadorGatesPhase6._gate_f3_markdown_valido(
        {'documentos': {'md': str(md)}}
    )
    assert gate.passou is False


def test_executar_todos_gates(documentador_06, tmp_path):
    html = tmp_path / 'index.html'
    html.write_text('<!DOCTYPE html><html><body><h1>x</h1></body></html>' + 'x' * 300, encoding='utf-8')
    pdf = tmp_path / 'doc.pdf'
    pdf.write_bytes(PDF_MINIMO_VALIDO)
    md = tmp_path / 'doc.md'
    md.write_text('# Título\n\n' + 'x' * 200, encoding='utf-8')

    docs = {
        'documentos': {
            'html': str(html),
            'md': str(md),
            'pdf': str(pdf),
        }
    }
    gates, todos_passaram = documentador_06.ValidadorGatesPhase6.executar_todos(docs)
    assert len(gates) == 3
    assert todos_passaram is True


# =============================================================================
# DOCUMENTADORFASE6
# =============================================================================

def test_documentador_init(tmp_path, documentador_06):
    doc = documentador_06.DocumentadorFase6(tmp_path / 'cache', output_base=tmp_path / 'output')
    assert (tmp_path / 'cache').exists()
    assert doc.output_base == tmp_path / 'output'


def test_gerar_narrativas(documentador_06):
    doc = documentador_06.DocumentadorFase6(Path('.'))
    narrativas = doc._gerar_narrativas('proj-x', 'Título X', {'stack': 'Python'})

    assert narrativas['video_id'] == 'proj-x'
    assert narrativas['titulo'] == 'Título X'
    assert 'Python' in narrativas['decisoes_stack']
    assert len(narrativas['camadas']) == 5
    assert 'AIDD' in narrativas['arquitetura_aidd']


def test_gerar_narrativas_com_dados_reais_de_fase2_e_fase3(documentador_06):
    """Achado na integração ponta a ponta: _gerar_narrativas só sabia ler
    {'stack': ...} de teste — nunca o formato real que analise_phase2.json
    (stack_recomendado) e design_aidd_phase3.json realmente produzem."""
    doc = documentador_06.DocumentadorFase6(Path('.'))
    contexto_real = {
        'objetivo': 'Rastreador de hábitos via linha de comando',
        'stack_recomendado': {
            'linguagem': 'Python 3.11+',
            'framework': 'Typer',
            'banco': 'SQLite',
        },
    }
    narrativas = doc._gerar_narrativas('habit-cli', 'Habit CLI', contexto_real)

    assert 'Python 3.11+' in narrativas['decisoes_stack']
    assert 'Typer' in narrativas['decisoes_stack']
    assert 'SQLite' in narrativas['decisoes_stack']
    assert narrativas['descricao'] == 'Rastreador de hábitos via linha de comando'


def test_escrever_markdown(documentador_06, tmp_path):
    doc = documentador_06.DocumentadorFase6(Path('.'))
    narrativas = doc._gerar_narrativas('proj-x', 'Título', {})
    path_md = tmp_path / 'doc.md'
    doc._escrever_markdown(path_md, narrativas)

    conteudo = path_md.read_text(encoding='utf-8')
    assert conteudo.startswith('# Título')
    assert '## 1. Visão Geral' in conteudo
    assert '## 2. Arquitetura AIDD' in conteudo
    assert '## 5. Auditoria de Gates' in conteudo


def test_escrever_html(documentador_06, tmp_path):
    doc = documentador_06.DocumentadorFase6(Path('.'))
    narrativas = doc._gerar_narrativas('proj-x', 'Título', {})
    path_html = tmp_path / 'index.html'
    doc._escrever_html(path_html, narrativas)

    conteudo = path_html.read_text(encoding='utf-8')
    assert '<!DOCTYPE html>' in conteudo
    assert '<html lang="pt-BR">' in conteudo
    assert '<body>' in conteudo and '</body>' in conteudo
    assert 'AIDD Documentação' in conteudo


def test_escrever_pdf_reportlab(documentador_06, tmp_path):
    doc = documentador_06.DocumentadorFase6(Path('.'))
    narrativas = doc._gerar_narrativas('proj-x', 'Título', {})
    path_pdf = tmp_path / 'doc.pdf'
    doc._escrever_pdf(path_pdf, tmp_path, narrativas)

    assert path_pdf.exists()
    assert path_pdf.stat().st_size > 500
    with open(path_pdf, 'rb') as f:
        assert f.read(5) == b'%PDF-'


def test_escrever_pdf_fallback_emergencia(documentador_06, tmp_path, monkeypatch):
    monkeypatch.setattr(documentador_06.shutil, 'which', lambda nome: None)
    monkeypatch.setitem(sys.modules, 'reportlab', None)

    doc = documentador_06.DocumentadorFase6(Path('.'))
    narrativas = doc._gerar_narrativas('proj-x', 'Título', {})
    path_pdf = tmp_path / 'doc.pdf'
    doc._escrever_pdf(path_pdf, tmp_path, narrativas)

    assert path_pdf.exists()
    with open(path_pdf, 'rb') as f:
        assert f.read(5) == b'%PDF-'


def test_escrever_pdf_typst(documentador_06, tmp_path, monkeypatch):
    def fake_run(cmd, capture_output=True, text=True):
        # cmd = [typst, 'compile', typ_file, pdf_path]
        Path(cmd[3]).write_bytes(b'%PDF-1.4\n' + b'0' * 700)
        return type('Res', (), {'returncode': 0})()

    monkeypatch.setattr(documentador_06.shutil, 'which', lambda nome: '/fake/typst')
    monkeypatch.setattr(documentador_06.subprocess, 'run', fake_run)

    doc = documentador_06.DocumentadorFase6(Path('.'))
    narrativas = doc._gerar_narrativas('proj-x', 'Título', {})
    path_pdf = tmp_path / 'doc.pdf'
    doc._escrever_pdf(path_pdf, tmp_path, narrativas)

    assert path_pdf.exists()
    assert (tmp_path / 'documento.typ').exists()
    assert path_pdf.stat().st_size > 500


def test_renderizar_formatos(documentador_06, tmp_path):
    doc = documentador_06.DocumentadorFase6(tmp_path / 'cache', output_base=tmp_path / 'output')
    narrativas = doc._gerar_narrativas('proj-x', 'Título', {})
    docs = doc._renderizar_formatos('proj-x', 'Título', narrativas)

    assert docs['html_valido'] is True
    assert docs['md_valido'] is True
    assert docs['pdf_gerado'] is True
    assert (tmp_path / 'output' / 'proj-x' / 'documentos' / 'index.html').exists()
    assert (tmp_path / 'output' / 'proj-x' / 'documentos' / 'documento.md').exists()
    assert (tmp_path / 'output' / 'proj-x' / 'documentos' / 'documento.pdf').exists()


def test_gerar_index(documentador_06):
    docs = {'documentos': {'html': 'a', 'md': 'b', 'pdf': 'c'}}
    gates = [
        documentador_06.Gate('F1', 'd', True, 'x'),
        documentador_06.Gate('F2', 'd', True, 'x'),
        documentador_06.Gate('F3', 'd', True, 'x'),
    ]
    index = documentador_06.DocumentadorFase6(Path('.'))._gerar_index(docs, gates, 1.5)

    assert index['fase_id'] == 'phase_06_documentation'
    assert index['status'] == 'COMPLETO'
    assert index['processamento']['formatos'] == ['html', 'md', 'pdf']
    assert index['tokens']['consumidos'] == 0  # 100% templates Python, zero chamada LLM
    assert index['tokens']['percentual_determinismo'] == 100
    assert index['resume_info']['proxima_fase'] == 'phase_07_auto_critique'
    assert index['resume_info']['pode_prosseguir'] is True


def test_executar_sucesso(documentador_06, tmp_path):
    doc = documentador_06.DocumentadorFase6(tmp_path / 'cache', output_base=tmp_path / 'output')
    index = doc.executar('proj-x', {'stack': 'Python'}, titulo='Doc Proj X')

    assert index is not None
    assert index['status'] == 'COMPLETO'
    assert (tmp_path / 'cache' / '_phase_06_index.json').exists()
    assert (tmp_path / 'cache' / 'data' / 'documentacao_phase6.json').exists()
    assert (tmp_path / 'output' / 'proj-x' / 'documentos' / 'documento.pdf').exists()


# =============================================================================
# MAIN (CLI)
# =============================================================================

def test_main_sucesso(documentador_06, tmp_path, monkeypatch):
    monkeypatch.setattr(
        sys, 'argv',
        ['06_documentador.py', 'proj-x', 'Título',
         '--cache-dir', str(tmp_path / 'cache'),
         '--output-dir', str(tmp_path / 'output')]
    )
    monkeypatch.setattr(
        documentador_06.DocumentadorFase6, 'executar',
        lambda self, nome, design, titulo=None: {'status': 'COMPLETO'}
    )
    with pytest.raises(SystemExit) as exc:
        documentador_06.main()
    assert exc.value.code == 0


def test_main_carrega_contexto_real_de_fases_anteriores(documentador_06, tmp_path, monkeypatch):
    """main() não pode mais chamar executar(nome, {}, ...) fixo — precisa
    ler analise_phase2.json e design_aidd_phase3.json de cache-dir/data/
    se existirem (achado na integração ponta a ponta do pipeline)."""
    data_dir = tmp_path / 'cache' / 'data'
    data_dir.mkdir(parents=True)
    (data_dir / 'analise_phase2.json').write_text(
        json.dumps({'objetivo': 'Objetivo real da Fase 2'}), encoding='utf-8'
    )
    (data_dir / 'design_aidd_phase3.json').write_text(
        json.dumps({'design': {'camadas': []}}), encoding='utf-8'
    )

    monkeypatch.setattr(
        sys, 'argv',
        ['06_documentador.py', 'proj-x', 'Título',
         '--cache-dir', str(tmp_path / 'cache'),
         '--output-dir', str(tmp_path / 'output')]
    )

    contexto_recebido = {}

    def executar_fake(self, nome, design, titulo=None):
        contexto_recebido.update(design)
        return {'status': 'COMPLETO'}

    monkeypatch.setattr(documentador_06.DocumentadorFase6, 'executar', executar_fake)
    with pytest.raises(SystemExit):
        documentador_06.main()

    assert contexto_recebido['objetivo'] == 'Objetivo real da Fase 2'
    assert contexto_recebido['design'] == {'camadas': []}


def test_main_falha(documentador_06, tmp_path, monkeypatch):
    monkeypatch.setattr(
        sys, 'argv',
        ['06_documentador.py', 'proj-x', 'Título',
         '--cache-dir', str(tmp_path / 'cache'),
         '--output-dir', str(tmp_path / 'output')]
    )
    monkeypatch.setattr(
        documentador_06.DocumentadorFase6, 'executar',
        lambda self, nome, design, titulo=None: None
    )
    with pytest.raises(SystemExit) as exc:
        documentador_06.main()
    assert exc.value.code == 1