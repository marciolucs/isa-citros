import streamlit as st
import pandas as pd
from datetime import datetime
from database import (
    init_db, get_inspecao_by_id, get_pragas,
    save_praga_plantas, save_planta_pragas, get_planta_pragas, get_inspecao_summary,
    save_observacoes_inspecao, get_observacoes_inspecao, get_observacoes_biblioteca,
    update_ultima_planta, finalize_inspecao,
    save_foto, get_fotos_by_planta, delete_foto, get_foto_data
)
from calculations import calcular_incidencia
from pdf_report import gerar_pdf_ficha_campo
from seed_data import seed
import ui

st.set_page_config(
    page_title="Ficha de Campo — ISA",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)
init_db()
seed()
ui.inject_theme()
ui.top_nav("campo")

# CSS específico da ficha (cabeçalho estilo Excel + cores das seções)
st.markdown("""
<style>
.fh-box { border: 2px solid #555; border-radius: 4px; background: #FFFDE7;
          margin-bottom: 0.6rem; overflow: hidden; }
.fh-box table { width: 100%; border-collapse: collapse; }
.fh-box td { padding: 4px 10px; font-size: 0.82rem; border: 1px solid #CCC; }
.fh-lbl { font-weight: 700; color: #1B5E20; }
.fh-val { color: #1a1a1a; }
.fh-red { color: #B71C1C; font-weight: 700; }
.fh-quote { font-style: italic; color: #6A1B9A; text-align: center; }
.fh-prox { text-align: right; }
.fh-prox-label { font-weight: 700; color: #1B5E20; font-size: 0.8rem; }
.fh-prox-val { color: #B71C1C; font-weight: 700; font-size: 1.05rem; }
.alerta-psil { background:#FFEBEE; border:2px solid #C62828; border-radius:8px;
               padding:0.6rem 1rem; margin:0.4rem 0; font-weight:700;
               color:#B71C1C; font-size:0.95rem; }
.secao-ferrugem { border-left-color:#C62828 !important; color:#B71C1C !important; }
.secao-leprose  { border-left-color:#E65100 !important; color:#BF360C !important; }
.secao-pragas   { border-left-color:#4527A0 !important; color:#311B92 !important; }
.secao-inimigos { border-left-color:#1B5E20 !important; color:#1B5E20 !important; }
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

# Mensagem vinda do Painel (criou/continuou inspeção)
_flash = st.session_state.pop('flash_campo', None)
if _flash:
    st.success(f"✅ {_flash}")

total_plantas = inspecao['total_plantas']
pragas        = get_pragas()
summary       = get_inspecao_summary(inspecao_id)

# Mapa nome → praga
pragas_map = {p['nome']: p for p in pragas}

# ── Datas e dia da semana ──────────────────────────────────────────────────────
DIAS = ['SEGUNDA-FEIRA', 'TERÇA-FEIRA', 'QUARTA-FEIRA',
        'QUINTA-FEIRA', 'SEXTA-FEIRA', 'SÁBADO', 'DOMINGO']

def fmt_data(s):
    if not s:
        return '—', ''
    try:
        dt = datetime.strptime(s, '%Y-%m-%d')
        return f"{dt.day}/{dt.month}/{dt.year}", DIAS[dt.weekday()]
    except Exception:
        return s, ''

data_fmt, dia_sem   = fmt_data(inspecao['data_inspecao'])
prox_fmt, prox_dia  = fmt_data(inspecao.get('proxima_inspecao', ''))

# Nº de plantas inspecionadas
all_plants_reg = set()
for d in summary.values():
    all_plants_reg |= d['plantas']
n_inspecionadas = max(all_plants_reg) if all_plants_reg else 0
total_insp = n_inspecionadas if n_inspecionadas > 0 else total_plantas

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
        <span class="fh-red"> {data_fmt} — {dia_sem}</span></td>
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

# ══════════════════════════════════════════════════════════════════════════════
# ── Grade de inspeção — estrutura igual ao ISAeGUI.xlsm aba "Citros" ─────────
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="secao-titulo">📋 Plantas Inspecionadas — marque ✅ as plantas com presença</div>',
    unsafe_allow_html=True
)

# Definição das seções na mesma ordem do Excel
SECOES_GRID = [
    {
        "nome": "🔴 ÁCARO FERRUGEM",
        "css_class": "secao-ferrugem",
        "info": "Fruto/Folha — marque as plantas com ferrugem. Limiar: <b>&lt;10 ácaros = 10%</b> | <b>≥10 ácaros = 5%</b>",
        "pragas": [
            "Ácaro Ferrugem (< 10 ácaros)",
            "Ácaro Ferrugem (10 ou + ácaros)",
        ],
    },
    {
        "nome": "🟠 ÁCARO LEPROSE",
        "css_class": "secao-leprose",
        "info": "Fruto/Ramo — vetor da Leprose Cítrica. Limiar: <b>1%</b>. Qualquer presença exige ação.",
        "pragas": [
            "Ácaro Leprose",
        ],
    },
    {
        "nome": "🐛 PRAGAS DIVERSAS",
        "css_class": "secao-pragas",
        "info": "Marque ✅ as plantas com presença. Veja limiar % em cada linha.",
        "pragas": [
            "Ácaro Branco",
            "Mosca das Frutas",
            "Bicho Furão",
            "Ácaro Purpúreo",
            "Ácaro Mexicano",
            "Ácaro Texano",
            "Pulgão Verde",
            "Pulgão Preto",
            "Lagarta",
            "Minadora das Folhas",
            "Tripes",
            "Psilídeo",
        ],
    },
    {
        "nome": "🌿 INIMIGOS NATURAIS",
        "css_class": "secao-inimigos",
        "info": "Registrar presença de inimigos naturais — indicam equilíbrio biológico no talhão.",
        "pragas": [
            "Inimigos Naturais",
        ],
    },
]

# Helper: monta DataFrame para uma seção
def _build_secao_df(secao_pragas, pragas_map, summary, total_plantas, total_insp):
    rows = []
    ids  = []
    for pnome in secao_pragas:
        praga = pragas_map.get(pnome)
        if not praga:
            continue
        pid = praga['id']
        plants_pest = summary.get(pid, {}).get('plantas', set())
        inc = calcular_incidencia(len(plants_pest), total_insp)
        lim = praga['limiar_acao'] * 100
        row = {
            'Praga / Doença': praga['nome'],
            'Parte':          praga.get('parte_avaliada', '') or '—',
            '%':              round(inc, 2),
            'Limiar %':       round(lim, 0),
        }
        for p in range(1, total_plantas + 1):
            row[f'p{p}'] = p in plants_pest
        rows.append(row)
        ids.append(pid)
    return pd.DataFrame(rows), ids


def _build_cc(total_plantas):
    cc = {
        'Praga / Doença': st.column_config.TextColumn('Praga / Doença', disabled=True, width='medium'),
        'Parte':          st.column_config.TextColumn('Parte',           disabled=True, width='small'),
        '%':              st.column_config.NumberColumn('%',             disabled=True, width='small', format='%.2f'),
        'Limiar %':       st.column_config.NumberColumn('Limiar %',      disabled=True, width='small', format='%.0f'),
    }
    for p in range(1, total_plantas + 1):
        cc[f'p{p}'] = st.column_config.CheckboxColumn(str(p), width='small')
    return cc


# ── Modo de preenchimento ─────────────────────────────────────────────────────
modo = st.radio(
    "Modo de preenchimento",
    ["📱 Modo Planta", "📊 Modo Grade"],
    horizontal=True,
    key="modo_campo",
    help="Modo Planta: uma planta por vez, ideal no celular. "
         "Modo Grade: matriz completa, ideal no computador. "
         "Os dois editam os mesmos dados.",
)

# Contador global de pragas acima do limiar
acima_count = sum(
    1 for praga in pragas
    if calcular_incidencia(
        len(summary.get(praga['id'], {}).get('plantas', set())), total_insp
    ) >= praga['limiar_acao'] * 100 > 0
)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# MODO GRADE — matriz pragas × plantas (fiel ao Excel)
# ══════════════════════════════════════════════════════════════════════════════
if modo == "📊 Modo Grade":
    cc = _build_cc(total_plantas)
    all_edited_sections = {}   # secao_nome → (edited_df, [praga_ids])

    for sec in SECOES_GRID:
        sname = sec['nome']
        st.markdown(
            f'<div class="secao-titulo {sec["css_class"]}">{sname}</div>',
            unsafe_allow_html=True
        )
        if sec.get('info'):
            st.markdown(f'<div class="info-box">ℹ️ {sec["info"]}</div>', unsafe_allow_html=True)

        df_sec, ids_sec = _build_secao_df(
            sec['pragas'], pragas_map, summary, total_plantas, total_insp
        )
        if df_sec.empty:
            st.caption("_(sem pragas desta seção na base de dados)_")
            continue

        acima_nomes = [row['Praga / Doença'] for _, row in df_sec.iterrows()
                       if row['Limiar %'] > 0 and row['%'] >= row['Limiar %']]
        if acima_nomes:
            st.warning(f"⚠️ Acima do limiar: {', '.join(acima_nomes)}")

        safe_key = (sname
                    .replace(' ', '_').replace('/', '_')
                    .replace('á', 'a').replace('â', 'a').replace('ã', 'a').replace('à', 'a')
                    .replace('é', 'e').replace('ê', 'e').replace('í', 'i')
                    .replace('ó', 'o').replace('ô', 'o').replace('õ', 'o')
                    .replace('ú', 'u').replace('ç', 'c')
                    .replace('🔴', '').replace('🟠', '').replace('🐛', '').replace('🌿', '')
                    .strip('_'))

        edited_df = st.data_editor(
            df_sec,
            column_config=cc,
            hide_index=True,
            use_container_width=True,
            num_rows='fixed',
            key=f'grid_{safe_key}',
        )
        all_edited_sections[sname] = (edited_df, ids_sec)

    col_sv, col_info = st.columns([2, 5])
    with col_sv:
        if st.button("💾 Salvar Ficha de Campo", type="primary", use_container_width=True):
            for sname, (edited_df, ids_sec) in all_edited_sections.items():
                for i, row in edited_df.iterrows():
                    praga_id = ids_sec[i]
                    marcadas = [p for p in range(1, total_plantas + 1)
                                if row.get(f'p{p}', False)]
                    save_praga_plantas(inspecao_id, praga_id, marcadas)
                    if marcadas:
                        update_ultima_planta(inspecao_id, max(marcadas))
            st.success("✅ Ficha de campo salva!")
            st.rerun()
    with col_info:
        st.info(f"💡 Marque ✅ nas plantas com presença e clique **Salvar**. "
                f"Pragas acima do limiar: **{acima_count}**")

# ══════════════════════════════════════════════════════════════════════════════
# MODO PLANTA — uma planta por vez (rápido no celular)
# ══════════════════════════════════════════════════════════════════════════════
else:
    # Aplica avanço programático ANTES de instanciar o widget number_input
    if 'planta_goto' in st.session_state:
        st.session_state['num_planta_campo'] = st.session_state.pop('planta_goto')

    col_p1, col_p2 = st.columns([1, 2])
    with col_p1:
        planta_sel = st.number_input(
            "🌳 Planta atual", min_value=1, max_value=total_plantas,
            step=1, key='num_planta_campo')
    with col_p2:
        registradas = sorted(all_plants_reg)
        st.markdown(
            f'<div class="info-box">Plantas com registro: '
            f'<b>{len(registradas)}</b> de {total_plantas} &nbsp;·&nbsp; '
            f'Última: <b>{max(registradas) if registradas else 0}</b></div>',
            unsafe_allow_html=True)

    pragas_da_planta = set(get_planta_pragas(inspecao_id, planta_sel))
    selected = []

    for sec in SECOES_GRID:
        st.markdown(
            f'<div class="secao-titulo {sec["css_class"]}">{sec["nome"]}</div>',
            unsafe_allow_html=True)
        pragas_sec = [pragas_map[n] for n in sec['pragas'] if n in pragas_map]
        cols = st.columns(2)
        for idx, praga in enumerate(pragas_sec):
            pid = praga['id']
            lim = praga['limiar_acao'] * 100
            label = praga['nome']
            if lim > 0:
                label += f"  ·  limiar {lim:.0f}%"
            with cols[idx % 2]:
                if st.checkbox(label, value=pid in pragas_da_planta,
                               key=f"chk_{planta_sel}_{pid}"):
                    selected.append(pid)

    st.divider()
    cpa, cpb, cpc = st.columns(3)
    with cpa:
        if st.button("💾 Salvar planta", use_container_width=True):
            save_planta_pragas(inspecao_id, planta_sel, selected)
            update_ultima_planta(inspecao_id, planta_sel)
            st.success(f"Planta {planta_sel} salva!")
            st.rerun()
    with cpb:
        if st.button("✅ Salvar e próxima →", type="primary", use_container_width=True):
            save_planta_pragas(inspecao_id, planta_sel, selected)
            update_ultima_planta(inspecao_id, planta_sel)
            if planta_sel < total_plantas:
                st.session_state['planta_goto'] = planta_sel + 1
            st.rerun()
    with cpc:
        st.markdown(
            f'<div class="info-box">Pragas acima do limiar (total): '
            f'<b>{acima_count}</b></div>', unsafe_allow_html=True)

st.divider()

# ── Exportar PDF da Ficha de Campo (disponível nos dois modos) ────────────────
# Recarrega o resumo do banco para saber se há plantas salvas
_summary_atual = get_inspecao_summary(inspecao_id)
_tem_dados = any(len(d['plantas']) > 0 for d in _summary_atual.values())
if not _tem_dados:
    st.info("ℹ️ Nenhuma planta salva ainda nesta inspeção. Marque as plantas acima e "
            "clique em **💾 Salvar** antes de gerar o PDF, senão ele sai em branco.")

col_pdf1, col_pdf2 = st.columns([2, 3])
with col_pdf1:
    if st.button("📄 Gerar PDF da Ficha de Campo", use_container_width=True):
        st.session_state['pdf_campo_bytes'] = gerar_pdf_ficha_campo(inspecao)
    if 'pdf_campo_bytes' in st.session_state:
        nome_pdf = (f"Ficha_Campo_{inspecao['propriedade'].replace(' ', '_')}"
                    f"_Q{inspecao['numero_quadra']}"
                    f"_{inspecao['data_inspecao'].replace('-', '')}.pdf")
        st.download_button(
            "⬇️ Baixar PDF da Ficha de Campo",
            data=st.session_state['pdf_campo_bytes'],
            file_name=nome_pdf, mime="application/pdf",
            use_container_width=True)
with col_pdf2:
    st.caption("O PDF replica a grade da planilha Excel (paisagem, plantas em "
               "blocos de 35, com % e limiar). Salve antes de gerar para refletir os dados atuais.")

st.divider()

# ── ÍNDICE DE AVALIAÇÃO (legenda lateral) ─────────────────────────────────────
with st.expander("📊 Índice de Avaliação — Escala de Referência", expanded=False):
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
**🔴 ÁCARO FERRUGEM** — *Fruto / Folha*

| Condição | Limiar |
|---|---|
| < 10 ácaros/cm² | **10% das plantas** |
| ≥ 10 ácaros/cm² | **5% das plantas** |

**Época crítica:** florada, formação de frutos novos e da safra.
Priorizar aplicação preventiva em início de safra.
""")
        st.markdown("""
**🟠 ÁCARO LEPROSE** — *Fruto / Ramo*

| Estágio | Limiar |
|---|---|
| Ovos / Ninfas / Adultos | **1% das plantas** |

⚠️ Vetor da Leprose Cítrica. Qualquer presença acima de 1% exige
ação imediata. Eliminar plantas com lesões avançadas.
""")
    with col_b:
        st.markdown("""
**🐛 PRAGAS DIVERSAS — Limiares**

| Praga | Parte | Limiar |
|---|---|---|
| Ácaro Branco | Frutos/Folhas novas | 5% |
| Mosca das Frutas | Frutos | 5% |
| Bicho Furão | Frutos | 5% |
| Ácaro Purpúreo | Frutos/Folhas | 10% |
| Ácaro Mexicano | Folhas | 10% |
| Ácaro Texano | Frutos/Folhas | 10% |
| Pulgão Verde | Veg. Novas | 10% |
| Pulgão Preto | Veg. Novas | 10% |
| Lagarta | Folhas/Frutos novos | 5% |
| Minadora | Veg. Novas | 10% |
| Tripes | Flores/Frutos novos | 10% |
| **Psilídeo** | **Veg. Novas** | **🚨 1%** |
""")

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

# Grupos especiais para o Índice de Avaliação
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

# Uma observação pode casar em mais de um grupo (ex.: "PRESENÇA DE ÁCAROS DA
# LEPROSE" bate em FERRUGEM por 'ácaro' e em LEPROSE por 'leprose'). Cada obs
# deve aparecer só uma vez para não gerar key de widget duplicada.
_obs_shown = set()
for grupo_nome, items in INDICE_GROUPS.items():
    items = [o for o in items if o['id'] not in _obs_shown]
    if not items:
        continue
    _obs_shown.update(o['id'] for o in items)
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
