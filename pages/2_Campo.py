import streamlit as st
import pandas as pd
from datetime import datetime
from database import (
    init_db, get_inspecao_by_id, get_pragas,
    save_praga_plantas, get_inspecao_summary,
    save_observacoes_inspecao, get_observacoes_inspecao, get_observacoes_biblioteca,
    update_ultima_planta, finalize_inspecao,
    save_foto, get_fotos_by_planta, delete_foto, get_foto_data
)
from calculations import calcular_incidencia
from seed_data import seed

st.set_page_config(
    page_title="Ficha de Campo — ISA",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)
init_db()
seed()

st.markdown("""
<style>
div[data-testid="stButton"] > button { min-height:44px; font-size:14px; border-radius:6px; font-weight:600; }

/* ── Cabeçalho da ficha (igual ao Excel) ── */
.fh-box {
    border: 2px solid #555; border-radius: 4px;
    background: #FFFDE7; margin-bottom: 0.6rem;
    overflow: hidden;
}
.fh-box table { width: 100%; border-collapse: collapse; }
.fh-box td {
    padding: 4px 10px; font-size: 0.82rem;
    border: 1px solid #CCC;
}
.fh-lbl { font-weight: 700; color: #1A237E; }
.fh-val { color: #1a1a1a; }
.fh-red { color: #B71C1C; font-weight: 700; }
.fh-quote { font-style: italic; color: #6A1B9A; text-align: center; }
.fh-prox { text-align: right; }
.fh-prox-label { font-weight: 700; color: #1A237E; font-size: 0.8rem; }
.fh-prox-val { color: #B71C1C; font-weight: 700; font-size: 1.05rem; }

/* ── Alertas ── */
.alerta-psil {
    background: #FFEBEE; border: 2px solid #C62828;
    border-radius: 8px; padding: 0.6rem 1rem; margin: 0.4rem 0;
    font-weight: 700; color: #B71C1C; font-size: 0.95rem;
}
.secao-titulo {
    font-size: 1rem; font-weight: 700; color: #1A237E;
    border-left: 4px solid #1976D2; padding-left: 8px;
    margin: 0.8rem 0 0.3rem;
}
</style>
""", unsafe_allow_html=True)

# ── Verificar sessão ───────────────────────────────────────────────────────────
if 'inspecao_id' not in st.session_state or not st.session_state.inspecao_id:
    st.warning("Nenhuma inspeção ativa. Configure primeiro no **Painel**.")
    if st.button("→ Ir ao Painel"):
        st.switch_page("pages/1_Painel.py")
    st.stop()

inspecao_id  = st.session_state.inspecao_id
inspecao     = get_inspecao_by_id(inspecao_id)
if not inspecao:
    st.error("Inspeção não encontrada.")
    st.stop()

total_plantas = inspecao['total_plantas']
pragas        = get_pragas()
summary       = get_inspecao_summary(inspecao_id)

# ── Datas e dia da semana ──────────────────────────────────────────────────────
DIAS = ['SEGUNDA-FEIRA', 'TERÇA-FEIRA', 'QUARTA-FEIRA',
        'QUINTA-FEIRA', 'SEXTA-FEIRA', 'SÁBADO', 'DOMINGO']

def fmt_data(s):
    if not s:
        return '—', ''
    try:
        dt = datetime.strptime(s, '%Y-%m-%d')
        return f"{dt.month}/{dt.day}/{dt.year}", DIAS[dt.weekday()]
    except Exception:
        return s, ''

data_fmt, dia_sem   = fmt_data(inspecao['data_inspecao'])
prox_fmt, prox_dia  = fmt_data(inspecao.get('proxima_inspecao', ''))

# Nº de plantas inspecionadas (máxima registrada ou total)
all_plants_reg = set()
for d in summary.values():
    all_plants_reg |= d['plantas']
n_inspecionadas = max(all_plants_reg) if all_plants_reg else 0

# ── Navegação ─────────────────────────────────────────────────────────────────
nav1, nav2, nav3 = st.columns([2, 2, 2])
with nav1:
    if st.button("← Início", use_container_width=True):
        st.switch_page("app.py")
with nav2:
    if st.button("🦠 Quarentenárias", use_container_width=True):
        st.switch_page("pages/3_Quarentenarias.py")
with nav3:
    if st.button("📊 Ver Relatório", use_container_width=True):
        st.switch_page("pages/4_Relatorio.py")

# ── Cabeçalho da ficha (replica visual do Excel) ──────────────────────────────
st.markdown(f"""
<div class="fh-box">
<table>
  <tr>
    <td colspan="3"><span class="fh-lbl">Propriedade:</span>
        <span class="fh-val"> {inspecao['propriedade']}</span></td>
    <td><span class="fh-lbl">Quadras:</span>
        <span class="fh-red"> {inspecao['numero_quadra']}</span></td>
    <td colspan="2"><span class="fh-lbl">Data da Inspeção</span>
        <span class="fh-red"> {data_fmt} {dia_sem}</span></td>
    <td rowspan="3" style="text-align:center; font-size:2.5rem; width:60px;">🍊</td>
    <td rowspan="3" class="fh-prox">
        <div class="fh-prox-label">DATA DA PRÓXIMA INSPEÇÃO</div>
        <div class="fh-prox-val">{prox_fmt} {prox_dia}</div>
    </td>
  </tr>
  <tr>
    <td colspan="3"><span class="fh-lbl">Proprietário:</span>
        <span class="fh-val"> {inspecao['proprietario']}</span></td>
    <td><span class="fh-lbl">N° de Plantas Insp.:</span>
        <span class="fh-red"> {n_inspecionadas or total_plantas}</span></td>
    <td colspan="2" class="fh-quote">
        <i>"LUCIANO COSTELLA, CONSULTORIA EM CITROS DESDE 2005"</i>
    </td>
  </tr>
  <tr>
    <td colspan="3"><span class="fh-lbl">Talhão:</span>
        <span class="fh-val"> {inspecao['municipio']}-{inspecao['estado']}</span></td>
    <td><span class="fh-lbl">Variedade:</span>
        <span class="fh-red"> {inspecao['variedade']}</span></td>
    <td colspan="2"><span class="fh-lbl">Inspetor:</span>
        <span class="fh-val"> {inspecao['inspetor']}</span>
        &nbsp;&nbsp;
        <span class="fh-lbl">Insp. N°:</span>
        <span class="fh-val"> {inspecao.get('numero_inspecao','—') or '—'}</span>
    </td>
  </tr>
</table>
</div>
""", unsafe_allow_html=True)

# ── Alerta Psilídeo ────────────────────────────────────────────────────────────
psil_ids = {p['id'] for p in pragas if 'psilídeo' in p['nome'].lower() or 'psil' in p['nome'].lower()}
psil_detectado = any(
    pid in summary and len(summary[pid]['plantas']) > 0
    for pid in psil_ids
)
if psil_detectado:
    st.markdown("""
    <div class="alerta-psil">
        🚨 ALERTA CRÍTICO — PSILÍDEO DETECTADO!
        Vetor do Greening (HLB). Aplicar inseticida imediatamente e notificar fiscalização.
    </div>""", unsafe_allow_html=True)

st.divider()

# ── Grade de inspeção (pragas × plantas) ───────────────────────────────────────
st.markdown('<div class="secao-titulo">📋 Plantas Inspecionadas — Marque os números das plantas com presença</div>',
            unsafe_allow_html=True)

total_insp = n_inspecionadas if n_inspecionadas > 0 else total_plantas

# Monta DataFrame: linhas = pragas, colunas = p1..pN + % + Limiar
rows_df = []
for praga in pragas:
    pid = praga['id']
    plants_pest = summary.get(pid, {}).get('plantas', set())
    inc = calcular_incidencia(len(plants_pest), total_insp)
    lim = praga['limiar_acao'] * 100
    acima = inc >= lim and lim > 0

    row = {
        'Praga / Doença':  praga['nome'],
        'Parte Avaliada':  praga.get('parte_avaliada', '') or '—',
        '%':               round(inc, 2),
        'Limiar %':        round(lim, 0),
    }
    for p in range(1, total_plantas + 1):
        row[f'p{p}'] = p in plants_pest
    rows_df.append(row)

df = pd.DataFrame(rows_df)

# Configuração das colunas
cc = {
    'Praga / Doença': st.column_config.TextColumn(
        'Praga / Doença', disabled=True, width='medium'),
    'Parte Avaliada': st.column_config.TextColumn(
        'Parte Avaliada', disabled=True, width='small'),
    '%': st.column_config.NumberColumn(
        '%', disabled=True, width='small', format='%.2f'),
    'Limiar %': st.column_config.NumberColumn(
        'Limiar %', disabled=True, width='small', format='%.0f'),
}
for p in range(1, total_plantas + 1):
    cc[f'p{p}'] = st.column_config.CheckboxColumn(str(p), width='small')

edited_df = st.data_editor(
    df,
    column_config=cc,
    hide_index=True,
    use_container_width=True,
    num_rows='fixed',
    key='grid_campo',
)

# Botão Salvar grade
col_sv, col_info = st.columns([2, 5])
with col_sv:
    if st.button("💾 Salvar Ficha de Campo", type="primary", use_container_width=True):
        for i, row in edited_df.iterrows():
            praga = pragas[i]
            marcadas = [p for p in range(1, total_plantas + 1)
                        if row.get(f'p{p}', False)]
            save_praga_plantas(inspecao_id, praga['id'], marcadas)
            if marcadas:
                update_ultima_planta(inspecao_id, max(marcadas))
        st.success("✅ Ficha de campo salva!")
        st.rerun()
with col_info:
    acima_count = sum(
        1 for praga in pragas
        if calcular_incidencia(
            len(summary.get(praga['id'], {}).get('plantas', set())), total_insp
        ) >= praga['limiar_acao'] * 100 > 0
    )
    st.info(f"💡 Marque ✅ nas plantas com presença e clique **Salvar**. "
            f"Pragas acima do limiar: **{acima_count}**")

st.divider()

# ── Fotos (expander compacto) ──────────────────────────────────────────────────
with st.expander("📷 Fotos da Inspeção", expanded=False):
    planta_foto = st.number_input("Planta", min_value=1, max_value=total_plantas,
                                   value=1, step=1, key="planta_foto_sel")
    fotos_existentes = get_fotos_by_planta(inspecao_id, planta_foto)
    if fotos_existentes:
        cols_foto = st.columns(min(len(fotos_existentes), 4))
        for idx, fm in enumerate(fotos_existentes):
            with cols_foto[idx % 4]:
                fd = get_foto_data(fm['id'])
                if fd:
                    st.image(fd['foto_data'],
                             caption=f"Planta {planta_foto}",
                             use_container_width=True)
                    if st.button("🗑️", key=f"del_foto_{fm['id']}"):
                        delete_foto(fm['id'])
                        st.rerun()
    uploaded = st.file_uploader("Adicionar foto", type=["jpg", "jpeg", "png"],
                                 key=f"up_foto_{planta_foto}",
                                 label_visibility="collapsed")
    if uploaded:
        save_foto(inspecao_id, planta_foto, uploaded.read(), uploaded.name)
        st.success("Foto salva!")
        st.rerun()

# ── Índice de Avaliação + Observações Gerais ──────────────────────────────────
st.markdown('<div class="secao-titulo">📝 Índice de Avaliação e Observações Gerais</div>',
            unsafe_allow_html=True)

obs_bibliot  = get_observacoes_biblioteca()
obs_salvas   = get_observacoes_inspecao(inspecao_id)
obs_sel      = list(obs_salvas)

# Grupos especiais para o Índice de Avaliação (topo, expandidos)
INDICE_GROUPS = {
    'ÁCAROS DA FERRUGEM': [o for o in obs_bibliot if 'ferrugem' in o['descricao'].lower()
                            or 'ácaro' in o['descricao'].lower()],
    'ÁCAROS DA LEPROSE':  [o for o in obs_bibliot if 'leprose' in o['descricao'].lower()],
    'COCHONILHAS':        [o for o in obs_bibliot if 'cochonilha' in o['descricao'].lower()],
    'DOENÇAS':            [o for o in obs_bibliot if o['categoria'] == 'doenca'],
    'PRAGAS DIVERSAS':    [o for o in obs_bibliot if o['categoria'] == 'praga'
                            and 'ferrugem' not in o['descricao'].lower()
                            and 'leprose' not in o['descricao'].lower()
                            and 'cochonilha' not in o['descricao'].lower()],
    'DANOS E OUTROS':     [o for o in obs_bibliot if o['categoria']
                            in ('dano_abiotico', 'fisiologico', 'nutricional',
                                'planta_daninha', 'operacional', 'geral')],
}

# IDs já mostrados nos grupos especiais
shown_ids = {o['id'] for grp in INDICE_GROUPS.values() for o in grp}

for grupo_nome, items in INDICE_GROUPS.items():
    if not items:
        continue
    expanded = grupo_nome in ('ÁCAROS DA FERRUGEM', 'ÁCAROS DA LEPROSE')
    with st.expander(f"▸ {grupo_nome}", expanded=expanded):
        cols = st.columns(2)
        for idx, obs in enumerate(items):
            with cols[idx % 2]:
                checked = st.checkbox(
                    obs['descricao'],
                    key=f"obs_{obs['id']}",
                    value=obs['descricao'] in obs_salvas
                )
                if checked and obs['descricao'] not in obs_sel:
                    obs_sel.append(obs['descricao'])
                elif not checked and obs['descricao'] in obs_sel:
                    obs_sel.remove(obs['descricao'])

# Observação livre
obs_livre = st.text_area("Observação livre (opcional)", height=70, key="obs_livre_campo")
if obs_livre.strip():
    obs_sel.append(obs_livre.strip())

# Botões finais
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    if st.button("💾 Salvar Observações", use_container_width=True):
        save_observacoes_inspecao(inspecao_id, obs_sel)
        st.success("Observações salvas!")
with col_f2:
    if st.button("🦠 Lançar Quarentenárias", use_container_width=True):
        save_observacoes_inspecao(inspecao_id, obs_sel)
        st.switch_page("pages/3_Quarentenarias.py")
with col_f3:
    if st.button("📊 Finalizar e Ver Relatório", type="primary", use_container_width=True):
        save_observacoes_inspecao(inspecao_id, obs_sel)
        finalize_inspecao(inspecao_id)
        st.switch_page("pages/4_Relatorio.py")
