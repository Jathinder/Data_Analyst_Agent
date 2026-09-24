import sqlite3
import json
import re
import ollama

from generate_sql import get_schema_context


# =========================================================
# CONFIGURATION
# =========================================================

DB_PATH = "chinook.db"
MODEL = "llama3.1:latest"

# Lower = faster, but fewer chances for complex queries to recover
MAX_STEPS = 3


# =========================================================
# SQL TOOL
# =========================================================

def run_sql(query):
    """
    Execute a read-only SQL query against the Chinook database.
    """

    query = query.strip().rstrip(";")

    # Only allow SELECT / WITH
    if not re.match(r"^(SELECT|WITH)\b", query, re.IGNORECASE):
        return json.dumps({
            "error": "Only SELECT/WITH queries are allowed."
        })

    # Prevent multiple statements
    if ";" in query:
        return json.dumps({
            "error": "Multiple SQL statements are not allowed."
        })

    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.execute(query)

        columns = [
            description[0]
            for description in cursor.description
        ]

        rows = cursor.fetchall()

        return json.dumps({
            "columns": columns,
            "rows": rows
        })

    except Exception as e:

        return json.dumps({
            "error": str(e)
        })

    finally:
        conn.close()


# =========================================================
# TOOL DEFINITION
# =========================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": (
                "Execute a read-only SQLite SELECT query "
                "against the Chinook database."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "A valid SQLite SELECT or WITH query."
                        )
                    }
                },
                "required": ["query"]
            }
        }
    }
]


# =========================================================
# AGENT
# =========================================================

def run_agent(question, max_steps=MAX_STEPS):

    schema = get_schema_context(DB_PATH)

    messages = [
        {
            "role": "system",
            "content": f"""
You are a fast AI data analyst.

DATABASE SCHEMA:
{schema}

You have one tool:

run_sql(query)

RULES:

1. ALWAYS use run_sql to get real database data.
2. NEVER invent tables or columns.
3. Only use tables and columns from the schema.
4. Only generate SELECT or WITH queries.
5. Never use INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
6. If SQL fails, fix it and call run_sql again.
7. Do not guess database values.
8. Avoid unnecessary JOINs.
9. For revenue, use Invoice.Total.
10. For revenue by country, use Invoice.BillingCountry.
11. Customer country is Customer.Country.
12. Once you have the result, give a SHORT direct answer.
13. Do NOT repeat the SQL in the final answer.
14. Do NOT explain your reasoning.
15. Do NOT write tool calls as text. Actually call run_sql.

IMPORTANT:
Use the database result to answer the user's question.
"""
        },
        {
            "role": "user",
            "content": question
        }
    ]

    last_sql = ""
    last_error = None

    successful_columns = []
    successful_rows = []

    for step in range(1, max_steps + 1):

        response = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            options={
                "temperature": 0,
                "num_predict": 150
            }
        )

        message = response["message"]

        # =================================================
        # TOOL CALL
        # =================================================

        if message.get("tool_calls"):

            messages.append(message)

            for call in message["tool_calls"]:

                function = call["function"]

                tool_name = function["name"]
                arguments = function["arguments"]

                if tool_name != "run_sql":
                    continue

                # Ollama may return arguments as dict or string
                if isinstance(arguments, str):

                    try:
                        arguments = json.loads(arguments)

                    except json.JSONDecodeError:

                        arguments = {}

                query = arguments.get(
                    "query",
                    ""
                ).strip()

                last_sql = query

                print(
                    f"\nAgent step {step} — SQL:\n{query}"
                )

                result = run_sql(query)

                print(
                    f"Result:\n{result}"
                )

                try:
                    result_data = json.loads(result)

                except json.JSONDecodeError:

                    result_data = {
                        "error": "Invalid tool response."
                    }

                # =================================================
                # SQL ERROR
                # =================================================

                if "error" in result_data:

                    last_error = result_data["error"]

                    messages.append({
                        "role": "tool",
                        "content": result
                    })

                    messages.append({
                        "role": "user",
                        "content": f"""
SQL failed.

SQL:
{query}

Error:
{last_error}

Fix the SQL using ONLY the provided database schema.

Call run_sql again.
"""
                    })

                # =================================================
                # SUCCESS
                # =================================================

                else:

                    successful_columns = result_data.get(
                        "columns",
                        []
                    )

                    successful_rows = result_data.get(
                        "rows",
                        []
                    )

                    last_error = None

                    messages.append({
                        "role": "tool",
                        "content": result
                    })

            continue

        # =================================================
        # FINAL ANSWER
        # =================================================

        answer = message.get(
            "content",
            ""
        ).strip()

        if answer:

            # Prevent accidental tool-call text
            if (
                '"name": "run_sql"' in answer
                or "'name': 'run_sql'" in answer
            ):

                messages.append(message)

                messages.append({
                    "role": "user",
                    "content": (
                        "Actually call the run_sql tool. "
                        "Do not write a tool call as text."
                    )
                })

                continue

            return {
                "answer": answer,
                "sql": last_sql,
                "columns": successful_columns,
                "rows": successful_rows,
                "steps": step,
                "error": last_error
            }

    # =====================================================
    # MAX STEPS REACHED
    # =====================================================

    return {
        "answer": (
            "The analysis could not be completed. "
            "Please try a simpler question."
        ),
        "sql": last_sql,
        "columns": successful_columns,
        "rows": successful_rows,
        "steps": max_steps,
        "error": last_error
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    question = "How many customers are there?"

    result = run_agent(question)

    print("\n" + "=" * 60)
    print("FINAL ANSWER")
    print("=" * 60)

    print(result["answer"])

    print("\nGenerated SQL:")
    print(result["sql"])

    print("\nColumns:")
    print(result["columns"])

    print("\nRows:")
    print(result["rows"])

    print(
        f"\nAgent steps used: {result['steps']}"
    )

    if result["error"]:

        print(
            f"\nLast error: {result['error']}"
        )