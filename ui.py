"""Tema visual único e navegação padronizada do sistema ISA.

Ponto único de design: mudar cores/estilo aqui reflete em todas as páginas.
Identidade "Verde Citros": verde + laranja 🍊, cards limpos, botões grandes,
pensado para uso no celular em campo.
"""
import streamlit as st

# ── Paleta ────────────────────────────────────────────────────────────────────
VERDE_ESCURO = "#1B5E20"
VERDE        = "#2E7D32"
VERDE_CLARO  = "#E8F5E9"
VERDE_TINT   = "#F1F8E9"
LARANJA      = "#F57C00"
LARANJA_CLR  = "#FB8C00"
VERMELHO     = "#C62828"
VERMELHO_BG  = "#FFEBEE"
AMARELO_BG   = "#FFF9C4"
TEXTO        = "#1a1a1a"

# ── Itens do menu (label, ícone, caminho, chave) ──────────────────────────────
NAV_ITENS = [
    ("Início",        "🏠", "app.py",                    "inicio"),
    ("Painel",        "⚙️", "pages/1_Painel.py",         "painel"),
    ("Campo",         "🔍", "pages/2_Campo.py",          "campo"),
    ("Quarentenárias", "🦠", "pages/3_Quarentenarias.py", "quarentenarias"),
    ("Relatório",     "📊", "pages/4_Relatorio.py",      "relatorio"),
    ("Consolidado",   "🗂️", "pages/5_Consolidado.py",    "consolidado"),
]


def inject_theme():
    """Injeta o CSS global. Chamar logo após st.set_page_config em toda página."""
    st.markdown(f"""
<style>
/* ═══ Base ═══ */
.block-container {{ padding-top: 1rem; }}
@media (max-width: 768px) {{
    .block-container {{ padding-left: 0.8rem !important; padding-right: 0.8rem !important; }}
}}

/* ═══ Botões (touch-friendly) ═══ */
div[data-testid="stButton"] > button {{
    min-height: 46px; font-size: 14px; border-radius: 8px; font-weight: 600;
    border: 1.5px solid {VERDE_CLARO}; transition: all .15s;
}}
div[data-testid="stButton"] > button:hover {{
    border-color: {VERDE}; color: {VERDE_ESCURO};
}}
/* Botão primário = laranja citros (ação principal / "você está aqui") */
div[data-testid="stButton"] > button[kind="primary"] {{
    background: {LARANJA}; border-color: {LARANJA};
}}
div[data-testid="stButton"] > button[kind="primary"]:hover {{
    background: {LARANJA_CLR}; border-color: {LARANJA_CLR}; color: white;
}}

/* ═══ Menu fixo no topo ═══ */
.isa-topbar {{
    background: linear-gradient(135deg, {VERDE_ESCURO}, {VERDE});
    border-radius: 12px; padding: 0.5rem 0.8rem 0.3rem;
    margin-bottom: 0.6rem;
}}
.isa-topbar-brand {{
    color: white; font-weight: 700; font-size: 0.95rem;
    padding: 0 0.3rem 0.35rem; display: flex; align-items: center; gap: 6px;
}}
.isa-topbar-brand small {{ color: #C8E6C9; font-weight: 500; font-size: 0.72rem; }}
/* botões dentro da topbar mais compactos */
.isa-nav div[data-testid="stButton"] > button {{
    min-height: 40px; font-size: 13px; padding: 0 6px;
    background: rgba(255,255,255,0.12); color: white; border: 1px solid rgba(255,255,255,0.25);
}}
.isa-nav div[data-testid="stButton"] > button:hover {{
    background: rgba(255,255,255,0.25); color: white; border-color: white;
}}
.isa-nav div[data-testid="stButton"] > button[kind="primary"] {{
    background: {LARANJA}; border-color: white; color: white; font-weight: 700;
}}

/* ═══ Cabeçalho de página ═══ */
.isa-header {{
    background: linear-gradient(135deg, {VERDE_ESCURO}, {VERDE});
    color: white; padding: 0.9rem 1.3rem; border-radius: 12px; margin-bottom: 1rem;
    display: flex; align-items: center; gap: 12px;
}}
.isa-header .ico {{ font-size: 2rem; line-height: 1; }}
.isa-header h2 {{ color: white; margin: 0; font-size: 1.3rem; }}
.isa-header p  {{ color: #C8E6C9; margin: 0.15rem 0 0; font-size: 0.82rem; }}

/* ═══ Cards de módulo (home) ═══ */
.modulo-card {{
    background: white; border: 2px solid {VERDE_CLARO}; border-radius: 12px;
    padding: 1.1rem; margin-bottom: 0.6rem; text-align: center; transition: border-color .2s;
}}
.modulo-card:hover {{ border-color: {VERDE}; }}
.modulo-icon  {{ font-size: 2.3rem; margin-bottom: 0.4rem; }}
.modulo-title {{ font-weight: 700; color: {VERDE_ESCURO}; font-size: 1rem; }}
.modulo-desc  {{ color: #666; font-size: 0.8rem; margin-top: 0.3rem; }}

/* ═══ Blocos de info / métricas / alertas ═══ */
.info-box {{
    background: {VERDE_TINT}; border-left: 4px solid {VERDE};
    padding: 0.6rem 1rem; border-radius: 0 8px 8px 0; margin: 0.4rem 0; font-size: 0.85rem;
}}
.m-card {{ background: white; border: 2px solid {VERDE_CLARO}; border-radius: 10px;
           padding: 0.6rem 0.4rem; text-align: center; }}
.m-val  {{ font-size: 1.6rem; font-weight: 700; color: {VERDE_ESCURO}; line-height: 1.1; }}
.m-lab  {{ font-size: 0.72rem; color: #666; margin-top: 2px; }}
.alerta {{ background: {VERMELHO_BG}; border: 2px solid {VERMELHO}; border-radius: 8px;
           padding: 0.6rem 1rem; color: #B71C1C; font-weight: 700; margin: 0.4rem 0; }}
.ok-box {{ background: {VERDE_CLARO}; border: 2px solid {VERDE}; border-radius: 8px;
           padding: 0.6rem 1rem; color: {VERDE_ESCURO}; font-weight: 700; margin: 0.4rem 0; }}
.secao-titulo {{
    font-size: 1.02rem; font-weight: 700; color: {VERDE_ESCURO};
    border-left: 4px solid {LARANJA}; padding-left: 8px; margin: 0.8rem 0 0.4rem;
}}

/* ═══ Badges de status ═══ */
.badge-verde    {{ background:{VERDE_CLARO}; color:{VERDE_ESCURO}; padding:3px 10px;
                   border-radius:20px; font-size:0.8rem; font-weight:600; }}
.badge-amarelo  {{ background:{AMARELO_BG}; color:#F57F17; padding:3px 10px;
                   border-radius:20px; font-size:0.8rem; font-weight:600; }}
.badge-vermelho {{ background:{VERMELHO_BG}; color:#B71C1C; padding:3px 10px;
                   border-radius:20px; font-size:0.8rem; font-weight:600; }}

/* ═══ Checkboxes maiores (touch) ═══ */
div[data-testid="stCheckbox"] label p {{ font-size: 15px; }}
div[data-testid="stCheckbox"] label {{ min-height: 38px; align-items: center; }}
</style>
""", unsafe_allow_html=True)


def top_nav(active: str):
    """Barra de navegação fixa no topo. `active` = chave do item atual."""
    st.markdown('<div class="isa-topbar">'
                '<div class="isa-topbar-brand">🍊 ISA — Inspeção Fitossanitária '
                '<small>Luciano Costella · Citros</small></div>'
                '<div class="isa-nav">', unsafe_allow_html=True)
    cols = st.columns(len(NAV_ITENS))
    for col, (label, ico, caminho, chave) in zip(cols, NAV_ITENS):
        with col:
            is_active = (chave == active)
            if st.button(f"{ico} {label}", key=f"nav_{chave}",
                         use_container_width=True,
                         type="primary" if is_active else "secondary"):
                if not is_active:
                    st.switch_page(caminho)
    st.markdown('</div></div>', unsafe_allow_html=True)


def page_header(icon: str, title: str, subtitle: str = ""):
    """Cabeçalho padrão de página (verde citros)."""
    sub = f'<p>{subtitle}</p>' if subtitle else ''
    st.markdown(f"""
<div class="isa-header">
    <div class="ico">{icon}</div>
    <div><h2>{title}</h2>{sub}</div>
</div>
""", unsafe_allow_html=True)
