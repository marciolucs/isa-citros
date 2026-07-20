# ISA — Sistema de Inspeção Fitossanitária Citros

**Stack:** Python · Streamlit · SQLite · ReportLab  
**Deploy:** Streamlit Cloud → https://isa-citros-esvpz8q2sb9armaufjx2jz.streamlit.app  
**GitHub:** https://github.com/marciolucs/isa-citros  
**Referência Excel:** `ISAeGUI.xlsm` (Desktop) — aba `Citros ` tem a ficha de campo original

---

## Arquitetura do projeto

```
app.py              # Página inicial: menu 2×2 + inspeções recentes
pages/
  1_Painel.py       # Configura nova inspeção (cliente, quadra, datas, inspetor)
  2_Campo.py        # Ficha de campo: grade pragas × plantas (estilo Excel), 2 modos
  3_Quarentenarias.py # Fichas Greening e Cancro Cítrico (26 ruas, PDF)
  4_Relatorio.py    # Relatório final por quadra em PDF com incidências e observações
  5_Consolidado.py  # Relatório consolidado por propriedade (espelho da aba CONTROLE)
database.py         # SQLite — init_db(), funções CRUD, migrations automáticas
calculations.py     # calcular_incidencia(), plantas_inspecionadas(), get_relatorio_pragas(), consolidar_quarentenaria(), consolidar_propriedade()
pdf_report.py       # gerar_pdf(), gerar_pdf_ficha_campo(), gerar_pdf_ficha_quarentenaria(), gerar_pdf_consolidado()
seed_data.py        # PRAGAS, OBSERVACOES, CLIENTES_QUADRAS — seed() idempotente
requirements.txt    # streamlit, pandas, reportlab, plotly, pillow
```

---

## Banco de dados (SQLite)

Arquivo: `isa_citros.db` (local) ou `$ISA_DB_PATH` (env).

### Tabelas principais

| Tabela | Chave / Unique | Observação |
|--------|---------------|------------|
| `clientes` | `(propriedade, proprietario)` | |
| `quadras` | `(cliente_id, numero_quadra)` | `total_plantas`, `variedade` |
| `pragas` | `nome` | `limiar_acao REAL`, `categoria`, `alerta_critico`, `quarentenaria` |
| `observacoes_biblioteca` | `descricao` | categorias: praga, doenca, dano_abiotico, fisiologico, nutricional, planta_daninha, operacional, geral |
| `inspecoes` | PK | `status`: em_andamento / concluida; campo `ultima_planta` (migration) |
| `inspecao_pragas` | `(inspecao_id, numero_planta, praga_id)` | Presença binária planta×praga |
| `inspecao_observacoes` | PK | Texto livre ou da biblioteca |
| `inspecao_fotos` | PK | BLOB comprimido via Pillow (max 1200×1200 JPEG 75%) |
| `fichas_quarentenarias` | PK | `doenca`: GREENING ou CANCRO |
| `ruas_quarentenarias` | `(ficha_id, numero_rua)` | 26 ruas; `inspetor_rua` (migration) |

### Funções-chave em database.py

```python
init_db()                     # cria tabelas + roda migrations try/except
seed()                        # idempotente: só executa se is_seeded() = False
get_inspecao_by_id(id)        # JOIN clientes+quadras → dict completo
get_inspecao_summary(id)      # → {praga_id: {nome, plantas:set, limiar_acao, ...}}
save_praga_plantas(insp_id, praga_id, [plant_nums])  # substitui todas as plantas da praga
save_rua_quarentenaria(ficha_id, rua_num, direcao, total, sintomas, inspetor)
get_fichas_by_inspecao(id, doenca=None)
get_ruas_by_ficha(ficha_id)
```

### Migrations (no init_db, try/except)
```python
"ALTER TABLE inspecoes ADD COLUMN ultima_planta INTEGER DEFAULT 0"
"ALTER TABLE ruas_quarentenarias ADD COLUMN inspetor_rua TEXT DEFAULT ''"
```

---

## Fluxo de navegação

```
app.py (Início)
  └─ 1_Painel.py    → cria/retoma inspeção, seta st.session_state.inspecao_id
       └─ 2_Campo.py  → grade pragas×plantas, salva inspecao_pragas
            ├─ 3_Quarentenarias.py  → fichas GREENING / CANCRO, 26 ruas, PDF
            └─ 4_Relatorio.py       → PDF geral + download
```

`st.session_state.inspecao_id` é o pivô: todas as páginas param com `st.stop()` se não existir.

---

## Ficha de Campo (2_Campo.py)

Grade inspirada na aba `Citros ` do `ISAeGUI.xlsm`. Estrutura:

| Seção | Pragas (nomes exatos no DB) |
|-------|----------------------------|
| 🔴 ÁCARO FERRUGEM | "Ácaro Ferrugem (< 10 ácaros)", "Ácaro Ferrugem (10 ou + ácaros)" |
| 🟠 ÁCARO LEPROSE | "Ácaro Leprose" |
| 🐛 PRAGAS DIVERSAS | Branco, Mosca, Bicho Furão, Purpúreo, Mexicano, Texano, Pulgão Verde, Pulgão Preto, Lagarta, Minadora das Folhas, Tripes, Psilídeo |
| 🌿 INIMIGOS NATURAIS | "Inimigos Naturais" |

**Dois modos** (radio no topo, key `modo_campo`), editam os mesmos dados (`inspecao_pragas`):
- 📱 **Modo Planta**: escolhe a planta (`num_planta_campo`) e marca pragas por seção; salva com `save_planta_pragas()`. Avanço via `st.session_state['planta_goto']` aplicado no topo antes do widget.
- 📊 **Modo Grade**: uma `st.data_editor` por seção (key `grid_{safe_key}`), colunas `p1..pN` (CheckboxColumn); salva com `save_praga_plantas()`.

Outros: botão PDF (`gerar_pdf_ficha_campo`), Índice de Avaliação (observações por grupo — deduplicadas por `_obs_shown` para não repetir key), fotos.

## Denominador de % (IMPORTANTE — fonte única)

`calculations.plantas_inspecionadas(inspecao_id, total_plantas)` = **maior número de planta registrado** (fallback: total da quadra). Usado em Campo, Relatório (4), Consolidado (5) e nos PDFs — todos mostram o MESMO %. Não usar `get_total_inspecionado` (conta só plantas com praga, infla o %).

---

## Relatório Consolidado (5_Consolidado.py) — espelho da aba CONTROLE

- Usuário escolhe a **propriedade**; `consolidar_propriedade(cliente_id)` gera 1 linha por inspeção/quadra.
- Colunas de praga em `CONSOLIDADO_COLS` (calculations.py) na ordem do Excel. Colunas com várias pragas (Ác. P/M/T, Pulgão) = **união** das plantas afetadas.
- Tabela `st.dataframe` com Styler: célula vermelha quando `% ≥ limiar`.
- PDF paisagem `gerar_pdf_consolidado(cliente, linhas)`.
- Evitar glifos fora da Helvetica no PDF (ex.: usar "10+" em vez de "≥10").

---

## Fichas Quarentenárias (3_Quarentenarias.py)

- Duas tabs: GREENING e CANCRO
- Cada tab: `render_doenca(doenca_key, inspetor_padrao)`
- DataFrame fixo de 26 linhas (ruas) — colunas: Rua, I/V, Sub.Total, Inspetor, Plantas c/ Sintoma, Qtd
- `Qtd` = `contar_sintomas(s)` — conta números separados por vírgula/ponto-vírgula
- PDF gerado por `gerar_pdf_ficha_quarentenaria(inspecao, ficha, ruas, doenca_key)` no pdf_report.py
- Consolidação: soma total_sintomas/total_vistoriadas; notifica se sintomas > 0

---

## Relatório PDF (pdf_report.py)

### gerar_pdf(inspecao) → bytes
- A4 portrait, margens 1.5cm
- Cabeçalho com dados da inspeção
- Tabela de incidências (via `get_relatorio_pragas`)
- Seção de alertas (acima do limiar)
- Observações gerais
- Fotos em grid
- Rodapé com assinatura Luciano Costella

### gerar_pdf_ficha_quarentenaria(inspecao, ficha, ruas, doenca_key) → bytes
- A4 portrait, margens 1.2cm
- 26 linhas de ruas com `repeatRows=1`
- Linhas alternadas `_VERDE_ALT` para ruas V (par)
- Rodapé com HR + assinatura

---

## Seed data (seed_data.py)

**PRAGAS** (16 não-quarentenárias + 2 quarentenárias = 18 total):  
Categorias: `acaro`, `inseto`, `benefico`, `doenca_quarentenaria`

**OBSERVACOES** (~80 itens) — biblioteca de observações pré-definidas

**CLIENTES_QUADRAS** — dados pré-cadastrados de propriedades (FAZENDA SÃO FRANCISCO, RAIO DE SOL, SÍTIO NOVO HORIZONTE, etc.)

---

## Convenções de código

- Streamlit: `st.session_state.inspecao_id` = único estado persistido entre páginas
- DB: sempre `with get_db() as conn` (contextmanager com commit/rollback automático)
- Colunas de planta no DataFrame: string `f'p{n}'` (não inteiro) para evitar conflito com pandas
- CSS inline via `st.markdown(..., unsafe_allow_html=True)`
- Migrations: sempre `try/except` dentro de `init_db()` (SQLite ignora ADD COLUMN duplicado via except)
- `seed()` tem guard `is_seeded()` — verifica se já existe alguma praga no DB

---

## Deploy / operações

```bash
# Rodar local
streamlit run app.py
# ou
python -m streamlit run app.py

# Push para Streamlit Cloud (auto-deploy)
git add <files> && git commit -m "msg" && git push

# Se Streamlit Cloud travar → Manage app → Reboot app
```

**Streamlit Cloud:** lê `requirements.txt`, usa Python 3.11+, DB SQLite em memória efêmera (perde dados ao dormir/reiniciar).

> ⚠️ O banco SQLite em produção é **ephemeral** — dados são perdidos ao reiniciar o app na nuvem. Para persistência real precisaria de Supabase/PostgreSQL.
