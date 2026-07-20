from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from calculations import (
    get_relatorio_pragas, consolidar_quarentenaria, calcular_incidencia,
    plantas_inspecionadas,
)
from database import (
    get_observacoes_inspecao, get_fotos_by_inspecao,
    get_pragas, get_inspecao_summary,
)

# ── Cores compartilhadas ───────────────────────────────────────────────────────
_VERDE_FICHA   = colors.HexColor("#009644")   # cabeçalho tabela (mesmo Excel GH)
_VERDE_ALT     = colors.HexColor("#E1FFD5")   # linha V alternada   (Excel GL)
_AZUL_TEXTO    = colors.HexColor("#0000FF")   # valores editáveis    (Excel BL)
_VERMELHO_SINT = colors.HexColor("#FF0000")   # sintomas             (Excel RD)
_CINZA_BG      = colors.HexColor("#F5F5F5")   # fundo cabeçalho info

VERDE_ESCURO = colors.HexColor("#1A5C2A")
VERDE_MEDIO = colors.HexColor("#2D7D46")
VERDE_CLARO = colors.HexColor("#D6EFD8")
VERMELHO = colors.HexColor("#C62828")
VERMELHO_CLARO = colors.HexColor("#FFEBEE")
AMARELO = colors.HexColor("#F9A825")
AMARELO_CLARO = colors.HexColor("#FFF9C4")
CINZA_CLARO = colors.HexColor("#F5F5F5")
CINZA = colors.HexColor("#9E9E9E")
LARANJA_CLARO = colors.HexColor("#FFF3E0")
BRANCO = colors.white


def _styles():
    base = getSampleStyleSheet()
    styles = {
        'titulo': ParagraphStyle('titulo', fontName='Helvetica-Bold', fontSize=11,
                                  textColor=VERDE_ESCURO, alignment=TA_CENTER, spaceAfter=2),
        'subtitulo': ParagraphStyle('subtitulo', fontName='Helvetica', fontSize=8,
                                     textColor=VERDE_MEDIO, alignment=TA_CENTER, spaceAfter=4),
        'cabecalho_label': ParagraphStyle('cab_label', fontName='Helvetica-Bold', fontSize=8,
                                           textColor=VERDE_ESCURO),
        'cabecalho_valor': ParagraphStyle('cab_valor', fontName='Helvetica', fontSize=8,
                                           textColor=colors.black),
        'secao': ParagraphStyle('secao', fontName='Helvetica-Bold', fontSize=9,
                                 textColor=VERDE_ESCURO, spaceBefore=6, spaceAfter=3),
        'normal': ParagraphStyle('normal', fontName='Helvetica', fontSize=8,
                                  textColor=colors.black, spaceAfter=2),
        'alerta': ParagraphStyle('alerta', fontName='Helvetica-Bold', fontSize=8,
                                  textColor=VERMELHO),
        'rodape': ParagraphStyle('rodape', fontName='Helvetica', fontSize=7,
                                  textColor=CINZA, alignment=TA_CENTER),
        'obs': ParagraphStyle('obs', fontName='Helvetica', fontSize=7.5,
                               textColor=colors.black, spaceAfter=1),
        'foto_leg': ParagraphStyle('foto_leg', fontName='Helvetica', fontSize=7,
                                    textColor=CINZA, alignment=TA_CENTER),
    }
    return styles


def gerar_pdf(inspecao: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    st = _styles()
    story = []

    inspecao_id = inspecao['id']
    total_plantas = inspecao['total_plantas']
    total_inspecionado = plantas_inspecionadas(inspecao_id, total_plantas)

    # ── Cabeçalho ──────────────────────────────────────────────────────────────
    story.append(Paragraph(
        "RELATÓRIO DE INSPEÇÃO FITOSSANITÁRIA EM CITROS", st['titulo']
    ))
    story.append(Paragraph(
        "Ficha de Campo — Pragas, Doenças e Inimigos Naturais", st['subtitulo']
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=VERDE_ESCURO, spaceAfter=6))

    # Dados do técnico e produtor
    dados_cab = [
        [
            Paragraph("<b>TÉCNICO RESPONSÁVEL</b>", st['cabecalho_label']),
            Paragraph("<b>PRODUTOR</b>", st['cabecalho_label']),
            Paragraph("<b>DATAS</b>", st['cabecalho_label']),
        ],
        [
            Paragraph("Luciano Costella<br/>Téc. Agropecuária — CFTA 17893896825<br/>lucianocostella@yahoo.com.br<br/>(19) 99278-2525", st['cabecalho_valor']),
            Paragraph(f"{inspecao['proprietario']}<br/>{inspecao['propriedade']}<br/>{inspecao['municipio']}-{inspecao['estado']}", st['cabecalho_valor']),
            Paragraph(
                f"Inspeção: <b>{inspecao['data_inspecao']}</b><br/>"
                f"Próxima: <b>{inspecao.get('proxima_inspecao', '') or '—'}</b><br/>"
                f"Nº Insp.: <b>{inspecao.get('numero_inspecao', '') or '—'}</b>",
                st['cabecalho_valor']
            ),
        ]
    ]
    t_cab = Table(dados_cab, colWidths=[5.5*cm, 6.5*cm, 5*cm])
    t_cab.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), VERDE_CLARO),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 0.5, VERDE_MEDIO),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, CINZA),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_cab)
    story.append(Spacer(1, 4))

    # Dados da quadra
    dados_quadra = [
        [
            Paragraph(f"<b>Quadra:</b> {inspecao['numero_quadra']}", st['cabecalho_valor']),
            Paragraph(f"<b>Variedade:</b> {inspecao['variedade']}", st['cabecalho_valor']),
            Paragraph(f"<b>Total Plantas:</b> {total_plantas} | <b>Inspecionadas:</b> {total_inspecionado}", st['cabecalho_valor']),
            Paragraph(f"<b>Inspetor(a):</b> {inspecao['inspetor']}", st['cabecalho_valor']),
            Paragraph(f"<b>Início:</b> {inspecao.get('inicio_inspecao', '') or '—'} | <b>Direção:</b> {inspecao.get('direcao', '') or '—'}", st['cabecalho_valor']),
        ]
    ]
    t_q = Table(dados_quadra, colWidths=[2.5*cm, 3.2*cm, 4*cm, 3.2*cm, 4.1*cm])
    t_q.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, VERDE_MEDIO),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, CINZA),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, 0), (-1, -1), CINZA_CLARO),
    ]))
    story.append(t_q)
    story.append(Spacer(1, 8))

    # ── Tabela de Incidência ────────────────────────────────────────────────────
    story.append(Paragraph("RESUMO DE INCIDÊNCIA DE PRAGAS E DOENÇAS", st['secao']))

    pragas_data = get_relatorio_pragas(inspecao_id, total_inspecionado)

    cab_tabela = [
        Paragraph("<b>Praga / Doença</b>", st['cabecalho_label']),
        Paragraph("<b>Parte Avaliada</b>", st['cabecalho_label']),
        Paragraph("<b>Plantas\nAfetadas</b>", st['cabecalho_label']),
        Paragraph("<b>% Incidência</b>", st['cabecalho_label']),
        Paragraph("<b>Limiar\nde Ação</b>", st['cabecalho_label']),
        Paragraph("<b>Situação</b>", st['cabecalho_label']),
    ]
    linhas = [cab_tabela]

    sugestoes = []

    if not pragas_data:
        linhas.append([
            Paragraph("Nenhuma praga registrada nesta inspeção.", st['normal']),
            "", "", "", "", ""
        ])
    else:
        for p in pragas_data:
            if p['alerta_critico'] and p['incidencia'] > 0:
                sit = Paragraph("⚠️ CRÍTICO", st['alerta'])
                row_bg = VERMELHO_CLARO
                sugestoes.append((p['nome'], p['sugestao_controle']))
            elif p['acima_limiar']:
                sit = Paragraph("▶ ACIMA", ParagraphStyle('ac', fontName='Helvetica-Bold', fontSize=8, textColor=AMARELO))
                row_bg = AMARELO_CLARO
                sugestoes.append((p['nome'], p['sugestao_controle']))
            else:
                sit = Paragraph("✓ OK", ParagraphStyle('ok', fontName='Helvetica', fontSize=8, textColor=VERDE_MEDIO))
                row_bg = BRANCO

            parte = p.get('parte_avaliada', '') or '—'
            linhas.append([
                Paragraph(p['nome'], st['normal']),
                Paragraph(parte, st['normal']),
                Paragraph(str(p['plantas_afetadas']), st['normal']),
                Paragraph(f"<b>{p['incidencia']:.1f}%</b>", st['normal']),
                Paragraph(f"{p['limiar_pct']:.0f}%", st['normal']),
                sit,
            ])

    t_pragas = Table(linhas, colWidths=[5.5*cm, 3*cm, 2.3*cm, 2.3*cm, 2.2*cm, 2.2*cm])
    style_pragas = [
        ('BACKGROUND', (0, 0), (-1, 0), VERDE_ESCURO),
        ('TEXTCOLOR', (0, 0), (-1, 0), BRANCO),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 0.5, VERDE_MEDIO),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, CINZA),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRANCO, CINZA_CLARO]),
    ]

    for i, p in enumerate(pragas_data, start=1):
        if p['alerta_critico'] and p['incidencia'] > 0:
            style_pragas.append(('BACKGROUND', (0, i), (-1, i), VERMELHO_CLARO))
        elif p['acima_limiar']:
            style_pragas.append(('BACKGROUND', (0, i), (-1, i), AMARELO_CLARO))

    t_pragas.setStyle(TableStyle(style_pragas))
    story.append(t_pragas)
    story.append(Spacer(1, 8))

    # ── Sugestões de Controle ──────────────────────────────────────────────────
    if sugestoes:
        story.append(Paragraph("SUGESTÃO DE AÇÃO E CONTROLE DE PRAGAS", st['secao']))
        for nome, sugestao in sugestoes:
            story.append(Paragraph(f"<b>• {nome}:</b>", st['normal']))
            story.append(Paragraph(f"&nbsp;&nbsp;{sugestao}", st['normal']))
            story.append(Spacer(1, 2))
        story.append(Spacer(1, 4))

    # ── Rastreabilidade Quarentenária ─────────────────────────────────────────
    for doenca in ("GREENING", "CANCRO"):
        cons = consolidar_quarentenaria(inspecao_id, doenca)
        if cons['total_vistoriadas'] == 0:
            continue

        emoji = "🦠" if doenca == "GREENING" else "⚠️"
        story.append(Paragraph(f"{emoji} RASTREABILIDADE — {doenca} CÍTRICO", st['secao']))

        cor_fundo = VERMELHO_CLARO if cons['notificar'] else VERDE_CLARO
        resumo_data = [[
            Paragraph(f"<b>Total Vistoriado:</b> {cons['total_vistoriadas']} plantas", st['normal']),
            Paragraph(f"<b>Com Sintomas:</b> {cons['total_sintomas']} plantas", st['normal']),
            Paragraph(f"<b>Incidência:</b> {cons['percentual']:.3f}%", st['normal']),
            Paragraph(
                "<b>⚠️ NOTIFICAÇÃO OBRIGATÓRIA</b>" if cons['notificar'] else "<b>✓ Sem ocorrência</b>",
                st['alerta'] if cons['notificar'] else st['normal']
            ),
        ]]
        t_resumo = Table(resumo_data, colWidths=[4*cm, 4*cm, 3.5*cm, 5.5*cm])
        t_resumo.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), cor_fundo),
            ('BOX', (0, 0), (-1, -1), 0.5, VERMELHO if cons['notificar'] else VERDE_MEDIO),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, CINZA),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        story.append(t_resumo)
        story.append(Spacer(1, 3))

        if cons['notificar']:
            for ficha in cons['fichas']:
                if ficha['total_sintomas'] == 0:
                    continue
                story.append(Paragraph(
                    f"{ficha['numero_ficha']} — Inspetor: {ficha['inspetor']} — "
                    f"{ficha['total_plantas']} plantas vistoriadas / {ficha['total_sintomas']} com sintoma",
                    st['normal']
                ))
                cab_rua = [
                    Paragraph("<b>Rua</b>", st['cabecalho_label']),
                    Paragraph("<b>Dir.</b>", st['cabecalho_label']),
                    Paragraph("<b>Total</b>", st['cabecalho_label']),
                    Paragraph("<b>Plantas c/ Sintoma</b>", st['cabecalho_label']),
                    Paragraph("<b>Qtd</b>", st['cabecalho_label']),
                ]
                linhas_rua = [cab_rua]
                for rua in ficha['ruas']:
                    if rua['qtd_sintomas'] > 0:
                        linhas_rua.append([
                            Paragraph(str(rua['numero_rua']), st['normal']),
                            Paragraph(rua['direcao'], st['normal']),
                            Paragraph(str(rua['total_plantas']), st['normal']),
                            Paragraph(rua['plantas_sintomas'], st['normal']),
                            Paragraph(str(rua['qtd_sintomas']), st['alerta']),
                        ])
                if len(linhas_rua) > 1:
                    t_rua = Table(linhas_rua, colWidths=[2*cm, 1.5*cm, 2*cm, 9*cm, 2*cm])
                    t_rua.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), VERDE_ESCURO),
                        ('TEXTCOLOR', (0, 0), (-1, 0), BRANCO),
                        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
                        ('BOX', (0, 0), (-1, -1), 0.5, CINZA),
                        ('INNERGRID', (0, 0), (-1, -1), 0.3, CINZA),
                        ('TOPPADDING', (0, 0), (-1, -1), 3),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                        ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ]))
                    story.append(t_rua)
                    story.append(Spacer(1, 3))

        story.append(Spacer(1, 4))

    # ── Observações Gerais ────────────────────────────────────────────────────
    obs = get_observacoes_inspecao(inspecao_id)
    if obs:
        story.append(Paragraph("OBSERVAÇÕES GERAIS", st['secao']))
        for txt in obs:
            story.append(Paragraph(f"• {txt}", st['obs']))
        story.append(Spacer(1, 6))

    # ── Fotos das Plantas ─────────────────────────────────────────────────────
    fotos = get_fotos_by_inspecao(inspecao_id)
    if fotos:
        story.append(Paragraph("REGISTRO FOTOGRÁFICO", st['secao']))
        story.append(Spacer(1, 4))

        FOTOS_POR_LINHA = 3
        LARGURA_FOTO = 5.5 * cm
        ALTURA_MAX = 5 * cm

        linha_imgs = []
        linha_legs = []

        for foto in fotos:
            try:
                img_buf = BytesIO(foto['foto_data'])
                img = Image(img_buf, width=LARGURA_FOTO, height=ALTURA_MAX, kind='proportional')
                leg = Paragraph(f"Planta {foto['numero_planta']}", st['foto_leg'])
                linha_imgs.append(img)
                linha_legs.append(leg)
            except Exception:
                continue

            if len(linha_imgs) == FOTOS_POR_LINHA:
                t_fotos = Table(
                    [linha_imgs, linha_legs],
                    colWidths=[LARGURA_FOTO] * FOTOS_POR_LINHA
                )
                t_fotos.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))
                story.append(t_fotos)
                story.append(Spacer(1, 4))
                linha_imgs = []
                linha_legs = []

        # Remaining photos (incomplete row)
        if linha_imgs:
            while len(linha_imgs) < FOTOS_POR_LINHA:
                linha_imgs.append(Paragraph("", st['normal']))
                linha_legs.append(Paragraph("", st['normal']))
            t_fotos = Table(
                [linha_imgs, linha_legs],
                colWidths=[LARGURA_FOTO] * FOTOS_POR_LINHA
            )
            t_fotos.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(t_fotos)
            story.append(Spacer(1, 4))

    # ── Assinatura ────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=CINZA, spaceBefore=10, spaceAfter=6))
    assin_data = [[
        Paragraph(
            "<b>Luciano Costella</b><br/>Técnico em Agropecuária<br/>"
            "CFTA: 17893896825<br/>\"Consultoria em Citros desde 2005\"",
            st['cabecalho_valor']
        ),
        Paragraph(
            f"<b>Assinado em:</b> {inspecao['data_inspecao']}<br/><br/>"
            "______________________________<br/>Assinatura do Técnico Responsável",
            st['cabecalho_valor']
        ),
    ]]
    t_ass = Table(assin_data, colWidths=[9*cm, 8*cm])
    t_ass.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_ass)

    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Documento gerado pelo Sistema ISA — Gestão de Inspeção Fitossanitária de Citros",
        st['rodape']
    ))

    doc.build(story)
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# PDF da Ficha Quarentenária — formato fiel à planilha Excel
# ══════════════════════════════════════════════════════════════════════════════

def gerar_pdf_ficha_quarentenaria(
    inspecao: dict,
    ficha: dict,
    ruas: list,
    doenca_key: str,
) -> bytes:
    """Gera o PDF no formato da Ficha de Inspeção de Greening/Cancro em Citros."""

    buffer = BytesIO()

    WH  = colors.white
    BK  = colors.black
    CZ  = _CINZA_BG

    # estilos
    S = {
        'title':  ParagraphStyle('fq_title',  fontName='Helvetica-Bold', fontSize=13,
                                 textColor=BK, alignment=TA_CENTER, spaceAfter=4),
        'lbl':    ParagraphStyle('fq_lbl',    fontName='Helvetica-Bold', fontSize=8,
                                 textColor=BK),
        'val_bl': ParagraphStyle('fq_vbl',    fontName='Helvetica-Bold', fontSize=8,
                                 textColor=_AZUL_TEXTO),
        'val_rd': ParagraphStyle('fq_vrd',    fontName='Helvetica-Bold', fontSize=8,
                                 textColor=_VERMELHO_SINT),
        'th':     ParagraphStyle('fq_th',     fontName='Helvetica-Bold', fontSize=8,
                                 textColor=WH, alignment=TA_CENTER),
        'td_c':   ParagraphStyle('fq_tdc',    fontName='Helvetica',      fontSize=7.5,
                                 textColor=BK, alignment=TA_CENTER),
        'td_bl':  ParagraphStyle('fq_tdbl',   fontName='Helvetica-Bold', fontSize=7.5,
                                 textColor=_AZUL_TEXTO, alignment=TA_CENTER),
        'td_rd':  ParagraphStyle('fq_tdrd',   fontName='Helvetica-Bold', fontSize=7.5,
                                 textColor=_VERMELHO_SINT),
        'rodape': ParagraphStyle('fq_rod',    fontName='Helvetica-Bold', fontSize=8,
                                 textColor=BK, alignment=TA_CENTER),
        'small':  ParagraphStyle('fq_sm',     fontName='Helvetica',      fontSize=7,
                                 textColor=colors.grey, alignment=TA_CENTER),
    }

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.2*cm, rightMargin=1.2*cm,
        topMargin=1.2*cm,  bottomMargin=1.2*cm,
    )

    story = []

    # ── Título ─────────────────────────────────────────────────────────────────
    doenca_nome = "GREENING (HLB)" if doenca_key == "GREENING" else "CANCRO CÍTRICO"
    story.append(Paragraph(
        f"FICHA DE INSPEÇÃO DE {doenca_nome} EM CITROS",
        S['title']
    ))

    # ── Calcular totais ────────────────────────────────────────────────────────
    def _cnt(s):
        if not s: return 0
        return len([n.strip() for n in str(s).replace(';', ',').split(',') if n.strip().isdigit()])

    total_pl   = sum(int(r.get('total_plantas_rua', 0) or 0) for r in ruas)
    total_sint = sum(_cnt(r.get('plantas_sintomas', '')) for r in ruas)
    pct        = (total_sint / total_pl * 100) if total_pl > 0 else 0.0

    # ── Cabeçalho (3 linhas, espelho do Excel) ─────────────────────────────────
    W = 17.6 * cm
    cw_lbl, cw_val = 2.8*cm, 3.4*cm   # label + valor, 4 pares = 4*(2.8+3.4)=24.8 — ajuste abaixo
    # 2 pares de 3.2+1.8 + 2 pares de 3.2+1.8 = 4 pares de 3.8+0.6... vamos usar 4 colunas uniformes
    cw = [2.5*cm, 3.4*cm, 2.2*cm, 3.4*cm, 2.2*cm, 3.4*cm, 3.6*cm, 2.4*cm]  # 8 cols = 23.1cm? A4=21cm

    # Simplifica para 4 linhas de info legíveis (não cabe 8 colunas em A4 portrait)
    def _row(pairs):
        """pairs = [(label, value, style_val), ...]"""
        cells = []
        for lbl, val, sty in pairs:
            cells.append(Paragraph(f'<b>{lbl}</b>', S['lbl']))
            cells.append(Paragraph(str(val), S[sty]))
        return cells

    # larguras: alternando label(2.6)+valor(3.0) × 3 = 17.4cm
    col_ws = [2.3*cm, 3.0*cm, 2.3*cm, 3.0*cm, 2.3*cm, 3.0*cm]

    cab_rows = [
        _row([
            ('Data da Inspeção:', inspecao['data_inspecao'],    'val_bl'),
            ('Quadra:',           inspecao['numero_quadra'],    'val_bl'),
            ('Variedade:',        inspecao['variedade'],        'val_bl'),
        ]),
        _row([
            ('Propriedade:',      inspecao['propriedade'],      'val_bl'),
            ('Proprietário:',     inspecao['proprietario'],     'val_bl'),
            ('Município:',        f"{inspecao['municipio']}-{inspecao['estado']}", 'val_bl'),
        ]),
        _row([
            ('Ficha Nº:',         ficha['numero_ficha'],        'val_bl'),
            ('Inspetor:',         ficha['inspetor'],            'val_bl'),
            ('Total de Plantas:', str(inspecao['total_plantas']), 'val_bl'),
        ]),
        _row([
            ('Total c/ Sintomas:', str(total_sint),             'val_bl'),
            ('% de Sintomas:',    f'{pct:.3f}%',               'val_rd'),
            ('Início Inspeção:',  inspecao.get('inicio_inspecao','') or '—', 'val_bl'),
        ]),
    ]

    t_cab = Table(cab_rows, colWidths=col_ws, repeatRows=0)
    t_cab.setStyle(TableStyle([
        ('BOX',          (0, 0), (-1, -1), 0.75, BK),
        ('INNERGRID',    (0, 0), (-1, -1), 0.4,  BK),
        ('BACKGROUND',   (0, 0), (-1, -1), CZ),
        ('TOPPADDING',   (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
        ('LEFTPADDING',  (0, 0), (-1, -1), 5),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE',     (0, 0), (-1, -1), 8),
    ]))
    story.append(t_cab)
    story.append(Spacer(1, 6))

    # ── Tabela de ruas (26 linhas, espelho da grade Excel) ─────────────────────
    rows_map = {r['numero_rua']: r for r in ruas}

    # Cabeçalho da tabela (verde escuro, texto branco)
    cabecalho_tabela = [
        Paragraph('<b>Rua</b>',              S['th']),
        Paragraph('<b>I/V</b>',              S['th']),
        Paragraph('<b>Sub.\nTotal</b>',      S['th']),
        Paragraph('<b>Inspetor</b>',         S['th']),
        Paragraph(f'<b>Números de Plantas com Sintomas de {doenca_key}</b>', S['th']),
        Paragraph('<b>Qtd</b>',              S['th']),
    ]
    linhas_tabela = [cabecalho_tabela]

    for i in range(1, 27):
        d_default = 'I' if i % 2 == 1 else 'V'
        r         = rows_map.get(i, {})
        total_r   = int(r.get('total_plantas_rua', 0) or 0)
        sint      = r.get('plantas_sintomas', '') or ''
        ins_rua   = r.get('inspetor_rua', '') or ficha['inspetor']
        direcao   = r.get('direcao_rua', d_default)
        qtd       = _cnt(sint)

        linhas_tabela.append([
            Paragraph(str(i),                                    S['td_bl']),
            Paragraph(direcao,                                   S['td_bl']),
            Paragraph(str(total_r) if total_r > 0 else '',      S['td_bl']),
            Paragraph(ins_rua,                                   S['td_c']),
            Paragraph(sint,                                      S['td_rd']),
            Paragraph(str(qtd)  if qtd > 0 else '',             S['td_bl']),
        ])

    # larguras: Rua(1.1) + IV(1.0) + SubTotal(1.5) + Inspetor(3.2) + Sintomas(9.3) + Qtd(1.4) = 17.5cm
    cw_tabela = [1.1*cm, 1.0*cm, 1.5*cm, 3.2*cm, 9.3*cm, 1.4*cm]

    rua_styles = [
        ('BACKGROUND',   (0, 0), (-1, 0), _VERDE_FICHA),
        ('FONTSIZE',     (0, 0), (-1, -1), 7.5),
        ('BOX',          (0, 0), (-1, -1), 0.75, BK),
        ('INNERGRID',    (0, 0), (-1, -1), 0.4, colors.HexColor('#AAAAAA')),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',   (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 2),
        ('LEFTPADDING',  (0, 0), (-1, -1), 3),
    ]
    # linhas V (par: 2, 4, 6, ... → índice de tabela 2, 4, 6, ...)
    for i in range(1, 27):
        if i % 2 == 0:          # linha V (par no número da rua)
            rua_styles.append(('BACKGROUND', (0, i), (-1, i), _VERDE_ALT))

    t_ruas = Table(linhas_tabela, colWidths=cw_tabela, repeatRows=1)
    t_ruas.setStyle(TableStyle(rua_styles))
    story.append(t_ruas)
    story.append(Spacer(1, 8))

    # ── Rodapé ─────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5,
                            color=colors.grey, spaceAfter=4))
    story.append(Paragraph(
        "LUCIANO COSTELLA — TÉCNICO AGRÍCOLA CFTA 17893896825 — "
        "Cel. (019) 99278-2525 — lucianocostella@yahoo.com.br",
        S['rodape']
    ))
    story.append(Spacer(1, 6))

    ass_data = [[
        Paragraph(
            f"<b>Início da Inspeção:</b> {inspecao.get('inicio_inspecao','') or '___________'}",
            S['small']
        ),
        Paragraph("Assinatura: ________________________________", S['small']),
    ]]
    t_ass = Table(ass_data, colWidths=[8.8*cm, 8.8*cm])
    t_ass.setStyle(TableStyle([
        ('TOPPADDING',    (0,0),(-1,-1), 3),
        ('BOTTOMPADDING', (0,0),(-1,-1), 3),
    ]))
    story.append(t_ass)
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        "Documento gerado pelo Sistema ISA — Gestão de Inspeção Fitossanitária de Citros",
        S['small']
    ))

    doc.build(story)
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# PDF da Ficha de Campo — grade pragas × plantas (fiel à aba "Citros " do Excel)
# ══════════════════════════════════════════════════════════════════════════════

# Estrutura de seções idêntica à página 2_Campo.py (mesma ordem do Excel).
_CAMPO_SECOES = [
    ("ÁCARO FERRUGEM", colors.HexColor("#C62828"), colors.HexColor("#FFEBEE"), [
        "Ácaro Ferrugem (< 10 ácaros)",
        "Ácaro Ferrugem (10 ou + ácaros)",
    ]),
    ("ÁCARO LEPROSE", colors.HexColor("#E65100"), colors.HexColor("#FFF3E0"), [
        "Ácaro Leprose",
    ]),
    ("PRAGAS DIVERSAS", colors.HexColor("#4527A0"), colors.HexColor("#EDE7F6"), [
        "Ácaro Branco", "Mosca das Frutas", "Bicho Furão", "Ácaro Purpúreo",
        "Ácaro Mexicano", "Ácaro Texano", "Pulgão Verde", "Pulgão Preto",
        "Lagarta", "Minadora das Folhas", "Tripes", "Psilídeo",
    ]),
    ("INIMIGOS NATURAIS", colors.HexColor("#1B5E20"), colors.HexColor("#E8F5E9"), [
        "Inimigos Naturais",
    ]),
]

_DIAS_PT = ['SEGUNDA-FEIRA', 'TERÇA-FEIRA', 'QUARTA-FEIRA',
            'QUINTA-FEIRA', 'SEXTA-FEIRA', 'SÁBADO', 'DOMINGO']


def _fmt_data_pt(s):
    if not s:
        return '—', ''
    try:
        dt = datetime.strptime(s, '%Y-%m-%d')
        return f"{dt.day:02d}/{dt.month:02d}/{dt.year}", _DIAS_PT[dt.weekday()]
    except Exception:
        return s, ''


def gerar_pdf_ficha_campo(inspecao: dict) -> bytes:
    """Gera o PDF da ficha de campo no formato de grade (pragas nas linhas,
    plantas nas colunas), replicando a aba 'Citros ' do ISAeGUI.xlsm."""

    inspecao_id   = inspecao['id']
    total_plantas = inspecao['total_plantas']
    summary       = get_inspecao_summary(inspecao_id)
    pragas        = get_pragas()
    pragas_map    = {p['nome']: p for p in pragas}

    # Plantas efetivamente inspecionadas (máx. registrada) para o cálculo do %.
    all_plants = set()
    for d in summary.values():
        all_plants |= d['plantas']
    n_insp     = max(all_plants) if all_plants else 0
    total_insp = n_insp if n_insp > 0 else total_plantas
    n_cols     = max(total_plantas, n_insp)

    buffer = BytesIO()
    BK = colors.black
    WH = colors.white

    S = {
        'title': ParagraphStyle('fc_title', fontName='Helvetica-Bold', fontSize=13,
                                 textColor=VERDE_ESCURO, alignment=TA_CENTER, spaceAfter=2),
        'sub':   ParagraphStyle('fc_sub', fontName='Helvetica-Oblique', fontSize=8,
                                 textColor=colors.HexColor("#6A1B9A"), alignment=TA_CENTER, spaceAfter=4),
        'lbl':   ParagraphStyle('fc_lbl', fontName='Helvetica-Bold', fontSize=8, textColor=VERDE_ESCURO),
        'val':   ParagraphStyle('fc_val', fontName='Helvetica-Bold', fontSize=8, textColor=colors.black),
        'th':    ParagraphStyle('fc_th', fontName='Helvetica-Bold', fontSize=7,
                                 textColor=WH, alignment=TA_CENTER),
        'praga': ParagraphStyle('fc_praga', fontName='Helvetica-Bold', fontSize=7, textColor=BK),
        'parte': ParagraphStyle('fc_parte', fontName='Helvetica', fontSize=6, textColor=colors.grey),
        'sec':   ParagraphStyle('fc_sec', fontName='Helvetica-Bold', fontSize=8, textColor=WH),
        'small': ParagraphStyle('fc_small', fontName='Helvetica', fontSize=7,
                                textColor=colors.grey, alignment=TA_CENTER),
        'obs':   ParagraphStyle('fc_obs', fontName='Helvetica', fontSize=7.5, textColor=BK, spaceAfter=1),
        'alerta':ParagraphStyle('fc_alerta', fontName='Helvetica-Bold', fontSize=9,
                                 textColor=VERMELHO, alignment=TA_CENTER),
    }

    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=1.0*cm, rightMargin=1.0*cm,
        topMargin=1.0*cm,  bottomMargin=1.0*cm,
    )
    story = []

    # ── Título ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("FICHA DE INSPEÇÃO FITOSSANITÁRIA EM CITROS", S['title']))
    story.append(Paragraph(
        '"LUCIANO COSTELLA, CONSULTORIA EM CITROS DESDE 2005"', S['sub']))

    # ── Cabeçalho ──────────────────────────────────────────────────────────────
    data_fmt, dia = _fmt_data_pt(inspecao.get('data_inspecao', ''))
    prox_fmt, prox_dia = _fmt_data_pt(inspecao.get('proxima_inspecao', ''))

    def _cell(lbl, val):
        return Table(
            [[Paragraph(f'<b>{lbl}</b>', S['lbl']), Paragraph(str(val), S['val'])]],
            colWidths=[2.4*cm, 4.6*cm],
            style=[('LEFTPADDING',(0,0),(-1,-1),1), ('RIGHTPADDING',(0,0),(-1,-1),1),
                   ('TOPPADDING',(0,0),(-1,-1),1), ('BOTTOMPADDING',(0,0),(-1,-1),1),
                   ('VALIGN',(0,0),(-1,-1),'MIDDLE')]
        )

    cab = [
        [_cell('Propriedade:', inspecao['propriedade']),
         _cell('Quadra:',      inspecao['numero_quadra']),
         _cell('Data:',        f"{data_fmt}  {dia}")],
        [_cell('Proprietário:', inspecao['proprietario']),
         _cell('Variedade:',    inspecao['variedade']),
         _cell('Nº Plantas Insp.:', n_insp or total_plantas)],
        [_cell('Talhão:',   f"{inspecao['municipio']}-{inspecao['estado']}"),
         _cell('Inspetor:', inspecao['inspetor']),
         _cell('Próxima Insp.:', f"{prox_fmt}  {prox_dia}")],
    ]
    t_cab = Table(cab, colWidths=[9.4*cm, 9.0*cm, 9.0*cm])
    t_cab.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1), 0.8, VERDE_MEDIO),
        ('INNERGRID',(0,0),(-1,-1), 0.4, colors.HexColor("#C8E6C9")),
        ('BACKGROUND',(0,0),(-1,-1), colors.HexColor("#F9FBE7")),
        ('LEFTPADDING',(0,0),(-1,-1),3), ('RIGHTPADDING',(0,0),(-1,-1),3),
        ('TOPPADDING',(0,0),(-1,-1),2), ('BOTTOMPADDING',(0,0),(-1,-1),2),
    ]))
    story.append(t_cab)
    story.append(Spacer(1, 6))

    # ── Alerta Psilídeo ────────────────────────────────────────────────────────
    psil = pragas_map.get("Psilídeo")
    if psil and len(summary.get(psil['id'], {}).get('plantas', set())) > 0:
        story.append(Paragraph(
            "ALERTA — PSILIDEO DETECTADO (vetor do Greening/HLB). "
            "Aplicar inseticida e notificar fiscalizacao.", S['alerta']))
        story.append(Spacer(1, 4))

    # ── Grade em blocos de 35 plantas ──────────────────────────────────────────
    BLOCO = 35
    usable_w = landscape(A4)[0] - 2.0*cm      # largura útil
    lbl_w, parte_w, pct_w, lim_w = 3.6*cm, 2.0*cm, 1.0*cm, 1.0*cm

    inicio = 1
    while inicio <= n_cols:
        fim = min(inicio + BLOCO - 1, n_cols)
        plantas_bloco = list(range(inicio, fim + 1))
        n = len(plantas_bloco)
        col_plant_w = (usable_w - lbl_w - parte_w - pct_w - lim_w) / max(n, 1)

        # Cabeçalho do bloco
        header = [
            Paragraph('Praga / Doença', S['th']),
            Paragraph('Parte', S['th']),
        ] + [Paragraph(str(p), S['th']) for p in plantas_bloco] + [
            Paragraph('%', S['th']),
            Paragraph('Lim', S['th']),
        ]
        data = [header]
        row_styles = [
            ('BACKGROUND', (0, 0), (-1, 0), VERDE_MEDIO),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#BDBDBD")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 1),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1),
        ]

        r = 1
        for sec_nome, sec_cor, sec_bg, sec_pragas in _CAMPO_SECOES:
            # Linha de título da seção (mesclada)
            sec_row = [Paragraph(sec_nome, S['sec'])] + [''] * (n + 3)
            data.append(sec_row)
            row_styles.append(('SPAN', (0, r), (-1, r)))
            row_styles.append(('BACKGROUND', (0, r), (-1, r), sec_cor))
            r += 1

            for pnome in sec_pragas:
                praga = pragas_map.get(pnome)
                if not praga:
                    continue
                pid = praga['id']
                plants_pest = summary.get(pid, {}).get('plantas', set())
                inc = calcular_incidencia(len(plants_pest), total_insp)
                lim = praga['limiar_acao'] * 100
                acima = lim > 0 and inc >= lim

                linha = [
                    Paragraph(praga['nome'], S['praga']),
                    Paragraph(praga.get('parte_avaliada', '') or '—', S['parte']),
                ]
                for p in plantas_bloco:
                    linha.append(Paragraph('X', S['praga']) if p in plants_pest else '')
                linha.append(Paragraph(f"{inc:.1f}", S['praga']))
                linha.append(Paragraph(f"{lim:.0f}", S['praga']))
                data.append(linha)

                row_styles.append(('BACKGROUND', (0, r), (1, r), sec_bg))
                # marca % acima do limiar em vermelho
                if acima:
                    row_styles.append(('BACKGROUND', (-2, r), (-1, r), VERMELHO_CLARO))
                    row_styles.append(('TEXTCOLOR', (-2, r), (-2, r), VERMELHO))
                # células com "X" em vermelho
                for j, p in enumerate(plantas_bloco):
                    if p in plants_pest:
                        row_styles.append(('TEXTCOLOR', (2 + j, r), (2 + j, r), VERMELHO))
                r += 1

        col_ws = [lbl_w, parte_w] + [col_plant_w] * n + [pct_w, lim_w]
        t = Table(data, colWidths=col_ws, repeatRows=1)
        t.setStyle(TableStyle(row_styles))
        story.append(t)
        story.append(Spacer(1, 6))
        inicio = fim + 1

    # ── Observações gerais / Índice de Avaliação ───────────────────────────────
    obs = get_observacoes_inspecao(inspecao_id)
    if obs:
        story.append(HRFlowable(width="100%", thickness=0.5, color=CINZA, spaceAfter=3))
        story.append(Paragraph("<b>ÍNDICE DE AVALIAÇÃO / OBSERVAÇÕES GERAIS</b>", S['lbl']))
        story.append(Spacer(1, 2))
        # em duas colunas para aproveitar a largura landscape
        meio = (len(obs) + 1) // 2
        col_a = "<br/>".join(f"• {o}" for o in obs[:meio])
        col_b = "<br/>".join(f"• {o}" for o in obs[meio:])
        t_obs = Table(
            [[Paragraph(col_a, S['obs']), Paragraph(col_b, S['obs'])]],
            colWidths=[13.4*cm, 13.4*cm]
        )
        t_obs.setStyle(TableStyle([('VALIGN', (0,0),(-1,-1),'TOP'),
                                   ('LEFTPADDING',(0,0),(-1,-1),4)]))
        story.append(t_obs)
        story.append(Spacer(1, 6))

    # ── Rodapé + assinatura ────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=CINZA, spaceAfter=4))
    story.append(Paragraph(
        "LUCIANO COSTELLA — TÉCNICO EM AGROPECUÁRIA CFTA 17893896825", S['small']))
    story.append(Spacer(1, 8))
    ass = [[
        Paragraph(f"<b>Início da Inspeção:</b> {inspecao.get('inicio_inspecao','') or '___________'}", S['small']),
        Paragraph("Assinatura: ________________________________", S['small']),
    ]]
    t_ass = Table(ass, colWidths=[13.4*cm, 13.4*cm])
    t_ass.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),3), ('BOTTOMPADDING',(0,0),(-1,-1),3)]))
    story.append(t_ass)

    doc.build(story)
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# PDF do Relatório Consolidado — todas as quadras da propriedade (aba CONTROLE)
# ══════════════════════════════════════════════════════════════════════════════

def gerar_pdf_consolidado(cliente: dict, linhas: list) -> bytes:
    """Relatório consolidado por propriedade: uma linha por quadra, colunas com
    o % de cada grupo de pragas. Replica a aba CONTROLE do ISAeGUI.xlsm."""

    buffer = BytesIO()
    BK, WH = colors.black, colors.white

    S = {
        'title': ParagraphStyle('cs_title', fontName='Helvetica-Bold', fontSize=13,
                                 textColor=VERDE_ESCURO, alignment=TA_CENTER, spaceAfter=2),
        'sub':   ParagraphStyle('cs_sub', fontName='Helvetica-Oblique', fontSize=8,
                                 textColor=colors.HexColor("#6A1B9A"), alignment=TA_CENTER, spaceAfter=4),
        'lbl':   ParagraphStyle('cs_lbl', fontName='Helvetica-Bold', fontSize=8, textColor=VERDE_ESCURO),
        'val':   ParagraphStyle('cs_val', fontName='Helvetica-Bold', fontSize=8, textColor=colors.black),
        'th':    ParagraphStyle('cs_th', fontName='Helvetica-Bold', fontSize=6.5,
                                 textColor=WH, alignment=TA_CENTER, leading=7.5),
        'lim':   ParagraphStyle('cs_lim', fontName='Helvetica-Oblique', fontSize=6,
                                 textColor=colors.grey, alignment=TA_CENTER),
        'cell':  ParagraphStyle('cs_cell', fontName='Helvetica', fontSize=7,
                                 textColor=BK, alignment=TA_CENTER),
        'cell_r':ParagraphStyle('cs_cellr', fontName='Helvetica-Bold', fontSize=7,
                                 textColor=VERMELHO, alignment=TA_CENTER),
        'quad':  ParagraphStyle('cs_quad', fontName='Helvetica-Bold', fontSize=7.5,
                                 textColor=BK, alignment=TA_CENTER),
        'var':   ParagraphStyle('cs_var', fontName='Helvetica', fontSize=6.5, textColor=BK),
        'small': ParagraphStyle('cs_small', fontName='Helvetica', fontSize=7,
                                textColor=colors.grey, alignment=TA_CENTER),
    }

    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=1.0*cm, rightMargin=1.0*cm, topMargin=1.0*cm, bottomMargin=1.0*cm,
    )
    story = []

    story.append(Paragraph("RELATÓRIO CONSOLIDADO — INSPEÇÃO FITOSSANITÁRIA EM CITROS", S['title']))
    story.append(Paragraph('"LUCIANO COSTELLA, CONSULTORIA EM CITROS DESDE 2005"', S['sub']))

    # ── Cabeçalho ──────────────────────────────────────────────────────────────
    tecnico = ("<b>Luciano Costella</b> — Técnico em Agropecuária CFTA 17893896825<br/>"
               "(19) 99278-2525 — lucianocostella@yahoo.com.br")
    prop = (f"<b>Produtor:</b> {cliente['proprietario']}<br/>"
            f"<b>Propriedade:</b> {cliente['propriedade']}<br/>"
            f"<b>Talhão:</b> {cliente['municipio']}-{cliente['estado']}")
    t_cab = Table([[Paragraph(tecnico, S['val']), Paragraph(prop, S['val'])]],
                  colWidths=[13.4*cm, 13.4*cm])
    t_cab.setStyle(TableStyle([
        ('BOX', (0,0),(-1,-1), 0.8, VERDE_MEDIO),
        ('INNERGRID', (0,0),(-1,-1), 0.4, colors.HexColor("#C8E6C9")),
        ('BACKGROUND', (0,0),(-1,-1), colors.HexColor("#F9FBE7")),
        ('VALIGN', (0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),6), ('TOPPADDING',(0,0),(-1,-1),3),
        ('BOTTOMPADDING',(0,0),(-1,-1),3),
    ]))
    story.append(t_cab)
    story.append(Spacer(1, 6))

    if not linhas:
        story.append(Paragraph("Nenhuma inspeção registrada para esta propriedade.", S['val']))
        doc.build(story)
        return buffer.getvalue()

    # ── Tabela consolidada ─────────────────────────────────────────────────────
    col_defs = linhas[0]['cols']          # rótulos e limiares (mesma ordem em todas as linhas)
    n_pest = len(col_defs)

    usable_w = landscape(A4)[0] - 2.0*cm
    quad_w, var_w = 1.3*cm, 2.4*cm
    pest_w = (usable_w - quad_w - var_w) / n_pest

    # Cabeçalho
    header = [Paragraph('Quadra', S['th']), Paragraph('Variedade', S['th'])]
    header += [Paragraph(c['rotulo'], S['th']) for c in col_defs]
    # Linha de limiares
    lim_row = [Paragraph('Limiar', S['lim']), Paragraph('', S['lim'])]
    lim_row += [Paragraph(f"{c['limiar']:.0f}%" if c['limiar'] > 0 else '—', S['lim'])
                for c in col_defs]

    data = [header, lim_row]
    row_styles = [
        ('BACKGROUND', (0,0),(-1,0), VERDE_MEDIO),
        ('BACKGROUND', (0,1),(-1,1), colors.HexColor("#EEEEEE")),
        ('GRID', (0,0),(-1,-1), 0.4, colors.HexColor("#BDBDBD")),
        ('VALIGN', (0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),2), ('BOTTOMPADDING',(0,0),(-1,-1),2),
        ('LEFTPADDING',(0,0),(-1,-1),2), ('RIGHTPADDING',(0,0),(-1,-1),2),
    ]

    r = 2
    for linha in linhas:
        cells = [
            Paragraph(str(linha['quadra']), S['quad']),
            Paragraph(str(linha['variedade']), S['var']),
        ]
        for j, c in enumerate(linha['cols']):
            sty = S['cell_r'] if c['acima'] else S['cell']
            txt = f"{c['valor']:.1f}" if c['valor'] > 0 else "-"
            cells.append(Paragraph(txt, sty))
            if c['acima']:
                row_styles.append(('BACKGROUND', (2 + j, r), (2 + j, r), VERMELHO_CLARO))
        data.append(cells)
        # zebra
        if r % 2 == 0:
            row_styles.append(('BACKGROUND', (0, r), (1, r), colors.HexColor("#F5F5F5")))
        r += 1

    col_ws = [quad_w, var_w] + [pest_w] * n_pest
    t = Table(data, colWidths=col_ws, repeatRows=2)
    t.setStyle(TableStyle(row_styles))
    story.append(t)
    story.append(Spacer(1, 6))

    # ── Legenda ────────────────────────────────────────────────────────────────
    story.append(Paragraph(
        "Valores em % de plantas com presença. Células em <font color='#C62828'><b>vermelho</b></font> "
        "indicam praga acima do limiar de ação. Colunas com mais de uma praga (Ác. P/M/T, Pulgão) "
        "consideram a união das plantas afetadas.", S['small']))
    story.append(Spacer(1, 8))

    # ── Rodapé ─────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=CINZA, spaceAfter=4))
    story.append(Paragraph(
        "Documento gerado pelo Sistema ISA — Gestão de Inspeção Fitossanitária de Citros", S['small']))

    doc.build(story)
    return buffer.getvalue()
