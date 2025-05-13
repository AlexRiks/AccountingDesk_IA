import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def classify_transaction(df):
    # This function simulates classification for now
    df["Category"] = "Admin"
    df["Subcategory"] = "Accounting Charges"
    df["Class"] = "DF"
    return df