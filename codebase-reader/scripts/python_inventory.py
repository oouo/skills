#!/usr/bin/env python3
"""Create a read-only static inventory of Python source files."""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
import tokenize
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence, Union


DISCLAIMER = (
    "AST results are static candidate relationships, not a precise runtime "
    "call graph. Target modules were read but never imported or executed."
)

EXCLUDED_DIRECTORIES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "site-packages",
    "venv",
}


FunctionNode = Union[ast.FunctionDef, ast.AsyncFunctionDef]
DefinitionNode = Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]


def node_text(node: Optional[ast.AST]) -> str:
    """Return a compact source-like representation without evaluating a node."""
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except (AttributeError, ValueError, TypeError):
        return node.__class__.__name__


def qualified_expression(node: ast.AST) -> str:
    """Return a dotted name for simple call and attribute expressions."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = qualified_expression(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return f"{qualified_expression(node.func)}(...)"
    if isinstance(node, ast.Subscript):
        return f"{qualified_expression(node.value)}[...]"
    return node_text(node)


def literal_string(node: Optional[ast.AST]) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def location(node: ast.AST) -> dict[str, int]:
    result = {"line": int(getattr(node, "lineno", 0) or 0)}
    end_line = int(getattr(node, "end_lineno", result["line"]) or result["line"])
    result["end_line"] = end_line
    return result


def parameter_names(arguments: ast.arguments) -> list[str]:
    names = [argument.arg for argument in arguments.posonlyargs]
    names.extend(argument.arg for argument in arguments.args)
    if arguments.vararg:
        names.append(f"*{arguments.vararg.arg}")
    names.extend(argument.arg for argument in arguments.kwonlyargs)
    if arguments.kwarg:
        names.append(f"**{arguments.kwarg.arg}")
    return names


class InventoryVisitor(ast.NodeVisitor):
    """Collect symbols and static call candidates while preserving lexical scope."""

    def __init__(self) -> None:
        self.symbols: list[dict[str, Any]] = []
        self.candidate_calls: list[dict[str, Any]] = []
        self.environment_variables: list[dict[str, Any]] = []
        self._scope_names: list[str] = []
        self._scope_kinds: list[str] = []
        self._await_depth = 0
        self._seen_environment_accesses: set[tuple[str, int, str]] = set()
        self._os_module_names = {"os"}
        self._environ_names: set[str] = set()
        self._getenv_names: set[str] = set()

    def current_scope(self) -> str:
        return ".".join(self._scope_names) if self._scope_names else "<module>"

    def _decorators(self, node: DefinitionNode) -> list[str]:
        return [node_text(decorator) for decorator in node.decorator_list]

    def _record_symbol(
        self,
        node: DefinitionNode,
        kind: str,
        parameters: Optional[Sequence[str]] = None,
    ) -> None:
        qualname = ".".join([*self._scope_names, node.name])
        symbol: dict[str, Any] = {
            "name": node.name,
            "qualname": qualname,
            "kind": kind,
            "decorators": self._decorators(node),
            **location(node),
        }
        if parameters is not None:
            symbol["parameters"] = list(parameters)
        self.symbols.append(symbol)

    def _visit_definition_expressions(
        self, node: FunctionNode
    ) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        for default in [*node.args.defaults, *node.args.kw_defaults]:
            if default is not None:
                self.visit(default)
        if node.returns:
            self.visit(node.returns)
        for argument in [
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        ]:
            if argument.annotation:
                self.visit(argument.annotation)
        if node.args.vararg and node.args.vararg.annotation:
            self.visit(node.args.vararg.annotation)
        if node.args.kwarg and node.args.kwarg.annotation:
            self.visit(node.args.kwarg.annotation)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self._record_symbol(node, "class")
        for decorator in node.decorator_list:
            self.visit(decorator)
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)
        self._scope_names.append(node.name)
        self._scope_kinds.append("class")
        for statement in node.body:
            self.visit(statement)
        self._scope_kinds.pop()
        self._scope_names.pop()

    def _visit_function(
        self, node: FunctionNode, asynchronous: bool
    ) -> None:
        is_method = bool(self._scope_kinds and self._scope_kinds[-1] == "class")
        if asynchronous and is_method:
            kind = "async_method"
        elif asynchronous:
            kind = "async_function"
        elif is_method:
            kind = "method"
        else:
            kind = "function"
        self._record_symbol(node, kind, parameter_names(node.args))
        self._visit_definition_expressions(node)
        self._scope_names.append(node.name)
        self._scope_kinds.append("function")
        for statement in node.body:
            self.visit(statement)
        self._scope_kinds.pop()
        self._scope_names.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._visit_function(node, asynchronous=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._visit_function(node, asynchronous=True)

    def visit_Lambda(self, node: ast.Lambda) -> None:  # noqa: N802
        name = f"<lambda@{getattr(node, 'lineno', 0)}>"
        qualname = ".".join([*self._scope_names, name])
        self.symbols.append(
            {
                "name": name,
                "qualname": qualname,
                "kind": "lambda",
                "decorators": [],
                "parameters": parameter_names(node.args),
                **location(node),
            }
        )
        self._scope_names.append(name)
        self._scope_kinds.append("lambda")
        self.visit(node.body)
        self._scope_kinds.pop()
        self._scope_names.pop()

    def visit_Await(self, node: ast.Await) -> None:  # noqa: N802
        self._await_depth += 1
        self.visit(node.value)
        self._await_depth -= 1

    def _record_environment(
        self, name: Optional[str], line: int, access: str
    ) -> None:
        if not name:
            return
        key = (name, line, access)
        if key in self._seen_environment_accesses:
            return
        self._seen_environment_accesses.add(key)
        self.environment_variables.append(
            {"name": name, "line": line, "access": access}
        )

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            if alias.name == "os":
                self._os_module_names.add(alias.asname or alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.module != "os":
            return
        for alias in node.names:
            local_name = alias.asname or alias.name
            if alias.name == "environ":
                self._environ_names.add(local_name)
            elif alias.name == "getenv":
                self._getenv_names.add(local_name)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        callee = qualified_expression(node.func)
        self.candidate_calls.append(
            {
                "caller": self.current_scope(),
                "callee": callee,
                "line": int(getattr(node, "lineno", 0) or 0),
                "awaited": self._await_depth > 0,
            }
        )

        first_argument = literal_string(node.args[0]) if node.args else None
        os_getenv_calls = {f"{name}.getenv" for name in self._os_module_names}
        os_environ_get_calls = {
            f"{name}.environ.get" for name in self._os_module_names
        }
        environ_get_calls = {f"{name}.get" for name in self._environ_names}
        if callee in os_getenv_calls or callee in self._getenv_names:
            self._record_environment(first_argument, node.lineno, callee)
        elif callee in os_environ_get_calls or callee in environ_get_calls:
            self._record_environment(first_argument, node.lineno, callee)

        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:  # noqa: N802
        container = qualified_expression(node.value)
        os_environ_names = {f"{name}.environ" for name in self._os_module_names}
        if container in os_environ_names or container in self._environ_names:
            self._record_environment(
                literal_string(node.slice), node.lineno, f"{container}[]"
            )
        self.generic_visit(node)


def top_level_summary(node: ast.stmt) -> str:
    if isinstance(node, ast.Import):
        return "import " + ", ".join(alias.name for alias in node.names)
    if isinstance(node, ast.ImportFrom):
        module = node.module or ""
        names = ", ".join(alias.name for alias in node.names)
        return f"from {module} import {names}"
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return f"{node.__class__.__name__} {node.name}"
    text = node_text(node).replace("\n", " ")
    return text[:157] + "..." if len(text) > 160 else text


def top_level_code(tree: ast.Module) -> list[dict[str, Any]]:
    statements: list[dict[str, Any]] = []
    for index, node in enumerate(tree.body):
        if (
            index == 0
            and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        statements.append(
            {
                "kind": node.__class__.__name__,
                "summary": top_level_summary(node),
                **location(node),
            }
        )
    return statements


def discover_python_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix == ".py" else []

    files: list[Path] = []
    for root, directories, filenames in os.walk(target):
        directories[:] = sorted(
            directory
            for directory in directories
            if directory not in EXCLUDED_DIRECTORIES
        )
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                files.append(Path(root) / filename)
    return files


def display_path(path: Path, target: Path) -> str:
    if target.is_file():
        return path.name
    try:
        return path.relative_to(target).as_posix()
    except ValueError:
        return path.as_posix()


def inventory_file(path: Path, target: Path) -> dict[str, Any]:
    shown_path = display_path(path, target)
    try:
        with tokenize.open(path) as source_file:
            source = source_file.read()
        tree = ast.parse(source, filename=shown_path)
    except SyntaxError as error:
        return {
            "path": shown_path,
            "error": {
                "type": "SyntaxError",
                "message": error.msg,
                "line": error.lineno,
                "offset": error.offset,
            },
        }
    except (OSError, UnicodeError) as error:
        return {
            "path": shown_path,
            "error": {"type": error.__class__.__name__, "message": str(error)},
        }

    visitor = InventoryVisitor()
    visitor.visit(tree)
    visitor.symbols.sort(key=lambda item: (item["line"], item["qualname"]))
    visitor.candidate_calls.sort(
        key=lambda item: (item["line"], item["caller"], item["callee"])
    )
    visitor.environment_variables.sort(
        key=lambda item: (item["line"], item["name"], item["access"])
    )

    return {
        "path": shown_path,
        "symbols": visitor.symbols,
        "top_level_code": top_level_code(tree),
        "environment_variables": visitor.environment_variables,
        "candidate_calls": visitor.candidate_calls,
    }


def build_inventory(target: Path) -> dict[str, Any]:
    files = discover_python_files(target)
    return {
        "disclaimer": DISCLAIMER,
        "root": str(target.resolve()),
        "files_scanned": len(files),
        "files": [inventory_file(path, target) for path in files],
    }


def print_human(inventory: dict[str, Any]) -> None:
    print(DISCLAIMER)
    print(f"Root: {inventory['root']}")
    print(f"Files scanned: {inventory['files_scanned']}")
    for file_inventory in inventory["files"]:
        print(f"\n## {file_inventory['path']}")
        if "error" in file_inventory:
            error = file_inventory["error"]
            line = f" at line {error['line']}" if error.get("line") else ""
            print(f"Error: {error['type']}{line}: {error['message']}")
            continue

        print("Symbols:")
        for symbol in file_inventory["symbols"]:
            decorators = (
                f" decorators={','.join(symbol['decorators'])}"
                if symbol["decorators"]
                else ""
            )
            print(
                f"  L{symbol['line']}-L{symbol['end_line']} "
                f"{symbol['kind']} {symbol['qualname']}{decorators}"
            )

        print("Top-level code:")
        for statement in file_inventory["top_level_code"]:
            print(
                f"  L{statement['line']}-L{statement['end_line']} "
                f"{statement['kind']}: {statement['summary']}"
            )

        print("Environment variables:")
        for access in file_inventory["environment_variables"]:
            print(f"  L{access['line']} {access['name']} via {access['access']}")

        print("Candidate calls (static):")
        for call in file_inventory["candidate_calls"]:
            awaited = " awaited" if call["awaited"] else ""
            print(
                f"  L{call['line']} {call['caller']} -> {call['callee']}{awaited}"
            )


def parse_arguments(arguments: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read Python source with the standard-library AST and report symbols, "
            "decorators, top-level code, environment variable names, and static "
            "candidate calls without importing or executing target modules."
        )
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Python file or directory to inspect (default: current directory)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of the human-readable report",
    )
    return parser.parse_args(arguments)


def main(arguments: Optional[Iterable[str]] = None) -> int:
    options = parse_arguments(arguments)
    target = Path(options.path).expanduser()
    if not target.exists():
        print(f"error: path does not exist: {target}", file=sys.stderr)
        return 2
    if not target.is_file() and not target.is_dir():
        print(f"error: path is not a file or directory: {target}", file=sys.stderr)
        return 2
    if target.is_file() and target.suffix != ".py":
        print(f"error: expected a .py file: {target}", file=sys.stderr)
        return 2

    target = target.resolve()
    inventory = build_inventory(target)
    if options.json:
        print(json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_human(inventory)

    return 1 if any("error" in item for item in inventory["files"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
