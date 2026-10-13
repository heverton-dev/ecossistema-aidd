# -*- coding: utf-8 -*-
"""Guarda da abolição do Next.js (Lei #11: o padrão-ouro é TanStack Router + Vite).

Varre os arquivos versionados (e os novos não ignorados) e reprova qualquer rastro vivo do
framework: dependência `next`, `next/link`, `NEXT_PUBLIC_*`, `next.config`, `NextJSExporter`,
`nextjs_*`, ou o texto "Next.js" sem ser para declarar a abolição.

Não entram na varredura (registro histórico, gerado ou de terceiros):
  - documentos datados (auditorias, relatórios, melhorias, livros, mapas gerados, seções);
  - listas defensivas de pastas de build `.next` (inertes; no fluxo freedom analisam projetos externos);
  - produtos de terceiros que são, eles próprios, apps Next.js (9Router, Cal.com, ERPNext).
"""
import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

PADRAO = re.compile(
    r"next\.?js|next/(?:link|navigation|image|font|router)|NEXT_PUBLIC|eslint-config-next|next\.config"
    r"|NextJSExporter|nextjs_exporter|nextjs_app_router|nextjs_typescript|nextjs-on-cloudflare"
    r"|\"next\"\s*:\s*\"[\^~]?\d",
    re.IGNORECASE,
)
DECLARA_ABOLICAO = re.compile(r"abolid|abolic|aboli[cç]|abolish", re.IGNORECASE)

HISTORICO = (
    "docs/auditoria/", "docs/melhorias/", "docs/reports/", "docs/relatorios/", "docs/teste-end-to-end/",
    "docs/issues/", "docs/explicacoes/", "docs/testes/", "docs/oficiais/", "docs/secoes/", "docs/features/",
    "docs/livros/", "docs/mapas-visuais/", "secoes/", "AUDITORIA-FLUXO-PURE/", "projetos/", ".mimocode/plans/",
)
# Testes e gates cujo trabalho é justamente nomear o framework para rejeitá-lo.
PROVAM_A_REJEICAO = (
    "tests/test_sem_nextjs_vivo.py",
    "tests/test_forge_templates_padrao_ouro.py",
    "modulos/02-triade-motores/fluxo-01-pure/gates/test_g_stack_padrao_ouro.py",
    "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/tests/unit/test_tanstack_exporter.py",
    "modulos/02-triade-motores/fluxo-02-open/core/aidd-open/tests/test_frontend_stack_tanstack.py",
)
# Produtos de terceiros que são apps Next.js (descrição do que o ecossistema orquestra).
DE_TERCEIROS = (
    "modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops/data/requisitos_recursos.json",
    "modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops/scripts/pipeline_ops.py",
    "modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops/GUIA.md",
)
# Mensagens/regras dos gates que mandam REPROVAR dependência `next` precisam citá-la.
REGRAS_DE_REJEICAO = (
    "G_STACK_PADRAO_OURO.py", "G_CONTRACTS.py", "G_FACTORY_INTEGRATION.py", "09_integracao.py",
)


def _arquivos():
    saida = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard"], cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    ).stdout.splitlines()
    return [f for f in saida if not f.startswith(HISTORICO)]


def test_nenhum_rastro_vivo_de_nextjs():
    achados = []
    for rel in _arquivos():
        if rel in PROVAM_A_REJEICAO or rel in DE_TERCEIROS or rel.endswith("aidd-9router/assets/ninerouter-stack.yml"):
            continue
        caminho = RAIZ / rel
        try:
            texto = caminho.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for numero, linha in enumerate(texto.splitlines(), 1):
            if PADRAO.search(linha) and not DECLARA_ABOLICAO.search(linha):
                if rel.endswith(REGRAS_DE_REJEICAO) and re.search(r"reprov|abolid|problemas\.append|rejeit", linha, re.I):
                    continue
                achados.append(f"{rel}:{numero}: {linha.strip()[:110]}")
    assert achados == [], f"{len(achados)} rastro(s) vivo(s) de Next.js:\n" + "\n".join(achados[:80])
