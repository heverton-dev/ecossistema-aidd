# -*- coding: utf-8 -*-
"""
Testes reais da Phase 6 (Documentador Tripartite) — NIH #25 (Pandoc).

Cobre: gates F1-F3 (validam arquivos REAIS no disco), DocumentadorFase6
(narrativas, fonte única markdown, conversão HTML/PDF via Pandoc — ramos
herméticos mockando subprocess + teste de integração real quando o pandoc
está instalado, index) e main(). Gera arquivos reais em tmp_path.

NIH #25: não há mais templates paralelos por formato. O markdown (documento.md)
é a fonte única; HTML e PDF são derivados por conversão Pandoc.
"""

import json
import shutil
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


def test_pandoc_disponivel_retorna_bool(documentador_06):
    assert isinstance(documentador_06.DocumentadorFase6.pandoc_disponivel(), bool)


def test_converter_md_para_html_pandoc_ok(documentador_06, tmp_path, monkeypatch):
    """Conversão HTML via Pandoc — ramo hermético com subprocess mockado."""
    def fake_run(cmd, capture_output=True, text=True):
        # [pandoc, md, --standalone, --metadata, title=..., -o, html_path]
        Path(cmd[-1]).write_text(
            '<!DOCTYPE html><html><head><title>Meu Doc</title></head>'
            '<body><h1>Meu Doc</h1></body></html>' + 'x' * 400, encoding='utf-8'
        )
        return type('Res', (), {'returncode': 0, 'stderr': ''})()

    monkeypatch.setattr(documentador_06.shutil, 'which', lambda nome: '/fake/pandoc')
    monkeypatch.setattr(documentador_06.subprocess, 'run', fake_run)

    doc = documentador_06.DocumentadorFase6(Path('.'))
    path_md = tmp_path / 'documento.md'
    path_html = tmp_path / 'index.html'
    path_md.write_text('# Título\n\n## 1. Visão Geral\nConteúdo', encoding='utf-8')

    assert doc._converter_md_para_html(path_md, path_html, 'Meu Doc') is True
    assert path_html.exists()
    assert '<html' in path_html.read_text(encoding='utf-8')


def test_converter_md_para_html_sem_pandoc(documentador_06, tmp_path, monkeypatch):
    """Sem pandoc no PATH: conversão falha honestamente (não escreve stub)."""
    monkeypatch.setattr(documentador_06.shutil, 'which', lambda nome: None)

    doc = documentador_06.DocumentadorFase6(Path('.'))
    path_md = tmp_path / 'documento.md'
    path_html = tmp_path / 'index.html'
    path_md.write_text('# Título', encoding='utf-8')

    assert doc._converter_md_para_html(path_md, path_html, 'Título') is False
    assert not path_html.exists()


def test_converter_md_para_html_pandoc_falha(documentador_06, tmp_path, monkeypatch):
    """Pandoc executa mas retorna fallha — conversão deve reprovar, sem arquivo."""
    def fake_run(cmd, capture_output=True, text=True):
        return type('Res', (), {'returncode': 1, 'stderr': 'boom'})()
    monkeypatch.setattr(documentador_06.shutil, 'which', lambda nome: '/fake/pandoc')
    monkeypatch.setattr(documentador_06.subprocess, 'run', fake_run)

    doc = documentador_06.DocumentadorFase6(Path('.'))
    path_md = tmp_path / 'documento.md'
    path_html = tmp_path / 'index.html'
    path_md.write_text('# Título', encoding='utf-8')

    assert doc._converter_md_para_html(path_md, path_html, 'Título') is False
    assert not path_html.exists()


def test_converter_md_para_pdf_pandoc_ok(documentador_06, tmp_path, monkeypatch):
    """Conversão PDF via Pandoc (engine typst) — ramo hermético mockado."""
    def fake_run(cmd, capture_output=True, text=True):
        Path(cmd[-1]).write_bytes(b'%PDF-1.4\n' + b'0' * 700)
        return type('Res', (), {'returncode': 0, 'stderr': ''})()
    monkeypatch.setattr(documentador_06.shutil, 'which', lambda nome: '/fake/pandoc')
    monkeypatch.setattr(documentador_06.subprocess, 'run', fake_run)

    doc = documentador_06.DocumentadorFase6(Path('.'))
    path_md = tmp_path / 'documento.md'
    path_pdf = tmp_path / 'doc.pdf'
    path_md.write_text('# Título', encoding='utf-8')

    assert doc._converter_md_para_pdf(path_md, path_pdf, 'Título') is True
    assert path_pdf.exists()
    with open(path_pdf, 'rb') as f:
        assert f.read(5) == b'%PDF-'


def test_converter_md_para_pdf_sem_pandoc(documentador_06, tmp_path, monkeypatch):
    """Sem pandoc no PATH: PDF falha honestamente (não gera 'PDF' falso/oculto)."""
    monkeypatch.setattr(documentador_06.shutil, 'which', lambda nome: None)

    doc = documentador_06.DocumentadorFase6(Path('.'))
    path_md = tmp_path / 'documento.md'
    path_pdf = tmp_path / 'doc.pdf'
    path_md.write_text('# Título', encoding='utf-8')

    assert doc._converter_md_para_pdf(path_md, path_pdf, 'Título') is False
    assert not path_pdf.exists()


def test_converter_md_para_pdf_pandoc_falha(documentador_06, tmp_path, monkeypatch):
    def fake_run(cmd, capture_output=True, text=True):
        return type('Res', (), {'returncode': 1, 'stderr': 'no engine'})()
    monkeypatch.setattr(documentador_06.shutil, 'which', lambda nome: '/fake/pandoc')
    monkeypatch.setattr(documentador_06.subprocess, 'run', fake_run)

    doc = documentador_06.DocumentadorFase6(Path('.'))
    path_md = tmp_path / 'documento.md'
    path_pdf = tmp_path / 'doc.pdf'
    path_md.write_text('# Título', encoding='utf-8')

    assert doc._converter_md_para_pdf(path_md, path_pdf, 'Título') is False
    assert not path_pdf.exists()


def test_renderizar_formatos_sem_pandoc_documento_md_ainda_gerado(documentador_06, tmp_path, monkeypatch):
    """Sem pandoc: o markdown (fonte única) SEMPRE é gerado; html/pdf reprovam."""
    monkeypatch.setattr(documentador_06.shutil, 'which', lambda nome: None)

    doc = documentador_06.DocumentadorFase6(tmp_path / 'cache', output_base=tmp_path / 'output')
    narrativas = doc._gerar_narrativas('proj-x', 'Título', {})
    docs = doc._renderizar_formatos('proj-x', 'Título', narrativas)

    assert docs['md_valido'] is True
    assert docs['html_valido'] is False
    assert docs['pdf_gerado'] is False
    assert (tmp_path / 'output' / 'proj-x' / 'documentos' / 'documento.md').exists()
    assert not (tmp_path / 'output' / 'proj-x' / 'documentos' / 'index.html').exists()
    assert not (tmp_path / 'output' / 'proj-x' / 'documentos' / 'documento.pdf').exists()


def test_renderizar_formatos_com_pandoc_hermetico(documentador_06, tmp_path, monkeypatch):
    """Pipeline completo com pandoc mockado: escreve a fonte e deriva html/pdf."""
    def fake_run(cmd, capture_output=True, text=True):
        out = cmd[-1]
        if out.endswith('.html'):
            Path(out).write_text(
                '<!DOCTYPE html><html><body><h1>Título</h1></body></html>'
                + 'x' * 400, encoding='utf-8'
            )
        elif out.endswith('.pdf'):
            Path(out).write_bytes(b'%PDF-1.4\n' + b'0' * 700)
        return type('Res', (), {'returncode': 0, 'stderr': ''})()
    monkeypatch.setattr(documentador_06.shutil, 'which', lambda nome: '/fake/pandoc')
    monkeypatch.setattr(documentador_06.subprocess, 'run', fake_run)

    doc = documentador_06.DocumentadorFase6(tmp_path / 'cache', output_base=tmp_path / 'output')
    narrativas = doc._gerar_narrativas('proj-x', 'Título', {})
    docs = doc._renderizar_formatos('proj-x', 'Título', narrativas)

    assert docs['md_valido'] is True
    assert docs['html_valido'] is True
    assert docs['pdf_gerado'] is True
    assert (tmp_path / 'output' / 'proj-x' / 'documentos' / 'index.html').exists()
    assert (tmp_path / 'output' / 'proj-x' / 'documentos' / 'documento.md').exists()
    assert (tmp_path / 'output' / 'proj-x' / 'documentos' / 'documento.pdf').exists()


@pytest.mark.skipif(
    not shutil.which('pandoc'), reason='pandoc não instalado no PATH'
)
def test_pandoc_conversao_real_qualidade_saida(documentador_06, tmp_path):
    """INTEGRAÇÃO REAL: pandoc converte a fonte markdown em HTML e PDF válidos,
    e os gates F1-F3 reprovam/aprovam sobre os arquivos reais no disco."""
    doc = documentador_06.DocumentadorFase6(tmp_path / 'cache', output_base=tmp_path / 'output')
    narrativas = doc._gerar_narrativas('proj-x', 'Título Real', {})
    docs = doc._renderizar_formatos('proj-x', 'Título Real', narrativas)

    assert docs['md_valido'] is True
    assert docs['html_valido'] is True
    assert docs['pdf_gerado'] is True

    gates, ok = documentador_06.ValidadorGatesPhase6.executar_todos(docs)
    assert ok is True
    assert all(g.passou for g in gates)

    # Qualidade: HTML validado pelo F1 exige DOM completo; PDF validado pelo
    # F2 exige cabeçalho %PDF- real e (com pypdf) páginas > 0.
    html_file = tmp_path / 'output' / 'proj-x' / 'documentos' / 'index.html'
    pdf_file = tmp_path / 'output' / 'proj-x' / 'documentos' / 'documento.pdf'
    assert html_file.stat().st_size > 200
    assert pdf_file.stat().st_size > 500
    with open(pdf_file, 'rb') as f:
        assert f.read(5) == b'%PDF-'


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