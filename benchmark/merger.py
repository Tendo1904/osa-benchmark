from pathlib import Path
from typing import List

class MethodSample:
    def __init__(self, file, method_id, code):
        self.file = file
        self.id = method_id
        self.code = code

        self.docs = {
            "osa": None,
            "agent": None,
            "original": None,
            "naive": None,
        }


class RepoMerger:
    def __init__(self, osa, agent, original=None):
        self.osa = osa
        self.agent = agent
        self.original = original or {}

    def _find_doc(self, repo, file, method_id):
        for item in repo.get(file, []):
            if item["id"] == method_id:
                return item["doc"]
        return None

    def merge(self):
        dataset = []

        for file, items in self.osa.items():
            for item in items:
                sample = MethodSample(file, item["id"], item["code"])

                sample.docs["osa"] = item["doc"]
                sample.docs["agent"] = self._find_doc(self.agent, file, item["id"])
                sample.docs["original"] = self._find_doc(self.original, file, item["id"])

                dataset.append(sample)

        return dataset