
import sqlite3

def create_tables():
    conn = sqlite3.connect("app_database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS correcciones_aprendizaje (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion_transaccion TEXT,
            descripcion_transaccion_original TEXT,
            categoria TEXT,
            subcategoria TEXT,
            clase TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT,
            subcategoria TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_all_categories():
    conn = sqlite3.connect("app_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT categoria, subcategoria FROM categorias")
    results = cursor.fetchall()
    conn.close()
    return results

def save_correction(description, categoria, subcategoria):
    try:
        conn = sqlite3.connect("app_database.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO correcciones_aprendizaje (
                descripcion_transaccion,
                descripcion_transaccion_original,
                categoria,
                subcategoria,
                clase
            ) VALUES (?, ?, ?, ?, ?)
        ''', (description, description, categoria, subcategoria, ""))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error saving correction:", e)
        return False

def get_manual_correction(description):
    conn = sqlite3.connect("app_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT categoria, subcategoria FROM correcciones_aprendizaje WHERE descripcion_transaccion = ?",
        (description,),
    )
    row = cursor.fetchone()
    conn.close()
    return row

