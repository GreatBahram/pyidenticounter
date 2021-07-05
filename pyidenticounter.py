import ast
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path


class PyIdentifierCounter(ast.NodeVisitor):
    def __init__(self):
        self.identifier_map = defaultdict(list)

    def check(self, files):
        for filename in files:
            self.filename = filename
            tree = ast.parse(Path(filename).read_text())
            self.visit(tree)

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


def main():
    parser = ArgumentParser(description="Count identifiers in python source codes.")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("files", metavar="SRC", nargs="+", help="Python source files")
    args = parser.parse_args()

    checker = PyIdentifierCounter()
    checker.check(args.files)
    checker.report(args.verbose)


if __name__ == "__main__":
    main()
