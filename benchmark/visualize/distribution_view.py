from benchmark.visualize.base_view import BaseView
from collections import defaultdict

class DistributionView(BaseView):
    def render(self, data):
        print("\n=== DISTRIBUTION ===")

        dist = defaultdict(lambda: defaultdict(int))

        for repo in data["per_repo"].values():
            for j in repo["judge"]:
                score = j["score"].get("overall", 0)
                dist[j["type"]][score] += 1

        for t, d in dist.items():
            print(f"\n{t}:")
            for k, v in sorted(d.items()):
                print(f"  {k}: {v}")