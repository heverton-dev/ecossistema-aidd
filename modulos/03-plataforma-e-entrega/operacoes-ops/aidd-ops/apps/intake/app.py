# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops — Intake Web Interativo (Streamlit | Anti-NIH #19)
=============================================================================
Frontend web do pipeline determinístico de infraestrutura (Fases 1-3).
Reusa 100% a lógica das fases do CLI através do intake_core — nenhuma
lógica duplicada, nenhum LLM: o JSON baixado é idêntico ao
PLANO-INFRAESTRUTURA.json gerado por `pipeline_ops.py plan`.

Abre em http://localhost:8501 (ou no domínio configurado no Coolify).

Fluxo:
  1. Usuário descreve o negócio em texto livre OU escolhe um nicho pronto.
  2. Cliente chama o builder único (montar_plano_em_memoria).
  3. Resultado renderizado + download do plano em JSON.
  4. Em texto ambíguo (NICHO_AMBIGUO), o app oferece a escolha explícita
     do candidato e regenera — exatamente como o --nicho do CLI.
=============================================================================
"""

import sys
import os

_APPS_DIR = os.path.dirname(os.path.abspath(__file__))
_TOOL_ROOT = os.path.dirname(os.path.dirname(_APPS_DIR))
if _APPS_DIR not in sys.path:
    sys.path.insert(0, _APPS_DIR)

import streamlit as st

import intake_core

st.set_page_config(
    page_title="AIDD-Ops — Intake Web",
    layout="centered",
)

st.title("AIDD-Ops — Intake Web")
st.caption(
    "Plano de infraestrutura determinístico (Intake → Curadoria → Sizing). "
    "Mesmas 3 fases do CLI, mesmo arquivo JSON. Sem LLM, sem promoção não testada."
)

with st.sidebar:
    st.subheader("Pipeline (Fases 1-3)")
    st.write("- 01 | Reconhecimento de Nicho (catálogo determinístico)")
    st.write("- 02 | Curadoria da Stack (validação por JSON Schema)")
    st.write("- 03 | Sizing de VPS e bancos (requisitos reais)")
    st.caption("Compatível com o JSON da CLI: pipeline_ops.py plan")

if "plano" not in st.session_state:
    st.session_state.plano = None
    st.session_state.entrada = ("", None)
    st.session_state.candidate_desc = None

modo = st.radio(
    "Como você prefere descrever o negócio?",
    options=["Descrever em texto livre", "Escolher um nicho pronto"],
    horizontal=True,
)

texto = ""
nicho_explicito = None
if modo == "Descrever em texto livre":
    texto = st.text_area(
        "Descreva o negócio em 1-2 frases (ex.: \"Clínica odontológica com agendamento de pacientes e WhatsApp\")",
        height=100,
        key="texto_livre",
    )
else:
    nichos = intake_core.listar_nichos()
    labels = {f"{n['nome_exibicao']} ({n['slug']})": n["slug"] for n in nichos}
    escolha = st.selectbox("Selecione o nicho", list(labels.keys()))
    nicho_explicito = labels[escolha]


def _gerar(texto_atual: str, nicho_atual: str):
    plano = intake_core.gerar_plano(texto_atual, nicho_explicito=nicho_atual)
    st.session_state.plano = plano
    st.session_state.entrada = (texto_atual, nicho_atual)


if st.button("Gerar Plano de Infraestrutura", type="primary"):
    if not texto.strip() and not nicho_explicito:
        st.error("Informe o texto do negócio ou escolha um nicho para gerar o plano.")
    else:
        _gerar(
            texto if nicho_explicito in (None, "") else (texto or nicho_explicito),
            nicho_explicito,
        )

plano = st.session_state.plano

# ── Recuperação de texto ambíguo (acima da renderização do resultado) ──
if plano is not None:
    erro = intake_core.primeiro_erro(plano)
    if erro and erro.get("codigo") == "NICHO_AMBIGUO":
        candidatos = (erro.get("detalhes") or {}).get("candidatos", [])
        if candidatos:
            r = st.radio(
                "O texto bateu com mais de 1 nicho. Qual se encaixa melhor?",
                options=[f"{c['nome_exibicao']} ({c['slug']})" for c in candidatos],
            )
            slug_escolhido = candidatos[[f"{c['nome_exibicao']} ({c['slug']})" for c in candidatos].index(r)]["slug"]
            if st.button("Gerar com este nicho"):
                _gerar(st.session_state.entrada[0], slug_escolhido)
                st.rerun()

if plano is None:
    st.info("Preencha uma descrição (ou escolha um nicho) e clique em **Gerar Plano de Infraestrutura**.")
    st.stop()

erro = intake_core.primeiro_erro(plano)

if erro:
    st.error(f"**{erro.get('codigo')}** — {erro.get('erro')}")
    if erro.get("codigo") == "NICHO_NAO_RECONHECIDO":
        disponiveis = (erro.get("detalhes") or {}).get("slugs_disponiveis", [])
        if disponiveis:
            st.caption("Nichos disponíveis no catálogo: " + ", ".join(disponiveis))
    st.download_button(
        "Baixar rascunho do plano (JSON)",
        data=intake_core.plano_para_json(plano),
        file_name="PLANO-INFRAESTRUTURA.json",
        mime="application/json",
    )
    st.stop()

# ── Resultado de sucesso ──
dados_f1 = plano["fase_1_intake"]["saida"]
dados_f2 = plano["fase_2_curadoria"]["saida"]
dados_f3 = plano["fase_3_sizing"]["saida"]

st.subheader("Resumo do Plano")

c1, c2, c3 = st.columns(3)
c1.metric("Nicho", dados_f1["nicho_nome_exibicao"])
vps = dados_f3.get("vps", {})
c2.metric("VPS", f"{vps.get('vcpu', '?')} vCPU / {vps.get('ram_gb', '?')} GB RAM")
c3.metric("Total de ferramentas", len(dados_f2.get("ferramentas", [])))

st.markdown("#### Stack selecionada (Fase 2)")
for ferr in dados_f2.get("ferramentas", []):
    st.markdown(f"- **{ferr.get('nome', '?')}**{' — ' + ferr.get('descricao', '') if ferr.get('descricao') else ''}")

st.markdown("#### Sizing da VPS (Fase 3)")
st.write(
    f"{vps.get('vcpu', '?')} vCPU · {vps.get('ram_gb', '?')} GB RAM · "
    f"{vps.get('disco_gb', '?')} GB disco · {vps.get('observacoes', '')}"
)
bancos = dados_f3.get("bancos_logicos", [])
if bancos:
    st.write("**Bancos lógicos:** " + ", ".join(b.get("nome_banco", "?") for b in bancos))
else:
    st.write("**Bancos lógicos:** nenhum necessário")

st.download_button(
    "Baixar PLANO-INFRAESTRUTURA.json",
    data=intake_core.plano_para_json(plano),
    file_name="PLANO-INFRAESTRUTURA.json",
    mime="application/json",
)