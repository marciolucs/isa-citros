import streamlit as st
import pandas as pd
import plotly.express as px
from database import (
    init_db, get_inspecao_by_id, get_inspecoes_recentes,
    get_observacoes_inspecao, finalize_inspecao, get_plantas_inspecionadas
)
from calculations import get_relatorio_pragas, consolidar_quarentenaria, plantas_inspecionadas
from pdf_report import gerar_pdf
from seed_data import seed
import ui

st.set_page_config(page_title="Relatório — ISA", page_icon="📊", layout="wide",
                   initial_sidebar_state="collapsed")
init_db()
seed()
ui.inject_theme()
ui.top_nav("relatorio")

# CSS específico: cartões de métrica do relatório
st.markdown("""
<style>
.metric-card { background:white; border-radius:10px; padding:1rem; text-align:center;
               border:2px solid #E8F5E9; }
.metric-value { font-size:2rem; font-weight:700; color:#1B5E20; }
.metric-label { font-size:0.8rem; color:#666; }
</style>
""", unsafe_allow_html=True)

ui.page_header("📊", "Relatório de Inspeção Fitossanitária",
               "Visualize resultados, estatísticas e gere o PDF para envio ao produtor")

st.divider()

# Selecionar inspeção
inspecoes = get_inspecoes_recentes(30)
if not inspecoes:
    st.info("Nenhuma inspeção registrada ainda.")
    st.stop()

# Nº de plantas marcadas por inspeção (para o usuário identificar a certa)
_marcadas = {}
insp_opts = {}
for i in inspecoes:
    _maxp, cnt = get_plantas_inspecionadas(i['id'])
    _marcadas[i['id']] = cnt
    aviso = "  ⚠️ SEM PLANTAS" if cnt == 0 else f"  ✓ {cnt} plantas"
    label = (f"{i['propriedade']} — Q.{i['numero_quadra']} ({i['variedade']}) | "
             f"{i['data_inspecao']}{aviso}")
    insp_opts[label] = i['id']

# Pré-selecionar a inspeção ativa da sessão; senão, a 1ª que tenha dados
default_idx = 0
ids_list = list(insp_opts.values())
if 'inspecao_id' in st.session_state and st.session_state.inspecao_id in ids_list:
    default_idx = ids_list.index(st.session_state.inspecao_id)
else:
    for idx, iid in enumerate(ids_list):
        if _marcadas.get(iid, 0) > 0:
            default_idx = idx
            break

insp_sel = st.selectbox("Selecionar Inspeção", list(insp_opts.keys()), index=default_idx)
inspecao_id = insp_opts[insp_sel]

# Aviso se a inspeção selecionada não tem plantas marcadas
if _marcadas.get(inspecao_id, 0) == 0:
    st.warning("⚠️ Esta inspeção **não tem nenhuma planta marcada**. "
               "Se você marcou plantas, verifique se não há **outra inspeção da mesma quadra** "
               "na lista acima (as com ✓ têm dados), ou volte ao **Campo** e clique em **Salvar**.")

# Clear cached PDF when inspection changes
if st.session_state.get('_pdf_inspecao_id') != inspecao_id:
    st.session_state.pop('pdf_bytes', None)
    st.session_state['_pdf_inspecao_id'] = inspecao_id

inspecao = get_inspecao_by_id(inspecao_id)
if not inspecao:
    st.error("Inspeção não encontrada.")
    st.stop()

st.session_state.inspecao_id = inspecao_id
total_plantas = inspecao['total_plantas']
total_inspecionado = plantas_inspecionadas(inspecao_id, total_plantas)

# ── Cabeçalho da propriedade ───────────────────────────────────────────────────
with st.container():
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.markdown(f"**Propriedade**<br/>{inspecao['propriedade']}", unsafe_allow_html=True)
    col_b.markdown(f"**Proprietário**<br/>{inspecao['proprietario']}", unsafe_allow_html=True)
    col_c.markdown(f"**Município**<br/>{inspecao['municipio']}-{inspecao['estado']}", unsafe_allow_html=True)
    col_d.markdown(
        f"**Data / Próxima**<br/>{inspecao['data_inspecao']} / {inspecao.get('proxima_inspecao', '—')}",
        unsafe_allow_html=True
    )
    st.caption(
        f"Quadra: {inspecao['numero_quadra']} | Variedade: {inspecao['variedade']} | "
        f"Total Plantas: {total_plantas} | Inspecionadas: {total_inspecionado} | "
        f"Inspetor: {inspecao['inspetor']} | "
        f"Insp. Nº {inspecao.get('numero_inspecao', '—')} | "
        f"Início: {inspecao.get('inicio_inspecao', '—')} | Direção: {inspecao.get('direcao', '—')}"
    )

st.divider()

# ── Dados de pragas ────────────────────────────────────────────────────────────
pragas_data = get_relatorio_pragas(inspecao_id, total_inspecionado)

# Métricas gerais
total_afetadas = len(set(p_num for p in pragas_data for p_num in p['plantas']))
acima_limiar = [p for p in pragas_data if p['acima_limiar']]
criticos = [p for p in pragas_data if p['alerta_critico'] and p['incidencia'] > 0]

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.markdown(f'<div class="metric-card"><div class="metric-value">{total_inspecionado}</div><div class="metric-label">Plantas Inspecionadas</div></div>', unsafe_allow_html=True)
with col_m2:
    cor = "#C62828" if total_afetadas > 0 else "#2E7D32"
    st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{cor}">{total_afetadas}</div><div class="metric-label">Plantas com Praga</div></div>', unsafe_allow_html=True)
with col_m3:
    cor = "#C62828" if acima_limiar else "#2E7D32"
    st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{cor}">{len(acima_limiar)}</div><div class="metric-label">Pragas Acima do Limiar</div></div>', unsafe_allow_html=True)
with col_m4:
    cor = "#C62828" if criticos else "#2E7D32"
    st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{cor}">{len(criticos)}</div><div class="metric-label">Alertas Críticos</div></div>', unsafe_allow_html=True)

st.divider()

# ── Tabela de incidência ───────────────────────────────────────────────────────
st.markdown('<div class="secao-titulo">📋 Incidência por Praga/Doença</div>', unsafe_allow_html=True)

if not pragas_data:
    st.info("Nenhuma praga registrada para esta inspeção.")
else:
    df_rows = []
    for p in pragas_data:
        if p['alerta_critico'] and p['incidencia'] > 0:
            status = "⚠️ CRÍTICO"
        elif p['acima_limiar']:
            status = "▶ ACIMA DO LIMIAR"
        else:
            status = "✓ OK"
        df_rows.append({
            'Praga / Doença': p['nome'],
            'Plantas Afetadas': p['plantas_afetadas'],
            '% Incidência': p['incidencia'],
            'Limiar (%)': p['limiar_pct'],
            'Situação': status,
        })

    df = pd.DataFrame(df_rows)

    def colorir(row):
        if '⚠️' in str(row['Situação']):
            return ['background-color: #FFEBEE; color: #B71C1C; font-weight:bold'] * len(row)
        elif '▶' in str(row['Situação']):
            return ['background-color: #FFF9C4; color: #F57F17; font-weight:bold'] * len(row)
        else:
            return ['background-color: #F1F8E9; color: #1B5E20'] * len(row)

    styled = df.style.apply(colorir, axis=1).format({
        '% Incidência': '{:.1f}%',
        'Limiar (%)': '{:.0f}%',
    })
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # Gráfico de barras
    if len(pragas_data) > 0:
        fig_data = [p for p in pragas_data if p['plantas_afetadas'] > 0]
        if fig_data:
            df_chart = pd.DataFrame([{
                'Praga': p['nome'],
                '% Incidência': p['incidencia'],
                'Limiar': p['limiar_pct'],
                'Status': 'Crítico' if (p['alerta_critico'] and p['incidencia'] > 0)
                          else ('Acima' if p['acima_limiar'] else 'OK')
            } for p in fig_data])

            color_map = {'Crítico': '#C62828', 'Acima': '#F9A825', 'OK': '#2E7D32'}
            fig = px.bar(
                df_chart, x='Praga', y='% Incidência',
                color='Status', color_discrete_map=color_map,
                title='Incidência de Pragas (%)',
                height=350
            )
            fig.update_layout(xaxis_tickangle=-30, margin=dict(b=100))
            st.plotly_chart(fig, use_container_width=True)

# ── Sugestões de controle ──────────────────────────────────────────────────────
pragas_acao = [p for p in pragas_data if p['acima_limiar'] or (p['alerta_critico'] and p['incidencia'] > 0)]
if pragas_acao:
    st.markdown('<div class="secao-titulo">💡 Sugestões de Ação e Controle</div>', unsafe_allow_html=True)
    for p in pragas_acao:
        with st.expander(f"{'⚠️' if p['alerta_critico'] else '▶'} {p['nome']}", expanded=True):
            if p['alerta_critico']:
                st.warning(p['sugestao_controle'])
            else:
                st.info(p['sugestao_controle'])
    st.divider()

# ── Consolidação Quarentenária ─────────────────────────────────────────────────
st.markdown('<div class="secao-titulo">🦠 Rastreabilidade Quarentenária</div>', unsafe_allow_html=True)

for doenca in ("GREENING", "CANCRO"):
    cons = consolidar_quarentenaria(inspecao_id, doenca)
    if cons['total_vistoriadas'] == 0:
        st.caption(f"*{doenca}: Nenhuma ficha quarentenária lançada.*")
        continue

    col_q1, col_q2, col_q3 = st.columns(3)
    col_q1.metric(f"{doenca} — Total Vistoriado", f"{cons['total_vistoriadas']} plantas")
    col_q2.metric("Com Sintomas", f"{cons['total_sintomas']}")
    col_q3.metric("Incidência", f"{cons['percentual']:.3f}%")

    if cons['notificar']:
        st.error(f"🚨 {doenca}: NOTIFICAÇÃO OBRIGATÓRIA — {cons['total_sintomas']} plantas com sintoma!")
        for ficha in cons['fichas']:
            if ficha['total_sintomas'] == 0:
                continue
            st.markdown(f"**{ficha['numero_ficha']}** — Inspetor: {ficha['inspetor']}")
            for rua in ficha['ruas']:
                if rua['qtd_sintomas'] > 0:
                    st.markdown(
                        f"&nbsp;&nbsp;Rua {rua['numero_rua']} ({rua['direcao']}) — "
                        f"Plantas: **{rua['plantas_sintomas']}** ({rua['qtd_sintomas']} plantas)"
                    )
    else:
        st.success(f"✅ {doenca}: Nenhuma planta com sintoma registrada.")

st.divider()

# ── Observações Gerais ─────────────────────────────────────────────────────────
obs = get_observacoes_inspecao(inspecao_id)
if obs:
    st.markdown('<div class="secao-titulo">📝 Observações Gerais</div>', unsafe_allow_html=True)
    for txt in obs:
        st.markdown(f"• {txt}")
    st.divider()

# ── Assinatura e técnico ───────────────────────────────────────────────────────
with st.container():
    col_ass1, col_ass2 = st.columns(2)
    with col_ass1:
        st.markdown("""
        **Luciano Costella**
        Técnico em Agropecuária — CFTA: 17893896825
        *"Consultoria em Citros desde 2005"*
        lucianocostella@yahoo.com.br | (19) 99278-2525
        """)
    with col_ass2:
        st.markdown(f"**Data da Inspeção:** {inspecao['data_inspecao']}")
        st.markdown(f"**Próxima Inspeção:** {inspecao.get('proxima_inspecao', '—')}")

st.divider()

# ── Gerar PDF ──────────────────────────────────────────────────────────────────
st.markdown('<div class="secao-titulo">📄 Gerar Relatório em PDF</div>', unsafe_allow_html=True)
st.info("O PDF será gerado com todos os dados acima: cabeçalho, tabela de pragas, alertas, rastreabilidade quarentenária, observações, fotos e assinatura.")

col_fin1, col_fin2 = st.columns(2)
with col_fin1:
    if st.button("📄 Gerar PDF", use_container_width=True, type="primary"):
        with st.spinner("Gerando relatório PDF..."):
            try:
                pdf_bytes = gerar_pdf(inspecao)
                st.session_state['pdf_bytes'] = pdf_bytes
                finalize_inspecao(inspecao_id)
                st.success("PDF gerado! Clique em **Baixar PDF** abaixo.")
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")

    if 'pdf_bytes' in st.session_state:
        nome_arquivo = (
            f"ISA_{inspecao['propriedade'].replace(' ', '_')}"
            f"_Q{inspecao['numero_quadra']}"
            f"_{inspecao['data_inspecao'].replace('-', '')}.pdf"
        )
        st.download_button(
            label="⬇️ Baixar PDF",
            data=st.session_state['pdf_bytes'],
            file_name=nome_arquivo,
            mime="application/pdf",
            use_container_width=True
        )

with col_fin2:
    st.markdown("""
    **Dica para enviar ao produtor:**
    1. Baixe o PDF
    2. Abra o WhatsApp Web ou app
    3. Envie o arquivo diretamente no chat do produtor
    """)
