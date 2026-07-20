import streamlit as st
import pandas as pd
from database import init_db, get_clientes, get_cliente_by_id
from calculations import consolidar_propriedade
from pdf_report import gerar_pdf_consolidado
from seed_data import seed
import ui

st.set_page_config(page_title="Consolidado — ISA", page_icon="🗂️", layout="wide",
                   initial_sidebar_state="collapsed")
init_db()
seed()
ui.inject_theme()
ui.top_nav("consolidado")

# CSS específico: bloco do técnico/propriedade
st.markdown("""
<style>
.tecnico-box { background:#F1F8E9; border:1px solid #C5E1A5; border-radius:10px;
               padding:0.7rem 1.2rem; margin-bottom:0.8rem; }
.tecnico-box table { width:100%; border-collapse:collapse; }
.tecnico-box td { padding:3px 10px; font-size:0.85rem; }
.tecnico-box .lbl { font-weight:700; color:#1B5E20; width:120px; }
</style>
""", unsafe_allow_html=True)

ui.page_header("🗂️", "Relatório Consolidado por Propriedade",
               "Todas as quadras numa tabela só — o % de cada praga por quadra (espelho da aba CONTROLE)")

st.divider()

# ── Seleção da propriedade ────────────────────────────────────────────────────
clientes = get_clientes()
if not clientes:
    st.info("Nenhuma propriedade cadastrada ainda.")
    st.stop()

props = {f"{c['propriedade']} — {c['proprietario']} ({c['municipio']}-{c['estado']})": c['id']
         for c in clientes}

# Pré-seleção pela inspeção ativa (se houver)
default_idx = 0
if 'consolidado_cliente_id' in st.session_state:
    ids = list(props.values())
    if st.session_state.consolidado_cliente_id in ids:
        default_idx = ids.index(st.session_state.consolidado_cliente_id)

prop_sel = st.selectbox("🏡 Propriedade / Produtor", list(props.keys()), index=default_idx)
cliente_id = props[prop_sel]
st.session_state.consolidado_cliente_id = cliente_id
cliente = get_cliente_by_id(cliente_id)

# Limpa PDF em cache ao trocar de propriedade
if st.session_state.get('_pdf_consolidado_cid') != cliente_id:
    st.session_state.pop('pdf_consolidado', None)
    st.session_state['_pdf_consolidado_cid'] = cliente_id

# ── Bloco técnico + propriedade (espelho do cabeçalho da aba CONTROLE) ─────────
st.markdown(f"""
<div class="tecnico-box">
<table>
  <tr>
    <td class="lbl">Técnico:</td><td>Luciano Costella — CFTA 17893896825</td>
    <td class="lbl">Produtor:</td><td>{cliente['proprietario']}</td>
  </tr>
  <tr>
    <td class="lbl">Contato:</td><td>(19) 99278-2525</td>
    <td class="lbl">Propriedade:</td><td>{cliente['propriedade']}</td>
  </tr>
  <tr>
    <td class="lbl">E-mail:</td><td>lucianocostella@yahoo.com.br</td>
    <td class="lbl">Talhão:</td><td>{cliente['municipio']}-{cliente['estado']}</td>
  </tr>
</table>
</div>
""", unsafe_allow_html=True)

# ── Consolidar ────────────────────────────────────────────────────────────────
linhas = consolidar_propriedade(cliente_id)

if not linhas:
    st.warning("Esta propriedade ainda não tem inspeções registradas. "
               "Crie uma inspeção no **Painel** e preencha a **Ficha de Campo**.")
    st.stop()

# ── Métricas ──────────────────────────────────────────────────────────────────
n_quadras     = len(linhas)
n_com_alerta  = sum(1 for l in linhas if l['tem_alerta'])
total_plantas = sum(l['total_inspecionado'] for l in linhas)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="m-card"><div class="m-val">{n_quadras}</div>'
                f'<div class="m-lab">Quadras Inspecionadas</div></div>', unsafe_allow_html=True)
with c2:
    cor = "#C62828" if n_com_alerta > 0 else "#2E7D32"
    st.markdown(f'<div class="m-card"><div class="m-val" style="color:{cor}">{n_com_alerta}</div>'
                f'<div class="m-lab">Quadras c/ Praga Acima do Limiar</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="m-card"><div class="m-val">{total_plantas}</div>'
                f'<div class="m-lab">Total de Plantas Inspecionadas</div></div>', unsafe_allow_html=True)

st.divider()

# ── Tabela consolidada (com formatação vermelha acima do limiar) ──────────────
st.markdown('<div class="secao-titulo">📋 Consolidado por Quadra</div>', unsafe_allow_html=True)

col_defs = linhas[0]['cols']
pest_labels = [c['rotulo'] for c in col_defs]

# DataFrame: valores numéricos
rows = []
for l in linhas:
    row = {'Quadra': str(l['quadra']), 'Variedade': l['variedade'], 'Data': l['data']}
    for c in l['cols']:
        row[c['rotulo']] = c['valor']
    rows.append(row)
df = pd.DataFrame(rows)

# Matriz booleana "acima do limiar" para colorir
acima = {}
for i, l in enumerate(linhas):
    for c in l['cols']:
        acima[(i, c['rotulo'])] = c['acima']

def _color_cells(_df):
    styles = pd.DataFrame('', index=_df.index, columns=_df.columns)
    for i in _df.index:
        for col in pest_labels:
            if acima.get((i, col), False):
                styles.loc[i, col] = 'background-color:#FFCDD2; color:#B71C1C; font-weight:bold'
            else:
                styles.loc[i, col] = 'color:#333'
    return styles

fmt = {col: '{:.1f}%' for col in pest_labels}
styled = df.style.apply(_color_cells, axis=None).format(fmt)
st.dataframe(styled, use_container_width=True, hide_index=True)

st.caption("Valores em % de plantas com presença. Vermelho = acima do limiar de ação. "
           "Colunas com mais de uma praga (Ác. P/M/T, Pulgão) usam a união das plantas afetadas. "
           "Limiares: Ferrugem <10 = 10% · Ferrugem ≥10 / Branco / Mosca / Furão / Lagarta = 5% · "
           "Ác. P/M/T / Pulgão / Minadora / Tripes = 10% · Leprose / Psilídeo = 1%.")

st.divider()

# ── Exportar PDF ──────────────────────────────────────────────────────────────
col_pdf1, col_pdf2 = st.columns([2, 3])
with col_pdf1:
    if st.button("📄 Gerar PDF Consolidado", type="primary", use_container_width=True):
        st.session_state['pdf_consolidado'] = gerar_pdf_consolidado(cliente, linhas)
    if 'pdf_consolidado' in st.session_state:
        nome = f"Consolidado_{cliente['propriedade'].replace(' ', '_')}.pdf"
        st.download_button("⬇️ Baixar PDF Consolidado",
                           data=st.session_state['pdf_consolidado'],
                           file_name=nome, mime="application/pdf",
                           use_container_width=True)
with col_pdf2:
    st.caption("O PDF sai em paisagem, no formato da aba CONTROLE do Excel — "
               "uma linha por quadra, com destaque vermelho para pragas acima do limiar.")
