from benchmark.visualize.base_view import BaseView

class MetricsView(BaseView):
    def render(self, data):
        print("\n=== METRICS ===")

        for repo, val in data["per_repo"].items():
            print(f"\n{repo}:")
            for k, v in val["metrics"].items():
                print(f"  {k}: {v}")