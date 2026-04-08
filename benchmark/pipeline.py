from pathlib import Path
from collections import defaultdict
import json

from benchmark.extractor import RepoExtractor
from benchmark.merger import RepoMerger
from benchmark.llm import LLMService
from benchmark.benchmark import BenchmarkEngine
from benchmark.metrics.registry import METRICS

import logging
from benchmark.logging import setup_logger

setup_logger()
log = logging.getLogger(__name__)

class Pipeline:
    def __init__(self, base):
        self.base = Path(base)

    def discover(self):
        groups = defaultdict(dict)

        for p in self.base.iterdir():
            name = p.name

            if "_" not in name:
                continue

            prefix, repo_name = name.split("_", 1)
            groups[repo_name][prefix] = p

        return groups

    async def run(self):
        groups = self.discover()
        llm = LLMService()

        all_samples = []
        all_judge = []
        results = {}

        log.info(f"Discovered {len(groups)} repo groups")
        for name, repos in groups.items():
            log.info(f"[{name}] processing...")
            if not repos:
                log.warning(f"[{name}] skipped (no repos)")
                continue
            
            log.info(f"[{name}] extracting...")
            extracted = {}

            for tool, path in repos.items():
                log.info(f"[{name}] extracting {tool}...")
                extracted[tool] = RepoExtractor(path).extract()

            samples = RepoMerger(name, extracted).merge()

            engine = BenchmarkEngine(samples, llm, METRICS)

            log.info("Generating naive...")
            await engine.generate_naive_all()

            judge = await engine.run_judge()
            log.info("Processing metrics...")
            metrics = await engine.compute_all_metrics()

            results[name] = {
                "metrics": metrics,
                "judge": judge
            }

            all_samples.extend(samples)
            all_judge.extend(judge)

        global_metrics = await BenchmarkEngine(all_samples, llm, METRICS).compute_all_metrics()

        Path("benchmark_result.json").write_text(json.dumps({
            "per_repo": results,
            "global": global_metrics
        }, indent=2))