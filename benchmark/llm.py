from pathlib import Path
from protollm.connectors import create_llm_connector
from protollm.connectors import CustomChatOpenAI
from langchain_core.messages import HumanMessage
import asyncio
import hashlib
import os
import json
from dotenv import load_dotenv
import logging
from .logging import setup_logger

setup_logger()
log = logging.getLogger(__name__)

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
        self.cache = json.loads(self.cache_path.read_text()) if self.cache_path.exists() else {}

    def _hash(self, text):
        return hashlib.md5(text.encode()).hexdigest()

    def _normalize(self, res):
        if hasattr(res, "content"):
            return res.content
        return str(res)

    async def generate(self, prompt):
        key = self._hash(prompt)

        if key in self.cache:
            return self.cache[key]

        def call():
            return self.connector.invoke([HumanMessage(content=prompt)])

        res = await asyncio.to_thread(call)
        text = self._normalize(res)

        self.cache[key] = text
        self.cache_path.write_text(json.dumps(self.cache, indent=2))

        return text