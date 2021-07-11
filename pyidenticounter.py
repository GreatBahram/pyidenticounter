import ast
import re
import sys
from argparse import ArgumentParser
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Iterator, NamedTuple, Pattern, Sized, Union

PYTHON_RE = re.compile(r"\.pyi?$")


class IdentifierType(str, Enum):
    VAR = "variable"
    FUNC = "func_or_method"
    CLASS = "class"

    def __str__(self) -> str:
        return self.value


class Report(NamedTuple):
    name: str
    type: IdentifierType
    lineno: int


class PyIdentifierCounter(ast.NodeVisitor):
    def check(self, source_code):
        self.identifiers = []
        tree = ast.parse(source_code)
        self.visit(tree)
        return self.identifiers

    def visit_Assign(self, node: ast.Assign) -> None:
        for name in node.targets:
            if name := getattr(name, "id", None):
                self.identifiers.append(Report(name, IdentifierType.VAR, node.lineno))

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.identifiers.append(Report(node.name, IdentifierType.FUNC, node.lineno))
        self.generic_visit(node)  # walk through any nested functions

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.identifiers.append(Report(node.name, IdentifierType.CLASS, node.lineno))
        self.generic_visit(node)  # walk through any nested classes

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name):
            if name := getattr(node.target, "id", None):
                self.identifiers.append(
                    Report(name, IdentifierType.VAR, node.target.lineno)
                )
        self.generic_visit(node)


def get_python_files(
    paths: Union[Path, str], pattern: Pattern[str] = PYTHON_RE
) -> Iterator[Path]:
    """Generate all files that match with a given pattern."""
    for entry in Path(paths).rglob("*"):
        if entry.is_file() and pattern.search(str(entry)):
            yield entry


def get_sources(paths: list[Path], pattern: Pattern[str] = PYTHON_RE) -> list[str]:
    """Compute a set of files to be validated."""
    sources = set()
    for entry in paths:
        entry = Path(entry)
        if entry.is_file() and pattern.search(str(entry)):
            sources.add(entry)
        elif entry.is_dir():
            sources.update(get_python_files(entry, pattern))
    return sources


def empty_path(sources: Sized, msg: str, quiet: bool) -> None:
    """Exit if there is not source to be validated."""
    if not sources:
        if not quiet:
            print(msg)
        sys.exit(0)


def report(identifier_map, verbose: int) -> None:
    for filename, identifiers in identifier_map.items():
        if verbose == 0:
            print(f"{filename}: {len(identifiers)}")
            continue
        elif verbose == 1:
            for path, identifiers in identifier_map.items():
                # groupby identifiers
                mapping = defaultdict(int)
                for item in identifiers:
                    mapping[item.type] += 1
                for iden_type, freq in mapping.items():
                    print(f"{path}:{iden_type}: {freq}")
        else:
            for (name, type, lineno) in identifiers:
                print(f"{filename}:{lineno}: {type} '{name}'")


def parse_files(sources: set[Path]) -> dict:
    identifiers_map = defaultdict(list)
    checker = PyIdentifierCounter()
    for src in sources:
        try:
            source_code = Path(src).read_text()
            identifiers_map[src] = checker.check(source_code)
        except SyntaxError:
            print(f"Parsing of file failed: {src}", file=sys.stderr)
            sys.exit(1)
    return identifiers_map


def main():
    parser = ArgumentParser(description="Count identifiers in python source codes.")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("-q", "--quiet", help="", default=False)
    parser.add_argument("paths", metavar="SRC", nargs="*", help="Python source files")
    args = parser.parse_args()

    if not args.paths:
        empty_path(args.paths, "No Path provided. Nothing to do 😴", args.quiet)
    sources = get_sources(args.paths)
    empty_path(
        sources,
        "No Python files are present to be examined. Nothing to do 😴",
        args.quiet,
    )
    identifiers_map = parse_files(sources)
    report(identifiers_map, args.verbose)


if __name__ == "__main__":
    main()
