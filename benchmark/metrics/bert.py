from benchmark.metrics.base import Metric
from bert_score import score
from typing import List
from benchmark.merger import MethodSample

class BertMetric(Metric):
    name = "bert"

    def compute(self, samples: List[MethodSample]):
        preds, refs = [], []

        for s in samples:
            target_tool = "osa"

            doc_pred = s.docs.get(target_tool)
            doc_gt = s.docs.get("original")
            if doc_pred and doc_gt:
                preds.append(doc_pred)
                refs.append(doc_gt)

        if not preds:
            return "skipped"

        _, _, f1 = score(preds, refs, lang="en", verbose=False)
        return float(f1.mean())