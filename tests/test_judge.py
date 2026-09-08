import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.llm.judge import judge

def test_judge_telephone():
    query = "Who invented the telephone?"
    response = "Alexander Graham Bell invented the first practical telephone."
    result = judge.evaluate(query, response)
    print("Judge Result:", result)
    assert result.get("verdict") in ["Supported", "Hallucinated"]

if __name__ == "__main__":
    test_judge_telephone()
