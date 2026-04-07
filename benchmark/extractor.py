import ast
from pathlib import Path
from typing import Dict, List


class RepoExtractor:
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)

    def extract(self) -> Dict[str, List[dict]]:
        data = {}

        for py_file in self.repo_path.rglob("*.py"):
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)

            visitor = _ASTVisitor(source)
            visitor.visit(tree)

            if visitor.items:
                rel = str(py_file.relative_to(self.repo_path))
                data[rel] = visitor.items

        return data


class _ASTVisitor(ast.NodeVisitor):
    def __init__(self, source: str):
        self.source = source
        self.items = []

        # стек классов
        self.class_stack = []

    # --- Classes ---
    def visit_ClassDef(self, node: ast.ClassDef):
        self.class_stack.append(node.name)

        # можно добавить docstring класса (опционально)
        # doc = ast.get_docstring(node)

        self.generic_visit(node)

        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._handle_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._handle_function(node)
        self.generic_visit(node)

    def _handle_function(self, node):
        # формируем полный путь
        if self.class_stack:
            class_path = ".".join(self.class_stack)
            method_id = f"{class_path}.{node.name}"
        else:
            method_id = node.name

        doc = ast.get_docstring(node)
        code = ast.get_source_segment(self.source, node)

        self.items.append({
            "id": method_id,
            "code": code,
            "doc": doc
        })