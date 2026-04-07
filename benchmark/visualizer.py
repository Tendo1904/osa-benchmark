import json
from collections import defaultdict
import matplotlib.pyplot as plt

class ResultVisualizer:
    def __init__(self, path="benchmark_result.json"):
        self.data = json.loads(open(path, encoding="utf-8").read())

    def summary(self):
        scores = defaultdict(list)

        for item in self.data["judge"]:
            t = item["type"]
            score = item["score"].get("score", 0)
            scores[t].append(score)

        print("\n=== AVERAGE SCORES ===")

        for k, vals in scores.items():
            avg = sum(vals) / len(vals) if vals else 0
            print(f"{k:10}: {avg:.2f}")

    def distribution(self):
        dist = defaultdict(lambda: defaultdict(int))

        for item in self.data["judge"]:
            t = item["type"]
            score = item["score"].get("score", 0)
            dist[t][score] += 1

        print("\n=== DISTRIBUTION ===")

        for k, d in dist.items():
            print(f"\n{k}:")
            for s in sorted(d):
                print(f"  {s}: {d[s]}")

    def worst_cases(self, n=5):
        print("\n=== WORST CASES ===")

        worst = sorted(
            self.data["judge"],
            key=lambda x: x["score"].get("score", 0)
        )[:n]

        for w in worst:
            print("\n---")
            print("ID:", w["id"])
            print("TYPE:", w["type"])
            print("SCORE:", w["score"])

    def plot_scores(self):
        scores = {"osa": [], "agent": [], "naive": []}

        for item in self.data["judge"]:
            t = item["type"]
            scores[t].append(item["score"].get("score", 0))

        for k, vals in scores.items():
            plt.hist(vals, alpha=0.5, label=k)

        plt.legend()
        plt.title("Score Distribution")
        plt.xlabel("Score")
        plt.ylabel("Count")
        plt.show()