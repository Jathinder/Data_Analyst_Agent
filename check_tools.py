import ollama

response = ollama.chat(
    model="llama3.1",
    messages=[{"role": "user", "content": "What's 2+2?"}],
    tools=[{
        "type": "function",
        "function": {
            "name": "add",
            "description": "Add two numbers",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["a", "b"]
            }
        }
    }]
)
print(response)