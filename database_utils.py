# database_utils.py
import sqlite3
import pandas as pd
import hashlib
import re # For normalization

DATABASE_NAME = "app_database.db"

def normalize_description(description):
    """Normalizes a transaction description for more robust matching."""
    if not isinstance(description, str):
        return ""
    # Convert to lowercase
    text = description.lower()
    # Remove non-alphanumeric characters (except spaces) and then normalize spaces
    text = re.sub(r"[^a-z0-9\s]", "", text)
    # Replace multiple spaces with a single space and strip leading/trailing spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_db_connection():
    # Returns a database connection object.
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Access columns by name
    return conn

def create_tables():
    # Creates the necessary database tables if they don"t already exist.
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
        hash_descripcion TEXT NOT NULL UNIQUE,        -- Hash of the NORMALIZED transaction description
        descripcion_transaccion_original TEXT NOT NULL, -- Original transaction description for reference
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
        if "Category" not in df.columns or "Subcategory" not in df.columns:
            # Corrected the print statement to use single quotes inside the f-string or escape double quotes.
            print(f"Error: The CSV file {csv_file_path} must contain 'Category' and 'Subcategory' columns.")
            return False

        cursor.execute("DELETE FROM lista_categorias")
        conn.commit()

        for index, row in df.iterrows():
            cat = row["Category"]
            sub_cat = row["Subcategory"]
            if pd.notna(cat) and pd.notna(sub_cat):
                try:
                    cursor.execute("INSERT INTO lista_categorias (nombre_categoria, nombre_subcategoria) VALUES (?, ?)",
                                   (str(cat).strip(), str(sub_cat).strip()))
                except sqlite3.IntegrityError:
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre_categoria, nombre_subcategoria FROM lista_categorias ORDER BY nombre_categoria, nombre_subcategoria")
    categories = cursor.fetchall()
    conn.close()
    return [(row["nombre_categoria"], row["nombre_subcategoria"]) for row in categories]

def get_corrected_category(normalized_description_hash):
    # Retrieves a manually corrected category for a given NORMALIZED transaction description hash.
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT categoria_corregida, subcategoria_corregida FROM correcciones_aprendizaje WHERE hash_descripcion = ?", 
                   (normalized_description_hash,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["categoria_corregida"], row["subcategoria_corregida"]
    return None

def save_correction(original_description, category, subcategory):
    # Saves or updates a manual correction for a transaction description.
    # Uses a normalized version of the description for hashing.
    conn = get_db_connection()
    cursor = conn.cursor()
    
    normalized_desc = normalize_description(original_description)
    if not normalized_desc: # Don"t save if normalization results in empty string
        print(f"Skipping saving correction for empty/invalid original description: {original_description}")
        return False
        
    description_hash = hashlib.sha256(normalized_desc.encode("utf-8")).hexdigest()
    
    try:
        cursor.execute("""
        INSERT INTO correcciones_aprendizaje (hash_descripcion, descripcion_transaccion_original, categoria_corregida, subcategoria_corregida)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(hash_descripcion) DO UPDATE SET
        descripcion_transaccion_original = excluded.descripcion_transaccion_original, -- Keep original desc updated if it changes for same normalized hash
        categoria_corregida = excluded.categoria_corregida,
        subcategoria_corregida = excluded.subcategoria_corregida,
        timestamp_correccion = CURRENT_TIMESTAMP
        """, (description_hash, original_description, category, subcategory))
        conn.commit()
        print(f"Correction saved for (normalized): 	{normalized_desc[:50]}...	 -> {category} - {subcategory}")
        return True
    except Exception as e:
        print(f"Error saving correction: {e}")
        return False
    finally:
        conn.close()

# For initial testing and DB generation
if __name__ == "__main__":
    create_tables()
    # Example of normalization
    # print(f"Normalized: {normalize_description("AIRBNB * HMROAS92K1 REFUND")}")
    # print(f"Normalized: {normalize_description("Airbnb * HMROAS92K1 Refund")}")
    # print(f"Normalized: {normalize_description("  AIRBNB *HMROAS92K1  REFUND  ")}")
    
    # Path to the user-provided CSV file (ensure it exists for testing)
    # categories_csv_path = "/home/ubuntu/upload/Categories.csv" 
    # if load_categories_from_csv(categories_csv_path):
    #     print(f"Database 	{DATABASE_NAME}	 populated successfully using {categories_csv_path}.")
    #     all_cats = get_all_categories()
    #     print(f"Total categories loaded: {len(all_cats)}")
    # else:
    #     print(f"Failed to populate database from {categories_csv_path}.")
    pass

def get_manual_correction(description):
    """
    Devuelve una categoría corregida (si existe) para una descripción de transacción.
    Usa hashing sobre la versión normalizada de la descripción.
    """
    normalized_desc = normalize_description(description)
    if not normalized_desc:
        return None

    description_hash = hashlib.sha256(normalized_desc.encode("utf-8")).hexdigest()
    return get_corrected_category(description_hash)
