# classification_engine.py
import hashlib
import database_utils # Imports normalize_description
import llm_service

def get_category_for_transaction(description, api_key_llm):
    """Orchestrates the classification: first checks for manual corrections (using normalized description), then uses AI."""
    if not description or not isinstance(description, str) or not description.strip():
        # print("Empty or invalid description, cannot classify.")
        return "Uncategorized"

    # Normalize the description first for consistent lookup and learning
    normalized_desc = database_utils.normalize_description(description)
    if not normalized_desc: # If normalization results in an empty string
        # print(f"Normalized description is empty for original: {description[:50]}... Defaulting to Uncategorized.")
        return "Uncategorized"
        
    description_hash = hashlib.sha256(normalized_desc.encode("utf-8")).hexdigest()

    # 1. Check for manual corrections (learning) using the normalized description's hash
    corrected_category_tuple = database_utils.get_corrected_category(description_hash)
    if corrected_category_tuple:
        # print(f"Category found in corrections for normalized 	{normalized_desc[:30]}...	 (original: 	{description[:30]}...	): {corrected_category_tuple[0]} - {corrected_category_tuple[1]}")
        return f"{corrected_category_tuple[0]} - {corrected_category_tuple[1]}"

    # 2. If no correction, get category list and use LLM with the original description
    all_categories_tuples = database_utils.get_all_categories()
    if not all_categories_tuples:
        # print("No categories loaded in the database. Cannot classify.")
        return "Error: Category List Empty"

    categories_list_str_for_prompt = "\n".join([f"{cat} - {subcat}" for cat, subcat in all_categories_tuples])

    # print(f"Querying LLM for original description: {description[:30]}...")
    # LLM still gets the original, potentially more nuanced description for its classification
    llm_assigned_category_str = llm_service.categorize_with_gemini(description, categories_list_str_for_prompt, api_key_llm)
    # print(f"LLM assigned for 	{description[:30]}...	: {llm_assigned_category_str}")
    
    return llm_assigned_category_str

# For initial testing
if __name__ == "__main__":
    # --- Test Setup ---
    database_utils.create_tables() # Ensure tables exist

    # --- Example Test Case for Learning ---
    # Ensure you have a GOOGLE_API_KEY environment variable set or provide it directly for llm_service tests.
    # test_api_key = os.getenv("GOOGLE_API_KEY", "YOUR_FALLBACK_API_KEY_FOR_TESTING_ONLY")

    # Step 1: Populate with some categories if DB is empty
    # if not database_utils.get_all_categories():
    #     print("Populating sample categories for testing...")
    #     sample_categories_for_db = [
    #         ("Travel", "Flights"), 
    #         ("Travel", "Accommodation"), 
    #         ("Food", "Groceries"),
    #         ("Food", "Restaurants")
    #     ]
    #     conn = database_utils.get_db_connection()
    #     cursor = conn.cursor()
    #     for cat, subcat in sample_categories_for_db:
    #         try:
    #             cursor.execute("INSERT INTO lista_categorias (nombre_categoria, nombre_subcategoria) VALUES (?, ?)", (cat, subcat))
    #         except sqlite3.IntegrityError:
    #             pass # Ignore if already exists
    #     conn.commit()
    #     conn.close()
    #     print("Sample categories loaded.")

    # Test descriptions
    # desc_airbnb_1 = "AIRBNB * HMROAS92K1 PAYMENT"
    # desc_airbnb_2 = "Airbnb * HMROAS92K1 Payment"
    # desc_airbnb_3 = "  airbnb * hmroas92k1 payment  "
    # desc_other = "SUPERMARKET XYZ PURCHASE"

    # print(f"Normalized 1: {database_utils.normalize_description(desc_airbnb_1)}")
    # print(f"Normalized 2: {database_utils.normalize_description(desc_airbnb_2)}")
    # print(f"Normalized 3: {database_utils.normalize_description(desc_airbnb_3)}")

    # Initial classification (assuming LLM would classify it or return Uncategorized)
    # print(f"Initial for 	{desc_airbnb_1}	: {get_category_for_transaction(desc_airbnb_1, test_api_key)}")

    # Simulate a manual correction for the first Airbnb transaction
    # print(f"Saving correction for 	{desc_airbnb_1}	 to Travel - Accommodation")
    # database_utils.save_correction(desc_airbnb_1, "Travel", "Accommodation")

    # Test if the correction is picked up for the same and similar descriptions
    # print(f"After correction for 	{desc_airbnb_1}	: {get_category_for_transaction(desc_airbnb_1, test_api_key)}")
    # print(f"After correction for 	{desc_airbnb_2}	: {get_category_for_transaction(desc_airbnb_2, test_api_key)}") # Should pick up correction
    # print(f"After correction for 	{desc_airbnb_3}	: {get_category_for_transaction(desc_airbnb_3, test_api_key)}") # Should pick up correction
    # print(f"Other transaction 	{desc_other}	: {get_category_for_transaction(desc_other, test_api_key)}") # Should go to LLM
    pass

