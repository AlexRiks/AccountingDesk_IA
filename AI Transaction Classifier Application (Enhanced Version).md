# AI Transaction Classifier Application (Enhanced Version)

## Summary

This Streamlit application allows users to upload financial transactions from a CSV file, automatically classify them using AI (Gemini Pro) based on a predefined list of categories and subcategories stored permanently in a database (`app_database.db`), manually correct classifications, and have the application "learn" from these corrections for future transactions. The Gemini API Key is configured securely via Streamlit Cloud Secrets. The results can be downloaded.

## Project File Structure

```
/
├── app.py                     # Main Streamlit application script
├── database_utils.py          # Utilities for SQLite database management
├── llm_service.py             # Service to interact with the Gemini API
├── classification_engine.py   # Classification logic (combines AI and learning)
├── requirements.txt           # Python dependencies
├── Categories_for_db_population.csv # Example CSV to populate the DB initially (see note below)
├── app_database.db            # SQLite database (should be populated and in the repo)
├── transaction_template.csv   # CSV template for the user to know the expected format
└── README.md                  # This file
```

## Local Setup and Execution

1.  **Prerequisites:**
    *   Python 3.9 or higher.
    *   `pip` to install packages.

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate    # On Windows
    ```

3.  **Install Dependencies:**
    Navigate to the project root directory and run:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Prepare the Category Database (`app_database.db`):**
    *   The application now expects `app_database.db` to exist and contain the populated `lista_categorias` table.
    *   **For the first time / or to bulk update categories:**
        1.  Ensure you have a `Categories_for_db_population.csv` file with your categories (columns: `Category`, `Subcategory`).
        2.  You can use the `database_utils.py` script directly to populate the database. Uncomment the test lines at the end of `database_utils.py` and run it:
            ```python
            # In database_utils.py, at the end, modify and uncomment:
            # if __name__ == '__main__':
            #     create_tables()
            #     # Ensure Categories_for_db_population.csv is in the same directory or provide the correct path
            #     if load_categories_from_csv('Categories_for_db_population.csv'): 
            #         print("Database populated with categories.")
            #     else:
            #         print("Error populating the database.")
            #     print(get_all_categories())
            ```
            Then run: `python database_utils.py`
        3.  This will create/update `app_database.db` with categories from the CSV. **Ensure this updated `app_database.db` is in your project directory.**

5.  **Configure Google Gemini API Key (for local execution):**
    *   The application will attempt to read the API Key from Streamlit Secrets (if you run in an environment that supports them, like Streamlit Cloud or locally with a `.streamlit/secrets.toml` file).
    *   For local development without `secrets.toml`, you can temporarily set the `GOOGLE_API_KEY` environment variable or modify `llm_service.py` to pass the key directly (not recommended for production).
    *   A `secrets.toml` file in a `.streamlit` directory at your project root would look like this:
        ```toml
        GOOGLE_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
        ```

6.  **Run the Application:**
    ```bash
    streamlit run app.py
    ```
    The application will open in your web browser.

7.  **Initial Use (Local):**
    *   Ensure `app_database.db` is populated and the API Key is accessible (via `secrets.toml` or environment variable).
    *   Download the transaction template if needed.
    *   Upload your transaction CSV file (with an `ExpenseDesc` column).
    *   The application will process the transactions. You can edit the categories.
    *   Download the results.

## Deployment on Streamlit Community Cloud

1.  **Prepare your GitHub Repository:**
    *   Create a new public GitHub repository.
    *   Upload all project files: `app.py`, `database_utils.py`, `llm_service.py`, `classification_engine.py`, `requirements.txt`, `transaction_template.csv`, and **very importantly, the `app_database.db` file already populated with your categories.**
    *   `app_database.db`: This SQLite database stores your categories and learned corrections. For categories and learning to persist, **you must include `app_database.db` in your Git repository and commit/push changes** whenever the database is updated (e.g., if you add new categories locally or if learned corrections are significant).

2.  **Connect your Repository to Streamlit Cloud:**
    *   Go to [share.streamlit.io](https://share.streamlit.io/) and sign up or log in.
    *   Click "New app".
    *   Select "Deploy from GitHub".
    *   Choose your repository, branch (usually `main` or `master`), and the main application file (`app.py`).

3.  **Configure Secrets (Environment Variables):**
    *   The application **requires** your Google Gemini API Key via Streamlit Cloud Secrets.
    *   In your Streamlit Cloud app settings, go to "Settings" -> "Secrets".
    *   Add a new secret with the following format:
        ```toml
        GOOGLE_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
        ```
        Replace `YOUR_GEMINI_API_KEY_HERE` with your actual key.
    *   The `app.py` application is designed to read this key from `st.secrets`.

4.  **Deploy:**
    *   Click "Deploy!". Streamlit Cloud will install dependencies and run your application.

## Using the Deployed Application

*   Access your Streamlit Cloud application's public URL.
*   The API Key will be taken from Secrets. Categories will be loaded from `app_database.db` in your repository.
*   Upload your transactions.
*   Review, correct, and download.

## Additional Notes

*   **Category Management:** To add, remove, or bulk-modify categories, you will need to update your `Categories_for_db_population.csv` file locally, re-populate `app_database.db` using `database_utils.py` (as described in local setup), and then commit and push the updated `app_database.db` to your GitHub repository.
*   **Description Column:** The application expects an `ExpenseDesc` column in your transaction file. If different, modify `description_column` in `app.py`.
*   **Learning:** Corrections are saved in `app_database.db`. For this learning to persist in Streamlit Cloud, remember to include and commit this file in Git.

Enjoy your enhanced transaction classification application!

