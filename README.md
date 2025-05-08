# Accounting AI Dashboard

This repository contains a Streamlit application for visualizing and managing financial transactions,
powered by a PostgreSQL database (e.g., Supabase).

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/<your-username>/AccountingDesk_IA.git
   cd AccountingDesk_IA
   ```

2. Create a virtual environment and install dependencies:
   ```
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configure Streamlit secrets:
   Create a file `.streamlit/secrets.toml` with:
   ```toml
   [postgres]
   connection_uri = "postgresql://<user>:<password>@<host>:5432/<database>?sslmode=require"
   ```

4. Run the app locally:
   ```
   streamlit run AccountingDesk_IA.py
   ```

## Deployment

Deploy on Streamlit Cloud by connecting this repository and adding the `postgres.connection_uri` secret.