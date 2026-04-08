from benchmark.llm import LLMService

class NaiveDocGenerator:
    def __init__(self, llm: LLMService):
        self.llm = llm

    async def generate(self, code: str):
        prompt = f"""
Write a short Python docstring for this function:

{code}

Return ONLY the docstring.
"""
        return await self.llm.generate(prompt)