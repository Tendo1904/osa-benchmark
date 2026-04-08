from benchmark.metrics.coverage import CoverageMetric
from benchmark.metrics.bert import BertMetric
from benchmark.metrics.pairwise import PairwiseMetric


METRICS = [
    CoverageMetric(),
    BertMetric(),
    PairwiseMetric(), 
]