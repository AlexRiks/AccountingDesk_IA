
import sqlite3
import pandas as pd
import hashlib
import re
import traceback

DATABASE_NAME = "app_database.db"

def normalize_description(description):
    if not isinstance(description, str):
        return ""
    text = description.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lista_categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_categoria TEXT NOT NULL,
        nombre_subcategoria TEXT NOT NULL,
        UNIQUE (nombre_categoria, nombre_subcategoria)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS correcciones_aprendizaje (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hash_descripcion TEXT NOT NULL UNIQUE,
        descripcion_transaccion_original TEXT NOT NULL,
        categoria_corregida TEXT NOT NULL,
        subcategoria_corregida TEXT NOT NULL,
        timestamp_correccion DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def get_all_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre_categoria, nombre_subcategoria FROM lista_categorias ORDER BY nombre_categoria, nombre_subcategoria")
    categories = cursor.fetchall()
    conn.close()
    return [(row["nombre_categoria"], row["nombre_subcategoria"]) for row in categories]

def get_corrected_category(normalized_description_hash):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT categoria_corregida, subcategoria_corregida FROM correcciones_aprendizaje WHERE hash_descripcion = ?", 
                   (normalized_description_hash,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["categoria_corregida"], row["subcategoria_corregida"]
    return None

def get_manual_correction(description):
    normalized_desc = normalize_description(description)
    if not normalized_desc:
        return None
    description_hash = hashlib.sha256(normalized_desc.encode("utf-8")).hexdigest()
    return get_corrected_category(description_hash)

def save_correction(original_description, category, subcategory):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print(f"Attempting to save correction:")
        print(f"Original: {original_description}")
        print(f"Category: {category}")
        print(f"Subcategory: {subcategory}")

        normalized_desc = normalize_description(original_description)
        print(f"Normalized: {normalized_desc}")

        if not normalized_desc:
            print(f"Skipping saving correction for empty/invalid description: {original_description}")
            return False

        description_hash = hashlib.sha256(normalized_desc.encode("utf-8")).hexdigest()

        cursor.execute("""
        INSERT INTO correcciones_aprendizaje (hash_descripcion, descripcion_transaccion_original, categoria_corregida, subcategoria_corregida)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(hash_descripcion) DO UPDATE SET
        descripcion_transaccion_original = excluded.descripcion_transaccion_original,
        categoria_corregida = excluded.categoria_corregida,
        subcategoria_corregida = excluded.subcategoria_corregida,
        timestamp_correccion = CURRENT_TIMESTAMP
        """, (description_hash, original_description, category, subcategory))

        conn.commit()
        print("✔ Correction saved.")
        return True
    except Exception as e:
        print("✖ Error saving correction:")
        traceback.print_exc()
        return False
    finally:
        conn.close()
