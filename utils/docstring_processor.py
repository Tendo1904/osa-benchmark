
import json
from dataclasses import dataclass
from io import StringIO
from typing import Dict, List, Optional, Tuple, Union
import libcst as cst
from libcst.metadata import MetadataWrapper, PositionProvider
from markdown import Markdown
from pathlib import Path
import subprocess
import sys


# ----------------------------
# Models
# ----------------------------
@dataclass(frozen=True)
class Target:
    node_type: str  # "ClassDef" | "FunctionDef"
    name: str
    docstring: str
    start_line: Optional[int] = None  # from code_start_line, if provided


# ----------------------------
# CST Transformer (ONLY transformation)
# ----------------------------
class DocstringInjector(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, targets: List[Target], source_lines: List[str], default_indent: str):
        self.targets = targets
        self.source_lines = source_lines
        self.default_indent = default_indent
        self.docstrings_upserted = 0

    def _escape_triple_quotes(self, text: str) -> str:
        return text.replace('"""', r'\"\"\"')

    def _escape_backslashes(self, text: str) -> str:
        return text.replace("\\", "\\\\")

    def _format_docstring_literal(self, text: str, indent: str) -> str:

        text = (text or "").rstrip("\n")
        text = self._escape_triple_quotes(text)
        text = self._escape_backslashes(text)

        lines = text.splitlines()
        inner = "\n".join((indent + ln) if ln.strip() else "" for ln in lines)

        return f'"""\n{inner}\n{indent}"""'

    def _make_docstring_stmt(self, docstring_value: str) -> cst.SimpleStatementLine:
        return cst.SimpleStatementLine(
            body=[cst.Expr(value=cst.SimpleString(value=docstring_value))]
        )

    def _is_docstring_stmt(self, stmt: cst.CSTNode) -> bool:
        if not isinstance(stmt, cst.SimpleStatementLine):
            return False
        if len(stmt.body) != 1:
            return False
        expr = stmt.body[0]
        if not isinstance(expr, cst.Expr):
            return False
        return isinstance(expr.value, cst.SimpleString)

    def _upsert_docstring_in_block(
        self,
        block: cst.IndentedBlock,
        doc_stmt: cst.SimpleStatementLine,
    ) -> Tuple[cst.IndentedBlock, bool]:
        body = list(block.body)
        if body and self._is_docstring_stmt(body[0]):
            body[0] = doc_stmt
            return block.with_changes(body=body), True
        body.insert(0, doc_stmt)
        return block.with_changes(body=body), True

    def _upsert_docstring_in_suite(
        self,
        body: cst.BaseSuite,
        doc_stmt: cst.SimpleStatementLine,
    ) -> Tuple[cst.BaseSuite, bool]:
        if isinstance(body, cst.IndentedBlock):
            return self._upsert_docstring_in_block(body, doc_stmt)

        if isinstance(body, cst.SimpleStatementSuite):
            existing_lines: List[cst.BaseStatement] = [
                cst.SimpleStatementLine(body=list(body.body))
            ]
            new_block = cst.IndentedBlock(body=[doc_stmt] + existing_lines)
            return new_block, True

        return body, False

    def _match_target(self, node: cst.CSTNode, node_type: str, name: str) -> Optional[Target]:
        pos = self.get_metadata(PositionProvider, node, None)
        node_start_line = pos.start.line if pos else None

        for t in self.targets:
            if t.node_type != node_type or t.name != name:
                continue
            if t.start_line is not None and node_start_line is not None:
                if t.start_line == node_start_line:
                    return t

        for t in self.targets:
            if t.node_type == node_type and t.name == name and t.start_line is None:
                return t

        for t in self.targets:
            if t.node_type == node_type and t.name == name:
                return t

        return None

    def _get_body_indent(self, original_node: cst.CSTNode) -> str:

        pos = self.get_metadata(PositionProvider, original_node, None)
        if not pos:
            return self.default_indent

        line = self.source_lines[pos.start.line - 1]
        prefix = line[:pos.start.column]  # пробелы/табы до def/class
        return prefix + self.default_indent

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        t = self._match_target(original_node, "FunctionDef", original_node.name.value)
        if not t:
            return updated_node

        indent = self._get_body_indent(original_node)
        doc_value = self._format_docstring_literal(t.docstring, indent)
        doc_stmt = self._make_docstring_stmt(doc_value)

        new_body, changed = self._upsert_docstring_in_suite(updated_node.body, doc_stmt)
        if changed:
            self.docstrings_upserted += 1
        return updated_node.with_changes(body=new_body)

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        t = self._match_target(original_node, "ClassDef", original_node.name.value)
        if not t:
            return updated_node

        indent = self._get_body_indent(original_node)
        doc_value = self._format_docstring_literal(t.docstring, indent)
        doc_stmt = self._make_docstring_stmt(doc_value)

        new_body, changed = self._upsert_docstring_in_suite(updated_node.body, doc_stmt)
        if changed:
            self.docstrings_upserted += 1
        return updated_node.with_changes(body=new_body)


# ----------------------------
# Processor / Orchestration
# ----------------------------
class DocstringProcessor:
    def __init__(self, repo_path: str | Path, dry_run: bool = False):
        self.repo_root = Path(repo_path).resolve()
        self.dry_run = dry_run
        self.total_docstrings = 0
        # prepare markdown->plain converter
        self._patch_markdown()

    # --- markdown -> plain helpers ---
    def _unmark_element(self, element, stream=None):
        if stream is None:
            stream = StringIO()
        if element.text:
            stream.write(element.text)
        for sub in element:
            self._unmark_element(sub, stream)
        if element.tail:
            stream.write(element.tail)
        return stream.getvalue()

    def _patch_markdown(self):
        Markdown.output_formats["plain"] = self._unmark_element
        self.md = Markdown(output_format="plain")
        self.md.stripTopLevelTags = False

    def _unmark(self, text: str) -> str:
        return self.md.convert(text)

    # --- docstring formatting ---
    def _escape_triple_quotes(self, text: str) -> str:
        return text.replace('"""', r'\"\"\"')

    def _escape_backslashes(self, text: str) -> str:
        # It’s usually enough to only escape backslashes for safe string literal emission.
        # Escaping '/' is not needed in Python strings.
        return text.replace("\\", "\\\\")

    def _to_docstring(self, text: str) -> str:
        text = text.rstrip("\n")
        text = self._escape_triple_quotes(text)
        text = self._escape_backslashes(text)
        return f'"""\n{text}\n"""'

    # --- hierarchy IO ---
    def _load_hierarchy(self, json_path: Path) -> Dict[str, list]:
        return json.loads(json_path.read_text(encoding="utf-8"))

    def _extract_targets(self, items: list) -> List[Target]:
        targets: List[Target] = []

        for item in items:
            node_type = item.get("type")
            name = item.get("name")

            md_content = item.get("md_content", [])
            if not isinstance(md_content, list) or len(md_content) == 0:
                continue

            md_text = md_content[0] if len(md_content) >= 1 else ""
            if not isinstance(md_text, str) or not md_text.strip():
                continue

            plain = self._unmark(md_text)
            docstring = plain

            start_line = item.get("code_start_line")
            sl: Optional[int] = start_line if isinstance(start_line, int) else None

            if node_type in ("ClassDef", "FunctionDef") and isinstance(name, str) and name:
                targets.append(
                    Target(node_type=node_type, name=name, docstring=docstring, start_line=sl)
                )

        return targets

    # --- per-file processing ---
    def process_file(self, rel_path: str, items: list, write: bool) -> Tuple[bool, int, str]:
        file_path = self.repo_root / rel_path
        if not file_path.exists() or not file_path.is_file():
            return False, 0, f"[skip] not found: {rel_path}"

        targets = self._extract_targets(items)
        if not targets:
            return False, 0, f"[skip] no targets with md_content: {rel_path}"

        code = file_path.read_text(encoding="utf-8")
        try:
            module = cst.parse_module(code)
        except Exception as e:
            return False, 0, f"[error] parse failed {rel_path}: {e}"

        wrapper = MetadataWrapper(module)
        transformer = DocstringInjector(
            targets=targets,
            source_lines=code.splitlines(True),   # True = сохраняем '\n'
            default_indent=module.default_indent, # indent файла (обычно "    ")
        )
        new_module = wrapper.visit(transformer)
        new_code = new_module.code
        upserted = transformer.docstrings_upserted

        if new_code == code:
            return False, 0, f"[ok] unchanged: {rel_path}"

        if write:
            file_path.write_text(new_code, encoding="utf-8")
            return True, upserted, f"[ok] updated: {rel_path} (+{upserted} docstrings)"

        return True, upserted, f"[ok] would update (dry-run): {rel_path} (+{upserted} docstrings)"

    def count_non_empty_md_content(self, json_path: Union[str, bytes]) -> int:
        """
        Counts objects with non-empty md_content field in the given JSON file.

        A field is considered non-empty if:
        - it exists
        - it is a list
        - it contains at least one non-empty (non-whitespace) string
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        count = 0

        for file_items in data.values():  # values are lists of objects
            for item in file_items:
                md_content = item.get("md_content")

                if (
                        isinstance(md_content, list)
                        and any(isinstance(text, str) and text.strip() for text in md_content)
                ):
                    count += 1

        return count

    def validate_docstring_count(self) -> bool:
        """
        Compares number of non-empty md_content entries in JSON
        with number of actually upserted docstrings.

        Returns True if counts match, otherwise False.
        """

        json_path = self.repo_root / ".project_doc_record" / "project_hierarchy.json"

        expected = self.count_non_empty_md_content(json_path)
        actual = self.total_docstrings

        print("\n--- Validation Report ---")
        print(f"Expected docstrings (non-empty md_content): {expected}")
        print(f"Actual docstrings inserted:               {actual}")

        if expected == actual:
            print("✅ Counts match.")
            return True
        else:
            diff = expected - actual
            if diff > 0:
                print(f"⚠ Missing docstrings: {diff}")
            else:
                print(f"⚠ Extra docstrings inserted: {-diff}")
            return False

    def validate_compilation(self) -> bool:
        """
        Runs 'python -m compileall -q .' inside the repository root
        and checks that all Python files compile successfully.

        Returns True if compilation succeeded, otherwise False.
        """

        print("\n--- Compilation Check ---")
        print(f"Running compileall in: {self.repo_root}")

        result = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", "."],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ All Python files compiled successfully.")
            return True
        else:
            print("❌ Compilation failed.")
            if result.stderr:
                print("\n--- Errors ---")
                print(result.stderr.strip())
            return False

    # --- main run ---
    def run(self):
        json_path = self.repo_root / ".project_doc_record" / "project_hierarchy.json"
        if not json_path.exists():
            raise FileNotFoundError(f"JSON not found: {json_path}")

        hierarchy = self._load_hierarchy(json_path)

        changed_files = 0

        for rel_path, items in hierarchy.items():
            if not isinstance(items, list):
                continue

            did_change, doc_count, msg = self.process_file(
                rel_path=rel_path,
                items=items,
                write=not self.dry_run,
            )
            # print(msg)

            if did_change:
                changed_files += 1
                self.total_docstrings += doc_count

        print(
            f"\nRepo {str(self.repo_root).split('/')[-1]} was processed. Files changed: {changed_files}, "
            f"Docstrings upserted: {self.total_docstrings} "
            # f"(dry-run={self.dry_run})"
        )

        self.validate_docstring_count()

        if not self.dry_run:
            self.validate_compilation()
