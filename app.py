import streamlit as st
from database import init_db
from seed_data import seed
import ui

st.set_page_config(
    page_title="ISA — Inspeção Fitossanitária Citros",
    page_icon="🍊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Inicialização ─────────────────────────────────────────────────────────────
init_db()
seed()
ui.inject_theme()
ui.top_nav("inicio")

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
ui.page_header(
    "🍊", "Sistema de Inspeção Fitossanitária",
    "Citros | Luciano Costella — Téc. Agropecuária CFTA 17893896825 | Consultoria desde 2005"
)

# ── Módulos — layout 2×2 (mobile-friendly) ────────────────────────────────────
row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

with row1_col1:
    st.markdown("""
    <div class="modulo-card">
        <div class="modulo-icon">⚙️</div>
        <div class="modulo-title">Painel</div>
        <div class="modulo-desc">Configure e inicie uma nova inspeção de campo</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Abrir Painel", use_container_width=True, key="btn_painel"):
        st.switch_page("pages/1_Painel.py")

with row1_col2:
    st.markdown("""
    <div class="modulo-card">
        <div class="modulo-icon">🔍</div>
        <div class="modulo-title">Campo</div>
        <div class="modulo-desc">Registre pragas planta a planta (até 70 plantas)</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Abrir Campo", use_container_width=True, key="btn_campo"):
        st.switch_page("pages/2_Campo.py")

with row2_col1:
    st.markdown("""
    <div class="modulo-card">
        <div class="modulo-icon">🦠</div>
        <div class="modulo-title">Quarentenárias</div>
        <div class="modulo-desc">Fichas de Greening e Cancro Cítrico por rua</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Abrir Quarentenárias", use_container_width=True, key="btn_quar"):
        st.switch_page("pages/3_Quarentenarias.py")

with row2_col2:
    st.markdown("""
    <div class="modulo-card">
        <div class="modulo-icon">📊</div>
        <div class="modulo-title">Relatório</div>
        <div class="modulo-desc">Gere e baixe o PDF para envio ao produtor</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Abrir Relatório", use_container_width=True, key="btn_rel"):
        st.switch_page("pages/4_Relatorio.py")

# ── Módulo consolidado (largura total) ────────────────────────────────────────
st.markdown("""
<div class="modulo-card">
    <div class="modulo-icon">🗂️</div>
    <div class="modulo-title">Consolidado por Propriedade</div>
    <div class="modulo-desc">Todas as quadras numa tabela só, com o % de cada praga — igual à aba CONTROLE do Excel</div>
</div>
""", unsafe_allow_html=True)
if st.button("Abrir Consolidado", use_container_width=True, key="btn_consolidado"):
    st.switch_page("pages/5_Consolidado.py")

st.divider()

# ── Inspeções recentes ─────────────────────────────────────────────────────────
from database import get_inspecoes_recentes

st.subheader("Inspeções Recentes")
inspecoes = get_inspecoes_recentes(10)
if not inspecoes:
    st.info("Nenhuma inspeção registrada ainda. Clique em **Painel** para começar.")
else:
    for insp in inspecoes:
        status = insp.get('status', 'em_andamento')
        badge = ('<span class="badge-verde">✓ Concluída</span>' if status == 'concluida'
                 else '<span class="badge-amarelo">⏳ Em andamento</span>')
        col_a, col_b, col_c, col_d = st.columns([4, 2, 2, 2])
        with col_a:
            st.markdown(
                f"**{insp['propriedade']}** — Q.{insp['numero_quadra']} ({insp['variedade']})<br/>"
                f"<small>{insp['proprietario']}</small>",
                unsafe_allow_html=True
            )
        with col_b:
            st.markdown(f"`{insp['data_inspecao']}`")
        with col_c:
            st.markdown(badge, unsafe_allow_html=True)
        with col_d:
            if st.button("Continuar", key=f"cont_{insp['id']}", use_container_width=True):
                st.session_state.inspecao_id = insp['id']
                ultima = insp.get('ultima_planta') or 0
                st.session_state.planta_atual = max(1, ultima + 1)
                st.switch_page("pages/2_Campo.py")
        st.divider()
