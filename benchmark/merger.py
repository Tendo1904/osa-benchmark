from pathlib import Path
from typing import List

class MethodSample:
    def __init__(self, repo, file, method_id, code):
        self.repo = repo
        self.file = file
        self.id = method_id
        self.code = code

        self.docs = {}


class RepoMerger:
    def __init__(self, repo_name: str, repos_dict: dict):
        self.repo_name = repo_name
        self.repos = repos_dict 

    def _find(self, repo, file, method_id):
        items = repo.get(file, [])

        # 1. точный матч
        for i in items:
            if i["id"] == method_id:
                return i["doc"]

        # 2. fallback: только имя метода
        short = method_id.split(".")[-1]

        for i in items:
            if i["id"].endswith(short):
                return i["doc"]

        return None

    def merge(self):
        dataset = []

        all_files = set()
        for repo in self.repos.values():
            all_files |= set(repo.keys())

        for file in all_files:
            all_ids = set()

            for repo in self.repos.values():
                all_ids |= {i["id"] for i in repo.get(file, [])}

            for mid in all_ids:
                code = None

                for repo in self.repos.values():
                    for i in repo.get(file, []):
                        if i["id"] == mid:
                            code = i["code"]
                            break

                s = MethodSample(self.repo_name, file, mid, code)

                for tool, repo in self.repos.items():
                    doc = self._find(repo, file, mid)
                    if doc:
                        s.docs[tool] = doc

                dataset.append(s)

        return dataset