# database_utils.py
import sqlite3
import pandas as pd
import hashlib

DATABASE_NAME = "app_database.db"

def get_db_connection():
    # Returns a database connection object.
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Access columns by name
    return conn

def create_tables():
    # Creates the necessary database tables if they don't already exist.
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table for the master list of categories
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lista_categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_categoria TEXT NOT NULL,       -- Category name (in original language or English)
        nombre_subcategoria TEXT NOT NULL,    -- Subcategory name (in original language or English)
        UNIQUE (nombre_categoria, nombre_subcategoria)
    )
    """)

    # Table for corrections and learning
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS correcciones_aprendizaje (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hash_descripcion TEXT NOT NULL UNIQUE,        -- Hash of the transaction description
        descripcion_transaccion TEXT NOT NULL,      -- Original transaction description
        categoria_corregida TEXT NOT NULL,        -- Corrected category (in original language or English)
        subcategoria_corregida TEXT NOT NULL,     -- Corrected subcategory (in original language or English)
        timestamp_correccion DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def load_categories_from_csv(csv_file_path):
    # Loads categories from a CSV file into the lista_categorias table.
    # Clears the table before loading to prevent duplicates on reload.
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        df = pd.read_csv(csv_file_path)
        # Use confirmed headers: 'Category' and 'Subcategory'
        # Ensure these columns exist in the df
        if 'Category' not in df.columns or 'Subcategory' not in df.columns:
            print(f"Error: The CSV file {csv_file_path} must contain 'Category' and 'Subcategory' columns.")
            return False

        # Clear the table before loading to avoid duplicates if reloaded
        cursor.execute("DELETE FROM lista_categorias")
        conn.commit()

        for index, row in df.iterrows():
            cat = row['Category']
            sub_cat = row['Subcategory']
            if pd.notna(cat) and pd.notna(sub_cat):
                try:
                    # Storing category names as they are. If they need to be English, 
                    # the source CSV should be in English or translated before this step.
                    cursor.execute("INSERT INTO lista_categorias (nombre_categoria, nombre_subcategoria) VALUES (?, ?)",
                                   (str(cat).strip(), str(sub_cat).strip()))
                except sqlite3.IntegrityError:
                    # Ignore duplicates if the previous cleaning fails or just in case
                    print(f"Duplicate category ignored: {cat} - {sub_cat}")
        conn.commit()
        print(f"Categories loaded successfully from {csv_file_path}")
        return True
    except Exception as e:
        print(f"Error loading categories from CSV: {e}")
        return False
    finally:
        conn.close()

def get_all_categories():
    # Retrieves all categories from the lista_categorias table.
    # Returns a list of tuples: (category_name, subcategory_name)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre_categoria, nombre_subcategoria FROM lista_categorias ORDER BY nombre_categoria, nombre_subcategoria")
    categories = cursor.fetchall()
    conn.close()
    return [(row['nombre_categoria'], row['nombre_subcategoria']) for row in categories]

def get_corrected_category(description_hash):
    # Retrieves a manually corrected category for a given transaction description hash.
    # Returns a tuple (corrected_category, corrected_subcategory) or None if not found.
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT categoria_corregida, subcategoria_corregida FROM correcciones_aprendizaje WHERE hash_descripcion = ?", (description_hash,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row['categoria_corregida'], row['subcategoria_corregida']
    return None

def save_correction(description, category, subcategory):
    # Saves or updates a manual correction for a transaction description.
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
        print(f"Correction saved for: {description[:50]}... -> {category} - {subcategory}")
        return True
    except Exception as e:
        print(f"Error saving correction: {e}")
        return False
    finally:
        conn.close()

# For initial testing and DB generation
if __name__ == '__main__':
    create_tables()
    # Path to the user-provided CSV file
    categories_csv_path = '/home/ubuntu/upload/Categories.csv' 
    if load_categories_from_csv(categories_csv_path):
        print(f"Database '{DATABASE_NAME}' populated successfully using {categories_csv_path}.")
        all_cats = get_all_categories()
        print(f"Total categories loaded: {len(all_cats)}")
        # print("Sample categories:", all_cats[:5]) # Print a few samples
    else:
        print(f"Failed to populate database from {categories_csv_path}.")

