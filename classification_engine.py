# classification_engine.py

import database_utils
import llm_service

def get_category_for_transaction(description):
    """Classifies the transaction using the AI model or falls back to the database."""

    # Check for manual correction in DB first
    existing = database_utils.get_manual_correction(description)
    if existing:
        return f"{existing[0]} - {existing[1]}" if existing[1] else existing[0]

    # If not found, use AI
    prompt = f"Classify the following transaction: '{description}'. Return format: Category - Subcategory"
    classification = llm_service.classify_transaction_with_ai(prompt)
    return classification
