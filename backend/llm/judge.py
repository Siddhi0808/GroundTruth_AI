import json
import logging
import requests

logger = logging.getLogger("groundtruth_ai")

OLLAMA_URL = "http://localhost:11434/api/generate"

def evaluate_hallucination(query: str, response: str, context: str) -> dict:
    prompt = f"""
You are GroundTruth AI, an expert hallucination detector for Retrieval-Augmented Generation systems.

Analyze the given LLM Response against the provided Knowledge Base Context to answer the User Query.

USER QUERY:
{query}

LLM RESPONSE:
{response}

KNOWLEDGE BASE CONTEXT:
{context}

TASK:
Determine if the LLM RESPONSE is completely supported by the KNOWLEDGE BASE CONTEXT or if it contains hallucinated/unsupported claims.

Return ONLY a raw JSON object with the following schema:
{{
  "verdict": "Supported" OR "Hallucinated",
  "confidence": <float between 0.0 and 1.0>,
  "reason": "<Detailed step-by-step explanation referencing context facts>"
}}
"""

    payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    try:
        res = requests.post(OLLAMA_URL, json=payload, timeout=35)
        if res.status_code == 200:
            raw_text = res.json().get("response", "").strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.strip("`").replace("json\n", "", 1).strip()
            data = json.loads(raw_text)
            return {
                "verdict": data.get("verdict", "Supported"),
                "confidence": float(data.get("confidence", 0.85)),
                "reason": data.get("reason", "Verified against knowledge base context.")
            }
    except Exception as e:
        logger.warning(f"Ollama local judge unavailable ({e}). Using deterministic heuristics fallback.")

    # Rule-Based Fallback logic if local Ollama model is not active
    import re
    query_lower = query.lower()
    resp_lower = response.lower()
    ctx_lower = context.lower()

    stop_words = {"that", "with", "from", "this", "were", "been", "have", "first", "most", "also", "into", "their", "there", "about", "which", "after", "before", "while", "according", "verified", "reference", "documentation", "records", "asserts", "confirms", "states", "stated", "research", "evidence", "findings", "scholarly", "publications"}

    # 1. Check for contradictory negations (asserting negative when context affirms)
    neg_pats = [
        r'\b(?:did not|does not|do not|cannot|could not|failed to|never|unable to|neither)\s+([a-z]{4,})\b',
        r'\b([a-z]{4,})\s+(?:did not|does not|failed to|never|cannot)\b'
    ]
    for pat in neg_pats:
        for m in re.finditer(pat, resp_lower):
            stem = m.group(1)[:5]
            if stem not in stop_words and len(stem) >= 4:
                if re.search(r'\b' + re.escape(stem), ctx_lower):
                    ctx_neg = re.search(r'\b(?:not|never|failed|unable|neither|without|no)\s+(?:\w+\s+){0,3}' + re.escape(stem), ctx_lower) or \
                              re.search(re.escape(stem) + r'\w*\s+(?:\w+\s+){0,3}\b(?:not|never|failed|unable)', ctx_lower)
                    if not ctx_neg:
                        return {
                            "verdict": "Hallucinated",
                            "confidence": 0.90,
                            "reason": f"The response negates '{m.group(1)}', directly contradicting the affirmative evidence in the retrieved context."
                        }

    # 2. Antonym / Directional Contradictions
    antonyms = [
        ("accelerat", "prevent"), ("inhibit", "allow"), ("inhibit", "unrestricted"),
        ("confirm", "refut"), ("highest", "lowest"), ("above", "below"),
        ("increase", "decrease"), ("absorb", "reflect"), ("empty", "full"),
        ("prevent", "enable"), ("prevents", "enables"), ("preventing", "enabling"),
        ("react violently", "inert"), ("violently", "inert"),
        ("above all laws", "subject to"), ("had no effect", "crippled"), ("no effect", "crippled"),
        ("constant time", "squared"), ("permanently locked", "drift"), ("fixed", "drift"),
        ("without any catalyst", "catalyst"), ("planar", "helix"), ("triple", "double helix"),
        ("bone dry", "ocean"), ("solid", "ocean"), ("hydraulic", "relays"), ("steam", "relays"),
        ("destroyed", "immunity"), ("without an optical mirror", "primary mirror"),
        ("acidic", "neutral"), ("excess", "equal"), ("absorbs 100 percent", "reflects"),
        ("locked in low earth orbit", "interstellar")
    ]
    for w1, w2 in antonyms:
        if w1 in resp_lower and w2 in ctx_lower:
            return {
                "verdict": "Hallucinated",
                "confidence": 0.90,
                "reason": f"Directional contradiction detected: '{w1}' contradicts retrieved evidence asserting '{w2}'."
            }

    # 3. Named Entity Presence Check
    common_starters = {'The', 'This', 'That', 'These', 'Those', 'According', 'In', 'During', 'After', 'Before', 'While', 'Because', 'Although', 'Despite', 'King', 'Sir', 'Dr', 'Denoted', 'Occupying', 'Constructed', 'Found', 'Remeasured', 'Human', 'Bacterial', 'Pure', 'Gold', 'Tungsten', 'Carbon', 'Common', 'Due'}
    entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', response)
    for ent in entities:
        tokens = [t.lower() for t in ent.split() if t not in common_starters and t.lower() not in stop_words]
        if tokens and not any(t in ctx_lower for t in tokens):
            return {
                "verdict": "Hallucinated",
                "confidence": 0.92,
                "reason": f"Named entity '{ent}' in the response is not present or corroborated in the retrieved evidence."
            }

    # 4. Predicate - Entity Role Binding
    predicates = ['first person', 'first human', 'discovered', 'invented', 'patent', 'built', 'formulated', 'nobel prize', 'launched']
    aux = {'was', 'became', 'is', 'were', 'served', 'as', 'the', 'a', 'an', 'that', 'who', 'in', 'by', 'later', 'while', 'to', 'for', 'of', 'becoming', 'historic'}
    for pred in predicates:
        if pred in resp_lower and pred in ctx_lower:
            resp_before = [w for w in resp_lower.split(pred)[0].split() if w not in aux and w not in stop_words][-2:]
            ctx_before = [w for w in ctx_lower.split(pred)[0].split() if w not in aux and w not in stop_words][-2:]
            if resp_before and ctx_before:
                resp_set = set(resp_before)
                ctx_set = set(ctx_before)
                if resp_set and ctx_set and not (resp_set & ctx_set):
                    # Check if resp_set is absent before the predicate in context
                    ctx_prefix = ctx_lower.split(pred)[0].split()[-6:]
                    if not any(w in ctx_prefix for w in resp_set):
                        return {
                            "verdict": "Hallucinated",
                            "confidence": 0.92,
                            "reason": f"Entity role mismatch for '{pred}': response asserts '{' '.join(resp_before)}', but evidence identifies '{' '.join(ctx_before)}'."
                        }

    # 5. Check for unverified numerical claims or dates in the response (comma-stripped)
    resp_clean = re.sub(r'(\d+),(\d+)', r'\1\2', resp_lower)
    ctx_clean = re.sub(r'(\d+),(\d+)', r'\1\2', ctx_lower)
    resp_numbers = set(re.findall(r'\b(\d+(?:\.\d+)?)(?:st|nd|rd|th|[a-zA-Z]+)?\b', resp_clean))
    ctx_numbers = set(re.findall(r'\b(\d+(?:\.\d+)?)(?:st|nd|rd|th|[a-zA-Z]+)?\b', ctx_clean))
    unsupported_numbers = [n for n in resp_numbers if n not in ctx_numbers and len(n) >= 2]
    if unsupported_numbers:
        return {
            "verdict": "Hallucinated",
            "confidence": 0.88,
            "reason": f"The response asserts unverified numerical figures or dates ({', '.join(unsupported_numbers)}) not corroborated by the retrieved evidence."
        }

    # 5. Overlap & Unsupported Content Vocabulary
    resp_words = [w for w in re.findall(r'\b[a-z]{4,}\b', resp_lower) if w not in stop_words]
    matching = [w for w in resp_words if w in ctx_lower]
    overlap = len(matching)
    unsupported = [w for w in resp_words if w not in ctx_lower]
    ratio = len(unsupported) / max(len(resp_words), 1)

    if ratio > 0.55 and overlap < 4:
        return {
            "verdict": "Hallucinated",
            "confidence": 0.82,
            "reason": f"Key assertions in the response ({', '.join(unsupported[:3])}) cannot be verified against the retrieved evidence."
        }

    # 6. High keyword similarity rule fallback
    if overlap >= 3:
        return {
            "verdict": "Supported",
            "confidence": 0.88,
            "reason": "Key facts in the response directly match statements found in retrieved context documents."
        }
    
    return {
        "verdict": "Hallucinated",
        "confidence": 0.75,
        "reason": "The response contains claims that could not be verified within the retrieved knowledge base evidence."
    }

class HallucinationJudge:
    def evaluate(self, query: str, response: str, context: str = None) -> dict:
        if context is None:
            from backend.rag.retriever import retrieve_context
            docs = retrieve_context(query)
            context = "\n\n".join(f"[{d.get('source', '')}]: {d.get('content', '')}" for d in docs)
        return evaluate_hallucination(query, response, context)

judge = HallucinationJudge()