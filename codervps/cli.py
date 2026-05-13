from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from . import __version__


def _fail(message: str) -> None:
    """Report an error and exit non-zero."""
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


# ---- Command handler stubs ----
# Each returns int (0 for success). Real implementations are wired in later tasks.


def cmd_validate(args: argparse.Namespace) -> int:
    print("validate: not implemented yet")
    return 0


def cmd_refresh_catalog(args: argparse.Namespace) -> int:
    """Stub: refresh-catalog will be wired in Task 4."""
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    print(f"refresh-catalog: not implemented yet (would write to {output})")
    return 0


def cmd_render_generated(args: argparse.Namespace) -> int:
    """Stub: render-generated will be wired in Task 9."""
    output = Path(args.output)
    catalog = Path(args.catalog)
    if not catalog.exists():
        _fail(f"catalog file not found: {catalog}")
    output.mkdir(parents=True, exist_ok=True)
    print(f"render-generated: not implemented yet (catalog={catalog}, output={output})")
    return 0


def cmd_build_matrix(args: argparse.Namespace) -> int:
    """Stub: build-matrix will be wired in Task 8."""
    catalog = Path(args.catalog)
    if not catalog.exists():
        _fail(f"catalog file not found: {catalog}")
    if args.format == "github-output":
        print("matrix=[]")
    else:
        print("[]")
    return 0


# All commands are registered in this dict; the key maps to a subparser name.
COMMANDS: dict[str, Callable[[argparse.Namespace], int]] = {
    "validate": cmd_validate,
    "refresh-catalog": cmd_refresh_catalog,
    "render-generated": cmd_render_generated,
    "build-matrix": cmd_build_matrix,
}


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="codervps",
        description="Pluginized generator and runtime assets for CoderVPS workspaces",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="store_true", help="print version and exit")

    sub = parser.add_subparsers(dest="command", title="commands")

    # Register all commands via the COMMANDS dict
    for name in COMMANDS:
        sub.add_parser(name, help=f"{name} (not yet implemented)")

    # refresh-catalog takes --output
    sub.choices["refresh-catalog"].add_argument(
        "--output", default="build/toolchains.json", help="output path for toolchain catalog JSON"
    )

    # render-generated takes --catalog and --output
    sub.choices["render-generated"].add_argument(
        "--catalog", required=True, help="path to toolchains.json catalog"
    )
    sub.choices["render-generated"].add_argument(
        "--output", default="build/generated", help="output directory for generated tree"
    )

    # build-matrix takes --catalog and --format
    sub.choices["build-matrix"].add_argument(
        "--catalog", required=True, help="path to toolchains.json catalog"
    )
    sub.choices["build-matrix"].add_argument(
        "--format",
        choices=["json", "github-output"],
        default="json",
        help="output format (default: json)",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Returns exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"codervps {__version__}")
        return 0

    if args.command is None:
        parser.print_help()
        return 0

    handler = COMMANDS.get(args.command)
    if handler is None:
        _fail(f"unknown command: {args.command}")

    return handler(args)
