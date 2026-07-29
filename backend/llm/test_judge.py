from backend.llm.judge import judge

query = "Who invented the telephone?"

response = "Alexander Graham Bell invented the first practical telephone."

result = judge.evaluate(query, response)

print(result)