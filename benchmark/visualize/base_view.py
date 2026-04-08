import json
from collections import defaultdict

class BaseView:
    def render(self, data):
        raise NotImplementedError