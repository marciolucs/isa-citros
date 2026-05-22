import sqlite3
import os
from contextlib import contextmanager
from io import BytesIO

DB_PATH = os.environ.get("ISA_DB_PATH", "isa_citros.db")


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                propriedade TEXT NOT NULL,
                proprietario TEXT NOT NULL,
                municipio TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'SP',
                UNIQUE(propriedade, proprietario)
            );

            CREATE TABLE IF NOT EXISTS quadras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL REFERENCES clientes(id),
                numero_quadra TEXT NOT NULL,
                total_plantas INTEGER NOT NULL DEFAULT 70,
                variedade TEXT NOT NULL,
                UNIQUE(cliente_id, numero_quadra)
            );

            CREATE TABLE IF NOT EXISTS pragas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                limiar_acao REAL NOT NULL DEFAULT 0.10,
                categoria TEXT NOT NULL DEFAULT 'inseto',
                parte_avaliada TEXT DEFAULT '',
                alerta_critico INTEGER DEFAULT 0,
                sugestao_controle TEXT DEFAULT '',
                quarentenaria INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS observacoes_biblioteca (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL UNIQUE,
                categoria TEXT DEFAULT 'geral'
            );

            CREATE TABLE IF NOT EXISTS inspecoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL REFERENCES clientes(id),
                quadra_id INTEGER NOT NULL REFERENCES quadras(id),
                numero_inspecao TEXT DEFAULT '',
                inspetor TEXT NOT NULL,
                data_inspecao TEXT NOT NULL,
                proxima_inspecao TEXT DEFAULT '',
                inicio_inspecao TEXT DEFAULT '',
                direcao TEXT DEFAULT 'De Cima para Baixo',
                status TEXT DEFAULT 'em_andamento',
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS inspecao_pragas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspecao_id INTEGER NOT NULL REFERENCES inspecoes(id),
                numero_planta INTEGER NOT NULL,
                praga_id INTEGER NOT NULL REFERENCES pragas(id),
                UNIQUE(inspecao_id, numero_planta, praga_id)
            );

            CREATE TABLE IF NOT EXISTS fichas_quarentenarias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspecao_id INTEGER NOT NULL REFERENCES inspecoes(id),
                doenca TEXT NOT NULL,
                inspetor TEXT NOT NULL,
                numero_ficha TEXT DEFAULT 'FICHA 01',
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS ruas_quarentenarias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ficha_id INTEGER NOT NULL REFERENCES fichas_quarentenarias(id),
                numero_rua INTEGER NOT NULL,
                direcao_rua TEXT DEFAULT 'I',
                total_plantas_rua INTEGER DEFAULT 0,
                plantas_sintomas TEXT DEFAULT '',
                UNIQUE(ficha_id, numero_rua)
            );

            CREATE TABLE IF NOT EXISTS inspecao_observacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspecao_id INTEGER NOT NULL REFERENCES inspecoes(id),
                texto TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS inspecao_fotos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspecao_id INTEGER NOT NULL REFERENCES inspecoes(id),
                numero_planta INTEGER,
                foto_data BLOB NOT NULL,
                foto_nome TEXT DEFAULT 'foto.jpg',
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            );
        """)

        # Migrations for existing databases
        for migration in [
            "ALTER TABLE inspecoes ADD COLUMN ultima_planta INTEGER DEFAULT 0",
            "ALTER TABLE ruas_quarentenarias ADD COLUMN inspetor_rua TEXT DEFAULT ''",
        ]:
            try:
                conn.execute(migration)
            except Exception:
                pass


# ── Clientes ──────────────────────────────────────────────────────────────────

def get_clientes():
    with get_db() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM clientes ORDER BY propriedade"
        ).fetchall()]


def add_cliente(propriedade, proprietario, municipio, estado):
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO clientes (propriedade, proprietario, municipio, estado) VALUES (?,?,?,?)",
            (propriedade.upper(), proprietario.upper(), municipio.upper(), estado.upper())
        )


def get_cliente_by_id(cliente_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM clientes WHERE id=?", (cliente_id,)).fetchone()
        return dict(row) if row else None


# ── Quadras ───────────────────────────────────────────────────────────────────

def get_quadras_by_cliente(cliente_id):
    with get_db() as conn:
        return [dict(r) for r in conn.execute(
            """SELECT * FROM quadras WHERE cliente_id=?
               ORDER BY CAST(numero_quadra AS INTEGER), numero_quadra""",
            (cliente_id,)
        ).fetchall()]


def get_quadra_by_id(quadra_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM quadras WHERE id=?", (quadra_id,)).fetchone()
        return dict(row) if row else None


def add_quadra(cliente_id, numero_quadra, total_plantas, variedade):
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO quadras (cliente_id, numero_quadra, total_plantas, variedade) VALUES (?,?,?,?)",
            (cliente_id, str(numero_quadra), int(total_plantas), variedade.upper())
        )


def update_quadra(quadra_id, total_plantas, variedade):
    with get_db() as conn:
        conn.execute(
            "UPDATE quadras SET total_plantas=?, variedade=? WHERE id=?",
            (int(total_plantas), variedade.upper(), quadra_id)
        )


# ── Pragas ────────────────────────────────────────────────────────────────────

def get_pragas():
    with get_db() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM pragas WHERE quarentenaria=0 ORDER BY categoria, nome"
        ).fetchall()]


def get_pragas_dict():
    return {p['id']: p for p in get_pragas()}


# ── Observações ───────────────────────────────────────────────────────────────

def get_observacoes_biblioteca():
    with get_db() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM observacoes_biblioteca ORDER BY categoria, descricao"
        ).fetchall()]


# ── Inspeções ─────────────────────────────────────────────────────────────────

def create_inspecao(cliente_id, quadra_id, numero_inspecao, inspetor,
                    data_inspecao, proxima_inspecao, inicio_inspecao, direcao):
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO inspecoes
               (cliente_id, quadra_id, numero_inspecao, inspetor, data_inspecao,
                proxima_inspecao, inicio_inspecao, direcao)
               VALUES (?,?,?,?,?,?,?,?)""",
            (cliente_id, quadra_id, numero_inspecao, inspetor, data_inspecao,
             proxima_inspecao, inicio_inspecao, direcao)
        )
        return cursor.lastrowid


def get_inspecao_by_id(inspecao_id):
    with get_db() as conn:
        row = conn.execute(
            """SELECT i.*, c.propriedade, c.proprietario, c.municipio, c.estado,
                      q.numero_quadra, q.total_plantas, q.variedade
               FROM inspecoes i
               JOIN clientes c ON i.cliente_id = c.id
               JOIN quadras q ON i.quadra_id = q.id
               WHERE i.id=?""",
            (inspecao_id,)
        ).fetchone()
        return dict(row) if row else None


def get_inspecoes_recentes(limit=30):
    with get_db() as conn:
        return [dict(r) for r in conn.execute(
            """SELECT i.*, c.propriedade, c.proprietario, q.numero_quadra, q.variedade
               FROM inspecoes i
               JOIN clientes c ON i.cliente_id = c.id
               JOIN quadras q ON i.quadra_id = q.id
               ORDER BY i.created_at DESC LIMIT ?""",
            (limit,)
        ).fetchall()]


def finalize_inspecao(inspecao_id):
    with get_db() as conn:
        conn.execute("UPDATE inspecoes SET status='concluida' WHERE id=?", (inspecao_id,))


def update_ultima_planta(inspecao_id, numero_planta):
    with get_db() as conn:
        conn.execute(
            "UPDATE inspecoes SET ultima_planta=MAX(COALESCE(ultima_planta,0),?) WHERE id=?",
            (numero_planta, inspecao_id)
        )


def get_total_inspecionado(inspecao_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(DISTINCT numero_planta) as cnt FROM inspecao_pragas WHERE inspecao_id=?",
            (inspecao_id,)
        ).fetchone()
        return row['cnt'] or 0


# ── Plantas / Pragas ──────────────────────────────────────────────────────────

def save_planta_pragas(inspecao_id, numero_planta, praga_ids):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM inspecao_pragas WHERE inspecao_id=? AND numero_planta=?",
            (inspecao_id, numero_planta)
        )
        for praga_id in praga_ids:
            conn.execute(
                "INSERT OR IGNORE INTO inspecao_pragas (inspecao_id, numero_planta, praga_id) VALUES (?,?,?)",
                (inspecao_id, int(numero_planta), int(praga_id))
            )


def get_planta_pragas(inspecao_id, numero_planta):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT praga_id FROM inspecao_pragas WHERE inspecao_id=? AND numero_planta=?",
            (inspecao_id, numero_planta)
        ).fetchall()
        return [r['praga_id'] for r in rows]


def get_plantas_inspecionadas(inspecao_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT MAX(numero_planta) as maxp, COUNT(DISTINCT numero_planta) as cnt FROM inspecao_pragas WHERE inspecao_id=?",
            (inspecao_id,)
        ).fetchone()
        return row['maxp'] or 0, row['cnt'] or 0


def get_inspecao_summary(inspecao_id):
    with get_db() as conn:
        rows = conn.execute(
            """SELECT ip.praga_id, ip.numero_planta, p.nome, p.limiar_acao,
                      p.alerta_critico, p.sugestao_controle, p.categoria, p.parte_avaliada
               FROM inspecao_pragas ip
               JOIN pragas p ON ip.praga_id = p.id
               WHERE ip.inspecao_id=?""",
            (inspecao_id,)
        ).fetchall()

    summary = {}
    for row in rows:
        pid = row['praga_id']
        if pid not in summary:
            summary[pid] = {
                'nome': row['nome'],
                'limiar_acao': row['limiar_acao'],
                'alerta_critico': bool(row['alerta_critico']),
                'sugestao_controle': row['sugestao_controle'],
                'categoria': row['categoria'],
                'parte_avaliada': row['parte_avaliada'] or '',
                'plantas': set()
            }
        summary[pid]['plantas'].add(row['numero_planta'])
    return summary


# ── Fotos ─────────────────────────────────────────────────────────────────────

def save_foto(inspecao_id, numero_planta, foto_bytes, foto_nome='foto.jpg'):
    try:
        from PIL import Image
        img = Image.open(BytesIO(foto_bytes))
        img.thumbnail((1200, 1200), Image.LANCZOS)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        buf = BytesIO()
        img.save(buf, format='JPEG', quality=75, optimize=True)
        foto_bytes = buf.getvalue()
    except Exception:
        pass

    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO inspecao_fotos (inspecao_id, numero_planta, foto_data, foto_nome) VALUES (?,?,?,?)",
            (inspecao_id, numero_planta, foto_bytes, foto_nome)
        )
        return cursor.lastrowid


def get_fotos_by_planta(inspecao_id, numero_planta):
    with get_db() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, foto_nome, created_at FROM inspecao_fotos WHERE inspecao_id=? AND numero_planta=? ORDER BY id",
            (inspecao_id, numero_planta)
        ).fetchall()]


def get_foto_data(foto_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT foto_data, foto_nome FROM inspecao_fotos WHERE id=?",
            (foto_id,)
        ).fetchone()
        return dict(row) if row else None


def get_fotos_by_inspecao(inspecao_id):
    with get_db() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, numero_planta, foto_nome, foto_data, created_at FROM inspecao_fotos WHERE inspecao_id=? ORDER BY numero_planta, id",
            (inspecao_id,)
        ).fetchall()]


def delete_foto(foto_id):
    with get_db() as conn:
        conn.execute("DELETE FROM inspecao_fotos WHERE id=?", (foto_id,))


# ── Fichas Quarentenárias ─────────────────────────────────────────────────────

def create_ficha_quarentenaria(inspecao_id, doenca, inspetor, numero_ficha):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO fichas_quarentenarias (inspecao_id, doenca, inspetor, numero_ficha) VALUES (?,?,?,?)",
            (inspecao_id, doenca, inspetor, numero_ficha)
        )
        return cursor.lastrowid


def get_fichas_by_inspecao(inspecao_id, doenca=None):
    with get_db() as conn:
        if doenca:
            q = "SELECT * FROM fichas_quarentenarias WHERE inspecao_id=? AND doenca=? ORDER BY created_at"
            p = (inspecao_id, doenca)
        else:
            q = "SELECT * FROM fichas_quarentenarias WHERE inspecao_id=? ORDER BY created_at"
            p = (inspecao_id,)
        return [dict(r) for r in conn.execute(q, p).fetchall()]


def save_rua_quarentenaria(ficha_id, numero_rua, direcao_rua, total_plantas, plantas_sintomas, inspetor_rua=''):
    with get_db() as conn:
        conn.execute(
            """INSERT INTO ruas_quarentenarias
               (ficha_id, numero_rua, direcao_rua, total_plantas_rua, plantas_sintomas, inspetor_rua)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(ficha_id, numero_rua) DO UPDATE SET
                   direcao_rua=excluded.direcao_rua,
                   total_plantas_rua=excluded.total_plantas_rua,
                   plantas_sintomas=excluded.plantas_sintomas,
                   inspetor_rua=excluded.inspetor_rua""",
            (ficha_id, numero_rua, direcao_rua, int(total_plantas), plantas_sintomas, inspetor_rua)
        )


def delete_rua_quarentenaria(ficha_id, numero_rua):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM ruas_quarentenarias WHERE ficha_id=? AND numero_rua=?",
            (ficha_id, numero_rua)
        )


def get_ruas_by_ficha(ficha_id):
    with get_db() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM ruas_quarentenarias WHERE ficha_id=? ORDER BY numero_rua",
            (ficha_id,)
        ).fetchall()]


def delete_ficha_quarentenaria(ficha_id):
    with get_db() as conn:
        conn.execute("DELETE FROM ruas_quarentenarias WHERE ficha_id=?", (ficha_id,))
        conn.execute("DELETE FROM fichas_quarentenarias WHERE id=?", (ficha_id,))


# ── Observações da Inspeção ───────────────────────────────────────────────────

def save_observacoes_inspecao(inspecao_id, textos):
    with get_db() as conn:
        conn.execute("DELETE FROM inspecao_observacoes WHERE inspecao_id=?", (inspecao_id,))
        for texto in textos:
            if texto.strip():
                conn.execute(
                    "INSERT INTO inspecao_observacoes (inspecao_id, texto) VALUES (?,?)",
                    (inspecao_id, texto.strip())
                )


def get_observacoes_inspecao(inspecao_id):
    with get_db() as conn:
        return [r['texto'] for r in conn.execute(
            "SELECT texto FROM inspecao_observacoes WHERE inspecao_id=? ORDER BY id",
            (inspecao_id,)
        ).fetchall()]


# ── Seed check ────────────────────────────────────────────────────────────────

def is_seeded():
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) as c FROM pragas").fetchone()['c']
        return count > 0
