# -*- coding: utf-8 -*-
"""
Gera o par <dd-mm-aaaa>_relatorio-evolucao-plano-acao.{json,html} em
docs/relatorios/, seguindo AGENTS.md secao 4.2 (Diretrizes de Design e
Governanca para Relatorios HTML): dados brutos em JSON, HTML interpolado
por script deterministico, nunca colado direto no chat.

DATA abaixo e a unica fonte de verdade: o .json e o .html sao sempre
gerados juntos a partir dela, nunca divergem.
"""
import json
import os

DATA_DATE = "11-09-2026"
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "relatorios")
BASENAME = f"{DATA_DATE}_relatorio-evolucao-plano-acao"

DATA = {
    "gerado_em": "2026-09-11",
    "summary": {
        "nota_original": 7.5,
        "composto_calculado": 9.13,
        "iniciativas_concluidas": 14,
        "iniciativas_total": 21,
        "tarefas_concluidas": 88,
        "tarefas_total": 163,
    },
    "dims": [
        {"name": "Testabilidade / Cobertura Real", "vals": [6.0, 9.0, 10.0], "state": "good"},
        {"name": "Modularização", "vals": [7.0, 9.0, 10.0], "state": "good"},
        {"name": "Gates Mecânicos", "vals": [7.0, 8.0, 9.0], "state": "good"},
        {"name": "Transparência / Zero Alucinação", "vals": [8.0, 8.5, 9.0], "state": "good"},
        {"name": "Universalidade / Agnosticismo", "vals": [8.0, 9.0, 9.0], "state": "flat"},
        {"name": "Engenharia Agêntica Aplicada", "vals": [8.0, 8.5, 8.5], "state": "flat"},
        {"name": "Determinismo Primeiro", "vals": [9.0, 9.5, 9.5], "state": "warning"},
        {"name": "Economia Severa de Tokens", "vals": [7.0, 8.0, 8.0], "state": "warning"},
        {"name": "Distribuição de Componentes (bônus, fora do composto)", "vals": [None, 9.0, 10.0], "state": "good"},
    ],
    "sistB": [
        {"tool": "forge", "old": 7.8, "now": 8.58},
        {"tool": "master", "old": 6.8, "now": 8.58},
        {"tool": "ops", "old": 4.8, "now": 8.33},
        {"tool": "enterprise", "old": 6.0, "now": 8.25},
        {"tool": "generator", "old": 6.8, "now": 8.00},
    ],
    "sistD": [
        {"tool": "generator", "val": 9.94},
        {"tool": "enterprise", "val": 9.9},
        {"tool": "forge", "val": 9.7},
        {"tool": "integrated", "val": 9.56},
        {"tool": "ops", "val": 8.8},
        {"tool": "master", "val": None},
    ],
    "matrix": [
        {"tool": "Orquestração raiz", "vals": [4, 3, 3, 3]},
        {"tool": "AIDD Forge", "vals": [4, 3, 3, 2]},
        {"tool": "AIDD Ops", "vals": [4, 3, 3, 3]},
        {"tool": "AIDD Generator", "vals": [3, 2, 2, 2]},
        {"tool": "AIDD Master", "vals": [3, 2, 2, 2]},
        {"tool": "AIDD Enterprise", "vals": [3, 2, 2, 2]},
    ],
    "tests": [
        {"tool": "generator", "passed": 929, "skipped": 0},
        {"tool": "forge", "passed": 196, "skipped": 1},
        {"tool": "master", "passed": 285, "skipped": 4},
        {"tool": "enterprise", "passed": 262, "skipped": 4},
        {"tool": "ops", "passed": 150, "skipped": 0},
        {"tool": "bridge", "passed": None, "skipped": None},
    ],
    "timeline": [
        ["04/09/2026", "Auditoria original (Sistema A)", "Nota consolidada 7,5/10 — 8 dimensões definidas."],
        ["05/09/2026", "Rodada 1 de evolução de notas (7 pacotes)", "Composto sobe para 8,7/10."],
        ["05–06/09/2026", "Rodada 2 de refinamento (5 itens + 1 residual)", "Testabilidade e Modularização chegam a 10/10; 2 tetos honestos reafirmados (Determinismo, Tokens)."],
        ["06/09/2026", "Testes completos do ecossistema (6 baterias reais)", "Todas aprovadas — 2 delas “com ressalvas”."],
        ["06/09/2026", "Validação Humana em sessões isoladas", "Integrado E2E 9,56/10 (Sistema D)."],
        ["06–07/09/2026", "Integração AIDD-Ops (9 pacotes)", "AIDD-Ops vira a 5ª ferramenta oficial do ecossistema."],
        ["06–09/09/2026", "Direcionamento Estratégico Anti-NIH", "Código reinventado trocado por OSS maduro (Cookiecutter, <span class=\"mono\">returns</span>, SQLAlchemy, Coolify)."],
        ["08/09/2026", "Reauditoria “Fase 3” (Sistema B, harness Antigravity)", "1.627 testes / 0 falhas (partindo de 1.427 / 13 falhas); heatmap por ferramenta."],
        ["08–09/09/2026", "Correção de Código Limpo + Correção de Arquitetura Limpa", "13 achados fechados."],
        ["09/09/2026", "5 auditorias-baseline formalizadas", "Viraram os planos de <span class=\"mono\">a-fazer/</span> — 45 itens de débito técnico, 0 iniciados."],
        ["09/09/2026", "Relatório Raio-X de Maturidade (Sistema C)", "Síntese cruzando planos + grafo de conhecimento."],
        ["09–11/09/2026", "Em andamento: Correção Pós-Auditoria Sem Maquiagem (18 itens) e Código Limpo Profundo (18 itens)", "22,2% e 5,6% concluídos, respectivamente."],
        ["11/09/2026 (hoje)", "Status consolidado de planos", "21 iniciativas, 14 concluídas (66,7%); 88/163 tarefas (54,0%)."],
    ],
    "plans": [
        {
            "num": "02", "name": "Otimização de Tokenomics & Latência", "items": 7,
            "solves": "Vazamento de contexto na Fase 8 do <b>aidd-generator</b>: o fix-loop reenvia código + teste + erro inteiro a cada tentativa.",
            "tools": ["generator"], "badge": {"cls": "muted", "label": "estimativa de eficiência"},
            "est": "Prompt por composição + diff no fix-loop — <b>estimativa de 10–12 mil tokens a menos por execução (15–25%)</b>.",
        },
        {
            "num": "03", "name": "Qualidade de Testes & Mutação", "items": 10,
            "solves": "Asserções fracas (<span class=\"mono\">assert X is not None</span>), sizing testado só pelo piso, <span class=\"mono\">time.sleep</span> em vez de relógio injetado, gate de mutação (<span class=\"mono\">mutmut</span>) inexistente.",
            "tools": ["master", "enterprise", "forge", "generator", "ops"], "badge": {"cls": "warn", "label": "cobertura real"},
            "est": "Foco em <b>aidd-enterprise</b> (verificação de hash de integridade) e <b>aidd-ops</b> (exatidão de sizing). Sem estimativa numérica de nota.",
        },
        {
            "num": "04", "name": "Resiliência, Concorrência & Integridade", "items": 8,
            "solves": "Outbox documentado como “at-least-once” mas <b>at-most-once na prática</b> — evento perdido se o listener falhar, sem retry/dead-letter. SQLite sem retry em <span class=\"mono\">SQLITE_BUSY</span>.",
            "tools": ["master", "enterprise"], "badge": {"cls": "crit", "label": "risco crítico"},
            "est": "Claim atômico + dead-letter no Outbox. Classificado como risco crítico nos próprios documentos.",
        },
        {
            "num": "05", "name": "Segurança Zero-Trust & Supply Chain", "items": 10,
            "solves": "Fase 8 do <b>aidd-generator</b> roda código de LLM <b>sem nenhum isolamento de processo</b> (RCE real). SQL injection na policy RLS. Selo de integridade do enterprise não resiste a adulteração deliberada.",
            "tools": ["generator", "enterprise"], "badge": {"cls": "crit", "label": "crítico — \"ainda esta semana\""},
            "est": "Sandbox nível 1 + gate OWASP sobre código gerado. A prioridade mais alta das 5, por classificação própria dos documentos.",
        },
        {
            "num": "06", "name": "Bootstrap de Ambiente & Preflight de Host", "items": 9,
            "solves": "Crashes crus em máquina virgem (<span class=\"mono\">ImportError</span>, ausência de Docker/Node/Git); 4 detectores de binário duplicados espalhados pelo código.",
            "tools": ["ecosystem"], "badge": {"cls": "muted", "label": "experiência de instalação"},
            "est": "Comando <span class=\"mono\">preflight-host</span> com diagnóstico em menos de 2 segundos.",
        },
    ],
    "in_progress": [
        {"name": "Correção Pós-Auditoria Sem Maquiagem", "items": 18, "done": 4},
        {"name": "Código Limpo Profundo do Ecossistema", "items": 18, "done": 1},
    ],
    "findings": [
        {"tool": "aidd-master + aidd-enterprise", "sev": "crit", "txt": "Outbox perde evento <b>silenciosamente</b> se o listener falhar (sem retry/dead-letter) — plano 04 (a-fazer), ainda não iniciado."},
        {"tool": "aidd-generator", "sev": "crit", "txt": "Fase 8 roda código de LLM <b>sem sandbox nem ambiente restrito</b> — RCE real, inclusive no smoke-test (<span class=\"mono\">--help</span>) — plano 05 (a-fazer), ainda não iniciado."},
        {"tool": "aidd-master + aidd-enterprise", "sev": "warn", "txt": "27 arquivos / 8.781 linhas byte-idênticas entre as duas ferramentas, com 3 divergências silenciosas já em curso — corrigir 1 bug hoje significa editar até 6 cópias físicas à mão."},
        {"tool": "aidd-forge + aidd-master + aidd-enterprise", "sev": "warn", "txt": "<span class=\"mono\">inject</span> de qualquer tipo grava sempre uma cópia no monorepo real, ignorando <span class=\"mono\">--dir</span>/<span class=\"mono\">--path</span> informado — recomendado documentar no <span class=\"mono\">--help</span>, ainda não corrigido."},
        {"tool": "aidd-master", "sev": "warn", "txt": "Boletim de nota da Sessão 3 da Validação Humana nunca foi preenchido, apesar de o índice marcar essa sessão como “Concluído & Aprovado” — inconsistência de documentação, não um dado ausente por acaso."},
        {"tool": "aidd-generator", "sev": "warn", "txt": "Fallback de <span class=\"mono\">referencias_utilizadas</span> na Fase 2 é estruturalmente inalcançável (lê a chave errada do JSON da Fase 1) — recomendado corrigir, ainda não corrigido."},
        {"tool": "aidd-master", "sev": "muted", "txt": "<span class=\"mono\">inject --remover</span> limpa o canônico mas deixa órfãos os espelhos multi-harness — gap real, não bloqueante."},
        {"tool": "aidd-bridge", "sev": "muted", "txt": "Não está integrada a nenhum dos 4 sistemas de nota — fica fora de toda comparação histórica até a próxima rodada de auditoria."},
    ],
    "action_plan": [
        {
            "order": 1, "priority": "crit",
            "title": "Plano 05 — Segurança Zero-Trust & Supply Chain",
            "status": "Rascunho aguardando aprovação",
            "why": "Os próprios documentos classificam este item como crítico, “ainda esta semana”: a Fase 8 do aidd-generator roda código de LLM sem nenhum isolamento de processo (RCE real).",
            "next": "Aprovar a Definição de Pronto e liberar o Prompt de Execução para o agente executor.",
        },
        {
            "order": 2, "priority": "crit",
            "title": "Plano 04 — Resiliência, Concorrência & Integridade",
            "status": "Rascunho aguardando aprovação",
            "why": "Risco crítico documentado: o Outbox perde evento silenciosamente se o listener falhar, sem retry nem dead-letter — afeta master e enterprise, os dois runtimes entregues ao cliente final.",
            "next": "Aprovar a Definição de Pronto e liberar o Prompt de Execução.",
        },
        {
            "order": 3, "priority": "good",
            "title": "Continuar as 2 iniciativas já em execução",
            "status": "Em andamento — 22,2% e 5,6%",
            "why": "Correção Pós-Auditoria Sem Maquiagem e Código Limpo Profundo já começaram e não estão bloqueadas por nenhum outro item desta fila.",
            "next": "Seguir executando os 31 itens restantes (14 + 17) no ritmo já estabelecido, em paralelo aos planos abaixo.",
        },
        {
            "order": 4, "priority": "muted",
            "title": "Plano 03 — Qualidade de Testes & Mutação",
            "status": "Rascunho aguardando aprovação",
            "why": "Fundamenta a confiança nos planos 04 e 05: sem teste de conteúdo (hash) e de exatidão (sizing), fica difícil provar que as correções de segurança e resiliência realmente pegaram.",
            "next": "Aprovar a Definição de Pronto — vale considerar priorizá-lo antes dos planos 04/05 se a cobertura de teste for tratada como pré-requisito, e não em paralelo.",
        },
        {
            "order": 5, "priority": "muted",
            "title": "Plano 02 — Otimização de Tokenomics & Latência",
            "status": "Rascunho aguardando aprovação",
            "why": "Ganho de eficiência estimado (15–25% menos tokens por execução do generator), sem caráter bloqueante para as demais frentes.",
            "next": "Aprovar a Definição de Pronto quando a fila de itens críticos estiver liberada.",
        },
        {
            "order": 6, "priority": "muted",
            "title": "Plano 06 — Bootstrap de Ambiente & Preflight de Host",
            "status": "Rascunho aguardando aprovação",
            "why": "Melhora a experiência de instalação em máquina virgem — não bloqueia nenhuma outra frente do ecossistema.",
            "next": "Aprovar a Definição de Pronto quando houver janela disponível.",
        },
        {
            "order": 7, "priority": "muted",
            "title": "Correções pontuais sem plano formal (quick wins)",
            "status": "Não iniciado",
            "why": "4 achados pequenos e independentes, já diagnosticados, que não precisam de um plano de 7–10 itens: o boletim da Sessão 3 do aidd-master, a falta de aviso no --help sobre o comportamento real do inject, a chave errada em referencias_utilizadas na Fase 2 do generator, e a integração do aidd-bridge à próxima rodada de auditoria.",
            "next": "Podem ser feitos em paralelo a qualquer um dos planos acima, sem precisar de Definição de Pronto formal.",
        },
    ],
}

TOOL_META_JS = """
  var TOOL_META = {
    master:{label:"aidd-master", colorVar:'--tool-master'},
    enterprise:{label:"aidd-enterprise", colorVar:'--tool-enterprise'},
    forge:{label:"aidd-forge", colorVar:'--tool-forge'},
    generator:{label:"aidd-generator", colorVar:'--tool-generator'},
    ops:{label:"aidd-ops", colorVar:'--tool-ops'},
    bridge:{label:"aidd-bridge", colorVar:'--tool-bridge'},
    ecosystem:{label:"ecossistema todo", colorVar:'--accent'},
    integrated:{label:"Integrado E2E", colorVar:'--accent'}
  };
"""

TEMPLATE = r"""<title>Raio-X do Ecossistema AIDD</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
  :root{
    color-scheme: light;
    --page:#f5f6f9; --surface:#ffffff; --surface-2:#eef0f4; --surface-3:#e6e9ee;
    --ink:#10141c; --ink-2:#4b5563; --ink-3:#858d9b;
    --hairline:#dfe3e9; --hairline-strong:#c7ccd6;
    --accent:#4a3aa7; --accent-ink:#ffffff; --accent-soft:#ece8fb; --accent-soft-ink:#3c2f8c;
    --good:#0ca30c; --good-soft:#e4f6e2; --good-ink:#0a6e0a;
    --warning:#b5790a; --warning-soft:#fdf1da; --warning-ink:#8a5b04;
    --serious:#c1522c; --serious-soft:#fbe7de;
    --critical:#d03b3b; --critical-soft:#fbe2e2; --critical-ink:#a11f1f;
    --tool-master:#2a78d6; --tool-enterprise:#eb6834; --tool-forge:#1baf7a;
    --tool-generator:#eda100; --tool-ops:#e87ba4; --tool-bridge:#8b93a1;
    --seq-100:#cde2fb; --seq-300:#6da7ec; --seq-500:#256abf; --seq-700:#0d366b;
    --shadow: 0 1px 2px rgba(16,20,28,0.04), 0 8px 24px -12px rgba(16,20,28,0.18);
  }
  * { scrollbar-width: thin; scrollbar-color: var(--accent) var(--page); }
  ::-webkit-scrollbar{ width:4px; height:4px; }
  ::-webkit-scrollbar-track{ background:var(--page); }
  ::-webkit-scrollbar-thumb{ background:var(--accent); border-radius:4px; }
  @media (prefers-color-scheme: dark){
    :root:not([data-theme="light"]){
      color-scheme: dark;
      --page:#0c0d10; --surface:#16171c; --surface-2:#1d1f25; --surface-3:#25272e;
      --ink:#f4f5f7; --ink-2:#c3c7d1; --ink-3:#8b91a0;
      --hairline:#2a2c33; --hairline-strong:#383b44;
      --accent:#9c93ef; --accent-ink:#161225; --accent-soft:#241f3d; --accent-soft-ink:#c9c2f7;
      --good:#3fc23f; --good-soft:#123318; --good-ink:#6adf6a;
      --warning:#e3ae3a; --warning-soft:#332a10; --warning-ink:#f0c563;
      --serious:#ef8f6b; --serious-soft:#3a2015;
      --critical:#e66767; --critical-soft:#3a1414; --critical-ink:#f29d9d;
      --tool-master:#3987e5; --tool-enterprise:#d95926; --tool-forge:#199e70;
      --tool-generator:#c98500; --tool-ops:#d55181; --tool-bridge:#9aa0ab;
      --seq-100:#12233a; --seq-300:#1c5cab; --seq-500:#5598e7; --seq-700:#b7d3f6;
      --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 8px 28px -12px rgba(0,0,0,0.55);
    }
  }
  :root[data-theme="dark"]{
    color-scheme: dark;
    --page:#0c0d10; --surface:#16171c; --surface-2:#1d1f25; --surface-3:#25272e;
    --ink:#f4f5f7; --ink-2:#c3c7d1; --ink-3:#8b91a0;
    --hairline:#2a2c33; --hairline-strong:#383b44;
    --accent:#9c93ef; --accent-ink:#161225; --accent-soft:#241f3d; --accent-soft-ink:#c9c2f7;
    --good:#3fc23f; --good-soft:#123318; --good-ink:#6adf6a;
    --warning:#e3ae3a; --warning-soft:#332a10; --warning-ink:#f0c563;
    --serious:#ef8f6b; --serious-soft:#3a2015;
    --critical:#e66767; --critical-soft:#3a1414; --critical-ink:#f29d9d;
    --tool-master:#3987e5; --tool-enterprise:#d95926; --tool-forge:#199e70;
    --tool-generator:#c98500; --tool-ops:#d55181; --tool-bridge:#9aa0ab;
    --seq-100:#12233a; --seq-300:#1c5cab; --seq-500:#5598e7; --seq-700:#b7d3f6;
    --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 8px 28px -12px rgba(0,0,0,0.55);
  }

  *{box-sizing:border-box;}
  body{
    background:var(--page); color:var(--ink);
    font-family:"IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
    line-height:1.5;
  }
  .wrap{ max-width:1180px; margin:0 auto; padding:0 20px 96px; }
  h1,h2,h3{ font-family:"Archivo", "IBM Plex Sans", sans-serif; text-wrap:balance; letter-spacing:-0.01em; margin:0; }
  .mono{ font-family:"IBM Plex Mono", ui-monospace, monospace; }
  .tabular{ font-variant-numeric: tabular-nums; }
  a{ color:var(--accent); }

  header.top{ padding:40px 0 24px; border-bottom:1px solid var(--hairline); display:flex; flex-direction:column; gap:14px; }
  .eyebrow{ font-family:"IBM Plex Mono",monospace; font-size:12px; letter-spacing:0.08em; text-transform:uppercase; color:var(--accent); display:flex; align-items:center; gap:8px; }
  .eyebrow::before{ content:""; width:8px; height:8px; border-radius:50%; background:var(--accent); display:inline-block; }
  h1.title{ font-size:clamp(28px,4vw,40px); font-weight:800; }
  .sub{ color:var(--ink-2); max-width:70ch; font-size:15px; }
  nav.jump{ display:flex; flex-wrap:wrap; gap:6px 4px; margin-top:6px; }
  nav.jump a{ font-size:12.5px; font-family:"IBM Plex Mono",monospace; color:var(--ink-2); text-decoration:none; padding:5px 10px; border:1px solid var(--hairline); border-radius:999px; background:var(--surface); }
  nav.jump a:hover{ border-color:var(--accent); color:var(--accent); }

  .callout{ margin-top:28px; background:var(--warning-soft); border:1px solid color-mix(in srgb, var(--warning) 40%, transparent); border-radius:10px; padding:16px 18px; display:flex; gap:12px; }
  .callout .glyph{ font-size:18px; line-height:1; flex-shrink:0; }
  .callout p{ margin:0; font-size:13.5px; color:var(--warning-ink); }
  .callout strong{ color:var(--ink); }

  .stats{ display:grid; grid-template-columns:repeat(4,1fr); gap:1px; background:var(--hairline); border:1px solid var(--hairline); border-radius:12px; overflow:hidden; margin-top:28px; }
  .stat{ background:var(--surface); padding:18px 20px; display:flex; flex-direction:column; gap:6px; }
  .stat .label{ font-size:11.5px; text-transform:uppercase; letter-spacing:0.06em; color:var(--ink-3); }
  .stat .value{ font-family:"Archivo",sans-serif; font-weight:800; font-size:30px; }
  .stat .note{ font-size:12px; color:var(--ink-3); }
  .stat .value.accent{ color:var(--accent); }
  .stat .value.good{ color:var(--good-ink); }
  @media (max-width:760px){ .stats{ grid-template-columns:repeat(2,1fr); } }

  section{ padding:56px 0; border-bottom:1px solid var(--hairline); }
  section:last-of-type{ border-bottom:none; }
  .sec-head{ display:flex; flex-direction:column; gap:8px; margin-bottom:28px; max-width:78ch; }
  .sec-num{ font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--ink-3); }
  h2.sec-title{ font-size:clamp(20px,2.6vw,26px); font-weight:800; }
  .sec-desc{ color:var(--ink-2); font-size:14.5px; }

  .card{ background:var(--surface); border:1px solid var(--hairline); border-radius:12px; box-shadow:var(--shadow); }
  .card-pad{ padding:22px 24px; }

  .legend{ display:flex; flex-wrap:wrap; gap:14px 18px; font-size:12.5px; color:var(--ink-2); margin-top:14px; }
  .legend .item{ display:flex; align-items:center; gap:6px; }
  .swatch{ width:11px; height:11px; border-radius:3px; display:inline-block; flex-shrink:0; }

  .chip{ display:inline-flex; align-items:center; gap:6px; font-size:12px; font-family:"IBM Plex Mono",monospace; padding:4px 9px; border-radius:999px; border:1px solid var(--hairline-strong); background:var(--surface-2); color:var(--ink-2); }
  .chip .dot{ width:8px; height:8px; border-radius:50%; }
  .badge{ display:inline-flex; align-items:center; gap:5px; font-size:11.5px; font-weight:600; padding:3px 9px; border-radius:6px; text-transform:uppercase; letter-spacing:0.03em; white-space:nowrap; }
  .badge.crit{ background:var(--critical-soft); color:var(--critical-ink); }
  .badge.warn{ background:var(--warning-soft); color:var(--warning-ink); }
  .badge.good{ background:var(--good-soft); color:var(--good-ink); }
  .badge.muted{ background:var(--surface-3); color:var(--ink-3); }

  .chart-shell{ position:relative; }
  svg.chart text{ font-family:"IBM Plex Mono",monospace; fill:var(--ink-2); }
  svg.chart .axis-line{ stroke:var(--hairline-strong); }
  svg.chart .grid-line{ stroke:var(--hairline); }
  .tip{ position:fixed; pointer-events:none; z-index:50; background:var(--ink); color:var(--page); font-family:"IBM Plex Mono",monospace; font-size:12px; padding:7px 10px; border-radius:7px; box-shadow:var(--shadow); max-width:240px; opacity:0; transform:translateY(4px); transition:opacity .1s ease; }
  .tip.show{ opacity:1; }
  .tip b{ color:var(--page); }

  .heat-wrap{ overflow-x:auto; }
  table.heat{ border-collapse:collapse; font-size:13px; width:100%; min-width:640px; }
  table.heat th{ font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--ink-3); padding:8px 10px; text-align:center; font-weight:600; }
  table.heat th.rowh{ text-align:left; }
  table.heat td{ text-align:center; padding:0; }
  table.heat td.rowh{ text-align:left; padding:10px 12px; font-weight:600; white-space:nowrap; border-right:1px solid var(--hairline-strong); }
  .heat-cell{ display:flex; align-items:center; justify-content:center; height:46px; font-family:"IBM Plex Mono",monospace; font-weight:600; font-size:14px; }

  .tool-bars{ display:flex; flex-direction:column; gap:14px; }
  .tool-row{ display:grid; grid-template-columns:150px 1fr 52px; align-items:center; gap:12px; }
  .tool-row .name{ font-size:13px; font-weight:600; display:flex; align-items:center; gap:8px; }
  .tool-row .track{ position:relative; height:22px; background:var(--surface-2); border-radius:5px; overflow:hidden; }
  .tool-row .fill{ position:absolute; inset:0 auto 0 0; border-radius:5px; }
  .tool-row .val{ font-family:"IBM Plex Mono",monospace; font-size:13px; text-align:right; }
  .tool-row.missing .track{ background:repeating-linear-gradient(135deg, var(--surface-3), var(--surface-3) 6px, var(--surface) 6px, var(--surface) 12px); }
  .tool-row.missing .val{ color:var(--ink-3); font-size:11px; }

  .timeline{ position:relative; padding-left:26px; }
  .timeline::before{ content:""; position:absolute; left:6px; top:4px; bottom:4px; width:2px; background:var(--hairline-strong); }
  .tl-item{ position:relative; padding-bottom:26px; }
  .tl-item:last-child{ padding-bottom:0; }
  .tl-item::before{ content:""; position:absolute; left:-26px; top:3px; width:11px; height:11px; border-radius:50%; background:var(--accent); border:2px solid var(--surface); box-shadow:0 0 0 1px var(--hairline-strong); }
  .tl-date{ font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--accent); font-weight:600; }
  .tl-title{ font-weight:700; font-size:14.5px; margin-top:2px; }
  .tl-desc{ font-size:13px; color:var(--ink-2); margin-top:3px; max-width:68ch; }

  .plans{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:16px; }
  .plan{ background:var(--surface); border:1px solid var(--hairline); border-radius:12px; padding:20px; display:flex; flex-direction:column; gap:12px; box-shadow:var(--shadow); }
  .plan-head{ display:flex; align-items:flex-start; justify-content:space-between; gap:10px; }
  .plan-num{ font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--ink-3); }
  .plan-name{ font-family:"Archivo",sans-serif; font-weight:700; font-size:15.5px; margin-top:2px; }
  .plan-solves{ font-size:13px; color:var(--ink-2); }
  .plan-solves b{ color:var(--ink); }
  .plan-foot{ margin-top:auto; display:flex; flex-direction:column; gap:8px; }
  .plan-tools{ display:flex; flex-wrap:wrap; gap:6px; }
  .plan-est{ font-size:12px; color:var(--ink-3); border-top:1px dashed var(--hairline-strong); padding-top:8px; }
  .plan-est b{ color:var(--ink-2); }
  .plan.inprogress{ border-style:dashed; }
  .progress-bar{ height:6px; background:var(--surface-2); border-radius:3px; overflow:hidden; }
  .progress-bar > span{ display:block; height:100%; background:var(--accent); }

  .roadmap{ list-style:none; margin:0; padding:0; display:flex; flex-direction:column; }
  .roadmap li{ display:grid; grid-template-columns:36px 1fr; gap:16px; padding:18px 0; border-bottom:1px solid var(--hairline); }
  .roadmap li:last-child{ border-bottom:none; }
  .roadmap .order{ font-family:"Archivo",sans-serif; font-weight:800; font-size:19px; color:var(--ink-3); text-align:center; padding-top:2px; }
  .roadmap .rm-head{ display:flex; flex-wrap:wrap; align-items:center; gap:10px; }
  .roadmap .rm-title{ font-weight:700; font-size:14.5px; }
  .roadmap .rm-status{ font-size:11.5px; color:var(--ink-3); font-family:"IBM Plex Mono",monospace; }
  .roadmap .rm-why{ font-size:13px; color:var(--ink-2); margin-top:7px; }
  .roadmap .rm-next{ font-size:13px; margin-top:9px; padding:9px 12px; background:var(--accent-soft); color:var(--accent-soft-ink); border-radius:7px; }
  .roadmap .rm-next b{ text-transform:uppercase; font-size:11px; letter-spacing:.04em; display:block; margin-bottom:2px; opacity:.85; }

  .findings{ display:flex; flex-direction:column; gap:10px; }
  .finding{ display:grid; grid-template-columns:100px 1fr; gap:16px; padding:14px 0; border-bottom:1px solid var(--hairline); }
  .finding:last-child{ border-bottom:none; }
  .finding .who{ font-size:12px; font-weight:600; }
  .finding .txt{ font-size:13.5px; color:var(--ink-2); }
  .finding .txt b{ color:var(--ink); }

  footer{ padding:36px 0 8px; font-size:12px; color:var(--ink-3); }
  footer p{ max-width:80ch; }

  @media (max-width:600px){
    .tool-row{ grid-template-columns:110px 1fr 46px; }
    .finding{ grid-template-columns:1fr; gap:4px; }
    .roadmap li{ grid-template-columns:1fr; }
    .roadmap .order{ text-align:left; }
  }
</style>

<div class="wrap">

  <header class="top">
    <span class="eyebrow">Ecossistema AIDD &middot; painel de auditoria</span>
    <h1 class="title">Raio-X do Ecossistema AIDD</h1>
    <p class="sub">Evolução das notas de auditoria desde o relatório original (04/09/2026) até hoje, por critério e por ferramenta, com o plano de ação para o que ainda falta — sem inflar nenhum número que não esteja documentado.</p>
    <nav class="jump">
      <a href="#metodologia">Metodologia</a>
      <a href="#criterios">8 critérios</a>
      <a href="#ferramentas">Por ferramenta</a>
      <a href="#linha-do-tempo">Linha do tempo</a>
      <a href="#pendentes">O que falta</a>
      <a href="#plano-de-acao">Plano de ação</a>
      <a href="#achados">Achados abertos</a>
    </nav>
  </header>

  <section id="metodologia" style="padding-top:28px;">
    <div class="callout">
      <span class="glyph">&#9888;&#65039;</span>
      <p><strong>Este ecossistema tem 4 sistemas de nota diferentes</strong>, feitos em datas diferentes, por processos e critérios diferentes — nenhum documento os unifica, e este painel não força uma fusão artificial. Cada seção abaixo identifica de qual sistema o número vem. Onde um número é <strong>calculado por este painel</strong> (não copiado de um documento-fonte), isso está marcado explicitamente.</p>
    </div>

    <div class="stats">
      <div class="stat">
        <span class="label">Nota original (Sistema A)</span>
        <span class="value tabular" id="statOriginal"></span>
        <span class="note">04/09/2026 &middot; relatório de auditoria original</span>
      </div>
      <div class="stat">
        <span class="label">Composto atual (calculado)</span>
        <span class="value accent tabular" id="statComposto"></span>
        <span class="note">média das 8 dimensões pós-Rodada 2 &mdash; nenhum documento cita este número pronto</span>
      </div>
      <div class="stat">
        <span class="label">Iniciativas concluídas</span>
        <span class="value good tabular" id="statIniciativas"></span>
        <span class="note">status de 11/09/2026</span>
      </div>
      <div class="stat">
        <span class="label">Tarefas concluídas</span>
        <span class="value tabular" id="statTarefas"></span>
        <span class="note">soma de todos os planos ativos</span>
      </div>
    </div>
  </section>

  <section id="criterios">
    <div class="sec-head">
      <span class="sec-num">01 &middot; Sistema A</span>
      <h2 class="sec-title">Evolução por critério — as 8 dimensões da auditoria original</h2>
      <p class="sec-desc">Nota do ecossistema como um todo (não por ferramenta) em cada checkpoint. Duas dimensões atingiram o teto declarado de propósito — não é estagnação, é um limite honesto documentado nas 4 perguntas de rigor da Rodada 2 (é necessário? é possível? é real? traz ganho real?).</p>
    </div>
    <div class="card card-pad">
      <div class="chart-shell">
        <svg id="slopeChart" class="chart" width="100%" viewBox="0 0 920 460" style="width:100%;height:auto;overflow:visible;"></svg>
      </div>
      <div class="legend">
        <div class="item"><span class="swatch" style="background:var(--good);"></span> alvo atingido nesta rodada</div>
        <div class="item"><span class="swatch" style="background:var(--warning);"></span> teto reafirmado (reprovado nas 4 perguntas de rigor)</div>
        <div class="item"><span class="swatch" style="background:var(--ink-3);"></span> sem mudança / fora do composto original</div>
      </div>
    </div>
  </section>

  <section id="ferramentas">
    <div class="sec-head">
      <span class="sec-num">02 &middot; Sistemas B, C e D</span>
      <h2 class="sec-title">Nota por ferramenta — três lentes que não se somam</h2>
      <p class="sec-desc">A auditoria de 8 dimensões (Sistema A) nunca quebra por ferramenta. Onde existe nota por ferramenta, vem de três processos distintos — apresentados lado a lado, não fundidos.</p>
    </div>

    <div class="card card-pad" style="margin-bottom:18px;">
      <h3 style="font-size:15px;margin-bottom:4px;">Sistema B &mdash; Reauditoria &ldquo;Fase 3&rdquo;, harness externo (Antigravity), 08/09/2026</h3>
      <p class="sec-desc" style="margin-bottom:16px;">6 dimensões próprias (Agêntica, Tokens, Uso/DX, Universalidade, Entrega, Determinismo), 0&ndash;10, média antiga vs. nova.</p>
      <div class="chart-shell">
        <svg id="sistemaBChart" class="chart" width="100%" viewBox="0 0 920 300" style="width:100%;height:auto;overflow:visible;"></svg>
      </div>
      <div class="legend">
        <div class="item"><span class="swatch" style="background:var(--surface-3);border:1px solid var(--hairline-strong);"></span> média antiga</div>
        <div class="item"><span class="swatch" style="background:var(--accent);"></span> média nova (08/09)</div>
      </div>
    </div>

    <div class="card card-pad" style="margin-bottom:18px;">
      <h3 style="font-size:15px;margin-bottom:4px;">Sistema D &mdash; Validação Humana em sessões isoladas, aprovação humana explícita, 06/09/2026</h3>
      <p class="sec-desc" style="margin-bottom:16px;">5 critérios por ferramenta (Usabilidade Leiga, Rigor de Engenharia, Fidelidade, UX/Frontend, Segurança), 0&ndash;10, nota final da sessão.</p>
      <div class="tool-bars" id="sistemaDBars"></div>
    </div>

    <div class="card card-pad" style="margin-bottom:18px;">
      <h3 style="font-size:15px;margin-bottom:4px;">Sistema C &mdash; Matriz arquitetural do Raio-X de Maturidade, 09/09/2026</h3>
      <p class="sec-desc" style="margin-bottom:16px;">Escala 1&ndash;5. &ldquo;Engine&rdquo; = motor interno da própria ferramenta; &ldquo;Deliverable&rdquo; = o que a ferramenta entrega ao app final do cliente.</p>
      <div class="heat-wrap">
        <table class="heat">
          <thead><tr><th class="rowh">Ferramenta</th><th>Engine<br>Clean Arch.</th><th>Engine<br>DDD</th><th>Deliverable<br>Clean Arch.</th><th>Deliverable<br>DDD</th></tr></thead>
          <tbody id="heatBody"></tbody>
        </table>
      </div>
      <p class="sec-desc" style="margin-top:14px;">Achado central: Master e Enterprise — as duas que entregam código de negócio ao usuário final — empatam em 2/5 no &ldquo;Deliverable DDD&rdquo;: a fatia vertical padrão ainda é <span class="mono">CREATE TABLE</span> + <span class="mono">dict(row)</span>, sem Entity/Value&nbsp;Object/Repository.</p>
    </div>

    <div class="card card-pad">
      <h3 style="font-size:15px;margin-bottom:4px;">Cobertura de testes automatizados por ferramenta (proxy objetivo, 10/09/2026)</h3>
      <div class="chart-shell" style="margin-top:10px;">
        <svg id="testCountChart" class="chart" width="100%" viewBox="0 0 920 260" style="width:100%;height:auto;overflow:visible;"></svg>
      </div>
    </div>
  </section>

  <section id="linha-do-tempo">
    <div class="sec-head">
      <span class="sec-num">03</span>
      <h2 class="sec-title">Linha do tempo consolidada</h2>
      <p class="sec-desc">Marco por marco, de 04/09 a hoje (11/09/2026), com o que cada um deixou como resultado.</p>
    </div>
    <div class="card card-pad">
      <div class="timeline" id="timeline"></div>
    </div>
  </section>

  <section id="pendentes">
    <div class="sec-head">
      <span class="sec-num">04</span>
      <h2 class="sec-title">O que falta — detalhe por plano, sem nota-alvo numérica</h2>
      <p class="sec-desc"><strong style="color:var(--ink);">Nenhum dos 5 planos em <span class="mono">docs/planos/a-fazer/</span> tem nota-alvo numérica documentada</strong> — todos os 44 itens seguem &ldquo;rascunho gerado, aguardando aprovação&rdquo;, zero iniciado. Cada card abaixo é sobre o que o plano resolve, não sobre quanto ele somaria a uma nota.</p>
    </div>
    <div class="plans" id="plansGrid"></div>
    <div class="plans" style="margin-top:16px;" id="inProgressGrid"></div>
  </section>

  <section id="plano-de-acao">
    <div class="sec-head">
      <span class="sec-num">05</span>
      <h2 class="sec-title">Plano de ação — fila de execução recomendada</h2>
      <p class="sec-desc">Ordem baseada na severidade que os próprios documentos declaram, não em preferência. Para os 5 planos de <span class="mono">a-fazer/</span>, a próxima ação concreta é sempre a mesma no processo já estabelecido do ecossistema: <strong style="color:var(--ink);">aprovar a Definição de Pronto antes de qualquer implementação</strong> — nenhum item começa sem isso.</p>
    </div>
    <div class="card card-pad">
      <ol class="roadmap" id="roadmapList"></ol>
    </div>
  </section>

  <section id="achados" style="border-bottom:none;">
    <div class="sec-head">
      <span class="sec-num">06</span>
      <h2 class="sec-title">Achados abertos, por ferramenta</h2>
      <p class="sec-desc">Consolidado de todas as fontes lidas. Severidade é a que os próprios documentos atribuem — nada foi promovido a &ldquo;crítico&rdquo; por este painel.</p>
    </div>
    <div class="card card-pad">
      <div class="findings" id="findingsList"></div>
    </div>
  </section>

  <footer>
    <p><strong style="color:var(--ink-2);">Fontes:</strong> <span class="mono">docs/relatorios/relatorio-auditoria-ecossistema-aidd.html</span>, <span class="mono">relatorio-evolucao-notas-ecossistema-aidd.html</span>, <span class="mono">relatorio-reauditoria-fase3-antes-depois.html</span>, <span class="mono">relatorio-raiox-maturidade-ecossistema-aidd.html</span>, <span class="mono">docs/planos/refinamento-notas-auditoria/</span>, <span class="mono">docs/planos/validacao-humana-testes-reais/</span>, <span class="mono">docs/testes/relatorios/</span>, <span class="mono">docs/testes/status_testes_ferramentas.json</span>, <span class="mono">11-09-2026_auditoria-status-planos.html</span>. Não lidos na íntegra nesta varredura (existem, ficam para aprofundamento futuro): <span class="mono">relatorio-auditoria-base-antes-f3.html</span>, <span class="mono">relatorio-auditoria-ecossistema-aidd-sem-maquiagem.html</span>, <span class="mono">relatorio-auditoria-codigo-limpo-ecossistema-aidd.html</span>, <span class="mono">relatorio-correcao-agnosticismo-e-duplicidade-2026-09-10.md</span>.</p>
    <p style="margin-top:8px;">aidd-bridge (concluída em 09/09/2026) não está integrada a nenhum dos 4 sistemas de nota acima — é a ferramenta mais nova do ecossistema e fica fora de toda comparação histórica até uma próxima rodada de auditoria a incluir.</p>
    <p style="margin-top:8px;">Gerado deterministicamente por <span class="mono">scripts/gerador_relatorio_evolucao_planos.py</span> a partir de <span class="mono">__BASENAME__.json</span> (par de dados brutos, mesma pasta) — conforme AGENTS.md §4.2.</p>
  </footer>
</div>

<div class="tip" id="tip"></div>

<script id="report-data" type="application/json">__REPORT_DATA_JSON__</script>
<script>
(function(){
  "use strict";
  var DATA = JSON.parse(document.getElementById('report-data').textContent);
  var tip = document.getElementById('tip');
  function showTip(evt, html){ tip.innerHTML = html; tip.classList.add('show'); moveTip(evt); }
  function moveTip(evt){
    var x = evt.clientX + 14, y = evt.clientY + 14;
    var r = tip.getBoundingClientRect();
    if (x + r.width > window.innerWidth - 8) x = evt.clientX - r.width - 14;
    if (y + r.height > window.innerHeight - 8) y = evt.clientY - r.height - 14;
    tip.style.left = x + 'px'; tip.style.top = y + 'px';
  }
  function hideTip(){ tip.classList.remove('show'); }

  var cs = getComputedStyle(document.documentElement);
  function tok(name){ return cs.getPropertyValue(name).trim(); }

  __TOOL_META_JS__

  var NS = "http://www.w3.org/2000/svg";
  function el(tag, attrs){
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }
  function textEl(attrs, content){ var t = el('text', attrs); t.textContent = content; return t; }

  /* ============ 0. Stat strip ============ */
  (function(){
    var s = DATA.summary;
    function setVal(id, main, sub){
      document.getElementById(id).innerHTML = main + '<span style="font-size:16px;color:var(--ink-3);">' + sub + '</span>';
    }
    setVal('statOriginal', s.nota_original.toFixed(1).replace('.', ','), '/10');
    setVal('statComposto', s.composto_calculado.toFixed(2).replace('.', ','), '/10');
    setVal('statIniciativas', s.iniciativas_concluidas, '/' + s.iniciativas_total);
    setVal('statTarefas', s.tarefas_concluidas, '/' + s.tarefas_total);
  })();

  /* ============ 1. SLOPE CHART — 8 dimensões (+1 bônus) ao longo de 3 checkpoints ============ */
  (function(){
    var dims = DATA.dims;
    var svg = document.getElementById('slopeChart');
    var W=920,H=460, padL=18, padR=210, padT=18, padB=40;
    var plotW = W-padL-padR, plotT=padT, plotB=H-padB;
    var xs = [padL, padL+plotW*0.46, padL+plotW];
    var labels = ["Original\n04/09", "Rodada 1\n05/09", "Rodada 2\n05-06/09"];
    function y(v){ return plotB - (v/10)*(plotB-plotT); }

    for (var g=0; g<=10; g+=2){
      svg.appendChild(el('line',{x1:padL,x2:W-padR,y1:y(g),y2:y(g),class:'grid-line'}));
      svg.appendChild(textEl({x:padL-8,y:y(g)+4,'text-anchor':'end','font-size':11}, g.toFixed(0)));
    }
    xs.forEach(function(x,i){
      labels[i].split("\n").forEach(function(ln,li){
        svg.appendChild(textEl({x:x,y:plotB+22+li*13,'text-anchor':'middle','font-size':11.5, 'font-weight': li===0?600:400}, ln));
      });
      svg.appendChild(el('line',{x1:x,x2:x,y1:plotT-4,y2:plotB,class:'axis-line'}));
    });

    var colorFor = {good: tok('--good'), warning: tok('--warning'), flat: tok('--ink-3')};
    var ends = [];
    dims.forEach(function(d){
      var pts = [];
      d.vals.forEach(function(v, i){ if (v!==null) pts.push([xs[i], y(v), v]); });
      var path = pts.map(function(p,i){ return (i===0?'M':'L') + p[0].toFixed(1) + ',' + p[1].toFixed(1); }).join(' ');
      var color = colorFor[d.state];
      svg.appendChild(el('path',{d:path, fill:'none', stroke:color, 'stroke-width':2.4, 'stroke-linecap':'round'}));
      pts.forEach(function(p){
        var c = el('circle',{cx:p[0],cy:p[1],r:4.5, fill: tok('--surface'), stroke:color, 'stroke-width':2.4});
        c.style.cursor='pointer';
        c.addEventListener('mouseenter', function(e){ showTip(e, '<b>'+d.name+'</b><br>nota: '+p[2].toFixed(1)+'/10'); });
        c.addEventListener('mousemove', moveTip);
        c.addEventListener('mouseleave', hideTip);
        svg.appendChild(c);
      });
      ends.push({name:d.name, y:pts[pts.length-1][1], val:pts[pts.length-1][2], color:color});
    });

    ends.sort(function(a,b){ return a.y-b.y; });
    var minGap = 15.5;
    for (var i=1;i<ends.length;i++){
      if (ends[i].y - ends[i-1].y < minGap) ends[i].y = ends[i-1].y + minGap;
    }
    ends.forEach(function(e2){
      var lx = xs[2]+10;
      svg.appendChild(el('line',{x1:xs[2]+4,x2:lx-2,y1:e2.y,y2:e2.y, stroke:e2.color, 'stroke-width':1, 'stroke-dasharray':'2,2'}));
      var t = textEl({x:lx, y:e2.y+3.5, 'font-size':11.5, fill: tok('--ink-2')}, e2.name.length>34 ? e2.name.slice(0,34)+'…' : e2.name);
      var title = el('title',{}); title.textContent = e2.name + ' — ' + e2.val.toFixed(1) + '/10';
      t.appendChild(title);
      svg.appendChild(t);
      svg.appendChild(textEl({x:W-4, y:e2.y+3.5, 'font-size':12,'text-anchor':'end','font-weight':600, fill:e2.color}, e2.val.toFixed(1)));
    });
  })();

  /* ============ 2. SISTEMA B — grouped bar antigo vs novo por ferramenta ============ */
  (function(){
    var sistB = DATA.sistB;
    var svg = document.getElementById('sistemaBChart');
    var W=920,H=300, padL=130, padR=70, padT=10, padB=30;
    var plotB = H-padB, plotT=padT;
    var rowH = (plotB-plotT)/sistB.length;
    function x(v){ return padL + (v/10)*(W-padL-padR); }
    for (var g=0; g<=10; g+=2){
      svg.appendChild(el('line',{x1:x(g),x2:x(g),y1:plotT,y2:plotB,class:'grid-line'}));
      svg.appendChild(textEl({x:x(g),y:plotB+18,'text-anchor':'middle','font-size':11}, g));
    }
    svg.appendChild(el('line',{x1:padL,x2:padL,y1:plotT,y2:plotB,class:'axis-line'}));
    sistB.forEach(function(d,i){
      var meta = TOOL_META[d.tool], color = tok(meta.colorVar);
      var rowY = plotT + i*rowH;
      var barH = rowH*0.30, gap=4;
      svg.appendChild(textEl({x:padL-12,y:rowY+rowH/2+4,'text-anchor':'end','font-size':12.5,'font-weight':600}, meta.label));
      var oy = rowY + rowH/2 - barH - gap/2;
      var ob = el('rect',{x:padL,y:oy,width:x(d.old)-padL,height:barH,rx:3,fill:tok('--surface-3'), stroke:tok('--hairline-strong')});
      ob.addEventListener('mouseenter', function(e){ showTip(e, '<b>'+meta.label+'</b><br>média antiga: '+d.old.toFixed(2)); });
      ob.addEventListener('mousemove', moveTip); ob.addEventListener('mouseleave', hideTip);
      svg.appendChild(ob);
      var ny = rowY + rowH/2 + gap/2;
      var nb = el('rect',{x:padL,y:ny,width:x(d.now)-padL,height:barH,rx:3,fill:color});
      nb.addEventListener('mouseenter', function(e){ showTip(e, '<b>'+meta.label+'</b><br>média nova: '+d.now.toFixed(2)+'<br>delta: +'+(d.now-d.old).toFixed(2)); });
      nb.addEventListener('mousemove', moveTip); nb.addEventListener('mouseleave', hideTip);
      svg.appendChild(nb);
      svg.appendChild(textEl({x:x(d.now)+8,y:ny+barH/2+4,'font-size':12,'font-weight':700,fill:color}, d.now.toFixed(2)+'  (+'+(d.now-d.old).toFixed(2)+')'));
    });
  })();

  /* ============ 3. SISTEMA D — barras de nota final por ferramenta ============ */
  (function(){
    var wrap = document.getElementById('sistemaDBars');
    DATA.sistD.forEach(function(d){
      var meta = TOOL_META[d.tool], color = tok(meta.colorVar);
      var row = document.createElement('div');
      row.className = 'tool-row' + (d.val===null ? ' missing' : '');
      var name = document.createElement('div'); name.className='name';
      var dot = document.createElement('span');
      dot.style.width='9px'; dot.style.height='9px'; dot.style.borderRadius='50%'; dot.style.background=color; dot.style.flexShrink='0';
      name.appendChild(dot); name.appendChild(document.createTextNode(meta.label));
      var track = document.createElement('div'); track.className='track';
      var val = document.createElement('div'); val.className='val';
      if (d.val!==null){
        var fill = document.createElement('div'); fill.className='fill';
        fill.style.width = (d.val/10*100)+'%'; fill.style.background=color;
        track.appendChild(fill);
        track.title = meta.label + ': ' + d.val.toFixed(2) + '/10';
        val.textContent = d.val.toFixed(2);
      } else {
        val.textContent = 'sem nota';
        track.title = 'Sessão registrada como "Concluído & Aprovado" no índice, mas o boletim individual nunca foi preenchido — inconsistência de documentação, não um dado.';
      }
      row.appendChild(name); row.appendChild(track); row.appendChild(val);
      wrap.appendChild(row);
    });
    var note = document.createElement('p');
    note.className = 'sec-desc'; note.style.marginTop='6px'; note.style.fontSize='12px';
    note.innerHTML = '<b style="color:var(--ink-2);">aidd-master</b>: sessão marcada "Concluído &amp; Aprovado" no índice, mas <span class="mono">03-teste-isolado-aidd-master.md</span> segue com o placeholder "(A ser preenchido ao final da sessão)" — sinalizado em Achados abertos, não preenchido aqui por invenção.';
    wrap.appendChild(note);
  })();

  /* ============ 4. SISTEMA C — matriz de arquitetura (heat table) ============ */
  (function(){
    function stepColor(v){
      var steps = [tok('--seq-100'), tok('--surface-3'), tok('--seq-300'), tok('--seq-500'), tok('--seq-700')];
      return steps[v-1] || tok('--surface-2');
    }
    function inkFor(v){ return v>=4 ? '#ffffff' : (v===1? tok('--ink-2') : tok('--ink')); }
    var tbody = document.getElementById('heatBody');
    DATA.matrix.forEach(function(row){
      var tr = document.createElement('tr');
      var th = document.createElement('td'); th.className='rowh'; th.textContent = row.tool;
      tr.appendChild(th);
      row.vals.forEach(function(v){
        var td = document.createElement('td');
        var cell = document.createElement('div'); cell.className='heat-cell';
        cell.style.background = stepColor(v); cell.style.color = inkFor(v);
        cell.textContent = v + '/5';
        td.appendChild(cell); tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
  })();

  /* ============ 5. Cobertura de testes ============ */
  (function(){
    var tests = DATA.tests;
    var svg = document.getElementById('testCountChart');
    var W=920,H=260, padL=140,padR=70,padT=10,padB=26;
    var plotB=H-padB, plotT=padT, max=929*1.08;
    var rowH=(plotB-plotT)/tests.length;
    function x(v){ return padL + (v/max)*(W-padL-padR); }
    [0,200,400,600,800].forEach(function(g){
      svg.appendChild(el('line',{x1:x(g),x2:x(g),y1:plotT,y2:plotB,class:'grid-line'}));
      svg.appendChild(textEl({x:x(g),y:plotB+16,'text-anchor':'middle','font-size':11}, g));
    });
    svg.appendChild(el('line',{x1:padL,x2:padL,y1:plotT,y2:plotB,class:'axis-line'}));
    tests.forEach(function(d,i){
      var meta = TOOL_META[d.tool], color = tok(meta.colorVar);
      var rowY=plotT+i*rowH, barH=rowH*0.5;
      var by = rowY + (rowH-barH)/2;
      svg.appendChild(textEl({x:padL-12,y:rowY+rowH/2+4,'text-anchor':'end','font-size':12.5,'font-weight':600}, meta.label));
      if (d.passed===null){
        svg.appendChild(el('rect',{x:padL,y:by,width:60,height:barH,rx:3,fill:'none',stroke:tok('--hairline-strong'),'stroke-dasharray':'4,3'}));
        svg.appendChild(textEl({x:padL+70,y:by+barH/2+4,'font-size':11.5,fill:tok('--ink-3')}, 'sem dado — não integrada a este levantamento'));
        return;
      }
      var bar = el('rect',{x:padL,y:by,width:Math.max(2,x(d.passed)-padL),height:barH,rx:3,fill:color});
      bar.addEventListener('mouseenter', function(e){ showTip(e, '<b>'+meta.label+'</b><br>'+d.passed+' passed'+(d.skipped?(' / '+d.skipped+' skipped'):'')); });
      bar.addEventListener('mousemove', moveTip); bar.addEventListener('mouseleave', hideTip);
      svg.appendChild(bar);
      svg.appendChild(textEl({x:x(d.passed)+8,y:by+barH/2+4,'font-size':12,'font-weight':700,fill:color}, d.passed + ' passed' + (d.skipped? ' · '+d.skipped+' skip' : '')));
    });
  })();

  /* ============ 6. Timeline ============ */
  (function(){
    var wrap = document.getElementById('timeline');
    DATA.timeline.forEach(function(item){
      var d = document.createElement('div'); d.className='tl-item';
      d.innerHTML = '<div class="tl-date">'+item[0]+'</div><div class="tl-title">'+item[1]+'</div><div class="tl-desc">'+item[2]+'</div>';
      wrap.appendChild(d);
    });
  })();

  /* ============ 7. Planos pendentes (a-fazer) ============ */
  (function(){
    var grid = document.getElementById('plansGrid');
    DATA.plans.forEach(function(p){
      var card = document.createElement('div'); card.className='plan';
      var chips = p.tools.map(function(tid){
        var m = TOOL_META[tid];
        return '<span class="chip"><span class="dot" style="background:var('+m.colorVar+');"></span>'+m.label+'</span>';
      }).join('');
      card.innerHTML =
        '<div class="plan-head"><div><div class="plan-num">a-fazer / '+p.num+' · '+p.items+' itens</div><div class="plan-name">'+p.name+'</div></div>'+
        '<span class="badge '+p.badge.cls+'">'+p.badge.label+'</span></div>'+
        '<div class="plan-solves">'+p.solves+'</div>'+
        '<div class="plan-foot"><div class="plan-tools">'+chips+'</div><div class="plan-est">'+p.est+'</div></div>';
      grid.appendChild(card);
    });
  })();

  (function(){
    var grid = document.getElementById('inProgressGrid');
    var head = document.createElement('div');
    head.style.gridColumn='1/-1'; head.style.fontSize='12.5px'; head.style.color='var(--ink-3)'; head.style.margin='4px 0 -4px';
    head.innerHTML = 'Além dos 5 planos acima, <b style="color:var(--ink-2);">2 iniciativas já em execução</b> — juntas, 31 tarefas ainda pendentes:';
    grid.parentNode.insertBefore(head, grid);
    DATA.in_progress.forEach(function(p){
      var pct = Math.round(p.done/p.items*100);
      var card = document.createElement('div'); card.className='plan inprogress';
      card.innerHTML =
        '<div class="plan-head"><div><div class="plan-num">em andamento · '+p.items+' itens</div><div class="plan-name">'+p.name+'</div></div>'+
        '<span class="badge muted">'+pct+'%</span></div>'+
        '<div class="progress-bar"><span style="width:'+pct+'%;"></span></div>'+
        '<div class="plan-est">'+p.done+' de '+p.items+' itens concluídos.</div>';
      grid.appendChild(card);
    });
  })();

  /* ============ 8. Plano de ação — roadmap ============ */
  (function(){
    var wrap = document.getElementById('roadmapList');
    var badgeCls = {crit:'crit', warn:'warn', good:'good', muted:'muted'};
    DATA.action_plan.forEach(function(a){
      var li = document.createElement('li');
      li.innerHTML =
        '<div class="order">'+String(a.order).padStart(2,'0')+'</div>'+
        '<div><div class="rm-head"><span class="badge '+badgeCls[a.priority]+'">'+
          (a.priority==='crit'?'crítico':a.priority==='warn'?'atenção':a.priority==='good'?'em execução':'fila')+
          '</span><span class="rm-title">'+a.title+'</span><span class="rm-status">'+a.status+'</span></div>'+
        '<div class="rm-why">'+a.why+'</div>'+
        '<div class="rm-next"><b>próxima ação</b>'+a.next+'</div></div>';
      wrap.appendChild(li);
    });
  })();

  /* ============ 9. Achados abertos ============ */
  (function(){
    var wrap = document.getElementById('findingsList');
    var sevLabel = {crit:"CRÍTICO", warn:"ATENÇÃO", muted:"GAP MENOR"};
    DATA.findings.forEach(function(f){
      var row = document.createElement('div'); row.className='finding';
      row.innerHTML =
        '<div class="who"><span class="badge '+f.sev+'">'+sevLabel[f.sev]+'</span><div style="margin-top:6px;">'+f.tool+'</div></div>'+
        '<div class="txt">'+f.txt+'</div>';
      wrap.appendChild(row);
    });
  })();

})();
</script>
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    json_path = os.path.join(OUT_DIR, BASENAME + ".json")
    html_path = os.path.join(OUT_DIR, BASENAME + ".html")

    json_text = json.dumps(DATA, ensure_ascii=False, indent=2)
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_text)

    html_text = TEMPLATE.replace("__REPORT_DATA_JSON__", json_text)
    html_text = html_text.replace("__TOOL_META_JS__", TOOL_META_JS)
    html_text = html_text.replace("__BASENAME__", BASENAME)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_text)

    print(f"[SUCESSO] Gerado: {json_path}")
    print(f"[SUCESSO] Gerado: {html_path}")


if __name__ == "__main__":
    main()
