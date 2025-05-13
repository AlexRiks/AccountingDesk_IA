# classification_engine.py
import hashlib
import database_utils
import llm_service

def get_category_for_transaction(description, api_key_llm):
    """Orquesta la clasificación: primero busca correcciones, luego usa IA."""
    if not description or not isinstance(description, str) or not description.strip():
        # print("Descripción vacía o inválida, no se puede clasificar.")
        return "No Categorizada" # O manejar de otra forma

    description_hash = hashlib.sha256(description.encode('utf-8')).hexdigest()

    # 1. Buscar en correcciones_aprendizaje
    corrected_category_tuple = database_utils.get_corrected_category(description_hash)
    if corrected_category_tuple:
        # print(f"Categoría encontrada en correcciones para '{description[:30]}...': {corrected_category_tuple[0]} - {corrected_category_tuple[1]}")
        return f"{corrected_category_tuple[0]} - {corrected_category_tuple[1]}"

    # 2. Si no hay corrección, obtener lista de categorías y usar LLM
    all_categories_tuples = database_utils.get_all_categories()
    if not all_categories_tuples:
        # print("No hay categorías cargadas en la base de datos. No se puede clasificar.")
        return "Error: Lista de categorías vacía"

    # Formatear la lista de categorías para el prompt del LLM
    # (ej: "Categoria1 - Subcategoria1\nCategoria2 - Subcategoria2")
    categories_list_str_for_prompt = "\n".join([f"{cat} - {subcat}" for cat, subcat in all_categories_tuples])

    # print(f"Consultando LLM para: {description[:30]}...")
    llm_assigned_category_str = llm_service.categorize_with_gemini(description, categories_list_str_for_prompt, api_key_llm)
    # print(f"LLM asignó para '{description[:30]}...': {llm_assigned_category_str}")
    
    return llm_assigned_category_str

# Para pruebas iniciales (requiere que database_utils.py y llm_service.py estén en el mismo directorio)
# y que la base de datos exista y tenga categorías.
if __name__ == '__main__':
    # --- Configuración de Prueba --- 
    # 1. Crear DB y tablas
    database_utils.create_tables()
    
    # 2. Cargar un Categories.csv de prueba (crea uno si no existe)
    # Ejemplo de Categories_test.csv:
    # Category,Subcategory
    # Gastos,Transporte
    # Gastos,Comida
    # Ingresos,Salario
    # Gastos,Entretenimiento
    # try:
    #     with open("Categories_test.csv", "w") as f:
    #         f.write("Category,Subcategory\n")
    #         f.write("Gastos,Transporte\n")
    #         f.write("Gastos,Comida\n")
    #         f.write("Ingresos,Salario\n")
    #         f.write("Gastos,Entretenimiento\n")
    #     print("Categories_test.csv creado.")
    #     database_utils.load_categories_from_csv("Categories_test.csv")
    # except Exception as e:
    #     print(f"Error creando/cargando Categories_test.csv: {e}")

    # 3. Configurar API Key de Gemini (reemplaza con tu key o usa variable de entorno)
    # test_api_key = os.getenv("GOOGLE_API_KEY") 
    # if not test_api_key:
    #     print("Por favor, establece GOOGLE_API_KEY para probar o ingrésala aquí.")
    #     test_api_key = "TU_API_KEY_AQUI" # ¡No commitear la key!

    # if test_api_key and test_api_key != "TU_API_KEY_AQUI":
    #     # --- Pruebas --- 
    #     desc1 = "UBER TRIP TO AIRPORT"
    #     desc2 = "PAYCHECK FROM ACME CORP"
    #     desc3 = "STARBUCKS COFFEE"
    #     desc4 = "MOVIE TICKETS FOR AVATAR"
    #     desc5 = "REFUND FOR RETURNED ITEM"

    #     print(f"Clasificando: {desc1} -> {get_category_for_transaction(desc1, test_api_key)}")
    #     print(f"Clasificando: {desc2} -> {get_category_for_transaction(desc2, test_api_key)}")
    #     print(f"Clasificando: {desc3} -> {get_category_for_transaction(desc3, test_api_key)}")

    #     # Simular una corrección manual
    #     print("Guardando corrección para Starbucks...")
    #     database_utils.save_correction(desc3, "Gastos", "Cafetería") # Asumiendo que "Cafetería" no estaba en la lista original
    #                                                              # Para que esto funcione bien, "Gastos - Cafetería" debería ser una opción válida
    #                                                              # o la lógica de guardado/recuperación debe manejarlo.
    #                                                              # Por ahora, el LLM se ciñe a la lista original.
    #                                                              # Si la corrección es a una categoría que no está en la lista_categorias, 
    #                                                              # el LLM no la podrá sugerir, pero la corrección manual sí se guardará.

    #     print(f"Clasificando de nuevo (con corrección): {desc3} -> {get_category_for_transaction(desc3, test_api_key)}")
        
    #     print(f"Clasificando: {desc4} -> {get_category_for_transaction(desc4, test_api_key)}")
    #     print(f"Clasificando: {desc5} -> {get_category_for_transaction(desc5, test_api_key)}")
    # else:
    #     print("API Key no proporcionada. Saltando pruebas de clasificación.")
    pass

