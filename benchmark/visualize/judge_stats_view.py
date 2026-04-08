from benchmark.visualize.base_view import BaseView
from collections import defaultdict

class JudgeStatsView(BaseView):
    def render(self, data):
        print("\n=== JUDGE STATS ===")

        scores = defaultdict(lambda: defaultdict(list))

        for repo, val in data["per_repo"].items():
            for j in val["judge"]:
                t = j["type"]
                for k, v in j["score"].items():
                    scores[t][k].append(v)

        for t, crits in scores.items():
            print(f"\n{t}:")
            for c, vals in crits.items():
                avg = sum(vals)/len(vals)
                print(f"  {c}: {avg:.2f}")