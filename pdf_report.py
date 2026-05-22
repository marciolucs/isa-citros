from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from calculations import get_relatorio_pragas, consolidar_quarentenaria
from database import get_observacoes_inspecao, get_fotos_by_inspecao, get_total_inspecionado

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
    total_inspecionado = get_total_inspecionado(inspecao_id)
    if total_inspecionado == 0:
        total_inspecionado = total_plantas

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
