import streamlit as st
from datetime import date, timedelta
from database import (
    init_db, get_clientes, get_quadras_by_cliente,
    create_inspecao, add_cliente, add_quadra
)
from seed_data import seed
import ui

st.set_page_config(page_title="Painel — ISA", page_icon="⚙️", layout="wide",
                   initial_sidebar_state="collapsed")
init_db()
seed()
ui.inject_theme()
ui.top_nav("painel")

ui.page_header("⚙️", "Painel de Configuração da Inspeção",
               "Selecione a propriedade e configure os parâmetros antes de ir ao campo")

# ── Formulário principal ───────────────────────────────────────────────────────
tab_nova, tab_cadastro = st.tabs(["📋 Nova Inspeção", "➕ Cadastrar Propriedade/Quadra"])

# ── Tab: Nova Inspeção ──────────────────────────────────────────────────────────
with tab_nova:
    clientes = get_clientes()
    if not clientes:
        st.warning("Nenhuma propriedade cadastrada. Acesse a aba **Cadastrar Propriedade/Quadra**.")
        st.stop()

    props = {f"{c['propriedade']} — {c['proprietario']} ({c['municipio']}-{c['estado']})": c['id']
             for c in clientes}
    prop_selecionada = st.selectbox("🏡 Propriedade / Produtor", options=list(props.keys()))
    cliente_id = props[prop_selecionada]
    cliente = next(c for c in clientes if c['id'] == cliente_id)

    st.markdown(f"""
    <div class="info-box">
        <b>Proprietário:</b> {cliente['proprietario']} &nbsp;|&nbsp;
        <b>Município:</b> {cliente['municipio']}-{cliente['estado']}
    </div>
    """, unsafe_allow_html=True)

    quadras = get_quadras_by_cliente(cliente_id)
    if not quadras:
        st.warning("Esta propriedade não possui quadras cadastradas. Acesse **Cadastrar Propriedade/Quadra**.")
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        quadras_opts = {f"Quadra {q['numero_quadra']} — {q['variedade']} ({q['total_plantas']} plantas)": q['id']
                        for q in quadras}
        quadra_selecionada = st.selectbox("🌿 Quadra", options=list(quadras_opts.keys()))
        quadra_id = quadras_opts[quadra_selecionada]
        quadra = next(q for q in quadras if q['id'] == quadra_id)

        st.markdown(f"""
        <div class="info-box">
            <b>Variedade:</b> {quadra['variedade']} &nbsp;|&nbsp;
            <b>Total de Plantas:</b> {quadra['total_plantas']}
        </div>
        """, unsafe_allow_html=True)

        data_insp = st.date_input("📅 Data da Inspeção", value=date.today())
        prox_insp = st.date_input("📅 Próxima Inspeção (sugestão)", value=date.today() + timedelta(days=14))

    with col2:
        inspetores = ["Luciano Costella", "Higor", "Hig/Luc", "Outro"]
        inspetor = st.selectbox("👤 Inspetor Responsável", inspetores)
        if inspetor == "Outro":
            inspetor = st.text_input("Nome do Inspetor")

        num_inspecao_opts = ["1º", "2º", "3º", "4º", "5º", "6º", "7º", "8º", "9º", "10º",
                             "11º", "12º", "13º", "14º", "15º", "16º", "17º", "18º", "19º", "20º"]
        num_insp = st.selectbox("🔢 Número da Inspeção", num_inspecao_opts, index=3)

        inicio_opts = [f"{i}ª rua" for i in range(1, 31)]
        inicio_insp = st.selectbox("📍 Início da Inspeção", inicio_opts, index=0)

        direcao = st.radio("🧭 Direção do Caminhamento",
                           ["De Cima para Baixo", "De Baixo para Cima"],
                           horizontal=True)

    st.divider()

    if st.button("✅ Iniciar Inspeção", use_container_width=True, type="primary"):
        if not inspetor.strip():
            st.error("Informe o nome do inspetor.")
        else:
            inspecao_id = create_inspecao(
                cliente_id=cliente_id,
                quadra_id=quadra_id,
                numero_inspecao=num_insp,
                inspetor=inspetor,
                data_inspecao=str(data_insp),
                proxima_inspecao=str(prox_insp),
                inicio_inspecao=inicio_insp,
                direcao=direcao,
            )
            st.session_state.inspecao_id = inspecao_id
            st.session_state.planta_atual = 1
            st.session_state.total_plantas = quadra['total_plantas']
            st.success(f"Inspeção criada (ID: {inspecao_id}). Redirecionando para o Campo...")
            st.switch_page("pages/2_Campo.py")

# ── Tab: Cadastrar Propriedade/Quadra ─────────────────────────────────────────
with tab_cadastro:
    st.subheader("Cadastrar Nova Propriedade")
    with st.form("form_cliente"):
        fc1, fc2 = st.columns(2)
        with fc1:
            nova_prop = st.text_input("Nome da Propriedade", placeholder="ex: SÍTIO ALEGRIA")
            novo_prop_owner = st.text_input("Proprietário", placeholder="ex: JOÃO DA SILVA")
        with fc2:
            novo_mun = st.text_input("Município", placeholder="ex: CAMPESTRE")
            novo_est = st.selectbox("Estado", ["SP", "MG", "PR", "GO", "BA", "MT"])
        if st.form_submit_button("Cadastrar Propriedade", use_container_width=True):
            if nova_prop and novo_prop_owner and novo_mun:
                add_cliente(nova_prop, novo_prop_owner, novo_mun, novo_est)
                st.success(f"Propriedade '{nova_prop.upper()}' cadastrada!")
                st.rerun()
            else:
                st.error("Preencha todos os campos.")

    st.subheader("Cadastrar Nova Quadra")
    clientes_refresh = get_clientes()
    if clientes_refresh:
        with st.form("form_quadra"):
            props2 = {f"{c['propriedade']} — {c['proprietario']}": c['id'] for c in clientes_refresh}
            prop_quad = st.selectbox("Propriedade", list(props2.keys()))
            fq1, fq2, fq3 = st.columns(3)
            with fq1:
                num_quad = st.text_input("Número da Quadra", placeholder="ex: 14 ou 17A")
            with fq2:
                total_pl = st.number_input("Total de Plantas", min_value=1, max_value=5000, value=70)
            with fq3:
                variedades_lista = [
                    "P.RIO", "M.MURCOTE", "LIMA MARAVILHA", "VALÊNCIA", "P.IAC", "P.NATAL",
                    "P.MURCHA", "LIMA", "BAIANINHA", "CHARMUTE", "WESTIN", "NATAL",
                    "LIMÃO SICILIANO", "LIMÃO TAHITI", "LIMA VERDE", "MURCOTE",
                    "OUTRA"
                ]
                var_sel = st.selectbox("Variedade", variedades_lista)
                if var_sel == "OUTRA":
                    var_sel = st.text_input("Variedade personalizada")

            if st.form_submit_button("Cadastrar Quadra", use_container_width=True):
                if num_quad and var_sel:
                    add_quadra(props2[prop_quad], num_quad, total_pl, var_sel)
                    st.success(f"Quadra {num_quad} cadastrada!")
                    st.rerun()
                else:
                    st.error("Preencha número da quadra e variedade.")
