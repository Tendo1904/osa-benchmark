import json
from benchmark.visualize.base_view import BaseView

class Visualizer:
    def __init__(self, path):
        self.data = json.load(open(path, encoding="utf-8"))
        self.views = []

    def add_view(self, view: BaseView):
        self.views.append(view)

    def run(self):
        for v in self.views:
            v.render(self.data)