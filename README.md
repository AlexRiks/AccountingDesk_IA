# 💸 AI Transaction Classifier

A Streamlit app to classify financial transactions using AI (OpenAI GPT) and Firebase.
Upload a CSV file with transactions. The app will predict categories and class (DF/DT) using AI.

## Features
- Upload CSV
- AI classification (OpenAI API)
- Firebase integration
- Editable interface

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your OpenAI API Key:
```bash
export OPENAI_API_KEY=your_key_here
```

3. Place your Firebase credentials as `firebase_key.json`.

4. Run the app:
```bash
streamlit run streamlit_app.py
```