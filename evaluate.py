from generate_sql import get_schema_context
from agent import run_query_with_retry

# Each test case: (question, expected_answer)
# expected_answer is the single number/value the correct SQL should return
test_cases = [
    # Simple counts
    ("How many customers are there?", 59),
    ("How many employees are there?", 8),
    ("How many tracks are in the database?", 3503),
    ("How many albums are there?", 347),
    ("How many playlists are there?", 18),

    # Filters
    ("How many customers are from the USA?", 13),
    ("How many tracks are longer than 5 minutes?", 1069),

    # Joins
    ("How many invoices does the customer with CustomerId 1 have?", 7),
    ("What is the total revenue from all invoices?", 2328.6),

    # Aggregations
    ("What is the average unit price of a track?", 1.05),
]
def extract_single_value(rows):
    """Pulls out a single number from a one-row, one-column result."""
    if len(rows) == 1 and len(rows[0]) == 1:
        return rows[0][0]
    return None

def evaluate(test_cases, schema, db_path):
    results = []
    correct = 0

    for question, expected in test_cases:
        print(f"\nTesting: {question}")
        try:
            sql, columns, rows = run_query_with_retry(question, schema, db_path)
            actual = extract_single_value(rows)
            if isinstance(expected, float) and actual is not None:
                is_correct=abs(actual-expected) < 0.5
            else:
                is_correct = actual == expected

            if is_correct:
                correct += 1
                print(f"CORRECT — got {actual}")
            else:
                print(f"WRONG — expected {expected}, got {actual}")

            results.append({
                "question": question,
                "expected": expected,
                "actual": actual,
                "sql": sql,
                "correct": is_correct
            })
        except Exception as e:
            print(f"FAILED — {e}")
            results.append({
                "question": question,
                "expected": expected,
                "actual": None,
                "sql": None,
                "correct": False
            })

    accuracy = correct / len(test_cases)
    return accuracy, results

if __name__ == "__main__":
    db_path = "chinook.db"
    schema = get_schema_context(db_path)

    accuracy, results = evaluate(test_cases, schema, db_path)

    print("\n" + "=" * 40)
    print(f"ACCURACY: {accuracy * 100:.1f}% ({sum(r['correct'] for r in results)}/{len(results)})")
    print("=" * 40)

    for r in results:
        status = "PASS" if r["correct"] else "FAIL"
        print(f"[{status}] {r['question']}")