import json
import logging
import ollama

logger = logging.getLogger("groundtruth_ai")

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

    try:
        result = ollama.chat(
            model="llama3.2",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        text = result["message"]["content"]
        return json.loads(text)
    except Exception as e:
        logger.warning(f"Ollama claim extraction unavailable ({e}). Falling back to raw response.")
        return [response]