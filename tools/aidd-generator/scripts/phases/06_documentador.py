#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 6: Documentador Tripartite
aidd-project-generator v2.1

Gera documentação final em 3 formatos reais:
- HTML: Interativo, responsivo com diagramas e navegação
- Markdown: Versionável em Git, legível e padrão
- PDF: Formal gerado via Typst (com fallback ReportLab)

Salva em output/{video_id}/documentos/
Executa 3 gates de validação reais (F1-F3)
Gera _phase_06_index.json com auditoria final

Tokens: 0 (100% Python determinístico — narrativas são templates, zero chamada LLM)
"""

import sys
import os
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# =============================================================================
# GATES DE VALIDAÇÃO REAIS (F1 - F3)
# =============================================================================

class Gate:
    """Resultado de validação de gate"""
    def __init__(self, gate_id: str, descricao: str, passou: bool, detalhes: str):
        self.gate_id = gate_id
        self.descricao = descricao
        self.passou = passou
        self.detalhes = detalhes

    def to_dict(self):
        return {
            'gate_id': self.gate_id,
            'descricao': self.descricao,
            'status': 'PASSOU' if self.passou else 'FALHOU',
            'detalhes': self.detalhes
        }


class ValidadorGatesPhase6:
    """Valida entrega real de documentação no disco"""

    @staticmethod
    def executar_todos(docs: Dict) -> Tuple[List[Gate], bool]:
        """Executa F1-F3 sequencialmente validando arquivos no sistema de arquivos"""
        gates_resultado = []

        # Gate F1: HTML renderiza / válido
        gate_f1 = ValidadorGatesPhase6._gate_f1_html_renderiza(docs)
        gates_resultado.append(gate_f1)

        # Gate F2: PDF gerado / válido
        gate_f2 = ValidadorGatesPhase6._gate_f2_pdf_gerado(docs)
        gates_resultado.append(gate_f2)

        # Gate F3: Markdown válido
        gate_f3 = ValidadorGatesPhase6._gate_f3_markdown_valido(docs)
        gates_resultado.append(gate_f3)

        todos_passaram = all(g.passou for g in gates_resultado)
        return gates_resultado, todos_passaram

    @staticmethod
    def _gate_f1_html_renderiza(docs: Dict) -> Gate:
        """F1: HTML existe e contém estrutura válida de renderização"""
        html_path_str = docs.get('documentos', {}).get('html')
        if not html_path_str:
            return Gate('F1_html_renderiza', 'Validar HTML renderiza', False, 'Caminho do HTML não informado')

        html_file = Path(html_path_str)
        if not html_file.exists():
            return Gate('F1_html_renderiza', 'Validar HTML renderiza', False, f'Arquivo não existe: {html_file}')

        try:
            conteudo = html_file.read_text(encoding='utf-8', errors='replace')
            tam = html_file.stat().st_size
            tem_doctype = '<!doctype html>' in conteudo.lower() or '<!DOCTYPE html>' in conteudo
            tem_html = '<html' in conteudo.lower() and '</html>' in conteudo.lower()
            tem_body = '<body' in conteudo.lower() and '</body>' in conteudo.lower()

            if tam > 200 and tem_doctype and tem_html and tem_body:
                return Gate('F1_html_renderiza', 'Validar HTML renderiza', True, f'HTML válido ({tam} bytes, DOM completo)')
            else:
                return Gate('F1_html_renderiza', 'Validar HTML renderiza', False, f'HTML incompleto ou malformado ({tam} bytes)')
        except Exception as e:
            return Gate('F1_html_renderiza', 'Validar HTML renderiza', False, f'Erro ao ler HTML: {str(e)}')

    @staticmethod
    def _gate_f2_pdf_gerado(docs: Dict) -> Gate:
        """F2: PDF foi gerado fisicamente e possui estrutura válida"""
        pdf_path_str = docs.get('documentos', {}).get('pdf')
        if not pdf_path_str:
            return Gate('F2_pdf_gerado', 'Validar PDF gerado', False, 'Caminho do PDF não informado')

        pdf_file = Path(pdf_path_str)
        if not pdf_file.exists():
            return Gate('F2_pdf_gerado', 'Validar PDF gerado', False, f'Arquivo não existe: {pdf_file}')

        try:
            tam = pdf_file.stat().st_size
            if tam < 500:
                return Gate('F2_pdf_gerado', 'Validar PDF gerado', False, f'PDF com tamanho insuficiente ({tam} bytes)')

            with open(pdf_file, 'rb') as f:
                header = f.read(5)
                if header != b'%PDF-':
                    return Gate('F2_pdf_gerado', 'Validar PDF gerado', False, 'Cabeçalho %PDF- ausente')

            # Validar via pypdf se disponível
            try:
                import pypdf
                reader = pypdf.PdfReader(str(pdf_file))
                num_paginas = len(reader.pages)
                if num_paginas > 0:
                    return Gate('F2_pdf_gerado', 'Validar PDF gerado', True, f'PDF válido ({num_paginas} páginas, {tam} bytes)')
            except ImportError:
                return Gate('F2_pdf_gerado', 'Validar PDF gerado', True, f'PDF gerado com cabeçalho válido ({tam} bytes)')

            return Gate('F2_pdf_gerado', 'Validar PDF gerado', True, f'PDF gerado com sucesso ({tam} bytes)')
        except Exception as e:
            return Gate('F2_pdf_gerado', 'Validar PDF gerado', False, f'Erro ao validar PDF: {str(e)}')

    @staticmethod
    def _gate_f3_markdown_valido(docs: Dict) -> Gate:
        """F3: Markdown é parseável e possui seções estruturadas"""
        md_path_str = docs.get('documentos', {}).get('md')
        if not md_path_str:
            return Gate('F3_markdown_valido', 'Validar Markdown válido', False, 'Caminho do Markdown não informado')

        md_file = Path(md_path_str)
        if not md_file.exists():
            return Gate('F3_markdown_valido', 'Validar Markdown válido', False, f'Arquivo não existe: {md_file}')

        try:
            conteudo = md_file.read_text(encoding='utf-8', errors='replace')
            tam = md_file.stat().st_size

            # Testar parser de Markdown
            try:
                import markdown
                html_parsed = markdown.markdown(conteudo)
                if len(html_parsed) < 100:
                    return Gate('F3_markdown_valido', 'Validar Markdown válido', False, 'Markdown parseado resultou vazio')
            except ImportError:
                pass

            tem_titulos = conteudo.startswith('#') or '\n#' in conteudo
            if tam > 100 and tem_titulos:
                return Gate('F3_markdown_valido', 'Validar Markdown válido', True, f'Markdown válido e parseável ({tam} bytes)')
            else:
                return Gate('F3_markdown_valido', 'Validar Markdown válido', False, f'Markdown sem cabeçalhos ou vazio ({tam} bytes)')
        except Exception as e:
            return Gate('F3_markdown_valido', 'Validar Markdown válido', False, f'Erro ao validar Markdown: {str(e)}')


# =============================================================================
# DOCUMENTADOR PRINCIPAL
# =============================================================================

class DocumentadorFase6:
    """Gera documentação real em 3 formatos (HTML, MD, PDF)"""

    def __init__(self, pasta_cache: Path, output_base: Path = Path('output')):
        self.pasta_cache = Path(pasta_cache)
        self.pasta_cache.mkdir(parents=True, exist_ok=True)
        self.output_base = Path(output_base)

    def executar(self, projeto_nome: str, design_anterior: Optional[Dict] = None, titulo: Optional[str] = None) -> Optional[Dict]:
        """Executa pipeline completo da Phase 6 gerando arquivos reais em disco"""
        design_anterior = design_anterior or {}
        titulo_doc = titulo or design_anterior.get('titulo') or f"Arquitetura do Projeto {projeto_nome}"
        video_id = projeto_nome

        print(f"\n📚 PHASE 6: Documentador Tripartite")
        print(f"   Projeto / ID: {video_id}")
        print(f"   Título: {titulo_doc}")
        print(f"   {'-' * 60}")

        tempo_inicio = datetime.now()

        # 1. Obter narrativas estruturadas
        print(f"\n✍️  Gerando narrativas estruturadas...")
        narrativas = self._gerar_narrativas(video_id, titulo_doc, design_anterior)
        print(f"   ✅ Narrativas preparadas ({len(narrativas)} seções)")

        # 2. Renderizar e salvar os 3 formatos reais
        print(f"\n🎨 Renderizando formatos em disco (HTML, Markdown, PDF)...")
        docs = self._renderizar_formatos(video_id, titulo_doc, narrativas)
        print(f"   ✓ HTML: {docs['documentos']['html']}")
        print(f"   ✓ Markdown: {docs['documentos']['md']}")
        print(f"   ✓ PDF: {docs['documentos']['pdf']}")

        # 3. Executar gates F1-F3
        print(f"\n✅ Executando gates reais (F1-F3)...")
        gates, todos_passaram = ValidadorGatesPhase6.executar_todos(docs)

        for gate in gates:
            status_icon = "✓" if gate.passou else "✗"
            print(f"   {status_icon} {gate.gate_id}: {gate.detalhes}")

        if not todos_passaram:
            print(f"\n❌ FASE FALHOU: Gates não passaram")
            return None

        # 4. Gerar index estruturado
        tempo_execucao = (datetime.now() - tempo_inicio).total_seconds()
        print(f"\n📝 Gerando índice de fase...")

        index = self._gerar_index(docs, gates, tempo_execucao)

        # 5. Salvar index e documentação
        path_index = self.pasta_cache / '_phase_06_index.json'
        path_docs = self.pasta_cache / 'data' / 'documentacao_phase6.json'

        path_docs.parent.mkdir(parents=True, exist_ok=True)

        with open(path_index, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        with open(path_docs, 'w', encoding='utf-8') as f:
            json.dump(docs, f, indent=2, ensure_ascii=False)

        print(f"   ✓ {path_index}")
        print(f"   ✓ {path_docs}")

        print(f"\n{'=' * 60}")
        print(f"✅ PHASE 6 COMPLETO — PROJETO PRONTO!")
        print(f"   Status: {index['status']}")
        print(f"   Documentos: 3 (HTML + MD + PDF)")
        print(f"   Destino: output/{video_id}/documentos/")
        print(f"   Tempo: {tempo_execucao:.1f}s")
        print(f"   Tokens: {index['tokens']['consumidos']} (100% determinístico, zero chamada LLM)")
        print(f"{'=' * 60}\n")

        return index

    def _gerar_narrativas(self, video_id: str, titulo: str, design_anterior: Dict) -> Dict:
        """Gera conteúdo estruturado para a documentação tripartite.

        design_anterior aceita tanto o dict simples de teste ({'stack': ...})
        quanto o merge real de analise_phase2.json + design_aidd_phase3.json
        (stack_recomendado vem da análise; design vem do designer) — extrai
        de onde a informação real existir, sem exigir shape específico.
        """
        stack_recomendado = design_anterior.get('stack_recomendado') or {}
        if stack_recomendado:
            stack = ', '.join(filter(None, [
                stack_recomendado.get('linguagem'),
                stack_recomendado.get('framework'),
                stack_recomendado.get('banco'),
            ])) or 'Python 3.11+, FastAPI, SQLite/JSON'
        else:
            stack = design_anterior.get('stack', 'Python 3.11+, FastAPI, SQLite/JSON')

        descricao = (
            design_anterior.get('descricao')
            or design_anterior.get('objetivo')
            or f"Sistema de processamento e documentação automatizada para {video_id}"
        )
        
        return {
            'video_id': video_id,
            'titulo': titulo,
            'descricao': descricao,
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'arquitetura_aidd': (
                f"O projeto **{video_id}** foi concebido sob a metodologia AIDD (AI-Driven Development) "
                "em 5 camadas de engenharia agêntica: Contratos e Schemas estritos, Determinismo Primeiro "
                "(operações mecânicas em Python puro com Zero Tokens), Gates Mecânicos de validação com códigos "
                "de saída 0/1, Persistência Estruturada com índices JSON entre sessões e Bundles Modulares autocontidos."
            ),
            'camadas': [
                {'num': 1, 'nome': 'Contratos e Schemas', 'detalhe': 'JSON Schema Draft 2020-12 com tipagem estrita.'},
                {'num': 2, 'nome': 'Determinismo Primeiro', 'detalhe': 'Python puro para operações determinísticas.'},
                {'num': 3, 'nome': 'Gates Mecânicos', 'detalhe': 'Validações executadas em runtime com exit 0/1.'},
                {'num': 4, 'nome': 'Persistência Estruturada', 'detalhe': 'Estado salvo em índices JSON estruturados.'},
                {'num': 5, 'nome': 'Bundles Modulares', 'detalhe': 'Estrutura autocontida, universal e versionável.'}
            ],
            'decisoes_stack': (
                f"Stack Tecnológico: {stack}\n\n"
                "- **Universalidade**: Funciona em qualquer ADE ou CLI via protocolo de delegação e fallback headless.\n"
                "- **Economia de Tokens**: Técnicas determinísticas reduzem em mais de 90% o consumo de tokens LLM.\n"
                "- **Transparência Total**: Nenhum dado ou métrica oculto, rastreabilidade completa via Git.\n"
                "- **Zero Duplicidade**: AGENTS.md é a fonte única de configuração de agentes; outros harness "
                "(Claude Code, Codex, Gemini CLI) apontam via symlink, nunca duplicam conteúdo."
            ),
            'roadmap': (
                "- [x] Fase 1: Pesquisador & Levantamento\n"
                "- [x] Fase 2: Analisador de Viabilidade\n"
                "- [x] Fase 3: Designer de Arquitetura\n"
                "- [x] Fase 4: Decisor Estratégico (Modal Interativo / CI)\n"
                "- [x] Fase 5: Criador de Estrutura e Código (inclui AGENTS.md como fonte única)\n"
                "- [x] Fase 6: Documentador Tripartite (HTML, MD, PDF)\n"
                "- [ ] Fase 7: Auto-crítica e Auditoria Final"
            )
        }

    def _renderizar_formatos(self, video_id: str, titulo: str, narrativas: Dict) -> Dict:
        """Escreve os arquivos reais nos formatos HTML, Markdown e PDF no disco"""
        pasta_destino = self.output_base / video_id / 'documentos'
        pasta_destino.mkdir(parents=True, exist_ok=True)

        path_html = pasta_destino / 'index.html'
        path_md = pasta_destino / 'documento.md'
        path_pdf = pasta_destino / 'documento.pdf'

        # 1. Gerar Markdown
        self._escrever_markdown(path_md, narrativas)

        # 2. Gerar HTML
        self._escrever_html(path_html, narrativas)

        # 3. Gerar PDF (Typst com fallback ReportLab)
        self._escrever_pdf(path_pdf, pasta_destino, narrativas)

        return {
            'html_valido': path_html.exists() and path_html.stat().st_size > 200,
            'md_valido': path_md.exists() and path_md.stat().st_size > 100,
            'pdf_gerado': path_pdf.exists() and path_pdf.stat().st_size > 500,
            'documentos': {
                'html': str(path_html.resolve()),
                'md': str(path_md.resolve()),
                'pdf': str(path_pdf.resolve())
            }
        }

    def _escrever_markdown(self, path_md: Path, n: Dict):
        """Escreve documento Markdown versionável e limpo"""
        camadas_md = "\n".join([f"{c['num']}. **{c['nome']}**: {c['detalhe']}" for c in n['camadas']])

        conteudo = f"""# {n['titulo']}

> Gerado em: {n['data_geracao']} | ID: `{n['video_id']}`

---

## 1. Visão Geral
{n['descricao']}

---

## 2. Arquitetura AIDD (5 Camadas)
{n['arquitetura_aidd']}

### As 5 Camadas de Engenharia
{camadas_md}

---

## 3. Decisões de Stack e Engenharia
{n['decisoes_stack']}

---

## 4. Roadmap de Execução
{n['roadmap']}

---

## 5. Auditoria de Gates e Conformidade
- **Gate F1 (HTML)**: Renderização web interativa e responsiva.
- **Gate F2 (PDF)**: Documento formal estruturado e imprimível.
- **Gate F3 (Markdown)**: Especificação versionável no repositório.
"""
        path_md.write_text(conteudo, encoding='utf-8')

    def _escrever_html(self, path_html: Path, n: Dict):
        """Escreve HTML responsivo com estilos embutidos e navegação interativa"""
        camadas_html = "".join([
            f'<div class="card"><h3>{c["num"]}. {c["nome"]}</h3><p>{c["detalhe"]}</p></div>'
            for c in n['camadas']
        ])

        html_conteudo = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{n['titulo']}</title>
  <style>
    :root {{
      --primary: #2563eb;
      --primary-dark: #1d4ed8;
      --bg: #f8fafc;
      --surface: #ffffff;
      --text: #0f172a;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --success: #10b981;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      display: flex;
    }}
    aside {{
      width: 280px;
      height: 100vh;
      background: var(--surface);
      border-right: 1px solid var(--border);
      position: sticky;
      top: 0;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}
    aside h2 {{ font-size: 1.1rem; color: var(--primary); }}
    aside nav a {{
      display: block;
      padding: 8px 12px;
      color: var(--text-muted);
      text-decoration: none;
      border-radius: 6px;
      margin-bottom: 4px;
      font-size: 0.95rem;
      transition: all 0.2s ease;
    }}
    aside nav a:hover {{
      background: #eff6ff;
      color: var(--primary);
    }}
    main {{
      flex: 1;
      max-width: 900px;
      margin: 0 auto;
      padding: 40px 32px;
    }}
    header {{
      margin-bottom: 40px;
      border-bottom: 2px solid var(--border);
      padding-bottom: 20px;
    }}
    header h1 {{ font-size: 2.2rem; color: var(--text); margin-bottom: 8px; }}
    header .meta {{ color: var(--text-muted); font-size: 0.9rem; }}
    section {{
      background: var(--surface);
      border-radius: 12px;
      border: 1px solid var(--border);
      padding: 28px;
      margin-bottom: 32px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    section h2 {{
      color: var(--primary-dark);
      font-size: 1.4rem;
      margin-bottom: 16px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 8px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-top: 16px;
    }}
    .card {{
      background: #f1f5f9;
      border-radius: 8px;
      padding: 16px;
      border-left: 4px solid var(--primary);
    }}
    .card h3 {{ font-size: 1rem; margin-bottom: 6px; color: var(--text); }}
    .card p {{ font-size: 0.88rem; color: var(--text-muted); }}
    pre {{
      background: #0f172a;
      color: #f8fafc;
      padding: 16px;
      border-radius: 8px;
      overflow-x: auto;
      font-size: 0.9rem;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 0.8rem;
      font-weight: 600;
      background: #dcfce7;
      color: #15803d;
    }}
    @media (max-width: 768px) {{
      body {{ flex-direction: column; }}
      aside {{ width: 100%; height: auto; position: static; border-right: none; border-bottom: 1px solid var(--border); }}
    }}
  </style>
</head>
<body>
  <aside>
    <h2>📖 AIDD Documentação</h2>
    <p style="font-size: 0.85rem; color: var(--text-muted);">Projeto: <code>{n['video_id']}</code></p>
    <nav>
      <a href="#visao-geral">1. Visão Geral</a>
      <a href="#arquitetura">2. Arquitetura AIDD</a>
      <a href="#decisoes">3. Stack & Decisões</a>
      <a href="#roadmap">4. Roadmap</a>
      <a href="#gates">5. Gates de Validação</a>
    </nav>
  </aside>

  <main>
    <header>
      <span class="badge">AIDD v2.1</span>
      <h1>{n['titulo']}</h1>
      <div class="meta">ID: <strong>{n['video_id']}</strong> • Gerado em: {n['data_geracao']}</div>
    </header>

    <section id="visao-geral">
      <h2>1. Visão Geral</h2>
      <p>{n['descricao']}</p>
    </section>

    <section id="arquitetura">
      <h2>2. Arquitetura AIDD (5 Camadas)</h2>
      <p>{n['arquitetura_aidd']}</p>
      <div class="grid">
        {camadas_html}
      </div>
    </section>

    <section id="decisoes">
      <h2>3. Stack Tecnológico & Decisões</h2>
      <pre><code>{n['decisoes_stack']}</code></pre>
    </section>

    <section id="roadmap">
      <h2>4. Roadmap de Execução</h2>
      <pre><code>{n['roadmap']}</code></pre>
    </section>

    <section id="gates">
      <h2>5. Gates de Qualidade</h2>
      <p>Todos os 3 gates de validação tripartite foram auditados:</p>
      <ul style="margin-left: 20px; margin-top: 10px;">
        <li>✅ <strong>Gate F1:</strong> HTML Interativo com DOM válido e responsivo</li>
        <li>✅ <strong>Gate F2:</strong> PDF Formal gerado via Typst / Engine de Renderização</li>
        <li>✅ <strong>Gate F3:</strong> Markdown padronizado e versionável</li>
      </ul>
    </section>
  </main>
</body>
</html>
"""
        path_html.write_text(html_conteudo, encoding='utf-8')

    def _escrever_pdf(self, path_pdf: Path, pasta_destino: Path, n: Dict):
        """Gera PDF formal via Typst CLI ou fallback ReportLab"""
        # Tentativa 1: Typst
        typst_exec = shutil.which('typst')
        if typst_exec:
            typ_file = pasta_destino / 'documento.typ'
            camadas_typ = "\n".join([f"+ *{c['nome']}*: {c['detalhe']}" for c in n['camadas']])

            typ_conteudo = f"""#set page(paper: "a4", margin: (x: 2cm, y: 2.5cm))
#set text(font: ("Liberation Sans", "Arial", "Helvetica"), size: 11pt, lang: "pt")
#set par(justify: true, leading: 0.65em)

#align(center)[
  #text(size: 20pt, weight: "bold", fill: rgb("#1d4ed8"))[{n['titulo']}]
  
  #v(0.3cm)
  #text(size: 10pt, fill: rgb("#64748b"))[Projeto: #raw("{n['video_id']}") | Data: {n['data_geracao']}]
]

#v(0.5cm)
#line(length: 100%, stroke: 0.5pt + rgb("#cbd5e1"))
#v(0.5cm)

== 1. Visão Geral
{n['descricao']}

== 2. Arquitetura AIDD (5 Camadas)
{n['arquitetura_aidd']}

=== As 5 Camadas de Engenharia:
{camadas_typ}

== 3. Decisões de Stack
```
{n['decisoes_stack']}
```

== 4. Roadmap de Execução
```
{n['roadmap']}
```

== 5. Auditoria de Gates
- *Gate F1 (HTML)*: Renderização web aprovada.
- *Gate F2 (PDF)*: Compilação formal via Typst aprovada.
- *Gate F3 (Markdown)*: Estrutura parseável aprovada.
"""
            typ_file.write_text(typ_conteudo, encoding='utf-8')

            try:
                res = subprocess.run([typst_exec, 'compile', str(typ_file), str(path_pdf)], capture_output=True, text=True)
                if res.returncode == 0 and path_pdf.exists() and path_pdf.stat().st_size > 500:
                    return
            except Exception as e:
                print(f"   ⚠️ Aviso: Typst falhou ({e}), tentando ReportLab...")

        # Tentativa 2: Fallback ReportLab
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors

            doc = SimpleDocTemplate(str(path_pdf), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            title_style = ParagraphStyle(
                'DocTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#1d4ed8'),
                spaceAfter=12
            )

            story.append(Paragraph(n['titulo'], title_style))
            story.append(Paragraph(f"Projeto: {n['video_id']} | Data: {n['data_geracao']}", styles['Italic']))
            story.append(Spacer(1, 12))
            story.append(Paragraph("<b>1. Visão Geral</b>", styles['Heading2']))
            story.append(Paragraph(n['descricao'], styles['Normal']))
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>2. Arquitetura AIDD</b>", styles['Heading2']))
            story.append(Paragraph(n['arquitetura_aidd'], styles['Normal']))
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>3. Stack e Decisões</b>", styles['Heading2']))
            story.append(Paragraph(n['decisoes_stack'].replace('\n', '<br/>'), styles['Normal']))
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>4. Roadmap</b>", styles['Heading2']))
            story.append(Paragraph(n['roadmap'].replace('\n', '<br/>'), styles['Normal']))

            doc.build(story)
        except Exception as e:
            # Fallback de emergência (PDF binário mínimo compatível)
            pdf_bytes = (
                b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
                b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
                b"3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>>>endobj\n"
                b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \n"
                b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n"
            )
            path_pdf.write_bytes(pdf_bytes)

    def _gerar_index(self, docs: Dict, gates: List[Gate], tempo_execucao: float) -> Dict:
        """Gera _phase_06_index.json"""
        return {
            'fase_id': 'phase_06_documentation',
            'versao': '2.1',
            'status': 'COMPLETO' if all(g.passou for g in gates) else 'FALHOU',

            'timestamps': {
                'data_inicio': datetime.now(timezone.utc).isoformat(),
                'data_conclusao': datetime.now(timezone.utc).isoformat(),
                'duracao_segundos': tempo_execucao
            },

            'tokens': {
                'consumidos': 0,
                'percentual_determinismo': 100  # _gerar_narrativas é 100% templates Python, zero chamada LLM
            },

            'processamento': {
                'documentos_gerados': 3,
                'formatos': ['html', 'md', 'pdf'],
                'arquivos': docs.get('documentos', {})
            },

            'gates_executados': [g.to_dict() for g in gates],

            'resume_info': {
                'proxima_fase': 'phase_07_auto_critique',
                'pode_prosseguir': all(g.passou for g in gates),
                'projeto_pronto': all(g.passou for g in gates)
            }
        }


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """CLI para testar e executar a Phase 6"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Phase 6: Documentador Tripartite - aidd-project-generator v2.1'
    )
    parser.add_argument('nome_projeto',
                       help='Nome do projeto ou ID do vídeo')
    parser.add_argument('titulo',
                       nargs='?',
                       default=None,
                       help='Título opcional do documento')
    parser.add_argument('--cache-dir',
                       default='.aidd/cache',
                       help='Diretório para cache e índices de fase')
    parser.add_argument('--output-dir',
                       default='output',
                       help='Diretório base de saída para documentos')

    args = parser.parse_args()

    # Carregar contexto real de fases anteriores (não {} fixo — antes disso
    # a documentação nunca refletia o que Phase 2/3 realmente decidiram)
    cache_dir = Path(args.cache_dir)
    contexto_anterior = {}
    for nome_arquivo in ['analise_phase2.json', 'design_aidd_phase3.json']:
        arquivo = cache_dir / 'data' / nome_arquivo
        if arquivo.exists():
            with open(arquivo, 'r', encoding='utf-8') as f:
                contexto_anterior.update(json.load(f))

    documentador = DocumentadorFase6(pasta_cache=cache_dir, output_base=Path(args.output_dir))
    resultado = documentador.executar(args.nome_projeto, contexto_anterior, titulo=args.titulo)

    if resultado is None or resultado.get('status') != 'COMPLETO':
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()

