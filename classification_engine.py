# classification_engine.py
import hashlib
import database_utils
import llm_service

def get_category_for_transaction(description, api_key_llm):
    """Orchestrates the classification: first checks for manual corrections, then uses AI."""
    if not description or not isinstance(description, str) or not description.strip():
        # print("Empty or invalid description, cannot classify.")
        return "Uncategorized" # Or handle differently

    description_hash = hashlib.sha256(description.encode("utf-8")).hexdigest()

    # 1. Check for manual corrections (learning)
    corrected_category_tuple = database_utils.get_corrected_category(description_hash)
    if corrected_category_tuple:
        # print(f"Category found in corrections for 	{description[:30]}...	: {corrected_category_tuple[0]} - {corrected_category_tuple[1]}")
        # Returns "Category - Subcategory" string
        return f"{corrected_category_tuple[0]} - {corrected_category_tuple[1]}"

    # 2. If no correction, get category list and use LLM
    all_categories_tuples = database_utils.get_all_categories() # List of (cat, subcat) tuples
    if not all_categories_tuples:
        # print("No categories loaded in the database. Cannot classify.")
        return "Error: Category List Empty" # Error or "Uncategorized"

    # Format the category list for the LLM prompt
    # (e.g., "Category1 - Subcategory1\nCategory2 - Subcategory2")
    categories_list_str_for_prompt = "\n".join([f"{cat} - {subcat}" for cat, subcat in all_categories_tuples])

    # print(f"Querying LLM for: {description[:30]}...")
    llm_assigned_category_str = llm_service.categorize_with_gemini(description, categories_list_str_for_prompt, api_key_llm)
    # print(f"LLM assigned for 	{description[:30]}...	: {llm_assigned_category_str}")
    
    return llm_assigned_category_str

# For initial testing (requires database_utils.py and llm_service.py in the same directory)
# and the database to exist and have categories.
if __name__ == '__main__':
    # --- Test Setup ---
    # 1. Create DB and tables
    database_utils.create_tables()
    
    # 2. Load a test Categories.csv (create one if it doesn't exist)
    # Example Categories_test.csv:
    # Category,Subcategory
    # Expenses,Transportation
    # Expenses,Food
    # Income,Salary
    # Expenses,Entertainment
    # try:
    #     with open("Categories_test.csv", "w") as f:
    #         f.write("Category,Subcategory\n")
    #         f.write("Expenses,Transportation\n")
    #         f.write("Expenses,Food\n")
    #         f.write("Income,Salary\n")
    #         f.write("Expenses,Entertainment\n")
    #     print("Categories_test.csv created.")
    #     database_utils.load_categories_from_csv("Categories_test.csv")
    # except Exception as e:
    #     print(f"Error creating/loading Categories_test.csv: {e}")

    # 3. Configure Gemini API Key (replace with your key or use environment variable)
    # import os
    # test_api_key = os.getenv("GOOGLE_API_KEY") 
    # if not test_api_key:
    #     print("Please set GOOGLE_API_KEY to test or enter it here.")
    #     test_api_key = "YOUR_API_KEY_HERE" # Do not commit the key!

    # if test_api_key and test_api_key != "YOUR_API_KEY_HERE":
    #     # --- Tests ---
    #     desc1 = "UBER TRIP TO AIRPORT"
    #     desc2 = "PAYCHECK FROM ACME CORP"
    #     desc3 = "STARBUCKS COFFEE"
    #     desc4 = "MOVIE TICKETS FOR AVATAR"
    #     desc5 = "REFUND FOR RETURNED ITEM"

    #     print(f"Classifying: {desc1} -> {get_category_for_transaction(desc1, test_api_key)}")
    #     print(f"Classifying: {desc2} -> {get_category_for_transaction(desc2, test_api_key)}")
    #     print(f"Classifying: {desc3} -> {get_category_for_transaction(desc3, test_api_key)}")

    #     # Simulate a manual correction
    #     print("Saving correction for Starbucks...")
    #     # Assuming "Coffee Shop" was not in the original list.
    #     # For this to work well, "Expenses - Coffee Shop" should be a valid option from the master list
    #     # or the save/retrieve logic must handle it. The LLM sticks to the original list.
    #     # If the correction is to a category not in lista_categorias, 
    #     # the LLM won't suggest it, but the manual correction will be saved.
    #     database_utils.save_correction(desc3, "Expenses", "Coffee Shop") 

    #     print(f"Re-classifying (with correction): {desc3} -> {get_category_for_transaction(desc3, test_api_key)}")
        
    #     print(f"Classifying: {desc4} -> {get_category_for_transaction(desc4, test_api_key)}")
    #     print(f"Classifying: {desc5} -> {get_category_for_transaction(desc5, test_api_key)}")
    # else:
    #     print("API Key not provided. Skipping classification tests.")
    pass

