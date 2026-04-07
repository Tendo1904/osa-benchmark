from bert_score import score as bert_score

class Metrics:
    @staticmethod
    def coverage(samples, key):
        total = len(samples)
        filled = sum(1 for s in samples if s.docs.get(key))
        return filled / total if total else 0

    @staticmethod
    def bert(samples, pred_key, ref_key):
        preds = []
        refs = []

        for s in samples:
            if s.docs.get(pred_key) and s.docs.get(ref_key):
                preds.append(s.docs[pred_key])
                refs.append(s.docs[ref_key])

        if not preds:
            return None

        P, R, F1 = bert_score(preds, refs, lang="en", verbose=False)
        return float(F1.mean())