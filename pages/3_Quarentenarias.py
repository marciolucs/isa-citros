import streamlit as st
from database import (
    init_db, get_inspecao_by_id, get_fichas_by_inspecao,
    create_ficha_quarentenaria, save_rua_quarentenaria, get_ruas_by_ficha,
    delete_rua_quarentenaria, delete_ficha_quarentenaria
)
from calculations import consolidar_quarentenaria
from seed_data import seed

st.set_page_config(page_title="Quarentenárias — ISA", page_icon="🦠", layout="wide",
                   initial_sidebar_state="collapsed")
init_db()
seed()

st.markdown("""
<style>
div[data-testid="stButton"] > button { min-height:46px; font-size:14px; border-radius:8px; font-weight:600; }
.header-box { background:linear-gradient(135deg,#7B1FA2,#9C27B0); color:white;
              padding:0.8rem 1.5rem; border-radius:12px; margin-bottom:1rem; }
.header-box h2 { color:white; margin:0; }
.header-box p  { color:#E1BEE7; margin:0.2rem 0 0; font-size:0.82rem; }
.ficha-card { background:white; border:2px solid #E1BEE7; border-radius:10px;
              padding:1rem; margin-bottom:0.8rem; }
.ficha-title { font-weight:700; color:#6A1B9A; font-size:1rem; margin-bottom:0.5rem; }
.alerta-quaren { background:#FFEBEE; border:2px solid #C62828; border-radius:8px;
                 padding:0.8rem 1rem; color:#B71C1C; font-weight:700; }
.ok-quaren { background:#E8F5E9; border:2px solid #2D7D46; border-radius:8px;
             padding:0.8rem 1rem; color:#1B5E20; font-weight:700; }
.rua-row { background:#F3E5F5; border-radius:6px; padding:0.4rem 0.8rem; margin:0.2rem 0; font-size:0.88rem; }
</style>
""", unsafe_allow_html=True)

# ── Verificar sessão ───────────────────────────────────────────────────────────
if 'inspecao_id' not in st.session_state or st.session_state.inspecao_id is None:
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
    <h2>🦠 Fichas de Doenças Quarentenárias</h2>
    <p>{inspecao['propriedade']} — Q.{inspecao['numero_quadra']} | {inspecao['variedade']} | {inspecao['data_inspecao']}</p>
</div>
""", unsafe_allow_html=True)

col_nav1, col_nav2, col_nav3 = st.columns([2, 2, 2])
with col_nav1:
    if st.button("← Voltar ao Campo", use_container_width=True):
        st.switch_page("pages/2_Campo.py")
with col_nav2:
    if st.button("📊 Ver Relatório", use_container_width=True):
        st.switch_page("pages/4_Relatorio.py")
with col_nav3:
    if st.button("← Início", use_container_width=True):
        st.switch_page("app.py")

st.divider()

# ── Seleção da doença ─────────────────────────────────────────────────────────
doenca_sel = st.radio(
    "Selecione a doença quarentenária:",
    ["GREENING (HLB)", "CANCRO CÍTRICO"],
    horizontal=True
)
doenca_key = "GREENING" if "GREENING" in doenca_sel else "CANCRO"

emoji_doenca = "🟡" if doenca_key == "GREENING" else "🔴"
st.markdown(f"### {emoji_doenca} Fichas de {doenca_sel}")

# ── Fichas existentes ─────────────────────────────────────────────────────────
fichas = get_fichas_by_inspecao(inspecao_id, doenca=doenca_key)

if fichas:
    for ficha in fichas:
        ruas = get_ruas_by_ficha(ficha['id'])
        total_plantas_ficha = sum(r['total_plantas_rua'] for r in ruas)
        total_sintomas_ficha = sum(
            len([n for n in r['plantas_sintomas'].replace(';', ',').split(',') if n.strip().isdigit()])
            for r in ruas
        )

        with st.expander(
            f"📋 {ficha['numero_ficha']} — Inspetor: {ficha['inspetor']} | "
            f"{total_plantas_ficha} plantas | {total_sintomas_ficha} com sintoma",
            expanded=True
        ):
            # Tabela de ruas existentes
            if ruas:
                cols_header = st.columns([1, 1, 2, 5, 1])
                cols_header[0].markdown("**Rua**")
                cols_header[1].markdown("**Dir.**")
                cols_header[2].markdown("**Total Plantas**")
                cols_header[3].markdown("**Plantas com Sintoma**")
                cols_header[4].markdown("**Qtd**")

                for rua in ruas:
                    sintomas_str = rua['plantas_sintomas']
                    nums = [n.strip() for n in sintomas_str.replace(';', ',').split(',') if n.strip().isdigit()]
                    qtd = len(nums)
                    cols_r = st.columns([1, 1, 2, 5, 1])
                    cols_r[0].markdown(f"**{rua['numero_rua']}**")
                    cols_r[1].markdown(rua['direcao_rua'])
                    cols_r[2].markdown(str(rua['total_plantas_rua']))
                    cols_r[3].markdown(sintomas_str if sintomas_str else "—")
                    cols_r[4].markdown(f"**{qtd}**" if qtd > 0 else "—")

                st.divider()

            # Formulário para adicionar/editar rua
            st.markdown("**Adicionar / Atualizar Rua:**")
            with st.form(key=f"form_rua_{ficha['id']}"):
                col_r1, col_r2, col_r3 = st.columns([1, 2, 5])
                with col_r1:
                    prox_rua = (max(r['numero_rua'] for r in ruas) + 1) if ruas else 1
                    num_rua = st.number_input("Rua Nº", min_value=1, max_value=200,
                                              value=prox_rua, step=1)
                with col_r2:
                    dir_rua = st.radio("Direção", ["I (Ida)", "V (Volta)"],
                                       horizontal=True, key=f"dir_{ficha['id']}")
                    dir_code = "I" if "I" in dir_rua else "V"

                with col_r3:
                    total_pl_rua = st.number_input("Total de Plantas na Rua",
                                                    min_value=0, max_value=2000,
                                                    value=0, step=1, key=f"tot_{ficha['id']}")

                plantas_sint = st.text_input(
                    "Números das Plantas com Sintoma (separados por vírgula)",
                    placeholder="ex: 11, 12, 13, 45",
                    key=f"sint_{ficha['id']}"
                )

                if plantas_sint.strip():
                    nums_preview = [n.strip() for n in plantas_sint.replace(';', ',').split(',')
                                    if n.strip().isdigit()]
                    st.caption(f"✅ {len(nums_preview)} plantas com sintoma identificadas: {', '.join(nums_preview)}")

                col_btn_add, col_btn_del = st.columns(2)
                with col_btn_add:
                    btn_add_rua = st.form_submit_button(f"💾 Salvar Rua {num_rua}", use_container_width=True)
                with col_btn_del:
                    btn_del_rua = st.form_submit_button(f"🗑️ Excluir Rua {num_rua}", use_container_width=True)

                if btn_add_rua:
                    save_rua_quarentenaria(
                        ficha_id=ficha['id'],
                        numero_rua=num_rua,
                        direcao_rua=dir_code,
                        total_plantas=total_pl_rua,
                        plantas_sintomas=plantas_sint.strip()
                    )
                    st.success(f"Rua {num_rua} salva!")
                    st.rerun()

                if btn_del_rua:
                    delete_rua_quarentenaria(ficha['id'], num_rua)
                    st.warning(f"Rua {num_rua} removida.")
                    st.rerun()

            # Excluir ficha
            if st.button(f"🗑️ Excluir {ficha['numero_ficha']} completa", key=f"del_ficha_{ficha['id']}",
                         type="secondary"):
                delete_ficha_quarentenaria(ficha['id'])
                st.warning("Ficha removida.")
                st.rerun()

st.divider()

# ── Criar nova ficha ───────────────────────────────────────────────────────────
st.subheader("➕ Criar Nova Ficha")
with st.form("form_nova_ficha"):
    num_fichas_existentes = len(fichas)
    sugestao_num = f"FICHA {num_fichas_existentes + 1:02d}"

    col_nf1, col_nf2 = st.columns(2)
    with col_nf1:
        num_ficha_nova = st.text_input("Número da Ficha", value=sugestao_num)
    with col_nf2:
        inspetores = ["Luciano Costella", "Higor", "Hig/Luc", "Outro"]
        inspetor_ficha = st.selectbox("Inspetor", inspetores, key="ins_nova_ficha")
        if inspetor_ficha == "Outro":
            inspetor_ficha = st.text_input("Nome do inspetor", key="ins_outro_ficha")

    if st.form_submit_button("Criar Ficha", use_container_width=True, type="primary"):
        if num_ficha_nova.strip() and inspetor_ficha.strip():
            nova_ficha_id = create_ficha_quarentenaria(
                inspecao_id=inspecao_id,
                doenca=doenca_key,
                inspetor=inspetor_ficha,
                numero_ficha=num_ficha_nova.strip().upper()
            )
            st.success(f"{num_ficha_nova.upper()} criada! Agora adicione as ruas.")
            st.rerun()
        else:
            st.error("Informe o número da ficha e o inspetor.")

st.divider()

# ── Consolidação ──────────────────────────────────────────────────────────────
if fichas:
    st.subheader(f"📊 Consolidação — {doenca_sel}")
    cons = consolidar_quarentenaria(inspecao_id, doenca_key)

    if cons['total_vistoriadas'] > 0:
        col_c1, col_c2, col_c3 = st.columns(3)
        col_c1.metric("Total Vistoriado", f"{cons['total_vistoriadas']} plantas")
        col_c2.metric("Com Sintomas", f"{cons['total_sintomas']} plantas",
                      delta=None if cons['total_sintomas'] == 0 else f"⚠️ Notificar")
        col_c3.metric("% Incidência", f"{cons['percentual']:.3f}%")

        if cons['notificar']:
            st.markdown("""
            <div class="alerta-quaren">
                🚨 NOTIFICAÇÃO OBRIGATÓRIA — Plantas com sintomas identificadas!<br/>
                Comunicar imediatamente à Defesa Agropecuária estadual.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="ok-quaren">
                ✅ Nenhuma planta com sintoma registrada nesta doença.
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Adicione ruas às fichas para ver a consolidação.")
