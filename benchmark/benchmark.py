from benchmark.judge import LLMJudge
from benchmark.merger import MethodSample
from tqdm.asyncio import tqdm_asyncio
from benchmark.naive_generator import NaiveDocGenerator
from benchmark.metrics.base import Metric
from typing import List
import asyncio
import logging
from .logging import setup_logger

setup_logger()
log = logging.getLogger(__name__)

class BenchmarkEngine:
    def __init__(self, samples: List[MethodSample], llm, metrics: List[Metric]):
        self.samples = samples
        self.llm = llm
        self.naive = NaiveDocGenerator(llm)
        self.metrics = metrics
        self.judge = LLMJudge(llm)

    async def run_judge(self):
        tasks = []
        log.info(f"Running judge on {len(self.samples)} samples")
        for s in self.samples:
            for tool in s.docs.keys():
                tasks.append(self._eval(s, tool))

        return await tqdm_asyncio.gather(*tasks)

    async def _eval(self, s, key):
        return {
            "repo": s.repo,
            "id": s.id,
            "type": key,
            "score": await self.judge.evaluate(s.code, s.docs.get(key))
        }
    
    async def generate_naive_all(self):
        tasks = []

        for s in self.samples:
            tasks.append(self._gen_naive(s))

        await tqdm_asyncio.gather(*tasks)

    async def _gen_naive(self, sample):
        sample.docs["naive"] = await self.naive.generate(sample.code)

    def compute_metrics(self):
        return {
            m.name: m.compute(self.samples)
            for m in self.metrics
        }
    
    async def compute_all_metrics(self):
        results = {}

        for m in self.metrics:
            try:
                result = m.compute(self.samples)

                # если async — ждём
                if asyncio.iscoroutine(result):
                    result = await result

            except TypeError:
                # fallback для метрик с judge
                result = m.compute(self.samples, judge=self.judge)

                if asyncio.iscoroutine(result):
                    result = await result

            results[m.name] = result

        return results