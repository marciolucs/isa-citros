# ISA — Sistema de Inspeção Fitossanitária de Citros

Desenvolvido para **Luciano Costella** — Técnico Agrícola em Agropecuária — CFTA 17893896825

---

## Como Rodar Localmente

### Requisito: Python 3.9 ou superior
Download: https://www.python.org/downloads/

**Opção 1 — Automático (Windows):**
Clique duas vezes em `instalar_e_rodar.bat`

**Opção 2 — Manual:**
```bash
pip install -r requirements.txt
streamlit run app.py
```

Acesse: **http://localhost:8501**

---

## Como Hospedar no Streamlit Cloud (Grátis)

1. Crie conta em https://github.com e faça upload desta pasta como repositório
2. Acesse https://share.streamlit.io
3. Clique em **New app** → selecione o repositório → arquivo: `app.py`
4. Clique **Deploy** — em ~2 minutos o app estará online com link público

> ⚠️ **Nota sobre o banco de dados:** No Streamlit Cloud, o arquivo SQLite
> é criado localmente no servidor e **reset a cada redeploy**.
> Para persistência permanente dos dados, configure o banco no Supabase
> (PostgreSQL gratuito) e substitua a string de conexão em `database.py`.

---

## Módulos do Sistema

| Módulo | Função |
|--------|--------|
| ⚙️ **Painel** | Configura a inspeção: propriedade, quadra, variedade, datas, inspetor |
| 🔍 **Campo** | Ficha digital planta a planta (até 70 plantas) com 16 pragas monitoradas |
| 🦠 **Quarentenárias** | Fichas de Greening e Cancro por rua, multi-inspetor, consolidação automática |
| 📊 **Relatório** | Tabela com % de incidência, alertas visuais, sugestões de controle + PDF |

---

## Pragas Monitoradas e Limiares

| Praga | Limiar | Alerta |
|-------|--------|--------|
| Ácaro Ferrugem (< 10) | 10% | Normal |
| Ácaro Ferrugem (10+)  | 5%  | Normal |
| Ácaro Leprose | 1% | Normal |
| Ácaro Branco | 5% | Normal |
| Ácaro Purpúreo | 10% | Normal |
| Ácaro Mexicano | 10% | Normal |
| Ácaro Texano | 10% | Normal |
| Mosca das Frutas | 5% | Normal |
| Bicho Furão | 5% | Normal |
| Pulgão Verde | 10% | Normal |
| Pulgão Preto | 10% | Normal |
| Lagarta | 5% | Normal |
| Minadora | 10% | Normal |
| Tripes | 10% | Normal |
| **Psilídeo** | **1%** | **🚨 CRÍTICO (vetor do Greening)** |
| Inimigos Naturais | — | Benéfico |
| Greening (HLB) | 0% | 🚨 Quarentenária |
| Cancro Cítrico | 0% | 🚨 Quarentenária |

---

## Estrutura dos Arquivos

```
isa_citros/
├── app.py                    # Página inicial
├── database.py               # Banco SQLite (CRUD)
├── seed_data.py              # Dados de referência
├── calculations.py           # Cálculos de incidência
├── pdf_report.py             # Geração de PDF
├── requirements.txt
├── instalar_e_rodar.bat      # Instalador Windows
├── .streamlit/
│   └── config.toml           # Tema verde
└── pages/
    ├── 1_Painel.py           # Módulo A
    ├── 2_Campo.py            # Módulo B
    ├── 3_Quarentenarias.py   # Módulo B2
    └── 4_Relatorio.py        # Módulo C
```
