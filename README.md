# Data Analyst AI Agent

A natural-language-to-SQL agent that answers questions about a database in plain English. Runs entirely on a free local LLM (Ollama + Llama 3.1) — no API costs, no external calls.

## Features
- **Schema-grounded SQL generation** — the model is given the real table/column structure so it doesn't guess blind
- **Self-correction loop** — catches SQL execution errors and retries with the error fed back to the model (up to 3 attempts)
- **Multi-step tool-use agent** — for questions requiring multiple queries (e.g. comparisons across categories), the model decides how many queries to run and when it has enough information to answer
- **Evaluation harness** — automated accuracy benchmark across counts, filters, joins, and aggregations
- **Streamlit UI** — interactive interface showing the generated SQL, raw results, and final answer

## Results
- **100% accuracy** on a 10-question benchmark covering simple counts, filters, a multi-table join, and aggregations (SUM/AVG)
- Multi-step comparison questions (e.g. "compare revenue between two countries") work reliably after adding an explicit instruction against using `LIMIT` as a shortcut

## Key finding / limitation discovered
While testing multi-step tool use, I found that Llama 3.1 8B occasionally "fakes" a tool call by writing it as plain text instead of triggering the actual tool-calling mechanism — particularly right after recovering from a SQL error. I added detection logic that catches this pattern and re-prompts the model to use the real tool interface, which resolved it. This is a good example of a failure mode that's specific to smaller local models and wouldn't necessarily show up with larger hosted models.

## Tech Stack
- Python
- Ollama (Llama 3.1) — local LLM
- SQLite
- Streamlit

## How it works
1. Agent reads the database schema (tables, columns, types)
2. Question + schema sent to the LLM, which either calls `run_sql` or answers directly
3. SQL execution errors are caught and fed back to the model for correction
4. For multi-step questions, the model can call `run_sql` multiple times before answering
5. Final answer generated in natural language from the query results

## Setup
\`\`\`bash
python -m venv venv
venv\\Scripts\\activate  # Windows
pip install -r requirements.txt
ollama pull llama3.1
streamlit run app.py
\`\`\`

## Files
- `generate_sql.py` — schema reading + single-query SQL generation
- `agent.py` — self-correction retry loop
- `multi_agent.py` — multi-step tool-use agent for complex questions
- `evaluate.py` — accuracy benchmark
- `app.py` — Streamlit UI

## Example
**Q:** Compare total revenue between the USA and Canada, and tell me which is higher.
**A:** The country with the higher total revenue is the USA ($523.06 vs Canada's $303.96).