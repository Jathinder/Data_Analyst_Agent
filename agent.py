import sqlite3
import ollama
from generate_sql import get_schema_context, generate_sql

def execute_sql(sql, db_path):
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return columns, rows
    finally:
        conn.close()

def run_query_with_retry(question, schema, db_path, max_retries=3):
    original_question = question
    last_sql = None
    for attempt in range(1, max_retries + 1):
        sql = generate_sql(question, schema)
        last_sql = sql
        print(f"\nAttempt {attempt} — generated SQL:\n{sql}")
        try:
            columns, rows = execute_sql(sql, db_path)
            return sql, columns, rows
        except Exception as e:
            print(f"Failed: {e}")
            question = (
                f"{original_question}\n\n"
                f"Previous SQL failed with error: {e}\n"
                f"Previous SQL: {sql}\n"
                f"Fix it and output only the corrected SQL."
            )
    raise Exception(f"Failed after {max_retries} attempts. Last SQL tried: {last_sql}")

def generate_answer(question, columns, rows):
    prompt = f"""Question: "{question}"
Columns: {columns}
Result rows: {rows}

Answer the question in one clear sentence, using the data above."""
    response = ollama.chat(
        model="llama3.1",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"].strip()

if __name__ == "__main__":
    db_path = "chinook.db"
    schema = get_schema_context(db_path)

    question = "How many customers are there?"
    sql, columns, rows = run_query_with_retry(question, schema, db_path)

    print("\nColumns:", columns)
    print("Rows:", rows)

    answer = generate_answer(question, columns, rows)
    print("\nFinal Answer:")
    print(answer)
    