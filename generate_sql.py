import sqlite3
import ollama

def get_schema_context(db_path):
    conn = sqlite3.connect(db_path)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    schema = {}
    for (table,) in tables:
        cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
        schema[table] = [(c[1], c[2]) for c in cols]  # name, type
    conn.close()
    return schema

def generate_sql(question, schema):
    prompt = f"""You are a SQL expert. Here is a database schema:

{schema}

Write a single SQLite query to answer this question:
"{question}"

Rules:
- Output ONLY the raw SQL query
- No markdown formatting, no explanation, no backticks
"""
    response = ollama.chat(
        model="llama3.1",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"].strip()

if __name__ == "__main__":
    schema = get_schema_context("chinook.db")
    question = "How many customers are there?"
    sql = generate_sql(question, schema)
    print("Generated SQL:")
    print(sql)
    