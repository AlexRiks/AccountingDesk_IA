# llm_service.py
import google.generativeai as genai
import os

# Placeholder for API Key, will be set by the Streamlit app from Streamlit Secrets
# os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY" # Example, not used directly if secrets are set up

def configure_gemini(api_key):
    # Configures the Gemini API with the provided API key.
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"Error configuring Gemini: {e}")
        return False

def categorize_with_gemini(description, categories_list_str, api_key):
    # Categorizes a transaction description using the Gemini API.
    # description: The transaction description string.
    # categories_list_str: A newline-separated string of "Category - Subcategory" for the prompt.
    # api_key: The Google Gemini API key.
    # Returns the assigned category string (e.g., "Category - Subcategory") or "Uncategorized".

    if not api_key:
        # This check might be redundant if configure_gemini is always called first by the app
        print("Error: Gemini API Key not provided to categorize_with_gemini.")
        return "Error: API Key Missing"
        
    if not configure_gemini(api_key): # Ensure API is configured before each call, or manage state elsewhere
        return "Error: Gemini API Key not configured or invalid."

    try:
        model = genai.GenerativeModel("gemini-pro") # Or the most suitable/available model
        
        prompt = f"""Given the following transaction description:
        '{description}'

        And the following list of valid categories and subcategories (format: Category - Subcategory):
        {categories_list_str}

        What is the most appropriate category and subcategory from the list for this transaction?
        Respond only with 'Category - Subcategory' exactly as it appears in the list, or respond 'Uncategorized' if no option from the list is clearly suitable.
        Do not invent new categories. If multiple options are possible, choose the most specific one or the first one you consider most relevant.
        Expected response example: 'Income - Salary' or 'Expenses - Food' or 'Uncategorized'.
        """
        
        # print(f"Prompt sent to Gemini: {prompt}") # For debugging
        response = model.generate_content(prompt)
        
        # print(f"Response from Gemini: {response.text}") # For debugging
        
        # Clean the response
        raw_response_text = response.text.strip()
        
        # Validate if the response is in the list of categories or is "Uncategorized"
        # First, create a list of valid response strings
        valid_category_format_list = [f"{cat} - {subcat}" for cat, subcat in categories_list_str_to_tuple_list(categories_list_str)]
        valid_responses_for_llm = valid_category_format_list + ["Uncategorized"]

        if raw_response_text in valid_responses_for_llm:
            return raw_response_text
        else:
            # If the response is not exactly one of the options, 
            # it might be a slight variation or an error by the LLM.
            # For strictness, mark as Uncategorized.
            print(f"Gemini's response ('{raw_response_text}') is not a valid category from the provided list. Marking as 'Uncategorized'.")
            return "Uncategorized"
            
    except Exception as e:
        print(f"Error interacting with Gemini API: {e}")
        # You might want to return a more specific error or just "Uncategorized"
        return "Error Contacting AI"

def categories_list_str_to_tuple_list(categories_str):
    # Converts a newline-separated string of 'Cat1 - Subcat1\nCat2 - Subcat2' 
    # to a list of tuples [('Cat1', 'Subcat1'), ...]
    pairs = []
    lines = categories_str.strip().split('\n')
    for line in lines:
        parts = line.split(' - ', 1) # Split only on the first occurrence
        if len(parts) == 2:
            pairs.append((parts[0].strip(), parts[1].strip()))
    return pairs

# For initial testing
if __name__ == '__main__':
    # You will need to set your GOOGLE_API_KEY as an environment variable to test this locally
    # or pass it directly to configure_gemini.
    # test_api_key = os.getenv("GOOGLE_API_KEY")
    # if not test_api_key:
    #     print("Please set the GOOGLE_API_KEY environment variable to test.")
    # else:
    #     if configure_gemini(test_api_key):
    #         sample_description = "UBER TRIP SAN FRANCISCO CA"
    #         sample_categories_str = ("Expenses - Transportation\n" 
    #                                  "Expenses - Food\n"
    #                                  "Income - Salary")
            
    #         # Test the helper function
    #         # print(categories_list_str_to_tuple_list(sample_categories_str))

    #         category = categorize_with_gemini(sample_description, sample_categories_str, test_api_key)
    #         print(f"Description: {sample_description}")
    #         print(f"Assigned Category: {category}")

    #         sample_description_2 = "SALARY DEPOSIT ABC CORP"
    #         category_2 = categorize_with_gemini(sample_description_2, sample_categories_str, test_api_key)
    #         print(f"Description: {sample_description_2}")
    #         print(f"Assigned Category: {category_2}")

    #         sample_description_3 = "Random stuff not in categories"
    #         category_3 = categorize_with_gemini(sample_description_3, sample_categories_str, test_api_key)
    #         print(f"Description: {sample_description_3}")
    #         print(f"Assigned Category: {category_3}")
    #     else:
    #         print("Failed to configure Gemini for testing.")
    pass

