#!/usr/bin/env python3
"""Static checker for MISRA-like violations in signal-decode source files.

Checks performed
----------------
MISRA 10.3  int() truncation of a float expression — any call to the built-in
            int() whose sole argument is a multiplication or addition expression
            is flagged as a potential narrowing conversion.

MISRA 16.4  if/elif chain without an explicit else branch inside any function
            named 'decode' — every dispatch table must have a catch-all case.
"""

import ast
import os
import sys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_arithmetic(node: ast.expr) -> bool:
    """Return True if *node* looks like a float arithmetic expression."""
    return isinstance(node, (ast.BinOp,))


def check_file(filepath: str) -> list[str]:
    """Return a list of violation strings for *filepath*."""
    with open(filepath, encoding="utf-8") as fh:
        source = fh.read()

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as exc:
        return [f"{filepath}:0: SyntaxError: {exc}"]

    violations: list[str] = []

    for node in ast.walk(tree):
        # MISRA 10.3 — int() wrapping an arithmetic expression
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "int"
            and len(node.args) == 1
            and _is_arithmetic(node.args[0])
        ):
            violations.append(
                f"{filepath}:{node.lineno}: [MISRA-10.3] int() truncation of "
                f"float arithmetic expression"
            )

        # MISRA 16.4 — decode() function with if/elif but no else
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "decode"
        ):
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.If):
                    # Walk the elif/else chain to the end
                    current = stmt
                    while isinstance(current, ast.If) and current.orelse:
                        inner = current.orelse
                        # orelse is a single If node for elif, or a list of stmts for else
                        if len(inner) == 1 and isinstance(inner[0], ast.If):
                            current = inner[0]
                        else:
                            current = None  # has an else clause
                            break
                    if current is not None:  # walked to the end without finding else
                        violations.append(
                            f"{filepath}:{stmt.lineno}: [MISRA-16.4] if/elif "
                            f"chain in 'decode' has no else branch"
                        )
                    break  # only report once per decode() function

    return violations


def main(src_dir: str) -> int:
    all_violations: list[str] = []
    for root, _dirs, files in os.walk(src_dir):
        for fname in sorted(files):
            if fname.endswith(".py"):
                all_violations.extend(check_file(os.path.join(root, fname)))

    if all_violations:
        for v in all_violations:
            print(v)
        return 1

    print("check_standard: no blocking violations found.")
    return 0


if __name__ == "__main__":
    src_path = sys.argv[1] if len(sys.argv) > 1 else "src/"
    sys.exit(main(src_path))
