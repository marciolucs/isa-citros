from database import (
    get_inspecao_summary, get_fichas_by_inspecao, get_ruas_by_ficha,
    get_inspecoes_by_cliente, get_plantas_inspecionadas,
)


def plantas_inspecionadas(inspecao_id: int, total_plantas: int) -> int:
    """Denominador único de % em todo o sistema: nº de plantas inspecionadas =
    maior número de planta registrado na ficha (fallback: total da quadra).
    Mantém Campo, Relatório e Consolidado com os mesmos percentuais."""
    maxp, _cnt = get_plantas_inspecionadas(inspecao_id)
    return maxp or total_plantas


def calcular_incidencia(plantas_com_praga: int, total_inspecionado: int) -> float:
    if total_inspecionado == 0:
        return 0.0
    return round((plantas_com_praga / total_inspecionado) * 100, 2)


# ── Colunas do relatório consolidado (mesma ordem/agrupamento da aba CONTROLE) ──
# (rótulo, [nomes de praga que compõem a coluna], limiar em fração)
CONSOLIDADO_COLS = [
    ("Ferrugem <10",  ["Ácaro Ferrugem (< 10 ácaros)"],                       0.10),
    ("Ferrugem 10+",  ["Ácaro Ferrugem (10 ou + ácaros)"],                    0.05),
    ("Leprose",       ["Ácaro Leprose"],                                       0.01),
    ("Ác. Branco",    ["Ácaro Branco"],                                        0.05),
    ("Mosca",         ["Mosca das Frutas"],                                    0.05),
    ("Furão",         ["Bicho Furão"],                                         0.05),
    ("Ác. P/M/T",     ["Ácaro Purpúreo", "Ácaro Mexicano", "Ácaro Texano"],   0.10),
    ("Pulgão",        ["Pulgão Verde", "Pulgão Preto"],                        0.10),
    ("Lagarta",       ["Lagarta"],                                             0.05),
    ("Minadora",      ["Minadora das Folhas"],                                 0.10),
    ("Tripes",        ["Tripes"],                                              0.10),
    ("Psilídeo",      ["Psilídeo"],                                            0.01),
    ("Inimigos Nat.", ["Inimigos Naturais"],                                   0.00),
]


def consolidar_propriedade(cliente_id: int) -> list[dict]:
    """Consolida todas as inspeções de uma propriedade em linhas (uma por
    inspeção/quadra), com o % de cada grupo de pragas — espelho da aba CONTROLE.

    Para colunas com várias pragas (ex.: Ác. P/M/T, Pulgão), usa a UNIÃO das
    plantas afetadas: uma planta com qualquer das pragas do grupo conta uma vez.
    """
    inspecoes = get_inspecoes_by_cliente(cliente_id)
    linhas = []
    for insp in inspecoes:
        summary = get_inspecao_summary(insp['id'])
        total = plantas_inspecionadas(insp['id'], insp['total_plantas'])
        # nome da praga -> conjunto de plantas afetadas
        nome_plantas = {d['nome']: d['plantas'] for d in summary.values()}

        cols = []
        for rotulo, nomes, limiar in CONSOLIDADO_COLS:
            union = set()
            for pn in nomes:
                union |= nome_plantas.get(pn, set())
            inc = calcular_incidencia(len(union), total)
            lim_pct = round(limiar * 100, 2)
            cols.append({
                'rotulo': rotulo,
                'valor': inc,
                'limiar': lim_pct,
                'acima': lim_pct > 0 and inc >= lim_pct,
            })

        linhas.append({
            'inspecao_id': insp['id'],
            'quadra': insp['numero_quadra'],
            'variedade': insp['variedade'],
            'data': insp['data_inspecao'],
            'numero_inspecao': insp.get('numero_inspecao', ''),
            'total_inspecionado': total,
            'total_plantas': insp['total_plantas'],
            'cols': cols,
            'tem_alerta': any(c['acima'] for c in cols),
        })
    return linhas


def get_relatorio_pragas(inspecao_id: int, total_inspecionado: int) -> list[dict]:
    summary = get_inspecao_summary(inspecao_id)
    result = []
    for praga_id, data in summary.items():
        count = len(data['plantas'])
        incidencia = calcular_incidencia(count, total_inspecionado)
        limiar_pct = round(data['limiar_acao'] * 100, 1)
        acima = incidencia >= limiar_pct and limiar_pct > 0
        result.append({
            'praga_id': praga_id,
            'nome': data['nome'],
            'categoria': data['categoria'],
            'parte_avaliada': data.get('parte_avaliada', ''),
            'plantas_afetadas': count,
            'incidencia': incidencia,
            'limiar_pct': limiar_pct,
            'acima_limiar': acima,
            'alerta_critico': data['alerta_critico'],
            'sugestao_controle': data['sugestao_controle'],
            'plantas': sorted(data['plantas']),
        })
    return sorted(result, key=lambda x: (-x['incidencia'], x['nome']))


def consolidar_quarentenaria(inspecao_id: int, doenca: str) -> dict:
    fichas = get_fichas_by_inspecao(inspecao_id, doenca=doenca)
    total_vistoriadas = 0
    total_sintomas = 0
    detalhes = []

    for ficha in fichas:
        ruas = get_ruas_by_ficha(ficha['id'])
        ficha_plantas = 0
        ficha_sintomas = 0
        ruas_detalhes = []
        for rua in ruas:
            plantas_rua = rua['total_plantas_rua']
            sintomas_str = rua['plantas_sintomas'].strip()
            if sintomas_str:
                nums = list(set(
                    s.strip() for s in sintomas_str.replace(';', ',').split(',')
                    if s.strip().isdigit()
                ))
                qtd_sintomas = len(nums)
            else:
                qtd_sintomas = 0
            ficha_plantas += plantas_rua
            ficha_sintomas += qtd_sintomas
            ruas_detalhes.append({
                'numero_rua': rua['numero_rua'],
                'direcao': rua['direcao_rua'],
                'total_plantas': plantas_rua,
                'plantas_sintomas': sintomas_str,
                'qtd_sintomas': qtd_sintomas,
            })

        total_vistoriadas += ficha_plantas
        total_sintomas += ficha_sintomas
        detalhes.append({
            'numero_ficha': ficha['numero_ficha'],
            'inspetor': ficha['inspetor'],
            'total_plantas': ficha_plantas,
            'total_sintomas': ficha_sintomas,
            'ruas': ruas_detalhes,
        })

    pct = calcular_incidencia(total_sintomas, total_vistoriadas)
    return {
        'doenca': doenca,
        'total_vistoriadas': total_vistoriadas,
        'total_sintomas': total_sintomas,
        'percentual': pct,
        'fichas': detalhes,
        'notificar': total_sintomas > 0,
    }
