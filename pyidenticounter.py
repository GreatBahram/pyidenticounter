import ast
import re
import sys
from argparse import ArgumentParser, ArgumentTypeError
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Iterator, NamedTuple, Optional, Pattern, Sized, Union

PYTHON_RE = re.compile(r"\.pyi?$")


class IdentifierType(str, Enum):
    VAR = "variable"
    FUNC = "func_or_method"
    CLASS = "class"
    ARG = "arg"

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
        for arg in node.args.args:
            # currently, we ignore self variable
            if arg.arg != "self":
                self.identifiers.append(Report(arg.arg, IdentifierType.ARG, arg.lineno))
        if node.args.vararg:
            self.identifiers.append(
                Report(
                    node.args.vararg.arg, IdentifierType.ARG, node.args.vararg.lineno
                )
            )
        if node.args.kwarg:
            self.identifiers.append(
                Report(node.args.kwarg.arg, IdentifierType.ARG, node.args.kwarg.lineno)
            )
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
    paths: Union[Path, str],
    pattern: Pattern[str] = PYTHON_RE,
    exclude: Optional[Pattern] = None,
) -> Iterator[Path]:
    """Generate all files that match with a given pattern."""
    for entry in Path(paths).rglob("*"):
        if entry.is_file() and pattern.search(str(entry)):
            if path_is_excluded(entry, exclude):
                continue
            yield entry


def path_is_excluded(path: Union[str, Path], exclude) -> bool:
    match = exclude.search(str(path)) if exclude else None
    return bool(match)


def get_sources(
    paths: list[Path],
    pattern: Pattern[str] = PYTHON_RE,
    exclude: Optional[Pattern] = None,
) -> set[Path]:
    """Compute a set of files to be validated."""
    sources = set()
    for entry in paths:
        entry = Path(entry)
        if (
            entry.is_file()
            and pattern.search(str(entry))
            and not path_is_excluded(str(entry), exclude)
        ):
            sources.add(entry)
        elif entry.is_dir():
            sources.update(get_python_files(entry, pattern, exclude))
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


def validate_regex_pattern(pattern: str) -> Pattern:
    try:
        return re.compile(pattern)
    except re.error:
        raise ArgumentTypeError("Invalid regex pattern") from None


def main():
    parser = ArgumentParser(description="Count identifiers in python source codes.")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("-q", "--quiet", help="", default=False)
    parser.add_argument(
        "-e",
        "--exclude",
        help="A regular expression that matches files and directories "
        + "that should be excluded on recursive searches.",
        type=validate_regex_pattern,
    )
    parser.add_argument("paths", metavar="SRC", nargs="*", help="Python source files")
    args = parser.parse_args()

    if not args.paths:
        empty_path(args.paths, "No Path provided. Nothing to do ????", args.quiet)
    sources = get_sources(args.paths, exclude=args.exclude)
    empty_path(
        sources,
        "No Python files are present to be examined. Nothing to do ????",
        args.quiet,
    )
    identifiers_map = parse_files(sources)
    report(identifiers_map, args.verbose)


if __name__ == "__main__":
    main()
