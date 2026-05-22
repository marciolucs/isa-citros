from database import get_inspecao_summary, get_fichas_by_inspecao, get_ruas_by_ficha


def calcular_incidencia(plantas_com_praga: int, total_inspecionado: int) -> float:
    if total_inspecionado == 0:
        return 0.0
    return round((plantas_com_praga / total_inspecionado) * 100, 2)


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
