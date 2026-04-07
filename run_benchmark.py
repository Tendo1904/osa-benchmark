from benchmark.pipeline import BenchmarkPipeline
from benchmark.visualizer import ResultVisualizer
import asyncio

if __name__ == "__main__":
    asyncio.run(BenchmarkPipeline("./repos").run())
    viz = ResultVisualizer()
    viz.summary()
    viz.worst_cases()
    viz.distribution()
    viz.plot_scores()