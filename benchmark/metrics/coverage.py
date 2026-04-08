from benchmark.metrics.base import Metric


class CoverageMetric(Metric):
    name = "coverage"

    def compute(self, samples):
        res = {}

        tools = set()
        for s in samples:
            tools |= set(s.docs.keys())

        for t in tools:
            total = len(samples)
            filled = sum(1 for s in samples if s.docs.get(t))
            res[t] = filled / total if total else 0

        return res