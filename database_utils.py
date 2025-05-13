# database_utils.py
import sqlite3
import pandas as pd
import hashlib

DATABASE_NAME = "app_database.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabla para la lista maestra de categorías
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lista_categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_categoria TEXT NOT NULL,
        nombre_subcategoria TEXT NOT NULL,
        UNIQUE (nombre_categoria, nombre_subcategoria)
    )
    """)

    # Tabla para las correcciones y aprendizaje
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS correcciones_aprendizaje (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hash_descripcion TEXT NOT NULL UNIQUE,
        descripcion_transaccion TEXT NOT NULL,
        categoria_corregida TEXT NOT NULL,
        subcategoria_corregida TEXT NOT NULL,
        timestamp_correccion DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def load_categories_from_csv(csv_file_path):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        df = pd.read_csv(csv_file_path)
        # Usar las cabeceras confirmadas: 'Category' y 'Subcategory'
        # Asegurarse de que estas columnas existan en el df
        if 'Category' not in df.columns or 'Subcategory' not in df.columns:
            print(f"Error: El archivo CSV {csv_file_path} debe contener las columnas 'Category' y 'Subcategory'.")
            return False

        # Limpiar la tabla antes de cargar para evitar duplicados si se recarga
        cursor.execute("DELETE FROM lista_categorias")
        conn.commit()

        for index, row in df.iterrows():
            cat = row['Category']
            sub_cat = row['Subcategory']
            if pd.notna(cat) and pd.notna(sub_cat):
                try:
                    cursor.execute("INSERT INTO lista_categorias (nombre_categoria, nombre_subcategoria) VALUES (?, ?)",
                                   (str(cat).strip(), str(sub_cat).strip()))
                except sqlite3.IntegrityError:
                    # Ignorar duplicados si la limpieza previa no se hace o por si acaso
                    print(f"Categoría duplicada ignorada: {cat} - {sub_cat}")
        conn.commit()
        print(f"Categorías cargadas exitosamente desde {csv_file_path}")
        return True
    except Exception as e:
        print(f"Error al cargar categorías desde CSV: {e}")
        return False
    finally:
        conn.close()

def get_all_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre_categoria, nombre_subcategoria FROM lista_categorias ORDER BY nombre_categoria, nombre_subcategoria")
    categories = cursor.fetchall()
    conn.close()
    return [(row['nombre_categoria'], row['nombre_subcategoria']) for row in categories]

def get_corrected_category(description_hash):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT categoria_corregida, subcategoria_corregida FROM correcciones_aprendizaje WHERE hash_descripcion = ?", (description_hash,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row['categoria_corregida'], row['subcategoria_corregida']
    return None

def save_correction(description, category, subcategory):
    conn = get_db_connection()
    cursor = conn.cursor()
    description_hash = hashlib.sha256(description.encode('utf-8')).hexdigest()
    try:
        cursor.execute("""
        INSERT INTO correcciones_aprendizaje (hash_descripcion, descripcion_transaccion, categoria_corregida, subcategoria_corregida)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(hash_descripcion) DO UPDATE SET
        categoria_corregida = excluded.categoria_corregida,
        subcategoria_corregida = excluded.subcategoria_corregida,
        timestamp_correccion = CURRENT_TIMESTAMP
        """, (description_hash, description, category, subcategory))
        conn.commit()
        print(f"Corrección guardada para: {description[:50]}... -> {category} - {subcategory}")
        return True
    except Exception as e:
        print(f"Error al guardar corrección: {e}")
        return False
    finally:
        conn.close()

# Para pruebas iniciales
if __name__ == '__main__':
    create_tables()
    # Suponiendo que tienes un 'Categories.csv' en el mismo directorio para probar
    # load_categories_from_csv('Categories.csv') 
    # print(get_all_categories())
    # save_correction("Test Transaction Description", "Gastos", "Comida")
    # print(get_corrected_category(hashlib.sha256("Test Transaction Description".encode('utf-8')).hexdigest()))

