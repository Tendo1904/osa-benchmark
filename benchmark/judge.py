import json, re, ast

def extract_json(text):
    text = text.replace("```json", "").replace("```", "")
    matches = re.findall(r"\{.*?\}", text, re.DOTALL)
    return matches[0] if matches else None


def safe_parse(text):
    try:
        return json.loads(text)
    except:
        try:
            return ast.literal_eval(text)
        except:
            return None


def normalize(parsed):
    if not parsed:
        return {"score": 0}

    score = parsed.get("score") or parsed.get("rating")

    try:
        score = int(score)
    except:
        score = 0

    return {"score": max(1, min(score, 5))}

class LLMJudge:
    def __init__(self, llm, debug=False):
        self.llm = llm
        self.debug = debug

    async def compare(self, code, d1, d2):
        prompt = f"""
Which docstring is better?

Code:
{code}

Docstring A:
{d1}

Docstring B:
{d2}

Return ONLY JSON:
{{"winner": "A" or "B"}}
"""
        raw = await self.llm.generate(prompt)
        js = extract_json(raw)
        parsed = safe_parse(js)

        if isinstance(parsed, dict):
            return parsed.get("winner")

        return None

    async def evaluate(self, code, doc):
        if not doc:
            return {"overall": 0}

        prompt = f"""
Evaluate this Python docstring.

Code:
{code}

Docstring:
{doc}

Return ONLY JSON:
{{
  "correctness": 1-5,
  "completeness": 1-5,
  "clarity": 1-5,
  "hallucination": 1-5,
  "overall": 1-5
}}
"""

        raw = await self.llm.generate(prompt)

        js = extract_json(raw)
        parsed = safe_parse(js) if js else None

        if self.debug:
            print("\nRAW:", raw[:200])
            print("PARSED:", parsed)

        return self._normalize(parsed)

    def _normalize(self, p):
        keys = ["correctness", "completeness", "clarity", "hallucination", "overall"]

        res = {}
        for k in keys:
            try:
                val = int(p.get(k, 0))
                res[k] = max(1, min(val, 5))
            except:
                res[k] = 0

        return res