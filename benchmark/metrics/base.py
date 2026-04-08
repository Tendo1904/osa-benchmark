from benchmark.merger import MethodSample
from  typing import List

class Metric:
    name = "base"

    def compute(self, samples: List[MethodSample]):
        raise NotImplementedError
    
class AsyncMetric:
    name = "async_base"

    def compute(self, samples, **kwargs):
        raise NotImplementedError