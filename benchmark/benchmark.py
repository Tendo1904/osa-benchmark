from benchmark.llm import NaiveDocGenerator, LLMJudge, LLMService
from benchmark.merger import MethodSample
from benchmark.metrics import Metrics
from typing import List
import asyncio

class BenchmarkEngine:
    def __init__(self, samples: List[MethodSample], llm: LLMService):
        self.samples = samples
        self.llm = llm
        self.naive = NaiveDocGenerator(llm)
        self.judge = LLMJudge(llm)

    async def generate_naive_all(self):
        tasks = []

        for s in self.samples:
            tasks.append(self._gen_naive(s))

        await asyncio.gather(*tasks)

    async def _gen_naive(self, sample):
        sample.docs["naive"] = await self.naive.generate(sample.code)

    async def evaluate_all(self):
        tasks = []

        for s in self.samples:
            for key in ["osa", "agent", "naive"]:
                tasks.append(self._judge_one(s, key))

        return await asyncio.gather(*tasks)

    async def _judge_one(self, sample, key):
        doc = sample.docs.get(key)
        return {
            "id": sample.id,
            "type": key,
            "score": await self.judge.evaluate(sample.code, doc)
        }

    def compute_metrics(self):
        has_gt = any(s.docs.get("original") for s in self.samples)

        metrics = {
            "coverage": {
                k: Metrics.coverage(self.samples, k)
                for k in ["osa", "agent", "naive"]
            }
        }

        if has_gt:
            metrics["bert"] = {
                "osa": Metrics.bert(self.samples, "osa", "original"),
                "agent": Metrics.bert(self.samples, "agent", "original"),
                "naive": Metrics.bert(self.samples, "naive", "original"),
            }
        else:
            metrics["bert"] = "skipped (no ground truth)"

        return metrics