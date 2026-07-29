import ollama


def extract_claims(response: str):

    prompt = f"""
Extract every factual claim from the following response.

Return ONLY a JSON array.

Example:

[
"Claim one",
"Claim two"
]

Response:

{response}
"""

    result = ollama.chat(
        model="llama3.2:3b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    text = result["message"]["content"]

    import json

    try:
        return json.loads(text)
    except:
        return [response]