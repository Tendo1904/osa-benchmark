import ast
from pathlib import Path


class RepoExtractor:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)

    def extract(self):
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
    def __init__(self, source):
        self.source = source
        self.items = []
        self.class_stack = []

    def visit_ClassDef(self, node):
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node):
        self._handle(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._handle(node)
        self.generic_visit(node)

    def _handle(self, node):
        if self.class_stack:
            method_id = ".".join(self.class_stack) + f".{node.name}"
        else:
            method_id = node.name

        self.items.append({
            "id": method_id,
            "code": ast.get_source_segment(self.source, node),
            "doc": ast.get_docstring(node)
        })