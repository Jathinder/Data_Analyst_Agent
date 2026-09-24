import sqlite3
import json
import ollama
from generate_sql import get_schema_context

def run_sql(query):
    """Executes SQL against chinook.db and returns rows as a string."""
    conn = sqlite3.connect("chinook.db")
    try:
        cursor = conn.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return json.dumps({"columns": columns, "rows": rows})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()

TOOLS = [{
    "type": "function",
    "function": {
        "name": "run_sql",
        "description": "Run a SQLite query against the chinook.db database and return the results.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "A valid SQLite SELECT query."}
            },
            "required": ["query"]
        }
    }
}]

def run_agent(question, schema, max_steps=5):
    messages = [{
        "role": "system",
        "content": f"""You are a data analyst agent with access to a SQLite database.
Schema:
{schema}

Use the run_sql tool to query the database as many times as needed to fully answer the question.
If the question asks you to compare multiple things (e.g. two countries, two time periods), you MUST run a separate query for each one before answering — do not use LIMIT to guess which one is highest.
Once you have enough information, respond with a final natural-language answer WITHOUT calling the tool again."""
    }, {
        "role": "user",
        "content": question
    }]

    for step in range(1, max_steps + 1):
        response = ollama.chat(model="llama3.1", messages=messages, tools=TOOLS)
        msg = response["message"]

        if msg.get("tool_calls"):
            messages.append(msg)
            for call in msg["tool_calls"]:
                query = call["function"]["arguments"]["query"]
                print(f"\nStep {step} — running SQL:\n{query}")
                result = run_sql(query)
                print(f"Result: {result}")
                messages.append({
                    "role": "tool",
                    "content": result
                })
        else:
            content = msg["content"]
            # Detect the model faking a tool call as text instead of using tool_calls
            if '"name": "run_sql"' in content or "'name': 'run_sql'" in content:
                print(f"\nStep {step} — model wrote a fake tool call instead of using tools. Nudging it to retry properly.")
                messages.append(msg)
                messages.append({
                    "role": "user",
                    "content": "Don't write the tool call as text — actually call the run_sql tool."
                })
                continue
            print(f"\nFinal answer (after {step} step(s)):")
            print(content)
            return content

    return "Agent did not converge on an answer within the step limit."

if __name__ == "__main__":
    schema = get_schema_context("chinook.db")
    question = "Compare total revenue between the USA and Canada, and tell me which is higher."
    run_agent(question, schema)


