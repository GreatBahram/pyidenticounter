import ast
import re
import sys
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
from typing import Iterator, Pattern, Sized, Union

PYTHON_RE = re.compile(r"\.pyi?$")


class PyIdentifierCounter(ast.NodeVisitor):
    def __init__(self):
        self.identifier_map = defaultdict(list)

    def check(self, files):
        for filename in files:
            self.filename = filename
            try:
                tree = ast.parse(Path(filename).read_text())
                self.visit(tree)
            except SyntaxError:
                print(f"Parsing of file failed: {filename}", file=sys.stderr)
                sys.exit(1)

    def visit_Assign(self, node: ast.Assign) -> None:
        for name in node.targets:
            if name := getattr(name, "id", None):
                self.identifier_map[self.filename].append(
                    (name, "variable", node.lineno)
                )

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.identifier_map[self.filename].append(
            (node.name, "func_or_method", node.lineno)
        )
        self.generic_visit(node)  # walk through any nested functions

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.identifier_map[self.filename].append((node.name, "class", node.lineno))
        self.generic_visit(node)  # walk through any nested classes

    def report(self, verbose: bool = True):
        for filename, identifiers in self.identifier_map.items():
            if not verbose:
                print(f"{filename}: {len(identifiers)}")
                continue
            for (name, type, lineno) in identifiers:
                print(f"{filename}:{lineno}: {type} '{name}'")


def get_python_files(
    paths: Union[Path, str], pattern: Pattern[str] = PYTHON_RE
) -> Iterator[Path]:
    """Generate all files that match with a given pattern."""
    for entry in Path(paths).iterdir():
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


def main():
    parser = ArgumentParser(description="Count identifiers in python source codes.")
    parser.add_argument("-v", "--verbose", action="store_true")
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
    checker = PyIdentifierCounter()
    checker.check(sources)
    checker.report(args.verbose)


if __name__ == "__main__":
    main()
