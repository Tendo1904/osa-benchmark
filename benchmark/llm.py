from pathlib import Path
from protollm.connectors import create_llm_connector
from protollm.connectors import CustomChatOpenAI
from langchain_core.messages import HumanMessage
import asyncio
import ast
import hashlib
import os
import json
import re
from dotenv import load_dotenv

load_dotenv(".env")

class LLMService:
    def __init__(self, model="openai/gpt-5-mini", cache_path="llm_cache.json"):
        self.model = model

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env")

        self.connector: CustomChatOpenAI = create_llm_connector(
            model_url="https://openrouter.ai/api/v1;qwen/qwen3-30b-a3b-instruct-2507"
        )

        self.cache_path = Path(cache_path)

        if self.cache_path.exists():
            self.cache = json.loads(self.cache_path.read_text())
        else:
            self.cache = {}

    def _hash(self, text: str):
        return hashlib.md5(text.encode()).hexdigest()

    def _normalize(self, result):
        if isinstance(result, str):
            return result

        if isinstance(result, dict):
            return (
                result.get("text")
                or result.get("content")
                or result.get("response")
                or ""
            )

        return str(result)

    async def generate(self, prompt: str) -> str:
        key = self._hash(prompt)

        if key in self.cache:
            return self.cache[key]

        def call():
            response = self.connector.invoke([
                HumanMessage(content=prompt)
            ])
            return response

        result = await asyncio.to_thread(call)
        result = self._normalize(result)

        self.cache[key] = result
        self.cache_path.write_text(json.dumps(self.cache, indent=2))

        return result

class NaiveDocGenerator:
    def __init__(self, llm: LLMService):
        self.llm = llm

    async def generate(self, code: str) -> str:
        prompt = f"""
        Write a concise Python docstring for this function:

        {code}

        Return only the docstring.
        """
        return await self.llm.generate(prompt)
    

class LLMJudge:
    def __init__(self, llm: LLMService, debug=True):
        self.llm = llm
        self.debug = debug

    def extract_json(self, text: str):
        # убираем markdown
        text = text.replace("```json", "").replace("```", "").strip()

        # ищем ВСЕ JSON объекты
        matches = re.findall(r"\{.*?\}", text, re.DOTALL)

        if not matches:
            return None

        # берём ПЕРВЫЙ (или можно лучший)
        return matches[0]
    
    def fix_json_escapes(self, text: str) -> str:
        # убираем невалидные \' → '
        text = text.replace("\\'", "'")
        return text
    
    def clean_json(self, text: str):
        # фиксим \' → '
        text = text.replace("\\'", "'")

        # иногда бывают лишние символы в конце
        text = text.strip()

        return text
    
    def safe_parse(self, text: str):
        try:
            return json.loads(text)
        except:
            try:
                return ast.literal_eval(text)
            except:
                return None

    def normalize_judge_output(self, parsed: dict):
        if not parsed:
            return {"score": 0, "reason": "empty"}

        score = parsed.get("score")

        # альтернативные ключи
        if score is None:
            score = parsed.get("rating")

        # если строка → int
        if isinstance(score, str):
            try:
                score = int(score)
            except:
                score = None

        # clamp
        if isinstance(score, (int, float)):
            score = int(score)
            score = max(1, min(score, 5))
        else:
            score = 0

        return {
            "score": score,
            "reason": parsed.get("reason", "")
        }

    async def evaluate(self, code: str, doc: str) -> dict:
        if not doc or not doc.strip():
            return {"score": 0, "reason": "empty_doc"}

        prompt = f"""
        You are evaluating a Python docstring.

        Code:
        {code}

        Docstring:
        {doc}

        Rate from 1 to 5 based on:
        - correctness
        - completeness
        - usefulness

        Return ONLY a valid JSON object.
        No text before or after JSON:
        {{"score": int, "reason": "short explanation"}}
        Do NOT use any other keys.
        Do NOT return null
        """

        raw = await self.llm.generate(prompt)

        if self.debug:
            print("\n--- LLM JUDGE RAW ---")
            print(raw[:500])
            print("---------------------")

        try:
            json_str = self.extract_json(raw)
            if json_str:
                parsed = self.safe_parse(json_str)
                if parsed:
                    return self.normalize_judge_output(parsed)

        except Exception as e:
            if self.debug:
                print("JSON PARSE ERROR:", e)

            return {
                "score": 0,
                "reason": "parse_error",
                "raw": raw[:300]
            }