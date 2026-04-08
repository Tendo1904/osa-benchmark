from benchmark.pipeline import Pipeline
from benchmark.visualize.visualizer import Visualizer
from benchmark.visualize.metrics_view import MetricsView
from benchmark.visualize.judge_stats_view import JudgeStatsView
from benchmark.visualize.distribution_view import DistributionView
import asyncio

if __name__ == "__main__":
    asyncio.run(Pipeline("./repos").run())
    v = Visualizer("benchmark_result.json")
    v.add_view(MetricsView())
    v.add_view(JudgeStatsView())
    v.add_view(DistributionView())
    v.run()