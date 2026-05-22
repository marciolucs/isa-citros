import streamlit as st
import pandas as pd
from database import (
    init_db, get_inspecao_by_id, get_fichas_by_inspecao,
    create_ficha_quarentenaria, save_rua_quarentenaria, get_ruas_by_ficha,
    delete_rua_quarentenaria, delete_ficha_quarentenaria
)
from calculations import consolidar_quarentenaria
from pdf_report import gerar_pdf_ficha_quarentenaria
from seed_data import seed

st.set_page_config(
    page_title="Fichas Quarentenárias — ISA",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="collapsed"
)
init_db()
seed()

st.markdown("""
<style>
div[data-testid="stButton"] > button {
    min-height: 44px; font-size: 14px; border-radius: 8px; font-weight: 600;
}
.header-box {
    background: linear-gradient(135deg, #1B5E20, #2E7D32);
    color: white; padding: 0.8rem 1.5rem; border-radius: 12px; margin-bottom: 1rem;
}
.header-box h2 { color: white; margin: 0; }
.header-box p  { color: #C8E6C9; margin: 0.2rem 0 0; font-size: 0.82rem; }
.insp-meta {
    background: #F9FBE7; border: 1px solid #C5E1A5;
    border-radius: 10px; padding: 0.7rem 1.2rem; margin-bottom: 0.8rem;
}
.insp-meta table { width: 100%; border-collapse: collapse; }
.insp-meta td { padding: 3px 10px; font-size: 0.87rem; }
.insp-meta .lbl { font-weight: 700; color: #33691E; width: 130px; }
.insp-meta .val { color: #1a1a1a; }
.m-card {
    background: white; border: 2px solid #E8F5E9; border-radius: 8px;
    padding: 0.55rem 0.4rem; text-align: center;
}
.m-val  { font-size: 1.5rem; font-weight: 700; color: #1B5E20; line-height: 1.1; }
.m-lab  { font-size: 0.72rem; color: #666; margin-top: 2px; }
.alerta { background:#FFEBEE; border:2px solid #C62828; border-radius:8px;
          padding:0.7rem 1rem; color:#B71C1C; font-weight:700; margin:0.3rem 0; }
.ok     { background:#E8F5E9; border:2px solid #2E7D32; border-radius:8px;
          padding:0.7rem 1rem; color:#1B5E20; font-weight:700; margin:0.3rem 0; }
.ficha-titulo {
    font-size: 1rem; font-weight: 700; color: #1B5E20;
    background: #F1F8E9; border-left: 4px solid #2E7D32;
    padding: 0.4rem 0.8rem; border-radius: 0 6px 6px 0; margin-bottom: 0.4rem;
}
</style>
""", unsafe_allow_html=True)

# ── Verificar sessão ───────────────────────────────────────────────────────────
if 'inspecao_id' not in st.session_state or not st.session_state.inspecao_id:
    st.warning("Nenhuma inspeção ativa. Configure primeiro no **Painel**.")
    if st.button("→ Ir ao Painel"):
        st.switch_page("pages/1_Painel.py")
    st.stop()

inspecao_id = st.session_state.inspecao_id
inspecao = get_inspecao_by_id(inspecao_id)
if not inspecao:
    st.error("Inspeção não encontrada.")
    st.stop()

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="header-box">
    <h2>🦠 Ficha de Inspeção de Doenças Quarentenárias</h2>
    <p>{inspecao['propriedade']} — Quadra {inspecao['numero_quadra']} &nbsp;|&nbsp;
       {inspecao['variedade']} &nbsp;|&nbsp; {inspecao['data_inspecao']}</p>
</div>
""", unsafe_allow_html=True)

col_n1, col_n2, col_n3 = st.columns(3)
with col_n1:
    if st.button("← Voltar ao Campo", use_container_width=True):
        st.switch_page("pages/2_Campo.py")
with col_n2:
    if st.button("📊 Ver Relatório", use_container_width=True):
        st.switch_page("pages/4_Relatorio.py")
with col_n3:
    if st.button("← Início", use_container_width=True):
        st.switch_page("app.py")

st.divider()

# ── Dados da inspeção (espelho do cabeçalho da planilha Excel) ────────────────
st.markdown(f"""
<div class="insp-meta">
<table>
  <tr>
    <td class="lbl">Data da Inspeção:</td><td class="val">{inspecao['data_inspecao']}</td>
    <td class="lbl">Quadra:</td><td class="val">{inspecao['numero_quadra']}</td>
    <td class="lbl">Variedade:</td><td class="val">{inspecao['variedade']}</td>
    <td class="lbl">Total de Plantas:</td><td class="val">{inspecao['total_plantas']}</td>
  </tr>
  <tr>
    <td class="lbl">Propriedade:</td><td class="val">{inspecao['propriedade']}</td>
    <td class="lbl">Proprietário:</td><td class="val">{inspecao['proprietario']}</td>
    <td class="lbl">Município:</td><td class="val">{inspecao['municipio']}-{inspecao['estado']}</td>
    <td class="lbl">Inspetor:</td><td class="val">{inspecao['inspetor']}</td>
  </tr>
</table>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Helpers ───────────────────────────────────────────────────────────────────
def contar_sintomas(s: str) -> int:
    if not s:
        return 0
    return len([n.strip() for n in str(s).replace(';', ',').split(',') if n.strip().isdigit()])


def build_df(ruas: list, inspetor_ficha: str) -> pd.DataFrame:
    """Constrói DataFrame de 26 linhas a partir dos dados do banco."""
    rows_map = {r['numero_rua']: r for r in ruas}
    rows = []
    for i in range(1, 27):
        dir_default = 'I' if i % 2 == 1 else 'V'
        r = rows_map.get(i, {})
        sint = r.get('plantas_sintomas', '') or ''
        rows.append({
            'Rua':               i,
            'I/V':               r.get('direcao_rua', dir_default),
            'Sub. Total':        int(r.get('total_plantas_rua', 0) or 0),
            'Inspetor':          r.get('inspetor_rua', '') or inspetor_ficha,
            'Plantas c/ Sintoma': sint,
            'Qtd':               contar_sintomas(sint),
        })
    return pd.DataFrame(rows)


def salvar_ficha(ficha_id: int, inspetor_ficha: str, edited_df: pd.DataFrame):
    """Persiste o DataFrame editado no banco."""
    saved = 0
    for _, row in edited_df.iterrows():
        rua_num = int(row['Rua'])
        total   = int(row['Sub. Total'])   if pd.notna(row['Sub. Total'])        else 0
        sint    = str(row['Plantas c/ Sintoma']) if pd.notna(row['Plantas c/ Sintoma']) else ''
        ins     = str(row['Inspetor'])     if pd.notna(row['Inspetor'])           else inspetor_ficha
        div     = str(row['I/V'])          if pd.notna(row['I/V'])                else ('I' if rua_num % 2 == 1 else 'V')
        sint    = sint.strip()

        if total > 0 or sint:
            save_rua_quarentenaria(ficha_id, rua_num, div, total, sint, ins)
            saved += 1
        else:
            delete_rua_quarentenaria(ficha_id, rua_num)
    return saved


# ── Render por doença ─────────────────────────────────────────────────────────
def render_doenca(doenca_key: str, inspetor_padrao: str):
    fichas = get_fichas_by_inspecao(inspecao_id, doenca=doenca_key)

    # ── Painel de consolidação ────────────────────────────────────────────────
    if fichas:
        cons = consolidar_quarentenaria(inspecao_id, doenca_key)
        if cons['total_vistoriadas'] > 0:
            c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
            cor_sint = "#C62828" if cons['total_sintomas'] > 0 else "#1B5E20"
            cor_pct  = "#C62828" if cons['notificar']        else "#1B5E20"
            with c1:
                st.markdown(
                    f'<div class="m-card"><div class="m-val">{cons["total_vistoriadas"]}</div>'
                    f'<div class="m-lab">Total Vistoriado</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(
                    f'<div class="m-card"><div class="m-val" style="color:{cor_sint}">{cons["total_sintomas"]}</div>'
                    f'<div class="m-lab">Com Sintomas</div></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(
                    f'<div class="m-card"><div class="m-val" style="color:{cor_pct}">{cons["percentual"]:.3f}%</div>'
                    f'<div class="m-lab">% Incidência</div></div>', unsafe_allow_html=True)
            with c4:
                if cons['notificar']:
                    st.markdown('<div class="alerta">🚨 NOTIFICAÇÃO OBRIGATÓRIA<br/>'
                                '<small>Comunicar imediatamente à Defesa Agropecuária.</small></div>',
                                unsafe_allow_html=True)
                else:
                    st.markdown('<div class="ok">✅ Nenhuma planta com sintoma registrada.</div>',
                                unsafe_allow_html=True)
            st.divider()

    # ── Fichas existentes ─────────────────────────────────────────────────────
    for ficha in fichas:
        ruas          = get_ruas_by_ficha(ficha['id'])
        total_pl      = sum(r['total_plantas_rua'] for r in ruas)
        total_sint    = sum(contar_sintomas(r['plantas_sintomas']) for r in ruas)
        pct           = (total_sint / total_pl * 100) if total_pl > 0 else 0.0

        st.markdown(
            f'<div class="ficha-titulo">📋 {ficha["numero_ficha"]} &nbsp;·&nbsp; '
            f'Inspetor: {ficha["inspetor"]} &nbsp;|&nbsp; '
            f'{total_pl} plantas vistoriadas &nbsp;·&nbsp; '
            f'{total_sint} com sintoma &nbsp;·&nbsp; {pct:.3f}%</div>',
            unsafe_allow_html=True
        )

        df = build_df(ruas, ficha['inspetor'])

        edited_df = st.data_editor(
            df,
            column_config={
                'Rua': st.column_config.NumberColumn(
                    'Rua', disabled=True, width='small'),
                'I/V': st.column_config.SelectboxColumn(
                    'I/V', options=['I', 'V'], width='small'),
                'Sub. Total': st.column_config.NumberColumn(
                    'Sub. Total', min_value=0, max_value=9999, width='small'),
                'Inspetor': st.column_config.TextColumn(
                    'Inspetor', width='medium'),
                'Plantas c/ Sintoma': st.column_config.TextColumn(
                    'Plantas c/ Sintoma', width='large',
                    help='Números separados por vírgula — ex: 11, 12, 45'),
                'Qtd': st.column_config.NumberColumn(
                    'Qtd', disabled=True, width='small'),
            },
            hide_index=True,
            use_container_width=True,
            num_rows='fixed',
            key=f"grid_{ficha['id']}",
        )

        # Botões de ação
        ba1, ba2, ba3 = st.columns([2, 2, 2])

        with ba1:
            if st.button("💾 Salvar Ficha", key=f"save_{ficha['id']}",
                         type="primary", use_container_width=True):
                n = salvar_ficha(ficha['id'], ficha['inspetor'], edited_df)
                st.success(f"✅ {n} linha(s) salvas!")
                st.rerun()

        with ba2:
            key_pdf = f"pdf_bytes_{ficha['id']}"
            if st.button("📄 Gerar PDF da Ficha", key=f"btn_pdf_{ficha['id']}",
                         use_container_width=True):
                ruas_db = get_ruas_by_ficha(ficha['id'])
                pdf_b   = gerar_pdf_ficha_quarentenaria(inspecao, ficha, ruas_db, doenca_key)
                st.session_state[key_pdf] = pdf_b
                st.rerun()

            if key_pdf in st.session_state:
                nome_pdf = (
                    f"Ficha_{doenca_key}_{ficha['numero_ficha'].replace(' ','_')}"
                    f"_{inspecao['data_inspecao'].replace('-','')}.pdf"
                )
                st.download_button(
                    "⬇️ Baixar PDF da Ficha",
                    data=st.session_state[key_pdf],
                    file_name=nome_pdf,
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"dl_{ficha['id']}",
                )

        with ba3:
            if st.button("🗑️ Excluir Ficha", key=f"del_{ficha['id']}",
                         use_container_width=True):
                delete_ficha_quarentenaria(ficha['id'])
                st.session_state.pop(f"pdf_bytes_{ficha['id']}", None)
                st.warning("Ficha removida.")
                st.rerun()

        st.divider()

    # ── Criar nova ficha ──────────────────────────────────────────────────────
    with st.expander("➕ Criar Nova Ficha", expanded=(len(fichas) == 0)):
        with st.form(f"nova_ficha_{doenca_key}"):
            nf_col1, nf_col2 = st.columns(2)
            with nf_col1:
                num_f = st.text_input("Número da Ficha",
                                      value=f"FICHA {len(fichas) + 1:02d}")
            with nf_col2:
                opcoes_ins = ["Luciano Costella", "Higor", "Hig/Luc", "Outro"]
                ins_sel = st.selectbox("Inspetor", opcoes_ins,
                                       key=f"ins_{doenca_key}")
                if ins_sel == "Outro":
                    ins_sel = st.text_input("Nome do inspetor",
                                            key=f"ins_outro_{doenca_key}")

            if st.form_submit_button("✅ Criar Ficha", use_container_width=True,
                                     type="primary"):
                if num_f.strip() and ins_sel.strip():
                    create_ficha_quarentenaria(
                        inspecao_id, doenca_key, ins_sel.strip(),
                        num_f.strip().upper()
                    )
                    st.success(f"Ficha '{num_f.upper()}' criada! Preencha as linhas na tabela.")
                    st.rerun()
                else:
                    st.error("Informe o número da ficha e o nome do inspetor.")


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_g, tab_c = st.tabs(["🟡 GREENING (HLB)", "🔴 CANCRO CÍTRICO"])

with tab_g:
    render_doenca("GREENING", inspecao['inspetor'])

with tab_c:
    render_doenca("CANCRO", inspecao['inspetor'])
