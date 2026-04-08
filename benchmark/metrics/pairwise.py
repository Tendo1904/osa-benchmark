from benchmark.metrics.base import Metric
from collections import defaultdict
from tqdm.asyncio import tqdm_asyncio


class PairwiseMetric(Metric):
    name = "pairwise"

    def compute(self, samples, judge):
        if judge is None:
            return {}

        return self._compute_async(samples, judge)

    async def _compute_async(self, samples, judge):
        all_tools = set()
        for s in samples:
            all_tools |= set(s.docs.keys())

        tools = list(all_tools)

        results = defaultdict(lambda: defaultdict(int))
        counts = defaultdict(lambda: defaultdict(int))

        tasks = []

        for s in samples:
            for i in range(len(tools)):
                for j in range(i + 1, len(tools)):
                    t1, t2 = tools[i], tools[j]

                    d1 = s.docs.get(t1)
                    d2 = s.docs.get(t2)

                    if not d1 or not d2:
                        continue

                    tasks.append(
                        self._compare(judge, s.code, t1, d1, t2, d2)
                    )

        results_raw = await tqdm_asyncio.gather(*tasks)

        for t1, t2, winner in results_raw:
            if winner == "A":
                results[t1][t2] += 1
            elif winner == "B":
                results[t2][t1] += 1

            counts[t1][t2] += 1
            counts[t2][t1] += 1

        # нормализация
        final = {}
        for t1 in results:
            final[t1] = {}
            for t2 in results[t1]:
                total = counts[t1][t2]
                final[t1][t2] = results[t1][t2] / total if total else 0

        return final

    async def _compare(self, judge, code, t1, d1, t2, d2):
        winner = await judge.compare(code, d1, d2)
        return t1, t2, winner