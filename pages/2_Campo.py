import streamlit as st
from database import (
    init_db, get_inspecao_by_id, get_pragas,
    save_planta_pragas, get_planta_pragas, get_plantas_inspecionadas,
    finalize_inspecao, get_inspecao_summary,
    save_observacoes_inspecao, get_observacoes_inspecao, get_observacoes_biblioteca,
    update_ultima_planta, save_foto, get_fotos_by_planta, delete_foto, get_foto_data
)
from calculations import calcular_incidencia
from seed_data import seed

st.set_page_config(page_title="Campo — ISA", page_icon="🔍", layout="wide",
                   initial_sidebar_state="collapsed")
init_db()
seed()

st.markdown("""
<style>
div[data-testid="stButton"] > button { min-height:50px; font-size:15px; border-radius:8px; font-weight:600; }
div[data-testid="stCheckbox"] label p { font-size:15px !important; }
div[data-testid="stCheckbox"] { padding: 4px 0; }
.planta-header {
    background:linear-gradient(135deg,#1A5C2A,#2D7D46);
    color:white; padding:1rem 1.5rem; border-radius:12px; margin-bottom:1rem;
    text-align:center;
}
.planta-header h2 { color:white; margin:0; font-size:1.8rem; }
.planta-header p  { color:#C8E6C9; margin:0.2rem 0 0; }
.grupo-pragas {
    background:white; border:2px solid #E8F5E9; border-radius:10px;
    padding:0.8rem 1rem; margin-bottom:0.8rem;
}
.grupo-titulo { font-weight:700; color:#1A5C2A; font-size:0.95rem; margin-bottom:0.5rem; }
.alerta-psil {
    background:#FFEBEE; border:2px solid #C62828; border-radius:8px;
    padding:0.6rem 1rem; margin:0.5rem 0;
    font-weight:700; color:#B71C1C; font-size:0.95rem;
}
.stats-box {
    background:#F1F8E9; border-left:4px solid #7CB342; border-radius:0 8px 8px 0;
    padding:0.6rem 1rem; margin:0.4rem 0; font-size:0.85rem;
}
.acima-limiar { color:#C62828; font-weight:700; }
.ok-limiar { color:#2E7D32; }
.header-box { background:linear-gradient(135deg,#1A5C2A,#2D7D46); color:white;
              padding:0.8rem 1.5rem; border-radius:12px; margin-bottom:1rem; }
.header-box h2 { color:white; margin:0; font-size:1.2rem; }
.header-box p  { color:#C8E6C9; margin:0.2rem 0 0; font-size:0.82rem; }
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

total_plantas = inspecao['total_plantas']
if 'planta_atual' not in st.session_state:
    st.session_state.planta_atual = 1

planta_atual = st.session_state.planta_atual
pragas = get_pragas()
pragas_por_cat = {}
for p in pragas:
    cat = p['categoria']
    pragas_por_cat.setdefault(cat, []).append(p)

CAT_LABELS = {
    'acaro': ('🕷️', 'Ácaros'),
    'inseto': ('🦟', 'Insetos'),
    'benefico': ('🐞', 'Benéficos / Inimigos Naturais'),
}

# ── Cabeçalho da inspeção ──────────────────────────────────────────────────────
st.markdown(f"""
<div class="header-box">
    <h2>🔍 Ficha de Campo — {inspecao['propriedade']}</h2>
    <p>Q.{inspecao['numero_quadra']} | {inspecao['variedade']} | {inspecao['total_plantas']} plantas |
       Inspetor: {inspecao['inspetor']} | {inspecao['data_inspecao']}</p>
</div>
""", unsafe_allow_html=True)

col_nav_top, col_home = st.columns([6, 1])
with col_home:
    if st.button("← Início", use_container_width=True):
        st.switch_page("app.py")

# ── Progresso ─────────────────────────────────────────────────────────────────
max_p, _ = get_plantas_inspecionadas(inspecao_id)
progresso = min(planta_atual / total_plantas, 1.0)
st.progress(progresso, text=f"Planta {planta_atual} de {total_plantas} ({progresso*100:.0f}%)")

# ── Card da planta atual ───────────────────────────────────────────────────────
st.markdown(f"""
<div class="planta-header">
    <h2>🌿 PLANTA {planta_atual}</h2>
    <p>Marque as pragas presentes nesta planta</p>
</div>
""", unsafe_allow_html=True)

# Carregar seleções já salvas para esta planta
pragas_salvas = get_planta_pragas(inspecao_id, planta_atual)
selecoes = {}

# ── Formulário de pragas ───────────────────────────────────────────────────────
with st.form(key=f"form_planta_{planta_atual}", clear_on_submit=False):
    for cat, (emoji, label) in CAT_LABELS.items():
        grupo = pragas_por_cat.get(cat, [])
        if not grupo:
            continue

        st.markdown(f'<div class="grupo-pragas"><div class="grupo-titulo">{emoji} {label}</div>', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, praga in enumerate(grupo):
            with cols[i % 2]:
                ja_marcado = praga['id'] in pragas_salvas
                alerta_str = " ⚠️" if praga['alerta_critico'] else ""
                selecoes[praga['id']] = st.checkbox(
                    f"{praga['nome']}{alerta_str}",
                    value=ja_marcado,
                    key=f"praga_{praga['id']}_p{planta_atual}"
                )
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    col_ant, col_limpa, col_avan = st.columns([2, 2, 3])
    with col_ant:
        btn_anterior = st.form_submit_button(
            "← Anterior", use_container_width=True,
            disabled=(planta_atual <= 1)
        )
    with col_limpa:
        btn_limpar = st.form_submit_button("🗑️ Limpar", use_container_width=True)
    with col_avan:
        if planta_atual < total_plantas:
            btn_avancar = st.form_submit_button(
                f"Avançar → Planta {planta_atual + 1}", use_container_width=True,
                type="primary"
            )
        else:
            btn_avancar = st.form_submit_button(
                "✅ Finalizar Inspeção de Pragas", use_container_width=True,
                type="primary"
            )

    # Processar ações
    if btn_limpar:
        save_planta_pragas(inspecao_id, planta_atual, [])
        st.rerun()

    pragas_selecionadas = [pid for pid, marcado in selecoes.items() if marcado]

    if btn_anterior and planta_atual > 1:
        save_planta_pragas(inspecao_id, planta_atual, pragas_selecionadas)
        update_ultima_planta(inspecao_id, planta_atual)
        st.session_state.planta_atual = planta_atual - 1
        st.rerun()

    if btn_avancar:
        save_planta_pragas(inspecao_id, planta_atual, pragas_selecionadas)
        update_ultima_planta(inspecao_id, planta_atual)

        if not pragas_selecionadas:
            st.session_state['sem_praga_planta'] = planta_atual
        else:
            st.session_state.pop('sem_praga_planta', None)

        if planta_atual < total_plantas:
            st.session_state.planta_atual = planta_atual + 1
            st.rerun()
        else:
            st.session_state['mostrar_finalizacao'] = True
            st.rerun()

# ── Confirmação "sem praga" ────────────────────────────────────────────────────
if st.session_state.get('sem_praga_planta') == planta_atual - 1:
    st.success(f"✓ Planta {planta_atual - 1} — Nenhuma praga registrada.")

# ── Alerta de Psilídeo (calculado da base a cada render) ──────────────────────
summary_atual = get_inspecao_summary(inspecao_id)
psil_ids = {p['id'] for p in pragas if 'psilídeo' in p['nome'].lower() or 'psil' in p['nome'].lower()}
psil_detectado = any(pid in summary_atual for pid in psil_ids if
                     pid in summary_atual and len(summary_atual[pid]['plantas']) > 0)
if psil_detectado:
    st.markdown("""
    <div class="alerta-psil">
        🚨 ALERTA CRÍTICO — PSILÍDEO DETECTADO!<br/>
        Vetor do Greening (HLB). Aplicar inseticida imediatamente e notificar fiscalização.
    </div>
    """, unsafe_allow_html=True)

# ── Upload de fotos da planta atual ───────────────────────────────────────────
with st.expander(f"📷 Fotos — Planta {planta_atual}", expanded=False):
    fotos_existentes = get_fotos_by_planta(inspecao_id, planta_atual)

    if fotos_existentes:
        cols_foto = st.columns(min(len(fotos_existentes), 4))
        for idx, foto_meta in enumerate(fotos_existentes):
            with cols_foto[idx % 4]:
                foto_row = get_foto_data(foto_meta['id'])
                if foto_row:
                    st.image(foto_row['foto_data'], caption=f"Planta {planta_atual}", use_container_width=True)
                    if st.button("🗑️", key=f"del_foto_{foto_meta['id']}", help="Excluir foto"):
                        delete_foto(foto_meta['id'])
                        st.rerun()

    uploaded = st.file_uploader(
        "Adicionar foto",
        type=["jpg", "jpeg", "png"],
        key=f"upload_foto_p{planta_atual}",
        label_visibility="collapsed"
    )
    if uploaded is not None:
        foto_bytes = uploaded.read()
        save_foto(inspecao_id, planta_atual, foto_bytes, uploaded.name)
        st.success("Foto salva!")
        st.rerun()

# ── Painel de estatísticas em tempo real ──────────────────────────────────────
with st.expander("📊 Estatísticas em Tempo Real", expanded=True):
    max_p_atual, _ = get_plantas_inspecionadas(inspecao_id)
    total_insp_ate_agora = max_p_atual
    if total_insp_ate_agora > 0:
        summary = get_inspecao_summary(inspecao_id)
        if summary:
            for pid, data in sorted(summary.items(), key=lambda x: -len(x[1]['plantas'])):
                count = len(data['plantas'])
                inc = calcular_incidencia(count, total_insp_ate_agora)
                lim = data['limiar_acao'] * 100
                css_class = "acima-limiar" if (inc >= lim and lim > 0) else "ok-limiar"
                st.markdown(
                    f'<div class="stats-box"><span class="{css_class}">'
                    f'{data["nome"]}: {count} plantas ({inc:.1f}%) — Limiar: {lim:.0f}%'
                    f'</span></div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("Nenhuma praga registrada ainda.")
    else:
        st.info("Aguardando primeiras plantas inspecionadas.")

# ── Navegação rápida entre plantas ────────────────────────────────────────────
with st.expander("🔢 Ir para Planta Específica", expanded=False):
    planta_nav = st.number_input("Número da planta", min_value=1, max_value=total_plantas,
                                  value=planta_atual, step=1, key="nav_planta")
    if st.button("Ir", key="btn_nav"):
        st.session_state.planta_atual = planta_nav
        st.rerun()

# ── Tela de finalização ────────────────────────────────────────────────────────
if st.session_state.get('mostrar_finalizacao'):
    st.divider()
    st.success(f"✅ Todas as {total_plantas} plantas registradas!")

    st.subheader("📝 Observações Gerais")
    obs_biblioteca = get_observacoes_biblioteca()
    obs_categorias = {}
    for obs in obs_biblioteca:
        obs_categorias.setdefault(obs['categoria'], []).append(obs)

    obs_salvas = get_observacoes_inspecao(inspecao_id)
    obs_selecionadas = list(obs_salvas)

    cat_labels_obs = {
        'praga': '🦟 Pragas',
        'doenca': '🦠 Doenças',
        'dano_abiotico': '🌡️ Danos Abióticos',
        'fisiologico': '🌱 Fisiológico',
        'nutricional': '🧪 Nutricional',
        'planta_daninha': '🌿 Plantas Daninhas',
        'operacional': '📋 Operacional',
        'geral': '📌 Geral',
    }

    for cat, items in obs_categorias.items():
        label = cat_labels_obs.get(cat, cat)
        with st.expander(label, expanded=False):
            for obs in items:
                if st.checkbox(obs['descricao'], key=f"obs_{obs['id']}",
                               value=obs['descricao'] in obs_salvas):
                    if obs['descricao'] not in obs_selecionadas:
                        obs_selecionadas.append(obs['descricao'])
                else:
                    if obs['descricao'] in obs_selecionadas:
                        obs_selecionadas.remove(obs['descricao'])

    obs_livre = st.text_area("Observação livre (opcional)", height=80)
    if obs_livre.strip():
        obs_selecionadas.append(obs_livre.strip())

    col_salvar, col_quaren, col_rel = st.columns(3)
    with col_salvar:
        if st.button("💾 Salvar Observações", use_container_width=True):
            save_observacoes_inspecao(inspecao_id, obs_selecionadas)
            st.success("Observações salvas!")

    with col_quaren:
        if st.button("🦠 Lançar Quarentenárias", use_container_width=True):
            save_observacoes_inspecao(inspecao_id, obs_selecionadas)
            st.switch_page("pages/3_Quarentenarias.py")

    with col_rel:
        if st.button("📊 Ver Relatório", use_container_width=True, type="primary"):
            save_observacoes_inspecao(inspecao_id, obs_selecionadas)
            finalize_inspecao(inspecao_id)
            st.session_state['mostrar_finalizacao'] = False
            st.switch_page("pages/4_Relatorio.py")
