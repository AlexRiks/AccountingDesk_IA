# llm_service.py
import google.generativeai as genai
import os

# Placeholder for API Key, will be set by the Streamlit app from user input or secrets
# os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY"

def configure_gemini(api_key):
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"Error configurando Gemini: {e}")
        return False

def categorize_with_gemini(description, categories_list_str, api_key):
    if not configure_gemini(api_key):
        return "Error: API Key de Gemini no configurada o inválida."

    try:
        model = genai.GenerativeModel("gemini-pro") # o el modelo que sea más adecuado y esté disponible
        
        prompt = f"""Dada la siguiente descripción de transacción:
        '{description}'

        Y la siguiente lista de categorías y subcategorías válidas (formato: Categoria - Subcategoria):
        {categories_list_str}

        ¿Cuál es la categoría y subcategoría más adecuada de la lista para esta transacción? 
        Responde únicamente con 'Categoria - Subcategoria' exactamente como aparece en la lista, o responde 'No Categorizada' si ninguna opción de la lista es claramente adecuada.
        No inventes categorías nuevas. Si hay múltiples opciones posibles, elige la más específica o la primera que consideres más relevante.
        Ejemplo de respuesta esperada: 'Ingresos - Salario' o 'Gastos - Comida' o 'No Categorizada'.
        """
        
        # print(f"Prompt enviado a Gemini: {prompt}") # Para depuración
        response = model.generate_content(prompt)
        
        # print(f"Respuesta de Gemini: {response.text}") # Para depuración
        
        # Limpiar la respuesta
        raw_response_text = response.text.strip()
        
        # Validar si la respuesta está en la lista de categorías o es "No Categorizada"
        # Primero, crear una lista de categorías válidas en el formato "Categoria - Subcategoria"
        valid_responses = [f"{cat} - {subcat}" for cat, subcat in categories_list_str_to_tuple_list(categories_list_str)]
        valid_responses.append("No Categorizada")

        if raw_response_text in valid_responses:
            return raw_response_text
        else:
            # Si la respuesta no es exactamente una de las opciones, intentar una coincidencia más laxa
            # o simplemente devolver "No Categorizada" para ser más estrictos.
            # Por ahora, seremos estrictos.
            print(f"Respuesta de Gemini ('{raw_response_text}') no es una categoría válida. Se marcará como 'No Categorizada'.")
            return "No Categorizada"
            
    except Exception as e:
        print(f"Error al interactuar con Gemini API: {e}")
        # Podrías querer devolver un error más específico o simplemente "No Categorizada"
        return "Error al contactar IA"

def categories_list_str_to_tuple_list(categories_str):
    """Convierte una cadena de 'Cat1 - Subcat1\nCat2 - Subcat2' a lista de tuplas [('Cat1', 'Subcat1'), ...]"""
    pairs = []
    lines = categories_str.strip().split('\n')
    for line in lines:
        parts = line.split(' - ', 1)
        if len(parts) == 2:
            pairs.append((parts[0].strip(), parts[1].strip()))
    return pairs

# Para pruebas iniciales
if __name__ == '__main__':
    # Necesitarás configurar tu GOOGLE_API_KEY como variable de entorno para probar esto localmente
    # o pasarla directamente a configure_gemini
    # test_api_key = os.getenv("GOOGLE_API_KEY")
    # if not test_api_key:
    #     print("Por favor, establece la variable de entorno GOOGLE_API_KEY para probar.")
    # else:
    #     configure_gemini(test_api_key)
    #     sample_description = "UBER TRIP SAN FRANCISCO CA"
    #     sample_categories_str = ("Gastos - Transporte\n" 
    #                              "Gastos - Comida\n"
    #                              "Ingresos - Salario")
    #     sample_categories_list = [("Gastos", "Transporte"), ("Gastos", "Comida"), ("Ingresos", "Salario")]
        
    #     # Test de la función auxiliar
    #     # print(categories_list_str_to_tuple_list(sample_categories_str))

    #     # category = categorize_with_gemini(sample_description, sample_categories_str, test_api_key)
    #     # print(f"Descripción: {sample_description}")
    #     # print(f"Categoría asignada: {category}")

    #     # sample_description_2 = "SALARY DEPOSIT ABC CORP"
    #     # category_2 = categorize_with_gemini(sample_description_2, sample_categories_str, test_api_key)
    #     # print(f"Descripción: {sample_description_2}")
    #     # print(f"Categoría asignada: {category_2}")

    #     # sample_description_3 = "Random stuff not in categories"
    #     # category_3 = categorize_with_gemini(sample_description_3, sample_categories_str, test_api_key)
    #     # print(f"Descripción: {sample_description_3}")
    #     # print(f"Categoría asignada: {category_3}")
    pass

