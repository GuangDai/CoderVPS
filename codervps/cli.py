from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from . import __version__


def _fail(message: str) -> None:
    """Report an error and exit non-zero."""
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def _load_catalog(catalog_path: str) -> dict:
    """Load and parse a catalog JSON file, exiting on error."""
    path = Path(catalog_path)
    if not path.exists():
        _fail(f"catalog file not found: {path}")
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        _fail(f"failed to read catalog {path}: {exc}")


# ---- Real command handlers ----


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate source configuration and generated assets."""
    try:
        config_dir = Path("config")
        if not config_dir.exists():
            _fail("config directory not found")

        toolchains_path = config_dir / "toolchains.toml"
        if not toolchains_path.exists():
            _fail("config/toolchains.toml not found")

        extensions_path = config_dir / "extensions.toml"
        if not extensions_path.exists():
            _fail("config/extensions.toml not found")

        from .config import load_extensions_config, load_toolchains_config

        tc_cfg = load_toolchains_config(toolchains_path)
        if not tc_cfg.enabled_plugins:
            _fail("no plugins enabled in toolchains config")
        if not tc_cfg.node_majors:
            _fail("no Node.js majors configured")

        ext_cfg = load_extensions_config(extensions_path)
        if not ext_cfg.core_marketplace:
            _fail("no core extensions configured")

        print("validate: OK")
        return 0
    except (OSError, ValueError, KeyError) as exc:
        _fail(f"validation failed: {exc}")
        return 1


def cmd_refresh_catalog(args: argparse.Namespace) -> int:
    """Refresh toolchain catalog from upstream metadata or fixtures."""
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    fixture_dir = None
    if args.fixture_dir:
        fixture_dir = Path(args.fixture_dir)

    from .catalog import refresh_catalog
    from .config import load_toolchains_config

    try:
        cfg = load_toolchains_config(Path("config/toolchains.toml"))
        catalog = refresh_catalog(cfg, fixture_dir=fixture_dir)
    except (OSError, ValueError, KeyError) as exc:
        _fail(f"catalog refresh failed: {exc}")
        return 1

    output.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")
    print(f"catalog written to {output}", file=sys.stderr)
    return 0


def cmd_render_generated(args: argparse.Namespace) -> int:
    """Render the full generated branch tree."""
    output = Path(args.output)
    catalog = _load_catalog(args.catalog)

    from .render.generated import render_generated_tree

    try:
        # Build images dict from --images if provided, else default to empty
        images = {"schema_version": 1, "images": []}
        images_path = args.images if getattr(args, "images", None) else None
        if images_path:
            raw = json.loads(Path(images_path).read_text())
            # Accept both dict format {"schema_version": 1, "images": [...]}
            # and list format [...] (from build-matrix --format json)
            if isinstance(raw, list):
                images = {"schema_version": 1, "images": raw}
            else:
                images = raw

        write_flag = getattr(args, "write_images_json", False)

        render_generated_tree(
            output_dir=output,
            catalog=catalog,
            images=images,
            write_images_json=write_flag,
        )
    except (OSError, ValueError, KeyError) as exc:
        _fail(f"render failed: {exc}")
        return 1

    print(f"generated tree written to {output}", file=sys.stderr)
    return 0


def cmd_build_matrix(args: argparse.Namespace) -> int:
    """Print the Docker image build matrix."""
    catalog = _load_catalog(args.catalog)

    from .render.docker import build_matrix, format_matrix_output

    try:
        image_repo = "ghcr.io/guangdai/codervps-devbox"
        matrix = build_matrix(catalog, image_repo)
    except (OSError, ValueError, KeyError) as exc:
        _fail(f"build matrix failed: {exc}")
        return 1

    print(format_matrix_output(matrix, fmt=args.format))
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

    # Validate
    sub.add_parser("validate", help="validate source configuration and generated assets")

    # refresh-catalog
    refresh_parser = sub.add_parser("refresh-catalog", help="refresh toolchain catalog")
    refresh_parser.add_argument(
        "--output", default="build/toolchains.json", help="output path for toolchain catalog JSON"
    )
    refresh_parser.add_argument(
        "--fixture-dir", default=None, help="directory with fixture JSON for testing"
    )

    # render-generated
    render_parser = sub.add_parser("render-generated", help="render the generated branch tree")
    render_parser.add_argument("--catalog", required=True, help="path to toolchains.json catalog")
    render_parser.add_argument(
        "--output", default="build/generated", help="output directory for generated tree"
    )
    render_parser.add_argument("--images", default=None, help="path to images.json catalog")
    render_parser.add_argument(
        "--write-images-json",
        action="store_true",
        dest="write_images_json",
        default=False,
        help="write images.json to the generated tree (use in publish job only)",
    )

    # build-matrix
    matrix_parser = sub.add_parser("build-matrix", help="print Docker image build matrix")
    matrix_parser.add_argument("--catalog", required=True, help="path to toolchains.json catalog")
    matrix_parser.add_argument(
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
