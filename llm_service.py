
import openai

openai.api_key = "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"

def classify_transaction_with_ai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial assistant classifying transactions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.3
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error: {str(e)}"
