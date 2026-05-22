from database import get_db, is_seeded

PRAGAS = [
    # (nome, limiar_acao, categoria, parte_avaliada, alerta_critico, sugestao_controle, quarentenaria)
    (
        "Ácaro Ferrugem (< 10 ácaros)", 0.10, "acaro", "Frutos / Folhas", 0,
        "Aplicar acaricida específico (ex: abamectina, propargite, enxofre). "
        "Monitorar início de safra e desenvolvimento dos frutos. Priorizar aplicação preventiva.",
        0
    ),
    (
        "Ácaro Ferrugem (10 ou + ácaros)", 0.05, "acaro", "Frutos / Folhas", 0,
        "AÇÃO IMEDIATA: Alta infestação. Aplicar acaricida de choque (ex: abamectina + óleo mineral). "
        "Retornar em 7 dias para avaliar reinfestação.",
        0
    ),
    (
        "Ácaro Leprose", 0.01, "acaro", "Frutos / Ramos", 0,
        "AÇÃO PRIORITÁRIA: Ácaro vetor da Leprose Cítrica. Aplicar acaricida específico "
        "(ex: propargite, hexitiazoxi). Eliminar plantas com lesões de leprose avançada. "
        "Notificar se presença acima do limiar.",
        0
    ),
    (
        "Ácaro Branco", 0.05, "acaro", "Frutos / Folhas Novas", 0,
        "Aplicar acaricida para ácaro branco (ex: abamectina, espiromesifeno). "
        "Monitorar vegetações novas. Evitar deficiência hídrica que favorece a praga.",
        0
    ),
    (
        "Ácaro Purpúreo", 0.10, "acaro", "Frutos / Folhas", 0,
        "Aplicar acaricida específico. Monitorar durante florescimento e formação dos frutos.",
        0
    ),
    (
        "Ácaro Mexicano", 0.10, "acaro", "Folhas", 0,
        "Aplicar acaricida (ex: clorfenapir, hexitiazoxi). Monitorar folhas com sintoma de mosqueado.",
        0
    ),
    (
        "Ácaro Texano", 0.10, "acaro", "Frutos / Folhas", 0,
        "Aplicar acaricida específico. Monitorar preferencialmente no período seco.",
        0
    ),
    (
        "Mosca das Frutas", 0.05, "inseto", "Frutos", 0,
        "Aplicar inseticida em isca tóxica (ex: malationa + proteína hidrolisada). "
        "Monitorar armadilhas McPhail semanalmente. Retirar frutos caídos do pomar.",
        0
    ),
    (
        "Bicho Furão", 0.05, "inseto", "Frutos", 0,
        "Aplicar inseticida preventivo no início da frutificação (ex: clorpirifós, lambda-cialotrina). "
        "Retirar e enterrar frutos atacados. Monitorar com armadilhas.",
        0
    ),
    (
        "Pulgão Verde", 0.10, "inseto", "Vegetações Novas", 0,
        "Aplicar inseticida sistêmico nas vegetações novas (ex: imidacloprida, tiametoxam). "
        "Verificar OBRIGATORIAMENTE a presença de Psilídeo nas mesmas vegetações.",
        0
    ),
    (
        "Pulgão Preto", 0.10, "inseto", "Vegetações Novas", 0,
        "Aplicar inseticida sistêmico nas vegetações novas. "
        "Verificar presença de Psilídeo concomitante.",
        0
    ),
    (
        "Lagarta", 0.05, "inseto", "Folhas Novas / Frutos Novos", 0,
        "Aplicar inseticida biológico (ex: Bacillus thuringiensis) ou spinosade nas vegetações novas. "
        "Monitorar folhas enroladas (lagarta enrola-folhas) e folhas mede-palmo.",
        0
    ),
    (
        "Minadora das Folhas", 0.10, "inseto", "Vegetações Novas", 0,
        "Aplicar inseticida sistêmico nas vegetações novas (ex: abamectina, espinosade). "
        "Controlar fluxos de brotação. Eliminar galhos com alta infestação.",
        0
    ),
    (
        "Tripes", 0.10, "inseto", "Flores / Frutos Novos", 0,
        "Aplicar inseticida durante florescimento (ex: espinosade, clorpirifós, acefato). "
        "Monitorar flores e frutos com tamanho de chumbinho. Aplicar nos horários de abertura das flores.",
        0
    ),
    (
        "Psilídeo", 0.01, "inseto", "Vegetações Novas", 1,
        "🚨 ALERTA CRÍTICO — VETOR DO GREENING (HLB)! "
        "Aplicar inseticida sistêmico IMEDIATAMENTE (ex: imidacloprida, tiametoxam, acetamiprido). "
        "Monitorar todas as plantas para sintomas de Greening. "
        "Comunicar ao responsável técnico e à fiscalização agropecuária.",
        0
    ),
    (
        "Inimigos Naturais", 0.00, "benefico", "Vegetações / Frutos", 0,
        "PRESERVAR. Reduzir uso de agroquímicos de amplo espectro. "
        "Presença de inimigos naturais indica equilíbrio biológico — favorece o controle natural de pragas.",
        0
    ),
    # Doenças quarentenárias (não aparecem na ficha de 70 plantas)
    (
        "Greening (HLB)", 0.00, "doenca_quarentenaria", "Planta inteira", 1,
        "🚨 DOENÇA QUARENTENÁRIA — NOTIFICAÇÃO OBRIGATÓRIA! "
        "Erradicação imediata das plantas suspeitas. Controle intensivo do Psilídeo. "
        "Notificar Defesa Agropecuária estadual.",
        1
    ),
    (
        "Cancro Cítrico", 0.00, "doenca_quarentenaria", "Frutos / Folhas / Ramos", 1,
        "🚨 DOENÇA QUARENTENÁRIA — NOTIFICAÇÃO OBRIGATÓRIA! "
        "Erradicação de plantas afetadas e raio de 30m. "
        "Destruição por fogo. Notificar Defesa Agropecuária estadual imediatamente.",
        1
    ),
]

OBSERVACOES = [
    ("FORMIGAS QUEM QUEM", "praga"),
    ("FORMIGAS SAÚVA", "praga"),
    ("FRUTOS QUEIMADOS", "dano_abiotico"),
    ("FOLHAS QUEIMADAS", "dano_abiotico"),
    ("PLANTAS COM SUSPEITA DE GREENING", "doenca"),
    ("PLANTAS COM SUSPEITA DE CANCRO", "doenca"),
    ("PLANTAS COM BROCAS NO TRONCO", "praga"),
    ("PLANTAS COM CIPÓ", "planta_daninha"),
    ("PLANTAS COM SUSPEITA DE GOMOSE", "doenca"),
    ("PLANTAS COM BROTOS NO TRONCO", "fisiologico"),
    ("VEGETAÇÕES NOVAS COM ARAPUÁS", "praga"),
    ("FRUTOS COM COCHONILHA ESCAMA VÍRGULA", "praga"),
    ("FRUTOS COM MANCHAS DE FERRUGEM", "praga"),
    ("FRUTOS COM COCHONILHAS BRANCAS NO PEDÚNCULO", "praga"),
    ("RAMOS COM RUBELOSE", "doenca"),
    ("VEGETAÇÕES NOVAS COM MOSCA BRANCA COTONOSA", "praga"),
    ("FOLHAS COM BESOUROS PANTOMORUS", "praga"),
    ("VEGETAÇÕES NOVAS COM OVOS E NINFAS DE PSILÍDEO", "praga"),
    ("VEGETAÇÕES NOVAS COM NINFAS DE PSILÍDEO", "praga"),
    ("FOLHAS COM SUSPEITA DE MELANOSE", "doenca"),
    ("PLANTAS COM SUSPEITA DE AMARELINHO (CVC)", "doenca"),
    ("FRUTOS COM SINTOMAS DE PINTA PRETA", "doenca"),
    ("COTONETES E FLORES COM PODRIDÃO FLORAL (ESTRELINHA)", "doenca"),
    ("FRUTOS COM MANCHAS DE LEPROSE", "doenca"),
    ("RAMOS COM MANCHAS DE LEPROSE", "doenca"),
    ("FOLHAS COM MANCHA GRAXA", "doenca"),
    ("FOLHAS COM FUMAGINA", "doenca"),
    ("FRUTOS COM FUMAGINA", "doenca"),
    ("PLANTAS COM SUSPEITA DE DEFICIÊNCIAS NUTRICIONAIS", "nutricional"),
    ("FRUTOS COM MANCHAS DE TRIPES", "praga"),
    ("PLANTAS COM CHUMBINHOS", "fisiologico"),
    ("FLORADA COM BESOURO DA GOIABA", "praga"),
    ("PLANTAS COM CARAMUJOS", "praga"),
    ("FLORADA COM VAQUINHAS", "praga"),
    ("VEGETAÇÕES NOVAS COM SINTOMAS DE ALTERNÁRIAS", "doenca"),
    ("FRUTOS COM SINTOMAS DE ALTERNÁRIAS", "doenca"),
    ("FOLHAS MOSQUEADAS POR ÁCARO MEXICANO", "praga"),
    ("FRUTOS MOSQUEADOS POR ÁCARO MEXICANO", "praga"),
    ("FOLHAS MOSQUEADAS POR ÁCARO PURPÚREO", "praga"),
    ("FRUTOS MOSQUEADOS POR ÁCARO PURPÚREO", "praga"),
    ("FOLHAS MOSQUEADAS POR ÁCARO TEXANO", "praga"),
    ("FRUTOS MOSQUEADOS POR ÁCARO TEXANO", "praga"),
    ("FRUTOS COM COCHONILHA CABEÇA DE PREGO", "praga"),
    ("PLANTAS COM COCHONILHA ESCAMA FARINHA", "praga"),
    ("PLANTAS E FRUTOS COM COCHONILHA ESCAMA FARINHA", "praga"),
    ("FRUTOS COM COCHONILHA ESCAMA LIXA", "praga"),
    ("FRUTOS COM MANCHAS DE ÁCARO BRANCO", "praga"),
    ("PLANTAS COM BOTÕES, COTONETES E FLORES", "fisiologico"),
    ("OVOS DE ÁCARO PURPÚREO", "praga"),
    ("OVOS DE ÁCARO TEXANO", "praga"),
    ("OVOS DE ÁCARO MEXICANO", "praga"),
    ("OVOS DE ÁCARO BRANCO", "praga"),
    ("FRUTOS COM SUSPEITA DE MELANOSE", "doenca"),
    ("VEGETAÇÕES NOVAS COM MOSCA BRANCA", "praga"),
    ("FRUTOS COM COCHONILHA PARLATÓRIA PEDÚNCULO", "praga"),
    ("FRUTOS RACHADOS", "dano_abiotico"),
    ("CHUMBINHOS COM PODRIDÃO FLORAL (ESTRELINHA)", "doenca"),
    ("FOLHAS NOVAS COM LAGARTA ENROLA FOLHAS", "praga"),
    ("FOLHAS NOVAS COM LAGARTA MEDE-PALMO", "praga"),
    ("PLANTAS COM BARRADOS QUEIMADOS", "dano_abiotico"),
    ("PLANTAS COM FRUTOS CAÍDOS NO CHÃO", "fisiologico"),
    ("FRUTOS COM COCHONILHA VERDE", "praga"),
    ("FRUTOS E FOLHAS COM COCHONILHA PARDINHA", "praga"),
    ("VERRUGOSE FRUTO E FOLHA", "doenca"),
    ("FOLHAS DANIFICADAS", "dano_abiotico"),
    ("FRUTOS COM FUNGO", "doenca"),
    ("FRUTOS E FOLHAS QUEIMADOS (GEADA)", "dano_abiotico"),
    ("FRUTOS E FOLHAS DANIFICADOS POR CHUVA DE PEDRA", "dano_abiotico"),
    ("FRUTOS E FOLHAS DANIFICADOS POR DANOS MECÂNICOS", "dano_abiotico"),
    ("VEGETAÇÃO NOVA DANIFICADA", "dano_abiotico"),
    ("NÃO INSPECIONEI FRUTOS DA SAFRA - ESTÃO COLHENDO", "operacional"),
    ("FERRUGEM NOS FRUTOS INTERNO DAS PLANTAS", "praga"),
    ("FERRUGEM NOS FRUTOS DAS PENCAS", "praga"),
    ("PRESENÇA DE ÁCAROS DA LEPROSE", "praga"),
    ("PRESENÇA DE ÁCAROS DA FERRUGEM", "praga"),
    ("% ALTA DE FRUTOS COM MANCHA DE ÁCARO BRANCO", "praga"),
    ("% ALTA DE FRUTOS E FOLHAS C/ COCHONILHA BRANCA DO PEDÚNCULO", "praga"),
    ("% ALTA DE FRUTOS RAMOS E FOLHAS COM COCHONILHAS PARDINHA", "praga"),
    ("FERRUGEM NAS PLANTAS NA BEIRADA DO CARRIADOR", "praga"),
    ("VEGETAÇÃO NOVA C/ COCHONILHA BRANCA DO PEDÚNCULO", "praga"),
    ("NÃO FORAM ENCONTRADAS PLANTAS COM CANCRO CÍTRICO", "doenca"),
    ("FRUTOS COM COCHONILHA ESCAMA LONGA", "praga"),
    ("FRUTOS E FOLHAS COM COCHONILHA PARDINHA", "praga"),
    ("PRESENÇA DE MOSCA DAS FRUTAS (INSETO ADULTO)", "praga"),
    ("PLANTAS COM SUSPEITA DE DEFICIÊNCIA DE ZINCO", "nutricional"),
    ("PLANTAS COM SUSPEITA DE DEFICIÊNCIA DE BORO", "nutricional"),
    ("PLANTAS COM SUSPEITA DE DEFICIÊNCIA DE MAGNÉSIO", "nutricional"),
]

CLIENTES_QUADRAS = [
    {
        "propriedade": "FAZENDA SÃO FRANCISCO",
        "proprietario": "EDUARDO SEGEREM",
        "municipio": "AGUAÍ",
        "estado": "SP",
        "quadras": [
            ("1", 40, "LIMA CASA"),
            ("2", 65, "P.NATAL"),
            ("3", 50, "PERA RIO GS2000"),
            ("4", 40, "FOLHA MURCHA DA GRANJA"),
            ("5", 35, "WESTIN DO ESCRITÓRIO"),
            ("7", 40, "CHARMUTE"),
            ("8", 70, "PERA BARRACÃO"),
            ("9", 45, "NATAL IRRIGAÇÃO"),
            ("10", 15, "WESTIN 2 ALQUEIRES"),
            ("11", 40, "BAIA VERDE S.S"),
        ]
    },
    {
        "propriedade": "FAZENDA INVERNADA E QUILOMBO",
        "proprietario": "EDUARDO SEGEREM",
        "municipio": "AGUAÍ",
        "estado": "SP",
        "quadras": [
            ("12", 70, "WESTIN SAARA"),
            ("13", 70, "WESTIN SAARA"),
            ("14", 35, "BAIANINHA"),
            ("15", 40, "LIMA FORTE"),
            ("17A", 70, "LIMÃO SICILIANO"),
            ("17B", 70, "LIMÃO SICILIANO"),
            ("19", 20, "LIMÃO TAHITI"),
            ("20", 60, "BAIANINHA 2018"),
        ]
    },
    {
        "propriedade": "FAZENDA SÃO DOMINGOS",
        "proprietario": "N.C.M SIMONETTI",
        "municipio": "AGUAÍ",
        "estado": "SP",
        "quadras": [
            ("1", 35, "PERA IAC"),
            ("2", 50, "PERA IAC"),
            ("3", 15, "PERA IAC"),
            ("4", 25, "PERA IAC"),
            ("5", 50, "VALÊNCIA"),
            ("6", 50, "VALÊNCIA"),
            ("7", 35, "VALÊNCIA"),
            ("8", 40, "MURCOTE"),
            ("9", 25, "PERA NATAL DO ADILSON"),
            ("10", 25, "NATAL CAIXA"),
            ("11", 45, "PERA NATAL"),
            ("12", 15, "FOLHA MURCHA"),
            ("13", 25, "PERA NATAL NOVA"),
            ("14", 25, "VALÊNCIA"),
            ("15", 15, "VALÊNCIA"),
            ("16", 30, "PERA NATAL"),
            ("17", 30, "VALÊNCIA"),
            ("18", 15, "PERA MURCHA"),
            ("19", 40, "MURCOTE"),
            ("20", 20, "LIMA MARAVILHA"),
            ("21", 50, "PERA NATAL"),
        ]
    },
    {
        "propriedade": "RAIO DE SOL",
        "proprietario": "N.C.M SIMONETTI",
        "municipio": "MOGI GUAÇU",
        "estado": "SP",
        "quadras": [
            ("1", 60, "PERA IAC"),
            ("2", 40, "PERA IAC"),
            ("3", 45, "PERA IAC"),
            ("4", 35, "MURCOTE"),
            ("5", 50, "WESTIN"),
            ("6", 30, "MURCOTE"),
            ("7", 50, "LIMA VERDE"),
            ("8", 65, "PERA IAC"),
            ("9", 45, "PERA IAC"),
            ("10", 50, "FOLHA MURCHA"),
            ("11", 70, "PEA NATAL"),
            ("12", 20, "PERA NATAL"),
            ("13", 60, "MURCOTE"),
            ("14", 40, "PERA IAC"),
            ("15", 40, "BAIANINHA"),
            ("16", 40, "PERA 7 LAGOAS"),
            ("17", 40, "PERA IAC"),
            ("18", 70, "PERA IAC"),
            ("19", 45, "PERA IAC"),
            ("20", 40, "PERA IAC"),
            ("21", 40, "FOLHA MURCHA"),
            ("22", 60, "PERA IAC"),
            ("23", 60, "PERA IAC"),
        ]
    },
    {
        "propriedade": "FAZENDA SÃO JOSÉ",
        "proprietario": "N.C.M SIMONETTI",
        "municipio": "MOGI GUAÇU",
        "estado": "SP",
        "quadras": [
            ("1", 35, "WESTIN"),
            ("2", 25, "WESTIN"),
            ("3", 35, "CHARMUTE"),
            ("4", 40, "CHARMUTE"),
            ("5", 60, "CHARMUTE"),
            ("6", 15, "WESTIN"),
            ("7", 20, "WESTIN"),
            ("8", 30, "M.MURCOTE"),
            ("9", 30, "M.MURCOTE"),
            ("10", 60, "M.MURCOTE"),
            ("11", 30, "M.MURCOTE"),
            ("12", 65, "LIMA VERDE"),
            ("13", 20, "BAIANINHA"),
            ("14", 15, "P.IAC"),
        ]
    },
    {
        "propriedade": "FAZENDA MODELO",
        "proprietario": "N.C.M SIMONETTI",
        "municipio": "MOGI GUAÇU",
        "estado": "SP",
        "quadras": [
            ("1", 50, "PERA IAC"),
            ("2", 50, "PERA IAC"),
            ("3", 50, "VALÊNCIA"),
        ]
    },
    {
        "propriedade": "SÍTIO SANTA ISABEL",
        "proprietario": "ANTÔNIO HERMES BRUNO",
        "municipio": "MOGI MIRIM",
        "estado": "SP",
        "quadras": [
            ("1", 50, "LIMA MARAVILHA"),
            ("2", 50, "LIMA MARAVILHA"),
        ]
    },
    {
        "propriedade": "SÍTIO SANTO ANTÔNIO",
        "proprietario": "ANTÔNIO HERMES BRUNO",
        "municipio": "MOGI MIRIM",
        "estado": "SP",
        "quadras": [
            ("1", 50, "VALÊNCIA"),
        ]
    },
    {
        "propriedade": "SÍTIO LAGOA DOS PATOS",
        "proprietario": "ANDREY",
        "municipio": "MOGI GUAÇU",
        "estado": "SP",
        "quadras": [
            ("1", 70, "M.MURCOTE"),
            ("2", 70, "M.MURCOTE"),
            ("3", 70, "P.IAC"),
            ("4", 70, "P.IAC"),
            ("5", 70, "P.MURCHA"),
        ]
    },
    {
        "propriedade": "SÍTIO SÃO PEDRO",
        "proprietario": "ANDREY",
        "municipio": "MOGI GUAÇU",
        "estado": "SP",
        "quadras": [
            ("1", 70, "LIMA MARAVILHA"),
            ("2", 70, "P.NATAL"),
        ]
    },
    {
        "propriedade": "SÍTIO N.S DE FÁTIMA",
        "proprietario": "OSVALDO MILANEZI",
        "municipio": "CAMPESTRE",
        "estado": "MG",
        "quadras": [
            ("1", 60, "LIMA MARAVILHA"),
            ("2", 60, "LIMA MARAVILHA"),
        ]
    },
    {
        "propriedade": "SÍTIO SÃO PAULO",
        "proprietario": "OSVALDO MILANEZI",
        "municipio": "CAMPESTRE",
        "estado": "MG",
        "quadras": [
            ("1", 70, "LIMA MARAVILHA"),
        ]
    },
    {
        "propriedade": "SÍTIO ALEGRIA",
        "proprietario": "OSVALDO MILANEZI",
        "municipio": "CAMPESTRE",
        "estado": "MG",
        "quadras": [
            ("6", 207, "LIMA MARAVILHA"),
            ("7", 150, "LIMA MARAVILHA"),
        ]
    },
    {
        "propriedade": "SÍTIO DOIS IRMÃOS",
        "proprietario": "OSVALDO MILANEZI",
        "municipio": "CAMPESTRE",
        "estado": "MG",
        "quadras": [
            ("1", 70, "LIMA MARAVILHA"),
            ("2", 70, "LIMA MARAVILHA"),
        ]
    },
    {
        "propriedade": "SÍTIO NOVO HORIZONTE",
        "proprietario": "OSVALDO MILANEZI",
        "municipio": "CAMPESTRE",
        "estado": "MG",
        "quadras": [
            ("1", 60, "P.RIO"),
            ("2", 60, "P.RIO"),
            ("3", 60, "M.MURCOTE"),
            ("4", 70, "M.MURCOTE"),
            ("5", 40, "M.MURCOTE"),
            ("6", 100, "P.IAC"),
            ("7", 70, "P.MURCHA"),
            ("8", 100, "M.MURCOTE"),
            ("9", 70, "P.RIO"),
            ("10", 40, "LIMA"),
            ("11", 40, "LIMA"),
            ("12", 40, "LIMA"),
            ("13", 50, "P.RIO/LIMA"),
            ("14", 40, "P.RIO"),
        ]
    },
    {
        "propriedade": "FAZENDA BOA ESPERANÇA",
        "proprietario": "OSVALDO MILANEZI",
        "municipio": "CAMPESTRE",
        "estado": "MG",
        "quadras": [
            ("1", 70, "LIMA MARAVILHA"),
            ("2", 70, "VALÊNCIA"),
        ]
    },
    {
        "propriedade": "SÍTIO CHAPADÃO",
        "proprietario": "RODRIGO BENVENUTO",
        "municipio": "CASA BRANCA",
        "estado": "SP",
        "quadras": [
            ("1", 50, "VALÊNCIA"),
            ("2", 50, "VALÊNCIA"),
        ]
    },
    {
        "propriedade": "SÍTIO SÃO SEBASTIÃO",
        "proprietario": "RODRIGO BENVENUTO",
        "municipio": "CASA BRANCA",
        "estado": "SP",
        "quadras": [
            ("1", 70, "VALÊNCIA"),
        ]
    },
    {
        "propriedade": "SÍTIO NOVO",
        "proprietario": "RODRIGO BENVENUTO",
        "municipio": "CASA BRANCA",
        "estado": "SP",
        "quadras": [
            ("1", 60, "VALÊNCIA"),
        ]
    },
    {
        "propriedade": "FAZENDA SÃO RAFAEL",
        "proprietario": "ROBERTA Q ADAMO",
        "municipio": "SANTO ANTÔNIO DE POSSE",
        "estado": "SP",
        "quadras": [
            ("1", 50, "VALÊNCIA"),
            ("2", 50, "LIMA MARAVILHA"),
        ]
    },
    {
        "propriedade": "FZD SÃO JOSÉ",
        "proprietario": "CRISTINA SIMONETTI",
        "municipio": "MOGI GUAÇU",
        "estado": "SP",
        "quadras": [
            ("1", 50, "WESTIN"),
            ("2", 50, "M.MURCOTE"),
        ]
    },
]


def seed():
    if is_seeded():
        return

    with get_db() as conn:
        # Pragas
        for praga in PRAGAS:
            conn.execute(
                """INSERT OR IGNORE INTO pragas
                   (nome, limiar_acao, categoria, parte_avaliada, alerta_critico, sugestao_controle, quarentenaria)
                   VALUES (?,?,?,?,?,?,?)""",
                praga
            )

        # Observações
        for obs in OBSERVACOES:
            conn.execute(
                "INSERT OR IGNORE INTO observacoes_biblioteca (descricao, categoria) VALUES (?,?)",
                obs
            )

        # Clientes e Quadras
        for entry in CLIENTES_QUADRAS:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO clientes (propriedade, proprietario, municipio, estado) VALUES (?,?,?,?)",
                (entry["propriedade"], entry["proprietario"], entry["municipio"], entry["estado"])
            )
            cliente_id = cursor.lastrowid
            if cliente_id == 0:
                row = conn.execute(
                    "SELECT id FROM clientes WHERE propriedade=? AND proprietario=?",
                    (entry["propriedade"], entry["proprietario"])
                ).fetchone()
                cliente_id = row["id"]

            for numero_quadra, total_plantas, variedade in entry["quadras"]:
                conn.execute(
                    "INSERT OR IGNORE INTO quadras (cliente_id, numero_quadra, total_plantas, variedade) VALUES (?,?,?,?)",
                    (cliente_id, numero_quadra, total_plantas, variedade)
                )
