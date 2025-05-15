
# AI Transaction Classifier Application (Enhanced Version)

## Summary

This Streamlit application allows users to upload financial transactions from a CSV file, automatically classify them using AI (**OpenAI GPT-4**) based on a predefined list of categories and subcategories stored in a database (`app_database.db`), manually correct classifications, and have the application "learn" from these corrections for future transactions. The OpenAI API Key is configured securely via Streamlit Cloud Secrets. The results can be downloaded.

## Project File Structure

```
/
├── app.py                     # Main Streamlit application script
├── database_utils.py          # Utilities for SQLite database management
├── llm_service.py             # Service to interact with the OpenAI API
├── classification_engine.py   # Classification logic (combines AI and learning)
├── requirements.txt           # Python dependencies
├── Categories_for_db_population.csv # Example CSV to populate the DB initially
├── app_database.db            # SQLite database (must be present and populated)
├── transaction_template.csv   # CSV template for user-uploaded transactions
└── README.md                  # This file
```

## Local Setup and Execution

1. **Prerequisites:**
    * Python 3.9 or higher.
    * `pip` to install packages.

2. **Create a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate    # On Windows
    ```

3. **Install Dependencies:**
    Navigate to the project root directory and run:
    ```bash
    pip install -r requirements.txt
    ```

4. **Prepare the Category Database (`app_database.db`):**
    * The application expects `app_database.db` to exist and contain the `lista_categorias` table.
    * **For first-time setup or to update categories:**
        1. Ensure `Categories_for_db_population.csv` exists with columns `Category` and `Subcategory`.
        2. Use `database_utils.py` to populate the database. Uncomment the lines at the end:
        ```python
        if __name__ == '__main__':
            create_tables()
            if load_categories_from_csv('Categories_for_db_population.csv'): 
                print("Database populated with categories.")
            else:
                print("Error populating the database.")
            print(get_all_categories())
        ```
        3. Then run: `python database_utils.py`
        4. This will create or update `app_database.db` with your categories.

## Secrets Configuration (Streamlit Cloud)

Create a secret entry:

```toml
OPENAI_API_KEY = "your_openai_api_key_here"
```

## Usage

1. Launch the app with:
    ```bash
    streamlit run app.py
    ```
2. Upload your transactions using the provided CSV template.
3. Classify automatically, review/edit the results, and download the final CSV.

## Notes

- The system uses `normalize_description()` and hashed values to remember previous corrections securely.
- Manual corrections improve the accuracy of future classifications.
- The system does not expose your API key or write corrections to external servers.

## License

MIT License
