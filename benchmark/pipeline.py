from pathlib import Path
from benchmark.extractor import RepoExtractor
from benchmark.merger import RepoMerger
from benchmark.llm import LLMService
from benchmark.benchmark import BenchmarkEngine
import json

class BenchmarkPipeline:
    def __init__(self, base_path):
        self.base = Path(base_path)

    def _find_repo(self, prefix):
        for p in self.base.iterdir():
            if p.name.startswith(prefix):
                return p
        return None

    async def run(self):
        osa_repo = self._find_repo("osa_")
        agent_repo = self._find_repo("repoagent_")
        original_repo = self._find_repo("original_")

        extractor = RepoExtractor

        osa = extractor(osa_repo).extract()
        agent = extractor(agent_repo).extract()
        original = {}
        if original_repo:
            original = extractor(original_repo).extract()

        samples = RepoMerger(osa, agent, original).merge()

        llm = LLMService()
        engine = BenchmarkEngine(samples, llm)

        print("Generating naive docstrings...")
        await engine.generate_naive_all()

        print("Running LLM judge...")
        judge_results = await engine.evaluate_all()

        print("Computing metrics...")
        metrics = engine.compute_metrics()

        result = {
            "metrics": metrics,
            "judge": judge_results
        }

        Path("benchmark_result.json").write_text(json.dumps(result, indent=2))
        print("Done.")
