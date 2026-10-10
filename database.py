import sqlite3
from models import Lancamento

DB_NAME = "financas.db"

def init_db():
    with sqlite3.connect(DB_NAME) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS lancamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                tipo TEXT NOT NULL CHECK(tipo IN ('receita','despesa')),
                categoria TEXT,
                data TEXT NOT NULL
            )
        """)

def adicionar(l: Lancamento) -> int:
    with sqlite3.connect(DB_NAME) as con:
        cur = con.execute(
            "INSERT INTO lancamentos (descricao, valor, tipo, categoria, data) VALUES (?,?,?,?,?)",
            (l.descricao, l.valor, l.tipo, l.categoria, l.data),
        )
        return cur.lastrowid

def listar(filtro_tipo: str = "todos") -> list[Lancamento]:
    query = "SELECT id, descricao, valor, tipo, categoria, data FROM lancamentos"
    params = ()
    if filtro_tipo != "todos":
        query += " WHERE tipo = ?"
        params = (filtro_tipo,)
    query += " ORDER BY data DESC, id DESC"
    with sqlite3.connect(DB_NAME) as con:
        rows = con.execute(query, params).fetchall()
    return [Lancamento(id=r[0], descricao=r[1], valor=r[2], tipo=r[3], categoria=r[4], data=r[5]) for r in rows]

def atualizar(l: Lancamento):
    with sqlite3.connect(DB_NAME) as con:
        con.execute(
            "UPDATE lancamentos SET descricao=?, valor=?, tipo=?, categoria=?, data=? WHERE id=?",
            (l.descricao, l.valor, l.tipo, l.categoria, l.data, l.id),
        )

def excluir(id_: int):
    with sqlite3.connect(DB_NAME) as con:
        con.execute("DELETE FROM lancamentos WHERE id=?", (id_,))

def saldo_atual() -> float:
    with sqlite3.connect(DB_NAME) as con:
        row = con.execute("""
            SELECT COALESCE(SUM(CASE WHEN tipo='receita' THEN valor ELSE -valor END), 0)
            FROM lancamentos
        """).fetchone()
    return row[0]

def resumo_por_categoria() -> dict[str, dict[str, float]]:
    """Retorna {'categoria': {'receitas': x, 'despesas': y}}"""
    with sqlite3.connect(DB_NAME) as con:
        rows = con.execute("""
            SELECT categoria,
                   SUM(CASE WHEN tipo='receita' THEN valor ELSE 0 END),
                   SUM(CASE WHEN tipo='despesa' THEN valor ELSE 0 END)
            FROM lancamentos GROUP BY categoria
        """).fetchall()
    return {r[0]: {"receitas": r[1], "despesas": r[2]} for r in rows}